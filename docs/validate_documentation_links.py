#!/usr/bin/env python3
"""
Documentation Link Validation Script
Validates all internal links in the Claude PM Framework documentation
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentationValidator:
    def __init__(self, docs_root: str):
        self.docs_root = Path(docs_root)
        self.framework_root = self.docs_root.parent
        self.errors = []
        self.warnings = []
        
    def validate_all_documentation(self) -> Dict[str, any]:
        """Validate all documentation links and structure"""
        print("🔍 Validating Claude PM Framework Documentation...")
        print(f"Documentation root: {self.docs_root}")
        print(f"Framework root: {self.framework_root}")
        
        # Validate main documentation files
        main_docs = [
            "INDEX.md",
            "FRAMEWORK_OVERVIEW.md", 
            "QUICK_START.md",
            "FIRST_DELEGATION.md"
        ]
        
        results = {
            "files_validated": 0,
            "links_checked": 0,
            "errors": [],
            "warnings": [],
            "missing_files": [],
            "broken_links": []
        }
        
        for doc_file in main_docs:
            file_path = self.docs_root / doc_file
            if file_path.exists():
                print(f"✅ Validating {doc_file}...")
                file_results = self.validate_file(file_path)
                results["files_validated"] += 1
                results["links_checked"] += file_results["links_checked"]
                results["errors"].extend(file_results["errors"])
                results["warnings"].extend(file_results["warnings"])
                results["broken_links"].extend(file_results["broken_links"])
            else:
                results["missing_files"].append(doc_file)
                print(f"❌ Missing file: {doc_file}")
        
        # Validate README.md integration
        readme_path = self.framework_root / "README.md"
        if readme_path.exists():
            print("✅ Validating README.md integration...")
            readme_results = self.validate_file(readme_path)
            results["files_validated"] += 1
            results["links_checked"] += readme_results["links_checked"]
            results["errors"].extend(readme_results["errors"])
            results["warnings"].extend(readme_results["warnings"])
            results["broken_links"].extend(readme_results["broken_links"])
        
        # Validate critical referenced files exist
        critical_files = [
            "trackdown/BACKLOG.md",
            "trackdown/CURRENT-STATUS.md", 
            "docs/TICKETING_SYSTEM.md",
            "docs/CLAUDE_PM_MEMORY_INTEGRATION.md",
            "docs/MEMORY_SETUP_GUIDE.md",
            "framework/agent-roles/",
            "config/memory_config.py"
        ]
        
        for critical_file in critical_files:
            file_path = self.framework_root / critical_file
            if not file_path.exists():
                results["missing_files"].append(critical_file)
                print(f"⚠️ Critical file missing: {critical_file}")
        
        return results
    
    def validate_file(self, file_path: Path) -> Dict[str, any]:
        """Validate links in a specific markdown file"""
        results = {
            "links_checked": 0,
            "errors": [],
            "warnings": [], 
            "broken_links": []
        }
        
        try:
            content = file_path.read_text()
            
            # Find all markdown links [text](path)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            links = re.findall(link_pattern, content)
            
            for link_text, link_path in links:
                results["links_checked"] += 1
                
                # Skip external links (http/https)
                if link_path.startswith(('http://', 'https://')):
                    continue
                    
                # Skip anchors within same document
                if link_path.startswith('#'):
                    continue
                
                # Check if linked file exists
                if link_path.startswith('../'):
                    # Relative to docs directory
                    target_path = self.docs_root / link_path[3:]
                elif link_path.startswith('./'):
                    # Relative to current file
                    target_path = file_path.parent / link_path[2:]
                else:
                    # Relative to current file
                    target_path = file_path.parent / link_path
                
                # Resolve relative paths
                try:
                    target_path = target_path.resolve()
                except:
                    results["broken_links"].append({
                        "file": str(file_path),
                        "link_text": link_text,
                        "link_path": link_path,
                        "error": "Invalid path format"
                    })
                    continue
                
                if not target_path.exists():
                    results["broken_links"].append({
                        "file": str(file_path),
                        "link_text": link_text, 
                        "link_path": link_path,
                        "resolved_path": str(target_path),
                        "error": "File does not exist"
                    })
            
            # Check for specific content requirements
            self.validate_content_requirements(file_path, content, results)
            
        except Exception as e:
            results["errors"].append({
                "file": str(file_path),
                "error": f"Failed to read file: {str(e)}"
            })
        
        return results
    
    def validate_content_requirements(self, file_path: Path, content: str, results: Dict):
        """Validate specific content requirements for documentation files"""
        file_name = file_path.name
        
        if file_name == "INDEX.md":
            # INDEX.md should have specific sections
            required_sections = [
                "Quick Start Guide",
                "User Journey Navigation", 
                "Agent Ecosystem",
                "Memory Integration",
                "Command Reference"
            ]
            
            for section in required_sections:
                if section not in content:
                    results["warnings"].append({
                        "file": str(file_path),
                        "warning": f"Missing required section: {section}"
                    })
        
        elif file_name == "FRAMEWORK_OVERVIEW.md":
            # Framework overview should cover key topics
            required_topics = [
                "11-Agent Ecosystem",
                "Memory Integration",
                "LangGraph",
                "Zero-Configuration"
            ]
            
            for topic in required_topics:
                if topic.lower() not in content.lower():
                    results["warnings"].append({
                        "file": str(file_path),
                        "warning": f"Missing key topic: {topic}"
                    })
        
        elif file_name == "QUICK_START.md":
            # Quick start should have practical examples
            if "```python" not in content:
                results["warnings"].append({
                    "file": str(file_path),
                    "warning": "Missing Python code examples"
                })
            
            if "```bash" not in content:
                results["warnings"].append({
                    "file": str(file_path), 
                    "warning": "Missing bash command examples"
                })
    
    def print_validation_report(self, results: Dict):
        """Print comprehensive validation report"""
        print("\n" + "="*60)
        print("📋 DOCUMENTATION VALIDATION REPORT")
        print("="*60)
        
        print(f"📁 Files validated: {results['files_validated']}")
        print(f"🔗 Links checked: {results['links_checked']}")
        print(f"❌ Errors found: {len(results['errors'])}")
        print(f"⚠️ Warnings: {len(results['warnings'])}")
        print(f"🔗 Broken links: {len(results['broken_links'])}")
        print(f"📄 Missing files: {len(results['missing_files'])}")
        
        # Report missing files
        if results['missing_files']:
            print(f"\n📄 Missing Files ({len(results['missing_files'])}):")
            for missing_file in results['missing_files']:
                print(f"  ❌ {missing_file}")
        
        # Report broken links
        if results['broken_links']:
            print(f"\n🔗 Broken Links ({len(results['broken_links'])}):")
            for broken_link in results['broken_links']:
                print(f"  ❌ {broken_link['file']}")
                print(f"     Link: [{broken_link['link_text']}]({broken_link['link_path']})")
                print(f"     Error: {broken_link['error']}")
                if 'resolved_path' in broken_link:
                    print(f"     Target: {broken_link['resolved_path']}")
                print()
        
        # Report errors
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  ❌ {error['file']}: {error['error']}")
        
        # Report warnings
        if results['warnings']:
            print(f"\n⚠️ Warnings ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  ⚠️ {warning['file']}: {warning['warning']}")
        
        # Summary
        print(f"\n{'='*60}")
        if not results['errors'] and not results['broken_links']:
            print("✅ VALIDATION PASSED: Documentation structure is healthy!")
        else:
            print("❌ VALIDATION ISSUES: Please fix errors and broken links above")
        
        if results['warnings']:
            print("⚠️ OPTIMIZATION OPPORTUNITIES: Consider addressing warnings for better documentation")
        
        print("="*60)
        
        return len(results['errors']) == 0 and len(results['broken_links']) == 0

def main():
    """Main validation function"""
    # Determine documentation root
    script_dir = Path(__file__).parent
    docs_root = script_dir
    
    print("🚀 Claude PM Framework Documentation Validator")
    print(f"Framework: v4.0.0 (Pure Task Delegation: mem0AI + Task Tools)")
    print(f"Validation Date: {os.popen('date').read().strip()}")
    
    # Create validator and run validation
    validator = DocumentationValidator(str(docs_root))
    results = validator.validate_all_documentation()
    
    # Print report and determine exit code
    success = validator.print_validation_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()