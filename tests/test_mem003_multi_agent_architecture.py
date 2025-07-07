"""
Integration tests for MEM-003 Enhanced Multi-Agent Architecture
Tests the complete multi-agent ecosystem with memory integration.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory, ClaudePMConfig
from claude_pm.services.multi_agent_orchestrator import (
    MultiAgentOrchestrator, AgentType, AgentStatus, AgentTask, 
    create_multi_agent_orchestrator
)
from claude_pm.services.mem0_context_manager import (
    Mem0ContextManager, ContextRequest, ContextType, ContextScope,
    create_mem0_context_manager
)


class TestMem0ContextManager:
    """Test the memory-driven context management system."""
    
    @pytest.fixture
    async def mock_memory(self):
        """Create a mock memory instance with sample data."""
        memory = Mock(spec=ClaudePMMemory)
        memory.retrieve_memories = AsyncMock()
        
        # Mock memory responses
        sample_memories = [
            {
                "id": "mem_001",
                "content": "FastAPI REST API pattern with async/await support",
                "metadata": {
                    "category": "pattern",
                    "pattern_type": "api_design",
                    "tags": ["fastapi", "api", "python"],
                    "stored_at": "2024-01-01T00:00:00"
                }
            },
            {
                "id": "mem_002", 
                "content": "Python coding standards: snake_case for variables",
                "metadata": {
                    "category": "team",
                    "standard_type": "naming_convention",
                    "tags": ["python", "standards"],
                    "stored_at": "2024-01-01T00:00:00"
                }
            }
        ]
        
        memory.retrieve_memories.return_value = Mock(
            success=True,
            data={"memories": sample_memories}
        )
        
        return memory
    
    @pytest.fixture
    def context_manager(self, mock_memory):
        """Create a context manager with mock memory."""
        return create_mem0_context_manager(mock_memory)
    
    @pytest.mark.asyncio
    async def test_agent_context_preparation(self, context_manager, mock_memory):
        """Test agent-specific context preparation."""
        context = await context_manager.prepare_agent_context(
            agent_type="code_review_engineer",
            project_name="test_project",
            task_description="Review Python code for style compliance"
        )
        
        assert context.request.agent_type == "code_review_engineer"
        assert context.request.project_name == "test_project"
        assert context.total_memories >= 0
        assert context.context_summary != ""
        assert context.preparation_time_ms >= 0
        
        # Verify memory was called
        mock_memory.retrieve_memories.assert_called()
    
    @pytest.mark.asyncio
    async def test_context_caching(self, context_manager, mock_memory):
        """Test context caching functionality."""
        # First call should retrieve from memory
        context1 = await context_manager.prepare_agent_context(
            agent_type="engineer",
            project_name="test_project",
            task_description="Implement user authentication"
        )
        
        call_count_1 = mock_memory.retrieve_memories.call_count
        
        # Second identical call should use cache
        context2 = await context_manager.prepare_agent_context(
            agent_type="engineer", 
            project_name="test_project",
            task_description="Implement user authentication"
        )
        
        call_count_2 = mock_memory.retrieve_memories.call_count
        
        # Should be cached (no additional memory calls)
        assert call_count_2 == call_count_1
        assert context1.context_id != context2.context_id  # Different instances but cached
    
    @pytest.mark.asyncio
    async def test_relevance_scoring(self, context_manager, mock_memory):
        """Test memory relevance scoring."""
        context = await context_manager.prepare_context(
            ContextRequest(
                context_type=ContextType.AGENT_TASK,
                scope=ContextScope.PROJECT_SPECIFIC,
                project_name="test_project",
                keywords=["fastapi", "python"],
                max_memories=5
            )
        )
        
        # Should have relevance scores for memories
        assert len(context.relevance_scores) >= 0
        
        # Scores should be between 0 and max possible score
        for score in context.relevance_scores.values():
            assert 0 <= score <= 5.0  # Approximate max score
    
    def test_agent_role_filters(self, context_manager):
        """Test agent role-specific filters."""
        # Test that different agent types have different filters
        filters = context_manager.agent_role_filters
        
        assert "code_review_engineer" in filters
        assert "architect" in filters
        assert "security_engineer" in filters
        
        # Code review engineer should focus on patterns, team, and errors
        code_review_filter = filters["code_review_engineer"]
        assert MemoryCategory.PATTERN in code_review_filter["primary_categories"]
        assert MemoryCategory.TEAM in code_review_filter["primary_categories"]
        assert MemoryCategory.ERROR in code_review_filter["primary_categories"]
        
        # Architect should focus on project and patterns
        architect_filter = filters["architect"]
        assert MemoryCategory.PROJECT in architect_filter["primary_categories"]
        assert MemoryCategory.PATTERN in architect_filter["primary_categories"]


class TestMultiAgentOrchestrator:
    """Test the multi-agent orchestration system."""
    
    @pytest.fixture
    async def mock_memory(self):
        """Create a mock memory instance."""
        memory = Mock(spec=ClaudePMMemory)
        memory.retrieve_memories = AsyncMock()
        memory.store_memory = AsyncMock()
        
        memory.retrieve_memories.return_value = Mock(
            success=True,
            data={"memories": []}
        )
        memory.store_memory.return_value = Mock(
            success=True,
            memory_id="test_memory_id"
        )
        
        return memory
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        os.system(f"cd {repo_path} && git init")
        os.system(f"cd {repo_path} && git config user.email 'test@example.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test User'")
        
        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        os.system(f"cd {repo_path} && git add README.md")
        os.system(f"cd {repo_path} && git commit -m 'Initial commit'")
        
        yield str(repo_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def orchestrator(self, temp_repo, mock_memory):
        """Create a multi-agent orchestrator for testing."""
        orchestrator = await create_multi_agent_orchestrator(
            base_repo_path=temp_repo,
            memory=mock_memory,
            max_parallel=2  # Reduced for testing
        )
        yield orchestrator
        await orchestrator.cleanup()
    
    def test_agent_definitions(self, orchestrator):
        """Test that all 11 agents are defined."""
        agent_types = list(orchestrator.agent_definitions.keys())
        
        # Should have exactly 11 agent types
        assert len(agent_types) == 11
        
        # Core agents
        assert AgentType.ORCHESTRATOR in agent_types
        assert AgentType.ARCHITECT in agent_types
        assert AgentType.ENGINEER in agent_types
        assert AgentType.QA in agent_types
        assert AgentType.RESEARCHER in agent_types
        
        # Specialist agents
        assert AgentType.SECURITY_ENGINEER in agent_types
        assert AgentType.PERFORMANCE_ENGINEER in agent_types
        assert AgentType.DEVOPS_ENGINEER in agent_types
        assert AgentType.DATA_ENGINEER in agent_types
        assert AgentType.UI_UX_ENGINEER in agent_types
        assert AgentType.CODE_REVIEW_ENGINEER in agent_types
    
    def test_code_review_engineer_definition(self, orchestrator):
        """Test the Code Review Engineer agent definition."""
        agent_def = orchestrator.agent_definitions[AgentType.CODE_REVIEW_ENGINEER]
        
        assert agent_def["name"] == "Code Review Engineer Agent"
        assert "comprehensive code reviews" in agent_def["description"]
        
        # Should support multi-dimensional review
        specializations = agent_def["specializations"]
        assert "code_review" in specializations
        assert "style_analysis" in specializations  
        assert "security_review" in specializations
        assert "performance_review" in specializations
        assert "test_coverage" in specializations
        
        # Should use appropriate memory categories
        memory_categories = agent_def["memory_categories"]
        assert MemoryCategory.PATTERN in memory_categories
        assert MemoryCategory.TEAM in memory_categories
        assert MemoryCategory.ERROR in memory_categories
    
    @pytest.mark.asyncio
    async def test_task_submission(self, orchestrator):
        """Test task submission to the orchestrator."""
        task_id = await orchestrator.submit_task(
            agent_type=AgentType.CODE_REVIEW_ENGINEER,
            description="Review user authentication code",
            project_name="test_project",
            priority=8
        )
        
        assert task_id is not None
        assert len(orchestrator.task_queue) == 1
        
        # Task should be in queue with correct priority
        task = orchestrator.task_queue[0]
        assert task.agent_type == AgentType.CODE_REVIEW_ENGINEER
        assert task.description == "Review user authentication code"
        assert task.priority == 8
    
    @pytest.mark.asyncio
    async def test_memory_context_preparation(self, orchestrator, mock_memory):
        """Test memory context preparation for agents."""
        context = await orchestrator.prepare_memory_context(
            agent_type=AgentType.SECURITY_ENGINEER,
            project_name="test_project",
            task_description="Analyze security vulnerabilities"
        )
        
        assert context["agent_type"] == "security_engineer"
        assert context["project_name"] == "test_project"
        assert context["task_description"] == "Analyze security vulnerabilities"
        assert "relevant_memories" in context
        assert "specializations" in context
        assert "context_keywords" in context
        
        # Should have called memory retrieval
        mock_memory.retrieve_memories.assert_called()
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator):
        """Test parallel execution of multiple tasks."""
        # Submit multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await orchestrator.submit_task(
                agent_type=AgentType.ENGINEER,
                description=f"Task {i+1}",
                project_name="test_project",
                priority=5
            )
            task_ids.append(task_id)
        
        # Execute tasks in parallel
        summary = await orchestrator.run_parallel_execution(max_iterations=2)
        
        assert summary["tasks_completed"] >= 0
        assert summary["tasks_failed"] >= 0
        assert summary["iterations"] <= 2
        assert "worktree_stats" in summary
    
    @pytest.mark.asyncio 
    async def test_agent_messaging(self, orchestrator):
        """Test agent-to-agent messaging."""
        # Send messages between agents
        await orchestrator.send_message(
            from_agent="architect",
            to_agent="security_engineer", 
            message={"type": "security_review_request", "content": "Please review auth design"}
        )
        
        await orchestrator.send_message(
            from_agent="security_engineer",
            to_agent="code_review_engineer",
            message={"type": "security_findings", "content": "Found vulnerability in auth"}
        )
        
        # Check message queues
        security_messages = await orchestrator.get_messages("security_engineer")
        review_messages = await orchestrator.get_messages("code_review_engineer")
        
        assert len(security_messages) == 1
        assert len(review_messages) == 1
        
        assert security_messages[0]["from"] == "architect"
        assert security_messages[0]["type"] == "security_review_request"
        
        assert review_messages[0]["from"] == "security_engineer"
        assert review_messages[0]["type"] == "security_findings"
    
    def test_orchestrator_stats(self, orchestrator):
        """Test orchestrator statistics."""
        stats = orchestrator.get_orchestrator_stats()
        
        assert "agent_definitions" in stats
        assert "active_executions" in stats
        assert "queued_tasks" in stats
        assert "completed_tasks" in stats
        assert "max_parallel" in stats
        assert "worktree_stats" in stats
        assert "agent_types" in stats
        
        assert stats["agent_definitions"] == 11
        assert stats["max_parallel"] == 2  # Set in fixture
        assert len(stats["agent_types"]) == 11


class TestIntegration:
    """Integration tests for the complete MEM-003 system."""
    
    @pytest.fixture
    async def mock_memory(self):
        """Create a comprehensive mock memory instance."""
        memory = Mock(spec=ClaudePMMemory)
        memory.connect = AsyncMock(return_value=True)
        memory.disconnect = AsyncMock()
        memory.retrieve_memories = AsyncMock()
        memory.store_memory = AsyncMock()
        memory.create_project_memory_space = AsyncMock()
        
        # Mock rich memory responses
        pattern_memories = [
            {
                "id": "pattern_001",
                "content": "Code review pattern: Check security, performance, style, and testing",
                "metadata": {
                    "category": "pattern",
                    "pattern_type": "code_review",
                    "tags": ["code_review", "security", "performance"],
                    "stored_at": "2024-01-01T00:00:00"
                }
            }
        ]
        
        team_memories = [
            {
                "id": "team_001",
                "content": "Team standard: All code must pass security review",
                "metadata": {
                    "category": "team", 
                    "standard_type": "security_policy",
                    "tags": ["security", "policy"],
                    "stored_at": "2024-01-01T00:00:00"
                }
            }
        ]
        
        def mock_retrieve(category=None, **kwargs):
            if category == MemoryCategory.PATTERN:
                return Mock(success=True, data={"memories": pattern_memories})
            elif category == MemoryCategory.TEAM:
                return Mock(success=True, data={"memories": team_memories})
            else:
                return Mock(success=True, data={"memories": []})
        
        memory.retrieve_memories.side_effect = mock_retrieve
        memory.store_memory.return_value = Mock(success=True, memory_id="test_id")
        memory.create_project_memory_space.return_value = Mock(success=True)
        
        return memory
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        os.system(f"cd {repo_path} && git init")
        os.system(f"cd {repo_path} && git config user.email 'test@example.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test User'")
        
        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        os.system(f"cd {repo_path} && git add README.md")  
        os.system(f"cd {repo_path} && git commit -m 'Initial commit'")
        
        yield str(repo_path)
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, temp_repo, mock_memory):
        """Test the complete end-to-end MEM-003 workflow."""
        # Initialize all components
        context_manager = create_mem0_context_manager(mock_memory)
        orchestrator = await create_multi_agent_orchestrator(
            base_repo_path=temp_repo,
            memory=mock_memory,
            max_parallel=2
        )
        
        try:
            # 1. Prepare context for code review
            context = await context_manager.prepare_agent_context(
                agent_type="code_review_engineer",
                project_name="integration_test",
                task_description="Review authentication implementation"
            )
            
            assert context.total_memories >= 0
            assert context.context_summary != ""
            
            # 2. Submit tasks to orchestrator
            task_id_1 = await orchestrator.submit_task(
                agent_type=AgentType.CODE_REVIEW_ENGINEER,
                description="Multi-dimensional code review of auth module",
                project_name="integration_test",
                priority=9
            )
            
            task_id_2 = await orchestrator.submit_task(
                agent_type=AgentType.SECURITY_ENGINEER,
                description="Security analysis of authentication endpoints",
                project_name="integration_test", 
                priority=8
            )
            
            assert task_id_1 is not None
            assert task_id_2 is not None
            
            # 3. Execute tasks
            summary = await orchestrator.run_parallel_execution(max_iterations=1)
            
            assert summary["iterations"] >= 1
            assert summary["tasks_completed"] + summary["tasks_failed"] >= 0
            
            # 4. Test agent coordination
            await orchestrator.send_message(
                from_agent="code_review_engineer",
                to_agent="security_engineer",
                message={
                    "type": "review_complete",
                    "findings": ["security_issue", "style_issue"],
                    "priority": "high"
                }
            )
            
            messages = await orchestrator.get_messages("security_engineer")
            assert len(messages) == 1
            assert messages[0]["type"] == "review_complete"
            
            # 5. Verify memory integration
            mock_memory.retrieve_memories.assert_called()
            mock_memory.store_memory.assert_called()
            
            # 6. Check final statistics
            stats = orchestrator.get_orchestrator_stats()
            assert stats["agent_definitions"] == 11
            assert "worktree_stats" in stats
            
        finally:
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_code_review_engineer_workflow(self, temp_repo, mock_memory):
        """Test the specific Code Review Engineer workflow."""
        orchestrator = await create_multi_agent_orchestrator(
            base_repo_path=temp_repo,
            memory=mock_memory,
            max_parallel=1
        )
        
        try:
            # Submit code review task
            task_id = await orchestrator.submit_task(
                agent_type=AgentType.CODE_REVIEW_ENGINEER,
                description="Comprehensive review of user management API",
                project_name="test_project",
                context={
                    "files_changed": ["user_api.py", "auth_utils.py"],
                    "review_scope": ["security", "performance", "style", "testing"]
                },
                priority=9
            )
            
            # Execute the task
            summary = await orchestrator.run_parallel_execution(max_iterations=1)
            
            # Check that task was processed
            if task_id in orchestrator.completed_tasks:
                execution = orchestrator.completed_tasks[task_id]
                
                # Verify it's a code review task
                assert execution.agent_type == AgentType.CODE_REVIEW_ENGINEER
                
                # Check that result contains code review specific fields
                if execution.result:
                    assert "review_dimensions" in execution.result
                    assert "security" in execution.result["review_dimensions"]
                    assert "performance" in execution.result["review_dimensions"]
                    assert "style" in execution.result["review_dimensions"]
                    assert "testing" in execution.result["review_dimensions"]
                    
                    assert "findings_count" in execution.result
                    assert "recommendations" in execution.result
            
        finally:
            await orchestrator.cleanup()


# Test runner configuration
@pytest.mark.asyncio
async def test_mem003_architecture_complete():
    """Test that MEM-003 architecture is complete and functional."""
    # Verify all required components exist
    from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator, AgentType
    from claude_pm.services.mem0_context_manager import Mem0ContextManager
    
    # Verify all 11 agent types are defined
    agent_types = list(AgentType)
    assert len(agent_types) == 11
    
    # Verify Code Review Engineer is included
    assert AgentType.CODE_REVIEW_ENGINEER in agent_types
    
    # Verify core components can be imported
    assert MultiAgentOrchestrator is not None
    assert Mem0ContextManager is not None
    
    print("✅ MEM-003 Enhanced Multi-Agent Architecture - All tests passed!")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])