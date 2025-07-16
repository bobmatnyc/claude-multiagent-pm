#!/usr/bin/env python3
"""
Codebase Research Agent for Claude PM Framework v0.9.0
======================================================

This is the FIRST PLACE TO GO when planning work on the Claude PM Framework codebase.
This agent has maximum-size embedded knowledge about the entire framework architecture,
services, patterns, and business logic.

Agent: codebase-research-agent
Type: research
Tier: project
Specializations: ['codebase', 'architecture', 'business_logic', 'framework', 'claude_pm_framework']
Created: 2025-07-15

This specialized Research Agent provides:
- Complete framework architecture knowledge
- Business logic and operational workflows
- Service relationships and integration patterns
- Implementation guidance and best practices
- Performance optimization recommendations
- Agent hierarchy and orchestration patterns
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    from claude_pm.core.base_service import BaseService
    from claude_pm.core.config import Config
    from claude_pm.core.logging_config import setup_logging
except ImportError:
    # Fallback for project-specific agent
    import sys
    import os
    from dataclasses import dataclass
    from abc import ABC, abstractmethod

    class BaseService(ABC):
        def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
            self.name = name
            self.config = config or {}
            self._running = False
            self._start_time = None
            self.logger = self._setup_logger()
        
        def _setup_logger(self):
            import logging
            logger = logging.getLogger(self.name)
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            return logger
        
        @property
        def running(self) -> bool:
            return self._running
        
        @property
        def uptime(self) -> float:
            if self._start_time:
                return (datetime.now() - self._start_time).total_seconds()
            return 0.0


class CodebaseResearchAgent(BaseService):
    """
    Specialized Research Agent for Claude PM Framework Codebase
    
    This agent contains maximum-size embedded knowledge about the Claude PM Framework
    and serves as the authoritative source for codebase questions, architecture analysis,
    and implementation guidance.
    
    Key Responsibilities:
    - Answer codebase-specific questions with detailed context
    - Provide architectural analysis and guidance
    - Explain business logic and operational workflows
    - Guide implementation decisions and patterns
    - Research framework patterns and optimizations
    - Serve as first reference for framework planning
    """
    
    # EMBEDDED KNOWLEDGE: MAXIMUM-SIZE FRAMEWORK KNOWLEDGE
    FRAMEWORK_KNOWLEDGE = {
        "version": "0.9.0",
        "architecture": {
            "core_philosophy": """
            Claude PM Framework is a multi-agent orchestration system designed for project management
            through AI agent delegation. The framework follows a two-tier agent hierarchy:
            
            1. System Agents (Code-Based): Foundational functionality in claude_pm/agents/
            2. User Agents (Filesystem-Based): Customizable agents with directory precedence
            
            Key principles:
            - PM Agent never performs direct work - always delegates via Task Tool
            - Agents have specialized responsibilities and authority domains
            - Hierarchical precedence for agent discovery and loading
            - Performance-optimized with shared prompt caching
            - Comprehensive operational tracking and reporting
            """,
            
            "agent_hierarchy": {
                "precedence_order": [
                    "Current Directory: $PWD/.claude-pm/agents/ (highest)",
                    "Parent Directories: Walk up tree checking .claude-pm/agents/",
                    "User Directory: ~/.claude-pm/agents/",
                    "System Directory: claude_pm/agents/ (lowest, always available)"
                ],
                "core_agent_types": {
                    "pm_agent": "Multi-agent orchestrator - delegates all work via Task Tool",
                    "documentation_agent": "Documentation operations and changelog generation",
                    "ticketing_agent": "Universal ticketing interface and lifecycle management",
                    "version_control_agent": "Git operations and version management",
                    "qa_agent": "Quality assurance, testing, and validation",
                    "research_agent": "Investigation, analysis, and information gathering",
                    "ops_agent": "Deployment, operations, and infrastructure management",
                    "security_agent": "Security analysis and vulnerability assessment",
                    "engineer_agent": "Code implementation and development",
                    "data_engineer_agent": "Data store management and AI API integrations"
                },
                "delegation_patterns": {
                    "init": "Ops Agent (framework initialization)",
                    "setup": "Ops Agent (directory structure, agent hierarchy)",
                    "push": "Multi-agent (Documentation → QA → Version Control)",
                    "deploy": "Ops → QA coordination",
                    "publish": "Documentation → Ops coordination",
                    "test": "QA Agent (testing coordination)",
                    "security": "Security Agent (security analysis)",
                    "document": "Documentation Agent (project pattern scanning)",
                    "ticket": "Ticketing Agent (all ticket operations)",
                    "branch": "Version Control Agent (branch management)",
                    "merge": "Version Control Agent (merge operations)",
                    "research": "Research Agent (general research)",
                    "code": "Engineer Agent (code implementation)",
                    "data": "Data Engineer Agent (data operations)"
                }
            },
            
            "service_architecture": {
                "core_services": {
                    "parent_directory_manager": {
                        "purpose": "Manages framework deployment across parent directories",
                        "key_features": [
                            "Template protection with automatic backups",
                            "Version checking and deployment management",
                            "Framework template deployment to parent directories",
                            "Rotation management (2 most recent backups)",
                            "Integrity validation and permission management"
                        ],
                        "critical_files": [
                            "framework/CLAUDE.md (master template - NEVER DELETE)",
                            ".claude-pm/framework_backups/ (automatic backups)",
                            "Protection mechanism code in parent_directory_manager.py"
                        ]
                    },
                    "agent_lifecycle_manager": {
                        "purpose": "Manages agent lifecycle and coordination",
                        "responsibilities": [
                            "Agent initialization and cleanup",
                            "Performance monitoring and metrics",
                            "Agent state management",
                            "Cross-agent coordination",
                            "Health monitoring and reporting"
                        ]
                    },
                    "agent_persistence_service": {
                        "purpose": "Handles agent state persistence and recovery",
                        "features": [
                            "Agent configuration persistence",
                            "State recovery mechanisms",
                            "Performance history tracking",
                            "Agent metadata management"
                        ]
                    },
                    "agent_modification_tracker": {
                        "purpose": "Tracks and manages agent modifications",
                        "capabilities": [
                            "Modification detection and logging",
                            "Change impact analysis",
                            "Rollback capabilities",
                            "Modification history tracking"
                        ]
                    }
                },
                
                "integration_patterns": {
                    "shared_prompt_cache": {
                        "performance_target": ">95% cache hit ratio",
                        "integration_points": [
                            "AgentPromptBuilder for agent enumeration",
                            "Agent discovery optimization",
                            "Specialized agent query caching",
                            "Performance metrics collection"
                        ]
                    },
                    "task_tool_integration": {
                        "subprocess_creation": "Hierarchical precedence respected",
                        "context_inheritance": "Filtered context by agent tier",
                        "result_integration": "Comprehensive operational insights",
                        "performance_targets": {
                            "agent_discovery": "<100ms for typical project",
                            "agent_loading": "<50ms per agent", 
                            "registry_initialization": "<200ms"
                        }
                    }
                }
            }
        },
        
        "business_logic": {
            "operational_workflows": {
                "startup_protocol": [
                    "MANDATORY: Acknowledge current date for temporal context",
                    "MANDATORY: Verify claude-pm init status with --verify",
                    "MANDATORY: Core system health check",
                    "MANDATORY: Initialize all 9 core agents",
                    "Review active tickets with date context",
                    "Provide status summary and ask for tasks"
                ],
                
                "push_workflow": {
                    "enhanced_delegation_flow": "PM → Documentation Agent (changelog) → QA Agent (testing) → Data Engineer Agent (validation) → Version Control Agent (Git operations)",
                    "components": [
                        "Documentation Agent: Generate changelog, analyze semantic versioning",
                        "QA Agent: Execute test suite, quality validation",
                        "Data Engineer Agent: Validate data integrity, verify API connectivity",
                        "Version Control Agent: Track files, apply version bumps, create tags"
                    ]
                },
                
                "deploy_workflow": {
                    "delegation_flow": "PM → Ops Agent (local deployment) → QA Agent (validation)",
                    "validation_requirements": [
                        "Script deployment automation",
                        "Framework integrity testing",
                        "Version consistency validation"
                    ]
                },
                
                "publish_workflow": {
                    "delegation_flow": "PM → Documentation Agent (version docs) → Ops Agent (package publication)",
                    "integration_requirements": [
                        "NPM package publication",
                        "Version alignment across all systems",
                        "Documentation synchronization"
                    ]
                }
            },
            
            "todowrite_integration": {
                "workflow_pattern": [
                    "Create TodoWrite entries with agent name prefixes",
                    "Mark todo as in_progress when delegating via Task Tool",
                    "Update todo status based on subprocess completion",
                    "Mark todo as completed when agent delivers results"
                ],
                "agent_prefixes": {
                    "research_tasks": "Researcher: [task description]",
                    "documentation_tasks": "Documentationer: [task description]",
                    "qa_tasks": "QA: [task description]",
                    "devops_tasks": "Ops: [task description]",
                    "security_tasks": "Security: [task description]",
                    "version_control_tasks": "Versioner: [task description]",
                    "code_implementation": "Engineer: [task description]",
                    "data_operations": "Data Engineer: [task description]"
                }
            },
            
            "subprocess_validation_protocol": {
                "critical_requirement": "PM MUST ALWAYS VERIFY SUBPROCESS CLAIMS WITH DIRECT TESTING",
                "validation_steps": [
                    "Direct CLI testing - run actual commands",
                    "Real import validation - test actual imports",
                    "Version consistency verification - check all version numbers",
                    "Functional end-to-end testing - simulate user workflows"
                ],
                "escalation_triggers": [
                    "Subprocess reports success but direct testing fails",
                    "Version numbers don't match between systems",
                    "Import errors for claimed existing modules",
                    "CLI commands fail despite subprocess validation"
                ]
            }
        },
        
        "deployment_patterns": {
            "framework_protection": {
                "absolute_prohibitions": [
                    "NEVER DELETE framework/CLAUDE.md (breaks ALL deployments)",
                    "NEVER REMOVE protection mechanisms",
                    "NEVER BYPASS version checking"
                ],
                "protection_mechanisms": [
                    "Automatic backup on access (2 most recent copies)",
                    "Rotation management and cleanup",
                    "Integrity validation on startup",
                    "Permission management",
                    "Path validation for legitimate files"
                ]
            },
            
            "script_deployment": {
                "automation_commands": [
                    "python scripts/deploy_scripts.py --deploy (deploy all)",
                    "python scripts/deploy_scripts.py --check (check drift)",
                    "python scripts/deploy_scripts.py --status (comprehensive status)",
                    "python scripts/deploy_scripts.py --verify (verify functionality)"
                ],
                "features": [
                    "Automatic backups before deployment",
                    "Checksum validation for drift detection",
                    "Version tracking and deployment history",
                    "Rollback support for recovery"
                ]
            },
            
            "integrity_testing": {
                "testing_commands": [
                    "python scripts/test_framework_integrity.py (all tests)",
                    "python test_framework_template.py (handlebars tests)",
                    "python scripts/validate_version_consistency.py (version validation)"
                ],
                "validation_scope": [
                    "Handlebars variables in framework/CLAUDE.md",
                    "Version consistency across VERSION, package.json, Python package",
                    "Template structure and required variables",
                    "Deployment integrity and variable substitution",
                    "Backup system operation"
                ]
            }
        },
        
        "performance_optimization": {
            "agent_registry_requirements": {
                "performance_targets": {
                    "agent_discovery": "<100ms for typical project",
                    "agent_loading": "<50ms per agent",
                    "registry_initialization": "<200ms",
                    "cache_hit_ratio": ">95% for repeated queries"
                },
                "optimization_strategies": [
                    "SharedPromptCache integration for performance",
                    "Lazy loading of agent capabilities",
                    "Hierarchical caching with precedence awareness",
                    "Specialized agent discovery beyond base types"
                ]
            },
            
            "health_monitoring": {
                "framework_health": "⚡ <15 second health monitoring (77% improvement)",
                "monitoring_commands": [
                    "python -c \"from claude_pm.services.health_monitor import HealthMonitor; HealthMonitor().check_framework_health()\"",
                    "claude-pm init --verify (agent hierarchy validation)"
                ]
            }
        },
        
        "critical_file_locations": {
            "protected_files": [
                "framework/CLAUDE.md - Master template (ESSENTIAL FOR ALL DEPLOYMENTS)",
                ".claude-pm/framework_backups/ - Automatic backups",
                "claude_pm/services/parent_directory_manager.py - Protection code",
                "VERSION - Framework version reference (must match package.json)"
            ],
            "configuration_files": [
                ".claude-pm/parent_directory_manager/ - Service state",
                ".claude-pm/config.json - Framework configuration",
                "package.json - NPM package and primary version source"
            ],
            "agent_locations": {
                "system_agents": "claude_pm/agents/ (code-based, lowest precedence)",
                "user_agents": "Directory hierarchy with precedence",
                "project_agents": "$PWD/.claude-pm/agents/ (highest precedence)"
            }
        }
    }
    
    def __init__(self, project_path: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize the Codebase Research Agent."""
        super().__init__(name="codebase-research-agent", config=config)
        
        # Agent metadata
        self.agent_type = "research"
        self.agent_tier = "project"
        self.agent_priority = 3
        self.agent_authority = "codebase_research_highest"
        self.specializations = ['codebase', 'architecture', 'business_logic', 'framework', 'claude_pm_framework']
        
        # Project configuration
        self.project_path = project_path or Path.cwd()
        self.project_name = self.project_path.name
        
        # Agent capabilities
        self.capabilities = [
            "codebase_question_answering",
            "architecture_analysis", 
            "business_logic_explanation",
            "implementation_guidance",
            "pattern_research",
            "framework_knowledge",
            "optimization_recommendations",
            "integration_guidance"
        ]
        
        # Performance metrics
        self.operations_count = 0
        self.knowledge_queries = 0
        self.architecture_analyses = 0
        self.implementation_guidances = 0
        
        self.logger.info(f"Initialized Codebase Research Agent for Claude PM Framework v{self.FRAMEWORK_KNOWLEDGE['version']}")
    
    async def _initialize(self) -> None:
        """Initialize the Codebase Research Agent."""
        try:
            self._start_time = datetime.now()
            self._running = True
            self.logger.info("Codebase Research Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Codebase Research Agent: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup Codebase Research Agent resources."""
        try:
            self._running = False
            self.logger.info("Codebase Research Agent cleanup completed")
        except Exception as e:
            self.logger.error(f"Failed to cleanup Codebase Research Agent: {e}")
            raise
    
    async def execute_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Execute codebase research operations.
        
        Args:
            operation: Operation name
            **kwargs: Operation parameters
            
        Returns:
            Operation result with comprehensive codebase knowledge
        """
        operation_start = time.time()
        
        try:
            self.operations_count += 1
            
            self.logger.info(f"Executing codebase research operation: {operation}")
            
            # Route to specialized methods
            if operation == "answer_codebase_question":
                result = await self.async_answer_codebase_question(**kwargs)
            elif operation == "analyze_architecture":
                result = await self.async_analyze_architecture(**kwargs)
            elif operation == "explain_business_logic":
                result = await self.async_explain_business_logic(**kwargs)
            elif operation == "guide_implementation":
                result = await self.async_guide_implementation(**kwargs)
            elif operation == "research_patterns":
                result = await self.async_research_patterns(**kwargs)
            else:
                result = await self._execute_general_research(operation, **kwargs)
            
            operation_time = time.time() - operation_start
            self.logger.info(f"Operation {operation} completed in {operation_time:.2f}s")
            
            return {
                "success": True,
                "operation": operation,
                "result": result,
                "execution_time": operation_time,
                "agent_type": self.agent_type,
                "agent_tier": self.agent_tier,
                "specializations": self.specializations,
                "framework_version": self.FRAMEWORK_KNOWLEDGE["version"]
            }
            
        except Exception as e:
            operation_time = time.time() - operation_start
            self.logger.error(f"Operation {operation} failed: {e}")
            
            return {
                "success": False,
                "operation": operation,
                "error": str(e),
                "execution_time": operation_time,
                "agent_type": self.agent_type,
                "agent_tier": self.agent_tier
            }
    
    async def async_answer_codebase_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer specific questions about the Claude PM Framework codebase.
        
        This is the primary method for getting authoritative answers about framework
        architecture, patterns, services, and implementation details.
        """
        self.knowledge_queries += 1
        
        if not question:
            return {"error": "Question parameter is required"}
        
        question_lower = question.lower()
        
        # Architecture questions
        if any(keyword in question_lower for keyword in ["architecture", "structure", "design", "pattern"]):
            return await self._answer_architecture_question(question, context)
        
        # Agent hierarchy questions
        elif any(keyword in question_lower for keyword in ["agent", "hierarchy", "precedence", "delegation"]):
            return await self._answer_agent_question(question, context)
        
        # Service questions
        elif any(keyword in question_lower for keyword in ["service", "manager", "lifecycle", "persistence"]):
            return await self._answer_service_question(question, context)
        
        # Workflow questions
        elif any(keyword in question_lower for keyword in ["workflow", "push", "deploy", "publish", "startup"]):
            return await self._answer_workflow_question(question, context)
        
        # Performance questions
        elif any(keyword in question_lower for keyword in ["performance", "optimization", "speed", "cache"]):
            return await self._answer_performance_question(question, context)
        
        # Protection and deployment questions
        elif any(keyword in question_lower for keyword in ["protection", "deployment", "backup", "template"]):
            return await self._answer_deployment_question(question, context)
        
        # General framework questions
        else:
            return await self._answer_general_question(question, context)
    
    async def _answer_architecture_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer architecture-related questions."""
        arch_knowledge = self.FRAMEWORK_KNOWLEDGE["architecture"]
        
        return {
            "question": question,
            "category": "architecture",
            "core_philosophy": arch_knowledge["core_philosophy"],
            "agent_hierarchy": arch_knowledge["agent_hierarchy"],
            "service_architecture": arch_knowledge["service_architecture"],
            "key_insights": [
                "Framework follows two-tier agent hierarchy (System + User)",
                "PM Agent never performs direct work - always delegates via Task Tool",
                "Agents have specialized responsibilities and authority domains",
                "Performance-optimized with shared prompt caching",
                "Hierarchical precedence for agent discovery and loading"
            ],
            "related_patterns": [
                "Multi-agent orchestration patterns",
                "Delegation and subprocess creation",
                "Hierarchical agent discovery",
                "Performance optimization strategies"
            ],
            "context": context
        }
    
    async def _answer_agent_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer agent hierarchy and delegation questions."""
        agent_info = self.FRAMEWORK_KNOWLEDGE["architecture"]["agent_hierarchy"]
        
        return {
            "question": question,
            "category": "agent_hierarchy",
            "precedence_order": agent_info["precedence_order"],
            "core_agent_types": agent_info["core_agent_types"],
            "delegation_patterns": agent_info["delegation_patterns"],
            "key_insights": [
                "Current directory agents have highest precedence",
                "System agents provide fallback functionality",
                "Each agent type has specialized authority domains",
                "Task Tool creates subprocesses with hierarchy respect",
                "Agent loading follows performance-optimized patterns"
            ],
            "implementation_guidance": [
                "Use Task Tool for all agent delegation",
                "Provide comprehensive context to each agent",
                "Respect agent authority boundaries",
                "Integrate TodoWrite with agent prefixes",
                "Follow subprocess validation protocol"
            ],
            "context": context
        }
    
    async def _answer_service_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer service architecture questions."""
        services = self.FRAMEWORK_KNOWLEDGE["architecture"]["service_architecture"]["core_services"]
        
        return {
            "question": question,
            "category": "services",
            "core_services": services,
            "key_integrations": [
                "Parent Directory Manager: Framework deployment and protection",
                "Agent Lifecycle Manager: Agent coordination and monitoring", 
                "Agent Persistence Service: State management and recovery",
                "Agent Modification Tracker: Change tracking and rollback"
            ],
            "critical_services": {
                "parent_directory_manager": "CRITICAL - Protects framework template, manages deployments",
                "agent_lifecycle_manager": "ESSENTIAL - Coordinates all agent operations",
                "shared_prompt_cache": "PERFORMANCE - Optimizes agent discovery and loading"
            },
            "integration_patterns": self.FRAMEWORK_KNOWLEDGE["architecture"]["service_architecture"]["integration_patterns"],
            "context": context
        }
    
    async def _answer_workflow_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer workflow and operational questions."""
        workflows = self.FRAMEWORK_KNOWLEDGE["business_logic"]["operational_workflows"]
        
        return {
            "question": question,
            "category": "workflows",
            "operational_workflows": workflows,
            "key_workflows": {
                "startup_protocol": "MANDATORY 6-step initialization sequence",
                "push_workflow": "Enhanced 4-agent delegation flow",
                "deploy_workflow": "Ops → QA validation coordination",
                "publish_workflow": "Documentation → Ops publication"
            },
            "todowrite_integration": self.FRAMEWORK_KNOWLEDGE["business_logic"]["todowrite_integration"],
            "subprocess_validation": self.FRAMEWORK_KNOWLEDGE["business_logic"]["subprocess_validation_protocol"],
            "critical_requirements": [
                "All work must be delegated via Task Tool",
                "TodoWrite integration with agent prefixes",
                "Subprocess validation with direct testing",
                "Temporal context integration throughout"
            ],
            "context": context
        }
    
    async def _answer_performance_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer performance optimization questions."""
        perf_info = self.FRAMEWORK_KNOWLEDGE["performance_optimization"]
        
        return {
            "question": question,
            "category": "performance",
            "performance_targets": perf_info["agent_registry_requirements"]["performance_targets"],
            "optimization_strategies": perf_info["agent_registry_requirements"]["optimization_strategies"],
            "health_monitoring": perf_info["health_monitoring"],
            "key_optimizations": [
                "SharedPromptCache integration for >95% cache hit ratio",
                "Agent discovery <100ms for typical project",
                "Agent loading <50ms per agent",
                "Registry initialization <200ms",
                "Framework health monitoring <15 seconds (77% improvement)"
            ],
            "monitoring_commands": perf_info["health_monitoring"]["monitoring_commands"],
            "context": context
        }
    
    async def _answer_deployment_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer deployment and protection questions."""
        deployment_info = self.FRAMEWORK_KNOWLEDGE["deployment_patterns"]
        
        return {
            "question": question,
            "category": "deployment",
            "framework_protection": deployment_info["framework_protection"],
            "script_deployment": deployment_info["script_deployment"],
            "integrity_testing": deployment_info["integrity_testing"],
            "critical_protections": [
                "framework/CLAUDE.md is ESSENTIAL - NEVER DELETE",
                "Automatic backup system with 2-copy rotation",
                "Version checking prevents corruption",
                "Protection mechanisms are non-negotiable"
            ],
            "deployment_automation": deployment_info["script_deployment"]["automation_commands"],
            "testing_requirements": deployment_info["integrity_testing"]["testing_commands"],
            "context": context
        }
    
    async def _answer_general_question(self, question: str, context: Optional[str]) -> Dict[str, Any]:
        """Answer general framework questions."""
        return {
            "question": question,
            "category": "general",
            "framework_overview": {
                "version": self.FRAMEWORK_KNOWLEDGE["version"],
                "purpose": "Multi-agent orchestration system for project management",
                "key_principles": [
                    "PM Agent delegates all work via Task Tool",
                    "Specialized agents with authority domains",
                    "Two-tier hierarchy with precedence rules",
                    "Performance optimization with caching",
                    "Comprehensive protection mechanisms"
                ]
            },
            "core_components": {
                "agents": "9 core agent types with specialized responsibilities",
                "services": "4 core services for lifecycle and coordination",
                "workflows": "Standardized operational patterns",
                "protection": "Framework integrity and deployment safety"
            },
            "getting_started": [
                "Use this Codebase Research Agent for planning questions",
                "Follow mandatory startup protocol",
                "Delegate all work via Task Tool",
                "Respect agent hierarchy and authority",
                "Apply subprocess validation protocol"
            ],
            "context": context
        }
    
    async def async_analyze_architecture(self, component: Optional[str] = None, depth: str = "detailed") -> Dict[str, Any]:
        """
        Analyze framework architecture components in detail.
        
        Args:
            component: Specific component to analyze (optional)
            depth: Analysis depth - "overview", "detailed", or "comprehensive"
        """
        self.architecture_analyses += 1
        
        if component:
            return await self._analyze_specific_component(component, depth)
        else:
            return await self._analyze_full_architecture(depth)
    
    async def _analyze_specific_component(self, component: str, depth: str) -> Dict[str, Any]:
        """Analyze a specific architecture component."""
        component_lower = component.lower()
        
        if "agent" in component_lower:
            return await self._analyze_agent_architecture(depth)
        elif "service" in component_lower:
            return await self._analyze_service_architecture(depth)
        elif "workflow" in component_lower:
            return await self._analyze_workflow_architecture(depth)
        else:
            return await self._analyze_full_architecture(depth)
    
    async def _analyze_agent_architecture(self, depth: str) -> Dict[str, Any]:
        """Analyze agent architecture in detail."""
        return {
            "component": "agent_architecture",
            "analysis_depth": depth,
            "hierarchy_structure": self.FRAMEWORK_KNOWLEDGE["architecture"]["agent_hierarchy"],
            "architectural_patterns": [
                "Two-tier hierarchy (System + User)",
                "Precedence-based discovery",
                "Specialized authority domains",
                "Task Tool subprocess creation",
                "Performance-optimized loading"
            ],
            "integration_points": [
                "SharedPromptCache for performance",
                "AgentPromptBuilder for enumeration",
                "Hierarchical agent loader",
                "Agent lifecycle manager",
                "Agent modification tracker"
            ],
            "design_decisions": [
                "Project agents override user and system agents",
                "System agents provide reliable fallback",
                "Each agent type has specialized capabilities",
                "Async operations for performance",
                "Comprehensive error handling and logging"
            ]
        }
    
    async def _analyze_service_architecture(self, depth: str) -> Dict[str, Any]:
        """Analyze service architecture in detail."""
        return {
            "component": "service_architecture", 
            "analysis_depth": depth,
            "core_services": self.FRAMEWORK_KNOWLEDGE["architecture"]["service_architecture"]["core_services"],
            "service_relationships": [
                "Parent Directory Manager → Framework deployment",
                "Agent Lifecycle Manager → Agent coordination",
                "Agent Persistence Service → State management",
                "Agent Modification Tracker → Change tracking"
            ],
            "integration_patterns": self.FRAMEWORK_KNOWLEDGE["architecture"]["service_architecture"]["integration_patterns"],
            "design_principles": [
                "Service separation of concerns",
                "Async operations for performance",
                "Comprehensive error handling",
                "State persistence and recovery",
                "Performance monitoring and metrics"
            ]
        }
    
    async def _analyze_full_architecture(self, depth: str) -> Dict[str, Any]:
        """Analyze complete framework architecture."""
        return {
            "component": "full_architecture",
            "analysis_depth": depth,
            "architecture_overview": self.FRAMEWORK_KNOWLEDGE["architecture"],
            "key_architectural_decisions": [
                "Multi-agent orchestration over monolithic approach",
                "Two-tier hierarchy for flexibility and performance",
                "Task Tool delegation for all PM operations",
                "Specialized agent authority domains",
                "Performance optimization with caching strategies"
            ],
            "architectural_benefits": [
                "Scalable agent specialization",
                "Flexible customization through hierarchy",
                "Performance optimization opportunities",
                "Clear separation of concerns",
                "Comprehensive operational tracking"
            ],
            "future_considerations": [
                "Agent registry optimization",
                "Enhanced performance monitoring",
                "Extended agent specializations",
                "Advanced workflow orchestration"
            ]
        }
    
    async def async_explain_business_logic(self, workflow: Optional[str] = None, detail_level: str = "comprehensive") -> Dict[str, Any]:
        """
        Explain business logic and operational workflows.
        
        Args:
            workflow: Specific workflow to explain (optional)
            detail_level: Explanation detail - "summary", "detailed", or "comprehensive"
        """
        if workflow:
            return await self._explain_specific_workflow(workflow, detail_level)
        else:
            return await self._explain_all_workflows(detail_level)
    
    async def _explain_specific_workflow(self, workflow: str, detail_level: str) -> Dict[str, Any]:
        """Explain a specific workflow in detail."""
        workflows = self.FRAMEWORK_KNOWLEDGE["business_logic"]["operational_workflows"]
        
        workflow_lower = workflow.lower()
        
        if "startup" in workflow_lower:
            return {
                "workflow": "startup_protocol",
                "detail_level": detail_level,
                "steps": workflows["startup_protocol"],
                "business_logic": [
                    "Date acknowledgment establishes temporal context",
                    "Init verification ensures framework readiness",
                    "Health check validates core system operation",
                    "Agent initialization prepares delegation targets",
                    "Ticket review provides current status context",
                    "Status summary and task request enables user interaction"
                ],
                "critical_requirements": [
                    "MANDATORY: All 6 steps must be completed",
                    "Temporal context affects all subsequent operations",
                    "Health validation prevents system issues",
                    "Agent readiness enables effective delegation"
                ]
            }
        elif "push" in workflow_lower:
            return {
                "workflow": "push_workflow",
                "detail_level": detail_level,
                "enhanced_flow": workflows["push_workflow"],
                "business_logic": [
                    "Documentation Agent generates changelog and analyzes version impact",
                    "QA Agent executes comprehensive testing and validation",
                    "Data Engineer Agent validates data integrity and API connectivity",
                    "Version Control Agent applies version bumps and Git operations"
                ],
                "coordination_requirements": [
                    "Sequential execution with dependency management",
                    "Comprehensive error handling and rollback",
                    "Status reporting and operational insights",
                    "Integration with TodoWrite tracking"
                ]
            }
        else:
            return {
                "workflow": workflow,
                "detail_level": detail_level,
                "all_workflows": workflows,
                "general_principles": [
                    "All workflows use Task Tool delegation",
                    "Comprehensive operational tracking",
                    "Error handling and recovery mechanisms",
                    "Performance optimization throughout"
                ]
            }
    
    async def _explain_all_workflows(self, detail_level: str) -> Dict[str, Any]:
        """Explain all business workflows."""
        return {
            "scope": "all_workflows",
            "detail_level": detail_level,
            "business_logic": self.FRAMEWORK_KNOWLEDGE["business_logic"],
            "key_workflow_patterns": [
                "Startup Protocol: 6-step mandatory initialization",
                "Push Workflow: 4-agent sequential delegation",
                "Deploy Workflow: Ops and QA coordination",
                "Publish Workflow: Documentation and Ops integration"
            ],
            "integration_mechanisms": [
                "TodoWrite with agent prefixes",
                "Subprocess validation protocol",
                "Temporal context integration",
                "Comprehensive operational reporting"
            ],
            "business_value": [
                "Systematic and repeatable operations",
                "Comprehensive quality assurance",
                "Performance optimization",
                "Operational transparency and tracking"
            ]
        }
    
    async def async_guide_implementation(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Provide implementation guidance for framework tasks.
        
        Args:
            task: Implementation task description
            context: Additional context for guidance
        """
        self.implementation_guidances += 1
        
        if not task:
            return {"error": "Task parameter is required"}
        
        task_lower = task.lower()
        
        # Agent implementation guidance
        if any(keyword in task_lower for keyword in ["agent", "create agent", "implement agent"]):
            return await self._guide_agent_implementation(task, context)
        
        # Service implementation guidance  
        elif any(keyword in task_lower for keyword in ["service", "create service", "implement service"]):
            return await self._guide_service_implementation(task, context)
        
        # Workflow implementation guidance
        elif any(keyword in task_lower for keyword in ["workflow", "push", "deploy", "publish"]):
            return await self._guide_workflow_implementation(task, context)
        
        # Performance optimization guidance
        elif any(keyword in task_lower for keyword in ["performance", "optimization", "speed", "cache"]):
            return await self._guide_performance_implementation(task, context)
        
        # General implementation guidance
        else:
            return await self._guide_general_implementation(task, context)
    
    async def _guide_agent_implementation(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Guide agent implementation tasks."""
        return {
            "task": task,
            "guidance_type": "agent_implementation",
            "implementation_steps": [
                "1. Choose appropriate agent tier (project/user/system)",
                "2. Use agent template from lib/framework/claude_pm/agents/templates/",
                "3. Implement specialized capabilities and methods",
                "4. Integrate with agent hierarchy and discovery",
                "5. Add performance optimization and caching",
                "6. Implement comprehensive error handling",
                "7. Add operational metrics and monitoring"
            ],
            "key_patterns": [
                "Extend BaseService for core functionality",
                "Implement async operations for performance",
                "Use agent_type and specializations for discovery",
                "Integrate with SharedPromptCache for optimization",
                "Follow agent authority and precedence rules"
            ],
            "critical_considerations": [
                "Respect agent hierarchy precedence",
                "Implement proper async initialization/cleanup",
                "Add comprehensive logging and error handling",
                "Integrate with agent lifecycle management",
                "Follow performance optimization patterns"
            ],
            "example_implementations": [
                "This CodebaseResearchAgent as project-tier specialized agent",
                "System agents in claude_pm/agents/ for core functionality",
                "User agents for customization and overrides"
            ],
            "context": context
        }
    
    async def _guide_service_implementation(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Guide service implementation tasks."""
        return {
            "task": task,
            "guidance_type": "service_implementation",
            "implementation_steps": [
                "1. Extend BaseService with specialized functionality",
                "2. Implement async initialization and cleanup",
                "3. Add service-specific configuration and state management",
                "4. Integrate with other framework services",
                "5. Implement performance monitoring and metrics",
                "6. Add comprehensive error handling and recovery",
                "7. Implement service lifecycle management"
            ],
            "service_patterns": [
                "Parent Directory Manager: Framework deployment and protection",
                "Agent Lifecycle Manager: Agent coordination and monitoring",
                "Agent Persistence Service: State management and recovery",
                "Agent Modification Tracker: Change tracking and rollback"
            ],
            "integration_requirements": [
                "Service discovery and registration",
                "Inter-service communication patterns",
                "Shared state management",
                "Performance optimization strategies",
                "Comprehensive error handling"
            ],
            "critical_considerations": [
                "Service separation of concerns",
                "Async operations for performance",
                "State persistence and recovery",
                "Integration with existing services",
                "Performance monitoring and optimization"
            ],
            "context": context
        }
    
    async def _guide_workflow_implementation(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Guide workflow implementation tasks."""
        return {
            "task": task,
            "guidance_type": "workflow_implementation",
            "implementation_steps": [
                "1. Define workflow sequence and agent delegation",
                "2. Implement TodoWrite integration with agent prefixes",
                "3. Add Task Tool subprocess creation and management",
                "4. Implement comprehensive error handling and rollback",
                "5. Add progress tracking and operational reporting",
                "6. Integrate subprocess validation protocol",
                "7. Add performance monitoring and optimization"
            ],
            "workflow_patterns": self.FRAMEWORK_KNOWLEDGE["business_logic"]["operational_workflows"],
            "delegation_guidelines": [
                "Use Task Tool for all agent delegation",
                "Provide comprehensive context to each agent",
                "Respect agent authority and capabilities",
                "Implement sequential and parallel coordination",
                "Add comprehensive result integration"
            ],
            "validation_requirements": [
                "Direct CLI testing of subprocess claims",
                "Real import validation for functionality",
                "Version consistency verification",
                "Functional end-to-end testing"
            ],
            "context": context
        }
    
    async def _guide_performance_implementation(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Guide performance optimization implementation."""
        perf_targets = self.FRAMEWORK_KNOWLEDGE["performance_optimization"]["agent_registry_requirements"]["performance_targets"]
        
        return {
            "task": task,
            "guidance_type": "performance_implementation",
            "performance_targets": perf_targets,
            "optimization_strategies": [
                "SharedPromptCache integration for >95% cache hit ratio",
                "Lazy loading of agent capabilities",
                "Hierarchical caching with precedence awareness",
                "Async operations with proper concurrency",
                "Performance monitoring and metrics collection"
            ],
            "implementation_steps": [
                "1. Identify performance bottlenecks and targets",
                "2. Implement caching strategies and optimization",
                "3. Add async operations and concurrency",
                "4. Integrate performance monitoring and metrics",
                "5. Implement lazy loading and resource optimization",
                "6. Add comprehensive performance testing",
                "7. Continuously monitor and optimize"
            ],
            "critical_optimizations": [
                "Agent discovery <100ms for typical project",
                "Agent loading <50ms per agent",
                "Registry initialization <200ms",
                "Health monitoring <15 seconds",
                "Cache hit ratio >95%"
            ],
            "context": context
        }
    
    async def _guide_general_implementation(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Guide general implementation tasks."""
        return {
            "task": task,
            "guidance_type": "general_implementation",
            "framework_principles": [
                "PM Agent delegates all work via Task Tool",
                "Agents have specialized responsibilities and authority",
                "Two-tier hierarchy with precedence rules",
                "Performance optimization with caching",
                "Comprehensive protection mechanisms"
            ],
            "implementation_guidelines": [
                "Follow framework architecture patterns",
                "Respect agent hierarchy and authority",
                "Implement comprehensive error handling",
                "Add performance monitoring and optimization",
                "Integrate with existing framework services"
            ],
            "critical_requirements": [
                "Use Task Tool for all delegation",
                "Implement subprocess validation protocol",
                "Add TodoWrite integration",
                "Respect protection mechanisms",
                "Follow performance targets"
            ],
            "best_practices": [
                "Comprehensive logging and error handling",
                "Async operations for performance",
                "State persistence and recovery",
                "Integration testing and validation",
                "Continuous monitoring and optimization"
            ],
            "context": context
        }
    
    async def async_research_patterns(self, pattern_type: str, scope: str = "comprehensive") -> Dict[str, Any]:
        """
        Research framework patterns and optimizations.
        
        Args:
            pattern_type: Type of patterns to research
            scope: Research scope - "focused", "comprehensive", or "exhaustive"
        """
        pattern_type_lower = pattern_type.lower()
        
        if "agent" in pattern_type_lower:
            return await self._research_agent_patterns(scope)
        elif "service" in pattern_type_lower:
            return await self._research_service_patterns(scope)
        elif "workflow" in pattern_type_lower:
            return await self._research_workflow_patterns(scope)
        elif "performance" in pattern_type_lower:
            return await self._research_performance_patterns(scope)
        else:
            return await self._research_all_patterns(scope)
    
    async def _research_agent_patterns(self, scope: str) -> Dict[str, Any]:
        """Research agent implementation patterns."""
        return {
            "pattern_type": "agent_patterns",
            "research_scope": scope,
            "core_patterns": [
                "Two-tier hierarchy with precedence",
                "Specialized authority domains",
                "Task Tool subprocess creation",
                "Performance-optimized loading",
                "Comprehensive error handling"
            ],
            "implementation_patterns": [
                "BaseService extension for core functionality",
                "Async initialization and cleanup",
                "Agent type and specialization metadata",
                "SharedPromptCache integration",
                "Performance monitoring and metrics"
            ],
            "optimization_patterns": [
                "Lazy loading of capabilities",
                "Caching with hierarchy awareness",
                "Async operations with concurrency",
                "Resource optimization strategies",
                "Performance target adherence"
            ],
            "best_practices": [
                "Clear separation of concerns",
                "Comprehensive logging and error handling",
                "State persistence and recovery",
                "Integration testing and validation",
                "Continuous monitoring and optimization"
            ]
        }
    
    async def _research_service_patterns(self, scope: str) -> Dict[str, Any]:
        """Research service implementation patterns."""
        return {
            "pattern_type": "service_patterns",
            "research_scope": scope,
            "service_architecture_patterns": self.FRAMEWORK_KNOWLEDGE["architecture"]["service_architecture"],
            "integration_patterns": [
                "Service discovery and registration",
                "Inter-service communication",
                "Shared state management",
                "Performance optimization",
                "Error handling and recovery"
            ],
            "lifecycle_patterns": [
                "Async initialization and cleanup",
                "Resource management and optimization",
                "State persistence and recovery",
                "Health monitoring and validation",
                "Performance monitoring and metrics"
            ],
            "best_practices": [
                "Service separation of concerns",
                "Comprehensive error handling",
                "Performance optimization",
                "State management and persistence",
                "Integration testing and validation"
            ]
        }
    
    async def _research_workflow_patterns(self, scope: str) -> Dict[str, Any]:
        """Research workflow orchestration patterns."""
        return {
            "pattern_type": "workflow_patterns",
            "research_scope": scope,
            "orchestration_patterns": self.FRAMEWORK_KNOWLEDGE["business_logic"]["operational_workflows"],
            "delegation_patterns": [
                "Task Tool subprocess creation",
                "Agent authority and capabilities",
                "Sequential and parallel coordination",
                "Comprehensive context provision",
                "Result integration and reporting"
            ],
            "coordination_patterns": [
                "TodoWrite integration with prefixes",
                "Subprocess validation protocol",
                "Error handling and rollback",
                "Progress tracking and reporting",
                "Performance monitoring"
            ],
            "optimization_patterns": [
                "Async operations and concurrency",
                "Caching and performance optimization",
                "Resource management and cleanup",
                "Comprehensive error handling",
                "Operational insights collection"
            ]
        }
    
    async def _research_performance_patterns(self, scope: str) -> Dict[str, Any]:
        """Research performance optimization patterns."""
        return {
            "pattern_type": "performance_patterns",
            "research_scope": scope,
            "optimization_strategies": self.FRAMEWORK_KNOWLEDGE["performance_optimization"],
            "caching_patterns": [
                "SharedPromptCache for >95% hit ratio",
                "Hierarchical caching with precedence",
                "Lazy loading of capabilities",
                "Resource optimization strategies",
                "Performance target adherence"
            ],
            "async_patterns": [
                "Async operations for performance",
                "Concurrency and parallelization",
                "Resource management and cleanup",
                "Error handling without blocking",
                "Performance monitoring and metrics"
            ],
            "monitoring_patterns": [
                "Performance metrics collection",
                "Health monitoring and validation",
                "Resource usage tracking",
                "Error rate monitoring",
                "Optimization opportunity identification"
            ]
        }
    
    async def _research_all_patterns(self, scope: str) -> Dict[str, Any]:
        """Research all framework patterns comprehensively."""
        return {
            "pattern_type": "all_patterns",
            "research_scope": scope,
            "framework_patterns": {
                "agent_patterns": await self._research_agent_patterns(scope),
                "service_patterns": await self._research_service_patterns(scope),
                "workflow_patterns": await self._research_workflow_patterns(scope),
                "performance_patterns": await self._research_performance_patterns(scope)
            },
            "cross_cutting_patterns": [
                "Comprehensive error handling",
                "Performance optimization",
                "State management and persistence",
                "Integration testing and validation",
                "Continuous monitoring and optimization"
            ],
            "architectural_insights": [
                "Two-tier hierarchy provides flexibility and performance",
                "Specialized agents enable focused functionality",
                "Task Tool delegation ensures proper orchestration",
                "SharedPromptCache optimization improves performance",
                "Protection mechanisms ensure framework integrity"
            ]
        }
    
    async def _execute_general_research(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute general research operations."""
        return {
            "operation": operation,
            "framework_version": self.FRAMEWORK_KNOWLEDGE["version"],
            "available_operations": [
                "answer_codebase_question - Answer specific framework questions",
                "analyze_architecture - Analyze framework architecture",
                "explain_business_logic - Explain workflows and business logic",
                "guide_implementation - Provide implementation guidance",
                "research_patterns - Research framework patterns"
            ],
            "embedded_knowledge": {
                "architecture": "Complete framework architecture knowledge",
                "business_logic": "Operational workflows and patterns",
                "deployment": "Protection and deployment patterns",
                "performance": "Optimization strategies and targets"
            },
            "specializations": self.specializations,
            "parameters": kwargs
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "agent_tier": self.agent_tier,
            "specializations": self.specializations,
            "framework_version": self.FRAMEWORK_KNOWLEDGE["version"],
            "project_name": self.project_name,
            "running": self.running,
            "uptime": self.uptime,
            "capabilities": self.capabilities,
            "operations_count": self.operations_count,
            "knowledge_queries": self.knowledge_queries,
            "architecture_analyses": self.architecture_analyses,
            "implementation_guidances": self.implementation_guidances,
            "embedded_knowledge_size": len(str(self.FRAMEWORK_KNOWLEDGE)),
            "last_health_check": datetime.now().isoformat()
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            "agent_metadata": {
                "name": self.name,
                "type": self.agent_type,
                "tier": self.agent_tier,
                "authority": self.agent_authority,
                "specializations": self.specializations,
                "created": "2025-07-15"
            },
            "framework_info": {
                "version": self.FRAMEWORK_KNOWLEDGE["version"],
                "embedded_knowledge_size": len(str(self.FRAMEWORK_KNOWLEDGE)),
                "knowledge_categories": list(self.FRAMEWORK_KNOWLEDGE.keys())
            },
            "capabilities": self.capabilities,
            "performance_metrics": {
                "operations_count": self.operations_count,
                "knowledge_queries": self.knowledge_queries,
                "architecture_analyses": self.architecture_analyses,
                "implementation_guidances": self.implementation_guidances
            },
            "operational_info": {
                "running": self.running,
                "uptime": self.uptime,
                "project_name": self.project_name
            }
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"CodebaseResearchAgent(name='{self.name}', specializations={self.specializations}, framework_v{self.FRAMEWORK_KNOWLEDGE['version']})"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"<CodebaseResearchAgent name='{self.name}' type='{self.agent_type}' tier='{self.agent_tier}' specializations={self.specializations} running={self.running}>"