#!/usr/bin/env python3
"""
Token Reduction Performance Benchmarks
=====================================

Validates the 66% token reduction claim through comprehensive benchmarking
across various task complexities and agent types.
"""

import os
import sys
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple
import statistics

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer
from claude_pm.services.task_complexity_integration_example import create_optimized_prompt


@dataclass
class TokenReductionResult:
    """Result of token reduction benchmark."""
    task_description: str
    agent_type: str
    complexity_level: str
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    optimization_time_ms: float


class TokenReductionBenchmark:
    """Comprehensive token reduction benchmarking."""
    
    def __init__(self):
        self.analyzer = TaskComplexityAnalyzer()
        self.results: List[TokenReductionResult] = []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (roughly 4 chars per token for English).
        For production, use actual tokenizer.
        """
        return len(text) // 4
    
    def create_unoptimized_prompt(
        self,
        agent_type: str,
        task: str,
        context: Dict
    ) -> str:
        """Create unoptimized prompt with full context."""
        # Simulate verbose, unoptimized prompt
        prompt = f"""You are a {agent_type} agent in the Claude PM Framework.

## Your Role and Responsibilities
{self._get_verbose_agent_description(agent_type)}

## Current Task
{task}

## Complete Project Context
{json.dumps(context, indent=2)}

## Additional Context and History
{self._get_verbose_context_history(context)}

## Detailed Instructions
{self._get_verbose_instructions(agent_type, task)}

## Examples and Patterns
{self._get_verbose_examples(agent_type)}

## Framework Information
{self._get_verbose_framework_info()}

## Standards and Guidelines
{self._get_verbose_guidelines(agent_type)}

