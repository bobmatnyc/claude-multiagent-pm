"""
Test suite for the Technical Enforcement Layer (FWK-003)
Tests delegation constraints, file access control, and violation monitoring.
"""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from claude_pm.core.enforcement import (
    EnforcementEngine,
    DelegationEnforcer,
    AgentCapabilityManager,
    ViolationMonitor,
    FileClassifier,
    Agent,
    Action,
    AgentPermissions,
    ConstraintViolation,
    ValidationResult,
    AgentType,
    ActionType,
    ViolationSeverity,
    FileCategory,
    get_enforcement_engine,
    enforce_file_access,
    validate_agent_action,
)


class TestFileClassifier:
    """Test file classification for permission enforcement."""

    def test_source_code_classification(self):
        """Test classification of source code files."""
        assert FileClassifier.classify_file("test.py") == FileCategory.SOURCE_CODE
        assert FileClassifier.classify_file("app.js") == FileCategory.SOURCE_CODE
        assert FileClassifier.classify_file("main.ts") == FileCategory.SOURCE_CODE
        assert FileClassifier.classify_file("Component.jsx") == FileCategory.SOURCE_CODE
        assert FileClassifier.classify_file("utils.java") == FileCategory.SOURCE_CODE

    def test_configuration_classification(self):
        """Test classification of configuration files."""
        assert FileClassifier.classify_file("Dockerfile") == FileCategory.CONFIGURATION
        assert FileClassifier.classify_file("config.yml") == FileCategory.CONFIGURATION
        assert FileClassifier.classify_file("package.json") == FileCategory.CONFIGURATION
        assert FileClassifier.classify_file("pyproject.toml") == FileCategory.CONFIGURATION
        assert FileClassifier.classify_file("requirements.txt") == FileCategory.CONFIGURATION
        assert FileClassifier.classify_file("deploy.sh") == FileCategory.CONFIGURATION

    def test_test_files_classification(self):
        """Test classification of test files."""
        assert FileClassifier.classify_file("test_main.py") == FileCategory.TEST_FILES
        assert FileClassifier.classify_file("utils_test.py") == FileCategory.TEST_FILES
        assert FileClassifier.classify_file("app.test.js") == FileCategory.TEST_FILES
        assert FileClassifier.classify_file("component.spec.ts") == FileCategory.TEST_FILES
        assert FileClassifier.classify_file("tests/integration.py") == FileCategory.TEST_FILES

    def test_documentation_classification(self):
        """Test classification of documentation files."""
        assert FileClassifier.classify_file("README.md") == FileCategory.DOCUMENTATION
        assert FileClassifier.classify_file("CHANGELOG.md") == FileCategory.DOCUMENTATION
        assert FileClassifier.classify_file("docs.rst") == FileCategory.DOCUMENTATION
        assert FileClassifier.classify_file("notes.txt") == FileCategory.DOCUMENTATION

    def test_project_management_classification(self):
        """Test classification of project management files."""
        assert FileClassifier.classify_file("CLAUDE.md") == FileCategory.PROJECT_MANAGEMENT
        assert FileClassifier.classify_file("BACKLOG.md") == FileCategory.PROJECT_MANAGEMENT
        assert (
            FileClassifier.classify_file("trackdown/issue-001.md")
            == FileCategory.PROJECT_MANAGEMENT
        )
        assert FileClassifier.classify_file("STATUS-REPORT.md") == FileCategory.PROJECT_MANAGEMENT

    def test_scaffolding_classification(self):
        """Test classification of scaffolding files."""
        assert FileClassifier.classify_file("api.template") == FileCategory.SCAFFOLDING
        assert FileClassifier.classify_file("templates/component.js") == FileCategory.SCAFFOLDING
        assert FileClassifier.classify_file("openapi.yml") == FileCategory.SCAFFOLDING
        assert FileClassifier.classify_file("swagger-spec.yml") == FileCategory.SCAFFOLDING

    def test_research_docs_classification(self):
        """Test classification of research documentation files."""
        assert FileClassifier.classify_file("research/analysis.md") == FileCategory.RESEARCH_DOCS
        assert (
            FileClassifier.classify_file("docs/research/tech-eval.md") == FileCategory.RESEARCH_DOCS
        )
        assert (
            FileClassifier.classify_file("investigation/findings.md") == FileCategory.RESEARCH_DOCS
        )


