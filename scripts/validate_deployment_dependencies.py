#!/usr/bin/env python3
"""
Deployment Dependency Validation Script

Validates that all required dependencies are properly installed and functional
for the Claude PM Framework deployment. This script integrates CMPM-103 
Dependency Management with CMPM-101 Deployment Detection.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.dependency_manager import DependencyManager


class DeploymentValidator:
    """Validates deployment dependencies and configuration."""
    
    def __init__(self):
        self.dependency_manager = None
        self.validation_results = {}
        self.exit_code = 0
    
    async def validate_deployment(self) -> int:
        """Validate the deployment and return exit code."""
        print("🔍 Claude PM Framework - Deployment Dependency Validation")
        print("=" * 60)
        print()
        
        try:
            # Initialize dependency manager
            await self._initialize_dependency_manager()
            
            # Validate deployment detection
            deployment_valid = await self._validate_deployment_detection()
            
            # Validate core dependencies
            dependencies_valid = await self._validate_core_dependencies()
            
            # Validate ai-trackdown-tools specifically
            ai_trackdown_valid = await self._validate_ai_trackdown_tools()
            
            # Validate Python environment
            python_valid = await self._validate_python_environment()
            
            # Validate Node.js environment
            node_valid = await self._validate_node_environment()
            
            # Run comprehensive health check
            health_valid = await self._validate_health()
            
            # Generate validation report
            await self._generate_validation_report()
            
            # Calculate overall validation result
            all_validations = [
                deployment_valid,
                dependencies_valid,
                ai_trackdown_valid,
                python_valid,
                node_valid,
                health_valid
            ]
            
            if all(all_validations):
                print("✅ All validations passed! Deployment is ready.")
                self.exit_code = 0
            else:
                print("❌ Some validations failed. Please review the issues above.")
                self.exit_code = 1
                
        except Exception as e:
            print(f"❌ Validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.exit_code = 1
        finally:
            # Cleanup
            if self.dependency_manager:
                await self.dependency_manager._cleanup()
        
        return self.exit_code
    
    async def _initialize_dependency_manager(self):
        """Initialize the dependency manager."""
        print("🚀 Initializing Dependency Manager...")
        
        config = {
            "check_interval": 60,
            "auto_install": False,
            "installation_timeout": 30,
            "enable_dependency_monitoring": False
        }
        
        self.dependency_manager = DependencyManager(config)
        await self.dependency_manager._initialize()
        
        print("✅ Dependency Manager initialized")
        print()
    
    async def _validate_deployment_detection(self) -> bool:
        """Validate deployment detection integration."""
        print("🔍 Validating Deployment Detection...")
        
        try:
            deployment_config = self.dependency_manager.deployment_config
            
            if not deployment_config:
                print("❌ No deployment configuration detected")
                self.validation_results['deployment_detection'] = {
                    'status': 'failed',
                    'message': 'No deployment configuration'
                }
                return False
            
            config = deployment_config.get('config', {})
            deployment_type = config.get('deploymentType', 'unknown')
            platform = config.get('platform', 'unknown')
            confidence = config.get('confidence', 'unknown')
            
            print(f"✅ Deployment Type: {deployment_type}")
            print(f"✅ Platform: {platform}")
            print(f"✅ Confidence: {confidence}")
            
            if 'frameworkPath' in config:
                framework_path = config['frameworkPath']
                print(f"✅ Framework Path: {framework_path}")
                
                # Verify framework path exists
                if not Path(framework_path).exists():
                    print(f"❌ Framework path does not exist: {framework_path}")
                    self.validation_results['deployment_detection'] = {
                        'status': 'failed',
                        'message': f'Framework path not found: {framework_path}'
                    }
                    return False
            
            self.validation_results['deployment_detection'] = {
                'status': 'passed',
                'deployment_type': deployment_type,
                'platform': platform,
                'confidence': confidence
            }
            
            print("✅ Deployment detection validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Deployment detection validation failed: {e}")
            self.validation_results['deployment_detection'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _validate_core_dependencies(self) -> bool:
        """Validate core dependencies."""
        print("🔍 Validating Core Dependencies...")
        
        try:
            dependencies = self.dependency_manager.get_dependencies()
            
            total_deps = len(dependencies)
            installed_deps = sum(1 for info in dependencies.values() if info.is_installed)
            missing_deps = total_deps - installed_deps
            
            print(f"📊 Total Dependencies: {total_deps}")
            print(f"📊 Installed: {installed_deps}")
            print(f"📊 Missing: {missing_deps}")
            
            # Check critical dependencies
            critical_missing = []
            for name, info in dependencies.items():
                dep_config = self.dependency_manager.CORE_DEPENDENCIES.get(name, {})
                if dep_config.get('critical', False) and not info.is_installed:
                    critical_missing.append(name)
            
            if critical_missing:
                print(f"❌ Critical dependencies missing: {', '.join(critical_missing)}")
                self.validation_results['core_dependencies'] = {
                    'status': 'failed',
                    'total': total_deps,
                    'installed': installed_deps,
                    'missing': missing_deps,
                    'critical_missing': critical_missing
                }
                return False
            
            # Show dependency status
            for name, info in dependencies.items():
                status = "✅" if info.is_installed else "❌"
                version = f" ({info.version})" if info.version else ""
                print(f"  {status} {name}{version}")
            
            self.validation_results['core_dependencies'] = {
                'status': 'passed',
                'total': total_deps,
                'installed': installed_deps,
                'missing': missing_deps,
                'critical_missing': []
            }
            
            print("✅ Core dependencies validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Core dependencies validation failed: {e}")
            self.validation_results['core_dependencies'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _validate_ai_trackdown_tools(self) -> bool:
        """Validate ai-trackdown-tools specifically."""
        print("🔍 Validating AI-Trackdown-Tools...")
        
        try:
            # Get dependency info
            ai_trackdown_info = self.dependency_manager.get_dependency("ai-trackdown-tools")
            
            if not ai_trackdown_info:
                print("❌ ai-trackdown-tools dependency not found")
                self.validation_results['ai_trackdown_tools'] = {
                    'status': 'failed',
                    'message': 'dependency not found'
                }
                return False
            
            # Check installation
            if not ai_trackdown_info.is_installed:
                print("❌ ai-trackdown-tools is not installed")
                self.validation_results['ai_trackdown_tools'] = {
                    'status': 'failed',
                    'message': 'not installed'
                }
                return False
            
            print(f"✅ ai-trackdown-tools is installed")
            print(f"✅ Version: {ai_trackdown_info.version or 'unknown'}")
            print(f"✅ Method: {ai_trackdown_info.installation_method.value if ai_trackdown_info.installation_method else 'unknown'}")
            
            # Verify functionality
            is_functional = await self.dependency_manager.verify_ai_trackdown_tools()
            
            if not is_functional:
                print("❌ ai-trackdown-tools is not functional")
                self.validation_results['ai_trackdown_tools'] = {
                    'status': 'failed',
                    'message': 'not functional',
                    'installed': True,
                    'version': ai_trackdown_info.version
                }
                return False
            
            print("✅ ai-trackdown-tools is functional")
            
            self.validation_results['ai_trackdown_tools'] = {
                'status': 'passed',
                'installed': True,
                'functional': True,
                'version': ai_trackdown_info.version,
                'method': ai_trackdown_info.installation_method.value if ai_trackdown_info.installation_method else None
            }
            
            print("✅ ai-trackdown-tools validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ ai-trackdown-tools validation failed: {e}")
            self.validation_results['ai_trackdown_tools'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _validate_python_environment(self) -> bool:
        """Validate Python environment."""
        print("🔍 Validating Python Environment...")
        
        try:
            # Check Python availability
            python_available = await self.dependency_manager._check_python_available()
            
            if not python_available:
                print("❌ Python is not available")
                self.validation_results['python_environment'] = {
                    'status': 'failed',
                    'message': 'Python not available'
                }
                return False
            
            print(f"✅ Python command: {self.dependency_manager.python_cmd}")
            
            # Get Python dependency info
            python_info = self.dependency_manager.get_dependency("python")
            if python_info:
                print(f"✅ Python version: {python_info.version or 'unknown'}")
                print(f"✅ Python path: {python_info.installation_path or 'unknown'}")
            
            # Check Python packages from requirements
            deployment_config = self.dependency_manager.deployment_config
            if deployment_config and "config" in deployment_config:
                framework_path = deployment_config["config"].get("frameworkPath")
                if framework_path:
                    requirements_path = Path(framework_path) / "requirements" / "base.txt"
                    if requirements_path.exists():
                        print(f"✅ Found requirements file: {requirements_path}")
                    else:
                        print(f"⚠️  Requirements file not found: {requirements_path}")
            
            self.validation_results['python_environment'] = {
                'status': 'passed',
                'python_cmd': self.dependency_manager.python_cmd,
                'version': python_info.version if python_info else None,
                'path': python_info.installation_path if python_info else None
            }
            
            print("✅ Python environment validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Python environment validation failed: {e}")
            self.validation_results['python_environment'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _validate_node_environment(self) -> bool:
        """Validate Node.js environment."""
        print("🔍 Validating Node.js Environment...")
        
        try:
            # Check Node.js availability
            node_available = await self.dependency_manager._check_node_available()
            npm_available = await self.dependency_manager._check_npm_available()
            
            if not node_available:
                print("❌ Node.js is not available")
                self.validation_results['node_environment'] = {
                    'status': 'failed',
                    'message': 'Node.js not available'
                }
                return False
            
            if not npm_available:
                print("❌ npm is not available")
                self.validation_results['node_environment'] = {
                    'status': 'failed',
                    'message': 'npm not available'
                }
                return False
            
            # Get Node.js dependency info
            node_info = self.dependency_manager.get_dependency("node")
            npm_info = self.dependency_manager.get_dependency("npm")
            
            if node_info:
                print(f"✅ Node.js version: {node_info.version or 'unknown'}")
                print(f"✅ Node.js path: {node_info.installation_path or 'unknown'}")
            
            if npm_info:
                print(f"✅ npm version: {npm_info.version or 'unknown'}")
                print(f"✅ npm path: {npm_info.installation_path or 'unknown'}")
            
            self.validation_results['node_environment'] = {
                'status': 'passed',
                'node_version': node_info.version if node_info else None,
                'node_path': node_info.installation_path if node_info else None,
                'npm_version': npm_info.version if npm_info else None,
                'npm_path': npm_info.installation_path if npm_info else None
            }
            
            print("✅ Node.js environment validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Node.js environment validation failed: {e}")
            self.validation_results['node_environment'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _validate_health(self) -> bool:
        """Validate overall health."""
        print("🔍 Validating Overall Health...")
        
        try:
            # Perform health check
            health_checks = await self.dependency_manager._health_check()
            
            # Calculate health score
            total_checks = len(health_checks)
            passed_checks = sum(1 for status in health_checks.values() if status)
            health_score = round((passed_checks / total_checks) * 100) if total_checks > 0 else 0
            
            print(f"📊 Health Score: {health_score}%")
            print(f"📊 Passed Checks: {passed_checks}/{total_checks}")
            
            # Show individual check results
            for check_name, status in health_checks.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check_name}")
            
            # Consider health acceptable if >= 80%
            health_acceptable = health_score >= 80
            
            if not health_acceptable:
                print(f"❌ Health score too low: {health_score}% (minimum 80%)")
                self.validation_results['health'] = {
                    'status': 'failed',
                    'health_score': health_score,
                    'passed_checks': passed_checks,
                    'total_checks': total_checks,
                    'health_checks': health_checks
                }
                return False
            
            self.validation_results['health'] = {
                'status': 'passed',
                'health_score': health_score,
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'health_checks': health_checks
            }
            
            print("✅ Health validation passed")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Health validation failed: {e}")
            self.validation_results['health'] = {
                'status': 'failed',
                'message': str(e)
            }
            return False
    
    async def _generate_validation_report(self):
        """Generate comprehensive validation report."""
        print("📊 Generating Validation Report...")
        
        try:
            # Generate dependency report
            dependency_report = await self.dependency_manager.generate_dependency_report()
            
            # Create comprehensive validation report
            validation_report = {
                'timestamp': dependency_report.timestamp,
                'deployment_type': dependency_report.deployment_type,
                'platform': dependency_report.platform,
                'validation_results': self.validation_results,
                'dependency_report': {
                    'health_score': dependency_report.health_score,
                    'total_dependencies': len(dependency_report.dependencies),
                    'missing_dependencies': dependency_report.missing_dependencies,
                    'outdated_dependencies': dependency_report.outdated_dependencies,
                    'installation_recommendations': dependency_report.installation_recommendations
                }
            }
            
            # Save report to file
            report_file = project_root / "logs" / "deployment-validation-report.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            
            print(f"✅ Validation report saved to: {report_file}")
            print()
            
        except Exception as e:
            print(f"⚠️  Failed to generate validation report: {e}")


async def main():
    """Main validation function."""
    validator = DeploymentValidator()
    exit_code = await validator.validate_deployment()
    
    print(f"\n🏁 Validation completed with exit code: {exit_code}")
    
    if exit_code == 0:
        print("🎉 Deployment is valid and ready for use!")
    else:
        print("💥 Deployment validation failed. Please address the issues above.")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)