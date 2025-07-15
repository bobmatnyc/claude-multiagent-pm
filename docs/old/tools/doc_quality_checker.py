#!/usr/bin/env python3
"""
Documentation Quality Checker

Automated quality assurance for documentation including spell checking,
grammar validation, readability analysis, and content completeness.

Features:
- Spell checking with technical dictionary support
- Grammar validation using basic heuristics
- Readability score analysis
- Structure consistency checking
- Content completeness validation
- Technical writing best practices

Usage:
    python doc_quality_checker.py [directory]
    python doc_quality_checker.py --help
"""

import os
import re
import sys
import json
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import argparse
from collections import Counter


@dataclass
class QualityIssue:
    """Represents a quality issue in documentation"""
    file_path: str
    issue_type: str
    severity: str  # 'low', 'medium', 'high'
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    context: Optional[str] = None


@dataclass
class QualityMetrics:
    """Quality metrics for a document"""
    file_path: str
    word_count: int
    sentence_count: int
    paragraph_count: int
    readability_score: float
    avg_sentence_length: float
    avg_paragraph_length: float
    heading_count: int
    code_block_count: int
    link_count: int
    image_count: int


@dataclass
class QualityReport:
    """Complete quality assessment report"""
    timestamp: str
    base_directory: str
    total_files: int
    issues: List[QualityIssue]
    metrics: List[QualityMetrics]
    summary: Dict[str, int]
    recommendations: List[str]


