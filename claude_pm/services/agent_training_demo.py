"""
Agent Training System Demo - Phase 4 Implementation
=================================================

Comprehensive demo of the agent-specific training system showing:
- Agent-specific training strategies
- Continuous learning and adaptation
- Advanced analytics and forecasting
- Multi-modal training support
- Integration with agent hierarchy
- Distributed processing capabilities

This demonstrates the complete Phase 4 implementation of the automatic prompt evaluation system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from claude_pm.core.config import Config
from claude_pm.services.agent_trainer import AgentTrainer, TrainingMode, TrainingDataFormat
from claude_pm.services.agent_training_integration import AgentTrainingIntegration
from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentTrainingDemo:
    """
    Comprehensive demo of the agent training system.
    
    Demonstrates all Phase 4 features in a realistic scenario.
    """
    
    def __init__(self):
        """Initialize demo with test configuration."""
        self.config = Config({
            "agent_training_enabled": True,
            "training_storage_path": "~/.claude-pm/training/demo",
            "distributed_training": True,
            "continuous_learning": True,
            "performance_forecasting": True,
            "multi_modal_training": True,
            "training_cache_enabled": True,
            "training_cache_ttl_hours": 2
        })
        
        # Initialize components
        self.agent_trainer = None
        self.training_integration = None
        self.correction_capture = None
        
        # Demo data for different agent types
        self.demo_scenarios = {
            "engineer": [
                {
                    "original_response": "def fibonacci(n): return fibonacci(n-1) + fibonacci(n-2) if n > 1 else n",
                    "user_correction": "def fibonacci(n):\n    if n <= 1:\n        return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b",
                    "task_description": "Implement fibonacci function efficiently",
                    "context": {"performance_critical": True, "language": "python"}
                },
                {
                    "original_response": "import os\nfiles = os.listdir('.')",
                    "user_correction": "import os\nfrom pathlib import Path\n\ntry:\n    files = list(Path('.').iterdir())\n    files = [f for f in files if f.is_file()]\nexcept PermissionError:\n    print('Permission denied')\n    files = []",
                    "task_description": "List files in current directory",
                    "context": {"error_handling": True, "modern_python": True}
                }
            ],
            "documentation": [
                {
                    "original_response": "This function calculates fibonacci numbers.",
                    "user_correction": "## Fibonacci Function\n\nCalculates the nth Fibonacci number using an iterative approach.\n\n**Parameters:**\n- n (int): The position in the Fibonacci sequence (0-indexed)\n\n**Returns:**\n- int: The nth Fibonacci number\n\n**Example:**\n```python\nresult = fibonacci(10)\nprint(result)  # Output: 55\n```\n\n**Time Complexity:** O(n)\n**Space Complexity:** O(1)",
                    "task_description": "Document fibonacci function",
                    "context": {"audience": "developers", "format": "markdown"}
                },
                {
                    "original_response": "The API endpoint accepts POST requests.",
                    "user_correction": "## API Endpoint Documentation\n\n### POST /api/users\n\nCreates a new user account.\n\n**Request Body:**\n```json\n{\n  \"username\": \"string\",\n  \"email\": \"string\",\n  \"password\": \"string\"\n}\n```\n\n**Response:**\n- **201 Created:** User created successfully\n- **400 Bad Request:** Invalid input data\n- **409 Conflict:** User already exists\n\n**Example:**\n```bash\ncurl -X POST /api/users \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\"username\":\"john\",\"email\":\"john@example.com\",\"password\":\"secret\"}'\n```",
                    "task_description": "Document API endpoint",
                    "context": {"api_documentation": True, "include_examples": True}
                }
            ],
            "qa": [
                {
                    "original_response": "Tests passed.",
                    "user_correction": "## Test Results Summary\n\n**Overall Status:** ✅ PASSED\n\n### Test Coverage\n- **Unit Tests:** 147/150 passed (98.0%)\n- **Integration Tests:** 23/25 passed (92.0%)\n- **End-to-End Tests:** 12/12 passed (100%)\n\n### Performance Metrics\n- **Total Execution Time:** 2.3 minutes\n- **Memory Usage:** Peak 256MB\n- **CPU Usage:** Average 45%\n\n### Failed Tests\n1. `test_user_login_timeout` - Network timeout simulation\n2. `test_data_validation_edge_case` - Boundary value testing\n3. `test_concurrent_access` - Race condition detection\n\n### Recommendations\n- Fix timeout handling in authentication module\n- Review data validation for edge cases\n- Implement proper locking for concurrent access",
                    "task_description": "Analyze test results",
                    "context": {"comprehensive_report": True, "actionable_insights": True}
                }
            ],
            "research": [
                {
                    "original_response": "Machine learning is useful for data analysis.",
                    "user_correction": "## Machine Learning for Data Analysis: Comprehensive Overview\n\n### Executive Summary\nMachine learning (ML) has revolutionized data analysis by enabling automated pattern recognition, predictive modeling, and intelligent decision-making from large datasets.\n\n### Key Applications\n1. **Predictive Analytics** - Forecasting trends and outcomes\n2. **Classification** - Categorizing data into predefined classes\n3. **Clustering** - Discovering hidden patterns in data\n4. **Anomaly Detection** - Identifying outliers and unusual patterns\n\n### Popular Algorithms\n- **Supervised Learning:** Linear Regression, Random Forest, SVM\n- **Unsupervised Learning:** K-Means, DBSCAN, PCA\n- **Deep Learning:** Neural Networks, CNN, RNN\n\n### Industry Impact\n- **Healthcare:** Disease prediction, drug discovery\n- **Finance:** Fraud detection, algorithmic trading\n- **Technology:** Recommendation systems, NLP\n\n### Future Trends\n- AutoML and democratization of ML\n- Edge computing and real-time analytics\n- Explainable AI and interpretability\n\n### References\n- [Recent studies and publications]\n- [Industry reports and whitepapers]",
                    "task_description": "Research machine learning applications",
                    "context": {"depth": "comprehensive", "audience": "technical"}
                }
            ],
            "ops": [
                {
                    "original_response": "Deploy the application to production.",
                    "user_correction": "## Production Deployment Plan\n\n### Pre-Deployment Checklist\n- [ ] All tests passing (unit, integration, e2e)\n- [ ] Security scan completed\n- [ ] Performance benchmarks met\n- [ ] Database migrations prepared\n- [ ] Monitoring and alerting configured\n\n### Deployment Strategy\n**Blue-Green Deployment** with automatic rollback\n\n1. **Preparation Phase**\n   - Scale up green environment\n   - Deploy new version to green\n   - Run smoke tests\n\n2. **Cutover Phase**\n   - Switch traffic to green environment\n   - Monitor key metrics for 15 minutes\n   - Validate application health\n\n3. **Verification Phase**\n   - Check error rates < 0.1%\n   - Verify response times < 200ms\n   - Confirm all services healthy\n\n### Rollback Plan\n- **Trigger:** Error rate > 1% OR response time > 500ms\n- **Action:** Immediate traffic switch to blue environment\n- **Timeline:** Complete rollback within 2 minutes\n\n### Monitoring\n- Real-time dashboards active\n- Automated alerts configured\n- On-call team notified\n\n### Post-Deployment\n- Monitor for 24 hours\n- Collect performance metrics\n- Update deployment documentation",
                    "task_description": "Plan production deployment",
                    "context": {"risk_management": True, "monitoring": True}
                }
            ],
            "security": [
                {
                    "original_response": "The system appears secure.",
                    "user_correction": "## Security Assessment Report\n\n### Executive Summary\n**Risk Level:** MEDIUM\n**Critical Issues:** 0\n**High Priority:** 2\n**Medium Priority:** 5\n**Low Priority:** 3\n\n### Vulnerability Analysis\n\n#### High Priority Issues\n1. **Authentication Bypass** (CVE-2023-XXXX)\n   - **Impact:** Unauthorized access to admin panel\n   - **Recommendation:** Implement multi-factor authentication\n   - **Timeline:** Fix within 48 hours\n\n2. **SQL Injection** in user search\n   - **Impact:** Data exfiltration risk\n   - **Recommendation:** Use parameterized queries\n   - **Timeline:** Fix within 72 hours\n\n#### Medium Priority Issues\n- Weak password policy\n- Missing security headers\n- Unencrypted data transmission\n- Insufficient logging\n- Outdated dependencies\n\n### Compliance Status\n- **SOC 2 Type II:** Compliant\n- **GDPR:** Requires attention (data retention)\n- **HIPAA:** Not applicable\n- **PCI DSS:** Compliant\n\n### Recommendations\n1. **Immediate Actions** (0-7 days)\n   - Patch high-priority vulnerabilities\n   - Enable security monitoring\n   - Update critical dependencies\n\n2. **Short-term Actions** (1-4 weeks)\n   - Implement security training\n   - Enhance monitoring and alerting\n   - Conduct penetration testing\n\n3. **Long-term Actions** (1-6 months)\n   - Establish security review process\n   - Implement zero-trust architecture\n   - Regular security audits\n\n### Next Steps\n- Schedule security team review\n- Create remediation timeline\n- Implement continuous monitoring",
                    "task_description": "Conduct security assessment",
                    "context": {"comprehensive_analysis": True, "risk_assessment": True}
                }
            ]
        }
        
        # Statistics tracking
        self.demo_start_time = None
        self.demo_stats = {
            'training_sessions_completed': 0,
            'improvements_generated': 0,
            'deployments_created': 0,
            'adaptations_applied': 0,
            'predictions_generated': 0,
            'agent_performance': {}
        }
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the training system."""
        print("🚀 Initializing Agent Training System...")
        
        try:
            # Initialize agent trainer
            self.agent_trainer = AgentTrainer(self.config)
            trainer_result = await self.agent_trainer.start_training_system()
            
            # Initialize training integration
            self.training_integration = AgentTrainingIntegration(self.config)
            integration_result = await self.training_integration.start_integration()
            
            # Initialize correction capture
            self.correction_capture = CorrectionCapture(self.config)
            
            print("✅ All components initialized successfully!")
            
            return {
                'initialized': True,
                'trainer_result': trainer_result,
                'integration_result': integration_result,
                'components_ready': True
            }
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return {'initialized': False, 'error': str(e)}
    
    async def run_comprehensive_demo(self) -> Dict[str, Any]:
        """Run comprehensive agent training demo."""
        print("\n🎯 Starting Comprehensive Agent Training Demo...")
        
        self.demo_start_time = time.time()
        
        # Phase 1: Basic agent training
        print("\n📚 Phase 1: Agent-Specific Training")
        await self._demo_agent_specific_training()
        
        # Phase 2: Continuous learning
        print("\n🔄 Phase 2: Continuous Learning and Adaptation")
        await self._demo_continuous_learning()
        
        # Phase 3: Advanced analytics
        print("\n📊 Phase 3: Advanced Analytics and Forecasting")
        await self._demo_advanced_analytics()
        
        # Phase 4: Multi-modal training
        print("\n🎨 Phase 4: Multi-Modal Training Support")
        await self._demo_multi_modal_training()
        
        # Phase 5: Integration with framework
        print("\n🔗 Phase 5: Framework Integration")
        await self._demo_framework_integration()
        
        # Phase 6: Performance optimization
        print("\n⚡ Phase 6: Performance Optimization")
        await self._demo_performance_optimization()
        
        demo_duration = time.time() - self.demo_start_time
        
        return {
            'demo_completed': True,
            'duration_seconds': demo_duration,
            'statistics': self.demo_stats
        }
    
    async def _demo_agent_specific_training(self) -> None:
        """Demo agent-specific training capabilities."""
        print("  → Training different agent types with specialized strategies...")
        
        for agent_type, scenarios in self.demo_scenarios.items():
            print(f"\n    Training {agent_type} agent:")
            
            for i, scenario in enumerate(scenarios[:1]):  # Use first scenario for demo
                try:
                    # Train the agent
                    session = await self.agent_trainer.train_agent_response(
                        agent_type=agent_type,
                        original_response=scenario["original_response"],
                        context=scenario["context"],
                        training_mode=TrainingMode.CONTINUOUS
                    )
                    
                    # Update statistics
                    self.demo_stats['training_sessions_completed'] += 1
                    if session.success:
                        self.demo_stats['improvements_generated'] += 1
                    
                    # Track agent performance
                    if agent_type not in self.demo_stats['agent_performance']:
                        self.demo_stats['agent_performance'][agent_type] = []
                    
                    self.demo_stats['agent_performance'][agent_type].append({
                        'improvement_score': session.improvement_score,
                        'success': session.success,
                        'duration': session.training_duration
                    })
                    
                    print(f"      ✓ Session {session.session_id[:8]}... - Improvement: {session.improvement_score:.1f} points")
                    
                except Exception as e:
                    print(f"      ✗ Training failed: {e}")
        
        print(f"  → Completed {self.demo_stats['training_sessions_completed']} training sessions")
    
    async def _demo_continuous_learning(self) -> None:
        """Demo continuous learning and adaptation."""
        print("  → Demonstrating continuous learning capabilities...")
        
        # Simulate continuous learning by training multiple iterations
        agent_type = "engineer"
        scenarios = self.demo_scenarios[agent_type]
        
        for iteration in range(3):
            print(f"    Learning iteration {iteration + 1}:")
            
            for scenario in scenarios:
                try:
                    # Train with continuous learning mode
                    session = await self.agent_trainer.train_agent_response(
                        agent_type=agent_type,
                        original_response=scenario["original_response"],
                        context={**scenario["context"], "iteration": iteration},
                        training_mode=TrainingMode.CONTINUOUS
                    )
                    
                    print(f"      → Iteration {iteration + 1}: {session.improvement_score:.1f} point improvement")
                    
                    # Simulate adaptation triggers
                    if session.improvement_score < 10.0:
                        print("      → Low improvement detected - triggering adaptation")
                        self.demo_stats['adaptations_applied'] += 1
                    
                except Exception as e:
                    print(f"      ✗ Continuous learning error: {e}")
            
            # Small delay between iterations
            await asyncio.sleep(1)
        
        print("  → Continuous learning demonstration completed")
    
    async def _demo_advanced_analytics(self) -> None:
        """Demo advanced analytics and forecasting."""
        print("  → Generating advanced analytics and performance forecasts...")
        
        try:
            # Get training statistics
            stats = await self.agent_trainer.get_training_statistics()
            
            # Display analytics
            print("    📊 Training Analytics:")
            print(f"      • Total sessions: {stats['system_metrics']['total_sessions']}")
            print(f"      • Success rate: {stats['system_metrics']['successful_sessions'] / max(1, stats['system_metrics']['total_sessions']):.1%}")
            print(f"      • Average improvement: {stats['system_metrics']['average_improvement']:.1f} points")
            
            # Agent performance breakdown
            print("\n    🎯 Agent Performance:")
            for agent_type, performance in stats['agent_performance'].items():
                if performance:
                    avg_improvement = sum(p['improvement_score'] for p in performance) / len(performance)
                    success_rate = sum(1 for p in performance if p['success']) / len(performance)
                    print(f"      • {agent_type}: {avg_improvement:.1f} avg improvement, {success_rate:.1%} success rate")
            
            # Generate dashboard for top performing agent
            if stats['agent_performance']:
                top_agent = max(stats['agent_performance'].keys(), 
                              key=lambda x: len(stats['agent_performance'][x]))
                dashboard = await self.agent_trainer.get_agent_training_dashboard(top_agent)
                
                print(f"\n    📈 {top_agent.title()} Agent Dashboard:")
                print(f"      • Training sessions: {dashboard['overview']['total_training_sessions']}")
                print(f"      • Success rate: {dashboard['overview']['success_rate']:.1%}")
                print(f"      • Average improvement: {dashboard['overview']['average_improvement']:.1f}")
                print(f"      • Active adaptations: {dashboard['adaptations']['active_adaptations']}")
                
                # Show predictions if available
                if dashboard['predictions']['current_predictions']:
                    print("      • Latest predictions:")
                    for pred in dashboard['predictions']['current_predictions'][:2]:
                        print(f"        - {pred['prediction_type']}: {pred['trend_direction']} trend")
                
                self.demo_stats['predictions_generated'] += len(dashboard['predictions']['current_predictions'])
            
        except Exception as e:
            print(f"    ✗ Analytics generation failed: {e}")
        
        print("  → Advanced analytics demonstration completed")
    
    async def _demo_multi_modal_training(self) -> None:
        """Demo multi-modal training support."""
        print("  → Demonstrating multi-modal training capabilities...")
        
        # Test different data formats
        formats = [
            (TrainingDataFormat.CODE, "engineer"),
            (TrainingDataFormat.DOCUMENTATION, "documentation"),
            (TrainingDataFormat.ANALYSIS, "qa"),
            (TrainingDataFormat.CONVERSATION, "research")
        ]
        
        for data_format, agent_type in formats:
            try:
                scenario = self.demo_scenarios[agent_type][0]
                
                # Train with specific data format
                session = await self.agent_trainer.train_agent_response(
                    agent_type=agent_type,
                    original_response=scenario["original_response"],
                    context={
                        **scenario["context"],
                        "data_format": data_format.value,
                        "multi_modal": True
                    },
                    training_mode=TrainingMode.MULTI_MODAL
                )
                
                print(f"    ✓ {data_format.value} format training: {session.improvement_score:.1f} point improvement")
                
            except Exception as e:
                print(f"    ✗ Multi-modal training failed for {data_format.value}: {e}")
        
        print("  → Multi-modal training demonstration completed")
    
    async def _demo_framework_integration(self) -> None:
        """Demo framework integration capabilities."""
        print("  → Demonstrating framework integration...")
        
        try:
            # Test subprocess response training
            agent_type = "engineer"
            scenario = self.demo_scenarios[agent_type][0]
            
            integration_result = await self.training_integration.train_subprocess_response(
                subprocess_id="demo_subprocess_001",
                agent_type=agent_type,
                original_response=scenario["original_response"],
                user_correction=scenario["user_correction"],
                context={
                    **scenario["context"],
                    "subprocess_integration": True
                }
            )
            
            print(f"    ✓ Subprocess training: {integration_result['improvement_score']:.1f} point improvement")
            
            if integration_result['deployment_queued']:
                print("    ✓ Deployment queued for significant improvement")
                self.demo_stats['deployments_created'] += 1
            
            # Test agent deployment
            if integration_result['training_success']:
                deployment_result = await self.training_integration.deploy_trained_agent(
                    agent_type=agent_type,
                    training_session_id=integration_result['session_id'],
                    deployment_tier='user'
                )
                
                if deployment_result['success']:
                    print(f"    ✓ Agent deployed to: {deployment_result['deployment_path']}")
                    self.demo_stats['deployments_created'] += 1
                else:
                    print(f"    ✗ Deployment failed: {deployment_result['error']}")
            
            # Get integration statistics
            integration_stats = await self.training_integration.get_integration_statistics()
            print(f"    📊 Integration metrics:")
            print(f"      • Training requests: {integration_stats['integration_metrics']['training_requests']}")
            print(f"      • Successful deployments: {integration_stats['integration_metrics']['successful_deployments']}")
            print(f"      • Average training time: {integration_stats['integration_metrics']['average_training_time']:.1f}s")
            
        except Exception as e:
            print(f"    ✗ Framework integration failed: {e}")
        
        print("  → Framework integration demonstration completed")
    
    async def _demo_performance_optimization(self) -> None:
        """Demo performance optimization features."""
        print("  → Testing performance optimization...")
        
        try:
            # Test caching performance
            agent_type = "documentation"
            scenario = self.demo_scenarios[agent_type][0]
            
            # First training (cache miss)
            start_time = time.time()
            session1 = await self.agent_trainer.train_agent_response(
                agent_type=agent_type,
                original_response=scenario["original_response"],
                context=scenario["context"],
                training_mode=TrainingMode.CONTINUOUS
            )
            first_time = time.time() - start_time
            
            # Second training (cache hit)
            start_time = time.time()
            session2 = await self.agent_trainer.train_agent_response(
                agent_type=agent_type,
                original_response=scenario["original_response"],
                context=scenario["context"],
                training_mode=TrainingMode.CONTINUOUS
            )
            second_time = time.time() - start_time
            
            # Performance comparison
            improvement = ((first_time - second_time) / first_time) * 100 if first_time > 0 else 0
            print(f"    ✓ Cache performance: {improvement:.1f}% improvement")
            print(f"      • First training: {first_time:.2f}s")
            print(f"      • Second training: {second_time:.2f}s")
            
            # Test distributed processing simulation
            print("    ⚡ Distributed processing simulation:")
            
            # Create multiple training tasks
            tasks = []
            for i in range(5):
                task = self.agent_trainer.train_agent_response(
                    agent_type="engineer",
                    original_response=f"def function_{i}(): pass",
                    context={"task_id": i, "distributed": True},
                    training_mode=TrainingMode.DISTRIBUTED
                )
                tasks.append(task)
            
            # Process tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            distributed_time = time.time() - start_time
            
            successful_tasks = len([r for r in results if not isinstance(r, Exception)])
            print(f"    ✓ Distributed processing: {successful_tasks}/5 tasks completed in {distributed_time:.2f}s")
            print(f"      • Throughput: {successful_tasks/distributed_time:.1f} tasks/second")
            
        except Exception as e:
            print(f"    ✗ Performance optimization failed: {e}")
        
        print("  → Performance optimization demonstration completed")
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive demo report."""
        print("\n📋 Generating Comprehensive Demo Report...")
        
        try:
            # Get system statistics
            training_stats = await self.agent_trainer.get_training_statistics()
            integration_stats = await self.training_integration.get_integration_statistics()
            
            # Generate report
            report = {
                'demo_info': {
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': time.time() - self.demo_start_time if self.demo_start_time else 0,
                    'demo_statistics': self.demo_stats
                },
                'system_performance': {
                    'training_system': training_stats,
                    'integration_system': integration_stats,
                    'overall_effectiveness': self._calculate_overall_effectiveness()
                },
                'agent_analysis': {
                    'agent_performance': self._analyze_agent_performance(),
                    'improvement_trends': self._analyze_improvement_trends(),
                    'adaptation_effectiveness': self._analyze_adaptation_effectiveness()
                },
                'recommendations': self._generate_recommendations(),
                'technical_metrics': {
                    'training_sessions_per_minute': (
                        self.demo_stats['training_sessions_completed'] / 
                        max(1, (time.time() - self.demo_start_time) / 60)
                    ),
                    'average_improvement_score': self._calculate_average_improvement(),
                    'success_rate': self._calculate_success_rate(),
                    'deployment_efficiency': self._calculate_deployment_efficiency()
                }
            }
            
            # Save report
            report_path = self._save_report(report)
            print(f"✅ Demo report saved: {report_path}")
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_effectiveness(self) -> float:
        """Calculate overall system effectiveness."""
        if not self.demo_stats['training_sessions_completed']:
            return 0.0
        
        success_rate = (
            self.demo_stats['improvements_generated'] / 
            self.demo_stats['training_sessions_completed']
        )
        
        deployment_rate = (
            self.demo_stats['deployments_created'] / 
            max(1, self.demo_stats['improvements_generated'])
        )
        
        return (success_rate * 0.7 + deployment_rate * 0.3) * 100
    
    def _analyze_agent_performance(self) -> Dict[str, Any]:
        """Analyze agent performance across all types."""
        analysis = {}
        
        for agent_type, performance_data in self.demo_stats['agent_performance'].items():
            if performance_data:
                improvements = [p['improvement_score'] for p in performance_data]
                successes = [p['success'] for p in performance_data]
                durations = [p['duration'] for p in performance_data]
                
                analysis[agent_type] = {
                    'total_sessions': len(performance_data),
                    'average_improvement': sum(improvements) / len(improvements),
                    'success_rate': sum(successes) / len(successes),
                    'average_duration': sum(durations) / len(durations),
                    'max_improvement': max(improvements),
                    'min_improvement': min(improvements),
                    'consistency_score': 1.0 - (max(improvements) - min(improvements)) / 100.0
                }
        
        return analysis
    
    def _analyze_improvement_trends(self) -> Dict[str, Any]:
        """Analyze improvement trends."""
        trends = {}
        
        for agent_type, performance_data in self.demo_stats['agent_performance'].items():
            if len(performance_data) > 1:
                improvements = [p['improvement_score'] for p in performance_data]
                
                # Calculate trend
                if len(improvements) >= 2:
                    trend_slope = (improvements[-1] - improvements[0]) / (len(improvements) - 1)
                    trends[agent_type] = {
                        'trend_direction': 'improving' if trend_slope > 0 else 'declining' if trend_slope < 0 else 'stable',
                        'trend_slope': trend_slope,
                        'recent_average': sum(improvements[-3:]) / min(3, len(improvements)),
                        'overall_average': sum(improvements) / len(improvements)
                    }
        
        return trends
    
    def _analyze_adaptation_effectiveness(self) -> Dict[str, Any]:
        """Analyze adaptation effectiveness."""
        return {
            'adaptations_triggered': self.demo_stats['adaptations_applied'],
            'adaptation_rate': (
                self.demo_stats['adaptations_applied'] / 
                max(1, self.demo_stats['training_sessions_completed'])
            ),
            'effectiveness_score': 0.75  # Simulated effectiveness
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on demo results."""
        recommendations = []
        
        # Overall performance recommendations
        if self.demo_stats['improvements_generated'] < self.demo_stats['training_sessions_completed'] * 0.8:
            recommendations.append("Consider adjusting training strategies for better improvement rates")
        
        # Agent-specific recommendations
        for agent_type, performance_data in self.demo_stats['agent_performance'].items():
            if performance_data:
                avg_improvement = sum(p['improvement_score'] for p in performance_data) / len(performance_data)
                if avg_improvement < 15.0:
                    recommendations.append(f"Review {agent_type} agent training templates for effectiveness")
        
        # System recommendations
        if self.demo_stats['deployments_created'] == 0:
            recommendations.append("No deployments created - consider lowering deployment thresholds")
        
        if self.demo_stats['adaptations_applied'] < 2:
            recommendations.append("Consider more aggressive adaptation triggers for continuous improvement")
        
        return recommendations
    
    def _calculate_average_improvement(self) -> float:
        """Calculate average improvement across all agents."""
        all_improvements = []
        for performance_data in self.demo_stats['agent_performance'].values():
            all_improvements.extend(p['improvement_score'] for p in performance_data)
        
        return sum(all_improvements) / len(all_improvements) if all_improvements else 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.demo_stats['training_sessions_completed']:
            return 0.0
        
        return self.demo_stats['improvements_generated'] / self.demo_stats['training_sessions_completed']
    
    def _calculate_deployment_efficiency(self) -> float:
        """Calculate deployment efficiency."""
        if not self.demo_stats['improvements_generated']:
            return 0.0
        
        return self.demo_stats['deployments_created'] / self.demo_stats['improvements_generated']
    
    def _save_report(self, report: Dict[str, Any]) -> str:
        """Save demo report to file."""
        # Create reports directory
        reports_dir = Path.home() / '.claude-pm' / 'training' / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_training_demo_report_{timestamp}.json"
        filepath = reports_dir / filename
        
        # Save report
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(filepath)
    
    def print_demo_summary(self, report: Dict[str, Any]) -> None:
        """Print demo summary."""
        print("\n" + "="*80)
        print("🎯 AGENT TRAINING SYSTEM DEMO SUMMARY")
        print("="*80)
        
        demo_info = report['demo_info']
        technical_metrics = report['technical_metrics']
        
        print(f"Demo Duration: {demo_info['duration_seconds']:.1f}s")
        print(f"Training Sessions: {demo_info['demo_statistics']['training_sessions_completed']}")
        print(f"Improvements Generated: {demo_info['demo_statistics']['improvements_generated']}")
        print(f"Deployments Created: {demo_info['demo_statistics']['deployments_created']}")
        print(f"Adaptations Applied: {demo_info['demo_statistics']['adaptations_applied']}")
        print(f"Predictions Generated: {demo_info['demo_statistics']['predictions_generated']}")
        
        print(f"\n📊 Technical Metrics:")
        print(f"Training Rate: {technical_metrics['training_sessions_per_minute']:.1f} sessions/minute")
        print(f"Average Improvement: {technical_metrics['average_improvement_score']:.1f} points")
        print(f"Success Rate: {technical_metrics['success_rate']:.1%}")
        print(f"Deployment Efficiency: {technical_metrics['deployment_efficiency']:.1%}")
        print(f"Overall Effectiveness: {report['system_performance']['overall_effectiveness']:.1f}%")
        
        print(f"\n🎯 Agent Performance:")
        for agent_type, analysis in report['agent_analysis']['agent_performance'].items():
            print(f"  {agent_type.title()}: {analysis['average_improvement']:.1f} avg improvement, "
                  f"{analysis['success_rate']:.1%} success rate")
        
        print(f"\n💡 Key Recommendations:")
        for i, recommendation in enumerate(report['recommendations'][:5], 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n✅ Demo completed successfully! All Phase 4 features demonstrated.")
        print("="*80)
    
    async def shutdown_system(self) -> None:
        """Shutdown the training system."""
        print("\n🔄 Shutting down training system...")
        
        try:
            # Stop training integration
            if self.training_integration:
                await self.training_integration.stop_integration()
            
            # Stop agent trainer
            if self.agent_trainer:
                await self.agent_trainer.stop_training_system()
            
            print("✅ System shutdown completed")
            
        except Exception as e:
            print(f"⚠️  Shutdown error: {e}")


async def main():
    """Run the agent training demo."""
    print("🚀 Starting Agent Training System Demo - Phase 4")
    print("="*80)
    
    demo = AgentTrainingDemo()
    
    try:
        # Initialize system
        init_result = await demo.initialize_system()
        if not init_result['initialized']:
            print(f"❌ Initialization failed: {init_result.get('error', 'Unknown error')}")
            return
        
        # Run comprehensive demo
        demo_result = await demo.run_comprehensive_demo()
        
        # Generate report
        report = await demo.generate_comprehensive_report()
        
        # Print summary
        demo.print_demo_summary(report)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Shutdown system
        await demo.shutdown_system()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())