class TestAgentCapabilityManager:
    """Test agent capability and permission management."""

    @pytest.fixture
    def capability_manager(self):
        """Create capability manager for testing."""
        return AgentCapabilityManager()

    def test_orchestrator_permissions(self, capability_manager):
        """Test orchestrator agent permissions."""
        permissions = capability_manager.get_agent_permissions(AgentType.ORCHESTRATOR)

        # Should be allowed to access PM files
        assert FileCategory.PROJECT_MANAGEMENT in permissions.allowed_file_categories
        assert FileCategory.DOCUMENTATION in permissions.allowed_file_categories

        # Should be forbidden from accessing code files
        assert FileCategory.SOURCE_CODE in permissions.forbidden_file_categories
        assert FileCategory.CONFIGURATION in permissions.forbidden_file_categories
        assert FileCategory.TEST_FILES in permissions.forbidden_file_categories

        # Should be able to delegate
        assert permissions.can_delegate is True
        assert permissions.max_parallel_instances == 1

    def test_engineer_permissions(self, capability_manager):
        """Test engineer agent permissions."""
        permissions = capability_manager.get_agent_permissions(AgentType.ENGINEER)

        # Should only be allowed to access source code
        assert FileCategory.SOURCE_CODE in permissions.allowed_file_categories

        # Should be forbidden from other file types
        assert FileCategory.PROJECT_MANAGEMENT in permissions.forbidden_file_categories
        assert FileCategory.CONFIGURATION in permissions.forbidden_file_categories
        assert FileCategory.TEST_FILES in permissions.forbidden_file_categories

        # Multiple engineers allowed
        assert permissions.max_parallel_instances == 5
        assert permissions.can_delegate is False

    def test_qa_permissions(self, capability_manager):
        """Test QA agent permissions."""
        permissions = capability_manager.get_agent_permissions(AgentType.QA)

        # Should only be allowed to access test files
        assert FileCategory.TEST_FILES in permissions.allowed_file_categories

        # Should be forbidden from other file types
        assert FileCategory.SOURCE_CODE in permissions.forbidden_file_categories
        assert FileCategory.PROJECT_MANAGEMENT in permissions.forbidden_file_categories

        assert permissions.max_parallel_instances == 1
        assert permissions.can_delegate is False

    def test_operations_permissions(self, capability_manager):
        """Test operations agent permissions."""
        permissions = capability_manager.get_agent_permissions(AgentType.OPERATIONS)

        # Should only be allowed to access configuration files
        assert FileCategory.CONFIGURATION in permissions.allowed_file_categories

        # Should be forbidden from other file types
        assert FileCategory.SOURCE_CODE in permissions.forbidden_file_categories
        assert FileCategory.PROJECT_MANAGEMENT in permissions.forbidden_file_categories

        assert permissions.max_parallel_instances == 1
        assert permissions.can_delegate is False

    def test_validate_orchestrator_code_access(self, capability_manager):
        """Test critical violation: orchestrator accessing source code."""
        orchestrator = Agent(agent_id="test-orchestrator", agent_type=AgentType.ORCHESTRATOR)

        action = Action(
            action_type=ActionType.WRITE, resource_path=Path("main.py"), agent=orchestrator
        )

        result = capability_manager.validate_agent_action(orchestrator, action)

        assert result.is_valid is False
        assert len(result.violations) > 0

        # Should have critical violation for orchestrator accessing code
        critical_violations = [
            v for v in result.violations if v.severity == ViolationSeverity.CRITICAL
        ]
        assert len(critical_violations) > 0
        assert "CRITICAL VIOLATION" in critical_violations[0].description

    def test_validate_engineer_code_access(self, capability_manager):
        """Test engineer accessing source code (should be allowed)."""
        engineer = Agent(agent_id="test-engineer", agent_type=AgentType.ENGINEER)

        action = Action(action_type=ActionType.WRITE, resource_path=Path("main.py"), agent=engineer)

        result = capability_manager.validate_agent_action(engineer, action)

        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_validate_qa_test_access(self, capability_manager):
        """Test QA agent accessing test files (should be allowed)."""
        qa_agent = Agent(agent_id="test-qa", agent_type=AgentType.QA)

        action = Action(
            action_type=ActionType.WRITE, resource_path=Path("test_main.py"), agent=qa_agent
        )

        result = capability_manager.validate_agent_action(qa_agent, action)

        assert result.is_valid is True
        assert len(result.violations) == 0


