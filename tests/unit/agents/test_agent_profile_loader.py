#!/usr/bin/env python3
"""
Test Suite for Agent Profile Loader
===================================

Comprehensive test suite for the AgentProfileLoader service and related components.
Tests all aspects of agent profile loading, improved prompt integration, and
Task Tool subprocess creation enhancement.

Framework Version: 014
Test Implementation: 2025-07-15
"""

import asyncio
import json
import pytest
import pytest_asyncio
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Import test target
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.services.agent_profile_loader import (
    AgentProfileLoader,
    AgentProfile,
    ImprovedPrompt,
    ProfileTier,
    ProfileStatus,
    create_agent_profile_loader
)
from claude_pm.services.task_tool_profile_integration import (
    TaskToolProfileIntegration,
    TaskToolRequest,
    TaskToolResponse,
    create_task_tool_integration
)
from claude_pm.core.config import Config


class TestAgentProfileLoader:
    """Test suite for AgentProfileLoader."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        # Return a dictionary instead of Mock object since Config expects a dict
        return {}
    
    @pytest.fixture
    def profile_loader(self, temp_dir, mock_config):
        """Create agent profile loader for testing."""
        # Create a fake framework path with agent-roles directory
        framework_path = temp_dir / 'framework'
        agent_roles_dir = framework_path / 'agent-roles'
        agent_roles_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock working directory, framework path, and user home to use temp dir
        with patch('claude_pm.services.agent_profile_loader.os.getcwd', return_value=str(temp_dir)), \
             patch.object(AgentProfileLoader, '_detect_framework_path', return_value=framework_path), \
             patch('claude_pm.services.agent_profile_loader.profile_manager.Path.home', return_value=temp_dir):
            loader = AgentProfileLoader(mock_config)
            
            # Create test directory structure
            for tier in ['project-specific', 'user-defined', 'system']:
                tier_dir = temp_dir / '.claude-pm' / 'agents' / tier
                tier_dir.mkdir(parents=True, exist_ok=True)
            
            # Create training directory
            training_dir = temp_dir / '.claude-pm' / 'training' / 'agent-prompts'
            training_dir.mkdir(parents=True, exist_ok=True)
            
            yield loader
    
    @pytest.fixture
    def sample_profile_content(self):
        """Create sample profile content."""
        return """# Engineer Agent Profile

## Role
Software Engineer specializing in backend development and API design.

## Core Capabilities
- **Backend Development**: Design and implement robust backend systems
- **API Design**: Create RESTful and GraphQL APIs
- **Database Management**: Optimize database queries and schema design
- **Testing**: Write comprehensive unit and integration tests
- **Code Review**: Provide thorough code review and feedback

## Authority Scope
- **Code Implementation**: Full authority over code changes and implementation
- **Architecture Decisions**: Can make architectural decisions for assigned modules
- **Testing Standards**: Define and enforce testing standards
- **Documentation**: Create and maintain technical documentation

## Context Preferences
- **Include**: Code examples, error handling patterns, performance considerations
- **Exclude**: Frontend styling, UI/UX design details
- **Focus**: Backend logic, data flow, system architecture

## Escalation Criteria
- **Complex Architecture**: Escalate system-wide architectural decisions
- **Security Issues**: Escalate security-related implementations
- **Performance Critical**: Escalate performance-critical optimizations

## Integration Patterns
- **With QA**: Collaborate on test strategy and implementation
- **With Documentation**: Provide technical details for documentation
- **With DevOps**: Coordinate on deployment and infrastructure needs

## Quality Standards
- **Code Quality**: Maintain high code quality with proper error handling
- **Testing Coverage**: Ensure minimum 80% test coverage
- **Documentation**: Document all public APIs and complex logic

## Communication Style
- **Updates**: Provide regular progress updates with technical details
- **Issues**: Report blockers immediately with potential solutions
- **Feedback**: Request feedback on architectural decisions

