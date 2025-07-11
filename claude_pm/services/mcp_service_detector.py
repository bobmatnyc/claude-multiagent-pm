"""
MCP Service Detector - Enhanced Multi-Agent Orchestrator Integration
Detects available MCP services and integrates them into development workflows.
"""

import asyncio
import logging
import subprocess
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class MCPServiceType(str, Enum):
    """Types of MCP services that can enhance development workflows."""

    PRODUCTIVITY = "productivity"
    CONTEXT_MANAGEMENT = "context_management"
    DEVELOPMENT_TOOLS = "development_tools"
    WORKFLOW_AUTOMATION = "workflow_automation"


@dataclass
class MCPService:
    """Represents an available MCP service and its capabilities."""

    name: str
    service_type: MCPServiceType
    description: str
    available_tools: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    is_available: bool = False
    configuration: Optional[Dict[str, Any]] = None
    usage_context: List[str] = field(default_factory=list)


@dataclass
class MCPWorkflowIntegration:
    """Defines how MCP services integrate into specific workflows."""

    workflow_name: str
    applicable_services: List[str]
    integration_points: Dict[str, str]
    enhancement_description: str


class MCPServiceDetector:
    """
    Detects and manages MCP service integration for the orchestrator.

    Provides capabilities for:
    - Auto-detecting available MCP services
    - Recommending service usage for specific workflows
    - Integrating services into agent task execution
    """

    def __init__(self):
        """Initialize the MCP service detector."""
        self.available_services: Dict[str, MCPService] = {}
        self.workflow_integrations: List[MCPWorkflowIntegration] = []
        self.detection_cache_timeout = 300  # 5 minutes
        self.last_detection_time = 0

        # Define known services and their capabilities
        self.known_services = self._initialize_known_services()
        self.workflow_integrations = self._initialize_workflow_integrations()

        logger.info("MCPServiceDetector initialized")

    def _initialize_known_services(self) -> Dict[str, MCPService]:
        """Initialize definitions for known MCP services."""
        return {
            "mcp-zen": MCPService(
                name="MCP-Zen",
                service_type=MCPServiceType.DEVELOPMENT_TOOLS,
                description="Second opinion service that validates responses with another LLM",
                available_tools=["zen_quote", "breathing_exercise", "focus_timer"],
                capabilities=[
                    "Generate zen quotes for mindfulness",
                    "Provide guided breathing exercises",
                    "Set up focus timers for productivity",
                    "Validate responses with alternative LLM perspective",
                ],
                usage_context=[
                    "When needing a second opinion on complex decisions",
                    "During critical code review processes",
                    "For validating architectural decisions",
                    "When seeking alternative perspectives on solutions",
                    "During stress management in development workflows",
                ],
            ),
            "context-7": MCPService(
                name="Context 7",
                service_type=MCPServiceType.DEVELOPMENT_TOOLS,
                description="Up-to-date code documentation and library examples fetcher",
                available_tools=["resolve-library-id", "get-library-docs"],
                capabilities=[
                    "Resolve library names to Context7-compatible IDs",
                    "Fetch up-to-date documentation for any library",
                    "Get version-specific code examples and APIs",
                    "Access current documentation instead of outdated training data",
                ],
                usage_context=[
                    "When needing current library documentation",
                    "For up-to-date code examples and API references",
                    "When working with new or updated libraries",
                    "To avoid hallucinated or outdated API information",
                    "During development tasks requiring specific library knowledge",
                ],
            ),
        }

    def _initialize_workflow_integrations(self) -> List[MCPWorkflowIntegration]:
        """Define how MCP services integrate into development workflows."""
        return [
            MCPWorkflowIntegration(
                workflow_name="multi_agent_coordination",
                applicable_services=["mcp-zen", "context-7"],
                integration_points={
                    "task_start": "Use zen_quote for motivation, get-library-docs for current documentation",
                    "agent_handoff": "Use get-library-docs to provide agents with up-to-date API references",
                    "error_handling": "Use breathing_exercise for stress management",
                    "task_completion": "Use resolve-library-id to identify proper documentation sources",
                },
                enhancement_description="Enhances multi-agent workflows with mindfulness and current documentation",
            ),
            MCPWorkflowIntegration(
                workflow_name="code_development",
                applicable_services=["mcp-zen"],
                integration_points={
                    "complex_task_start": "Use focus_timer to set dedicated work sessions",
                    "debugging_session": "Use zen_quote for maintaining calm perspective",
                    "refactoring": "Use breathing_exercise before major changes",
                },
                enhancement_description="Improves code development with productivity and mindfulness tools",
            ),
            MCPWorkflowIntegration(
                workflow_name="library_integration",
                applicable_services=["context-7"],
                integration_points={
                    "library_selection": "Use resolve-library-id to identify proper library documentation",
                    "implementation": "Use get-library-docs for current API references and examples",
                    "troubleshooting": "Use get-library-docs with specific topics for targeted help",
                },
                enhancement_description="Enhances development with current, accurate library documentation",
            ),
        ]

    async def detect_available_services(self, force_refresh: bool = False) -> Dict[str, MCPService]:
        """
        Detect which MCP services are currently available.

        Args:
            force_refresh: Force re-detection even if cache is valid

        Returns:
            Dictionary of available MCP services
        """
        import time

        current_time = time.time()

        # Use cache if valid and not forcing refresh
        if (
            not force_refresh
            and (current_time - self.last_detection_time) < self.detection_cache_timeout
        ):
            return self.available_services

        logger.info("Detecting available MCP services...")

        detected_services = {}

        for service_id, service_def in self.known_services.items():
            try:
                is_available = await self._check_service_availability(service_id, service_def)

                if is_available:
                    service_def.is_available = True
                    detected_services[service_id] = service_def
                    logger.info(f"✓ {service_def.name} is available")
                else:
                    logger.debug(f"⚠ {service_def.name} not available")

            except Exception as e:
                logger.debug(f"Error checking {service_def.name}: {e}")

        self.available_services = detected_services
        self.last_detection_time = current_time

        logger.info(f"Detected {len(detected_services)} available MCP services")
        return detected_services

    async def _check_service_availability(self, service_id: str, service_def: MCPService) -> bool:
        """
        Check if a specific MCP service is available.

        Args:
            service_id: Service identifier
            service_def: Service definition

        Returns:
            True if service is available
        """
        try:
            # For MCP-Zen, we can check if the mcp__zen__ tools are available
            if service_id == "mcp-zen":
                # In a real implementation, this would check MCP server availability
                # For now, we'll simulate by checking if npx command exists
                result = await asyncio.create_subprocess_exec(
                    "npx", "--help", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await result.wait()
                return result.returncode == 0

            # For Context 7, check if the service is available via npm
            elif service_id == "context-7":
                try:
                    # Check if npx can find the package
                    result = await asyncio.create_subprocess_exec(
                        "npx",
                        "--help",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await result.wait()
                    if result.returncode == 0:
                        # If npx is available, Context 7 can be installed
                        return True
                    return False
                except:
                    return False

            return False

        except Exception as e:
            logger.debug(f"Error checking service {service_id}: {e}")
            return False

    def get_workflow_recommendations(self, workflow_name: str) -> List[Dict[str, Any]]:
        """
        Get MCP service recommendations for a specific workflow.

        Args:
            workflow_name: Name of the workflow (e.g., 'multi_agent_coordination')

        Returns:
            List of recommendations with service details and usage suggestions
        """
        recommendations = []

        # Find workflow integrations
        relevant_integrations = [
            wi for wi in self.workflow_integrations if wi.workflow_name == workflow_name
        ]

        for integration in relevant_integrations:
            for service_name in integration.applicable_services:
                service_id = service_name.replace("-", "_").lower()

                if service_id in self.available_services:
                    service = self.available_services[service_id]

                    recommendation = {
                        "service": service.name,
                        "type": service.service_type.value,
                        "description": service.description,
                        "available_tools": service.available_tools,
                        "integration_points": integration.integration_points,
                        "enhancement": integration.enhancement_description,
                        "usage_suggestions": service.usage_context,
                    }

                    recommendations.append(recommendation)

        return recommendations

    def get_service_for_context(self, context: str) -> List[MCPService]:
        """
        Get recommended MCP services for a specific development context.

        Args:
            context: Development context (e.g., 'debugging', 'project_switching')

        Returns:
            List of relevant MCP services
        """
        relevant_services = []

        for service in self.available_services.values():
            if any(context.lower() in usage.lower() for usage in service.usage_context):
                relevant_services.append(service)

        return relevant_services

    def generate_orchestrator_guidance(self) -> Dict[str, Any]:
        """
        Generate guidance for the orchestrator on how to use available MCP services.

        Returns:
            Comprehensive guidance dictionary
        """
        if not self.available_services:
            return {
                "status": "no_services",
                "message": "No MCP services detected. Consider installing MCP-Zen or Context 7.",
                "recommendations": [],
            }

        guidance = {
            "status": "services_available",
            "available_services": list(self.available_services.keys()),
            "service_details": {},
            "workflow_integrations": {},
            "usage_patterns": {},
        }

        # Add service details
        for service_id, service in self.available_services.items():
            guidance["service_details"][service_id] = {
                "name": service.name,
                "type": service.service_type.value,
                "tools": service.available_tools,
                "capabilities": service.capabilities,
            }

        # Add workflow integration guidance
        for integration in self.workflow_integrations:
            applicable_services = [
                s
                for s in integration.applicable_services
                if s.replace("-", "_").lower() in self.available_services
            ]

            if applicable_services:
                guidance["workflow_integrations"][integration.workflow_name] = {
                    "services": applicable_services,
                    "integration_points": integration.integration_points,
                    "enhancement": integration.enhancement_description,
                }

        # Add usage patterns
        guidance["usage_patterns"] = {
            "task_initiation": [
                "Use zen_quote for motivation before complex tasks",
                "Use context_switch when changing projects",
            ],
            "stress_management": [
                "Use breathing_exercise during difficult debugging",
                "Use focus_timer for dedicated work sessions",
            ],
            "workflow_optimization": [
                "Use workflow_optimizer for process improvements",
                "Use project_memory to maintain context",
            ],
        }

        return guidance

    async def refresh_service_detection(self) -> Dict[str, Any]:
        """
        Force refresh of service detection and return updated status.

        Returns:
            Updated service status and recommendations
        """
        await self.detect_available_services(force_refresh=True)
        return self.generate_orchestrator_guidance()


# Global instance for the orchestrator
mcp_detector = MCPServiceDetector()


async def get_mcp_service_recommendations(
    workflow: str = None, context: str = None
) -> Dict[str, Any]:
    """
    Convenience function to get MCP service recommendations.

    Args:
        workflow: Optional workflow name
        context: Optional development context

    Returns:
        Service recommendations and guidance
    """
    await mcp_detector.detect_available_services()

    result = {
        "orchestrator_guidance": mcp_detector.generate_orchestrator_guidance(),
        "available_services": len(mcp_detector.available_services),
    }

    if workflow:
        result["workflow_recommendations"] = mcp_detector.get_workflow_recommendations(workflow)

    if context:
        result["context_services"] = [
            {"name": service.name, "tools": service.available_tools, "usage": service.usage_context}
            for service in mcp_detector.get_service_for_context(context)
        ]

    return result
