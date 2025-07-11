"""
Version Control Agent - Git and version management specialist for Claude PM Framework.

This agent specializes in:
1. Git branch management and operations
2. Semantic versioning and release management
3. Conflict resolution and merge operations
4. Branch strategy implementation
5. Version control workflow automation
6. Integration with quality gates and CI/CD
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

from ..core.base_agent import BaseAgent
from ..core.config import Config
from ..services.version_control import (
    GitOperationsManager,
    SemanticVersionManager,
    BranchStrategyManager,
    ConflictResolutionManager,
    GitBranchInfo,
    GitOperationResult,
    SemanticVersion,
    VersionBumpType,
    BranchStrategyType,
    BranchType,
    ConflictAnalysis,
    ResolutionStrategy,
)


@dataclass
class VersionControlConfig:
    """Configuration for Version Control Agent."""

    default_main_branch: str = "main"
    default_branch_strategy: str = "issue_driven"
    auto_merge_enabled: bool = True
    auto_cleanup_enabled: bool = True
    conflict_auto_resolution: bool = True
    require_qa_approval: bool = True
    version_file_auto_update: bool = True
    changelog_auto_generation: bool = True
    tag_creation_enabled: bool = True
    remote_sync_enabled: bool = True


@dataclass
class VersionControlOperation:
    """Represents a version control operation."""

    operation_id: str
    operation_type: str
    status: str = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    branch_before: Optional[str] = None
    branch_after: Optional[str] = None


class PMIntegrationInterface:
    """Interface for integrating with PM and other agents."""

    def __init__(self, agent, logger):
        self.agent = agent
        self.logger = logger

    async def request_qa_approval(
        self, branch_name: str, operation_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request QA approval for branch operations."""
        await self.agent.collaborate_with_pm(
            f"QA approval requested for {operation_type} on branch {branch_name}",
            context={
                "operation_type": operation_type,
                "branch_name": branch_name,
                "requires_qa": True,
                **context,
            },
            priority="high",
        )

        return {"approval_requested": True, "pending": True}

    async def notify_merge_completion(
        self, source_branch: str, target_branch: str, result: GitOperationResult
    ) -> None:
        """Notify PM of merge completion."""
        await self.agent.collaborate_with_pm(
            f"Branch merge completed: {source_branch} → {target_branch}",
            context={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "success": result.success,
                "execution_time": result.execution_time,
                "files_changed": result.files_changed,
            },
            priority="normal",
        )

    async def report_conflict_analysis(self, analysis: ConflictAnalysis) -> None:
        """Report conflict analysis to PM."""
        priority = "high" if analysis.conflict_severity in ["medium", "high"] else "normal"

        await self.agent.collaborate_with_pm(
            f"Merge conflicts detected: {analysis.total_conflicts} conflicts in {len(analysis.conflicted_files)} files",
            context={
                "total_conflicts": analysis.total_conflicts,
                "conflicted_files": analysis.conflicted_files,
                "auto_resolvable": analysis.auto_resolvable_count,
                "manual_required": analysis.manual_resolution_count,
                "severity": analysis.conflict_severity,
                "estimated_time": analysis.estimated_resolution_time,
            },
            priority=priority,
        )

    async def request_manual_conflict_resolution(
        self, file_path: str, guidance: Dict[str, Any]
    ) -> None:
        """Request manual conflict resolution assistance."""
        await self.agent.collaborate_with_pm(
            f"Manual conflict resolution needed for {file_path}",
            context={
                "file_path": file_path,
                "resolution_guidance": guidance,
                "requires_manual_intervention": True,
            },
            priority="high",
        )