**Template ID**: engineer_backend_v1
**Training Enabled**: true
"""
    
    @pytest.mark.asyncio
    async def test_profile_loader_initialization(self, profile_loader):
        """Test profile loader initialization."""
        assert profile_loader is not None
        assert profile_loader.working_directory is not None
        assert profile_loader.framework_path is not None
        assert profile_loader.user_home is not None
        assert profile_loader.profile_manager is not None
        assert len(profile_loader.profile_manager.tier_paths) == 3
        assert ProfileTier.PROJECT in profile_loader.profile_manager.tier_paths
        assert ProfileTier.USER in profile_loader.profile_manager.tier_paths
        assert ProfileTier.SYSTEM in profile_loader.profile_manager.tier_paths
    
    @pytest.mark.asyncio
    async def test_create_profile_files(self, profile_loader, sample_profile_content):
        """Test creating profile files in different tiers."""
        # Create profile in project tier
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        # Create profile in user tier
        user_path = profile_loader.profile_manager.tier_paths[ProfileTier.USER]
        user_file = user_path / "engineer.md"
        user_file.write_text(sample_profile_content.replace("backend", "fullstack"))
        
        # Create profile in system tier
        system_path = profile_loader.profile_manager.tier_paths[ProfileTier.SYSTEM]
        system_file = system_path / "engineer.md"
        system_file.write_text(sample_profile_content.replace("backend", "generic"))
        
        # Verify files exist
        assert project_file.exists()
        assert user_file.exists()
        assert system_file.exists()
    
    @pytest.mark.asyncio
    async def test_load_agent_profile_hierarchy(self, profile_loader, sample_profile_content):
        """Test loading agent profile with hierarchy precedence."""
        # Create profiles in different tiers
        await self.test_create_profile_files(profile_loader, sample_profile_content)
        
        # Start the loader
        await profile_loader.start()
        
        try:
            # Load profile - should get project tier (highest precedence)
            profile = await profile_loader.load_agent_profile(agent_name="engineer")
            
            assert profile is not None
            assert profile.name == "engineer"
            assert profile.tier == ProfileTier.PROJECT
            assert "backend" in profile.content
            assert profile.role == "Software Engineer specializing in backend development and API design."
            assert len(profile.capabilities) > 0
            assert len(profile.authority_scope) > 0
            assert profile.prompt_template_id == "engineer_backend_v1"
            assert profile.training_enabled is True
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_load_agent_profile_user_tier(self, profile_loader, sample_profile_content):
        """Test loading agent profile from user tier when project tier doesn't exist."""
        # Create profile only in user tier
        user_path = profile_loader.profile_manager.tier_paths[ProfileTier.USER]
        user_file = user_path / "engineer.md"
        user_file.write_text(sample_profile_content.replace("backend", "fullstack"))
        
        await profile_loader.start()
        
        try:
            # Load profile - should get user tier
            profile = await profile_loader.load_agent_profile(agent_name="engineer")
            
            assert profile is not None
            assert profile.name == "engineer"
            assert profile.tier == ProfileTier.USER
            assert "fullstack" in profile.content
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_load_agent_profile_system_tier(self, profile_loader, sample_profile_content):
        """Test loading agent profile from system tier as fallback."""
        # Create profile only in system tier
        system_path = profile_loader.profile_manager.tier_paths[ProfileTier.SYSTEM]
        system_file = system_path / "engineer.md"
        system_file.write_text(sample_profile_content.replace("backend", "generic"))
        
        await profile_loader.start()
        
        try:
            # Load profile - should get system tier
            profile = await profile_loader.load_agent_profile(agent_name="engineer")
            
            assert profile is not None
            assert profile.name == "engineer"
            assert profile.tier == ProfileTier.SYSTEM
            assert "generic" in profile.content
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_profile(self, profile_loader):
        """Test loading nonexistent profile."""
        await profile_loader.start()
        
        try:
            profile = await profile_loader.load_agent_profile(agent_name="nonexistent")
            assert profile is None
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_improved_prompt_integration(self, profile_loader, sample_profile_content):
        """Test improved prompt integration."""
        # Create base profile
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        # Create improved prompt
        improved_prompt = ImprovedPrompt(
            agent_type="engineer",
            original_prompt="Original prompt content",
            improved_prompt="Improved prompt with better structure and examples",
            improvement_score=25.5,
            training_session_id="sess_12345",
            timestamp=datetime.now(),
            validation_metrics={"accuracy": 0.95, "completeness": 0.90},
            deployment_ready=True
        )
        
        await profile_loader.start()
        
        try:
            # Save improved prompt
            success = await profile_loader.save_improved_prompt(improved_prompt)
            assert success is True
            
            # Load profile with improved prompt
            profile = await profile_loader.load_agent_profile(agent_name="engineer")
            
            assert profile is not None
            assert profile.has_improved_prompt is True
            assert profile.improved_prompt is not None
            assert profile.improved_prompt.improvement_score == 25.5
            assert profile.status == ProfileStatus.IMPROVED
            
            # Test effective prompt
            effective_prompt = profile.get_effective_prompt()
            assert effective_prompt == improved_prompt.improved_prompt
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_build_enhanced_task_prompt(self, profile_loader, sample_profile_content):
        """Test building enhanced task prompt."""
        # Create profile
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        await profile_loader.start()
        
        try:
            # Build enhanced prompt
            task_context = {
                'task_description': 'Implement JWT authentication system',
                'requirements': [
                    'Use secure token generation',
                    'Implement token expiration'
                ],
                'deliverables': [
                    'JWT middleware',
                    'Token validation service'
                ],
                'priority': 'high'
            }
            
            enhanced_prompt = await profile_loader.build_enhanced_task_prompt(
                "engineer", 
                task_context
            )
            
            assert enhanced_prompt is not None
            assert "Engineer" in enhanced_prompt
            assert "JWT authentication system" in enhanced_prompt
            assert "Enhanced Agent Profile Integration" in enhanced_prompt
            assert "Backend Development" in enhanced_prompt
            assert "project" in enhanced_prompt
            assert "high" in enhanced_prompt
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_list_available_agents(self, profile_loader, sample_profile_content):
        """Test listing available agents."""
        # Create profiles in different tiers
        await self.test_create_profile_files(profile_loader, sample_profile_content)
        
        # Create additional profiles
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        (project_path / "documentation.md").write_text(sample_profile_content.replace("Engineer", "Documentation"))
        
        await profile_loader.start()
        
        try:
            agents = await profile_loader.list_available_agents()
            
            assert isinstance(agents, dict)
            assert len(agents) > 0
            
            # Check that we have agents in different tiers
            found_agents = []
            for tier, tier_agents in agents.items():
                for agent in tier_agents:
                    found_agents.append(agent['name'])
            
            assert 'engineer' in found_agents
            assert 'documentation' in found_agents
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, profile_loader, sample_profile_content):
        """Test performance metrics collection."""
        # Create profile
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        await profile_loader.start()
        
        try:
            # Load profile multiple times
            for _ in range(3):
                await profile_loader.load_agent_profile(agent_name="engineer")
            
            # Get performance metrics
            metrics = await profile_loader.get_performance_metrics()
            
            assert isinstance(metrics, dict)
            assert 'profiles_loaded' in metrics
            assert 'cache_hits' in metrics
            assert 'cache_misses' in metrics
            assert metrics['profiles_loaded'] >= 1
            assert metrics['cache_hits'] >= 2  # Second and third calls should hit cache
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_profile_validation(self, profile_loader, sample_profile_content):
        """Test profile integration validation."""
        # Create profile
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        await profile_loader.start()
        
        try:
            validation = await profile_loader.validate_profile_integration()
            
            assert isinstance(validation, dict)
            assert 'valid' in validation
            assert 'issues' in validation
            assert 'warnings' in validation
            assert 'integrations' in validation
            
            # Should be valid with proper setup
            assert validation['valid'] is True
            
        finally:
            await profile_loader.stop()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, profile_loader, sample_profile_content):
        """Test cache invalidation."""
        # Create profile
        project_path = profile_loader.profile_manager.tier_paths[ProfileTier.PROJECT]
        project_file = project_path / "engineer.md"
        project_file.write_text(sample_profile_content)
        
        await profile_loader.start()
        
        try:
            # Load profile
            profile1 = await profile_loader.load_agent_profile(agent_name="engineer")
            assert profile1 is not None
            
            # Invalidate cache
            profile_loader.profile_manager.invalidate_cache("engineer")
            
            # Load again - should reload from file
            profile2 = await profile_loader.load_agent_profile(agent_name="engineer")
            assert profile2 is not None
            
            # Invalidate all
            profile_loader.profile_manager.invalidate_cache()
            
            profile3 = await profile_loader.load_agent_profile(agent_name="engineer")
            assert profile3 is not None
            
        finally:
            await profile_loader.stop()


