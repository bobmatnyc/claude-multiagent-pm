#!/usr/bin/env python3
"""
Documentation Drift Detector

Monitors for documentation drift and outdated content by tracking file modifications,
API changes, and configuration updates that affect documentation.

Features:
- File modification time tracking
- API change detection
- Configuration drift monitoring
- Automated drift reports with actionable recommendations
- Integration with framework tools

Usage:
    python doc_drift_detector.py [options]
    python doc_drift_detector.py --help
"""

import os
import re
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import argparse
import hashlib


@dataclass
class DriftItem:
    """Represents a detected drift item"""
    file_path: str
    drift_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    last_modified: str
    related_files: List[str]
    recommendations: List[str]
    auto_fixable: bool = False


@dataclass
class DriftReport:
    """Complete drift detection report"""
    timestamp: str
    base_directory: str
    total_files: int
    drift_items: List[DriftItem]
    summary: Dict[str, int]
    recommendations: List[str]


class DocumentDriftDetector:
    """Detects documentation drift and outdated content"""
    
    def __init__(self, base_dir: str, config_file: str = None):
        self.base_dir = Path(base_dir)
        self.config = self._load_config(config_file)
        self.drift_items: List[DriftItem] = []
        self.file_cache: Dict[str, Dict] = {}
        
    def _load_config(self, config_file: str = None) -> Dict:
        """Load configuration for drift detection"""
        default_config = {
            "max_age_days": 30,
            "critical_files": [
                "README.md",
                "QUICK_START.md",
                "DEPLOYMENT_GUIDE.md",
                "TICKETING_SYSTEM.md"
            ],
            "api_patterns": [
                r"aitrackdown\s+\w+",
                r"atd\s+\w+",
                r"mem0\.\w+",
                r"claude\.\w+"
            ],
            "config_files": [
                "package.json",
                "requirements.txt",
                "*.yml",
                "*.yaml",
                "*.json"
            ],
            "ignore_patterns": [
                "archive/",
                "node_modules/",
                ".git/",
                "*.tmp",
                "*.log"
            ]
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config file: {e}")
        
        return default_config
    
    def detect_drift(self) -> DriftReport:
        """Main drift detection process"""
        print(f"🔍 Starting drift detection in {self.base_dir}")
        
        # Collect all relevant files
        files = self._collect_files()
        print(f"📄 Analyzing {len(files)} files")
        
        # Build file cache with metadata
        self._build_file_cache(files)
        
        # Run drift detection checks
        self._detect_stale_files()
        self._detect_api_changes()
        self._detect_config_drift()
        self._detect_broken_references()
        self._detect_version_mismatches()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = DriftReport(
            timestamp=datetime.now().isoformat(),
            base_directory=str(self.base_dir),
            total_files=len(files),
            drift_items=self.drift_items,
            summary=self._generate_summary(),
            recommendations=recommendations
        )
        
        self._print_summary(report)
        return report
    
    def _collect_files(self) -> List[Path]:
        """Collect all files for analysis"""
        files = []
        
        # Collect markdown files
        md_files = list(self.base_dir.rglob("*.md"))
        files.extend(md_files)
        
        # Collect configuration files
        for pattern in self.config["config_files"]:
            config_files = list(self.base_dir.rglob(pattern))
            files.extend(config_files)
        
        # Filter out ignored patterns
        filtered_files = []
        for file in files:
            skip = False
            for ignore_pattern in self.config["ignore_patterns"]:
                if ignore_pattern in str(file):
                    skip = True
                    break
            if not skip:
                filtered_files.append(file)
        
        return filtered_files
    
    def _build_file_cache(self, files: List[Path]):
        """Build cache of file metadata"""
        for file in files:
            try:
                stat = file.stat()
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.file_cache[str(file)] = {
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "content": content,
                    "hash": hashlib.md5(content.encode()).hexdigest(),
                    "line_count": len(content.splitlines())
                }
            except Exception as e:
                print(f"⚠️  Could not read {file}: {e}")
    
    def _detect_stale_files(self):
        """Detect files that haven't been updated in a while"""
        max_age = timedelta(days=self.config["max_age_days"])
        now = datetime.now()
        
        for file_path, metadata in self.file_cache.items():
            if not file_path.endswith('.md'):
                continue
                
            age = now - metadata["modified"]
            file_name = Path(file_path).name
            
            if age > max_age:
                severity = "high" if file_name in self.config["critical_files"] else "medium"
                
                # Check if file references recent tickets or features
                recent_refs = self._find_recent_references(metadata["content"])
                if recent_refs:
                    severity = "low"  # File might be current despite age
                
                self.drift_items.append(DriftItem(
                    file_path=file_path,
                    drift_type="stale_content",
                    severity=severity,
                    description=f"File not updated in {age.days} days",
                    last_modified=metadata["modified"].isoformat(),
                    related_files=[],
                    recommendations=[
                        f"Review {file_name} for accuracy",
                        "Update modification date if content is current",
                        "Add recent examples or references"
                    ]
                ))
    
    def _detect_api_changes(self):
        """Detect documentation that references potentially outdated APIs"""
        for file_path, metadata in self.file_cache.items():
            if not file_path.endswith('.md'):
                continue
            
            content = metadata["content"]
            
            # Check for API patterns
            for pattern in self.config["api_patterns"]:
                matches = re.findall(pattern, content)
                if matches:
                    # Check if API commands are still valid
                    for match in matches:
                        if not self._verify_api_command(match):
                            self.drift_items.append(DriftItem(
                                file_path=file_path,
                                drift_type="api_change",
                                severity="high",
                                description=f"Potentially outdated API reference: {match}",
                                last_modified=metadata["modified"].isoformat(),
                                related_files=[],
                                recommendations=[
                                    f"Verify {match} command is still valid",
                                    "Update command syntax if changed",
                                    "Add version-specific documentation"
                                ]
                            ))
    
    def _detect_config_drift(self):
        """Detect configuration changes that affect documentation"""
        config_changes = []
        
        # Check for package.json changes
        package_json = self.base_dir / "package.json"
        if package_json.exists():
            config_changes.extend(self._check_package_changes(package_json))
        
        # Check for requirements.txt changes
        requirements = self.base_dir / "requirements.txt"
        if requirements.exists():
            config_changes.extend(self._check_requirements_changes(requirements))
        
        # Check for YAML configuration changes
        yaml_files = list(self.base_dir.rglob("*.yml")) + list(self.base_dir.rglob("*.yaml"))
        for yaml_file in yaml_files:
            config_changes.extend(self._check_yaml_changes(yaml_file))
        
        # Generate drift items for configuration changes
        for change in config_changes:
            self.drift_items.append(DriftItem(
                file_path=change["file"],
                drift_type="config_drift",
                severity="medium",
                description=change["description"],
                last_modified=change["modified"],
                related_files=change.get("related_files", []),
                recommendations=[
                    "Update documentation to reflect configuration changes",
                    "Verify examples still work with new configuration",
                    "Update installation instructions if needed"
                ]
            ))
    
    def _detect_broken_references(self):
        """Detect broken references to files, tickets, or other resources"""
        for file_path, metadata in self.file_cache.items():
            if not file_path.endswith('.md'):
                continue
            
            content = metadata["content"]
            
            # Check for file references
            file_refs = re.findall(r'`([^`]+\.[a-z]+)`', content)
            for ref in file_refs:
                if not self._verify_file_reference(file_path, ref):
                    self.drift_items.append(DriftItem(
                        file_path=file_path,
                        drift_type="broken_reference",
                        severity="medium",
                        description=f"Broken file reference: {ref}",
                        last_modified=metadata["modified"].isoformat(),
                        related_files=[],
                        recommendations=[
                            f"Fix or remove reference to {ref}",
                            "Update path if file was moved",
                            "Add note if file is intentionally missing"
                        ]
                    ))
            
            # Check for ticket references
            ticket_refs = re.findall(r'\b((?:EP|ISS|TSK|MEM|FRW|FWK)-\d+)\b', content)
            for ticket_id in ticket_refs:
                if not self._verify_ticket_reference(ticket_id):
                    self.drift_items.append(DriftItem(
                        file_path=file_path,
                        drift_type="broken_ticket_reference",
                        severity="low",
                        description=f"Ticket reference may be outdated: {ticket_id}",
                        last_modified=metadata["modified"].isoformat(),
                        related_files=[],
                        recommendations=[
                            f"Verify ticket {ticket_id} still exists",
                            "Update reference if ticket was merged or closed",
                            "Add context about ticket status"
                        ]
                    ))
    
    def _detect_version_mismatches(self):
        """Detect version mismatches between documentation and actual versions"""
        # Check for version references in documentation
        for file_path, metadata in self.file_cache.items():
            if not file_path.endswith('.md'):
                continue
            
            content = metadata["content"]
            
            # Find version references
            version_patterns = [
                r'version\s+(\d+\.\d+\.\d+)',
                r'v(\d+\.\d+\.\d+)',
                r'@(\d+\.\d+\.\d+)'
            ]
            
            for pattern in version_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for version in matches:
                    if not self._verify_version(version):
                        self.drift_items.append(DriftItem(
                            file_path=file_path,
                            drift_type="version_mismatch",
                            severity="medium",
                            description=f"Version reference may be outdated: {version}",
                            last_modified=metadata["modified"].isoformat(),
                            related_files=[],
                            recommendations=[
                                f"Verify version {version} is current",
                                "Update to latest version if appropriate",
                                "Add version compatibility notes"
                            ]
                        ))
    
    def _find_recent_references(self, content: str) -> List[str]:
        """Find references to recent tickets or features"""
        recent_patterns = [
            r'\b((?:EP|ISS|TSK|MEM|FRW|FWK)-\d+)\b',
            r'20(?:24|25)-\d{2}-\d{2}',  # Recent dates
            r'v\d+\.\d+\.\d+'  # Version references
        ]
        
        recent_refs = []
        for pattern in recent_patterns:
            matches = re.findall(pattern, content)
            recent_refs.extend(matches)
        
        return recent_refs
    
    def _verify_api_command(self, command: str) -> bool:
        """Verify if an API command is still valid"""
        try:
            if command.startswith('aitrackdown') or command.startswith('atd'):
                result = subprocess.run(
                    [command.split()[0], '--help'],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
        except Exception:
            pass
        return True  # Assume valid if can't verify
    
    def _verify_file_reference(self, doc_path: str, ref: str) -> bool:
        """Verify if a file reference is still valid"""
        doc_dir = Path(doc_path).parent
        potential_paths = [
            Path(ref),
            doc_dir / ref,
            self.base_dir / ref
        ]
        
        for path in potential_paths:
            if path.exists():
                return True
        return False
    
    def _verify_ticket_reference(self, ticket_id: str) -> bool:
        """Verify if a ticket reference is still valid"""
        try:
            result = subprocess.run(
                ['aitrackdown', 'show', ticket_id],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            pass
        return True  # Assume valid if can't verify
    
    def _verify_version(self, version: str) -> bool:
        """Verify if a version reference is current"""
        # Basic version validation - could be enhanced with package-specific checks
        try:
            parts = version.split('.')
            if len(parts) == 3 and all(part.isdigit() for part in parts):
                # Check if version seems reasonable (not too old)
                major = int(parts[0])
                return major >= 1  # Assume versions >= 1.0.0 are reasonable
        except:
            pass
        return True
    
    def _check_package_changes(self, package_json: Path) -> List[Dict]:
        """Check for package.json changes that affect documentation"""
        changes = []
        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            # Check for new dependencies that might need documentation
            if 'dependencies' in package_data:
                for dep_name, dep_version in package_data['dependencies'].items():
                    if self._is_recently_added_dependency(dep_name):
                        changes.append({
                            "file": str(package_json),
                            "description": f"New dependency {dep_name} may need documentation",
                            "modified": datetime.fromtimestamp(package_json.stat().st_mtime).isoformat()
                        })
        except Exception:
            pass
        
        return changes
    
    def _check_requirements_changes(self, requirements_file: Path) -> List[Dict]:
        """Check for requirements.txt changes that affect documentation"""
        changes = []
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read().splitlines()
            
            # Check for new packages
            for req in requirements:
                if req.strip() and not req.startswith('#'):
                    package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                    if self._is_recently_added_dependency(package_name):
                        changes.append({
                            "file": str(requirements_file),
                            "description": f"New requirement {package_name} may need documentation",
                            "modified": datetime.fromtimestamp(requirements_file.stat().st_mtime).isoformat()
                        })
        except Exception:
            pass
        
        return changes
    
    def _check_yaml_changes(self, yaml_file: Path) -> List[Dict]:
        """Check for YAML configuration changes"""
        changes = []
        try:
            with open(yaml_file, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            # Check for configuration changes that might affect documentation
            if yaml_data and isinstance(yaml_data, dict):
                if 'version' in yaml_data:
                    changes.append({
                        "file": str(yaml_file),
                        "description": f"Configuration version in {yaml_file.name} may need documentation update",
                        "modified": datetime.fromtimestamp(yaml_file.stat().st_mtime).isoformat()
                    })
        except Exception:
            pass
        
        return changes
    
    def _is_recently_added_dependency(self, package_name: str) -> bool:
        """Check if a dependency was recently added"""
        # This is a simplified check - in practice, you'd compare with a baseline
        recent_packages = ['mem0', 'aitrackdown', 'langgraph']
        return package_name in recent_packages
    
    def _generate_recommendations(self) -> List[str]:
        """Generate overall recommendations based on drift analysis"""
        recommendations = []
        
        # Count drift types
        drift_counts = {}
        for item in self.drift_items:
            drift_counts[item.drift_type] = drift_counts.get(item.drift_type, 0) + 1
        
        # Generate recommendations based on patterns
        if drift_counts.get("stale_content", 0) > 5:
            recommendations.append("Schedule regular documentation review cycles")
        
        if drift_counts.get("api_change", 0) > 0:
            recommendations.append("Implement API change monitoring in documentation workflow")
        
        if drift_counts.get("broken_reference", 0) > 0:
            recommendations.append("Add automated link checking to CI/CD pipeline")
        
        if drift_counts.get("config_drift", 0) > 0:
            recommendations.append("Set up configuration change notifications for documentation team")
        
        if drift_counts.get("version_mismatch", 0) > 0:
            recommendations.append("Implement version synchronization checks")
        
        return recommendations
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generate summary statistics"""
        summary = {
            "total_drift_items": len(self.drift_items),
            "critical": len([item for item in self.drift_items if item.severity == "critical"]),
            "high": len([item for item in self.drift_items if item.severity == "high"]),
            "medium": len([item for item in self.drift_items if item.severity == "medium"]),
            "low": len([item for item in self.drift_items if item.severity == "low"])
        }
        
        # Add drift type counts
        for item in self.drift_items:
            summary[f"{item.drift_type}_count"] = summary.get(f"{item.drift_type}_count", 0) + 1
        
        return summary
    
    def _print_summary(self, report: DriftReport):
        """Print drift detection summary"""
        print(f"\n📊 Drift Detection Summary:")
        print(f"  Total files analyzed: {report.total_files}")
        print(f"  Total drift items: {report.summary['total_drift_items']}")
        print(f"  🔴 Critical: {report.summary['critical']}")
        print(f"  🟠 High: {report.summary['high']}")
        print(f"  🟡 Medium: {report.summary['medium']}")
        print(f"  🟢 Low: {report.summary['low']}")
        
        if report.summary['total_drift_items'] > 0:
            print(f"\n🔍 Drift Types:")
            drift_types = set(item.drift_type for item in report.drift_items)
            for drift_type in sorted(drift_types):
                count = len([item for item in report.drift_items if item.drift_type == drift_type])
                print(f"  {drift_type}: {count}")
        
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
    
    def save_report(self, report: DriftReport, output_path: str = None):
        """Save drift report to file"""
        if not output_path:
            output_path = self.base_dir / "drift_report.json"
        
        # Convert dataclasses to dict for JSON serialization
        report_dict = {
            "timestamp": report.timestamp,
            "base_directory": report.base_directory,
            "total_files": report.total_files,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "drift_items": [asdict(item) for item in report.drift_items]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"📄 Drift report saved to: {output_path}")
        return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Documentation Drift Detector")
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to analyze (default: current directory)'
    )
    parser.add_argument(
        '--config',
        '-c',
        help='Configuration file path'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for drift report'
    )
    parser.add_argument(
        '--max-age',
        type=int,
        default=30,
        help='Maximum age in days before considering content stale'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = DocumentDriftDetector(args.directory, args.config)
    
    # Override max age if specified
    if args.max_age:
        detector.config["max_age_days"] = args.max_age
    
    # Run drift detection
    report = detector.detect_drift()
    
    # Save report
    detector.save_report(report, args.output)
    
    # Exit with appropriate code
    critical_count = report.summary.get('critical', 0)
    high_count = report.summary.get('high', 0)
    
    if critical_count > 0:
        sys.exit(2)  # Critical issues
    elif high_count > 0:
        sys.exit(1)  # High priority issues
    else:
        sys.exit(0)  # Success


if __name__ == '__main__':
    main()