class TestDelegationEnforcer:
    """Test delegation constraint enforcement."""

    @pytest.fixture
    def delegation_enforcer(self):
        """Create delegation enforcer for testing."""
        capability_manager = AgentCapabilityManager()
        return DelegationEnforcer(capability_manager)

    def test_file_access_validation(self, delegation_enforcer):
        """Test file access validation."""
        # Orchestrator should not access source code
        assert delegation_enforcer.validate_file_access("orchestrator", "main.py") is False

        # Engineer should access source code
        assert delegation_enforcer.validate_file_access("engineer", "main.py") is True

        # QA should access test files
        assert delegation_enforcer.validate_file_access("qa", "test_main.py") is True

        # QA should not access source code
        assert delegation_enforcer.validate_file_access("qa", "main.py") is False

    def test_circular_delegation_detection(self, delegation_enforcer):
        """Test circular delegation detection."""
        orchestrator = Agent("orch-1", AgentType.ORCHESTRATOR)
        engineer = Agent("eng-1", AgentType.ENGINEER)
        qa = Agent("qa-1", AgentType.QA)

        # Normal chain should be fine
        normal_chain = [orchestrator, engineer, qa]
        assert delegation_enforcer.detect_circular_delegation(normal_chain) is False

        # Circular chain should be detected
        circular_chain = [orchestrator, engineer, qa, orchestrator]
        assert delegation_enforcer.detect_circular_delegation(circular_chain) is True

    def test_delegation_chain_management(self, delegation_enforcer):
        """Test delegation chain tracking."""
        orchestrator = Agent("orch-1", AgentType.ORCHESTRATOR)
        engineer = Agent("eng-1", AgentType.ENGINEER)

        chain_id = "test-chain-1"

        # Start chain
        delegation_enforcer.start_delegation_chain(orchestrator, chain_id)
        assert chain_id in delegation_enforcer.delegation_chains

        # Add to chain
        success = delegation_enforcer.add_to_delegation_chain(chain_id, engineer)
        assert success is True

        # Try to add orchestrator again (should fail due to circular delegation)
        success = delegation_enforcer.add_to_delegation_chain(chain_id, orchestrator)
        assert success is False

        # End chain
        chain = delegation_enforcer.end_delegation_chain(chain_id)
        assert len(chain) == 2
        assert chain_id not in delegation_enforcer.delegation_chains