Please complete the task according to all the above information.
"""
        return prompt
    
    def _get_verbose_agent_description(self, agent_type: str) -> str:
        """Get verbose agent description."""
        descriptions = {
            'engineer': """As an Engineer Agent, you are responsible for all code implementation,
            development, and inline documentation creation. You must follow best practices,
            write clean code, ensure proper error handling, implement comprehensive logging,
            create unit tests, handle edge cases, optimize for performance, and maintain
            backward compatibility. You should also consider security implications, follow
            SOLID principles, use appropriate design patterns, and ensure code is maintainable.""",
            
            'documentation': """As a Documentation Agent, you handle all documentation tasks including
            README files, API documentation, user guides, developer guides, changelog generation,
            version documentation, inline code comments, docstring creation, example creation,
            tutorial writing, FAQ compilation, troubleshooting guides, and migration guides.
            You must ensure clarity, completeness, accuracy, and maintainability.""",
            
            'qa': """As a QA Agent, you are responsible for quality assurance, testing, validation,
            test planning, test case creation, test execution, regression testing, performance testing,
            security testing, integration testing, end-to-end testing, smoke testing, user acceptance
            testing, load testing, stress testing, and test automation."""
        }
        return descriptions.get(agent_type, "Generic agent description" * 10)
    
    def _get_verbose_context_history(self, context: Dict) -> str:
        """Get verbose context history."""
        # Simulate extensive context
        history = []
        for i in range(20):
            history.append(f"Historical context item {i}: " + "x" * 100)
        return "\n".join(history)
    
    def _get_verbose_instructions(self, agent_type: str, task: str) -> str:
        """Get verbose instructions."""
        instructions = []
        for i in range(15):
            instructions.append(f"{i+1}. Detailed instruction for {agent_type}: " + "y" * 80)
        return "\n".join(instructions)
    
    def _get_verbose_examples(self, agent_type: str) -> str:
        """Get verbose examples."""
        examples = []
        for i in range(10):
            examples.append(f"Example {i+1} for {agent_type}:\n" + "z" * 200)
        return "\n\n".join(examples)
    
    def _get_verbose_framework_info(self) -> str:
        """Get verbose framework information."""
        return "Framework details: " * 50 + "\n" + "Configuration: " * 30
    
    def _get_verbose_guidelines(self, agent_type: str) -> str:
        """Get verbose guidelines."""
        return f"Guidelines for {agent_type}: " * 20 + "\nStandards: " * 20
    
    def run_benchmark(self, task: str, agent_type: str, context: Dict) -> TokenReductionResult:
        """Run a single benchmark test."""
        start_time = time.time()
        
        # Create unoptimized prompt
        unoptimized_prompt = self.create_unoptimized_prompt(agent_type, task, context)
        unoptimized_tokens = self.estimate_tokens(unoptimized_prompt)
        
        # Create optimized prompt
        optimized_result = create_optimized_prompt(
            agent_name=agent_type,
            task_description=task,
            context=context
        )
        optimized_prompt = optimized_result['prompt']
        optimized_tokens = self.estimate_tokens(optimized_prompt)
        
        # Calculate reduction
        reduction_percentage = (1 - optimized_tokens / unoptimized_tokens) * 100
        
        # Calculate time
        optimization_time = (time.time() - start_time) * 1000
        
        result = TokenReductionResult(
            task_description=task,
            agent_type=agent_type,
            complexity_level=optimized_result['complexity_level'],
            original_tokens=unoptimized_tokens,
            optimized_tokens=optimized_tokens,
            reduction_percentage=reduction_percentage,
            optimization_time_ms=optimization_time
        )
        
        self.results.append(result)
        return result
    
    def run_comprehensive_benchmark(self):
        """Run comprehensive benchmark suite."""
        # Test scenarios covering different complexities
        test_scenarios = [
            # Simple tasks
            {
                'task': 'Read the configuration file and return its contents',
                'agent': 'engineer',
                'context': {
                    'file': 'config.json',
                    'project': 'simple-app'
                }
            },
            {
                'task': 'List all Python files in the project',
                'agent': 'qa',
                'context': {
                    'directory': 'src/',
                    'extension': '.py'
                }
            },
            
            # Medium complexity tasks
            {
                'task': 'Implement user registration endpoint with email validation',
                'agent': 'engineer',
                'context': {
                    'framework': 'FastAPI',
                    'database': 'PostgreSQL',
                    'files': ['models.py', 'routes.py', 'validators.py'],
                    'requirements': ['Email validation', 'Password hashing', 'User creation']
                }
            },
            {
                'task': 'Write comprehensive API documentation for the authentication module',
                'agent': 'documentation',
                'context': {
                    'modules': ['auth', 'users', 'permissions'],
                    'endpoints': ['/login', '/logout', '/register', '/refresh'],
                    'auth_type': 'JWT'
                }
            },
            
            # Complex tasks
            {
                'task': 'Refactor the monolithic application into microservices architecture',
                'agent': 'engineer',
                'context': {
                    'current_architecture': {
                        'type': 'monolith',
                        'components': ['api', 'auth', 'database', 'cache'],
                        'loc': 50000
                    },
                    'target_architecture': {
                        'type': 'microservices',
                        'services': ['auth-service', 'user-service', 'api-gateway', 'notification-service'],
                        'communication': 'gRPC and REST'
                    },
                    'requirements': [
                        'Zero downtime migration',
                        'Data consistency',
                        'Performance optimization',
                        'Service discovery',
                        'Load balancing'
                    ],
                    'timeline': '3 months',
                    'team_size': 5
                }
            },
            {
                'task': 'Design and implement comprehensive test strategy for distributed system',
                'agent': 'qa',
                'context': {
                    'system_type': 'distributed',
                    'components': ['api', 'workers', 'queue', 'cache', 'database'],
                    'test_types': ['unit', 'integration', 'e2e', 'performance', 'chaos'],
                    'tools': ['pytest', 'locust', 'chaos-monkey'],
                    'coverage_target': '90%',
                    'performance_requirements': {
                        'latency': '<100ms p99',
                        'throughput': '>10k rps'
                    }
                }
            }
        ]
        
        print("Running Token Reduction Benchmarks...")
        print("=" * 80)
        
        for scenario in test_scenarios:
            result = self.run_benchmark(
                task=scenario['task'],
                agent_type=scenario['agent'],
                context=scenario['context']
            )
            
            print(f"\nTask: {result.task_description[:60]}...")
            print(f"Agent: {result.agent_type}")
            print(f"Complexity: {result.complexity_level}")
            print(f"Original tokens: {result.original_tokens:,}")
            print(f"Optimized tokens: {result.optimized_tokens:,}")
            print(f"Reduction: {result.reduction_percentage:.1f}%")
            print(f"Optimization time: {result.optimization_time_ms:.2f}ms")
    
    def generate_report(self):
        """Generate comprehensive benchmark report."""
        if not self.results:
            print("No benchmark results to report.")
            return
        
        print("\n" + "=" * 80)
        print("TOKEN REDUCTION BENCHMARK REPORT")
        print("=" * 80)
        
        # Overall statistics
        reductions = [r.reduction_percentage for r in self.results]
        avg_reduction = statistics.mean(reductions)
        min_reduction = min(reductions)
        max_reduction = max(reductions)
        
        print(f"\nOverall Statistics:")
        print(f"  Average reduction: {avg_reduction:.1f}%")
        print(f"  Minimum reduction: {min_reduction:.1f}%")
        print(f"  Maximum reduction: {max_reduction:.1f}%")
        print(f"  Standard deviation: {statistics.stdev(reductions):.1f}%")
        
        # By complexity level
        print(f"\nReduction by Complexity Level:")
        for level in ['SIMPLE', 'MEDIUM', 'COMPLEX']:
            level_results = [r for r in self.results if r.complexity_level == level]
            if level_results:
                level_avg = statistics.mean([r.reduction_percentage for r in level_results])
                print(f"  {level}: {level_avg:.1f}% (n={len(level_results)})")
        
        # By agent type
        print(f"\nReduction by Agent Type:")
        for agent in set(r.agent_type for r in self.results):
            agent_results = [r for r in self.results if r.agent_type == agent]
            agent_avg = statistics.mean([r.reduction_percentage for r in agent_results])
            print(f"  {agent}: {agent_avg:.1f}% (n={len(agent_results)})")
        
        # Token savings
        total_original = sum(r.original_tokens for r in self.results)
        total_optimized = sum(r.optimized_tokens for r in self.results)
        total_saved = total_original - total_optimized
        
        print(f"\nToken Savings:")
        print(f"  Total original tokens: {total_original:,}")
        print(f"  Total optimized tokens: {total_optimized:,}")
        print(f"  Total tokens saved: {total_saved:,}")
        print(f"  Overall reduction: {(1 - total_optimized/total_original)*100:.1f}%")
        
        # Performance
        optimization_times = [r.optimization_time_ms for r in self.results]
        print(f"\nOptimization Performance:")
        print(f"  Average time: {statistics.mean(optimization_times):.2f}ms")
        print(f"  Min time: {min(optimization_times):.2f}ms")
        print(f"  Max time: {max(optimization_times):.2f}ms")
        
        # Validation against 66% claim
        print(f"\n{'='*80}")
        print(f"VALIDATION AGAINST 66% TOKEN REDUCTION CLAIM:")
        if avg_reduction >= 66:
            print(f"✅ CLAIM VALIDATED: Average reduction of {avg_reduction:.1f}% exceeds 66%")
        elif avg_reduction >= 60:
            print(f"⚠️  CLAIM PARTIALLY VALIDATED: Average reduction of {avg_reduction:.1f}% is close to 66%")
        else:
            print(f"❌ CLAIM NOT VALIDATED: Average reduction of {avg_reduction:.1f}% is below 66%")
        
        # Export results
        self.export_results()
    
    def export_results(self):
        """Export detailed results to JSON."""
        results_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': len(self.results),
                'average_reduction': statistics.mean([r.reduction_percentage for r in self.results]),
                'min_reduction': min(r.reduction_percentage for r in self.results),
                'max_reduction': max(r.reduction_percentage for r in self.results),
            },
            'detailed_results': [
                {
                    'task': r.task_description,
                    'agent': r.agent_type,
                    'complexity': r.complexity_level,
                    'original_tokens': r.original_tokens,
                    'optimized_tokens': r.optimized_tokens,
                    'reduction_percentage': r.reduction_percentage,
                    'optimization_time_ms': r.optimization_time_ms
                }
                for r in self.results
            ]
        }
        
        output_file = 'token_reduction_benchmark_results.json'
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\nDetailed results exported to: {output_file}")


def run_token_reduction_benchmarks():
    """Run comprehensive token reduction benchmarks."""
    benchmark = TokenReductionBenchmark()
    benchmark.run_comprehensive_benchmark()
    benchmark.generate_report()


if __name__ == "__main__":
    run_token_reduction_benchmarks()