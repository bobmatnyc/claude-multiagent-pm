#!/usr/bin/env python3
"""
Security Agent Scanner Implementation
Comprehensive security validation test for the Claude PM Framework
"""

import os
import re
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import hashlib

class SecurityFinding:
    """Represents a single security finding"""
    def __init__(self, severity: str, category: str, title: str, description: str, 
                 file_path: str, line: int, column: int, pattern: str, 
                 recommendation: str, remediation: Dict):
        self.severity = severity
        self.category = category
        self.title = title
        self.description = description
        self.file_path = file_path
        self.line = line
        self.column = column
        self.pattern = pattern
        self.recommendation = recommendation
        self.remediation = remediation
        self.id = self._generate_id()
        
    def _generate_id(self) -> str:
        """Generate unique ID for finding"""
        data = f"{self.severity}{self.category}{self.file_path}{self.line}"
        return f"SEC-{hashlib.md5(data.encode()).hexdigest()[:8].upper()}"
    
    def to_dict(self) -> Dict:
        """Convert finding to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "file": self.file_path,
            "line": self.line,
            "column": self.column,
            "pattern": self.pattern,
            "recommendation": self.recommendation,
            "remediation": self.remediation
        }

class SecurityAgentScanner:
    """Security Agent Scanner Implementation"""
    
    def __init__(self, security_posture: str = "medium"):
        self.security_posture = security_posture
        self.findings = []
        self.scan_id = f"sec-scan-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        
        # Initialize security patterns
        self._init_critical_patterns()
        self._init_high_risk_patterns()
        self._init_medium_risk_patterns()
        
    def _init_critical_patterns(self):
        """Initialize critical security patterns - automatic veto"""
        self.critical_patterns = {
            # API Keys & Tokens
            "aws_access_key": {
                "pattern": r"AKIA[0-9A-Z]{16}",
                "description": "AWS Access Key ID detected",
                "recommendation": "Move to environment variables"
            },
            "aws_secret_key": {
                "pattern": r"aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}",
                "description": "AWS Secret Access Key detected",
                "recommendation": "Move to environment variables"
            },
            "github_token": {
                "pattern": r"ghp_[0-9a-zA-Z]{36}",
                "description": "GitHub Personal Access Token detected",
                "recommendation": "Use GitHub secrets or environment variables"
            },
            "generic_api_key": {
                "pattern": r"(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer[_-]?token)[\s]*[:=][\s]*['\"][a-zA-Z0-9]{20,}['\"]",
                "description": "Generic API key or token detected",
                "recommendation": "Move to secure configuration"
            },
            
            # Passwords & Credentials
            "hardcoded_password": {
                "pattern": r"(?i)(password|passwd|pwd|secret|key)[\s]*[:=][\s]*['\"][^\s'\"]{8,}['\"]",
                "description": "Hardcoded password detected",
                "recommendation": "Use environment variables or secure vault"
            },
            "db_password": {
                "pattern": r"(?i)(db[_-]?password|database[_-]?password|mysql[_-]?password|postgres[_-]?password|mongo[_-]?password)[\s]*[:=][\s]*['\"][^\s'\"]+['\"]",
                "description": "Database password detected",
                "recommendation": "Use environment variables"
            },
            "connection_string": {
                "pattern": r"(?i)(postgresql|mysql|mongodb)://[^:]+:[^@]+@",
                "description": "Database connection string with credentials",
                "recommendation": "Use environment variables for credentials"
            },
            
            # Private Keys & Certificates
            "private_key": {
                "pattern": r"-----BEGIN (RSA )?PRIVATE KEY-----",
                "description": "Private key detected in code",
                "recommendation": "Move to secure key management system"
            },
            "certificate": {
                "pattern": r"-----BEGIN CERTIFICATE-----",
                "description": "Certificate detected in code",
                "recommendation": "Move to secure certificate storage"
            },
            "ssh_key": {
                "pattern": r"-----BEGIN OPENSSH PRIVATE KEY-----",
                "description": "SSH private key detected",
                "recommendation": "Move to secure key management"
            }
        }
        
    def _init_high_risk_patterns(self):
        """Initialize high-risk security patterns - conditional veto"""
        self.high_risk_patterns = {
            # Weak Cryptography
            "md5_usage": {
                "pattern": r"(?i)(md5|hashlib\.md5|crypto\.createHash\(['\"]md5['\"])",
                "description": "Weak MD5 hash function usage",
                "recommendation": "Use SHA-256 or stronger hashing algorithm"
            },
            "sha1_usage": {
                "pattern": r"(?i)(sha1|hashlib\.sha1|crypto\.createHash\(['\"]sha1['\"])",
                "description": "Weak SHA1 hash function usage",
                "recommendation": "Use SHA-256 or stronger hashing algorithm"
            },
            "des_encryption": {
                "pattern": r"(?i)(des|crypto\.createCipher\(['\"]des['\"])",
                "description": "Weak DES encryption detected",
                "recommendation": "Use AES-256 or stronger encryption"
            },
            "rc4_encryption": {
                "pattern": r"(?i)(rc4|crypto\.createCipher\(['\"]rc4['\"])",
                "description": "Weak RC4 encryption detected",
                "recommendation": "Use AES-256 or stronger encryption"
            },
            
            # Code Vulnerabilities
            "eval_usage": {
                "pattern": r"(?i)\beval\s*\(",
                "description": "Dangerous eval() usage detected",
                "recommendation": "Avoid eval() or use safe alternatives"
            },
            "exec_usage": {
                "pattern": r"(?i)\bexec\s*\(",
                "description": "Dangerous exec() usage detected",
                "recommendation": "Avoid exec() or use safe alternatives"
            },
            "pickle_usage": {
                "pattern": r"(?i)pickle\.loads?\s*\(",
                "description": "Unsafe pickle deserialization",
                "recommendation": "Use JSON or other safe serialization"
            },
            "shell_injection": {
                "pattern": r"(?i)(os\.system|subprocess\.call|shell=True)",
                "description": "Potential shell injection vulnerability",
                "recommendation": "Use subprocess with argument list"
            },
            
            # SQL Injection
            "sql_concat": {
                "pattern": r"(?i)(SELECT|INSERT|UPDATE|DELETE).*\+.*['\"]",
                "description": "SQL injection via string concatenation",
                "recommendation": "Use parameterized queries"
            },
            "sql_format": {
                "pattern": r"(?i)(SELECT|INSERT|UPDATE|DELETE).*%s.*%",
                "description": "SQL injection via string formatting",
                "recommendation": "Use parameterized queries"
            },
            "sql_fstring": {
                "pattern": r"(?i)(SELECT|INSERT|UPDATE|DELETE).*f['\"].*\{.*\}",
                "description": "SQL injection via f-string",
                "recommendation": "Use parameterized queries"
            },
            
            # Insecure Configuration
            "bind_all_interfaces": {
                "pattern": r"(?i)(host|bind|listen)[\s]*[:=][\s]*['\"]0\.0\.0\.0['\"]",
                "description": "Binding to all interfaces (0.0.0.0)",
                "recommendation": "Bind to specific interface or localhost"
            },
            "debug_enabled": {
                "pattern": r"(?i)debug[\s]*[:=][\s]*(True|true|1)",
                "description": "Debug mode enabled",
                "recommendation": "Disable debug mode in production"
            },
            "ssl_disabled": {
                "pattern": r"(?i)(ssl|tls)[\s]*[:=][\s]*(False|false|0|off|disable)",
                "description": "SSL/TLS disabled",
                "recommendation": "Enable SSL/TLS for secure communication"
            }
        }
        
    def _init_medium_risk_patterns(self):
        """Initialize medium-risk security patterns - warnings"""
        self.medium_risk_patterns = {
            # Missing Security Headers
            "missing_xframe": {
                "pattern": r"(?i)X-Frame-Options",
                "description": "Missing X-Frame-Options header",
                "recommendation": "Add X-Frame-Options header to prevent clickjacking"
            },
            "missing_csp": {
                "pattern": r"(?i)Content-Security-Policy",
                "description": "Missing Content-Security-Policy header",
                "recommendation": "Add CSP header to prevent XSS attacks"
            },
            "missing_hsts": {
                "pattern": r"(?i)Strict-Transport-Security",
                "description": "Missing HSTS header",
                "recommendation": "Add HSTS header for HTTPS enforcement"
            },
            
            # Session Security
            "insecure_session": {
                "pattern": r"(?i)(secure|httpOnly|sameSite)[\s]*[:=][\s]*(false|False|0)",
                "description": "Insecure session configuration",
                "recommendation": "Enable secure session settings"
            },
            "weak_session_secret": {
                "pattern": r"(?i)secret[\s]*[:=][\s]*['\"][^'\"]{1,15}['\"]",
                "description": "Weak session secret",
                "recommendation": "Use strong, random session secret"
            },
            
            # Input Validation
            "no_input_validation": {
                "pattern": r"(?i)(req\.body|req\.query|req\.params|\$_GET|\$_POST).*without.*validation",
                "description": "Input used without validation",
                "recommendation": "Validate and sanitize all input"
            },
            "file_upload_risk": {
                "pattern": r"(?i)(move_uploaded_file|multer|file.*upload).*without.*validation",
                "description": "File upload without validation",
                "recommendation": "Validate file type, size, and content"
            }
        }
    
    def scan_file(self, file_path: str) -> List[SecurityFinding]:
        """Scan a single file for security issues"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Scan for critical issues
            findings.extend(self._scan_patterns(file_path, lines, self.critical_patterns, "critical", "secrets"))
            
            # Scan for high-risk issues
            findings.extend(self._scan_patterns(file_path, lines, self.high_risk_patterns, "high", "vulnerabilities"))
            
            # Scan for medium-risk issues
            findings.extend(self._scan_patterns(file_path, lines, self.medium_risk_patterns, "medium", "configuration"))
            
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
            
        return findings
    
    def _scan_patterns(self, file_path: str, lines: List[str], patterns: Dict, 
                      severity: str, category: str) -> List[SecurityFinding]:
        """Scan for specific patterns in file content"""
        findings = []
        
        for pattern_name, pattern_info in patterns.items():
            regex = re.compile(pattern_info["pattern"], re.IGNORECASE | re.MULTILINE)
            
            for line_num, line in enumerate(lines, 1):
                matches = regex.finditer(line)
                
                for match in matches:
                    finding = SecurityFinding(
                        severity=severity,
                        category=category,
                        title=pattern_info["description"],
                        description=f"{pattern_info['description']} in {file_path}:{line_num}",
                        file_path=file_path,
                        line=line_num,
                        column=match.start(),
                        pattern=pattern_info["pattern"],
                        recommendation=pattern_info["recommendation"],
                        remediation={
                            "steps": [
                                "Review the detected pattern",
                                "Apply recommended fix",
                                "Test the changes",
                                "Re-scan to verify fix"
                            ],
                            "references": [
                                "https://owasp.org/www-project-top-ten/",
                                "https://docs.microsoft.com/en-us/azure/security/"
                            ]
                        }
                    )
                    findings.append(finding)
                    
        return findings
    
    def scan_directory(self, directory_path: str) -> List[SecurityFinding]:
        """Scan entire directory for security issues"""
        all_findings = []
        
        # File extensions to scan
        scan_extensions = {'.py', '.js', '.ts', '.php', '.java', '.go', '.rb', '.cs', 
                          '.yml', '.yaml', '.json', '.xml', '.html', '.htm', '.css',
                          '.dockerfile', '.pem', '.key', '.crt', '.env'}
        
        for root, dirs, files in os.walk(directory_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '.venv', '__pycache__'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                if file_ext in scan_extensions or file.lower() in {'dockerfile', 'makefile'}:
                    file_findings = self.scan_file(file_path)
                    all_findings.extend(file_findings)
                    
        return all_findings
    
    def evaluate_veto_decision(self, findings: List[SecurityFinding]) -> Tuple[str, str, bool]:
        """Evaluate whether to veto the push based on findings"""
        critical_count = sum(1 for f in findings if f.severity == "critical")
        high_count = sum(1 for f in findings if f.severity == "high")
        medium_count = sum(1 for f in findings if f.severity == "medium")
        
        # Critical issues - always veto
        if critical_count > 0:
            return "BLOCK", "Critical security issues detected", False
        
        # High issues - conditional veto
        if high_count > 0:
            return "BLOCK", "High-risk security issues detected", True
        
        # Medium issues - veto only in high security mode
        if medium_count > 0 and self.security_posture == "high":
            return "BLOCK", "Medium-risk issues in high security mode", True
        
        # No blocking issues
        if medium_count > 0:
            return "WARN", "Medium-risk security issues detected", False
        
        return "PASS", "No blocking security issues", False
    
    def generate_report(self, findings: List[SecurityFinding]) -> Dict:
        """Generate comprehensive security report"""
        veto_decision, veto_reason, override_available = self.evaluate_veto_decision(findings)
        
        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity_counts[finding.severity] += 1
        
        # Get unique files scanned
        scanned_files = set(f.file_path for f in findings)
        
        report = {
            "scan_id": self.scan_id,
            "timestamp": datetime.now().isoformat(),
            "project": "claude-multiagent-pm-security-test",
            "security_posture": self.security_posture,
            "summary": {
                "total_files": len(scanned_files),
                "scanned_files": len(scanned_files),
                "issues_found": len(findings),
                "critical": severity_counts["critical"],
                "high": severity_counts["high"],
                "medium": severity_counts["medium"],
                "low": severity_counts["low"]
            },
            "findings": [f.to_dict() for f in findings],
            "veto_decision": veto_decision,
            "veto_reason": veto_reason,
            "override_available": override_available
        }
        
        return report
    
    def print_veto_response(self, findings: List[SecurityFinding]):
        """Print formatted veto response"""
        veto_decision, veto_reason, override_available = self.evaluate_veto_decision(findings)
        
        critical_findings = [f for f in findings if f.severity == "critical"]
        high_findings = [f for f in findings if f.severity == "high"]
        medium_findings = [f for f in findings if f.severity == "medium"]
        
        if veto_decision == "BLOCK":
            if critical_findings:
                print("🚨 SECURITY VETO - CRITICAL ISSUE DETECTED")
                print("=" * 50)
                for finding in critical_findings:
                    print(f"\nIssue: {finding.title}")
                    print(f"File: {finding.file_path}:{finding.line}")
                    print(f"Pattern: {finding.pattern}")
                    print(f"\nRESOLUTION REQUIRED:")
                    for step in finding.remediation["steps"]:
                        print(f"- {step}")
                    print("\nPush BLOCKED until resolved.")
                    
            elif high_findings:
                print("🔒 SECURITY VETO - HIGH RISK ISSUE")
                print("=" * 50)
                for finding in high_findings:
                    print(f"\nIssue: {finding.title}")
                    print(f"File: {finding.file_path}:{finding.line}")
                    print(f"Pattern: {finding.pattern}")
                    print(f"\nRECOMMENDATION:")
                    print(f"- {finding.recommendation}")
                    if override_available:
                        print(f"\nOverride available with: --security-override={finding.id}")
                        
        elif veto_decision == "WARN":
            print("⚠️ SECURITY WARNING - MEDIUM RISK")
            print("=" * 50)
            for finding in medium_findings:
                print(f"\nIssue: {finding.title}")
                print(f"File: {finding.file_path}:{finding.line}")
                print(f"\nRECOMMENDATION:")
                print(f"- {finding.recommendation}")
                
            if self.security_posture == "high":
                print("\nHigh Security Mode: Push blocked until resolved.")
            else:
                print("\nStandard Mode: Consider fixing before production.")
                
        else:
            print("✅ SECURITY SCAN PASSED")
            print("=" * 50)
            print("No blocking security issues detected.")

def main():
    """Main function for testing the Security Agent scanner"""
    test_directory = "/Users/masa/Projects/claude-multiagent-pm/test/security-test-files"
    
    print("🔐 Security Agent Scanner - Comprehensive Validation Test")
    print("=" * 60)
    print(f"Scanning directory: {test_directory}")
    print()
    
    # Test with different security postures
    for posture in ["medium", "high"]:
        print(f"\n🔍 Testing with Security Posture: {posture.upper()}")
        print("-" * 40)
        
        scanner = SecurityAgentScanner(security_posture=posture)
        findings = scanner.scan_directory(test_directory)
        
        print(f"Total findings: {len(findings)}")
        print(f"Critical: {len([f for f in findings if f.severity == 'critical'])}")
        print(f"High: {len([f for f in findings if f.severity == 'high'])}")
        print(f"Medium: {len([f for f in findings if f.severity == 'medium'])}")
        
        # Generate and save report
        report = scanner.generate_report(findings)
        report_file = f"/Users/masa/Projects/claude-multiagent-pm/test/security-test-files/security-report-{posture}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {report_file}")
        
        # Print veto response
        print("\n📋 Veto Decision:")
        scanner.print_veto_response(findings)
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()