class VersionControlAgent(BaseAgent):
    """
    Version Control Agent - Specialized agent for Git and version management.

    Responsibilities:
    1. Git branch management and operations
    2. Semantic versioning and release management
    3. Conflict resolution and merge operations
    4. Branch strategy implementation and enforcement
    5. Version control workflow automation
    6. Integration with quality gates and CI/CD pipelines
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Version Control Agent."""
        super().__init__(
            agent_id="version-control-agent",
            agent_type="version_control",
            capabilities=[
                "git_operations",
                "branch_management",
                "semantic_versioning",
                "conflict_resolution",
                "merge_operations",
                "branch_strategy_enforcement",
                "version_tagging",
                "changelog_generation",
                "workflow_automation",
                "quality_gate_integration",
                "pm_collaboration",
            ],
            config=config,
            tier="system",  # Core framework agent
        )

        # Initialize configuration
        self.vc_config = VersionControlConfig()
        if config and "version_control" in config:
            vc_config_dict = config["version_control"]
            for key, value in vc_config_dict.items():
                if hasattr(self.vc_config, key):
                    setattr(self.vc_config, key, value)

        # Initialize service managers (will be set in _initialize)
        self.git_manager: Optional[GitOperationsManager] = None
        self.version_manager: Optional[SemanticVersionManager] = None
        self.branch_strategy: Optional[BranchStrategyManager] = None
        self.conflict_resolver: Optional[ConflictResolutionManager] = None

        # Integration interfaces
        self.pm_integration = PMIntegrationInterface(self, self.logger)

        # Operation tracking
        self.active_operations: Dict[str, VersionControlOperation] = {}
        self.operation_history: List[VersionControlOperation] = []

        # Current project context
        self.current_project_root: Optional[str] = None
        self.current_branch_info: Optional[GitBranchInfo] = None

        self.logger.info("Version Control Agent initialized successfully")

    async def _initialize(self) -> None:
        """Initialize the Version Control Agent."""
        try:
            # Detect project root
            current_dir = Path.cwd()
            project_root = await self._find_git_repository(current_dir)

            if project_root:
                self.current_project_root = str(project_root)
                self.logger.info(f"Git repository detected: {project_root}")

                # Initialize service managers
                self.git_manager = GitOperationsManager(
                    project_root=self.current_project_root, logger=self.logger
                )

                self.version_manager = SemanticVersionManager(
                    project_root=self.current_project_root, logger=self.logger
                )

                self.branch_strategy = BranchStrategyManager(
                    project_root=self.current_project_root, logger=self.logger
                )

                self.conflict_resolver = ConflictResolutionManager(
                    project_root=self.current_project_root, logger=self.logger
                )

                # Get current branch info
                self.current_branch_info = self.git_manager.get_branch_info()

                # Report initialization to PM
                await self.collaborate_with_pm(
                    f"Version Control Agent initialized for Git repository: {project_root}",
                    context={
                        "project_root": self.current_project_root,
                        "current_branch": (
                            self.current_branch_info.name if self.current_branch_info else None
                        ),
                        "strategy": self.branch_strategy.get_current_strategy().strategy_type.value,
                    },
                    priority="normal",
                )

            else:
                self.logger.warning("No Git repository found in current directory")

            self.logger.info("Version Control Agent initialization complete")

        except Exception as e:
            self.logger.error(f"Error initializing Version Control Agent: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup Version Control Agent resources."""
        try:
            # Complete any pending operations
            await self._complete_pending_operations()

            # Save operation history if needed
            await self._save_operation_history()

            self.logger.info("Version Control Agent cleanup complete")

        except Exception as e:
            self.logger.error(f"Error cleaning up Version Control Agent: {e}")
            raise

    async def _execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """Execute Version Control Agent operations."""
        context = context or {}

        # Ensure we have a Git repository
        if not self.git_manager:
            raise ValueError("No Git repository initialized")

        # Branch management operations
        if operation == "create_branch":
            return await self.create_branch(
                branch_name=kwargs.get("branch_name") or context.get("branch_name"),
                branch_type=kwargs.get("branch_type") or context.get("branch_type", "issue"),
                ticket_id=kwargs.get("ticket_id") or context.get("ticket_id"),
                description=kwargs.get("description") or context.get("description"),
            )

        elif operation == "switch_branch":
            return await self.switch_branch(
                branch_name=kwargs.get("branch_name") or context.get("branch_name")
            )

        elif operation == "merge_branch":
            return await self.merge_branch(
                source_branch=kwargs.get("source_branch") or context.get("source_branch"),
                target_branch=kwargs.get("target_branch") or context.get("target_branch"),
                strategy=kwargs.get("strategy") or context.get("strategy", "auto"),
            )

        elif operation == "delete_branch":
            return await self.delete_branch(
                branch_name=kwargs.get("branch_name") or context.get("branch_name")
            )

        # Version management operations
        elif operation == "bump_version":
            return await self.bump_version(
                bump_type=kwargs.get("bump_type") or context.get("bump_type"),
                commit_messages=kwargs.get("commit_messages") or context.get("commit_messages", []),
            )

        elif operation == "create_release":
            return await self.create_release(
                version=kwargs.get("version") or context.get("version"),
                changelog=kwargs.get("changelog") or context.get("changelog", True),
            )

        # Conflict resolution operations
        elif operation == "resolve_conflicts":
            return await self.resolve_conflicts(
                strategy=kwargs.get("strategy") or context.get("strategy", "auto")
            )

        elif operation == "analyze_conflicts":
            return await self.analyze_conflicts()

        # Information operations
        elif operation == "get_branch_status":
            return await self.get_branch_status()

        elif operation == "get_version_info":
            return await self.get_version_info()

        elif operation == "get_repository_status":
            return await self.get_repository_status()

        # Branch strategy operations
        elif operation == "set_branch_strategy":
            return await self.set_branch_strategy(
                strategy_type=kwargs.get("strategy_type") or context.get("strategy_type")
            )

        elif operation == "validate_branch_name":
            return await self.validate_branch_name(
                branch_name=kwargs.get("branch_name") or context.get("branch_name")
            )

        # Cleanup operations
        elif operation == "cleanup_branches":
            return await self.cleanup_merged_branches()

        elif operation == "sync_with_remote":
            return await self.sync_with_remote(
                branch_name=kwargs.get("branch_name") or context.get("branch_name")
            )

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _find_git_repository(self, start_path: Path) -> Optional[Path]:
        """Find Git repository root starting from a path."""
        current_path = start_path.resolve()

        while current_path.parent != current_path:
            git_dir = current_path / ".git"
            if git_dir.exists():
                return current_path
            current_path = current_path.parent

        return None

    async def create_branch(
        self,
        branch_name: str,
        branch_type: str = "issue",
        ticket_id: Optional[str] = None,
        description: Optional[str] = None,
        base_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Git branch following branch strategy.

        Args:
            branch_name: Base name for the branch
            branch_type: Type of branch (issue, feature, enhancement, hotfix, epic)
            ticket_id: Optional ticket ID
            description: Optional description
            base_branch: Base branch to create from

        Returns:
            Operation result
        """
        operation_id = f"create_branch_{int(time.time())}"
        operation = VersionControlOperation(
            operation_id=operation_id, operation_type="create_branch", start_time=datetime.now()
        )
        self.active_operations[operation_id] = operation

        try:
            # Generate branch name using strategy
            if ticket_id:
                full_branch_name = self.branch_strategy.generate_branch_name(
                    branch_type=BranchType(branch_type),
                    ticket_id=ticket_id,
                    description=description,
                )
            else:
                full_branch_name = self.branch_strategy.generate_branch_name(
                    branch_type=BranchType(branch_type), description=branch_name
                )

            # Validate branch name
            is_valid, error_msg = self.branch_strategy.validate_branch_name(full_branch_name)
            if not is_valid:
                raise ValueError(f"Invalid branch name: {error_msg}")

            # Use strategy's main branch as default base
            if not base_branch:
                base_branch = self.branch_strategy.get_current_strategy().main_branch

            # Create the branch
            result = self.git_manager.create_branch(
                branch_name=full_branch_name,
                branch_type=branch_type,
                base_branch=base_branch,
                switch_to_branch=True,
            )

            operation.status = "completed" if result.success else "failed"
            operation.end_time = datetime.now()
            operation.result = {
                "success": result.success,
                "branch_name": full_branch_name,
                "git_result": result.__dict__,
            }

            if not result.success:
                operation.error = result.error

            # Update current branch info
            if result.success:
                self.current_branch_info = self.git_manager.get_branch_info(full_branch_name)

            return operation.result

        except Exception as e:
            operation.status = "failed"
            operation.end_time = datetime.now()
            operation.error = str(e)
            self.logger.error(f"Error creating branch: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.operation_history.append(operation)
            del self.active_operations[operation_id]

    async def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Switch to an existing branch.

        Args:
            branch_name: Name of branch to switch to

        Returns:
            Operation result
        """
        try:
            result = self.git_manager.switch_branch(branch_name)

            if result.success:
                self.current_branch_info = self.git_manager.get_branch_info(branch_name)

            return {
                "success": result.success,
                "message": result.message,
                "branch_before": result.branch_before,
                "branch_after": result.branch_after,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            self.logger.error(f"Error switching branch: {e}")
            return {"success": False, "error": str(e)}

    async def merge_branch(
        self, source_branch: str, target_branch: Optional[str] = None, strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        Merge a source branch into target branch with strategy validation.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into (auto-detected if None)
            strategy: Merge strategy (auto, manual, ours, theirs)

        Returns:
            Operation result
        """
        try:
            # Auto-detect target branch if not specified
            if not target_branch:
                target_branch = self.branch_strategy.get_merge_target(source_branch)

            # Check if merge requires QA approval
            if self.branch_strategy.requires_qa_approval(source_branch):
                qa_approval = await self.pm_integration.request_qa_approval(
                    source_branch, "merge", {"target_branch": target_branch, "strategy": strategy}
                )

                if qa_approval.get("pending"):
                    return {
                        "success": False,
                        "pending_qa_approval": True,
                        "message": "Merge pending QA approval",
                    }

            # Check for conflicts first
            conflicts = self.git_manager.detect_merge_conflicts(source_branch, target_branch)

            if conflicts["has_conflicts"] and strategy == "auto":
                # Attempt automatic conflict resolution
                conflict_analysis = self.conflict_resolver.detect_conflicts()

                if conflict_analysis.auto_resolvable_count > 0:
                    await self.pm_integration.report_conflict_analysis(conflict_analysis)

                    # Try auto-resolution
                    resolve_result = await self.resolve_conflicts("auto")
                    if not resolve_result.get("success"):
                        return {
                            "success": False,
                            "conflicts_detected": True,
                            "manual_resolution_required": True,
                            "conflict_analysis": conflict_analysis.__dict__,
                        }
                else:
                    await self.pm_integration.report_conflict_analysis(conflict_analysis)
                    return {
                        "success": False,
                        "conflicts_detected": True,
                        "manual_resolution_required": True,
                        "conflict_analysis": conflict_analysis.__dict__,
                    }

            # Get merge strategy from branch strategy
            merge_strategy = self.branch_strategy.get_merge_strategy(source_branch)

            # Perform the merge
            result = self.git_manager.merge_branch(
                source_branch=source_branch,
                target_branch=target_branch,
                merge_strategy=merge_strategy,
                delete_source=self.branch_strategy.should_delete_after_merge(source_branch),
            )

            # Notify PM of completion
            await self.pm_integration.notify_merge_completion(source_branch, target_branch, result)

            # Update current branch info
            if result.success:
                self.current_branch_info = self.git_manager.get_branch_info()

            return {
                "success": result.success,
                "message": result.message,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "merge_strategy": merge_strategy,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            self.logger.error(f"Error merging branch: {e}")
            return {"success": False, "error": str(e)}

    async def delete_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Delete a Git branch safely.

        Args:
            branch_name: Name of branch to delete

        Returns:
            Operation result
        """
        try:
            current_branch = self.git_manager.get_current_branch()

            # Cannot delete current branch
            if branch_name == current_branch:
                return {"success": False, "error": "Cannot delete current branch"}

            # Check if branch has been merged
            strategy = self.branch_strategy.get_current_strategy()
            main_branch = strategy.main_branch

            # TODO: Add merge check logic

            # Delete local branch
            result = self.git_manager._run_git_command(["branch", "-d", branch_name], check=False)

            success = result.returncode == 0

            if success:
                # Try to delete remote branch
                remote_result = self.git_manager._run_git_command(
                    ["push", "origin", "--delete", branch_name], check=False
                )

                return {
                    "success": True,
                    "message": f"Branch {branch_name} deleted successfully",
                    "local_deleted": True,
                    "remote_deleted": remote_result.returncode == 0,
                }
            else:
                return {"success": False, "error": result.stderr or "Failed to delete branch"}

        except Exception as e:
            self.logger.error(f"Error deleting branch: {e}")
            return {"success": False, "error": str(e)}

    async def bump_version(
        self, bump_type: Optional[str] = None, commit_messages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Bump version based on semantic versioning rules.

        Args:
            bump_type: Type of bump (major, minor, patch, auto)
            commit_messages: Recent commit messages for analysis

        Returns:
            Operation result with new version
        """
        try:
            current_version = self.version_manager.get_current_version()

            if not current_version:
                return {"success": False, "error": "No current version found in project files"}

            # Auto-detect bump type if not specified
            if bump_type == "auto" or not bump_type:
                if not commit_messages:
                    # Get recent commit messages
                    result = self.git_manager._run_git_command(
                        ["log", "--oneline", "-10", "--format=%s"]
                    )
                    commit_messages = result.stdout.strip().split("\n")

                suggested_bump, confidence = self.version_manager.suggest_version_bump(
                    commit_messages
                )
                bump_type = suggested_bump.value

            # Perform version bump
            new_version = self.version_manager.bump_version(
                current_version, VersionBumpType(bump_type)
            )

            # Update version files
            update_results = self.version_manager.update_version_files(new_version)

            # Update changelog if enabled
            changelog_updated = False
            if self.vc_config.changelog_auto_generation and commit_messages:
                changelog_updated = self.version_manager.update_changelog(
                    new_version, commit_messages
                )

            return {
                "success": True,
                "previous_version": str(current_version),
                "new_version": str(new_version),
                "bump_type": bump_type,
                "files_updated": update_results,
                "changelog_updated": changelog_updated,
            }

        except Exception as e:
            self.logger.error(f"Error bumping version: {e}")
            return {"success": False, "error": str(e)}

    async def create_release(
        self, version: Optional[str] = None, changelog: bool = True
    ) -> Dict[str, Any]:
        """
        Create a release with version tagging.

        Args:
            version: Version to release (auto-detected if None)
            changelog: Whether to update changelog

        Returns:
            Operation result
        """
        try:
            if not version:
                current_version = self.version_manager.get_current_version()
                if not current_version:
                    return {"success": False, "error": "No version specified or found"}
                version = str(current_version)

            # Create Git tag
            tag_name = f"v{version}"
            result = self.git_manager._run_git_command(
                ["tag", "-a", tag_name, "-m", f"Release version {version}"]
            )

            # Push tag to remote
            push_result = self.git_manager._run_git_command(
                ["push", "origin", tag_name], check=False
            )

            return {
                "success": True,
                "version": version,
                "tag_name": tag_name,
                "tag_created": True,
                "tag_pushed": push_result.returncode == 0,
            }

        except Exception as e:
            self.logger.error(f"Error creating release: {e}")
            return {"success": False, "error": str(e)}

    async def resolve_conflicts(self, strategy: str = "auto") -> Dict[str, Any]:
        """
        Resolve merge conflicts using specified strategy.

        Args:
            strategy: Resolution strategy (auto, manual, ours, theirs)

        Returns:
            Operation result
        """
        try:
            # Detect conflicts
            analysis = self.conflict_resolver.detect_conflicts()

            if analysis.total_conflicts == 0:
                return {"success": True, "message": "No conflicts detected"}

            # Report to PM
            await self.pm_integration.report_conflict_analysis(analysis)

            if strategy == "auto":
                # Attempt automatic resolution
                resolutions = self.conflict_resolver.resolve_conflicts_automatically(
                    analysis.file_conflicts, ResolutionStrategy.AUTO_MERGE
                )

                successful_resolutions = [r for r in resolutions if r.success]
                failed_resolutions = [r for r in resolutions if not r.success]

                # Request manual intervention for failed resolutions
                for resolution in failed_resolutions:
                    if resolution.manual_intervention_required:
                        guidance = self.conflict_resolver.get_resolution_guidance(
                            resolution.file_path
                        )
                        await self.pm_integration.request_manual_conflict_resolution(
                            resolution.file_path, guidance
                        )

                return {
                    "success": len(failed_resolutions) == 0,
                    "auto_resolved": len(successful_resolutions),
                    "manual_required": len(failed_resolutions),
                    "resolutions": [r.__dict__ for r in resolutions],
                }

            else:
                # Manual or specific strategy
                return {
                    "success": False,
                    "message": f"Strategy '{strategy}' requires manual implementation",
                    "conflict_analysis": analysis.__dict__,
                }

        except Exception as e:
            self.logger.error(f"Error resolving conflicts: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_conflicts(self) -> Dict[str, Any]:
        """
        Analyze current merge conflicts.

        Returns:
            Conflict analysis
        """
        try:
            analysis = self.conflict_resolver.detect_conflicts()
            report = self.conflict_resolver.generate_resolution_report(analysis)

            return {"success": True, "analysis": analysis.__dict__, "report": report}

        except Exception as e:
            self.logger.error(f"Error analyzing conflicts: {e}")
            return {"success": False, "error": str(e)}

    async def get_branch_status(self) -> Dict[str, Any]:
        """Get current branch status and information."""
        try:
            if not self.current_branch_info:
                self.current_branch_info = self.git_manager.get_branch_info()

            return {
                "success": True,
                "current_branch": self.current_branch_info.__dict__,
                "strategy": self.branch_strategy.get_current_strategy().strategy_type.value,
                "working_directory_clean": self.git_manager.is_working_directory_clean(),
            }

        except Exception as e:
            self.logger.error(f"Error getting branch status: {e}")
            return {"success": False, "error": str(e)}

    async def get_version_info(self) -> Dict[str, Any]:
        """Get current version information."""
        try:
            current_version = self.version_manager.get_current_version()
            version_history = self.version_manager.get_version_history()

            return {
                "success": True,
                "current_version": str(current_version) if current_version else None,
                "version_history": [str(v) for v in version_history[:10]],  # Last 10 versions
            }

        except Exception as e:
            self.logger.error(f"Error getting version info: {e}")
            return {"success": False, "error": str(e)}

    async def get_repository_status(self) -> Dict[str, Any]:
        """Get comprehensive repository status."""
        try:
            repo_status = self.git_manager.get_repository_status()

            return {"success": True, "repository_status": repo_status}

        except Exception as e:
            self.logger.error(f"Error getting repository status: {e}")
            return {"success": False, "error": str(e)}

    async def set_branch_strategy(self, strategy_type: str) -> Dict[str, Any]:
        """Set the branch strategy for the project."""
        try:
            strategy_enum = BranchStrategyType(strategy_type)
            success = self.branch_strategy.set_strategy(strategy_enum)

            return {
                "success": success,
                "strategy_type": strategy_type,
                "message": (
                    f"Branch strategy set to {strategy_type}"
                    if success
                    else "Failed to set strategy"
                ),
            }

        except Exception as e:
            self.logger.error(f"Error setting branch strategy: {e}")
            return {"success": False, "error": str(e)}

    async def validate_branch_name(self, branch_name: str) -> Dict[str, Any]:
        """Validate a branch name against current strategy."""
        try:
            is_valid, message = self.branch_strategy.validate_branch_name(branch_name)

            return {
                "success": True,
                "valid": is_valid,
                "message": message,
                "branch_name": branch_name,
            }

        except Exception as e:
            self.logger.error(f"Error validating branch name: {e}")
            return {"success": False, "error": str(e)}

    async def cleanup_merged_branches(self) -> Dict[str, Any]:
        """Clean up branches that have been merged."""
        try:
            strategy = self.branch_strategy.get_current_strategy()
            result = self.git_manager.cleanup_merged_branches(strategy.main_branch)

            return {
                "success": result.success,
                "message": result.message,
                "cleaned_branches": result.output,
            }

        except Exception as e:
            self.logger.error(f"Error cleaning up branches: {e}")
            return {"success": False, "error": str(e)}

    async def sync_with_remote(self, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """Sync local branch with remote."""
        try:
            result = self.git_manager.sync_with_remote(branch_name)

            return {
                "success": result.success,
                "message": result.message,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            self.logger.error(f"Error syncing with remote: {e}")
            return {"success": False, "error": str(e)}

    async def _complete_pending_operations(self) -> None:
        """Complete any pending operations."""
        for operation in self.active_operations.values():
            if operation.status == "pending":
                operation.status = "cancelled"
                operation.end_time = datetime.now()
                operation.error = "Operation cancelled during cleanup"

    async def _save_operation_history(self) -> None:
        """Save operation history for persistence."""
        # This would implement persistence logic
        self.logger.debug("Operation history save requested (not implemented)")

    def _should_notify_pm(self, operation: str, result: Any) -> bool:
        """Determine if PM should be notified of operation completion."""
        # Notify PM for major operations
        major_operations = [
            "create_branch",
            "merge_branch",
            "delete_branch",
            "bump_version",
            "create_release",
            "resolve_conflicts",
        ]
        return operation in major_operations