class TestViolationMonitor:
    """Test violation monitoring and reporting."""

    @pytest.fixture
    def violation_monitor(self):
        """Create violation monitor for testing."""
        return ViolationMonitor()

    def test_track_violation(self, violation_monitor):
        """Test violation tracking."""
        agent = Agent("test-agent", AgentType.ORCHESTRATOR)
        action = Action(ActionType.WRITE, Path("main.py"), agent)

        violation = ConstraintViolation(
            violation_id="test-violation",
            agent=agent,
            action=action,
            violation_type="test_violation",
            severity=ViolationSeverity.HIGH,
            description="Test violation",
        )

        violation_monitor.track_violation(violation)

        assert len(violation_monitor.violations) == 1
        assert violation_monitor.violations[0] == violation

        # High severity should create alert
        alerts = violation_monitor.get_violation_alerts()
        assert len(alerts) == 1
        assert alerts[0].violation == violation

    def test_alert_acknowledgment(self, violation_monitor):
        """Test alert acknowledgment."""
        agent = Agent("test-agent", AgentType.ORCHESTRATOR)
        action = Action(ActionType.WRITE, Path("main.py"), agent)

        violation = ConstraintViolation(
            violation_id="test-violation",
            agent=agent,
            action=action,
            violation_type="test_violation",
            severity=ViolationSeverity.CRITICAL,
            description="Critical test violation",
        )

        violation_monitor.track_violation(violation)

        # Get unacknowledged alerts
        alerts = violation_monitor.get_violation_alerts()
        assert len(alerts) == 1

        # Acknowledge alert
        alert_id = alerts[0].alert_id
        success = violation_monitor.acknowledge_alert(alert_id)
        assert success is True

        # Should have no unacknowledged alerts now
        alerts = violation_monitor.get_violation_alerts()
        assert len(alerts) == 0

    def test_violation_report_generation(self, violation_monitor):
        """Test violation report generation."""
        agent = Agent("test-agent", AgentType.ORCHESTRATOR)
        action = Action(ActionType.WRITE, Path("main.py"), agent)

        # Add multiple violations with different severities
        for i, severity in enumerate(
            [ViolationSeverity.LOW, ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]
        ):
            violation = ConstraintViolation(
                violation_id=f"test-violation-{i}",
                agent=agent,
                action=action,
                violation_type="test_violation",
                severity=severity,
                description=f"Test violation {i}",
            )
            violation_monitor.track_violation(violation)

        # Generate report
        report = violation_monitor.generate_violation_report()

        assert report.report_id.startswith("report-")
        assert len(report.violations) == 3
        assert report.summary["total_violations"] == 3
        assert report.summary["by_severity"]["critical"] == 1
        assert report.summary["by_severity"]["high"] == 1
        assert report.summary["by_severity"]["low"] == 1

        # Should have recommendations for critical violations
        assert len(report.recommendations) > 0
        assert any("critical" in rec.lower() for rec in report.recommendations)


class TestEnforcementEngine:
    """Test the main enforcement engine integration."""

    @pytest.fixture
    def enforcement_engine(self):
        """Create enforcement engine for testing."""
        return EnforcementEngine()

    def test_validate_action_integration(self, enforcement_engine):
        """Test complete action validation pipeline."""
        # Test orchestrator trying to write code (should fail)
        orchestrator = Agent("orch-1", AgentType.ORCHESTRATOR)
        code_action = Action(ActionType.WRITE, Path("main.py"), orchestrator)

        result = enforcement_engine.validate_action(orchestrator, code_action)

        assert result.is_valid is False
        assert len(result.violations) > 0

        # Should track violations
        assert len(enforcement_engine.violation_monitor.violations) > 0

    def test_enforce_file_access_convenience(self, enforcement_engine):
        """Test convenience file access enforcement method."""
        # Orchestrator should not write to source code
        assert enforcement_engine.enforce_file_access("orchestrator", "main.py", "write") is False

        # Engineer should write to source code
        assert enforcement_engine.enforce_file_access("engineer", "main.py", "write") is True

        # QA should write to test files
        assert enforcement_engine.enforce_file_access("qa", "test_main.py", "write") is True

    def test_enforcement_statistics(self, enforcement_engine):
        """Test enforcement statistics collection."""
        # Generate some violations
        enforcement_engine.enforce_file_access("orchestrator", "main.py", "write")
        enforcement_engine.enforce_file_access("qa", "main.py", "write")

        stats = enforcement_engine.get_enforcement_stats()

        assert "enforcement_enabled" in stats
        assert "total_violations" in stats
        assert "active_alerts" in stats
        assert "critical_violations" in stats
        assert "recent_violations" in stats

        assert stats["total_violations"] > 0
        assert len(stats["recent_violations"]) > 0

    def test_enforcement_enable_disable(self, enforcement_engine):
        """Test enforcement enable/disable functionality."""
        # Initially enabled
        assert enforcement_engine.enabled is True

        # Disable enforcement
        enforcement_engine.disable_enforcement()
        assert enforcement_engine.enabled is False

        # Validation should pass when disabled
        orchestrator = Agent("orch-1", AgentType.ORCHESTRATOR)
        code_action = Action(ActionType.WRITE, Path("main.py"), orchestrator)
        result = enforcement_engine.validate_action(orchestrator, code_action)
        assert result.is_valid is True

        # Re-enable enforcement
        enforcement_engine.enable_enforcement()
        assert enforcement_engine.enabled is True

        # Validation should fail again
        result = enforcement_engine.validate_action(orchestrator, code_action)
        assert result.is_valid is False


