"""
Scaffolding Workflow - Orchestrates the scaffolding process with PM approval
"""

from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum
import asyncio

from ..agents.scaffolding_agent import ScaffoldingAgent, ScaffoldingRecommendation, DesignDocAnalysis
from ..core.memory import MemoryManager
from ..services.ai_trackdown import AITrackdownService
from ..services.notification_service import NotificationService


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ScaffoldingWorkflow:
    """
    Orchestrates the complete scaffolding workflow from design doc analysis to implementation.
    
    Workflow steps:
    1. Analyze design document
    2. Generate scaffolding recommendation
    3. Present recommendation to PM
    4. Handle PM approval/rejection
    5. Implement approved scaffolding
    6. Validate setup
    """
    
    def __init__(self, memory_manager: MemoryManager, trackdown_service: AITrackdownService, 
                 notification_service: NotificationService):
        self.scaffolding_agent = ScaffoldingAgent(memory_manager, trackdown_service)
        self.memory_manager = memory_manager
        self.trackdown_service = trackdown_service
        self.notification_service = notification_service
        
        # Workflow state
        self.current_recommendation: Optional[ScaffoldingRecommendation] = None
        self.current_analysis: Optional[DesignDocAnalysis] = None
        self.approval_status: ApprovalStatus = ApprovalStatus.PENDING
        self.workflow_id: Optional[str] = None
    
    async def execute_scaffolding_workflow(self, design_doc_path: str, project_path: str, 
                                         pm_contact: str) -> Dict[str, Any]:
        """
        Execute the complete scaffolding workflow.
        
        Args:
            design_doc_path: Path to the design document
            project_path: Path where to create the project
            pm_contact: PM contact for approval notifications
            
        Returns:
            Workflow result with status and details
        """
        try:
            # Create workflow tracking
            self.workflow_id = await self._create_workflow_tracking(design_doc_path, project_path)
            
            # Step 1: Analyze design document
            self.current_analysis = await self.scaffolding_agent.analyze_design_document(design_doc_path)
            await self._update_workflow_status("design_analysis_complete")
            
            # Step 2: Generate scaffolding recommendation
            self.current_recommendation = await self.scaffolding_agent.generate_scaffolding_recommendation(
                self.current_analysis
            )
            await self._update_workflow_status("recommendation_generated")
            
            # Step 3: Present recommendation to PM
            if self.current_recommendation.approval_required:
                pm_suggestion = await self.scaffolding_agent.suggest_to_pm(
                    self.current_recommendation, self.current_analysis
                )
                
                # Send notification to PM
                await self.notification_service.send_notification(
                    recipient=pm_contact,
                    subject=f"Scaffolding Approval Required: {self.current_recommendation.template_used}",
                    message=pm_suggestion,
                    priority="high"
                )
                
                await self._update_workflow_status("awaiting_pm_approval")
                
                # Wait for PM approval (with timeout)
                approval_result = await self._wait_for_pm_approval(timeout_minutes=60)
                
                if approval_result["status"] != "approved":
                    await self._update_workflow_status("workflow_terminated")
                    return {
                        "status": "failed",
                        "reason": f"PM approval {approval_result['status']}",
                        "details": approval_result.get("feedback", "")
                    }
            else:
                # Auto-approve non-controversial scaffolding
                await self._update_workflow_status("auto_approved")
            
            # Step 4: Implement scaffolding
            implementation_success = await self.scaffolding_agent.implement_scaffolding(
                self.current_recommendation, project_path
            )
            
            if not implementation_success:
                await self._update_workflow_status("implementation_failed")
                return {
                    "status": "failed",
                    "reason": "Scaffolding implementation failed",
                    "details": "Check logs for implementation errors"
                }
            
            await self._update_workflow_status("scaffolding_implemented")
            
            # Step 5: Validate setup
            validation_result = await self._validate_scaffolding_setup(project_path)
            
            if validation_result["success"]:
                await self._update_workflow_status("workflow_complete")
                
                # Notify PM of successful completion
                await self.notification_service.send_notification(
                    recipient=pm_contact,
                    subject=f"Scaffolding Complete: {self.current_recommendation.template_used}",
                    message=f"Project scaffolding completed successfully at {project_path}",
                    priority="medium"
                )
                
                return {
                    "status": "success",
                    "project_path": project_path,
                    "template_used": self.current_recommendation.template_used,
                    "validation_results": validation_result
                }
            else:
                await self._update_workflow_status("validation_failed")
                return {
                    "status": "failed",
                    "reason": "Setup validation failed",
                    "details": validation_result.get("errors", [])
                }
                
        except Exception as e:
            await self._update_workflow_status("workflow_error")
            return {
                "status": "error",
                "reason": str(e),
                "details": "Unexpected error during scaffolding workflow"
            }
    
    async def _create_workflow_tracking(self, design_doc_path: str, project_path: str) -> str:
        """Create workflow tracking ticket"""
        workflow_ticket = await self.trackdown_service.create_epic(
            title="Scaffolding Workflow",
            description=f"Automated scaffolding workflow for project at {project_path}",
            priority="high",
            labels=["scaffolding", "workflow", "automation"]
        )
        
        return workflow_ticket["id"]
    
    async def _update_workflow_status(self, status: str):
        """Update workflow status in tracking system"""
        if self.workflow_id:
            await self.trackdown_service.update_epic_status(
                self.workflow_id, 
                status,
                f"Workflow status: {status}"
            )
    
    async def _wait_for_pm_approval(self, timeout_minutes: int = 60) -> Dict[str, Any]:
        """
        Wait for PM approval with timeout.
        
        Args:
            timeout_minutes: Timeout in minutes
            
        Returns:
            Approval result with status and feedback
        """
        timeout_seconds = timeout_minutes * 60
        check_interval = 30  # Check every 30 seconds
        
        for _ in range(0, timeout_seconds, check_interval):
            # Check for approval in tracking system
            approval_status = await self._check_approval_status()
            
            if approval_status["status"] != "pending":
                return approval_status
            
            await asyncio.sleep(check_interval)
        
        # Timeout reached
        return {
            "status": "timeout",
            "feedback": f"No response from PM within {timeout_minutes} minutes"
        }
    
    async def _check_approval_status(self) -> Dict[str, Any]:
        """Check current approval status from tracking system"""
        # This would check the tracking system for PM approval
        # For now, return pending status
        return {
            "status": "pending",
            "feedback": None
        }
    
    async def _validate_scaffolding_setup(self, project_path: str) -> Dict[str, Any]:
        """
        Validate the scaffolding setup.
        
        Args:
            project_path: Path to the scaffolded project
            
        Returns:
            Validation result with success status and details
        """
        validation_results = {
            "success": True,
            "checks": {},
            "errors": []
        }
        
        project_dir = Path(project_path)
        
        # Check if project directory exists
        if not project_dir.exists():
            validation_results["success"] = False
            validation_results["errors"].append("Project directory does not exist")
            return validation_results
        
        # Validate project structure
        structure_check = self._validate_project_structure(project_dir)
        validation_results["checks"]["project_structure"] = structure_check
        
        if not structure_check["success"]:
            validation_results["success"] = False
            validation_results["errors"].extend(structure_check["errors"])
        
        # Validate configuration files
        config_check = self._validate_configuration_files(project_dir)
        validation_results["checks"]["configuration_files"] = config_check
        
        if not config_check["success"]:
            validation_results["success"] = False
            validation_results["errors"].extend(config_check["errors"])
        
        # Validate dependencies (if applicable)
        if self.current_recommendation:
            deps_check = self._validate_dependencies(project_dir)
            validation_results["checks"]["dependencies"] = deps_check
            
            if not deps_check["success"]:
                validation_results["success"] = False
                validation_results["errors"].extend(deps_check["errors"])
        
        return validation_results
    
    def _validate_project_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Validate project directory structure"""
        result = {
            "success": True,
            "missing_directories": [],
            "missing_files": [],
            "errors": []
        }
        
        if not self.current_recommendation:
            result["success"] = False
            result["errors"].append("No recommendation available for validation")
            return result
        
        # Check expected directories and files
        expected_structure = self.current_recommendation.project_structure
        
        def check_structure(base_path: Path, structure: Dict[str, Any], path_prefix: str = ""):
            for item_name, item_value in structure.items():
                item_path = base_path / item_name
                current_path = f"{path_prefix}/{item_name}" if path_prefix else item_name
                
                if isinstance(item_value, dict):
                    # Directory with subdirectories
                    if not item_path.exists():
                        result["missing_directories"].append(current_path)
                    else:
                        check_structure(item_path, item_value, current_path)
                elif isinstance(item_value, list):
                    # Directory with files
                    if not item_path.exists():
                        result["missing_directories"].append(current_path)
                    else:
                        for file_name in item_value:
                            if not file_name.endswith('/'):
                                file_path = item_path / file_name
                                if not file_path.exists():
                                    result["missing_files"].append(f"{current_path}/{file_name}")
        
        check_structure(project_dir, expected_structure)
        
        if result["missing_directories"] or result["missing_files"]:
            result["success"] = False
            result["errors"].append("Missing directories or files in project structure")
        
        return result
    
    def _validate_configuration_files(self, project_dir: Path) -> Dict[str, Any]:
        """Validate configuration files"""
        result = {
            "success": True,
            "missing_configs": [],
            "invalid_configs": [],
            "errors": []
        }
        
        # Check for common configuration files
        expected_configs = [
            "package.json",
            "pyproject.toml",
            "tsconfig.json",
            ".gitignore",
            "README.md"
        ]
        
        for config_file in expected_configs:
            config_path = project_dir / config_file
            if not config_path.exists():
                result["missing_configs"].append(config_file)
        
        # For now, just check existence
        # In a full implementation, we'd validate file contents
        
        if result["missing_configs"]:
            result["success"] = False
            result["errors"].append("Missing configuration files")
        
        return result
    
    def _validate_dependencies(self, project_dir: Path) -> Dict[str, Any]:
        """Validate dependencies installation"""
        result = {
            "success": True,
            "missing_dependencies": [],
            "errors": []
        }
        
        # Check for dependency files
        package_json = project_dir / "package.json"
        pyproject_toml = project_dir / "pyproject.toml"
        
        if package_json.exists():
            # Check for node_modules
            node_modules = project_dir / "node_modules"
            if not node_modules.exists():
                result["missing_dependencies"].append("node_modules")
        
        if pyproject_toml.exists():
            # Check for Python virtual environment indicators
            # This is a simplified check
            pass
        
        if result["missing_dependencies"]:
            result["success"] = False
            result["errors"].append("Dependencies not installed")
        
        return result
    
    async def handle_pm_feedback(self, workflow_id: str, feedback: str, decision: str) -> Dict[str, Any]:
        """
        Handle PM feedback on scaffolding recommendation.
        
        Args:
            workflow_id: Workflow identifier
            feedback: PM feedback text
            decision: PM decision (approve/reject/revise)
            
        Returns:
            Response to PM feedback
        """
        if decision.lower() == "approve":
            self.approval_status = ApprovalStatus.APPROVED
            await self._update_workflow_status("pm_approved")
            return {"status": "approved", "message": "Proceeding with scaffolding"}
        
        elif decision.lower() == "reject":
            self.approval_status = ApprovalStatus.REJECTED
            await self._update_workflow_status("pm_rejected")
            return {"status": "rejected", "message": "Scaffolding workflow terminated"}
        
        elif decision.lower() == "revise":
            self.approval_status = ApprovalStatus.NEEDS_REVISION
            await self._update_workflow_status("revision_requested")
            
            # Store feedback for revision
            await self.memory_manager.store_memory(
                agent_id=self.scaffolding_agent.agent_id,
                category="SCAFFOLDING_PATTERN",
                content=f"PM revision feedback: {feedback}",
                context={"workflow_id": workflow_id, "feedback": feedback}
            )
            
            return {"status": "revision_requested", "message": "Will revise recommendation based on feedback"}
        
        else:
            return {"status": "error", "message": "Invalid decision. Use approve/reject/revise"}