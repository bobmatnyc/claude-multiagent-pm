"""
Tests for SimpleMessageBus async message passing system.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from claude_pm.orchestration.message_bus import (
    SimpleMessageBus,
    Message,
    Request,
    Response,
    MessageStatus
)


class TestMessageClasses:
    """Test Message, Request, and Response data classes."""
    
    def test_message_creation(self):
        """Test basic message creation with defaults."""
        msg = Message()
        
        assert msg.id is not None
        assert len(msg.id) == 36  # UUID format
        assert msg.correlation_id is None
        assert isinstance(msg.timestamp, datetime)
        assert msg.agent_id is None
        assert msg.data == {}
        assert msg.status == MessageStatus.PENDING
        
    def test_request_creation(self):
        """Test request creation with custom values."""
        req = Request(
            agent_id="test_agent",
            data={"action": "process"},
            timeout=10.0
        )
        
        assert req.agent_id == "test_agent"
        assert req.data == {"action": "process"}
        assert req.timeout == 10.0
        assert req.reply_to is None
        
    def test_response_creation(self):
        """Test response creation and correlation."""
        resp = Response(
            request_id="req-123",
            agent_id="test_agent",
            data={"result": "success"}
        )
        
        assert resp.request_id == "req-123"
        assert resp.correlation_id == "req-123"  # Auto-set from request_id
        assert resp.success is True
        assert resp.error is None
        
    def test_response_with_error(self):
        """Test error response creation."""
        resp = Response(
            request_id="req-123",
            success=False,
            error="Processing failed"
        )
        
        assert resp.success is False
        assert resp.error == "Processing failed"


class TestSimpleMessageBus:
    """Test SimpleMessageBus functionality."""
    
    @pytest.fixture
    def message_bus(self):
        """Create a fresh message bus instance."""
        return SimpleMessageBus()
        
    @pytest.mark.asyncio
    async def test_handler_registration(self, message_bus):
        """Test registering and unregistering handlers."""
        # Create mock handler
        handler = AsyncMock(return_value=Response())
        
        # Register handler
        message_bus.register_handler("agent1", handler)
        assert "agent1" in message_bus.registered_agents
        
        # Try to register duplicate - should raise
        with pytest.raises(ValueError, match="Handler already registered"):
            message_bus.register_handler("agent1", handler)
            
        # Unregister handler
        message_bus.unregister_handler("agent1")
        assert "agent1" not in message_bus.registered_agents
        
    @pytest.mark.asyncio
    async def test_simple_request_response(self, message_bus):
        """Test basic request/response flow."""
        # Define handler
        async def echo_handler(request: Request) -> Response:
            return Response(
                request_id=request.id,
                agent_id="echo",
                data={"echo": request.data}
            )
            
        # Register handler
        message_bus.register_handler("echo", echo_handler)
        
        # Send request
        response = await message_bus.send_request(
            "echo",
            {"message": "hello"}
        )
        
        assert response.success is True
        assert response.data == {"echo": {"message": "hello"}}
        assert response.status == MessageStatus.COMPLETED
        
    @pytest.mark.asyncio
    async def test_handler_exception(self, message_bus):
        """Test handling of exceptions in handlers."""
        # Define failing handler
        async def failing_handler(request: Request) -> Response:
            raise ValueError("Handler error")
            
        # Register handler
        message_bus.register_handler("failing", failing_handler)
        
        # Send request - should get error response
        response = await message_bus.send_request(
            "failing",
            {"test": "data"}
        )
        
        assert response.success is False
        assert response.status == MessageStatus.ERROR
        assert "Handler error" in response.error
        
    @pytest.mark.asyncio
    async def test_request_timeout(self, message_bus):
        """Test request timeout handling."""
        # Define slow handler
        async def slow_handler(request: Request) -> Response:
            await asyncio.sleep(2.0)  # Longer than timeout
            return Response(request_id=request.id)
            
        # Register handler
        message_bus.register_handler("slow", slow_handler)
        
        # Send request with short timeout
        response = await message_bus.send_request(
            "slow",
            {"test": "data"},
            timeout=0.1
        )
        
        assert response.success is False
        assert response.status == MessageStatus.TIMEOUT
        assert "timed out" in response.error
        
    @pytest.mark.asyncio
    async def test_no_handler_registered(self, message_bus):
        """Test sending request to unregistered agent."""
        with pytest.raises(ValueError, match="No handler registered"):
            await message_bus.send_request(
                "unknown",
                {"test": "data"}
            )
            
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, message_bus):
        """Test handling multiple concurrent requests."""
        call_count = 0
        call_order = []
        
        # Define handler with counter
        async def counter_handler(request: Request) -> Response:
            nonlocal call_count
            call_count += 1
            current_count = call_count
            call_order.append(current_count)
            await asyncio.sleep(0.1)  # Simulate work
            return Response(
                request_id=request.id,
                data={"count": current_count, "n": request.data["n"]}
            )
            
        # Register handler
        message_bus.register_handler("counter", counter_handler)
        
        # Send multiple concurrent requests
        tasks = [
            message_bus.send_request("counter", {"n": i})
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.success for r in responses)
        assert call_count == 5
        
        # Should have called handler 5 times with unique counts
        assert len(call_order) == 5
        assert set(call_order) == {1, 2, 3, 4, 5}
        
    @pytest.mark.asyncio
    async def test_shutdown(self, message_bus):
        """Test graceful shutdown."""
        # Define handler
        async def handler(request: Request) -> Response:
            await asyncio.sleep(0.5)  # Longer sleep
            return Response(request_id=request.id)
            
        message_bus.register_handler("test", handler)
        
        # Start a request but don't wait for it
        request_task = asyncio.create_task(
            message_bus.send_request("test", {}, timeout=2.0)
        )
        
        # Give it a moment to start processing
        await asyncio.sleep(0.1)
        
        # Shutdown
        await message_bus.shutdown()
        
        # Check shutdown state
        assert message_bus.is_shutdown
        assert len(message_bus.registered_agents) == 0
        
        # Try to send after shutdown
        with pytest.raises(RuntimeError, match="shutting down"):
            await message_bus.send_request("test", {})
            
        # The request task should complete (possibly cancelled)
        try:
            await request_task
        except asyncio.CancelledError:
            pass  # Expected if request was cancelled during shutdown
            
    @pytest.mark.asyncio
    async def test_correlation_tracking(self, message_bus):
        """Test request/response correlation."""
        received_requests = []
        
        # Define handler that tracks requests
        async def tracking_handler(request: Request) -> Response:
            received_requests.append(request)
            return Response(
                request_id=request.id,
                correlation_id=request.id,
                data={"req_id": request.id}
            )
            
        message_bus.register_handler("tracker", tracking_handler)
        
        # Send multiple requests
        responses = []
        for i in range(3):
            resp = await message_bus.send_request(
                "tracker",
                {"index": i}
            )
            responses.append(resp)
            
        # Verify correlation
        assert len(received_requests) == 3
        assert len(responses) == 3
        
        for req, resp in zip(received_requests, responses):
            assert resp.request_id == req.id
            assert resp.correlation_id == req.id
            assert resp.data["req_id"] == req.id
            
    @pytest.mark.asyncio
    async def test_pending_request_tracking(self, message_bus):
        """Test tracking of pending requests."""
        # Define slow handler
        async def slow_handler(request: Request) -> Response:
            await asyncio.sleep(0.2)
            return Response(request_id=request.id)
            
        message_bus.register_handler("slow", slow_handler)
        
        # Start multiple requests
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                message_bus.send_request("slow", {"n": i})
            )
            tasks.append(task)
            
        # Check pending count while processing
        await asyncio.sleep(0.1)
        assert message_bus.pending_request_count > 0
        
        # Wait for completion
        await asyncio.gather(*tasks)
        
        # Should have no pending requests
        assert message_bus.pending_request_count == 0
        
    @pytest.mark.asyncio
    async def test_custom_timeout_per_request(self, message_bus):
        """Test different timeouts for different requests."""
        # Define handler with variable delay
        async def delay_handler(request: Request) -> Response:
            delay = request.data.get("delay", 0.1)
            await asyncio.sleep(delay)
            return Response(request_id=request.id)
            
        message_bus.register_handler("delay", delay_handler)
        
        # Fast request should succeed
        fast_response = await message_bus.send_request(
            "delay",
            {"delay": 0.05},
            timeout=0.2
        )
        assert fast_response.success is True
        
        # Slow request should timeout
        slow_response = await message_bus.send_request(
            "delay",
            {"delay": 0.3},
            timeout=0.1
        )
        assert slow_response.success is False
        assert slow_response.status == MessageStatus.TIMEOUT


class TestMessageBusIntegration:
    """Integration tests for message bus scenarios."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_communication(self):
        """Test communication between multiple agents."""
        bus = SimpleMessageBus()
        
        # Agent A handler - processes data
        async def agent_a_handler(request: Request) -> Response:
            value = request.data.get("value", 0)
            result = value * 2
            return Response(
                request_id=request.id,
                agent_id="agent_a",
                data={"result": result}
            )
            
        # Agent B handler - uses Agent A
        async def agent_b_handler(request: Request) -> Response:
            # Forward to Agent A
            a_response = await bus.send_request(
                "agent_a",
                {"value": request.data.get("input", 0)}
            )
            
            # Process result
            final_result = a_response.data["result"] + 10
            return Response(
                request_id=request.id,
                agent_id="agent_b",
                data={"final": final_result}
            )
            
        # Register handlers
        bus.register_handler("agent_a", agent_a_handler)
        bus.register_handler("agent_b", agent_b_handler)
        
        # Send request to Agent B
        response = await bus.send_request(
            "agent_b",
            {"input": 5}
        )
        
        assert response.success is True
        assert response.data["final"] == 20  # (5 * 2) + 10
        
        await bus.shutdown()
        
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test error propagation through agent chain."""
        bus = SimpleMessageBus()
        
        # Agent A - fails sometimes
        async def agent_a_handler(request: Request) -> Response:
            if request.data.get("fail", False):
                raise RuntimeError("Agent A failure")
            return Response(
                request_id=request.id,
                data={"status": "ok"}
            )
            
        # Agent B - calls Agent A
        async def agent_b_handler(request: Request) -> Response:
            a_response = await bus.send_request(
                "agent_a",
                {"fail": request.data.get("trigger_fail", False)}
            )
            
            if not a_response.success:
                return Response(
                    request_id=request.id,
                    success=False,
                    error=f"Upstream error: {a_response.error}"
                )
                
            return Response(
                request_id=request.id,
                data={"upstream_status": a_response.data.get("status")}
            )
            
        bus.register_handler("agent_a", agent_a_handler)
        bus.register_handler("agent_b", agent_b_handler)
        
        # Success case
        success_response = await bus.send_request(
            "agent_b",
            {"trigger_fail": False}
        )
        assert success_response.success is True
        assert success_response.data["upstream_status"] == "ok"
        
        # Failure case
        fail_response = await bus.send_request(
            "agent_b",
            {"trigger_fail": True}
        )
        assert fail_response.success is False
        assert "Upstream error" in fail_response.error
        assert "Agent A failure" in fail_response.error
        
        await bus.shutdown()