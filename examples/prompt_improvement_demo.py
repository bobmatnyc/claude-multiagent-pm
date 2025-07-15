#!/usr/bin/env python3
"""
Prompt Improvement Pipeline Demonstration

This script demonstrates the complete automated prompt improvement pipeline
including all phases: correction capture, pattern analysis, improvement
generation, validation, and deployment.

Usage:
    python examples/prompt_improvement_demo.py --mode [full|targeted|validation|dashboard]

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.prompt_improvement_pipeline import (
    PromptImprovementPipeline,
    run_pipeline_for_agents,
    get_pipeline_dashboard
)
from claude_pm.services.prompt_improver import (
    PromptImprover,
    analyze_and_improve_prompts,
    get_improvement_dashboard
)
from claude_pm.services.prompt_validator import (
    PromptValidator,
    run_quick_validation,
    compare_prompts
)
from claude_pm.services.prompt_template_manager import (
    PromptTemplateManager,
    create_agent_template,
    get_deployment_dashboard
)
from claude_pm.services.pattern_analyzer import (
    PatternAnalyzer,
    run_comprehensive_analysis
)


class PromptImprovementDemo:
    """Demonstration of the prompt improvement pipeline"""
    
    def __init__(self):
        """Initialize demo"""
        self.demo_config = {
            'base_path': '.claude-pm/demo',
            'agent_types': ['Documentation', 'QA', 'Engineer', 'Ops'],
            'correction_analysis_days': 14,
            'pattern_detection_threshold': 0.6,
            'improvement_confidence_threshold': 0.7,
            'validation_sample_size': 5,
            'auto_deployment_enabled': False,
            'monitoring_interval': 300
        }
        
        # Initialize components
        self.pipeline = PromptImprovementPipeline(self.demo_config)
        self.improver = PromptImprover(self.demo_config)
        self.validator = PromptValidator(self.demo_config)
        self.template_manager = PromptTemplateManager(self.demo_config)
        self.pattern_analyzer = PatternAnalyzer(self.demo_config)
        
        print("🤖 Prompt Improvement Pipeline Demo Initialized")
        print(f"📁 Demo workspace: {self.demo_config['base_path']}")
        print(f"🔧 Agent types: {', '.join(self.demo_config['agent_types'])}")
        print()
    
    async def run_full_pipeline_demo(self):
        """Demonstrate the complete pipeline execution"""
        print("🚀 Starting Full Pipeline Demo")
        print("=" * 50)
        
        try:
            # Phase 1: Setup demo data
            print("\n📊 Phase 1: Setting up demo data...")
            await self._setup_demo_data()
            
            # Phase 2: Run pipeline analysis
            print("\n🔍 Phase 2: Running pipeline analysis...")
            results = await self.pipeline.run_full_pipeline(
                agent_types=['Documentation', 'Engineer']
            )
            
            # Phase 3: Display results
            print("\n📈 Phase 3: Pipeline Results")
            print(f"✅ Execution ID: {results.execution_id}")
            print(f"📊 Total improvements: {results.improvement_summary['total_improvements']}")
            print(f"🚀 Deployed improvements: {results.improvement_summary['deployed_improvements']}")
            print(f"📋 Recommendations: {len(results.recommendations)}")
            
            # Show agent-specific results
            for agent_type, agent_results in results.agent_results.items():
                print(f"\n🤖 {agent_type} Agent Results:")
                corrections = agent_results.get('corrections', {})
                patterns = agent_results.get('patterns', {})
                improvements = agent_results.get('improvements', {})
                
                print(f"   📝 Corrections analyzed: {corrections.get('corrections_found', 0)}")
                print(f"   🔍 Patterns detected: {patterns.get('significant_patterns', 0)}")
                print(f"   💡 Improvements generated: {improvements.get('confident_improvements', 0)}")
            
            # Show recommendations
            if results.recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(results.recommendations, 1):
                    print(f"   {i}. {rec}")
            
            print(f"\n✅ Full pipeline demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Pipeline demo failed: {e}")
            raise
    
    async def run_targeted_improvement_demo(self):
        """Demonstrate targeted improvement for specific agent"""
        print("🎯 Starting Targeted Improvement Demo")
        print("=" * 50)
        
        try:
            # Setup demo data
            print("\n📊 Setting up targeted improvement demo...")
            await self._setup_demo_data()
            
            # Run targeted improvement for Documentation agent
            print("\n🔍 Running targeted improvement for Documentation agent...")
            results = await self.pipeline.run_targeted_improvement('Documentation')
            
            # Display results
            print(f"\n📈 Targeted Improvement Results:")
            print(f"✅ Execution ID: {results['execution_id']}")
            print(f"🤖 Agent Type: {results['agent_type']}")
            print(f"🔍 Patterns analyzed: {results['patterns_analyzed']}")
            print(f"💡 Improvements generated: {results['improvements_generated']}")
            print(f"✅ Improvements validated: {results['improvements_validated']}")
            
            # Show pattern details
            if results['patterns']:
                print(f"\n📊 Pattern Analysis:")
                for pattern in results['patterns'][:3]:  # Show top 3
                    print(f"   🔍 Pattern: {pattern['pattern_type']}")
                    print(f"      Frequency: {pattern['frequency']}")
                    print(f"      Confidence: {pattern['confidence']:.2f}")
                    print(f"      Severity: {pattern['severity']}")
            
            # Show improvement details
            if results['validated_improvements']:
                print(f"\n💡 Validated Improvements:")
                for imp in results['validated_improvements'][:2]:  # Show top 2
                    print(f"   💡 Improvement: {imp['improvement_id'][:12]}...")
                    print(f"      Strategy: {imp['strategy']}")
                    print(f"      Confidence: {imp['confidence_score']:.2f}")
                    print(f"      Reason: {imp['improvement_reason']}")
            
            print(f"\n✅ Targeted improvement demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Targeted improvement demo failed: {e}")
            raise
    
    async def run_validation_demo(self):
        """Demonstrate prompt validation and A/B testing"""
        print("🧪 Starting Validation Demo")
        print("=" * 50)
        
        try:
            # Create test prompts
            print("\n📝 Creating test prompts...")
            
            prompt_a = """
            **Documentation Agent**: Generate comprehensive documentation
            
            **Task**: Create detailed documentation for the given code or feature
            1. Analyze the code structure and functionality
            2. Generate clear, concise documentation
            3. Include examples and usage patterns
            4. Ensure completeness and accuracy
            
            **Context**: You are a documentation specialist focused on clarity and completeness
            **Authority**: Generate documentation, examples, and usage guides
            """
            
            prompt_b = """
            **Documentation Agent**: Generate comprehensive documentation with enhanced guidelines
            
            **Task**: Create detailed documentation for the given code or feature
            1. Analyze the code structure and functionality
            2. Generate clear, concise documentation with proper formatting
            3. Include comprehensive examples and usage patterns
            4. Add troubleshooting and FAQ sections
            5. Ensure completeness, accuracy, and consistency
            
            **Context**: You are a documentation specialist focused on clarity, completeness, and user experience
            **Authority**: Generate documentation, examples, usage guides, and troubleshooting content
            **Quality Standards**: Follow documentation best practices and style guides
            """
            
            # Run quick validation
            print("\n🔍 Running quick validation for Prompt A...")
            validation_a = await run_quick_validation(prompt_a, 'Documentation')
            
            print(f"📊 Prompt A Results:")
            print(f"   Score: {validation_a['overall_score']:.2f}")
            print(f"   Success Rate: {validation_a['success_rate']:.2f}")
            print(f"   Recommendations: {len(validation_a['recommendations'])}")
            
            print("\n🔍 Running quick validation for Prompt B...")
            validation_b = await run_quick_validation(prompt_b, 'Documentation')
            
            print(f"📊 Prompt B Results:")
            print(f"   Score: {validation_b['overall_score']:.2f}")
            print(f"   Success Rate: {validation_b['success_rate']:.2f}")
            print(f"   Recommendations: {len(validation_b['recommendations'])}")
            
            # Run A/B comparison
            print("\n⚖️  Running A/B comparison...")
            comparison = await compare_prompts(prompt_a, prompt_b, 'Documentation')
            
            print(f"📊 A/B Test Results:")
            print(f"   Winner: {comparison['winner'] or 'No significant difference'}")
            print(f"   Confidence Level: {comparison['confidence_level']:.2f}")
            print(f"   Statistical Significance: {comparison['statistical_significance']:.4f}")
            print(f"   Recommendation: {comparison['recommendation']}")
            
            # Show improvement metrics
            if comparison['improvement_metrics']:
                metrics = comparison['improvement_metrics']
                print(f"\n📈 Improvement Metrics:")
                print(f"   Success Rate Change: {metrics.get('success_rate_improvement', 0):.3f}")
                print(f"   Score Change: {metrics.get('score_improvement', 0):.3f}")
                print(f"   Time Change: {metrics.get('execution_time_improvement', 0):.3f}s")
            
            print(f"\n✅ Validation demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Validation demo failed: {e}")
            raise
    
    async def run_dashboard_demo(self):
        """Demonstrate dashboard and monitoring capabilities"""
        print("📊 Starting Dashboard Demo")
        print("=" * 50)
        
        try:
            # Get pipeline dashboard
            print("\n🚀 Getting pipeline dashboard...")
            pipeline_dashboard = await get_pipeline_dashboard()
            
            print(f"📊 Pipeline Dashboard:")
            print(f"   Status: {pipeline_dashboard['health_status']['pipeline_status']}")
            print(f"   Active Executions: {pipeline_dashboard['health_status']['active_executions']}")
            print(f"   System Available: {pipeline_dashboard['system_status']['pipeline_available']}")
            
            # Show analytics if available
            analytics = pipeline_dashboard.get('analytics', {})
            if analytics.get('execution_summary'):
                exec_summary = analytics['execution_summary']
                print(f"\n📈 Execution Analytics:")
                print(f"   Total Executions: {exec_summary.get('total_executions', 0)}")
                print(f"   Success Rate: {exec_summary.get('success_rate', 0):.2f}")
                print(f"   Avg Execution Time: {exec_summary.get('avg_execution_time', 0):.0f}s")
            
            # Get improvement dashboard
            print("\n💡 Getting improvement dashboard...")
            improvement_dashboard = await get_improvement_dashboard()
            
            print(f"📊 Improvement Dashboard:")
            if improvement_dashboard.get('metrics'):
                metrics = improvement_dashboard['metrics']
                print(f"   Last 7 Days: {metrics.get('last_7_days', {}).get('summary', {})}")
                print(f"   Last 30 Days: {metrics.get('last_30_days', {}).get('summary', {})}")
            
            # Get template deployment dashboard
            print("\n🚀 Getting deployment dashboard...")
            deployment_dashboard = await get_deployment_dashboard()
            
            print(f"📊 Deployment Dashboard:")
            if deployment_dashboard.get('summary'):
                summary = deployment_dashboard['summary']
                print(f"   Total Templates: {summary.get('total_templates', 0)}")
                print(f"   Active Deployments: {summary.get('active_deployments', 0)}")
                print(f"   Template Types: {summary.get('template_types', 0)}")
            
            # Show system health
            print("\n🏥 System Health:")
            component_health = pipeline_dashboard['health_status'].get('component_health', {})
            for component, health in component_health.items():
                status = health.get('status', 'unknown')
                print(f"   {component}: {status}")
            
            print(f"\n✅ Dashboard demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Dashboard demo failed: {e}")
            raise
    
    async def run_component_demo(self):
        """Demonstrate individual component capabilities"""
        print("🧩 Starting Component Demo")
        print("=" * 50)
        
        try:
            # Demo Pattern Analyzer
            print("\n🔍 Pattern Analyzer Demo:")
            mock_corrections = await self._create_mock_corrections()
            analysis_result = await run_comprehensive_analysis(mock_corrections, 'Documentation')
            
            print(f"   Patterns Detected: {analysis_result['patterns_detected']}")
            print(f"   Anomalies Found: {analysis_result['anomalies_detected']}")
            print(f"   ML Support: {analysis_result['has_ml_support']}")
            
            # Demo Prompt Improver
            print("\n💡 Prompt Improver Demo:")
            improvement_result = await analyze_and_improve_prompts('Documentation', days_back=14)
            
            print(f"   Patterns Found: {improvement_result['patterns_found']}")
            print(f"   Improvements Generated: {improvement_result['improvements_generated']}")
            print(f"   Improvements Validated: {improvement_result['improvements_validated']}")
            
            # Demo Template Manager
            print("\n📝 Template Manager Demo:")
            template = await create_agent_template(
                'Documentation',
                'Demo template content for Documentation agent',
                'demo_system'
            )
            
            print(f"   Template Created: {template.template_id}")
            print(f"   Version: {template.version}")
            print(f"   Status: {template.status.value}")
            
            # Demo Validator
            print("\n🧪 Validator Demo:")
            validator_result = await run_quick_validation(
                'Demo prompt content for validation',
                'Documentation'
            )
            
            print(f"   Overall Score: {validator_result['overall_score']:.2f}")
            print(f"   Success Rate: {validator_result['success_rate']:.2f}")
            print(f"   Test Details: {len(validator_result['test_details'])} tests")
            
            print(f"\n✅ Component demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Component demo failed: {e}")
            raise
    
    async def _setup_demo_data(self):
        """Setup demo data for testing"""
        try:
            # Create demo base directory
            demo_base = Path(self.demo_config['base_path'])
            demo_base.mkdir(parents=True, exist_ok=True)
            
            # Create mock correction data
            corrections = await self._create_mock_corrections()
            
            # Save demo data
            demo_data_file = demo_base / 'demo_data.json'
            with open(demo_data_file, 'w') as f:
                json.dump({
                    'corrections': [
                        {
                            'agent_type': c.agent_type,
                            'error_type': c.error_type,
                            'timestamp': c.timestamp.isoformat(),
                            'issue_description': c.issue_description,
                            'correction_applied': c.correction_applied
                        }
                        for c in corrections
                    ],
                    'created_at': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"   📊 Created {len(corrections)} mock corrections")
            print(f"   💾 Saved demo data to {demo_data_file}")
            
        except Exception as e:
            print(f"❌ Demo data setup failed: {e}")
            raise
    
    async def _create_mock_corrections(self):
        """Create mock correction data for demonstration"""
        from types import SimpleNamespace
        
        corrections = []
        
        # Documentation agent corrections
        doc_corrections = [
            {
                'agent_type': 'Documentation',
                'error_type': 'format_error',
                'issue_description': 'Missing proper section headers',
                'correction_applied': 'Added consistent section headers with proper formatting'
            },
            {
                'agent_type': 'Documentation',
                'error_type': 'incomplete_info',
                'issue_description': 'Missing usage examples',
                'correction_applied': 'Added comprehensive usage examples and code snippets'
            },
            {
                'agent_type': 'Documentation',
                'error_type': 'format_error',
                'issue_description': 'Inconsistent code block formatting',
                'correction_applied': 'Standardized code block formatting with proper syntax highlighting'
            }
        ]
        
        # Engineer agent corrections
        eng_corrections = [
            {
                'agent_type': 'Engineer',
                'error_type': 'logic_error',
                'issue_description': 'Incorrect error handling logic',
                'correction_applied': 'Implemented proper try-catch blocks and error propagation'
            },
            {
                'agent_type': 'Engineer',
                'error_type': 'performance_issue',
                'issue_description': 'Inefficient algorithm implementation',
                'correction_applied': 'Optimized algorithm with better time complexity'
            }
        ]
        
        # QA agent corrections
        qa_corrections = [
            {
                'agent_type': 'QA',
                'error_type': 'test_failure',
                'issue_description': 'Incomplete test coverage',
                'correction_applied': 'Added comprehensive test cases for edge cases'
            }
        ]
        
        # Create correction objects
        all_corrections = doc_corrections + eng_corrections + qa_corrections
        
        for i, correction_data in enumerate(all_corrections):
            correction = SimpleNamespace(
                agent_type=correction_data['agent_type'],
                error_type=correction_data['error_type'],
                issue_description=correction_data['issue_description'],
                correction_applied=correction_data['correction_applied'],
                timestamp=datetime.now() - timedelta(hours=i * 2)
            )
            corrections.append(correction)
        
        return corrections
    
    async def show_help(self):
        """Show help information"""
        print("🤖 Prompt Improvement Pipeline Demo")
        print("=" * 50)
        print()
        print("Available demo modes:")
        print("  full         - Complete pipeline execution with all phases")
        print("  targeted     - Targeted improvement for specific agent type")
        print("  validation   - Prompt validation and A/B testing")
        print("  dashboard    - Dashboard and monitoring capabilities")
        print("  components   - Individual component demonstrations")
        print()
        print("Usage:")
        print("  python examples/prompt_improvement_demo.py --mode full")
        print("  python examples/prompt_improvement_demo.py --mode targeted")
        print("  python examples/prompt_improvement_demo.py --mode validation")
        print("  python examples/prompt_improvement_demo.py --mode dashboard")
        print("  python examples/prompt_improvement_demo.py --mode components")
        print()
        print("Features demonstrated:")
        print("  📊 Pattern analysis and anomaly detection")
        print("  💡 Automated prompt improvement generation")
        print("  🧪 A/B testing and validation")
        print("  📝 Template management and versioning")
        print("  🚀 Deployment and monitoring")
        print("  📈 Analytics and reporting")


async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description='Prompt Improvement Pipeline Demo')
    parser.add_argument('--mode', choices=['full', 'targeted', 'validation', 'dashboard', 'components'], 
                       default='full', help='Demo mode to run')
    parser.add_argument('--help-demo', action='store_true', help='Show demo help')
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = PromptImprovementDemo()
    
    if args.help_demo:
        await demo.show_help()
        return
    
    try:
        print(f"🚀 Starting demo in '{args.mode}' mode...")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if args.mode == 'full':
            await demo.run_full_pipeline_demo()
        elif args.mode == 'targeted':
            await demo.run_targeted_improvement_demo()
        elif args.mode == 'validation':
            await demo.run_validation_demo()
        elif args.mode == 'dashboard':
            await demo.run_dashboard_demo()
        elif args.mode == 'components':
            await demo.run_component_demo()
        
        print()
        print("🎉 Demo completed successfully!")
        print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Run the demo
    asyncio.run(main())