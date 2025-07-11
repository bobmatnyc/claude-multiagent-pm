"""
Tools Manager for AI Operations

Manages AI tools and function calls with sandboxed execution,
security controls, and performance monitoring.
"""

import asyncio
import logging
import json
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class ToolStatus(Enum):
    """Tool execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolExecution:
    """Tool execution record."""

    id: str
    tool_name: str
    parameters: Dict[str, Any]
    status: ToolStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


@dataclass
class ToolDefinition:
    """Tool definition."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    security_level: str = "medium"  # low, medium, high
    timeout: float = 30.0
    sandboxed: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolsManager:
    """
    Tools management system for AI operations.

    Provides secure tool execution with sandboxing, monitoring,
    and enterprise-grade security controls.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tools manager.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Tool registry
        self.tools: Dict[str, ToolDefinition] = {}
        self.executions: Dict[str, ToolExecution] = {}

        # Configuration
        self.max_concurrent_executions = self.config.get("max_concurrent_executions", 10)
        self.default_timeout = self.config.get("default_timeout", 30.0)
        self.sandbox_enabled = self.config.get("sandbox_enabled", True)
        self.security_level = self.config.get("security_level", "medium")

        # Security controls
        self.allowed_commands = self.config.get("allowed_commands", [])
        self.blocked_commands = self.config.get("blocked_commands", [])
        self.allowed_file_extensions = self.config.get(
            "allowed_file_extensions", [".txt", ".json", ".csv"]
        )
        self.blocked_paths = self.config.get("blocked_paths", ["/etc", "/sys", "/proc"])

        # Performance tracking
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0

        # Concurrent execution control
        self.execution_semaphore = asyncio.Semaphore(self.max_concurrent_executions)

        # Initialize default tools
        self._initialize_default_tools()

        self.logger.info("Tools manager initialized")

    def _initialize_default_tools(self):
        """Initialize default tools."""
        # File operations
        self.register_tool(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["file_path"],
            },
            function=self._read_file,
            security_level="medium",
        )

        self.register_tool(
            name="write_file",
            description="Write content to a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["file_path", "content"],
            },
            function=self._write_file,
            security_level="high",
        )

        # System operations
        self.register_tool(
            name="execute_command",
            description="Execute a system command",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "number", "description": "Timeout in seconds"},
                },
                "required": ["command"],
            },
            function=self._execute_command,
            security_level="high",
        )

        # Data processing
        self.register_tool(
            name="process_json",
            description="Process JSON data",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "JSON data to process"},
                    "operation": {"type": "string", "description": "Operation to perform"},
                },
                "required": ["data", "operation"],
            },
            function=self._process_json,
            security_level="low",
        )

        # HTTP operations
        self.register_tool(
            name="http_request",
            description="Make HTTP request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method"},
                    "headers": {"type": "object", "description": "HTTP headers"},
                    "data": {"type": "string", "description": "Request body"},
                },
                "required": ["url"],
            },
            function=self._http_request,
            security_level="medium",
        )

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable,
        security_level: str = "medium",
        timeout: float = None,
        sandboxed: bool = True,
        enabled: bool = True,
    ):
        """
        Register a new tool.

        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            function: Tool function
            security_level: Security level (low, medium, high)
            timeout: Execution timeout
            sandboxed: Whether to execute in sandbox
            enabled: Whether tool is enabled
        """
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            security_level=security_level,
            timeout=timeout or self.default_timeout,
            sandboxed=sandboxed,
            enabled=enabled,
        )

        self.logger.info(f"Registered tool: {name}")

    def unregister_tool(self, name: str):
        """Unregister a tool."""
        if name in self.tools:
            del self.tools[name]
            self.logger.info(f"Unregistered tool: {name}")

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool definitions."""
        return {
            name: {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "security_level": tool.security_level,
                "timeout": tool.timeout,
                "sandboxed": tool.sandboxed,
                "enabled": tool.enabled,
            }
            for name, tool in self.tools.items()
            if tool.enabled
        }

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with security controls.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Optional execution context

        Returns:
            Execution result
        """
        # Check if tool exists and is enabled
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        if not tool.enabled:
            raise ValueError(f"Tool '{tool_name}' is disabled")

        # Create execution record
        execution_id = f"{tool_name}_{int(time.time() * 1000)}"
        execution = ToolExecution(
            id=execution_id,
            tool_name=tool_name,
            parameters=parameters,
            status=ToolStatus.PENDING,
            start_time=datetime.now(),
            metadata=context or {},
        )

        self.executions[execution_id] = execution

        try:
            # Security validation
            await self._validate_tool_execution(tool, parameters)

            # Execute with concurrency control
            async with self.execution_semaphore:
                execution.status = ToolStatus.RUNNING
                start_time = time.time()

                try:
                    # Execute tool function
                    if tool.sandboxed and self.sandbox_enabled:
                        result = await self._execute_sandboxed(tool, parameters, context)
                    else:
                        result = await self._execute_direct(tool, parameters, context)

                    execution_time = time.time() - start_time

                    # Update execution record
                    execution.status = ToolStatus.COMPLETED
                    execution.end_time = datetime.now()
                    execution.result = result
                    execution.execution_time = execution_time

                    # Update metrics
                    self.total_executions += 1
                    self.successful_executions += 1
                    self.total_execution_time += execution_time

                    self.logger.info(
                        f"Tool executed successfully: {tool_name} ({execution_time:.2f}s)"
                    )

                    return {
                        "success": True,
                        "execution_id": execution_id,
                        "result": result,
                        "execution_time": execution_time,
                    }

                except asyncio.TimeoutError:
                    execution.status = ToolStatus.TIMEOUT
                    execution.error = "Execution timeout"
                    self.failed_executions += 1
                    raise
                except Exception as e:
                    execution.status = ToolStatus.FAILED
                    execution.error = str(e)
                    self.failed_executions += 1
                    raise
                finally:
                    execution.end_time = datetime.now()
                    execution.execution_time = time.time() - start_time
                    self.total_executions += 1

        except Exception as e:
            self.logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "execution_time": execution.execution_time,
            }

    async def _validate_tool_execution(self, tool: ToolDefinition, parameters: Dict[str, Any]):
        """Validate tool execution security."""
        # Check security level
        if tool.security_level == "high" and self.security_level == "low":
            raise ValueError("High security tool requires higher security level")

        # Validate parameters
        if "command" in parameters:
            await self._validate_command(parameters["command"])

        if "file_path" in parameters:
            await self._validate_file_path(parameters["file_path"])

        if "url" in parameters:
            await self._validate_url(parameters["url"])

    async def _validate_command(self, command: str):
        """Validate command execution."""
        command_parts = command.split()
        if not command_parts:
            raise ValueError("Empty command")

        base_command = command_parts[0]

        # Check allowed commands
        if self.allowed_commands and base_command not in self.allowed_commands:
            raise ValueError(f"Command '{base_command}' not allowed")

        # Check blocked commands
        if base_command in self.blocked_commands:
            raise ValueError(f"Command '{base_command}' is blocked")

        # Check for dangerous patterns
        dangerous_patterns = ["rm -rf", "sudo", "chmod 777", "wget", "curl"]
        if any(pattern in command for pattern in dangerous_patterns):
            raise ValueError("Command contains dangerous patterns")

    async def _validate_file_path(self, file_path: str):
        """Validate file path access."""
        # Check for blocked paths
        for blocked_path in self.blocked_paths:
            if file_path.startswith(blocked_path):
                raise ValueError(f"Access to '{blocked_path}' is blocked")

        # Check file extension
        if self.allowed_file_extensions:
            _, ext = os.path.splitext(file_path)
            if ext and ext not in self.allowed_file_extensions:
                raise ValueError(f"File extension '{ext}' not allowed")

        # Check for path traversal
        if ".." in file_path:
            raise ValueError("Path traversal not allowed")

    async def _validate_url(self, url: str):
        """Validate URL access."""
        # Check for localhost/internal URLs
        if "localhost" in url or "127.0.0.1" in url or "192.168." in url:
            raise ValueError("Access to internal URLs is blocked")

        # Check for file:// URLs
        if url.startswith("file://"):
            raise ValueError("File URLs are not allowed")

    async def _execute_sandboxed(
        self, tool: ToolDefinition, parameters: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute tool in sandbox."""
        # Create temporary directory for sandbox
        with tempfile.TemporaryDirectory() as sandbox_dir:
            # Set up sandbox environment
            sandbox_env = os.environ.copy()
            sandbox_env["TMPDIR"] = sandbox_dir
            sandbox_env["HOME"] = sandbox_dir

            # Execute tool with timeout
            try:
                result = await asyncio.wait_for(
                    tool.function(parameters, context, sandbox_env), timeout=tool.timeout
                )
                return result
            except asyncio.TimeoutError:
                self.logger.warning(f"Tool execution timeout: {tool.name}")
                raise

    async def _execute_direct(
        self, tool: ToolDefinition, parameters: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute tool directly."""
        try:
            result = await asyncio.wait_for(
                tool.function(parameters, context), timeout=tool.timeout
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Tool execution timeout: {tool.name}")
            raise

    # Default tool implementations

    async def _read_file(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> str:
        """Read file content."""
        file_path = parameters["file_path"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")

    async def _write_file(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> str:
        """Write file content."""
        file_path = parameters["file_path"]
        content = parameters["content"]

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as e:
            raise ValueError(f"Failed to write file: {e}")

    async def _execute_command(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> str:
        """Execute system command."""
        command = parameters["command"]
        timeout = parameters.get("timeout", 30.0)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env or os.environ,
            )

            if result.returncode != 0:
                raise ValueError(f"Command failed: {result.stderr}")

            return result.stdout
        except subprocess.TimeoutExpired:
            raise ValueError("Command execution timeout")
        except Exception as e:
            raise ValueError(f"Command execution failed: {e}")

    async def _process_json(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Process JSON data."""
        data = parameters["data"]
        operation = parameters["operation"]

        try:
            json_data = json.loads(data)

            if operation == "validate":
                return {"valid": True, "data": json_data}
            elif operation == "keys":
                return list(json_data.keys()) if isinstance(json_data, dict) else []
            elif operation == "values":
                return list(json_data.values()) if isinstance(json_data, dict) else []
            elif operation == "pretty":
                return json.dumps(json_data, indent=2)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    async def _http_request(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request."""
        import httpx

        url = parameters["url"]
        method = parameters.get("method", "GET")
        headers = parameters.get("headers", {})
        data = parameters.get("data")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method, url=url, headers=headers, content=data
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                }
        except Exception as e:
            raise ValueError(f"HTTP request failed: {e}")

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history."""
        executions = sorted(self.executions.values(), key=lambda x: x.start_time, reverse=True)

        return [execution.to_dict() for execution in executions[:limit]]

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "average_execution_time": self.total_execution_time / max(self.total_executions, 1),
            "registered_tools": len(self.tools),
            "enabled_tools": len([t for t in self.tools.values() if t.enabled]),
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "healthy": True,
            "registered_tools": len(self.tools),
            "enabled_tools": len([t for t in self.tools.values() if t.enabled]),
            "total_executions": self.total_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "sandbox_enabled": self.sandbox_enabled,
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "average_execution_time": self.total_execution_time / max(self.total_executions, 1),
            "registered_tools": len(self.tools),
            "enabled_tools": len([t for t in self.tools.values() if t.enabled]),
            "concurrent_executions": self.max_concurrent_executions
            - self.execution_semaphore._value,
            "security_level": self.security_level,
            "sandbox_enabled": self.sandbox_enabled,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"ToolsManager(tools={len(self.tools)}, executions={self.total_executions})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<ToolsManager tools={len(self.tools)} executions={self.total_executions} success_rate={self.successful_executions/max(self.total_executions,1):.2%}>"
