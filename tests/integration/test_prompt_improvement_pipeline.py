"""
Test Suite for Prompt Improvement Pipeline

Comprehensive tests for the automated prompt improvement pipeline including
unit tests, integration tests, and end-to-end pipeline validation.

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

# Import pipeline components
from claude_pm.services.prompt_improvement_pipeline import (
    PromptImprovementPipeline, 
    PipelineConfig, 
    PipelineExecution,
    PipelineStatus,
    PipelineStage
)
from claude_pm.services.prompt_improver import (
    PromptImprover,
    PromptImprovement,
    ImprovementStrategy
)
from claude_pm.services.pattern_analyzer import (
    PatternAnalyzer,
    PatternMetrics,
    CorrectionPattern
)
from claude_pm.services.prompt_template_manager import (
    PromptTemplateManager,
    TemplateVersion,
    TemplateStatus,
    TemplateType
)
from claude_pm.services.prompt_validator import (
    PromptValidator,
    ValidationReport,
    TestResult,
    ABTestResult
)


class TestPromptImprovementPipeline:
    """Test suite for the main pipeline orchestration"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def pipeline_config(self):
        """Create test pipeline configuration"""
        return {
            'agent_types': ['Documentation', 'Engineer'],
            'correction_analysis_days': 7,
            'pattern_detection_threshold': 0.5,
            'improvement_confidence_threshold': 0.6,
            'validation_sample_size': 3,
            'auto_deployment_enabled': False,
            'monitoring_interval': 300,
            'pipeline_timeout': 1800
        }
    
    @pytest.fixture
    def pipeline(self, temp_dir, pipeline_config):
        """Create pipeline instance for testing"""
        config = {
            **pipeline_config,
            'base_path': temp_dir
        }
        return PromptImprovementPipeline(config)
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization"""
        assert pipeline is not None
        assert len(pipeline.pipeline_config.agent_types) == 2
        assert pipeline.pipeline_config.correction_analysis_days == 7
        assert pipeline.pipeline_config.pattern_detection_threshold == 0.5
        assert pipeline.pipeline_config.improvement_confidence_threshold == 0.6
        assert pipeline.pipeline_config.validation_sample_size == 3
        assert pipeline.pipeline_config.auto_deployment_enabled == False
        
        # Check directory creation
        assert pipeline.base_path.exists()
        assert pipeline.executions_path.exists()
        assert pipeline.results_path.exists()
        assert pipeline.monitoring_path.exists()
    
    @pytest.mark.asyncio
    async def test_pipeline_execution_tracking(self, pipeline):
        """Test execution tracking functionality"""
        execution_id = pipeline._generate_execution_id()
        
        # Test execution ID generation
        assert execution_id.startswith('pipeline_')
        assert len(execution_id) > 20
        
        # Test execution creation
        execution = PipelineExecution(
            execution_id=execution_id,
            config=pipeline.pipeline_config,
            start_time=datetime.now(),
            status=PipelineStatus.RUNNING
        )
        
        pipeline.active_executions[execution_id] = execution
        assert execution_id in pipeline.active_executions
        
        # Test execution status update
        await pipeline._update_execution_status(execution)
        
        # Check that execution record was saved
        execution_file = pipeline.executions_path / f"{execution_id}.json"
        assert execution_file.exists()
        
        with open(execution_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data['execution_id'] == execution_id
            assert saved_data['status'] == 'running'
    
    @pytest.mark.asyncio
    async def test_pipeline_pause_resume_cancel(self, pipeline):
        """Test pipeline control operations"""
        execution_id = pipeline._generate_execution_id()
        execution = PipelineExecution(
            execution_id=execution_id,
            config=pipeline.pipeline_config,
            start_time=datetime.now(),
            status=PipelineStatus.RUNNING
        )
        
        pipeline.active_executions[execution_id] = execution
        
        # Test pause
        success = await pipeline.pause_pipeline(execution_id)
        assert success == True
        assert pipeline.active_executions[execution_id].status == PipelineStatus.PAUSED
        
        # Test resume
        success = await pipeline.resume_pipeline(execution_id)
        assert success == True
        assert pipeline.active_executions[execution_id].status == PipelineStatus.RUNNING
        
        # Test cancel
        success = await pipeline.cancel_pipeline(execution_id)
        assert success == True
        assert execution_id not in pipeline.active_executions
    
    @pytest.mark.asyncio
    async def test_pipeline_health_monitoring(self, pipeline):
        """Test pipeline health monitoring"""
        health_status = await pipeline.monitor_pipeline_health()
        
        assert 'pipeline_status' in health_status
        assert 'active_executions' in health_status
        assert 'component_health' in health_status
        assert 'timestamp' in health_status
        
        # Check component health structure
        assert 'correction_capture' in health_status['component_health']
        assert 'pattern_analyzer' in health_status['component_health']
        assert 'prompt_improver' in health_status['component_health']
        assert 'template_manager' in health_status['component_health']
        assert 'validator' in health_status['component_health']
    
    @pytest.mark.asyncio
    async def test_pipeline_analytics(self, pipeline):
        """Test pipeline analytics generation"""
        analytics = await pipeline.get_pipeline_analytics(days_back=7)
        
        assert 'period' in analytics
        assert 'execution_summary' in analytics
        assert 'improvement_metrics' in analytics
        assert 'agent_performance' in analytics
        
        # Check structure
        assert 'total_executions' in analytics['execution_summary']
        assert 'success_rate' in analytics['execution_summary']
        assert 'total_improvements_generated' in analytics['improvement_metrics']
        assert 'deployment_rate' in analytics['improvement_metrics']
    
    @pytest.mark.asyncio
    async def test_targeted_improvement(self, pipeline):
        """Test targeted improvement functionality"""
        # Mock the dependencies
        with patch.object(pipeline.correction_capture, 'get_corrections_for_agent') as mock_corrections:
            with patch.object(pipeline.pattern_analyzer, 'analyze_correction_patterns') as mock_patterns:
                with patch.object(pipeline.prompt_improver, 'generate_prompt_improvements') as mock_improvements:
                    with patch.object(pipeline.prompt_improver, 'validate_improvements') as mock_validate:
                        
                        # Setup mocks
                        mock_corrections.return_value = [Mock()]
                        mock_patterns.return_value = [Mock()]
                        mock_improvements.return_value = [Mock()]
                        mock_validate.return_value = [Mock()]
                        
                        # Run targeted improvement
                        results = await pipeline.run_targeted_improvement('Documentation')
                        
                        # Verify results
                        assert 'execution_id' in results
                        assert 'agent_type' in results
                        assert results['agent_type'] == 'Documentation'
                        assert 'patterns_analyzed' in results
                        assert 'improvements_generated' in results
                        assert 'improvements_validated' in results
    
    @pytest.mark.asyncio
    async def test_config_merging(self, pipeline):
        """Test configuration merging"""
        custom_config = {
            'correction_analysis_days': 14,
            'auto_deployment_enabled': True
        }
        
        merged_config = pipeline._merge_config(custom_config)
        
        assert merged_config.correction_analysis_days == 14
        assert merged_config.auto_deployment_enabled == True
        assert merged_config.pattern_detection_threshold == 0.5  # Should keep default
    
    @pytest.mark.asyncio
    async def test_execution_metrics_calculation(self, pipeline):
        """Test execution metrics calculation"""
        execution = PipelineExecution(
            execution_id='test_exec',
            config=pipeline.pipeline_config,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=300),
            status=PipelineStatus.COMPLETED,
            total_improvements=5,
            deployed_improvements=3,
            stage_results={'test_stage': {'result': 'success'}}
        )
        
        metrics = pipeline._calculate_execution_metrics(execution)
        
        assert metrics['execution_time'] == 300.0
        assert metrics['total_improvements'] == 5
        assert metrics['deployed_improvements'] == 3
        assert metrics['deployment_rate'] == 0.6
        assert 'stage_performance' in metrics


class TestPromptImprover:
    """Test suite for the prompt improvement component"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def improver(self, temp_dir):
        """Create improver instance for testing"""
        config = {'base_path': temp_dir}
        return PromptImprover(config)
    
    @pytest.mark.asyncio
    async def test_improver_initialization(self, improver):
        """Test improver initialization"""
        assert improver is not None
        assert improver.base_path.exists()
        assert improver.patterns_path.exists()
        assert improver.improvements_path.exists()
        assert improver.templates_path.exists()
        assert improver.metrics_path.exists()
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, improver):
        """Test pattern analysis functionality"""
        # Mock correction data
        mock_corrections = [
            Mock(
                agent_type='Documentation',
                error_type='format_error',
                timestamp=datetime.now(),
                issue_description='Missing formatting',
                correction_applied='Added proper formatting'
            ),
            Mock(
                agent_type='Documentation',
                error_type='format_error',
                timestamp=datetime.now(),
                issue_description='Inconsistent formatting',
                correction_applied='Standardized formatting'
            )
        ]
        
        patterns = await improver.analyze_correction_patterns(mock_corrections)
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert hasattr(pattern, 'pattern_id')
        assert hasattr(pattern, 'frequency')
        assert hasattr(pattern, 'severity')
        assert hasattr(pattern, 'confidence')
    
    @pytest.mark.asyncio
    async def test_improvement_generation(self, improver):
        """Test improvement generation"""
        # Mock pattern data
        mock_pattern = CorrectionPattern(
            pattern_id='test_pattern',
            agent_type='Documentation',
            pattern_type='format_error',
            frequency=5,
            severity='medium',
            common_issues=['formatting', 'consistency'],
            suggested_improvement='Add formatting guidelines',
            confidence=0.8,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        
        # Mock current prompt
        with patch.object(improver, '_get_current_prompt') as mock_prompt:
            mock_prompt.return_value = "Current prompt content"
            
            improvements = await improver.generate_prompt_improvements([mock_pattern])
            
            assert len(improvements) > 0
            improvement = improvements[0]
            assert hasattr(improvement, 'improvement_id')
            assert hasattr(improvement, 'agent_type')
            assert hasattr(improvement, 'strategy')
            assert hasattr(improvement, 'improved_prompt')
    
    @pytest.mark.asyncio
    async def test_improvement_validation(self, improver):
        """Test improvement validation"""
        # Mock improvement
        improvement = PromptImprovement(
            improvement_id='test_improvement',
            agent_type='Documentation',
            strategy=ImprovementStrategy.ADDITIVE,
            original_prompt='Original prompt',
            improved_prompt='Improved prompt',
            improvement_reason='Better formatting',
            confidence_score=0.8,
            timestamp=datetime.now(),
            version='1.0.0'
        )
        
        # Mock validation test
        with patch.object(improver, '_run_validation_test') as mock_test:
            mock_test.return_value = {
                'success': True,
                'effectiveness': 0.85,
                'original_score': 0.7,
                'improved_score': 0.85
            }
            
            validated = await improver.validate_improvements([improvement])
            
            assert len(validated) == 1
            assert validated[0].validation_status == 'approved'
            assert validated[0].effectiveness_score == 0.85
    
    @pytest.mark.asyncio
    async def test_improvement_rollback(self, improver):
        """Test improvement rollback"""
        # Mock improvement
        improvement = PromptImprovement(
            improvement_id='test_improvement',
            agent_type='Documentation',
            strategy=ImprovementStrategy.ADDITIVE,
            original_prompt='Original prompt',
            improved_prompt='Improved prompt',
            improvement_reason='Better formatting',
            confidence_score=0.8,
            timestamp=datetime.now(),
            version='1.0.0'
        )
        
        # Add to cache
        improver.improvements_cache['test_improvement'] = improvement
        
        # Mock backup finding
        with patch.object(improver, '_find_backup_for_improvement') as mock_backup:
            with patch.object(improver, '_apply_rollback') as mock_apply:
                mock_backup.return_value = Path('backup.txt')
                mock_apply.return_value = True
                
                # Create mock backup file
                backup_file = improver.base_path / 'backup.txt'
                backup_file.write_text('Original prompt content')
                
                success = await improver.rollback_improvement('test_improvement', 'Test rollback')
                
                assert success == True
                assert improver.improvements_cache['test_improvement'].validation_status == 'rolled_back'
    
    @pytest.mark.asyncio
    async def test_improvement_metrics(self, improver):
        """Test improvement metrics calculation"""
        # Mock improvements with different timestamps
        now = datetime.now()
        improvements = [
            PromptImprovement(
                improvement_id='imp1',
                agent_type='Documentation',
                strategy=ImprovementStrategy.ADDITIVE,
                original_prompt='Original',
                improved_prompt='Improved',
                improvement_reason='Test',
                confidence_score=0.8,
                timestamp=now - timedelta(days=1),
                version='1.0.0',
                validation_status='approved',
                effectiveness_score=0.85
            ),
            PromptImprovement(
                improvement_id='imp2',
                agent_type='Documentation',
                strategy=ImprovementStrategy.REPLACEMENT,
                original_prompt='Original',
                improved_prompt='Improved',
                improvement_reason='Test',
                confidence_score=0.7,
                timestamp=now - timedelta(days=2),
                version='1.0.0',
                validation_status='approved',
                effectiveness_score=0.75
            )
        ]
        
        # Mock loading improvements
        with patch.object(improver, '_load_improvements_since') as mock_load:
            mock_load.return_value = improvements
            
            metrics = await improver.get_improvement_metrics(days_back=7)
            
            assert 'summary' in metrics
            assert 'effectiveness' in metrics
            assert 'strategy_distribution' in metrics
            assert metrics['summary']['total_improvements'] == 2
            assert metrics['summary']['approved_improvements'] == 2
            assert metrics['effectiveness']['average_effectiveness'] == 0.8


class TestPatternAnalyzer:
    """Test suite for the pattern analyzer component"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analyzer(self, temp_dir):
        """Create analyzer instance for testing"""
        config = {'base_path': temp_dir}
        return PatternAnalyzer(config)
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer is not None
        assert analyzer.base_path.exists()
        assert analyzer.patterns_path.exists()
        assert analyzer.clusters_path.exists()
        assert analyzer.trends_path.exists()
    
    @pytest.mark.asyncio
    async def test_pattern_extraction(self, analyzer):
        """Test pattern extraction from corrections"""
        # Mock correction data
        mock_corrections = [
            Mock(
                agent_type='Documentation',
                error_type='format_error',
                timestamp=datetime.now(),
                issue_description='Missing formatting',
                correction_applied='Added proper formatting'
            ),
            Mock(
                agent_type='Documentation',
                error_type='format_error',
                timestamp=datetime.now() - timedelta(hours=1),
                issue_description='Inconsistent formatting',
                correction_applied='Standardized formatting'
            ),
            Mock(
                agent_type='QA',
                error_type='test_failure',
                timestamp=datetime.now() - timedelta(hours=2),
                issue_description='Test failed',
                correction_applied='Fixed test'
            )
        ]
        
        patterns = await analyzer._extract_patterns(mock_corrections)
        
        assert len(patterns) > 0
        
        # Check pattern structure
        doc_pattern = None
        for pattern in patterns:
            if pattern.agent_type == 'Documentation':
                doc_pattern = pattern
                break
        
        assert doc_pattern is not None
        assert doc_pattern.pattern_type == 'format_error'
        assert doc_pattern.frequency == 2
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, analyzer):
        """Test trend analysis"""
        # Mock timestamps for trend analysis
        now = datetime.now()
        timestamps = [
            now - timedelta(days=7),
            now - timedelta(days=6),
            now - timedelta(days=5),
            now - timedelta(days=1),
            now
        ]
        
        trend = await analyzer._calculate_trend_analysis('test_pattern', timestamps)
        
        assert trend is not None
        assert hasattr(trend, 'trend_type')
        assert hasattr(trend, 'slope')
        assert hasattr(trend, 'r_squared')
        assert hasattr(trend, 'forecast_points')
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, analyzer):
        """Test anomaly detection"""
        # Mock pattern metrics
        patterns = [
            PatternMetrics(
                pattern_id='p1',
                frequency=5,
                severity_score=2.0,
                trend_direction='stable',
                confidence=0.8,
                impact_score=0.3,
                prediction_accuracy=0.7,
                correlation_strength=0.6
            ),
            PatternMetrics(
                pattern_id='p2',
                frequency=50,  # Anomalous frequency
                severity_score=2.0,
                trend_direction='increasing',
                confidence=0.9,
                impact_score=0.8,
                prediction_accuracy=0.8,
                correlation_strength=0.7
            ),
            PatternMetrics(
                pattern_id='p3',
                frequency=3,
                severity_score=4.0,  # Anomalous severity
                trend_direction='stable',
                confidence=0.7,
                impact_score=0.5,
                prediction_accuracy=0.6,
                correlation_strength=0.5
            )
        ]
        
        anomalies = await analyzer.detect_anomalies(patterns, threshold=2.0)
        
        assert len(anomalies) >= 2  # Should detect the anomalous patterns
        
        # Check that anomalous patterns are detected
        anomaly_ids = [a.pattern_id for a in anomalies]
        assert 'p2' in anomaly_ids or 'p3' in anomaly_ids
    
    @pytest.mark.asyncio
    async def test_improvement_priorities(self, analyzer):
        """Test improvement priority generation"""
        # Mock data
        patterns = [
            PatternMetrics(
                pattern_id='high_priority',
                frequency=10,
                severity_score=3.0,
                trend_direction='increasing',
                confidence=0.9,
                impact_score=0.8,
                prediction_accuracy=0.8,
                correlation_strength=0.7
            ),
            PatternMetrics(
                pattern_id='low_priority',
                frequency=2,
                severity_score=1.0,
                trend_direction='stable',
                confidence=0.5,
                impact_score=0.2,
                prediction_accuracy=0.5,
                correlation_strength=0.4
            )
        ]
        
        clusters = []
        trends = []
        
        priorities = await analyzer.generate_improvement_priorities(patterns, clusters, trends)
        
        assert len(priorities) == 2
        
        # Check that high priority pattern is ranked first
        assert priorities[0]['pattern_id'] == 'high_priority'
        assert priorities[0]['priority_score'] > priorities[1]['priority_score']
        
        # Check priority structure
        assert 'improvement_urgency' in priorities[0]
        assert 'recommended_action' in priorities[0]


class TestPromptTemplateManager:
    """Test suite for the template manager component"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create manager instance for testing"""
        config = {'base_path': temp_dir}
        return PromptTemplateManager(config)
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert manager is not None
        assert manager.base_path.exists()
        assert manager.templates_path.exists()
        assert manager.versions_path.exists()
        assert manager.deployments_path.exists()
    
    @pytest.mark.asyncio
    async def test_template_creation(self, manager):
        """Test template creation"""
        template = await manager.create_template(
            template_id='test_template',
            content='Test template content',
            template_type=TemplateType.AGENT_PROMPT,
            agent_type='Documentation',
            author='test_author'
        )
        
        assert template.template_id == 'test_template'
        assert template.version == '1.0.0'
        assert template.content == 'Test template content'
        assert template.status == TemplateStatus.DRAFT
        assert template.author == 'test_author'
    
    @pytest.mark.asyncio
    async def test_template_update(self, manager):
        """Test template update"""
        # Create initial template
        template = await manager.create_template(
            template_id='test_template',
            content='Original content',
            template_type=TemplateType.AGENT_PROMPT,
            agent_type='Documentation'
        )
        
        # Update template
        updated = await manager.update_template(
            template_id='test_template',
            content='Updated content',
            change_summary='Updated for testing'
        )
        
        assert updated.template_id == 'test_template'
        assert updated.version == '1.0.1'
        assert updated.content == 'Updated content'
        assert updated.parent_version == '1.0.0'
        assert updated.change_summary == 'Updated for testing'
    
    @pytest.mark.asyncio
    async def test_template_versioning(self, manager):
        """Test template versioning"""
        # Create template
        template = await manager.create_template(
            template_id='version_test',
            content='Version 1',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        # Create multiple versions
        for i in range(3):
            await manager.update_template(
                template_id='version_test',
                content=f'Version {i+2}',
                change_summary=f'Update {i+2}'
            )
        
        # Get all versions
        versions = await manager.get_template_versions('version_test')
        
        assert len(versions) == 4  # Original + 3 updates
        
        # Check version ordering (newest first)
        assert versions[0].version == '1.0.3'
        assert versions[1].version == '1.0.2'
        assert versions[2].version == '1.0.1'
        assert versions[3].version == '1.0.0'
    
    @pytest.mark.asyncio
    async def test_template_activation(self, manager):
        """Test template activation"""
        # Create template
        template = await manager.create_template(
            template_id='activation_test',
            content='Test content',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        # Activate version
        success = await manager.activate_version('activation_test', '1.0.0')
        assert success == True
        
        # Check active version
        active = await manager.get_active_version('activation_test')
        assert active is not None
        assert active.status == TemplateStatus.ACTIVE
        assert active.version == '1.0.0'
    
    @pytest.mark.asyncio
    async def test_template_rollback(self, manager):
        """Test template rollback"""
        # Create template with multiple versions
        template = await manager.create_template(
            template_id='rollback_test',
            content='Version 1',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        await manager.update_template(
            template_id='rollback_test',
            content='Version 2',
            change_summary='Second version'
        )
        
        # Activate version 2
        await manager.activate_version('rollback_test', '1.0.1')
        
        # Rollback to version 1
        success = await manager.rollback_template(
            template_id='rollback_test',
            target_version='1.0.0',
            reason='Testing rollback'
        )
        
        assert success == True
        
        # Check that version 1 is now active
        active = await manager.get_active_version('rollback_test')
        assert active.version == '1.0.0'
        assert active.status == TemplateStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_template_comparison(self, manager):
        """Test template comparison"""
        # Create template with multiple versions
        template = await manager.create_template(
            template_id='comparison_test',
            content='Original content',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        await manager.update_template(
            template_id='comparison_test',
            content='Modified content',
            change_summary='Changed for comparison'
        )
        
        # Compare versions
        comparison = await manager.compare_versions(
            template_id='comparison_test',
            version_a='1.0.0',
            version_b='1.0.1'
        )
        
        assert comparison.template_id == 'comparison_test'
        assert comparison.version_a == '1.0.0'
        assert comparison.version_b == '1.0.1'
        assert comparison.similarity_score < 1.0  # Should be different
        assert len(comparison.diff_text) > 0
        assert len(comparison.change_summary) > 0
    
    @pytest.mark.asyncio
    async def test_template_deployment(self, manager):
        """Test template deployment"""
        # Create and activate template
        template = await manager.create_template(
            template_id='deployment_test',
            content='Deployment content',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        await manager.activate_version('deployment_test', '1.0.0')
        
        # Deploy template
        deployment = await manager.deploy_template(
            template_id='deployment_test',
            version='1.0.0',
            target_agents=['Documentation', 'Engineer']
        )
        
        assert deployment.template_id == 'deployment_test'
        assert deployment.version == '1.0.0'
        assert deployment.target_agents == ['Documentation', 'Engineer']
        assert deployment.status in ['deployed', 'deploying']
    
    @pytest.mark.asyncio
    async def test_template_cleanup(self, manager):
        """Test template cleanup"""
        # Create template with multiple versions
        template = await manager.create_template(
            template_id='cleanup_test',
            content='Version 1',
            template_type=TemplateType.AGENT_PROMPT
        )
        
        # Create several versions
        for i in range(5):
            await manager.update_template(
                template_id='cleanup_test',
                content=f'Version {i+2}',
                change_summary=f'Update {i+2}'
            )
        
        # Run cleanup with very short retention
        results = await manager.cleanup_old_versions(
            template_id='cleanup_test',
            days_old=0  # This should clean up everything except recent versions
        )
        
        assert results['templates_processed'] == 1
        
        # Check that some versions remain
        remaining_versions = await manager.get_template_versions('cleanup_test')
        assert len(remaining_versions) >= 3  # Should keep at least 3 versions


class TestPromptValidator:
    """Test suite for the prompt validator component"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def validator(self, temp_dir):
        """Create validator instance for testing"""
        config = {'base_path': temp_dir}
        return PromptValidator(config)
    
    @pytest.mark.asyncio
    async def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator is not None
        assert validator.base_path.exists()
        assert validator.scenarios_path.exists()
        assert validator.results_path.exists()
        assert validator.reports_path.exists()
    
    @pytest.mark.asyncio
    async def test_scenario_creation(self, validator):
        """Test test scenario creation"""
        scenario = await validator.create_test_scenario(
            name='Test Scenario',
            description='Test scenario for validation',
            agent_type='Documentation',
            task_description='Generate documentation',
            expected_outputs=['documentation', 'examples'],
            evaluation_criteria={'completeness': 0.5, 'clarity': 0.5}
        )
        
        assert scenario.name == 'Test Scenario'
        assert scenario.agent_type == 'Documentation'
        assert scenario.task_description == 'Generate documentation'
        assert len(scenario.expected_outputs) == 2
        assert scenario.scenario_id in validator.scenario_registry
    
    @pytest.mark.asyncio
    async def test_validation_test(self, validator):
        """Test validation test execution"""
        # Create test scenario
        scenario = await validator.create_test_scenario(
            name='Validation Test',
            description='Test validation',
            agent_type='Documentation',
            task_description='Test task',
            expected_outputs=['output1', 'output2'],
            evaluation_criteria={'quality': 1.0}
        )
        
        # Run validation test
        report = await validator.run_validation_test(
            prompt_id='test_prompt',
            prompt_content='Test prompt content',
            scenarios=[scenario.scenario_id]
        )
        
        assert report.prompt_id == 'test_prompt'
        assert report.total_tests == 1
        assert len(report.test_results) == 1
        assert report.overall_score >= 0.0
        assert report.overall_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_ab_testing(self, validator):
        """Test A/B testing functionality"""
        # Create test scenario
        scenario = await validator.create_test_scenario(
            name='AB Test Scenario',
            description='Test A/B testing',
            agent_type='Documentation',
            task_description='Test task',
            expected_outputs=['output'],
            evaluation_criteria={'quality': 1.0}
        )
        
        # Run A/B test
        ab_result = await validator.run_ab_test(
            prompt_a_id='prompt_a',
            prompt_a_content='Prompt A content',
            prompt_b_id='prompt_b',
            prompt_b_content='Prompt B content',
            scenarios=[scenario.scenario_id],
            sample_size=5
        )
        
        assert ab_result.prompt_a_id == 'prompt_a'
        assert ab_result.prompt_b_id == 'prompt_b'
        assert ab_result.scenarios_tested == 1
        assert len(ab_result.prompt_a_results) == 5
        assert len(ab_result.prompt_b_results) == 5
        assert ab_result.statistical_significance >= 0.0
        assert ab_result.confidence_level >= 0.0
    
    @pytest.mark.asyncio
    async def test_scenario_generation(self, validator):
        """Test automatic scenario generation"""
        scenarios = await validator.generate_test_scenarios(
            agent_type='Documentation',
            difficulty_level='medium',
            count=3
        )
        
        assert len(scenarios) <= 3  # May be limited by available templates
        
        for scenario in scenarios:
            assert scenario.agent_type == 'Documentation'
            assert 'medium' in scenario.name
            assert len(scenario.expected_outputs) > 0
            assert len(scenario.evaluation_criteria) > 0
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self, validator):
        """Test performance benchmarking"""
        # Create test scenario
        scenario = await validator.create_test_scenario(
            name='Performance Test',
            description='Performance benchmark',
            agent_type='Documentation',
            task_description='Performance task',
            expected_outputs=['output'],
            evaluation_criteria={'speed': 1.0}
        )
        
        # Run performance benchmark
        results = await validator.run_performance_benchmark(
            prompt_id='perf_test',
            prompt_content='Performance test prompt',
            scenarios=[scenario.scenario_id],
            iterations=3
        )
        
        assert results['prompt_id'] == 'perf_test'
        assert results['scenarios_tested'] == 1
        assert results['iterations_per_scenario'] == 3
        assert len(results['results']) == 1
        assert 'performance_metrics' in results
        
        # Check performance metrics
        metrics = results['performance_metrics']
        assert 'overall_avg_execution_time' in metrics
        assert 'overall_success_rate' in metrics
        assert 'overall_throughput' in metrics
    
    @pytest.mark.asyncio
    async def test_regression_testing(self, validator):
        """Test regression testing"""
        # Create test scenario
        scenario = await validator.create_test_scenario(
            name='Regression Test',
            description='Regression testing',
            agent_type='Documentation',
            task_description='Regression task',
            expected_outputs=['output'],
            evaluation_criteria={'quality': 1.0}
        )
        
        # Run regression test
        results = await validator.run_regression_test(
            prompt_id='regression_test',
            current_content='Current prompt content',
            previous_content='Previous prompt content',
            scenarios=[scenario.scenario_id]
        )
        
        assert 'regression_detected' in results
        assert 'performance_change' in results
        assert 'recommendations' in results
        assert 'ab_test_result' in results
    
    @pytest.mark.asyncio
    async def test_analytics(self, validator):
        """Test analytics generation"""
        # Create and run some tests first
        scenario = await validator.create_test_scenario(
            name='Analytics Test',
            description='Analytics testing',
            agent_type='Documentation',
            task_description='Analytics task',
            expected_outputs=['output'],
            evaluation_criteria={'quality': 1.0}
        )
        
        await validator.run_validation_test(
            prompt_id='analytics_test',
            prompt_content='Analytics test prompt',
            scenarios=[scenario.scenario_id]
        )
        
        # Get analytics
        analytics = await validator.get_test_analytics(days_back=1)
        
        assert 'period' in analytics
        assert 'summary' in analytics
        assert 'performance_metrics' in analytics
        assert analytics['summary']['total_tests'] >= 1


class TestIntegration:
    """Integration tests for the complete pipeline"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self, temp_dir):
        """Test convenience functions"""
        # Test run_full_pipeline for specific agents
        pipeline = PromptImprovementPipeline(temp_dir)
        
        # Mock the execution manager
        mock_results = Mock()
        mock_results.execution_id = 'test_exec'
        mock_results.improvement_summary = {'total_improvements': 5, 'deployed_improvements': 3}
        mock_results.agent_results = {'Documentation': {}, 'Engineer': {}}
        mock_results.recommendations = ['Test recommendation']
        
        pipeline.execution_manager.run_full_pipeline = AsyncMock(return_value=mock_results)
        
        results = await pipeline.run_full_pipeline(['Documentation', 'Engineer'])
        
        assert results.execution_id == 'test_exec'
        assert results.improvement_summary['total_improvements'] == 5
        assert results.improvement_summary['deployed_improvements'] == 3
        assert len(results.agent_results) == 2
    
    @pytest.mark.asyncio
    async def test_pipeline_dashboard(self, temp_dir):
        """Test pipeline dashboard generation"""
        pipeline = PromptImprovementPipeline(temp_dir)
        
        # Mock health status
        mock_health = Mock()
        mock_health.status = 'healthy'
        mock_health.active_executions = 0
        mock_health.recent_failures = 0
        mock_health.success_rate = 0.95
        mock_health.average_execution_time = 120.5
        mock_health.storage_usage_mb = 150.0
        mock_health.alerts = []
        mock_health.last_check = datetime.now()
        
        pipeline.monitoring.check_pipeline_health = AsyncMock(return_value=mock_health)
        
        # Get health status (equivalent to dashboard)
        health = await pipeline.get_pipeline_health()
        
        assert health['status'] == 'healthy'
        assert health['active_executions'] == 0
        assert health['success_rate'] == 0.95
            assert 'active_executions' in dashboard
            assert 'system_status' in dashboard
    
    @pytest.mark.asyncio
    async def test_error_handling(self, temp_dir):
        """Test error handling in pipeline"""
        config = {'base_path': temp_dir}
        pipeline = PromptImprovementPipeline(config)
        
        # Test with invalid agent type
        with pytest.raises(Exception):
            await pipeline.run_targeted_improvement('InvalidAgent')
        
        # Test pause/resume with invalid execution ID
        success = await pipeline.pause_pipeline('invalid_id')
        assert success == False
        
        success = await pipeline.resume_pipeline('invalid_id')
        assert success == False
        
        success = await pipeline.cancel_pipeline('invalid_id')
        assert success == False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_dir):
        """Test concurrent pipeline operations"""
        config = {'base_path': temp_dir}
        pipeline = PromptImprovementPipeline(config)
        
        # Create multiple executions
        execution_ids = []
        for i in range(3):
            execution_id = pipeline._generate_execution_id()
            execution = PipelineExecution(
                execution_id=execution_id,
                config=pipeline.pipeline_config,
                start_time=datetime.now(),
                status=PipelineStatus.RUNNING
            )
            pipeline.active_executions[execution_id] = execution
            execution_ids.append(execution_id)
        
        # Test concurrent operations
        operations = [
            pipeline.pause_pipeline(execution_ids[0]),
            pipeline.pause_pipeline(execution_ids[1]),
            pipeline.cancel_pipeline(execution_ids[2])
        ]
        
        results = await asyncio.gather(*operations)
        
        assert all(results)  # All operations should succeed
        assert len(pipeline.active_executions) == 2  # One cancelled, two paused
    
    @pytest.mark.asyncio
    async def test_storage_persistence(self, temp_dir):
        """Test storage persistence"""
        config = {'base_path': temp_dir}
        pipeline = PromptImprovementPipeline(config)
        
        # Create execution
        execution = PipelineExecution(
            execution_id='persist_test',
            config=pipeline.pipeline_config,
            start_time=datetime.now(),
            status=PipelineStatus.COMPLETED,
            total_improvements=5
        )
        
        # Save execution
        await pipeline._save_execution_record(execution)
        
        # Load executions
        executions = await pipeline._get_executions_since(datetime.now() - timedelta(hours=1))
        
        assert len(executions) == 1
        assert executions[0].execution_id == 'persist_test'
        assert executions[0].total_improvements == 5
        assert executions[0].status == PipelineStatus.COMPLETED


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])