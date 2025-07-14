#!/usr/bin/env python3
"""
Test script for the Claude PM deployment system.

Tests the newly implemented deployment validation and enforcement system.
"""

import sys
import asyncio
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.framework_deployment_validator import FrameworkDeploymentValidator
from claude_pm.services.working_directory_deployer import WorkingDirectoryDeployer, DeploymentConfig
from claude_pm.core.deployment_enforcement import get_deployment_enforcer

async def test_deployment_validator():
    """Test the framework deployment validator."""
    print("🔍 Testing Framework Deployment Validator...")
    
    validator = FrameworkDeploymentValidator()
    
    # Test validation
    result = await validator.validate_deployment()
    
    print(f"   NPM Installation: {'✅' if result.npm_installation_found else '❌'}")
    print(f"   Framework Deployed: {'✅' if result.framework_deployed else '❌'}")
    print(f"   Overall Valid: {'✅' if result.is_valid else '❌'}")
    
    if not result.is_valid:
        print("   Error:", result.error_message)
        if result.actionable_guidance:
            print("   Guidance:")
            for guidance in result.actionable_guidance[:3]:
                print(f"     • {guidance}")
    
    return result.is_valid

async def test_working_directory_deployer():
    """Test the working directory deployer."""
    print("\n🚀 Testing Working Directory Deployer...")
    
    deployer = WorkingDirectoryDeployer()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"   Test directory: {temp_path}")
        
        # Test deployment status check (before deployment)
        status_before = await deployer.get_deployment_status(temp_path)
        print(f"   Deployed before: {'✅' if status_before['deployed'] else '❌'}")
        
        # Test deployment (dry run simulation) - use deployer's detected source
        config = DeploymentConfig(
            source_path=deployer.claude_pm_home,
            target_path=temp_path / ".claude-pm",
            verify_after_deployment=False  # Skip verification for this test
        )
        
        # Check if source exists
        source_exists = config.source_path.exists()
        print(f"   Source exists: {'✅' if source_exists else '❌'}")
        
        if source_exists:
            # Test actual deployment
            result = await deployer.deploy_to_working_directory(temp_path, config)
            print(f"   Deployment success: {'✅' if result.success else '❌'}")
            
            if not result.success:
                print(f"   Error: {result.error_message}")
            else:
                print(f"   Files deployed: {len(result.deployed_files)}")
                
                # Test deployment status check (after deployment)
                status_after = await deployer.get_deployment_status(temp_path)
                print(f"   Deployed after: {'✅' if status_after['deployed'] else '❌'}")
        else:
            print("   ⚠️  Skipping deployment test - no NPM installation found")
            return False
    
    return True

async def test_deployment_enforcer():
    """Test the deployment enforcement system."""
    print("\n🛡️  Testing Deployment Enforcer...")
    
    enforcer = get_deployment_enforcer()
    
    # Test deployment status check
    status = await enforcer.check_deployment_status()
    print(f"   Enforcement valid: {'✅' if status['valid'] else '❌'}")
    print(f"   NPM installation: {'✅' if status.get('npm_installation') else '❌'}")
    print(f"   Framework deployed: {'✅' if status.get('framework_deployed') else '❌'}")
    
    return status['valid']

async def test_template_existence():
    """Test that deployment templates exist."""
    print("\n📄 Testing Template Files...")
    
    template_base = Path(__file__).parent.parent / "templates"
    
    required_templates = [
        "CLAUDE.md",
        "config/working-directory-config.json", 
        "project-agents.json",
        "project-template.md",
        "health/working-directory-health.json"
    ]
    
    all_exist = True
    for template in required_templates:
        template_path = template_base / template
        exists = template_path.exists()
        print(f"   {template}: {'✅' if exists else '❌'}")
        if not exists:
            all_exist = False
    
    return all_exist

async def main():
    """Run all deployment system tests."""
    print("🧪 Claude PM Deployment System Test Suite")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Template files
    test_results['templates'] = await test_template_existence()
    
    # Test 2: Deployment validator
    test_results['validator'] = await test_deployment_validator()
    
    # Test 3: Working directory deployer
    test_results['deployer'] = await test_working_directory_deployer()
    
    # Test 4: Deployment enforcer
    test_results['enforcer'] = await test_deployment_enforcer()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.title()}: {status}")
    
    overall_success = all(test_results.values())
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if not overall_success:
        print("\n💡 Next Steps:")
        print("   • Check that NPM installation exists at ~/.claude-pm")
        print("   • Verify template files are correctly placed")
        print("   • Run 'npm install -g @bobmatnyc/claude-multiagent-pm' if needed")
    else:
        print("\n🚀 Deployment system is ready for use!")
        print("   • Run 'claude-pm deploy' to deploy framework to working directory")
        print("   • Run 'claude-pm verify' to validate deployment")
        print("   • Run 'claude-pm diagnose' for comprehensive diagnostics")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))