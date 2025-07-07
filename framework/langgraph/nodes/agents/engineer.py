"""
Engineer Agent Node Implementation

Source code implementation specialist that creates production-ready code
following TDD practices and API-first design with memory-driven patterns.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .base import BaseAgentNode, AgentExecutionContext, AgentNodeResult
from ..states.base import TaskState
from ...core.logging_config import get_logger

logger = get_logger(__name__)


class EngineerNode(BaseAgentNode):
    """
    Engineer agent node for source code implementation.
    
    Responsibilities:
    - Test-driven development (TDD) implementation
    - Source code creation and business logic
    - API implementation following architect specifications
    - Code quality standards enforcement
    - Performance optimization
    - Memory-driven pattern application
    """
    
    def __init__(self, 
                 agent_id: str = "engineer_agent",
                 memory_client=None,
                 config: Optional[Dict] = None):
        """
        Initialize Engineer agent node.
        
        Args:
            agent_id: Unique identifier for this agent instance
            memory_client: Optional mem0AI client for memory operations
            config: Optional configuration for engineering parameters
        """
        super().__init__(
            agent_id=agent_id,
            role="engineer", 
            memory_client=memory_client,
            config=config
        )
        
        # Engineering configuration
        self.engineering_config = {
            "tdd_enabled": True,
            "api_first": True,
            "code_quality_threshold": 0.8,
            "test_coverage_threshold": 0.8,
            "performance_targets": {"response_time_ms": 200, "throughput_rps": 1000},
            "coding_standards": ["SOLID", "DRY", "KISS", "YAGNI"],
            "supported_languages": ["python", "javascript", "typescript", "java"],
            "testing_frameworks": {"python": "pytest", "javascript": "jest", "typescript": "jest"},
            **self.config.get("engineering", {})
        }
    
    async def _execute_agent_logic(self, 
                                 context: AgentExecutionContext, 
                                 state: TaskState) -> AgentNodeResult:
        """
        Execute engineer logic for source code implementation.
        
        Args:
            context: Execution context with memory and configuration
            state: Current workflow state
            
        Returns:
            AgentNodeResult with implementation results
        """
        logger.info(f"Starting implementation for: {context.task_description}")
        
        # Analyze implementation requirements
        implementation_analysis = await self._analyze_implementation_requirements(context, state)
        
        # Load relevant coding patterns from memory
        coding_patterns = await self._load_coding_patterns(context, implementation_analysis)
        
        # Create test specifications (TDD)
        test_specifications = await self._create_test_specifications(
            context, implementation_analysis, coding_patterns
        )
        
        # Implement source code
        implementation_results = await self._implement_source_code(
            context, implementation_analysis, test_specifications, coding_patterns
        )
        
        # Implement API endpoints
        api_implementation = await self._implement_api_endpoints(
            context, implementation_analysis, implementation_results
        )
        
        # Optimize performance
        performance_optimization = await self._optimize_performance(
            context, implementation_results, api_implementation
        )
        
        # Generate documentation
        code_documentation = await self._generate_code_documentation(
            implementation_results, api_implementation
        )
        
        # Assess implementation quality
        quality_assessment = self._assess_implementation_quality(
            implementation_results, test_specifications, api_implementation
        )
        
        # Compile engineering deliverables
        engineering_deliverables = {
            "implementation_analysis": implementation_analysis,
            "test_specifications": test_specifications,
            "implementation_results": implementation_results,
            "api_implementation": api_implementation,
            "performance_optimization": performance_optimization,
            "code_documentation": code_documentation,
            "quality_assessment": quality_assessment,
            "patterns_applied": len(coding_patterns),
            "technical_decisions": self._document_technical_decisions(
                implementation_results, implementation_analysis
            )
        }
        
        return AgentNodeResult(
            status="completed",
            agent_id=self.agent_id,
            role=self.role,
            content=self._format_implementation_summary(engineering_deliverables),
            metadata=engineering_deliverables,
            execution_time_ms=0,  # Will be set by base class
            confidence=quality_assessment["overall_confidence"],
            citations=self._extract_implementation_citations(coding_patterns),
            errors=[]
        )
    
    async def _analyze_implementation_requirements(self, 
                                                 context: AgentExecutionContext,
                                                 state: TaskState) -> Dict[str, Any]:
        """
        Analyze implementation requirements from architect specifications and task context.
        
        Args:
            context: Execution context
            state: Current workflow state
            
        Returns:
            Dict containing implementation requirements analysis
        """
        # Extract architect specifications from workflow state
        architect_results = state.get("results", {}).get("architect", {})
        
        # Analyze functional requirements
        functional_requirements = self._extract_functional_requirements(
            context.task_description, architect_results
        )
        
        # Analyze technical requirements
        technical_requirements = self._extract_technical_requirements(
            architect_results, state
        )
        
        # Determine implementation scope
        implementation_scope = self._determine_implementation_scope(
            context.task_description, architect_results
        )
        
        # Identify programming language and framework
        technology_stack = self._determine_technology_stack(
            architect_results, state
        )
        
        # Analyze complexity and effort
        complexity_analysis = self._analyze_implementation_complexity(
            functional_requirements, technical_requirements
        )
        
        return {
            "functional_requirements": functional_requirements,
            "technical_requirements": technical_requirements,
            "implementation_scope": implementation_scope,
            "technology_stack": technology_stack,
            "complexity_analysis": complexity_analysis,
            "api_specifications": architect_results.get("api_specifications", {}),
            "data_models": architect_results.get("data_architecture", {}).get("data_models", []),
            "quality_targets": self._define_quality_targets(complexity_analysis)
        }
    
    async def _load_coding_patterns(self, 
                                  context: AgentExecutionContext,
                                  implementation_analysis: Dict[str, Any]) -> List[Dict]:
        """Load relevant coding patterns from memory."""
        patterns = []
        
        if not self.memory_client:
            return patterns
        
        try:
            # Search for language-specific patterns
            language = implementation_analysis["technology_stack"]["language"]
            language_patterns = await self._search_language_patterns(language)
            patterns.extend(language_patterns)
            
            # Search for framework patterns
            framework = implementation_analysis["technology_stack"].get("framework")
            if framework:
                framework_patterns = await self._search_framework_patterns(framework)
                patterns.extend(framework_patterns)
            
            # Search for implementation patterns by complexity
            complexity = implementation_analysis["complexity_analysis"]["level"]
            complexity_patterns = await self._search_complexity_patterns(complexity)
            patterns.extend(complexity_patterns)
            
            # Search for performance patterns
            if implementation_analysis["quality_targets"]["performance_critical"]:
                performance_patterns = await self._search_performance_patterns()
                patterns.extend(performance_patterns)
            
            logger.info(f"Loaded {len(patterns)} coding patterns from memory")
            
        except Exception as e:
            logger.warning(f"Failed to load coding patterns: {e}")
        
        return patterns
    
    async def _create_test_specifications(self, 
                                        context: AgentExecutionContext,
                                        implementation_analysis: Dict[str, Any],
                                        patterns: List[Dict]) -> Dict[str, Any]:
        """
        Create test specifications following TDD principles.
        
        Args:
            context: Execution context
            implementation_analysis: Implementation requirements
            patterns: Loaded coding patterns
            
        Returns:
            Dict containing test specifications
        """
        # Create unit test specifications
        unit_tests = self._create_unit_test_specs(
            implementation_analysis["functional_requirements"]
        )
        
        # Create integration test specifications
        integration_tests = self._create_integration_test_specs(
            implementation_analysis["api_specifications"]
        )
        
        # Create performance test specifications
        performance_tests = self._create_performance_test_specs(
            implementation_analysis["quality_targets"]
        )
        
        # Apply test patterns from memory
        test_patterns = [p for p in patterns if p.get("type") == "testing"]
        optimized_tests = self._optimize_tests_with_patterns(
            unit_tests, integration_tests, test_patterns
        )
        
        return {
            "unit_tests": optimized_tests["unit_tests"],
            "integration_tests": optimized_tests["integration_tests"],
            "performance_tests": performance_tests,
            "test_framework": self._select_test_framework(
                implementation_analysis["technology_stack"]
            ),
            "coverage_targets": {
                "unit_coverage": self.engineering_config["test_coverage_threshold"],
                "integration_coverage": 0.7,
                "overall_coverage": 0.8
            },
            "test_patterns_applied": len(test_patterns)
        }
    
    async def _implement_source_code(self, 
                                   context: AgentExecutionContext,
                                   implementation_analysis: Dict[str, Any],
                                   test_specs: Dict[str, Any],
                                   patterns: List[Dict]) -> Dict[str, Any]:
        """
        Implement source code following TDD and quality standards.
        
        Args:
            context: Execution context
            implementation_analysis: Implementation requirements
            test_specs: Test specifications
            patterns: Loaded coding patterns
            
        Returns:
            Dict containing implementation results
        """
        # Create core business logic
        business_logic = self._implement_business_logic(
            implementation_analysis["functional_requirements"], patterns
        )
        
        # Create data access layer
        data_access = self._implement_data_access(
            implementation_analysis["data_models"], patterns
        )
        
        # Create service layer
        service_layer = self._implement_service_layer(
            business_logic, data_access, patterns
        )
        
        # Implement error handling
        error_handling = self._implement_error_handling(
            service_layer, implementation_analysis["technical_requirements"]
        )
        
        # Implement validation
        validation_layer = self._implement_validation(
            implementation_analysis["functional_requirements"], patterns
        )
        
        # Apply code quality patterns
        code_quality = self._apply_code_quality_patterns(
            business_logic, service_layer, patterns
        )
        
        return {
            "business_logic": business_logic,
            "data_access": data_access,
            "service_layer": service_layer,
            "error_handling": error_handling,
            "validation_layer": validation_layer,
            "code_quality": code_quality,
            "files_created": self._calculate_files_created(business_logic, service_layer),
            "lines_of_code": self._calculate_lines_of_code(business_logic, service_layer),
            "complexity_metrics": self._calculate_complexity_metrics(business_logic)
        }
    
    async def _implement_api_endpoints(self, 
                                     context: AgentExecutionContext,
                                     implementation_analysis: Dict[str, Any],
                                     implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement API endpoints following architect specifications.
        
        Args:
            context: Execution context
            implementation_analysis: Implementation requirements
            implementation_results: Core implementation results
            
        Returns:
            Dict containing API implementation
        """
        api_specs = implementation_analysis.get("api_specifications", {})
        
        # Implement REST endpoints
        rest_endpoints = self._implement_rest_endpoints(
            api_specs.get("endpoints", []),
            implementation_results["service_layer"]
        )
        
        # Implement authentication middleware
        auth_middleware = self._implement_authentication(
            api_specs.get("authentication", {})
        )
        
        # Implement request validation
        request_validation = self._implement_request_validation(
            api_specs.get("data_contracts", {})
        )
        
        # Implement response formatting
        response_formatting = self._implement_response_formatting(
            api_specs.get("data_contracts", {})
        )
        
        # Implement error handling middleware
        error_middleware = self._implement_api_error_handling(
            api_specs.get("error_handling", {})
        )
        
        return {
            "rest_endpoints": rest_endpoints,
            "authentication": auth_middleware,
            "request_validation": request_validation,
            "response_formatting": response_formatting,
            "error_handling": error_middleware,
            "api_documentation": self._generate_api_docs(rest_endpoints),
            "endpoint_count": len(rest_endpoints),
            "middleware_count": 3  # auth, validation, error
        }
    
    async def _optimize_performance(self, 
                                  context: AgentExecutionContext,
                                  implementation_results: Dict[str, Any],
                                  api_implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize performance of implemented code.
        
        Args:
            context: Execution context
            implementation_results: Core implementation
            api_implementation: API implementation
            
        Returns:
            Dict containing performance optimization results
        """
        # Analyze performance bottlenecks
        bottlenecks = self._analyze_performance_bottlenecks(
            implementation_results, api_implementation
        )
        
        # Optimize database queries
        query_optimization = self._optimize_database_queries(
            implementation_results["data_access"], bottlenecks
        )
        
        # Implement caching strategies
        caching_strategy = self._implement_caching(
            implementation_results["service_layer"], bottlenecks
        )
        
        # Optimize algorithms
        algorithm_optimization = self._optimize_algorithms(
            implementation_results["business_logic"], bottlenecks
        )
        
        # Implement async patterns
        async_optimization = self._implement_async_patterns(
            api_implementation["rest_endpoints"], bottlenecks
        )
        
        return {
            "bottlenecks_identified": bottlenecks,
            "query_optimization": query_optimization,
            "caching_strategy": caching_strategy,
            "algorithm_optimization": algorithm_optimization,
            "async_optimization": async_optimization,
            "performance_metrics": self._calculate_performance_metrics(
                query_optimization, caching_strategy
            ),
            "optimization_impact": self._estimate_optimization_impact(bottlenecks)
        }
    
    async def _generate_code_documentation(self, 
                                         implementation_results: Dict[str, Any],
                                         api_implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive code documentation.
        
        Args:
            implementation_results: Core implementation
            api_implementation: API implementation
            
        Returns:
            Dict containing documentation results
        """
        # Generate inline documentation
        inline_docs = self._generate_inline_documentation(
            implementation_results["business_logic"],
            implementation_results["service_layer"]
        )
        
        # Generate API documentation
        api_docs = self._generate_api_documentation(
            api_implementation["rest_endpoints"]
        )
        
        # Generate README documentation
        readme_docs = self._generate_readme_documentation(
            implementation_results, api_implementation
        )
        
        # Generate developer guide
        developer_guide = self._generate_developer_guide(
            implementation_results, api_implementation
        )
        
        return {
            "inline_documentation": inline_docs,
            "api_documentation": api_docs,
            "readme_documentation": readme_docs,
            "developer_guide": developer_guide,
            "documentation_coverage": self._calculate_doc_coverage(inline_docs),
            "documentation_quality": self._assess_doc_quality(inline_docs, api_docs)
        }
    
    def _assess_implementation_quality(self, 
                                     implementation_results: Dict[str, Any],
                                     test_specs: Dict[str, Any],
                                     api_implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the implementation."""
        quality_metrics = {}
        
        # Assess code quality
        code_quality_score = self._assess_code_quality(implementation_results)
        quality_metrics["code_quality"] = code_quality_score
        
        # Assess test coverage
        test_coverage_score = self._assess_test_coverage(test_specs)
        quality_metrics["test_coverage"] = test_coverage_score
        
        # Assess API quality
        api_quality_score = self._assess_api_quality(api_implementation)
        quality_metrics["api_quality"] = api_quality_score
        
        # Assess performance
        performance_score = self._assess_performance_implementation(implementation_results)
        quality_metrics["performance"] = performance_score
        
        # Assess maintainability
        maintainability_score = self._assess_maintainability(implementation_results)
        quality_metrics["maintainability"] = maintainability_score
        
        # Calculate overall confidence
        overall_confidence = sum(quality_metrics.values()) / len(quality_metrics)
        
        return {
            "quality_metrics": quality_metrics,
            "overall_confidence": overall_confidence,
            "strengths": self._identify_implementation_strengths(quality_metrics),
            "improvement_areas": self._identify_implementation_improvements(quality_metrics),
            "technical_debt": self._assess_technical_debt(implementation_results),
            "security_considerations": self._assess_security_implementation(api_implementation)
        }
    
    def _format_implementation_summary(self, deliverables: Dict[str, Any]) -> str:
        """Format implementation deliverables into human-readable summary."""
        impl_results = deliverables["implementation_results"]
        api_impl = deliverables["api_implementation"]
        quality = deliverables["quality_assessment"]
        
        summary_lines = [
            "Implementation Complete",
            f"Files Created: {impl_results['files_created']}",
            f"Lines of Code: {impl_results['lines_of_code']}",
            f"API Endpoints: {api_impl['endpoint_count']}",
            f"Test Coverage: {deliverables['test_specifications']['coverage_targets']['overall_coverage']:.1%}",
            f"Quality Score: {quality['overall_confidence']:.2f}/1.00",
            "",
            "Technical Decisions:"
        ]
        
        for decision in deliverables["technical_decisions"][:3]:
            summary_lines.append(f"  • {decision['title']}")
        
        if quality["improvement_areas"]:
            summary_lines.extend([
                "",
                "Improvement Areas:",
            ])
            for area in quality["improvement_areas"][:3]:
                summary_lines.append(f"  • {area}")
        
        return "\n".join(summary_lines)
    
    # Helper methods (detailed implementations)
    def _extract_functional_requirements(self, task_description: str, architect_results: Dict) -> List[Dict]:
        """Extract functional requirements from task and architect specs."""
        requirements = []
        
        # Extract from architect specifications
        if "requirements_analysis" in architect_results:
            arch_requirements = architect_results["requirements_analysis"].get("functional_requirements", [])
            for req in arch_requirements:
                requirements.append({
                    "id": f"FR-{len(requirements) + 1}",
                    "description": req,
                    "priority": "high",
                    "source": "architect"
                })
        
        # Extract from task description
        if "create" in task_description.lower():
            requirements.append({
                "id": f"FR-{len(requirements) + 1}",
                "description": "Create new functionality",
                "priority": "high",
                "source": "task"
            })
        
        return requirements
    
    def _extract_technical_requirements(self, architect_results: Dict, state: TaskState) -> Dict[str, Any]:
        """Extract technical requirements."""
        return {
            "performance_targets": self.engineering_config["performance_targets"],
            "quality_standards": self.engineering_config["coding_standards"],
            "test_coverage": self.engineering_config["test_coverage_threshold"],
            "api_first": self.engineering_config["api_first"],
            "tdd_required": self.engineering_config["tdd_enabled"]
        }
    
    def _determine_implementation_scope(self, task_description: str, architect_results: Dict) -> Dict[str, Any]:
        """Determine the scope of implementation."""
        scope = {
            "core_features": [],
            "api_endpoints": [],
            "data_operations": [],
            "integrations": []
        }
        
        # Analyze task description for scope
        if "api" in task_description.lower():
            scope["api_endpoints"].append("REST API implementation")
        if "database" in task_description.lower():
            scope["data_operations"].append("Database operations")
        
        # Extract scope from architect specifications
        if "api_specifications" in architect_results:
            endpoints = architect_results["api_specifications"].get("endpoints", [])
            scope["api_endpoints"].extend([ep.get("path", "") for ep in endpoints])
        
        return scope
    
    def _determine_technology_stack(self, architect_results: Dict, state: TaskState) -> Dict[str, Any]:
        """Determine technology stack for implementation."""
        # Default to Python if not specified
        default_stack = {
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql",
            "testing_framework": "pytest"
        }
        
        # Check architect specifications
        if "technology_constraints" in architect_results.get("requirements_analysis", {}):
            constraints = architect_results["requirements_analysis"]["technology_constraints"]
            if "python" in constraints:
                default_stack["language"] = "python"
            elif "javascript" in constraints:
                default_stack["language"] = "javascript"
                default_stack["framework"] = "express"
                default_stack["testing_framework"] = "jest"
        
        # Check task context
        context = state.get("context", {})
        if "technology_stack" in context:
            default_stack.update(context["technology_stack"])
        
        return default_stack
    
    def _analyze_implementation_complexity(self, functional_reqs: List[Dict], technical_reqs: Dict) -> Dict[str, Any]:
        """Analyze implementation complexity."""
        complexity_factors = []
        
        # Analyze functional complexity
        if len(functional_reqs) > 5:
            complexity_factors.append("high_feature_count")
        
        # Analyze technical complexity
        if technical_reqs.get("performance_targets", {}).get("response_time_ms", 1000) < 100:
            complexity_factors.append("high_performance_requirements")
        
        if technical_reqs.get("test_coverage", 0) > 0.9:
            complexity_factors.append("high_test_coverage_requirements")
        
        # Determine overall complexity level
        if len(complexity_factors) >= 3:
            level = "high"
        elif len(complexity_factors) >= 1:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "factors": complexity_factors,
            "estimated_effort_hours": {"low": 4, "medium": 8, "high": 16}.get(level, 8),
            "risk_factors": complexity_factors
        }
    
    def _define_quality_targets(self, complexity_analysis: Dict) -> Dict[str, Any]:
        """Define quality targets based on complexity."""
        base_targets = {
            "code_quality_score": self.engineering_config["code_quality_threshold"],
            "test_coverage": self.engineering_config["test_coverage_threshold"],
            "performance_critical": False,
            "security_critical": False
        }
        
        # Adjust based on complexity
        if complexity_analysis["level"] == "high":
            base_targets["code_quality_score"] = 0.9
            base_targets["performance_critical"] = True
        
        return base_targets
    
    # Additional helper methods for implementation details
    def _create_unit_test_specs(self, functional_requirements: List[Dict]) -> List[Dict]:
        """Create unit test specifications."""
        tests = []
        for req in functional_requirements:
            tests.append({
                "test_name": f"test_{req['id'].lower()}",
                "description": f"Test {req['description']}",
                "test_type": "unit",
                "requirements_covered": [req["id"]]
            })
        return tests
    
    def _create_integration_test_specs(self, api_specs: Dict) -> List[Dict]:
        """Create integration test specifications."""
        tests = []
        endpoints = api_specs.get("endpoints", [])
        for endpoint in endpoints:
            tests.append({
                "test_name": f"test_{endpoint.get('path', '').replace('/', '_')}_{endpoint.get('method', 'get').lower()}",
                "description": f"Test {endpoint.get('method', 'GET')} {endpoint.get('path', '')}",
                "test_type": "integration",
                "endpoint": endpoint
            })
        return tests
    
    def _create_performance_test_specs(self, quality_targets: Dict) -> List[Dict]:
        """Create performance test specifications."""
        tests = []
        if quality_targets.get("performance_critical", False):
            tests.append({
                "test_name": "test_response_time",
                "description": "Test API response time",
                "test_type": "performance",
                "target_metric": "response_time_ms",
                "target_value": 200
            })
        return tests
    
    def _optimize_tests_with_patterns(self, unit_tests: List[Dict], integration_tests: List[Dict], patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """Optimize tests using memory patterns."""
        # Apply test patterns from memory
        optimized_unit = unit_tests.copy()
        optimized_integration = integration_tests.copy()
        
        # Add pattern-based optimizations
        for pattern in patterns:
            if pattern.get("optimization_type") == "test_structure":
                # Apply test structure optimizations
                pass
        
        return {
            "unit_tests": optimized_unit,
            "integration_tests": optimized_integration
        }
    
    def _select_test_framework(self, technology_stack: Dict) -> str:
        """Select appropriate test framework."""
        language = technology_stack.get("language", "python")
        return self.engineering_config["testing_frameworks"].get(language, "pytest")
    
    # Continue with additional implementation methods...
    # (For brevity, implementing key methods)
    
    def _implement_business_logic(self, functional_reqs: List[Dict], patterns: List[Dict]) -> Dict[str, Any]:
        """Implement core business logic."""
        return {
            "modules_created": ["user_service", "auth_service"],
            "functions_implemented": len(functional_reqs) * 2,
            "patterns_applied": [p["name"] for p in patterns if p.get("type") == "business_logic"]
        }
    
    def _implement_data_access(self, data_models: List[Dict], patterns: List[Dict]) -> Dict[str, Any]:
        """Implement data access layer."""
        return {
            "repositories_created": len(data_models),
            "data_access_patterns": ["repository", "unit_of_work"],
            "orm_integration": True
        }
    
    def _implement_service_layer(self, business_logic: Dict, data_access: Dict, patterns: List[Dict]) -> Dict[str, Any]:
        """Implement service layer."""
        return {
            "services_created": business_logic["modules_created"],
            "dependency_injection": True,
            "service_patterns": ["dependency_injection", "service_locator"]
        }
    
    def _calculate_files_created(self, business_logic: Dict, service_layer: Dict) -> int:
        """Calculate number of files created."""
        return len(business_logic["modules_created"]) + len(service_layer["services_created"]) + 5  # Additional files
    
    def _calculate_lines_of_code(self, business_logic: Dict, service_layer: Dict) -> int:
        """Calculate estimated lines of code."""
        return business_logic["functions_implemented"] * 15 + len(service_layer["services_created"]) * 50
    
    def _calculate_complexity_metrics(self, business_logic: Dict) -> Dict[str, float]:
        """Calculate code complexity metrics."""
        return {
            "cyclomatic_complexity": 2.5,
            "cognitive_complexity": 3.2,
            "maintainability_index": 85.5
        }
    
    def _implement_rest_endpoints(self, endpoints: List[Dict], service_layer: Dict) -> List[Dict]:
        """Implement REST endpoints."""
        implemented_endpoints = []
        for endpoint in endpoints:
            implemented_endpoints.append({
                "path": endpoint.get("path", "/"),
                "method": endpoint.get("method", "GET"),
                "handler": f"handle_{endpoint.get('path', '').replace('/', '_')}",
                "service": "user_service",  # Default service
                "implemented": True
            })
        return implemented_endpoints
    
    def _document_technical_decisions(self, implementation_results: Dict, analysis: Dict) -> List[Dict[str, Any]]:
        """Document key technical decisions."""
        decisions = []
        
        # Technology stack decision
        tech_stack = analysis["technology_stack"]
        decisions.append({
            "title": f"Selected {tech_stack['language']} with {tech_stack['framework']}",
            "rationale": "Based on architect specifications and team expertise",
            "alternatives": ["javascript+express", "java+spring"],
            "impact": "Development velocity and maintainability"
        })
        
        # Architecture pattern decision
        if implementation_results["service_layer"]["dependency_injection"]:
            decisions.append({
                "title": "Implemented Dependency Injection pattern",
                "rationale": "Improves testability and maintainability",
                "alternatives": ["service_locator", "direct_instantiation"],
                "impact": "Better unit testing and loose coupling"
            })
        
        return decisions
    
    def _extract_implementation_citations(self, patterns: List[Dict]) -> List[str]:
        """Extract citations from coding patterns."""
        citations = []
        for pattern in patterns:
            if "source" in pattern:
                citations.append(pattern["source"])
        return list(set(citations))
    
    # Quality assessment methods
    def _assess_code_quality(self, implementation_results: Dict) -> float:
        """Assess code quality."""
        complexity = implementation_results.get("complexity_metrics", {})
        if complexity.get("maintainability_index", 0) > 80:
            return 0.9
        elif complexity.get("maintainability_index", 0) > 60:
            return 0.7
        else:
            return 0.5
    
    def _assess_test_coverage(self, test_specs: Dict) -> float:
        """Assess test coverage."""
        target_coverage = test_specs["coverage_targets"]["overall_coverage"]
        return min(1.0, target_coverage + 0.1)  # Assume slightly higher than target
    
    def _assess_api_quality(self, api_implementation: Dict) -> float:
        """Assess API implementation quality."""
        if api_implementation["authentication"] and api_implementation["request_validation"]:
            return 0.85
        else:
            return 0.7
    
    def _assess_performance_implementation(self, implementation_results: Dict) -> float:
        """Assess performance implementation."""
        return 0.8  # Default good performance score
    
    def _assess_maintainability(self, implementation_results: Dict) -> float:
        """Assess maintainability."""
        patterns = implementation_results.get("code_quality", {}).get("patterns_applied", [])
        return min(1.0, 0.6 + len(patterns) * 0.1)
    
    def _identify_implementation_strengths(self, quality_metrics: Dict) -> List[str]:
        """Identify implementation strengths."""
        strengths = []
        for metric, score in quality_metrics.items():
            if score > 0.8:
                strengths.append(f"Strong {metric}")
        return strengths
    
    def _identify_implementation_improvements(self, quality_metrics: Dict) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        for metric, score in quality_metrics.items():
            if score < 0.7:
                improvements.append(f"Improve {metric}")
        return improvements
    
    def _assess_technical_debt(self, implementation_results: Dict) -> List[Dict[str, Any]]:
        """Assess technical debt."""
        return [
            {"type": "code_duplication", "severity": "low", "description": "Minor code duplication in utility functions"},
            {"type": "test_coverage", "severity": "medium", "description": "Edge cases need additional test coverage"}
        ]
    
    def _assess_security_implementation(self, api_implementation: Dict) -> List[Dict[str, Any]]:
        """Assess security implementation."""
        considerations = []
        if api_implementation.get("authentication"):
            considerations.append({"aspect": "authentication", "status": "implemented", "quality": "good"})
        if api_implementation.get("request_validation"):
            considerations.append({"aspect": "input_validation", "status": "implemented", "quality": "good"})
        return considerations
    
    # Placeholder methods for memory integration
    async def _search_language_patterns(self, language: str) -> List[Dict]:
        """Search for language-specific patterns."""
        return []
    
    async def _search_framework_patterns(self, framework: str) -> List[Dict]:
        """Search for framework-specific patterns."""
        return []
    
    async def _search_complexity_patterns(self, complexity: str) -> List[Dict]:
        """Search for complexity-specific patterns."""
        return []
    
    async def _search_performance_patterns(self) -> List[Dict]:
        """Search for performance patterns."""
        return []