class TestConvenienceFunctions:
    """Test convenience functions for enforcement."""

    def test_global_enforcement_engine(self):
        """Test global enforcement engine access."""
        engine1 = get_enforcement_engine()
        engine2 = get_enforcement_engine()

        # Should be the same instance
        assert engine1 is engine2
        assert isinstance(engine1, EnforcementEngine)

    def test_enforce_file_access_function(self):
        """Test global enforce_file_access function."""
        # Should delegate to global enforcement engine
        assert enforce_file_access("engineer", "main.py", "write") is True
        assert enforce_file_access("orchestrator", "main.py", "write") is False

    def test_validate_agent_action_function(self):
        """Test global validate_agent_action function."""
        # Should return ValidationResult
        result = validate_agent_action("orchestrator", "write", "main.py", "test-agent")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.violations) > 0


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_orchestrator_delegation_scenario(self):
        """Test orchestrator attempting to write code instead of delegating."""
        engine = get_enforcement_engine()

        # Orchestrator tries to write source code
        result = validate_agent_action("orchestrator", "write", "src/main.py")

        assert result.is_valid is False
        assert any("CRITICAL VIOLATION" in v.description for v in result.violations)
        assert any("delegate" in v.resolution_guidance.lower() for v in result.violations)

    def test_cross_agent_file_access_scenario(self):
        """Test various agents accessing different file types."""
        scenarios = [
            # (agent_type, file_path, action, expected_result)
            ("orchestrator", "CLAUDE.md", "write", True),  # PM files OK
            ("orchestrator", "main.py", "write", False),  # Code files forbidden
            ("engineer", "main.py", "write", True),  # Code files OK
            ("engineer", "CLAUDE.md", "write", False),  # PM files forbidden
            ("qa", "test_main.py", "write", True),  # Test files OK
            ("qa", "main.py", "write", False),  # Code files forbidden
            ("operations", "Dockerfile", "write", True),  # Config files OK
            ("operations", "main.py", "write", False),  # Code files forbidden
            ("researcher", "docs/analysis.md", "write", True),  # Research docs OK
            ("researcher", "main.py", "write", False),  # Code files forbidden
            ("architect", "api-spec.yml", "write", True),  # Scaffolding OK
            ("architect", "main.py", "write", False),  # Code files forbidden
        ]

        for agent_type, file_path, action, expected in scenarios:
            result = enforce_file_access(agent_type, file_path, action)
            assert (
                result == expected
            ), f"Failed: {agent_type} {action} {file_path} expected {expected}, got {result}"

    def test_multi_agent_parallel_execution_scenario(self):
        """Test multiple agents working in parallel with enforcement."""
        engine = get_enforcement_engine()

        # Simulate multiple agents working simultaneously
        agents_and_files = [
            ("engineer", "src/main.py", "write"),
            ("qa", "tests/test_main.py", "write"),
            ("operations", "docker/Dockerfile", "write"),
            ("researcher", "docs/research.md", "write"),
            ("architect", "api/spec.yml", "write"),
        ]

        results = []
        for agent_type, file_path, action in agents_and_files:
            result = validate_agent_action(agent_type, action, file_path)
            results.append((agent_type, result.is_valid))

        # All should be valid
        for agent_type, is_valid in results:
            assert is_valid, f"Agent {agent_type} should be authorized for their file type"

        # Check that violations are properly tracked
        stats = engine.get_enforcement_stats()
        assert "enforcement_enabled" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
