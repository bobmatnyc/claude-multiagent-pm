#!/usr/bin/env python3
"""
Claude-MultiAgent-PM Ops Agent - Integration Validation
Validate complete agent integration with the framework.

Author: Claude-MultiAgent-PM Ops Agent
Version: 1.0.0
Date: 2025-07-11
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

def validate_agent_integration():
    """Validate complete Ops Agent integration."""
    print("🔍 Claude-MultiAgent-PM Ops Agent - Integration Validation")
    print("=" * 60)
    
    project_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    ops_agent_root = project_root / ".claude-pm" / "agents" / "project-specific" / "ops-agent"
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "unknown"
    }
    
    # Test 1: Agent structure validation
    print("📁 Test 1: Agent Directory Structure")
    required_files = [
        ops_agent_root / "ops-agent.py",
        ops_agent_root / "config" / "agent-definition.yaml",
        ops_agent_root / "automation" / "full-deployment.py",
        ops_agent_root / "automation" / "incremental-sync.py",
        ops_agent_root / "diagnostics" / "comprehensive-diagnostics.py",
        ops_agent_root / "knowledge" / "framework-architecture.md",
        ops_agent_root / "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if not missing_files:
        print("   ✅ All required files present")
        validation_results["tests"]["structure"] = "PASS"
    else:
        print(f"   ❌ Missing files: {missing_files}")
        validation_results["tests"]["structure"] = f"FAIL: {missing_files}"
    
    # Test 2: Agent registry integration
    print("\n🤖 Test 2: Agent Registry Integration")
    registry_file = project_root / ".claude-pm" / "agents" / "registry.json"
    
    if registry_file.exists():
        try:
            with open(registry_file, 'r') as f:
                registry_data = json.load(f)
            
            if "claude-multiagent-pm-ops-agent" in registry_data.get("agents_by_tier", {}).get("project", {}):
                print("   ✅ Agent registered in project tier")
                validation_results["tests"]["registry"] = "PASS"
            else:
                print("   ❌ Agent not found in registry")
                validation_results["tests"]["registry"] = "FAIL: Not registered"
        except Exception as e:
            print(f"   ❌ Registry read error: {e}")
            validation_results["tests"]["registry"] = f"FAIL: {e}"
    else:
        print("   ❌ Registry file missing")
        validation_results["tests"]["registry"] = "FAIL: Registry missing"
    
    # Test 3: Agent executable validation
    print("\n⚙️ Test 3: Agent Executable Validation")
    try:
        os.chdir(ops_agent_root)
        result = subprocess.run([sys.executable, "ops-agent.py", "info"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "claude-multiagent-pm-ops-agent" in result.stdout:
            print("   ✅ Agent executable and responsive")
            validation_results["tests"]["executable"] = "PASS"
        else:
            print(f"   ❌ Agent execution failed: {result.stderr}")
            validation_results["tests"]["executable"] = f"FAIL: {result.stderr}"
    except Exception as e:
        print(f"   ❌ Agent execution error: {e}")
        validation_results["tests"]["executable"] = f"FAIL: {e}"
    
    # Test 4: Framework knowledge validation
    print("\n📚 Test 4: Framework Knowledge Base")
    knowledge_file = ops_agent_root / "knowledge" / "framework-architecture.md"
    
    if knowledge_file.exists():
        with open(knowledge_file, 'r') as f:
            content = f.read()
        
        required_knowledge = [
            "Framework Version**: 4.5.1",
            "mem0AI v0.1.113",
            "three-tier hierarchy",
            "claude-multiagent-pm"
        ]
        
        missing_knowledge = []
        for knowledge in required_knowledge:
            if knowledge not in content:
                missing_knowledge.append(knowledge)
        
        if not missing_knowledge:
            print("   ✅ Framework knowledge complete")
            validation_results["tests"]["knowledge"] = "PASS"
        else:
            print(f"   ❌ Missing knowledge: {missing_knowledge}")
            validation_results["tests"]["knowledge"] = f"FAIL: {missing_knowledge}"
    else:
        print("   ❌ Knowledge base missing")
        validation_results["tests"]["knowledge"] = "FAIL: Knowledge missing"
    
    # Test 5: Automation capabilities validation
    print("\n🚀 Test 5: Automation Capabilities")
    automation_scripts = [
        ops_agent_root / "automation" / "full-deployment.py",
        ops_agent_root / "automation" / "incremental-sync.py"
    ]
    
    executable_scripts = []
    for script in automation_scripts:
        if script.exists() and os.access(script, os.X_OK):
            executable_scripts.append(script.name)
    
    if len(executable_scripts) == len(automation_scripts):
        print(f"   ✅ All automation scripts executable: {executable_scripts}")
        validation_results["tests"]["automation"] = "PASS"
    else:
        print(f"   ❌ Some scripts not executable. Found: {executable_scripts}")
        validation_results["tests"]["automation"] = f"FAIL: Partial executable"
    
    # Test 6: Diagnostic capabilities validation
    print("\n🔍 Test 6: Diagnostic Capabilities")
    try:
        result = subprocess.run([sys.executable, "ops-agent.py", "status"], 
                              capture_output=True, text=True, timeout=15,
                              cwd=ops_agent_root)
        
        if result.returncode == 0 and "System Status" in result.stdout:
            print("   ✅ Diagnostic capabilities functional")
            validation_results["tests"]["diagnostics"] = "PASS"
        else:
            print(f"   ❌ Diagnostic test failed: {result.stderr}")
            validation_results["tests"]["diagnostics"] = f"FAIL: {result.stderr}"
    except Exception as e:
        print(f"   ❌ Diagnostic test error: {e}")
        validation_results["tests"]["diagnostics"] = f"FAIL: {e}"
    
    # Calculate overall status
    print("\n" + "=" * 60)
    passed_tests = len([t for t in validation_results["tests"].values() if t == "PASS"])
    total_tests = len(validation_results["tests"])
    
    if passed_tests == total_tests:
        validation_results["overall_status"] = "FULLY_INTEGRATED"
        print("🎉 INTEGRATION VALIDATION: FULLY INTEGRATED")
        print(f"   All {total_tests} tests passed successfully")
        print("   The Claude-MultiAgent-PM Ops Agent is fully operational")
    elif passed_tests >= total_tests * 0.8:
        validation_results["overall_status"] = "MOSTLY_INTEGRATED"
        print("⚠️ INTEGRATION VALIDATION: MOSTLY INTEGRATED")
        print(f"   {passed_tests}/{total_tests} tests passed")
        print("   Minor issues may need attention")
    else:
        validation_results["overall_status"] = "INTEGRATION_ISSUES"
        print("❌ INTEGRATION VALIDATION: INTEGRATION ISSUES")
        print(f"   Only {passed_tests}/{total_tests} tests passed")
        print("   Significant issues need resolution")
    
    # Save validation report
    report_path = project_root / "logs" / "ops-agent-integration-validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n📊 Validation report saved: {report_path}")
    print("=" * 60)
    
    return validation_results["overall_status"] == "FULLY_INTEGRATED"

if __name__ == "__main__":
    success = validate_agent_integration()
    sys.exit(0 if success else 1)