class TestTaskToolProfileIntegration:
    """Test suite for TaskToolProfileIntegration."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        # Return a dictionary instead of Mock object since Config expects a dict
        return {}
    
    @pytest.fixture
    def mock_agent_loader(self):
        """Create mock agent loader."""
        loader = Mock()
        loader.start = Mock(return_value=None)
        loader.stop = Mock(return_value=None)
        loader.load_agent_profile = Mock()
        loader.build_enhanced_task_prompt = Mock()
        loader.get_performance_metrics = Mock(return_value={})
        loader.validate_profile_integration = Mock(return_value={'valid': True, 'issues': [], 'warnings': []})
        return loader
    
    @pytest.fixture
    def mock_agent_profile(self):
        """Create mock agent profile."""
        profile = Mock(spec=AgentProfile)
        profile.name = "engineer"
        profile.tier = ProfileTier.PROJECT
        profile.role = "Software Engineer"
        profile.nickname = "Engineer"
        profile.has_improved_prompt = False
        profile.improved_prompt = None
        profile.status = ProfileStatus.ACTIVE
        return profile
    
    @pytest.fixture
    def integration_service(self, mock_config):
        """Create integration service for testing."""
        return TaskToolProfileIntegration(mock_config)
    
    @pytest.mark.asyncio
    async def test_task_tool_request_creation(self):
        """Test TaskToolRequest creation."""
        request = TaskToolRequest(
            agent_name="engineer",
            task_description="Implement JWT authentication",
            requirements=["Secure tokens", "Token expiration"],
            deliverables=["JWT middleware", "Token service"],
            priority="high"
        )
        
        assert request.agent_name == "engineer"
        assert request.task_description == "Implement JWT authentication"
        assert len(request.requirements) == 2
        assert len(request.deliverables) == 2
        assert request.priority == "high"
        assert request.enhanced_prompts is True
        assert request.training_integration is True
        assert request.request_id is not None
        assert request.timestamp is not None
        
        # Test task context
        context = request.task_context
        assert context['task_description'] == "Implement JWT authentication"
        assert context['priority'] == "high"
        assert context['requirements'] == ["Secure tokens", "Token expiration"]
    
    @pytest.mark.asyncio
    async def test_task_tool_response_creation(self):
        """Test TaskToolResponse creation."""
        response = TaskToolResponse(
            request_id="req_123",
            success=True,
            enhanced_prompt="Enhanced prompt content",
            prompt_improvement_score=15.5,
            cache_hit=False,
            response_time_ms=250.0
        )
        
        assert response.request_id == "req_123"
        assert response.success is True
        assert response.enhanced_prompt == "Enhanced prompt content"
        assert response.prompt_improvement_score == 15.5
        assert response.cache_hit is False
        assert response.response_time_ms == 250.0
    
    @patch('claude_pm.services.task_tool_profile_integration.AgentProfileLoader')
    @pytest.mark.asyncio
    async def test_integration_service_initialization(self, mock_loader_class, integration_service):
        """Test integration service initialization."""
        mock_loader = Mock()
        mock_loader.start = AsyncMock()  # Use AsyncMock for async method
        mock_loader_class.return_value = mock_loader
        
        await integration_service._initialize()
        
        assert integration_service.agent_loader is not None
        mock_loader.start.assert_called_once()
    
    @patch('claude_pm.services.task_tool_profile_integration.AgentProfileLoader')
    @pytest.mark.asyncio
    async def test_create_enhanced_subprocess(self, mock_loader_class, integration_service, mock_agent_profile):
        """Test creating enhanced subprocess."""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.start = AsyncMock()
        mock_loader.load_agent_profile = AsyncMock(return_value=mock_agent_profile)
        mock_loader.build_enhanced_task_prompt = AsyncMock(return_value="Enhanced prompt content")
        mock_loader_class.return_value = mock_loader
        
        integration_service.agent_loader = mock_loader
        
        # Create request
        request = TaskToolRequest(
            agent_name="engineer",
            task_description="Implement JWT authentication",
            requirements=["Secure tokens"],
            deliverables=["JWT middleware"],
            priority="high"
        )
        
        # Create subprocess
        response = await integration_service.create_enhanced_subprocess(request)
        
        assert response.success is True
        assert response.request_id == request.request_id
        # The enhanced prompt includes the base content plus task tool integration metadata
        assert "Enhanced prompt content" in response.enhanced_prompt
        assert "Task Tool Integration" in response.enhanced_prompt
        assert response.agent_profile == mock_agent_profile
        assert response.response_time_ms > 0
        
        # Verify method calls
        mock_loader.load_agent_profile.assert_called_once_with("engineer")
        mock_loader.build_enhanced_task_prompt.assert_called_once()
    
    @patch('claude_pm.services.task_tool_profile_integration.AgentProfileLoader')
    @pytest.mark.asyncio
    async def test_create_enhanced_subprocess_profile_not_found(self, mock_loader_class, integration_service):
        """Test creating enhanced subprocess when profile not found."""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.start = AsyncMock()
        mock_loader.load_agent_profile = AsyncMock(return_value=None)
        mock_loader_class.return_value = mock_loader
        
        integration_service.agent_loader = mock_loader
        
        # Create request
        request = TaskToolRequest(
            agent_name="nonexistent",
            task_description="Test task"
        )
        
        # Create subprocess
        response = await integration_service.create_enhanced_subprocess(request)
        
        assert response.success is False
        assert "Agent profile not found" in response.error
        assert response.request_id == request.request_id
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, integration_service):
        """Test cache key generation."""
        request = TaskToolRequest(
            agent_name="engineer",
            task_description="Implement JWT authentication",
            requirements=["Secure tokens", "Token expiration"],
            deliverables=["JWT middleware"],
            priority="high"
        )
        
        cache_key = integration_service._generate_cache_key(request)
        
        assert cache_key is not None
        assert "task_tool_enhanced:engineer:" in cache_key
        assert len(cache_key.split(':')) == 3
    
    @pytest.mark.asyncio
    async def test_request_history_management(self, integration_service):
        """Test request history management."""
        # Create multiple requests
        requests = [
            TaskToolRequest(
                agent_name="engineer",
                task_description=f"Task {i}",
                priority="medium"
            )
            for i in range(5)
        ]
        
        # Add to history
        for request in requests:
            integration_service._add_to_history(request)
        
        assert len(integration_service.request_history) == 5
        
        # Get history
        history = await integration_service.get_request_history()
        assert len(history) == 5
        
        # Get filtered history
        filtered_history = await integration_service.get_request_history(
            agent_name="engineer",
            limit=3
        )
        assert len(filtered_history) == 3
        
        # All should be for engineer
        for entry in filtered_history:
            assert entry['agent_name'] == "engineer"
    
    @pytest.mark.asyncio
    async def test_performance_metrics_update(self, integration_service):
        """Test performance metrics update."""
        # Initial metrics
        initial_metrics = integration_service.performance_metrics.copy()
        
        # Update metrics
        integration_service.performance_metrics['subprocess_requests'] += 1
        integration_service.performance_metrics['successful_enhancements'] += 1
        integration_service._update_average_response_time(150.0)
        
        # Check updates
        assert integration_service.performance_metrics['subprocess_requests'] > initial_metrics['subprocess_requests']
        assert integration_service.performance_metrics['successful_enhancements'] > initial_metrics['successful_enhancements']
        assert integration_service.performance_metrics['average_response_time_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_batch_subprocess_creation(self, integration_service):
        """Test batch subprocess creation."""
        # Create multiple requests
        requests = [
            TaskToolRequest(
                agent_name="engineer",
                task_description=f"Task {i}",
                priority="medium"
            )
            for i in range(3)
        ]
        
        # Mock the single subprocess creation
        async def mock_create_subprocess(request):
            return TaskToolResponse(
                request_id=request.request_id,
                success=True,
                enhanced_prompt=f"Enhanced prompt for {request.task_description}",
                response_time_ms=100.0
            )
        
        integration_service.create_enhanced_subprocess = mock_create_subprocess
        
        # Create batch
        responses = await integration_service.batch_create_subprocesses(requests)
        
        assert len(responses) == 3
        for response in responses:
            assert response.success is True
            assert response.enhanced_prompt is not None
    
    @pytest.mark.asyncio
    async def test_create_subprocess_from_dict(self, integration_service):
        """Test creating subprocess from dictionary."""
        request_data = {
            'agent_name': 'engineer',
            'task_description': 'Implement JWT authentication',
            'requirements': ['Secure tokens'],
            'deliverables': ['JWT middleware'],
            'priority': 'high',
            'enhanced_prompts': True,
            'training_integration': True
        }
        
        # Mock the subprocess creation
        async def mock_create_subprocess(request):
            return TaskToolResponse(
                request_id=request.request_id,
                success=True,
                enhanced_prompt="Enhanced prompt content",
                response_time_ms=200.0
            )
        
        integration_service.create_enhanced_subprocess = mock_create_subprocess
        
        # Create subprocess from dict
        response = await integration_service.create_subprocess_from_dict(request_data)
        
        assert response.success is True
        assert response.enhanced_prompt == "Enhanced prompt content"
        assert response.response_time_ms > 0


class TestIntegrationWorkflow:
    """Test end-to-end integration workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_profile_content(self):
        """Create sample profile content."""
        return """# Engineer Agent Profile

## Role
Software Engineer specializing in backend development.

## Core Capabilities
- **Backend Development**: Design and implement backend systems
- **API Design**: Create RESTful APIs
- **Testing**: Write unit and integration tests

## Authority Scope
- **Code Implementation**: Full authority over code changes
- **Testing Standards**: Define testing standards

## Context Preferences
- **Include**: Code examples, error handling
- **Focus**: Backend logic, system architecture

## Quality Standards
- **Code Quality**: Maintain high code quality
- **Testing Coverage**: Ensure 80% test coverage

**Training Enabled**: true
"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, temp_dir, sample_profile_content):
        """Test complete end-to-end workflow."""
        # Setup directory structure
        project_dir = temp_dir / '.claude-pm' / 'agents' / 'project-specific'
        project_dir.mkdir(parents=True)
        
        # Create profile file
        profile_file = project_dir / 'engineer.md'
        profile_file.write_text(sample_profile_content)
        
        # Mock working directory
        with patch('claude_pm.services.agent_profile_loader.os.getcwd', return_value=str(temp_dir)):
            # Create config - use a dict instead of Mock
            config = {}
            
            # Create integration service
            integration = TaskToolProfileIntegration(config)
            
            # Mock dependencies to avoid actual service initialization
            mock_loader = Mock()
            mock_loader.start = AsyncMock()
            mock_loader.stop = AsyncMock()
            
            # Create test profile
            test_profile = AgentProfile(
                name="engineer",
                tier=ProfileTier.PROJECT,
                path=profile_file,
                role="Software Engineer",
                capabilities=["Backend Development", "API Design"],
                authority_scope=["Code Implementation"],
                context_preferences={"include": "Code examples"},
                escalation_criteria=[],
                integration_patterns={},
                quality_standards=["Code Quality"],
                communication_style={},
                content=sample_profile_content,
                training_enabled=True
            )
            
            mock_loader.load_agent_profile = AsyncMock(return_value=test_profile)
            mock_loader.build_enhanced_task_prompt = AsyncMock(return_value="Enhanced prompt content")
            mock_loader.get_performance_metrics = Mock(return_value={})
            mock_loader.validate_profile_integration = Mock(return_value={'valid': True, 'issues': [], 'warnings': []})
            
            integration.agent_loader = mock_loader
            
            # Create request
            request = TaskToolRequest(
                agent_name="engineer",
                task_description="Implement JWT authentication system",
                requirements=[
                    "Use secure token generation",
                    "Implement token expiration",
                    "Add refresh token support"
                ],
                deliverables=[
                    "JWT authentication middleware",
                    "Token validation service",
                    "Unit tests for auth system"
                ],
                priority="high"
            )
            
            # Execute workflow
            response = await integration.create_enhanced_subprocess(request)
            
            # Verify results
            assert response.success is True
            assert response.request_id == request.request_id
            # The enhanced prompt includes the base content plus task tool integration metadata
            assert "Enhanced prompt content" in response.enhanced_prompt
            assert "Task Tool Integration" in response.enhanced_prompt
            assert response.agent_profile == test_profile
            assert response.response_time_ms > 0
            
            # Verify method calls
            mock_loader.load_agent_profile.assert_called_once_with("engineer")
            mock_loader.build_enhanced_task_prompt.assert_called_once()
            
            # Verify request was added to history
            history = await integration.get_request_history()
            assert len(history) == 1
            assert history[0]['agent_name'] == "engineer"
            assert history[0]['task_description'] == "Implement JWT authentication system"
            assert history[0]['priority'] == "high"


# Test runner
if __name__ == "__main__":
    async def run_tests():
        """Run all tests."""
        print("🧪 Running Agent Profile Loader Tests")
        print("=" * 50)
        
        # Run specific test methods
        test_loader = TestAgentProfileLoader()
        test_integration = TestTaskToolProfileIntegration()
        test_workflow = TestIntegrationWorkflow()
        
        # Create fixtures
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Test profile loader
            print("\n📋 Testing AgentProfileLoader...")
            
            # Mock working directory
            with patch('claude_pm.services.agent_profile_loader.os.getcwd', return_value=str(temp_dir)):
                config = Mock(spec=Config)
                config.get = Mock(return_value=None)
                
                loader = AgentProfileLoader(config)
                
                # Create test directory structure
                for tier in ['project-specific', 'user-defined', 'system']:
                    tier_dir = temp_dir / '.claude-pm' / 'agents' / tier
                    tier_dir.mkdir(parents=True, exist_ok=True)
                
                # Test basic initialization
                await test_loader.test_profile_loader_initialization(loader)
                print("✅ Profile loader initialization test passed")
                
                # Test profile loading
                sample_content = """# Engineer Agent Profile
