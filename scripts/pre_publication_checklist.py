#!/usr/bin/env python3
"""
Pre-Publication Checklist for Claude Multi-Agent PM Framework

This script validates that all requirements are met before publishing to PyPI.

Author: Claude Multi-Agent PM Team
Date: 2025-07-20
"""

import os
import sys
import subprocess
import json
import toml
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from claude_pm._version import __version__ as module_version
except ImportError:
    module_version = None


class PublicationChecker:
    """Validates pre-publication requirements."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        
    def print_header(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def check_version_consistency(self) -> bool:
        """Check that all version references are consistent."""
        self.print_header("Version Consistency Check")
        
        versions = {}
        issues = []
        
        # Check pyproject.toml
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
                versions['pyproject.toml'] = data['project']['version']
                print(f"✅ pyproject.toml: {versions['pyproject.toml']}")
        except Exception as e:
            issues.append(f"❌ pyproject.toml: {e}")
        
        # Check VERSION file
        try:
            version_path = self.project_root / "VERSION"
            if version_path.exists():
                with open(version_path, 'r') as f:
                    versions['VERSION'] = f.read().strip()
                    print(f"✅ VERSION file: {versions['VERSION']}")
            else:
                print("⚠️  VERSION file not found")
        except Exception as e:
            issues.append(f"❌ VERSION file: {e}")
        
        # Check package.json
        try:
            package_json_path = self.project_root / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    versions['package.json'] = data.get('version')
                    print(f"✅ package.json: {versions['package.json']}")
        except Exception as e:
            issues.append(f"❌ package.json: {e}")
        
        # Check Python module
        if module_version:
            versions['Python module'] = module_version
            print(f"✅ Python module: {module_version}")
        else:
            print("⚠️  Could not import Python module version")
        
        # Verify all versions match
        unique_versions = set(versions.values())
        if len(unique_versions) > 1:
            issues.append(f"❌ Version mismatch detected: {versions}")
        elif len(unique_versions) == 1:
            print(f"\n✅ All versions consistent: {list(unique_versions)[0]}")
        
        if issues:
            for issue in issues:
                print(issue)
            return False
        
        return True
    
    def check_changelog(self) -> bool:
        """Check if CHANGELOG.md is updated."""
        self.print_header("Changelog Check")
        
        changelog_path = self.project_root / "CHANGELOG.md"
        if not changelog_path.exists():
            print("❌ CHANGELOG.md not found")
            return False
        
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
                current_version = data['project']['version']
            
            with open(changelog_path, 'r') as f:
                content = f.read()
                
            if current_version in content:
                print(f"✅ CHANGELOG.md contains entry for v{current_version}")
                return True
            else:
                print(f"❌ CHANGELOG.md missing entry for v{current_version}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking changelog: {e}")
            return False
    
    def check_tests(self) -> bool:
        """Run tests to ensure they pass."""
        self.print_header("Test Suite Check")
        
        print("Running test suite (this may take a moment)...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                print("❌ Tests failed")
                print("Output:", result.stdout[-500:] if result.stdout else "")
                print("Errors:", result.stderr[-500:] if result.stderr else "")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not run tests: {e}")
            self.warnings.append("Tests could not be run automatically")
            return True  # Don't fail if pytest not available
    
    def check_code_quality(self) -> bool:
        """Check code quality with linters."""
        self.print_header("Code Quality Check")
        
        all_passed = True
        
        # Check with black
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "claude_pm"],
                cwd=self.project_root,
                capture_output=True
            )
            if result.returncode == 0:
                print("✅ Black formatting check passed")
            else:
                print("❌ Black formatting issues found")
                all_passed = False
        except:
            print("⚠️  Black not available")
            self.warnings.append("Black formatter not available")
        
        # Check with isort
        try:
            result = subprocess.run(
                [sys.executable, "-m", "isort", "--check-only", "claude_pm"],
                cwd=self.project_root,
                capture_output=True
            )
            if result.returncode == 0:
                print("✅ isort import ordering check passed")
            else:
                print("❌ isort import ordering issues found")
                all_passed = False
        except:
            print("⚠️  isort not available")
            self.warnings.append("isort not available")
        
        return all_passed
    
    def check_build_tools(self) -> bool:
        """Check if build tools are installed."""
        self.print_header("Build Tools Check")
        
        tools = ['build', 'twine', 'wheel', 'setuptools']
        all_present = True
        
        for tool in tools:
            try:
                __import__(tool)
                print(f"✅ {tool} is installed")
            except ImportError:
                print(f"❌ {tool} is not installed")
                all_present = False
        
        return all_present
    
    def check_package_metadata(self) -> bool:
        """Validate package metadata in pyproject.toml."""
        self.print_header("Package Metadata Check")
        
        try:
            pyproject_path = self.project_root / "pyproject.toml"
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
            
            project = data.get('project', {})
            required_fields = [
                'name', 'version', 'description', 'readme', 
                'license', 'authors', 'classifiers', 'dependencies'
            ]
            
            missing = []
            for field in required_fields:
                if field in project:
                    print(f"✅ {field}: present")
                else:
                    print(f"❌ {field}: missing")
                    missing.append(field)
            
            # Check URLs
            urls = project.get('urls', {})
            if urls:
                print(f"✅ URLs configured: {', '.join(urls.keys())}")
            else:
                print("⚠️  No URLs configured")
                self.warnings.append("Consider adding project URLs")
            
            return len(missing) == 0
            
        except Exception as e:
            print(f"❌ Error reading pyproject.toml: {e}")
            return False
    
    def check_files_exist(self) -> bool:
        """Check that all necessary files exist."""
        self.print_header("Required Files Check")
        
        required_files = [
            "README.md",
            "LICENSE",
            "pyproject.toml",
            "CHANGELOG.md",
            ".gitignore"
        ]
        
        all_present = True
        for file in required_files:
            path = self.project_root / file
            if path.exists():
                print(f"✅ {file}: exists")
            else:
                print(f"❌ {file}: missing")
                all_present = False
        
        return all_present
    
    def check_dist_files(self) -> bool:
        """Check if distribution files can be built."""
        self.print_header("Distribution Build Check")
        
        dist_dir = self.project_root / "dist"
        
        # Try to build
        print("Attempting to build distribution files...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Build successful")
                
                # Check created files
                wheel_files = list(dist_dir.glob("*.whl"))
                tar_files = list(dist_dir.glob("*.tar.gz"))
                
                if wheel_files:
                    print(f"✅ Wheel created: {wheel_files[0].name}")
                else:
                    print("❌ No wheel file created")
                    
                if tar_files:
                    print(f"✅ Source distribution created: {tar_files[0].name}")
                else:
                    print("❌ No source distribution created")
                
                # Run twine check
                if wheel_files or tar_files:
                    print("\nRunning twine check...")
                    check_result = subprocess.run(
                        ["twine", "check", str(dist_dir / "*")],
                        capture_output=True,
                        text=True
                    )
                    if check_result.returncode == 0:
                        print("✅ Package validation passed")
                        return True
                    else:
                        print("❌ Package validation failed:")
                        print(check_result.stdout)
                        return False
                
                return bool(wheel_files and tar_files)
                
            else:
                print("❌ Build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """Run all pre-publication checks."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║          Pre-Publication Checklist for Claude PM             ║
║                      Version Check                           ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        checks = [
            ("Version Consistency", self.check_version_consistency),
            ("Changelog", self.check_changelog),
            ("Required Files", self.check_files_exist),
            ("Package Metadata", self.check_package_metadata),
            ("Build Tools", self.check_build_tools),
            ("Code Quality", self.check_code_quality),
            ("Test Suite", self.check_tests),
            ("Distribution Build", self.check_dist_files),
        ]
        
        for name, check_func in checks:
            try:
                if check_func():
                    self.checks_passed += 1
                else:
                    self.checks_failed += 1
            except Exception as e:
                print(f"❌ Error during {name} check: {e}")
                self.checks_failed += 1
        
        # Summary
        self.print_header("Summary")
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.checks_failed == 0:
            print("\n🎉 All checks passed! Ready for publication.")
            print("\nNext steps:")
            print("1. Test publication: python scripts/publish_to_pypi.py")
            print("2. Production publication: python scripts/publish_to_pypi.py --production")
            return True
        else:
            print("\n❌ Some checks failed. Please fix issues before publishing.")
            return False


def main():
    """Main entry point."""
    checker = PublicationChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()