class DocumentQualityChecker:
    """Comprehensive documentation quality checker"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.issues: List[QualityIssue] = []
        self.metrics: List[QualityMetrics] = []
        self.technical_dict = self._load_technical_dictionary()
        self.style_rules = self._load_style_rules()
        
    def _load_technical_dictionary(self) -> Set[str]:
        """Load technical terms dictionary"""
        technical_terms = {
            # Programming terms
            'aitrackdown', 'atd', 'mem0', 'claude', 'langgraph', 'api', 'cli',
            'json', 'yaml', 'markdown', 'regex', 'subprocess', 'async', 'await',
            'github', 'git', 'npm', 'node', 'python', 'javascript', 'bash',
            'typescript', 'html', 'css', 'sql', 'docker', 'kubernetes',
            
            # Framework terms
            'multiagent', 'orchestrator', 'workflow', 'deployment', 'config',
            'endpoint', 'authentication', 'authorization', 'middleware', 'schema',
            'validation', 'serialization', 'deserialization', 'webhook', 'callback',
            
            # Business terms
            'backlog', 'sprint', 'epic', 'scrum', 'agile', 'kanban', 'roadmap',
            'stakeholder', 'milestone', 'deliverable', 'requirement', 'specification',
            
            # Technical acronyms
            'ai', 'ml', 'nlp', 'api', 'rest', 'crud', 'ui', 'ux', 'qa', 'ci', 'cd',
            'http', 'https', 'ssl', 'tls', 'ssh', 'ftp', 'dns', 'url', 'uri',
            'uuid', 'jwt', 'oauth', 'saml', 'ldap', 'rbac', 'cors', 'csrf'
        }
        
        return technical_terms
    
    def _load_style_rules(self) -> Dict[str, Dict]:
        """Load style rules for technical writing"""
        return {
            "sentence_length": {
                "max_words": 25,
                "ideal_words": 20
            },
            "paragraph_length": {
                "max_sentences": 8,
                "ideal_sentences": 4
            },
            "readability": {
                "min_score": 40,
                "target_score": 60
            },
            "heading_structure": {
                "max_depth": 6,
                "require_h1": True
            },
            "common_issues": {
                "passive_voice": r'\b(is|are|was|were|being|been)\s+\w+ed\b',
                "redundant_phrases": [
                    r'\bin order to\b',
                    r'\bdue to the fact that\b',
                    r'\bfor the purpose of\b',
                    r'\bin spite of the fact that\b'
                ],
                "weak_words": [
                    r'\bvery\b',
                    r'\breally\b',
                    r'\bquite\b',
                    r'\bsomewhat\b',
                    r'\brather\b'
                ]
            }
        }
    
    def check_quality(self) -> QualityReport:
        """Run comprehensive quality check"""
        print(f"🔍 Starting quality check of {self.base_dir}")
        
        # Find all markdown files
        md_files = list(self.base_dir.rglob("*.md"))
        print(f"📄 Analyzing {len(md_files)} markdown files")
        
        # Analyze each file
        for md_file in md_files:
            self._analyze_file(md_file)
        
        # Generate overall recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            base_directory=str(self.base_dir),
            total_files=len(md_files),
            issues=self.issues,
            metrics=self.metrics,
            summary=self._generate_summary(),
            recommendations=recommendations
        )
        
        self._print_summary(report)
        return report
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single markdown file"""
        print(f"  📋 Analyzing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="file_access",
                severity="high",
                description=f"Cannot read file: {e}"
            ))
            return
        
        # Run quality checks
        self._check_spelling(file_path, content, lines)
        self._check_grammar(file_path, content, lines)
        self._check_readability(file_path, content, lines)
        self._check_structure(file_path, content, lines)
        self._check_consistency(file_path, content, lines)
        self._check_completeness(file_path, content, lines)
        
        # Generate metrics
        metrics = self._calculate_metrics(file_path, content, lines)
        self.metrics.append(metrics)
    
    def _check_spelling(self, file_path: Path, content: str, lines: List[str]):
        """Check for spelling errors"""
        # Simple spelling check using word patterns
        word_pattern = r'\b[a-zA-Z]+\b'
        words = re.findall(word_pattern, content.lower())
        
        # Check for common misspellings
        common_misspellings = {
            'seperate': 'separate',
            'recieve': 'receive',
            'definately': 'definitely',
            'occured': 'occurred',
            'neccessary': 'necessary',
            'existance': 'existence',
            'independant': 'independent',
            'refference': 'reference',
            'begining': 'beginning',
            'accross': 'across'
        }
        
        for word in words:
            if word in common_misspellings:
                line_num = self._find_line_number(lines, word)
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="spelling",
                    severity="medium",
                    description=f"Possible misspelling: '{word}'",
                    line_number=line_num,
                    suggestion=f"Consider: '{common_misspellings[word]}'"
                ))
        
        # Check for repeated words
        word_pairs = zip(words, words[1:])
        for i, (word1, word2) in enumerate(word_pairs):
            if word1 == word2 and len(word1) > 3:
                line_num = self._find_line_number(lines, f"{word1} {word2}")
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="repeated_words",
                    severity="low",
                    description=f"Repeated word: '{word1}'",
                    line_number=line_num,
                    suggestion="Check if repetition is intentional"
                ))
    
    def _check_grammar(self, file_path: Path, content: str, lines: List[str]):
        """Basic grammar and style checking"""
        
        # Check for passive voice
        passive_pattern = self.style_rules["common_issues"]["passive_voice"]
        passive_matches = re.finditer(passive_pattern, content)
        for match in passive_matches:
            line_num = self._find_line_number(lines, match.group())
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="passive_voice",
                severity="low",
                description=f"Passive voice detected: '{match.group()}'",
                line_number=line_num,
                suggestion="Consider using active voice"
            ))
        
        # Check for redundant phrases
        for phrase_pattern in self.style_rules["common_issues"]["redundant_phrases"]:
            matches = re.finditer(phrase_pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = self._find_line_number(lines, match.group())
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="redundant_phrase",
                    severity="low",
                    description=f"Redundant phrase: '{match.group()}'",
                    line_number=line_num,
                    suggestion="Consider more concise wording"
                ))
        
        # Check for weak words
        for weak_pattern in self.style_rules["common_issues"]["weak_words"]:
            matches = re.finditer(weak_pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = self._find_line_number(lines, match.group())
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="weak_word",
                    severity="low",
                    description=f"Weak word: '{match.group()}'",
                    line_number=line_num,
                    suggestion="Consider stronger, more specific language"
                ))
    
    def _check_readability(self, file_path: Path, content: str, lines: List[str]):
        """Check readability using Flesch Reading Ease"""
        
        # Calculate basic readability metrics
        sentences = self._count_sentences(content)
        words = len(re.findall(r'\b\w+\b', content))
        syllables = self._count_syllables(content)
        
        if sentences == 0 or words == 0:
            return
        
        # Flesch Reading Ease score
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        flesch_score = (206.835 
                       - (1.015 * avg_sentence_length) 
                       - (84.6 * avg_syllables_per_word))
        
        # Check against target score
        target_score = self.style_rules["readability"]["target_score"]
        min_score = self.style_rules["readability"]["min_score"]
        
        if flesch_score < min_score:
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="readability",
                severity="medium",
                description=f"Low readability score: {flesch_score:.1f}",
                suggestion=f"Target score: {target_score}. Consider shorter sentences and simpler words"
            ))
        
        # Check sentence length
        max_words = self.style_rules["sentence_length"]["max_words"]
        sentences_text = re.split(r'[.!?]+', content)
        for i, sentence in enumerate(sentences_text):
            word_count = len(re.findall(r'\b\w+\b', sentence))
            if word_count > max_words:
                line_num = self._find_line_number(lines, sentence[:50])
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="long_sentence",
                    severity="low",
                    description=f"Long sentence: {word_count} words",
                    line_number=line_num,
                    suggestion=f"Consider breaking into shorter sentences (max {max_words} words)"
                ))
    
    def _check_structure(self, file_path: Path, content: str, lines: List[str]):
        """Check document structure"""
        
        # Check heading structure
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        if not headings:
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="structure",
                severity="medium",
                description="No headings found",
                suggestion="Add headings to improve document structure"
            ))
            return
        
        # Check for H1 title
        if self.style_rules["heading_structure"]["require_h1"]:
            has_h1 = any(len(heading[0]) == 1 for heading in headings)
            if not has_h1:
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="missing_h1",
                    severity="medium",
                    description="No H1 title found",
                    suggestion="Add a main title (# Title)"
                ))
        
        # Check heading hierarchy
        prev_level = 0
        for i, (heading_marks, heading_text) in enumerate(headings):
            level = len(heading_marks)
            if level > prev_level + 1:
                line_num = self._find_line_number(lines, heading_marks + " " + heading_text)
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="heading_hierarchy",
                    severity="low",
                    description=f"Heading level jump from H{prev_level} to H{level}",
                    line_number=line_num,
                    suggestion="Use sequential heading levels"
                ))
            prev_level = level
        
        # Check for empty sections
        sections = re.split(r'\n#{1,6}\s+', content)
        for i, section in enumerate(sections[1:], 1):
            if len(section.strip()) < 100:  # Arbitrary threshold
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="empty_section",
                    severity="low",
                    description=f"Very short section #{i}",
                    suggestion="Add more content or remove empty section"
                ))
    
    def _check_consistency(self, file_path: Path, content: str, lines: List[str]):
        """Check for consistency issues"""
        
        # Check for consistent terminology
        tech_terms = {
            'ai-trackdown': ['aitrackdown', 'ai_trackdown'],
            'mem0': ['mem0ai', 'mem0-ai'],
            'claude': ['Claude', 'claude'],
            'api': ['API', 'api']
        }
        
        for canonical, variants in tech_terms.items():
            for variant in variants:
                if variant in content and canonical in content:
                    line_num = self._find_line_number(lines, variant)
                    self.issues.append(QualityIssue(
                        file_path=str(file_path),
                        issue_type="inconsistent_terminology",
                        severity="low",
                        description=f"Inconsistent terminology: '{variant}' vs '{canonical}'",
                        line_number=line_num,
                        suggestion=f"Use consistent term: '{canonical}'"
                    ))
        
        # Check for consistent code formatting
        inline_code_pattern = r'`[^`]+`'
        code_blocks = re.findall(inline_code_pattern, content)
        
        # Check for unbalanced backticks
        backtick_count = content.count('`')
        if backtick_count % 2 != 0:
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="unbalanced_backticks",
                severity="medium",
                description="Unbalanced backticks detected",
                suggestion="Check for missing opening or closing backticks"
            ))
    
    def _check_completeness(self, file_path: Path, content: str, lines: List[str]):
        """Check for content completeness"""
        
        # Check for TODO/FIXME comments
        todo_pattern = r'(?i)(TODO|FIXME|XXX|HACK):\s*(.+)'
        todos = re.finditer(todo_pattern, content)
        for match in todos:
            line_num = self._find_line_number(lines, match.group())
            self.issues.append(QualityIssue(
                file_path=str(file_path),
                issue_type="incomplete_content",
                severity="medium",
                description=f"Incomplete content marker: {match.group()}",
                line_number=line_num,
                suggestion="Complete or remove TODO/FIXME comments"
            ))
        
        # Check for placeholder content
        placeholder_patterns = [
            r'Lorem ipsum',
            r'placeholder',
            r'TBD',
            r'To be determined',
            r'\[Insert .+\]'
        ]
        
        for pattern in placeholder_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = self._find_line_number(lines, match.group())
                self.issues.append(QualityIssue(
                    file_path=str(file_path),
                    issue_type="placeholder_content",
                    severity="high",
                    description=f"Placeholder content: {match.group()}",
                    line_number=line_num,
                    suggestion="Replace with actual content"
                ))
        
        # Check for broken internal references
        ref_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        refs = re.findall(ref_pattern, content)
        for ref_text, ref_url in refs:
            if ref_url.startswith('#'):
                # Check if anchor exists
                anchor_id = ref_url[1:]
                if not self._anchor_exists(content, anchor_id):
                    line_num = self._find_line_number(lines, f"[{ref_text}]({ref_url})")
                    self.issues.append(QualityIssue(
                        file_path=str(file_path),
                        issue_type="broken_reference",
                        severity="medium",
                        description=f"Broken internal reference: {ref_url}",
                        line_number=line_num,
                        suggestion="Fix or remove broken reference"
                    ))
    
    def _calculate_metrics(self, file_path: Path, content: str, lines: List[str]) -> QualityMetrics:
        """Calculate quality metrics for a document"""
        
        # Basic counts
        words = len(re.findall(r'\b\w+\b', content))
        sentences = self._count_sentences(content)
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        headings = len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        images = len(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content))
        
        # Calculate averages
        avg_sentence_length = words / sentences if sentences > 0 else 0
        avg_paragraph_length = sentences / paragraphs if paragraphs > 0 else 0
        
        # Calculate readability score
        syllables = self._count_syllables(content)
        if sentences > 0 and words > 0:
            flesch_score = (206.835 
                           - (1.015 * avg_sentence_length) 
                           - (84.6 * (syllables / words)))
        else:
            flesch_score = 0
        
        return QualityMetrics(
            file_path=str(file_path),
            word_count=words,
            sentence_count=sentences,
            paragraph_count=paragraphs,
            readability_score=flesch_score,
            avg_sentence_length=avg_sentence_length,
            avg_paragraph_length=avg_paragraph_length,
            heading_count=headings,
            code_block_count=code_blocks,
            link_count=links,
            image_count=images
        )
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count"""
        words = re.findall(r'\b\w+\b', text.lower())
        syllable_count = 0
        
        for word in words:
            # Simple syllable estimation
            vowels = 'aeiouy'
            syllables = 0
            prev_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not prev_was_vowel:
                        syllables += 1
                    prev_was_vowel = True
                else:
                    prev_was_vowel = False
            
            # Handle silent e
            if word.endswith('e') and syllables > 1:
                syllables -= 1
            
            # Minimum of 1 syllable per word
            syllables = max(1, syllables)
            syllable_count += syllables
        
        return syllable_count
    
    def _find_line_number(self, lines: List[str], search_text: str) -> int:
        """Find line number containing search text"""
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1
    
    def _anchor_exists(self, content: str, anchor_id: str) -> bool:
        """Check if anchor exists in content"""
        # Convert anchor to possible heading formats
        heading_text = anchor_id.replace('-', ' ').replace('_', ' ')
        patterns = [
            f"#{{{1,6}}}\\s+.*?{re.escape(heading_text)}",
            f"#{{{1,6}}}\\s+.*?{re.escape(anchor_id)}"
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _generate_recommendations(self) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Count issue types
        issue_counts = Counter(issue.issue_type for issue in self.issues)
        
        # Generate recommendations based on common issues
        if issue_counts.get('spelling', 0) > 5:
            recommendations.append("Consider using spell-check tools or automated validation")
        
        if issue_counts.get('readability', 0) > 0:
            recommendations.append("Focus on improving readability with shorter sentences and simpler language")
        
        if issue_counts.get('structure', 0) > 0:
            recommendations.append("Improve document structure with clear headings and logical flow")
        
        if issue_counts.get('incomplete_content', 0) > 0:
            recommendations.append("Complete all TODO/FIXME items before publishing")
        
        if issue_counts.get('placeholder_content', 0) > 0:
            recommendations.append("Replace all placeholder content with actual information")
        
        if issue_counts.get('passive_voice', 0) > 10:
            recommendations.append("Reduce passive voice usage for clearer, more direct communication")
        
        # Calculate average readability
        if self.metrics:
            avg_readability = sum(m.readability_score for m in self.metrics) / len(self.metrics)
            if avg_readability < 50:
                recommendations.append("Overall documentation readability is low - consider simplifying language")
        
        return recommendations
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generate summary statistics"""
        summary = {
            "total_issues": len(self.issues),
            "high_severity": len([i for i in self.issues if i.severity == "high"]),
            "medium_severity": len([i for i in self.issues if i.severity == "medium"]),
            "low_severity": len([i for i in self.issues if i.severity == "low"])
        }
        
        # Add issue type counts
        issue_counts = Counter(issue.issue_type for issue in self.issues)
        for issue_type, count in issue_counts.items():
            summary[f"{issue_type}_count"] = count
        
        # Add average metrics
        if self.metrics:
            summary["avg_readability"] = sum(m.readability_score for m in self.metrics) / len(self.metrics)
            summary["avg_word_count"] = sum(m.word_count for m in self.metrics) / len(self.metrics)
            summary["avg_sentence_length"] = sum(m.avg_sentence_length for m in self.metrics) / len(self.metrics)
        
        return summary
    
    def _print_summary(self, report: QualityReport):
        """Print quality check summary"""
        print(f"\n📊 Quality Check Summary:")
        print(f"  Total files analyzed: {report.total_files}")
        print(f"  Total issues found: {report.summary['total_issues']}")
        print(f"  🔴 High severity: {report.summary['high_severity']}")
        print(f"  🟡 Medium severity: {report.summary['medium_severity']}")
        print(f"  🟢 Low severity: {report.summary['low_severity']}")
        
        if report.summary.get('avg_readability'):
            print(f"  📖 Average readability: {report.summary['avg_readability']:.1f}")
        
        if report.summary['total_issues'] > 0:
            print(f"\n🔍 Common Issues:")
            issue_types = Counter(issue.issue_type for issue in report.issues)
            for issue_type, count in issue_types.most_common(5):
                print(f"  {issue_type}: {count}")
        
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
    
    def save_report(self, report: QualityReport, output_path: str = None):
        """Save quality report to file"""
        if not output_path:
            output_path = self.base_dir / "quality_report.json"
        
        # Convert dataclasses to dict for JSON serialization
        report_dict = {
            "timestamp": report.timestamp,
            "base_directory": report.base_directory,
            "total_files": report.total_files,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "issues": [asdict(issue) for issue in report.issues],
            "metrics": [asdict(metric) for metric in report.metrics]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"📄 Quality report saved to: {output_path}")
        return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Documentation Quality Checker")
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to check (default: current directory)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for quality report'
    )
    parser.add_argument(
        '--min-readability',
        type=float,
        default=40,
        help='Minimum readability score (default: 40)'
    )
    parser.add_argument(
        '--max-sentence-length',
        type=int,
        default=25,
        help='Maximum sentence length in words (default: 25)'
    )
    
    args = parser.parse_args()
    
    # Initialize checker
    checker = DocumentQualityChecker(args.directory)
    
    # Override settings if specified
    if args.min_readability:
        checker.style_rules["readability"]["min_score"] = args.min_readability
    if args.max_sentence_length:
        checker.style_rules["sentence_length"]["max_words"] = args.max_sentence_length
    
    # Run quality check
    report = checker.check_quality()
    
    # Save report
    checker.save_report(report, args.output)
    
    # Exit with appropriate code
    high_count = report.summary.get('high_severity', 0)
    medium_count = report.summary.get('medium_severity', 0)
    
    if high_count > 0:
        sys.exit(1)  # High severity issues
    elif medium_count > 10:  # Allow some medium issues
        sys.exit(1)  # Too many medium issues
    else:
        sys.exit(0)  # Success


if __name__ == '__main__':
    main()