#!/usr/bin/env python3
"""
Deployment Validation Script
============================

Comprehensive validation script that verifies deployment integrity,
symlink health, PATH resolution, and script execution consistency.

This script helps identify and diagnose deployment issues before they
affect users, ensuring reliable script execution across different environments.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Validates deployment integrity and consistency."""
    
    def __init__(self):
        self.framework_root = Path(__file__).parent.parent
        self.bin_dir = self.framework_root / "bin"
        self.target_dir = Path.home() / ".local" / "bin"
        
        # Scripts to validate
        self.scripts_to_validate = [
            "claude-pm",
            "cmpm"
        ]
        
        self.validation_results = {}
        
    def validate_source_files(self) -> Dict[str, bool]:
        """Validate that source files exist and are accessible."""
        logger.info("Validating source files...")
        
        source_results = {}
        
        for script_name in self.scripts_to_validate:
            source_path = self.bin_dir / script_name
            
            if source_path.exists():
                if source_path.is_file():
                    if os.access(source_path, os.R_OK):
                        source_results[script_name] = True
                        logger.info(f"✅ Source file {script_name} is valid")
                    else:
                        source_results[script_name] = False
                        logger.error(f"❌ Source file {script_name} is not readable")
                else:
                    source_results[script_name] = False
                    logger.error(f"❌ Source {script_name} exists but is not a file")
            else:
                source_results[script_name] = False
                logger.error(f"❌ Source file {script_name} does not exist")
        
        return source_results
    
    def validate_target_deployment(self) -> Dict[str, Dict]:
        """Validate target deployment files and symlinks."""
        logger.info("Validating target deployment...")
        
        target_results = {}
        
        for script_name in self.scripts_to_validate:
            target_path = self.target_dir / script_name
            source_path = self.bin_dir / script_name
            
            result = {
                "exists": False,
                "is_symlink": False,
                "points_to_source": False,
                "is_executable": False,
                "valid": False
            }
            
            if target_path.exists():
                result["exists"] = True
                
                if target_path.is_symlink():
                    result["is_symlink"] = True
                    
                    # Check if symlink points to source
                    try:
                        resolved_target = target_path.resolve()
                        expected_source = source_path.resolve()
                        
                        if resolved_target == expected_source:
                            result["points_to_source"] = True
                        else:
                            logger.warning(f"⚠️  {script_name} symlink points to {resolved_target}, expected {expected_source}")
                    except Exception as e:
                        logger.error(f"❌ Could not resolve symlink for {script_name}: {e}")
                
                # Check if executable
                if os.access(target_path, os.X_OK):
                    result["is_executable"] = True
                
                # Overall validation
                if result["exists"] and result["is_symlink"] and result["points_to_source"] and result["is_executable"]:
                    result["valid"] = True
                    logger.info(f"✅ Target deployment {script_name} is valid")
                else:
                    logger.error(f"❌ Target deployment {script_name} has issues")
            else:
                logger.error(f"❌ Target file {script_name} does not exist")
            
            target_results[script_name] = result
        
        return target_results
    
    def validate_path_resolution(self) -> Dict[str, Dict]:
        """Validate that PATH resolution points to the correct scripts."""
        logger.info("Validating PATH resolution...")
        
        path_results = {}
        
        for script_name in self.scripts_to_validate:
            result = {
                "found_in_path": False,
                "path_location": None,
                "points_to_target": False,
                "valid": False
            }
            
            try:
                # Use 'which' to find script in PATH
                which_result = subprocess.run(
                    ['which', script_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if which_result.returncode == 0:
                    result["found_in_path"] = True
                    path_location = Path(which_result.stdout.strip())
                    result["path_location"] = str(path_location)
                    
                    # Check if PATH location matches our target
                    target_path = self.target_dir / script_name
                    
                    if path_location.resolve() == target_path.resolve():
                        result["points_to_target"] = True
                        result["valid"] = True
                        logger.info(f"✅ PATH resolution for {script_name} is valid")
                    else:
                        logger.error(f"❌ PATH resolution for {script_name} points to {path_location}, expected {target_path}")
                else:
                    logger.error(f"❌ {script_name} not found in PATH")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"❌ PATH resolution timeout for {script_name}")
            except Exception as e:
                logger.error(f"❌ PATH resolution error for {script_name}: {e}")
            
            path_results[script_name] = result
        
        return path_results
    
    def validate_script_execution(self) -> Dict[str, Dict]:
        """Validate that scripts can be executed successfully."""
        logger.info("Validating script execution...")
        
        execution_results = {}
        
        for script_name in self.scripts_to_validate:
            result = {
                "can_execute": False,
                "version_check": False,
                "help_check": False,
                "execution_time": None,
                "valid": False
            }
            
            target_path = self.target_dir / script_name
            
            if not target_path.exists():
                execution_results[script_name] = result
                continue
            
            # Test basic execution
            try:
                start_time = datetime.now()
                
                # Try version check first
                version_result = subprocess.run(
                    [str(target_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                end_time = datetime.now()
                result["execution_time"] = (end_time - start_time).total_seconds()
                
                if version_result.returncode == 0:
                    result["can_execute"] = True
                    result["version_check"] = True
                    logger.info(f"✅ {script_name} execution successful (version check)")
                else:
                    # Try help command as fallback
                    help_result = subprocess.run(
                        [str(target_path), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if help_result.returncode == 0:
                        result["can_execute"] = True
                        result["help_check"] = True
                        logger.info(f"✅ {script_name} execution successful (help check)")
                    else:
                        logger.error(f"❌ {script_name} execution failed")
                
                # Overall validation
                if result["can_execute"] and (result["version_check"] or result["help_check"]):
                    result["valid"] = True
                    
            except subprocess.TimeoutExpired:
                logger.error(f"❌ {script_name} execution timeout")
            except Exception as e:
                logger.error(f"❌ {script_name} execution error: {e}")
            
            execution_results[script_name] = result
        
        return execution_results
    
    def validate_deployment_consistency(self) -> Dict[str, any]:
        """Validate consistency across all deployment aspects."""
        logger.info("Validating deployment consistency...")
        
        consistency_results = {
            "timestamp": datetime.now().isoformat(),
            "framework_path": str(self.framework_root),
            "target_directory": str(self.target_dir),
            "scripts_validated": len(self.scripts_to_validate),
            "overall_status": "unknown",
            "issues": []
        }
        
        # Run all validation checks
        source_results = self.validate_source_files()
        target_results = self.validate_target_deployment()
        path_results = self.validate_path_resolution()
        execution_results = self.validate_script_execution()
        
        # Aggregate results
        all_scripts_valid = True
        
        for script_name in self.scripts_to_validate:
            script_valid = (
                source_results.get(script_name, False) and
                target_results.get(script_name, {}).get("valid", False) and
                path_results.get(script_name, {}).get("valid", False) and
                execution_results.get(script_name, {}).get("valid", False)
            )
            
            if not script_valid:
                all_scripts_valid = False
                consistency_results["issues"].append(f"{script_name} validation failed")
        
        # Check for specific issues
        if not all(source_results.values()):
            consistency_results["issues"].append("Source file validation failed")
        
        if not all(target_results[script]["valid"] for script in self.scripts_to_validate if script in target_results):
            consistency_results["issues"].append("Target deployment validation failed")
        
        if not all(path_results[script]["valid"] for script in self.scripts_to_validate if script in path_results):
            consistency_results["issues"].append("PATH resolution validation failed")
        
        if not all(execution_results[script]["valid"] for script in self.scripts_to_validate if script in execution_results):
            consistency_results["issues"].append("Script execution validation failed")
        
        # Set overall status
        if all_scripts_valid:
            consistency_results["overall_status"] = "valid"
        else:
            consistency_results["overall_status"] = "invalid"
        
        # Store detailed results
        consistency_results["detailed_results"] = {
            "source_files": source_results,
            "target_deployment": target_results,
            "path_resolution": path_results,
            "script_execution": execution_results
        }
        
        return consistency_results
    
    def print_validation_report(self, results: Dict[str, any]):
        """Print a comprehensive validation report."""
        print("\n" + "="*80)
        print("🔍 CLAUDE PM FRAMEWORK - DEPLOYMENT VALIDATION REPORT")
        print("="*80)
        print(f"📅 Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏠 Framework Path: {results['framework_path']}")
        print(f"🎯 Target Directory: {results['target_directory']}")
        print(f"📊 Scripts Validated: {results['scripts_validated']}")
        print()
        
        # Overall status
        status_emoji = "✅" if results["overall_status"] == "valid" else "❌"
        print(f"{status_emoji} OVERALL STATUS: {results['overall_status'].upper()}")
        
        if results["issues"]:
            print("\n⚠️  ISSUES FOUND:")
            for issue in results["issues"]:
                print(f"   • {issue}")
        
        print()
        
        # Detailed results
        detailed = results["detailed_results"]
        
        # Source files
        print("📁 SOURCE FILES:")
        print("-" * 40)
        for script, valid in detailed["source_files"].items():
            emoji = "✅" if valid else "❌"
            print(f"{emoji} {script}: {'Valid' if valid else 'Invalid'}")
        
        print()
        
        # Target deployment
        print("🔗 TARGET DEPLOYMENT:")
        print("-" * 40)
        for script, result in detailed["target_deployment"].items():
            emoji = "✅" if result["valid"] else "❌"
            print(f"{emoji} {script}:")
            print(f"   Exists: {'Yes' if result['exists'] else 'No'}")
            print(f"   Symlink: {'Yes' if result['is_symlink'] else 'No'}")
            print(f"   Points to Source: {'Yes' if result['points_to_source'] else 'No'}")
            print(f"   Executable: {'Yes' if result['is_executable'] else 'No'}")
        
        print()
        
        # PATH resolution
        print("🛤️  PATH RESOLUTION:")
        print("-" * 40)
        for script, result in detailed["path_resolution"].items():
            emoji = "✅" if result["valid"] else "❌"
            print(f"{emoji} {script}:")
            print(f"   Found in PATH: {'Yes' if result['found_in_path'] else 'No'}")
            if result["path_location"]:
                print(f"   PATH Location: {result['path_location']}")
            print(f"   Points to Target: {'Yes' if result['points_to_target'] else 'No'}")
        
        print()
        
        # Script execution
        print("⚡ SCRIPT EXECUTION:")
        print("-" * 40)
        for script, result in detailed["script_execution"].items():
            emoji = "✅" if result["valid"] else "❌"
            print(f"{emoji} {script}:")
            print(f"   Can Execute: {'Yes' if result['can_execute'] else 'No'}")
            print(f"   Version Check: {'Yes' if result['version_check'] else 'No'}")
            print(f"   Help Check: {'Yes' if result['help_check'] else 'No'}")
            if result["execution_time"]:
                print(f"   Execution Time: {result['execution_time']:.2f}s")
        
        print()
        
        # Recommendations
        if results["overall_status"] != "valid":
            print("🔧 RECOMMENDATIONS:")
            print("-" * 40)
            print("1. Run unified deployment to fix issues:")
            print("   python scripts/deploy_scripts.py --unified --deploy")
            print("2. Check symlink integrity:")
            print("   python scripts/unified_deployment_strategy.py --verify")
            print("3. Validate PATH configuration:")
            print("   echo $PATH | grep -o '[^:]*' | head -10")
            print("4. Test script execution manually:")
            print("   which claude-pm && claude-pm --version")
        else:
            print("🎉 DEPLOYMENT IS HEALTHY!")
            print("All scripts are properly deployed and validated.")
        
        print()
        print("="*80)
    
    def run_validation(self) -> Dict[str, any]:
        """Run complete validation suite."""
        logger.info("Starting deployment validation...")
        
        results = self.validate_deployment_consistency()
        
        logger.info(f"Validation completed. Status: {results['overall_status']}")
        
        return results


def main():
    """Main entry point for deployment validation."""
    parser = argparse.ArgumentParser(
        description="Claude PM Framework Deployment Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate and display validation report"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix validation issues automatically"
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    validator = DeploymentValidator()
    
    try:
        results = validator.run_validation()
        
        if args.json:
            print(json.dumps(results, indent=2))
        elif args.report or not args.quiet:
            validator.print_validation_report(results)
        
        if args.fix and results["overall_status"] != "valid":
            print("\n🔧 Attempting to fix deployment issues...")
            try:
                # Try to run unified deployment
                fix_command = [
                    sys.executable,
                    str(validator.framework_root / "scripts" / "deploy_scripts.py"),
                    "--unified",
                    "--deploy"
                ]
                
                fix_result = subprocess.run(
                    fix_command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if fix_result.returncode == 0:
                    print("✅ Deployment fix completed successfully")
                    
                    # Re-validate
                    print("🔍 Re-validating deployment...")
                    new_results = validator.run_validation()
                    
                    if new_results["overall_status"] == "valid":
                        print("✅ Deployment is now valid!")
                    else:
                        print("⚠️  Some issues remain after fix attempt")
                        sys.exit(1)
                else:
                    print(f"❌ Fix attempt failed: {fix_result.stderr}")
                    sys.exit(1)
                    
            except Exception as e:
                print(f"❌ Error during fix attempt: {e}")
                sys.exit(1)
        
        # Exit with error code if validation failed
        if results["overall_status"] != "valid":
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()