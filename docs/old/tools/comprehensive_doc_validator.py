#!/usr/bin/env python3
"""
Comprehensive Documentation Validator

A complete validation suite for documentation links, code examples, and references.
Validates internal/external links, code syntax, ticket references, and markdown structure.

Features:
- Link validation (internal/external)
- Code example syntax checking
- Ticket reference validation against ai-trackdown system
- Markdown structure validation
- Comprehensive reporting

Usage:
    python comprehensive_doc_validator.py [directory]
    python comprehensive_doc_validator.py --help
"""

import os
import re
import sys
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import argparse
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ValidationResult:
    """Result of a validation check"""
    file_path: str
    check_type: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    line_number: Optional[int] = None
    details: Optional[Dict] = None


class DocumentValidator:
    """Comprehensive document validation suite"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.results: List[ValidationResult] = []
        self.ticket_cache: Dict[str, bool] = {}
        self.link_cache: Dict[str, bool] = {}
        
    def validate_directory(self) -> List[ValidationResult]:
        """Validate all documentation in directory"""
        print(f"🔍 Starting comprehensive validation of {self.base_dir}")
        
        # Find all markdown files
        md_files = list(self.base_dir.rglob("*.md"))
        print(f"📄 Found {len(md_files)} markdown files")
        
        # Validate each file
        for md_file in md_files:
            self._validate_file(md_file)
            
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _validate_file(self, file_path: Path):
        """Validate a single markdown file"""
        print(f"  📋 Validating: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="file_access",
                status="fail",
                message=f"Cannot read file: {e}"
            ))
            return
        
        # Run all validation checks
        self._validate_markdown_structure(file_path, content, lines)
        self._validate_links(file_path, content, lines)
        self._validate_code_examples(file_path, content, lines)
        self._validate_ticket_references(file_path, content, lines)
        self._validate_file_references(file_path, content, lines)
    
    def _validate_markdown_structure(self, file_path: Path, content: str, lines: List[str]):
        """Validate markdown structure and formatting"""
        
        # Check for title (H1)
        h1_count = content.count('\n# ')
        if h1_count == 0:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="structure",
                status="warning",
                message="No H1 title found"
            ))
        elif h1_count > 1:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="structure",
                status="warning",
                message=f"Multiple H1 titles found ({h1_count})"
            ))
        
        # Check heading hierarchy
        prev_level = 0
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level > prev_level + 1:
                    self.results.append(ValidationResult(
                        file_path=str(file_path),
                        check_type="structure",
                        status="warning",
                        message=f"Heading level jump from H{prev_level} to H{level}",
                        line_number=i
                    ))
                prev_level = level
        
        # Check for empty sections
        sections = re.split(r'\n#+\s+', content)
        for i, section in enumerate(sections[1:], 1):  # Skip first split
            if len(section.strip()) < 50:  # Arbitrary threshold
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="structure",
                    status="warning",
                    message=f"Very short section #{i} (may be empty)"
                ))
        
        # Check for table of contents consistency
        toc_pattern = r'^\s*[-*+]\s+\[.*?\]\(#.*?\)'
        toc_links = re.findall(toc_pattern, content, re.MULTILINE)
        if toc_links:
            for toc_link in toc_links:
                anchor = re.search(r'\(#(.*?)\)', toc_link)
                if anchor:
                    anchor_id = anchor.group(1)
                    # Check if corresponding heading exists
                    heading_pattern = f"#{{{1,6}}}\\s+.*?{re.escape(anchor_id.replace('-', ' '))}"
                    if not re.search(heading_pattern, content, re.IGNORECASE):
                        self.results.append(ValidationResult(
                            file_path=str(file_path),
                            check_type="structure",
                            status="warning",
                            message=f"TOC link #{anchor_id} has no corresponding heading"
                        ))
    
    def _validate_links(self, file_path: Path, content: str, lines: List[str]):
        """Validate all links in the document"""
        
        # Find all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, link_url in links:
            line_num = self._find_line_number(lines, f"[{link_text}]({link_url})")
            
            if link_url.startswith('http'):
                # External link
                self._validate_external_link(file_path, link_url, line_num)
            elif link_url.startswith('#'):
                # Anchor link
                self._validate_anchor_link(file_path, content, link_url, line_num)
            else:
                # Internal file link
                self._validate_internal_link(file_path, link_url, line_num)
    
    def _validate_external_link(self, file_path: Path, url: str, line_num: int):
        """Validate external link availability"""
        if url in self.link_cache:
            if not self.link_cache[url]:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="external_link",
                    status="fail",
                    message=f"External link unavailable: {url}",
                    line_number=line_num
                ))
            return
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DocValidator/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            if response.getcode() == 200:
                self.link_cache[url] = True
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="external_link",
                    status="pass",
                    message=f"External link valid: {url}",
                    line_number=line_num
                ))
            else:
                self.link_cache[url] = False
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="external_link",
                    status="fail",
                    message=f"External link returned {response.getcode()}: {url}",
                    line_number=line_num
                ))
        except Exception as e:
            self.link_cache[url] = False
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="external_link",
                status="fail",
                message=f"External link error: {url} - {str(e)}",
                line_number=line_num
            ))
    
    def _validate_anchor_link(self, file_path: Path, content: str, anchor: str, line_num: int):
        """Validate anchor link within document"""
        anchor_id = anchor[1:]  # Remove #
        
        # Look for corresponding heading
        heading_patterns = [
            f"#{{{1,6}}}\\s+.*?{re.escape(anchor_id.replace('-', ' '))}",
            f"#{{{1,6}}}\\s+.*?{re.escape(anchor_id.replace('-', '_'))}",
            f"#{{{1,6}}}\\s+.*?{re.escape(anchor_id)}"
        ]
        
        found = False
        for pattern in heading_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break
        
        if found:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="anchor_link",
                status="pass",
                message=f"Anchor link valid: {anchor}",
                line_number=line_num
            ))
        else:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="anchor_link",
                status="fail",
                message=f"Anchor link target not found: {anchor}",
                line_number=line_num
            ))
    
    def _validate_internal_link(self, file_path: Path, link_path: str, line_num: int):
        """Validate internal file link"""
        # Resolve relative path
        if link_path.startswith('./'):
            target_path = file_path.parent / link_path[2:]
        elif link_path.startswith('../'):
            target_path = file_path.parent / link_path
        else:
            target_path = file_path.parent / link_path
        
        # Normalize path
        try:
            target_path = target_path.resolve()
        except Exception:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="internal_link",
                status="fail",
                message=f"Invalid internal link path: {link_path}",
                line_number=line_num
            ))
            return
        
        if target_path.exists():
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="internal_link",
                status="pass",
                message=f"Internal link valid: {link_path}",
                line_number=line_num
            ))
        else:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="internal_link",
                status="fail",
                message=f"Internal link target not found: {link_path}",
                line_number=line_num
            ))
    
    def _validate_code_examples(self, file_path: Path, content: str, lines: List[str]):
        """Validate code examples for syntax"""
        
        # Find code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        for lang, code in code_blocks:
            if not lang:
                continue
                
            line_num = self._find_line_number(lines, f"```{lang}")
            
            if lang.lower() in ['python', 'py']:
                self._validate_python_code(file_path, code, line_num)
            elif lang.lower() in ['bash', 'shell', 'sh']:
                self._validate_bash_code(file_path, code, line_num)
            elif lang.lower() in ['javascript', 'js']:
                self._validate_javascript_code(file_path, code, line_num)
            elif lang.lower() in ['json']:
                self._validate_json_code(file_path, code, line_num)
            else:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="code_syntax",
                    status="warning",
                    message=f"Unknown language for syntax validation: {lang}",
                    line_number=line_num
                ))
    
    def _validate_python_code(self, file_path: Path, code: str, line_num: int):
        """Validate Python code syntax"""
        try:
            compile(code, f"{file_path}:{line_num}", 'exec')
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="python_syntax",
                status="pass",
                message="Python code syntax valid",
                line_number=line_num
            ))
        except SyntaxError as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="python_syntax",
                status="fail",
                message=f"Python syntax error: {e}",
                line_number=line_num
            ))
    
    def _validate_bash_code(self, file_path: Path, code: str, line_num: int):
        """Validate Bash code syntax"""
        try:
            # Basic bash syntax validation using bash -n
            result = subprocess.run(
                ['bash', '-n'],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="bash_syntax",
                    status="pass",
                    message="Bash code syntax valid",
                    line_number=line_num
                ))
            else:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="bash_syntax",
                    status="fail",
                    message=f"Bash syntax error: {result.stderr}",
                    line_number=line_num
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="bash_syntax",
                status="warning",
                message=f"Cannot validate bash syntax: {e}",
                line_number=line_num
            ))
    
    def _validate_javascript_code(self, file_path: Path, code: str, line_num: int):
        """Validate JavaScript code syntax using node if available"""
        try:
            result = subprocess.run(
                ['node', '--check'],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="javascript_syntax",
                    status="pass",
                    message="JavaScript code syntax valid",
                    line_number=line_num
                ))
            else:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="javascript_syntax",
                    status="fail",
                    message=f"JavaScript syntax error: {result.stderr}",
                    line_number=line_num
                ))
        except FileNotFoundError:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="javascript_syntax",
                status="warning",
                message="Node.js not available for JavaScript validation",
                line_number=line_num
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="javascript_syntax",
                status="warning",
                message=f"Cannot validate JavaScript syntax: {e}",
                line_number=line_num
            ))
    
    def _validate_json_code(self, file_path: Path, code: str, line_num: int):
        """Validate JSON code syntax"""
        try:
            json.loads(code)
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="json_syntax",
                status="pass",
                message="JSON syntax valid",
                line_number=line_num
            ))
        except json.JSONDecodeError as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="json_syntax",
                status="fail",
                message=f"JSON syntax error: {e}",
                line_number=line_num
            ))
    
    def _validate_ticket_references(self, file_path: Path, content: str, lines: List[str]):
        """Validate ticket references against ai-trackdown system"""
        
        # Find ticket references
        ticket_patterns = [
            r'\b(EP-\d+)\b',  # Epic references
            r'\b(ISS-\d+)\b',  # Issue references
            r'\b(TSK-\d+)\b',  # Task references
            r'\b(MEM-\d+)\b',  # Memory integration tickets
            r'\b(FRW-\d+)\b',  # Framework tickets
            r'\b(FWK-\d+)\b',  # Framework tickets (alt)
        ]
        
        for pattern in ticket_patterns:
            matches = re.findall(pattern, content)
            for ticket_id in matches:
                line_num = self._find_line_number(lines, ticket_id)
                self._validate_ticket_exists(file_path, ticket_id, line_num)
    
    def _validate_ticket_exists(self, file_path: Path, ticket_id: str, line_num: int):
        """Check if ticket exists in ai-trackdown system"""
        if ticket_id in self.ticket_cache:
            if not self.ticket_cache[ticket_id]:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="ticket_reference",
                    status="fail",
                    message=f"Ticket reference not found: {ticket_id}",
                    line_number=line_num
                ))
            return
        
        try:
            # Check if ticket exists using ai-trackdown CLI
            result = subprocess.run(
                ['aitrackdown', 'show', ticket_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.ticket_cache[ticket_id] = True
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="ticket_reference",
                    status="pass",
                    message=f"Ticket reference valid: {ticket_id}",
                    line_number=line_num
                ))
            else:
                self.ticket_cache[ticket_id] = False
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    check_type="ticket_reference",
                    status="fail",
                    message=f"Ticket reference not found: {ticket_id}",
                    line_number=line_num
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="ticket_reference",
                status="warning",
                message=f"Cannot validate ticket {ticket_id}: {e}",
                line_number=line_num
            ))
    
    def _validate_file_references(self, file_path: Path, content: str, lines: List[str]):
        """Validate file path references in documentation"""
        
        # Find file path references
        file_patterns = [
            r'`([^`]+\.[a-z]+)`',  # Backtick file references
            r'`([^`]+/[^`]+)`',    # Backtick path references
            r'File:\s+([^\s]+)',   # File: prefix
            r'Path:\s+([^\s]+)',   # Path: prefix
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            for file_ref in matches:
                line_num = self._find_line_number(lines, file_ref)
                self._validate_file_reference(file_path, file_ref, line_num)
    
    def _validate_file_reference(self, file_path: Path, file_ref: str, line_num: int):
        """Validate a single file reference"""
        # Skip validation for certain patterns
        skip_patterns = [
            r'^https?://',  # URLs
            r'^\$',         # Environment variables
            r'^\~',         # Home directory references
            r'example',     # Example files
            r'<.*>',        # Template references
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, file_ref):
                return
        
        # Try to resolve the file path
        potential_paths = [
            Path(file_ref),  # Absolute path
            file_path.parent / file_ref,  # Relative to current file
            self.base_dir / file_ref,  # Relative to base directory
        ]
        
        found = False
        for path in potential_paths:
            try:
                if path.exists():
                    found = True
                    break
            except Exception:
                continue
        
        if found:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="file_reference",
                status="pass",
                message=f"File reference valid: {file_ref}",
                line_number=line_num
            ))
        else:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                check_type="file_reference",
                status="warning",
                message=f"File reference may be invalid: {file_ref}",
                line_number=line_num
            ))
    
    def _find_line_number(self, lines: List[str], search_text: str) -> int:
        """Find line number containing search text"""
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1
    
    def _generate_summary(self):
        """Generate validation summary"""
        total = len(self.results)
        passed = len([r for r in self.results if r.status == 'pass'])
        failed = len([r for r in self.results if r.status == 'fail'])
        warnings = len([r for r in self.results if r.status == 'warning'])
        
        print(f"\n📊 Validation Summary:")
        print(f"  Total checks: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warnings}")
        
        if failed > 0:
            print(f"\n❌ Failed checks:")
            for result in self.results:
                if result.status == 'fail':
                    location = f":{result.line_number}" if result.line_number else ""
                    print(f"  {Path(result.file_path).name}{location} - {result.message}")
    
    def generate_report(self, output_path: str = None):
        """Generate detailed validation report"""
        if not output_path:
            output_path = self.base_dir / "validation_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_directory": str(self.base_dir),
            "summary": {
                "total": len(self.results),
                "passed": len([r for r in self.results if r.status == 'pass']),
                "failed": len([r for r in self.results if r.status == 'fail']),
                "warnings": len([r for r in self.results if r.status == 'warning'])
            },
            "results": [
                {
                    "file": result.file_path,
                    "check_type": result.check_type,
                    "status": result.status,
                    "message": result.message,
                    "line_number": result.line_number,
                    "details": result.details
                }
                for result in self.results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to: {output_path}")
        return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Documentation Validator")
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to validate (default: current directory)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for detailed report (default: validation_report.json)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DocumentValidator(args.directory)
    
    # Run validation
    results = validator.validate_directory()
    
    # Generate report
    report_path = validator.generate_report(args.output)
    
    # Exit with appropriate code
    failed_count = len([r for r in results if r.status == 'fail'])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    main()