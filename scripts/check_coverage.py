#!/usr/bin/env python3
"""Quick script to check current test coverage"""

import subprocess
import xml.etree.ElementTree as ET
import sys

# Run tests with coverage
print("Running unit tests with coverage...")
result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "tests/unit/",
    "--cov=claude_pm",
    "--cov-report=xml",
    "--tb=no",
    "-q"
], capture_output=True, text=True)

print(f"Tests run result: {result.returncode}")

# Parse coverage XML
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    
    # Get overall coverage
    line_rate = float(root.attrib['line-rate'])
    coverage_pct = line_rate * 100
    
    print(f"\n📊 Overall Coverage: {coverage_pct:.2f}%")
    
    # Get package details
    print("\n📦 Package Coverage:")
    for package in root.findall('.//package'):
        pkg_name = package.attrib['name']
        pkg_line_rate = float(package.attrib['line-rate'])
        pkg_coverage = pkg_line_rate * 100
        print(f"  {pkg_name}: {pkg_coverage:.2f}%")
    
    # Improvement from baseline
    baseline = 4.54
    improvement = coverage_pct - baseline
    print(f"\n📈 Improvement from baseline: +{improvement:.2f}%")
    print(f"🎯 Target: 80% (need +{80 - coverage_pct:.2f}% more)")
    
except Exception as e:
    print(f"Error parsing coverage: {e}")
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)