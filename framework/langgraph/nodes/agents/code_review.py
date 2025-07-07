"""
Code Review Agent Node - Priority 1 Implementation

Multi-dimensional code review agent that performs parallel analysis across
security, performance, style, and testing dimensions with memory integration.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseAgentNode, AgentExecutionContext, AgentNodeResult
from ..states.base import TaskState, CodeReviewState
from ...core.logging_config import get_logger

logger = get_logger(__name__)


class CodeReviewNode(BaseAgentNode):
    """
    Multi-dimensional code review agent node.
    
    Performs comprehensive code review across multiple dimensions:
    - Security: Vulnerability and compliance analysis
    - Performance: Algorithm and optimization analysis  
    - Style: Standards and readability analysis
    - Testing: Coverage and quality analysis
    
    Integrates with memory to apply learned patterns and team standards.
    """
    
    def __init__(self, 
                 agent_id: str = "code_review_agent",
                 memory_client=None,
                 config: Optional[Dict] = None):
        """
        Initialize Code Review agent node.
        
        Args:
            agent_id: Unique identifier for this agent instance
            memory_client: Optional mem0AI client for memory operations
            config: Optional configuration for review parameters
        """
        super().__init__(
            agent_id=agent_id,
            role="code_review_engineer", 
            memory_client=memory_client,
            config=config
        )
        
        # Review configuration
        self.review_config = {
            "parallel_execution": True,
            "security_enabled": True,
            "performance_enabled": True,
            "style_enabled": True,
            "testing_enabled": True,
            "min_confidence_threshold": 0.7,
            **self.config.get("code_review", {})
        }
    
    async def _execute_agent_logic(self, 
                                 context: AgentExecutionContext, 
                                 state: TaskState) -> AgentNodeResult:
        """
        Execute multi-dimensional code review logic.
        
        Args:
            context: Execution context with memory and configuration
            state: Current workflow state (should be CodeReviewState)
            
        Returns:
            AgentNodeResult with comprehensive review findings
        """
        logger.info(f"Starting multi-dimensional code review for {context.workflow_id}")
        
        # Validate state type and extract review parameters
        review_params = self._extract_review_parameters(state)
        
        # Load code review patterns from memory
        review_patterns = await self._load_review_patterns(context, review_params)
        
        # Execute parallel review across all dimensions
        if self.review_config["parallel_execution"]:
            review_results = await self._execute_parallel_review(
                context, review_params, review_patterns
            )
        else:
            review_results = await self._execute_sequential_review(
                context, review_params, review_patterns
            )
        
        # Aggregate and analyze results
        aggregated_results = self._aggregate_review_results(review_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(aggregated_results, review_patterns)
        
        # Calculate overall confidence and score
        overall_score, confidence = self._calculate_overall_assessment(aggregated_results)
        
        return AgentNodeResult(
            status="completed",
            agent_id=self.agent_id,
            role=self.role,
            content=self._format_review_summary(aggregated_results, recommendations),
            metadata={
                "review_results": aggregated_results,
                "recommendations": recommendations,
                "overall_score": overall_score,
                "review_parameters": review_params,
                "patterns_applied": len(review_patterns),
                "dimensions_analyzed": list(review_results.keys())
            },
            execution_time_ms=0,  # Will be set by base class
            confidence=confidence,
            citations=self._extract_citations(review_patterns),
            errors=[]
        )
    
    def _extract_review_parameters(self, state: TaskState) -> Dict[str, Any]:
        """Extract code review parameters from state."""
        # For TaskState, extract from context or metadata
        if isinstance(state, dict) and "target_files" in state:
            # This is actually a CodeReviewState
            return {
                "target_files": state.get("target_files", []),
                "git_ref": state.get("git_ref"),
                "change_summary": state.get("change_summary"),
                "review_types": state.get("review_types", ["security", "performance", "style", "testing"]),
                "parallel_execution": state.get("parallel_execution", True)
            }
        else:
            # Extract from task context
            context = state.get("context", {})
            return {
                "target_files": context.get("target_files", []),
                "git_ref": context.get("git_ref"),
                "change_summary": context.get("change_summary", state.get("task_description", "")),
                "review_types": context.get("review_types", ["security", "performance", "style", "testing"]),
                "parallel_execution": context.get("parallel_execution", True)
            }
    
    async def _load_review_patterns(self, 
                                  context: AgentExecutionContext,
                                  review_params: Dict[str, Any]) -> List[Dict]:
        """Load relevant code review patterns from memory."""
        patterns = []
        
        if not self.memory_client:
            return patterns
        
        try:
            # Load security patterns
            if "security" in review_params["review_types"]:
                security_patterns = await self._search_security_patterns(
                    review_params["target_files"]
                )
                patterns.extend(security_patterns)
            
            # Load performance patterns
            if "performance" in review_params["review_types"]:
                performance_patterns = await self._search_performance_patterns(
                    review_params["target_files"]
                )
                patterns.extend(performance_patterns)
            
            # Load style patterns
            if "style" in review_params["review_types"]:
                style_patterns = await self._search_style_patterns(
                    review_params["target_files"]
                )
                patterns.extend(style_patterns)
            
            # Load testing patterns
            if "testing" in review_params["review_types"]:
                testing_patterns = await self._search_testing_patterns(
                    review_params["target_files"]
                )
                patterns.extend(testing_patterns)
            
            logger.info(f"Loaded {len(patterns)} review patterns from memory")
            
        except Exception as e:
            logger.warning(f"Failed to load review patterns: {e}")
        
        return patterns
    
    async def _execute_parallel_review(self, 
                                     context: AgentExecutionContext,
                                     review_params: Dict[str, Any],
                                     patterns: List[Dict]) -> Dict[str, Any]:
        """Execute review dimensions in parallel."""
        review_tasks = []
        
        # Create review tasks for each enabled dimension
        if "security" in review_params["review_types"]:
            review_tasks.append(
                self._security_review(context, review_params, patterns)
            )
        
        if "performance" in review_params["review_types"]:
            review_tasks.append(
                self._performance_review(context, review_params, patterns)
            )
        
        if "style" in review_params["review_types"]:
            review_tasks.append(
                self._style_review(context, review_params, patterns)
            )
        
        if "testing" in review_params["review_types"]:
            review_tasks.append(
                self._testing_review(context, review_params, patterns)
            )
        
        # Execute all reviews in parallel
        results = await asyncio.gather(*review_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        review_results = {}
        for i, result in enumerate(results):
            review_type = review_params["review_types"][i]
            if isinstance(result, Exception):
                logger.error(f"{review_type} review failed: {result}")
                review_results[review_type] = {
                    "status": "failed",
                    "error": str(result),
                    "issues": [],
                    "score": 0.0
                }
            else:
                review_results[review_type] = result
        
        return review_results
    
    async def _execute_sequential_review(self, 
                                       context: AgentExecutionContext,
                                       review_params: Dict[str, Any],
                                       patterns: List[Dict]) -> Dict[str, Any]:
        """Execute review dimensions sequentially."""
        review_results = {}
        
        for review_type in review_params["review_types"]:
            try:
                if review_type == "security":
                    result = await self._security_review(context, review_params, patterns)
                elif review_type == "performance":
                    result = await self._performance_review(context, review_params, patterns)
                elif review_type == "style":
                    result = await self._style_review(context, review_params, patterns)
                elif review_type == "testing":
                    result = await self._testing_review(context, review_params, patterns)
                else:
                    logger.warning(f"Unknown review type: {review_type}")
                    continue
                
                review_results[review_type] = result
                
            except Exception as e:
                logger.error(f"{review_type} review failed: {e}")
                review_results[review_type] = {
                    "status": "failed",
                    "error": str(e),
                    "issues": [],
                    "score": 0.0
                }
        
        return review_results
    
    async def _security_review(self, 
                             context: AgentExecutionContext,
                             review_params: Dict[str, Any],
                             patterns: List[Dict]) -> Dict[str, Any]:
        """Perform security-focused code review."""
        # Placeholder implementation - replace with actual security analysis
        await asyncio.sleep(0.1)  # Simulate analysis time
        
        # Apply security patterns from memory
        security_patterns = [p for p in patterns if p.get("type") == "security"]
        
        return {
            "status": "completed",
            "dimension": "security",
            "issues": [
                {
                    "severity": "medium",
                    "type": "input_validation",
                    "description": "Potential SQL injection vulnerability detected",
                    "file": review_params["target_files"][0] if review_params["target_files"] else "unknown",
                    "line": 42,
                    "confidence": 0.8
                }
            ],
            "score": 0.75,
            "patterns_applied": len(security_patterns),
            "recommendations": [
                "Use parameterized queries to prevent SQL injection",
                "Implement input validation for all user inputs"
            ]
        }
    
    async def _performance_review(self, 
                                context: AgentExecutionContext,
                                review_params: Dict[str, Any],
                                patterns: List[Dict]) -> Dict[str, Any]:
        """Perform performance-focused code review."""
        # Placeholder implementation - replace with actual performance analysis
        await asyncio.sleep(0.1)  # Simulate analysis time
        
        # Apply performance patterns from memory
        performance_patterns = [p for p in patterns if p.get("type") == "performance"]
        
        return {
            "status": "completed",
            "dimension": "performance",
            "issues": [
                {
                    "severity": "low",
                    "type": "algorithm_complexity",
                    "description": "Nested loop with O(n²) complexity could be optimized",
                    "file": review_params["target_files"][0] if review_params["target_files"] else "unknown",
                    "line": 15,
                    "confidence": 0.9
                }
            ],
            "score": 0.85,
            "patterns_applied": len(performance_patterns),
            "recommendations": [
                "Consider using a hash map to reduce complexity to O(n)",
                "Profile code to identify actual bottlenecks"
            ]
        }
    
    async def _style_review(self, 
                          context: AgentExecutionContext,
                          review_params: Dict[str, Any],
                          patterns: List[Dict]) -> Dict[str, Any]:
        """Perform style-focused code review."""
        # Placeholder implementation - replace with actual style analysis
        await asyncio.sleep(0.1)  # Simulate analysis time
        
        # Apply style patterns from memory
        style_patterns = [p for p in patterns if p.get("type") == "style"]
        
        return {
            "status": "completed",
            "dimension": "style",
            "issues": [
                {
                    "severity": "low",
                    "type": "naming_convention",
                    "description": "Variable name should use camelCase",
                    "file": review_params["target_files"][0] if review_params["target_files"] else "unknown",
                    "line": 8,
                    "confidence": 0.95
                }
            ],
            "score": 0.90,
            "patterns_applied": len(style_patterns),
            "recommendations": [
                "Follow consistent naming conventions",
                "Add documentation for public methods"
            ]
        }
    
    async def _testing_review(self, 
                            context: AgentExecutionContext,
                            review_params: Dict[str, Any],
                            patterns: List[Dict]) -> Dict[str, Any]:
        """Perform testing-focused code review."""
        # Placeholder implementation - replace with actual testing analysis
        await asyncio.sleep(0.1)  # Simulate analysis time
        
        # Apply testing patterns from memory
        testing_patterns = [p for p in patterns if p.get("type") == "testing"]
        
        return {
            "status": "completed",
            "dimension": "testing",
            "issues": [
                {
                    "severity": "high",
                    "type": "test_coverage",
                    "description": "No unit tests found for new functionality",
                    "file": review_params["target_files"][0] if review_params["target_files"] else "unknown",
                    "line": 1,
                    "confidence": 1.0
                }
            ],
            "score": 0.60,
            "patterns_applied": len(testing_patterns),
            "recommendations": [
                "Add comprehensive unit tests",
                "Implement integration tests for API endpoints",
                "Achieve minimum 80% test coverage"
            ]
        }
    
    def _aggregate_review_results(self, review_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all review dimensions."""
        aggregated = {
            "dimensions_reviewed": list(review_results.keys()),
            "total_issues": 0,
            "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "average_score": 0.0,
            "dimension_scores": {},
            "all_issues": [],
            "failed_dimensions": []
        }
        
        total_score = 0.0
        valid_dimensions = 0
        
        for dimension, result in review_results.items():
            if result["status"] == "completed":
                # Aggregate scores
                score = result.get("score", 0.0)
                aggregated["dimension_scores"][dimension] = score
                total_score += score
                valid_dimensions += 1
                
                # Aggregate issues
                issues = result.get("issues", [])
                aggregated["total_issues"] += len(issues)
                aggregated["all_issues"].extend(issues)
                
                # Count issues by severity
                for issue in issues:
                    severity = issue.get("severity", "low")
                    if severity in aggregated["issues_by_severity"]:
                        aggregated["issues_by_severity"][severity] += 1
            else:
                aggregated["failed_dimensions"].append(dimension)
        
        # Calculate average score
        if valid_dimensions > 0:
            aggregated["average_score"] = total_score / valid_dimensions
        
        return aggregated
    
    def _generate_recommendations(self, 
                                 aggregated_results: Dict[str, Any],
                                 patterns: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on review results."""
        recommendations = []
        
        # Critical and high severity issues get priority recommendations
        critical_issues = [
            issue for issue in aggregated_results["all_issues"] 
            if issue.get("severity") in ["critical", "high"]
        ]
        
        for issue in critical_issues:
            recommendations.append({
                "priority": "high",
                "type": issue.get("type", "general"),
                "description": f"Address {issue.get('severity')} severity issue: {issue.get('description')}",
                "action": "fix_issue",
                "estimated_effort": "medium",
                "dimension": issue.get("dimension", "unknown")
            })
        
        # Add pattern-based recommendations
        pattern_recommendations = self._get_pattern_recommendations(patterns, aggregated_results)
        recommendations.extend(pattern_recommendations)
        
        # Add general improvement recommendations
        if aggregated_results["average_score"] < 0.8:
            recommendations.append({
                "priority": "medium",
                "type": "general_improvement",
                "description": "Overall code quality below target threshold",
                "action": "comprehensive_review",
                "estimated_effort": "high",
                "dimension": "overall"
            })
        
        return recommendations
    
    def _get_pattern_recommendations(self, 
                                   patterns: List[Dict],
                                   results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on memory patterns."""
        # Placeholder - implement pattern-based recommendation logic
        return []
    
    def _calculate_overall_assessment(self, aggregated_results: Dict[str, Any]) -> tuple[float, float]:
        """Calculate overall score and confidence for the review."""
        # Base score from dimension averages
        base_score = aggregated_results["average_score"]
        
        # Penalize for critical and high severity issues
        critical_penalty = aggregated_results["issues_by_severity"]["critical"] * 0.2
        high_penalty = aggregated_results["issues_by_severity"]["high"] * 0.1
        
        overall_score = max(0.0, base_score - critical_penalty - high_penalty)
        
        # Calculate confidence based on successful dimensions and issue confidence
        successful_dimensions = len(aggregated_results["dimension_scores"])
        total_dimensions = len(aggregated_results["dimensions_reviewed"])
        
        dimension_confidence = successful_dimensions / total_dimensions if total_dimensions > 0 else 0.0
        
        # Factor in issue detection confidence
        issue_confidences = [
            issue.get("confidence", 0.5) 
            for issue in aggregated_results["all_issues"]
        ]
        avg_issue_confidence = sum(issue_confidences) / len(issue_confidences) if issue_confidences else 0.8
        
        overall_confidence = (dimension_confidence + avg_issue_confidence) / 2
        
        return overall_score, overall_confidence
    
    def _format_review_summary(self, 
                              aggregated_results: Dict[str, Any],
                              recommendations: List[Dict[str, Any]]) -> str:
        """Format a human-readable review summary."""
        summary_lines = [
            f"Code Review Complete - Score: {aggregated_results['average_score']:.2f}/1.00",
            f"Total Issues Found: {aggregated_results['total_issues']}",
            f"Critical: {aggregated_results['issues_by_severity']['critical']}, "
            f"High: {aggregated_results['issues_by_severity']['high']}, "
            f"Medium: {aggregated_results['issues_by_severity']['medium']}, "
            f"Low: {aggregated_results['issues_by_severity']['low']}",
            "",
            "Dimension Scores:"
        ]
        
        for dimension, score in aggregated_results["dimension_scores"].items():
            summary_lines.append(f"  {dimension.title()}: {score:.2f}")
        
        if recommendations:
            summary_lines.extend([
                "",
                "Top Recommendations:",
            ])
            for i, rec in enumerate(recommendations[:3]):  # Top 3 recommendations
                summary_lines.append(f"  {i+1}. {rec['description']}")
        
        return "\n".join(summary_lines)
    
    def _extract_citations(self, patterns: List[Dict]) -> List[str]:
        """Extract citations from applied patterns."""
        citations = []
        for pattern in patterns:
            if "source" in pattern:
                citations.append(pattern["source"])
        return list(set(citations))  # Remove duplicates
    
    # Memory search methods (placeholders for mem0AI integration)
    async def _search_security_patterns(self, target_files: List[str]) -> List[Dict]:
        """Search for relevant security patterns."""
        # Placeholder - implement with mem0AI
        return []
    
    async def _search_performance_patterns(self, target_files: List[str]) -> List[Dict]:
        """Search for relevant performance patterns."""
        # Placeholder - implement with mem0AI
        return []
    
    async def _search_style_patterns(self, target_files: List[str]) -> List[Dict]:
        """Search for relevant style patterns."""
        # Placeholder - implement with mem0AI
        return []
    
    async def _search_testing_patterns(self, target_files: List[str]) -> List[Dict]:
        """Search for relevant testing patterns."""
        # Placeholder - implement with mem0AI
        return []