## Role
Software Engineer specializing in backend development.
## Core Capabilities
- **Backend Development**: Design and implement backend systems
**Training Enabled**: true
"""
                
                # Create profile file
                project_path = loader.tier_paths[ProfileTier.PROJECT]
                project_file = project_path / "engineer.md"
                project_file.write_text(sample_content)
                
                await loader.start()
                try:
                    profile = await loader.load_agent_profile("engineer")
                    assert profile is not None
                    assert profile.name == "engineer"
                    assert profile.tier == ProfileTier.PROJECT
                    print("✅ Profile loading test passed")
                finally:
                    await loader.stop()
            
            # Test integration service
            print("\n🔧 Testing TaskToolProfileIntegration...")
            
            config = Mock(spec=Config)
            config.get = Mock(return_value=None)
            integration = TaskToolProfileIntegration(config)
            
            # Test request creation
            request = TaskToolRequest(
                agent_name="engineer",
                task_description="Test task",
                priority="high"
            )
            
            assert request.agent_name == "engineer"
            assert request.priority == "high"
            print("✅ Request creation test passed")
            
            # Test response creation
            response = TaskToolResponse(
                request_id="test_123",
                success=True,
                enhanced_prompt="Test prompt"
            )
            
            assert response.request_id == "test_123"
            assert response.success is True
            print("✅ Response creation test passed")
            
            print("\n🎯 All tests completed successfully!")
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
    
    # Run the tests
    asyncio.run(run_tests())