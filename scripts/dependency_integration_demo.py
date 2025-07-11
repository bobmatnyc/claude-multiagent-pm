#!/usr/bin/env python3
"""
Dependency Integration Demo Script

Demonstrates CMPM-103 Dependency Management Strategy integration with CMPM-101 Deployment Detection.
This script shows how the DependencyManager works with the DeploymentDetector to provide
deployment-aware dependency resolution and installation.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.dependency_manager import DependencyManager, DependencyType, InstallationMethod


class DependencyIntegrationDemo:
    """Demonstrates dependency management integration with deployment detection."""
    
    def __init__(self):
        self.dependency_manager = None
        self.demo_results = {}
    
    async def run_demo(self):
        """Run the complete dependency integration demo."""
        print("🔧 Claude PM Framework - Dependency Integration Demo")
        print("=" * 60)
        print("CMPM-103: Dependency Management Strategy")
        print("Integration with CMPM-101: Deployment Detection")
        print()
        
        try:
            # Initialize dependency manager
            await self._initialize_dependency_manager()
            
            # Demo 1: Deployment Detection Integration
            await self._demo_deployment_detection()
            
            # Demo 2: Dependency Discovery and Analysis
            await self._demo_dependency_discovery()
            
            # Demo 3: AI-Trackdown-Tools Verification
            await self._demo_ai_trackdown_tools_verification()
            
            # Demo 4: Installation Recommendations
            await self._demo_installation_recommendations()
            
            # Demo 5: Health Monitoring
            await self._demo_health_monitoring()
            
            # Demo 6: Comprehensive Reporting
            await self._demo_comprehensive_reporting()
            
            # Show final results
            await self._show_final_results()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if self.dependency_manager:
                await self.dependency_manager._cleanup()
    
    async def _initialize_dependency_manager(self):
        """Initialize the dependency manager with demo configuration."""
        print("🚀 Initializing Dependency Manager...")
        
        config = {
            "check_interval": 60,
            "auto_install": False,  # Disable auto-install for demo
            "installation_timeout": 30,
            "enable_dependency_monitoring": False  # Disable background monitoring for demo
        }
        
        self.dependency_manager = DependencyManager(config)
        await self.dependency_manager._initialize()
        
        print(f"✅ Dependency Manager initialized")
        print(f"   Service: {self.dependency_manager.name}")
        print(f"   Platform: {self.dependency_manager.platform}")
        print(f"   Python Command: {self.dependency_manager.python_cmd}")
        print()
    
    async def _demo_deployment_detection(self):
        """Demonstrate deployment detection integration."""
        print("🔍 Demo 1: Deployment Detection Integration")
        print("-" * 40)
        
        # Show deployment configuration
        deployment_config = self.dependency_manager.deployment_config
        if deployment_config:
            print("Deployment Configuration:")
            print(f"  Strategy: {deployment_config.get('strategy', 'unknown')}")
            
            config = deployment_config.get('config', {})
            print(f"  Type: {config.get('deploymentType', 'unknown')}")
            print(f"  Platform: {config.get('platform', 'unknown')}")
            print(f"  Confidence: {config.get('confidence', 'unknown')}")
            
            if 'frameworkPath' in config:
                print(f"  Framework Path: {config['frameworkPath']}")
            
            if 'metadata' in config:
                metadata = config['metadata']
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
        else:
            print("  No deployment configuration available")
        
        self.demo_results['deployment_detection'] = {
            'status': 'completed',
            'deployment_config': deployment_config
        }
        
        print()
    
    async def _demo_dependency_discovery(self):
        """Demonstrate dependency discovery and analysis."""
        print("🔍 Demo 2: Dependency Discovery and Analysis")
        print("-" * 40)
        
        dependencies = self.dependency_manager.get_dependencies()
        
        print(f"Discovered {len(dependencies)} dependencies:")
        
        for name, info in dependencies.items():
            status = "✅ Installed" if info.is_installed else "❌ Missing"
            print(f"  {name}: {status}")
            
            if info.is_installed:
                print(f"    Version: {info.version or 'unknown'}")
                print(f"    Method: {info.installation_method.value if info.installation_method else 'unknown'}")
                if info.installation_path:
                    print(f"    Path: {info.installation_path}")
            else:
                print(f"    Required: {info.required_version or 'any'}")
            
            print(f"    Type: {info.type.value}")
            print()
        
        # Show dependency types breakdown
        type_counts = {}
        for info in dependencies.values():
            dep_type = info.type.value
            type_counts[dep_type] = type_counts.get(dep_type, 0) + 1
        
        print("Dependency Types:")
        for dep_type, count in type_counts.items():
            print(f"  {dep_type}: {count}")
        
        self.demo_results['dependency_discovery'] = {
            'status': 'completed',
            'total_dependencies': len(dependencies),
            'installed_dependencies': sum(1 for info in dependencies.values() if info.is_installed),
            'type_breakdown': type_counts
        }
        
        print()
    
    async def _demo_ai_trackdown_tools_verification(self):
        """Demonstrate ai-trackdown-tools verification."""
        print("🔍 Demo 3: AI-Trackdown-Tools Verification")
        print("-" * 40)
        
        # Get ai-trackdown-tools dependency info
        ai_trackdown_info = self.dependency_manager.get_dependency("ai-trackdown-tools")
        
        if ai_trackdown_info:
            print("AI-Trackdown-Tools Dependency:")
            print(f"  Installed: {ai_trackdown_info.is_installed}")
            print(f"  Version: {ai_trackdown_info.version or 'unknown'}")
            print(f"  Method: {ai_trackdown_info.installation_method.value if ai_trackdown_info.installation_method else 'unknown'}")
            print(f"  Required: {ai_trackdown_info.required_version or 'any'}")
            
            # Verify functionality
            print("\nVerifying AI-Trackdown-Tools functionality...")
            is_functional = await self.dependency_manager.verify_ai_trackdown_tools()
            print(f"  Functional: {'✅ Yes' if is_functional else '❌ No'}")
            
            self.demo_results['ai_trackdown_tools'] = {
                'status': 'completed',
                'installed': ai_trackdown_info.is_installed,
                'functional': is_functional,
                'version': ai_trackdown_info.version
            }
        else:
            print("❌ AI-Trackdown-Tools dependency not found")
            self.demo_results['ai_trackdown_tools'] = {
                'status': 'error',
                'message': 'dependency not found'
            }
        
        print()
    
    async def _demo_installation_recommendations(self):
        """Demonstrate installation recommendations."""
        print("🔍 Demo 4: Installation Recommendations")
        print("-" * 40)
        
        recommendations = await self.dependency_manager.get_installation_recommendations()
        
        if recommendations:
            print("Installation Recommendations:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")
        else:
            print("✅ No installation recommendations - all dependencies satisfied")
        
        # Show installation methods for each dependency type
        print("\nAvailable Installation Methods:")
        for dep_type in DependencyType:
            best_method = self.dependency_manager._select_best_installation_method(dep_type, {})
            print(f"  {dep_type.value}: {best_method.value}")
        
        self.demo_results['installation_recommendations'] = {
            'status': 'completed',
            'recommendations': recommendations,
            'count': len(recommendations)
        }
        
        print()
    
    async def _demo_health_monitoring(self):
        """Demonstrate health monitoring."""
        print("🔍 Demo 5: Health Monitoring")
        print("-" * 40)
        
        health_checks = await self.dependency_manager._health_check()
        
        print("Health Check Results:")
        for check_name, status in health_checks.items():
            status_icon = "✅" if status else "❌"
            print(f"  {check_name}: {status_icon} {status}")
        
        # Calculate overall health score
        total_checks = len(health_checks)
        passed_checks = sum(1 for status in health_checks.values() if status)
        health_score = round((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        
        print(f"\nOverall Health Score: {health_score}% ({passed_checks}/{total_checks})")
        
        self.demo_results['health_monitoring'] = {
            'status': 'completed',
            'health_checks': health_checks,
            'health_score': health_score,
            'passed_checks': passed_checks,
            'total_checks': total_checks
        }
        
        print()
    
    async def _demo_comprehensive_reporting(self):
        """Demonstrate comprehensive reporting."""
        print("🔍 Demo 6: Comprehensive Reporting")
        print("-" * 40)
        
        report = await self.dependency_manager.generate_dependency_report()
        
        print("Dependency Report:")
        print(f"  Deployment Type: {report.deployment_type}")
        print(f"  Platform: {report.platform}")
        print(f"  Timestamp: {report.timestamp}")
        print(f"  Health Score: {report.health_score}%")
        
        print(f"\nDependency Status:")
        print(f"  Total Dependencies: {len(report.dependencies)}")
        print(f"  Missing Dependencies: {len(report.missing_dependencies)}")
        print(f"  Outdated Dependencies: {len(report.outdated_dependencies)}")
        
        if report.missing_dependencies:
            print("\nMissing Dependencies:")
            for dep in report.missing_dependencies:
                print(f"    - {dep}")
        
        if report.outdated_dependencies:
            print("\nOutdated Dependencies:")
            for dep in report.outdated_dependencies:
                print(f"    - {dep}")
        
        if report.installation_recommendations:
            print("\nInstallation Recommendations:")
            for rec in report.installation_recommendations:
                print(f"    - {rec}")
        
        self.demo_results['comprehensive_reporting'] = {
            'status': 'completed',
            'report': {
                'deployment_type': report.deployment_type,
                'platform': report.platform,
                'health_score': report.health_score,
                'total_dependencies': len(report.dependencies),
                'missing_dependencies': len(report.missing_dependencies),
                'outdated_dependencies': len(report.outdated_dependencies),
                'recommendations': len(report.installation_recommendations)
            }
        }
        
        print()
    
    async def _show_final_results(self):
        """Show final demo results."""
        print("📊 Demo Results Summary")
        print("-" * 40)
        
        # Calculate overall success rate
        completed_demos = sum(1 for result in self.demo_results.values() if result.get('status') == 'completed')
        total_demos = len(self.demo_results)
        success_rate = round((completed_demos / total_demos) * 100) if total_demos > 0 else 0
        
        print(f"Overall Success Rate: {success_rate}% ({completed_demos}/{total_demos})")
        
        # Show individual demo results
        print("\nDemo Results:")
        for demo_name, result in self.demo_results.items():
            status = result.get('status', 'unknown')
            status_icon = "✅" if status == 'completed' else "❌"
            print(f"  {demo_name}: {status_icon} {status}")
        
        # Show key metrics
        print("\nKey Metrics:")
        if 'dependency_discovery' in self.demo_results:
            discovery = self.demo_results['dependency_discovery']
            print(f"  Total Dependencies: {discovery.get('total_dependencies', 0)}")
            print(f"  Installed Dependencies: {discovery.get('installed_dependencies', 0)}")
        
        if 'health_monitoring' in self.demo_results:
            health = self.demo_results['health_monitoring']
            print(f"  Health Score: {health.get('health_score', 0)}%")
        
        if 'comprehensive_reporting' in self.demo_results:
            reporting = self.demo_results['comprehensive_reporting']
            report = reporting.get('report', {})
            print(f"  Missing Dependencies: {report.get('missing_dependencies', 0)}")
            print(f"  Recommendations: {report.get('recommendations', 0)}")
        
        # Save results to file
        try:
            results_file = project_root / "logs" / "dependency-integration-demo-results.json"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(self.demo_results, f, indent=2, default=str)
            
            print(f"\n📄 Results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")
        
        print("\n🎉 Demo completed successfully!")


async def main():
    """Main demo function."""
    demo = DependencyIntegrationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())