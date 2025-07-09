"""
Scaffolding Agent - Intelligent project scaffolding using framework-based best practices
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

from ..core.base_agent import BaseAgent
from ..core.memory import MemoryManager
from ..services.ai_trackdown import AITrackdownService


@dataclass
class ScaffoldingRecommendation:
    """Represents a scaffolding recommendation for a project"""
    tech_stack: Dict[str, Any]
    project_structure: Dict[str, Any]
    dependencies: Dict[str, Any]
    reasoning: str
    confidence_score: float
    template_used: str
    approval_required: bool = False
    concerns: List[str] = field(default_factory=list)


@dataclass
class DesignDocAnalysis:
    """Analysis results from a design document"""
    project_type: str
    requirements: List[str]
    constraints: List[str]
    technology_hints: List[str]
    complexity_score: float
    recommended_frameworks: List[str]


class ScaffoldingAgent(BaseAgent):
    """
    Specialized agent for intelligent project scaffolding using framework-based best practices.
    
    This agent:
    1. Reads and analyzes design documents
    2. Researches project requirements
    3. Recommends appropriate technology stacks
    4. Suggests scaffolding approaches to PM
    5. Implements approved scaffolding if not controversial
    """
    
    def __init__(self, memory_manager: MemoryManager, trackdown_service: AITrackdownService):
        super().__init__(
            agent_id="scaffolding-agent",
            agent_type="scaffolding",
            capabilities=[
                "intelligent_scaffolding",
                "framework_analysis", 
                "design_doc_interpretation",
                "technology_stack_recommendation",
                "project_structure_generation",
                "best_practices_enforcement"
            ]
        )
        self.memory_manager = memory_manager
        self.trackdown_service = trackdown_service
        self.templates_path = Path(__file__).parent.parent.parent / "templates" / "scaffolding-agent"
        
        # Load framework preferences
        self.framework_preferences = {
            "typescript": {
                "framework": "next.js",
                "build_tool": "vite", 
                "linting": "biome",
                "state_management": "zustand",
                "styling": "tailwind",
                "components": "shadcn"
            },
            "python": {
                "web_framework": "fastapi",
                "testing": "pytest",
                "dependency_management": "poetry",
                "linting": "ruff",
                "formatting": "black",
                "type_checking": "mypy"
            }
        }
    
    async def analyze_design_document(self, doc_path: str) -> DesignDocAnalysis:
        """
        Analyze a design document to extract requirements and constraints.
        
        Args:
            doc_path: Path to the design document
            
        Returns:
            DesignDocAnalysis with extracted information
        """
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract project type based on keywords
            project_type = self._determine_project_type(content)
            
            # Extract requirements
            requirements = self._extract_requirements(content)
            
            # Extract constraints
            constraints = self._extract_constraints(content)
            
            # Extract technology hints
            tech_hints = self._extract_technology_hints(content)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(content, requirements)
            
            # Recommend frameworks based on analysis
            recommended_frameworks = self._recommend_frameworks(project_type, tech_hints, requirements)
            
            analysis = DesignDocAnalysis(
                project_type=project_type,
                requirements=requirements,
                constraints=constraints,
                technology_hints=tech_hints,
                complexity_score=complexity_score,
                recommended_frameworks=recommended_frameworks
            )
            
            # Store analysis in memory
            await self.memory_manager.store_memory(
                agent_id=self.agent_id,
                category="SCAFFOLDING_PATTERN",
                content=f"Design doc analysis: {project_type}, complexity: {complexity_score}",
                context={"analysis": analysis.__dict__}
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing design document: {e}")
            raise
    
    def _determine_project_type(self, content: str) -> str:
        """Determine project type from document content"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["web app", "frontend", "react", "nextjs", "vue"]):
            return "web_application"
        elif any(keyword in content_lower for keyword in ["api", "backend", "fastapi", "django", "flask"]):
            return "api_service"
        elif any(keyword in content_lower for keyword in ["cli", "command line", "script"]):
            return "cli_tool"
        elif any(keyword in content_lower for keyword in ["library", "package", "module"]):
            return "library"
        elif any(keyword in content_lower for keyword in ["microservice", "service", "server"]):
            return "microservice"
        else:
            return "general_application"
    
    def _extract_requirements(self, content: str) -> List[str]:
        """Extract functional requirements from document"""
        requirements = []
        
        # Look for requirement patterns
        import re
        patterns = [
            r"requirement[s]?\s*:?\s*(.+)",
            r"must\s+(.+)",
            r"should\s+(.+)",
            r"needs?\s+to\s+(.+)",
            r"feature[s]?\s*:?\s*(.+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            requirements.extend([match.strip() for match in matches])
        
        return list(set(requirements))  # Remove duplicates
    
    def _extract_constraints(self, content: str) -> List[str]:
        """Extract technical constraints from document"""
        constraints = []
        
        import re
        patterns = [
            r"constraint[s]?\s*:?\s*(.+)",
            r"limitation[s]?\s*:?\s*(.+)",
            r"cannot\s+(.+)",
            r"must not\s+(.+)",
            r"restriction[s]?\s*:?\s*(.+)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            constraints.extend([match.strip() for match in matches])
        
        return list(set(constraints))
    
    def _extract_technology_hints(self, content: str) -> List[str]:
        """Extract technology hints from document"""
        tech_keywords = [
            "react", "nextjs", "vue", "angular", "typescript", "javascript",
            "python", "fastapi", "django", "flask", "node.js", "express",
            "docker", "kubernetes", "aws", "azure", "gcp", "postgresql",
            "mongodb", "redis", "graphql", "rest", "api", "microservices"
        ]
        
        content_lower = content.lower()
        found_tech = [tech for tech in tech_keywords if tech in content_lower]
        
        return found_tech
    
    def _calculate_complexity_score(self, content: str, requirements: List[str]) -> float:
        """Calculate project complexity score (0-1)"""
        complexity_indicators = [
            "microservice", "distributed", "scalable", "high availability",
            "real-time", "authentication", "authorization", "payment",
            "integration", "api", "database", "cache", "queue"
        ]
        
        content_lower = content.lower()
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in content_lower)
        
        # Base score on indicators and requirements count
        base_score = min(complexity_count / len(complexity_indicators), 1.0)
        requirements_score = min(len(requirements) / 20, 1.0)  # Normalize to 20 requirements
        
        return (base_score + requirements_score) / 2
    
    def _recommend_frameworks(self, project_type: str, tech_hints: List[str], requirements: List[str]) -> List[str]:
        """Recommend appropriate frameworks based on analysis"""
        recommendations = []
        
        if project_type == "web_application":
            if "typescript" in tech_hints or "react" in tech_hints:
                recommendations.append("next.js")
            elif "vue" in tech_hints:
                recommendations.append("nuxt.js")
            else:
                recommendations.append("next.js")  # Default preference
        
        elif project_type == "api_service":
            if "python" in tech_hints:
                recommendations.append("fastapi")
            elif "node.js" in tech_hints or "javascript" in tech_hints:
                recommendations.append("express")
            else:
                recommendations.append("fastapi")  # Default preference
        
        elif project_type == "cli_tool":
            if "python" in tech_hints:
                recommendations.append("click")
            elif "node.js" in tech_hints:
                recommendations.append("commander.js")
            else:
                recommendations.append("click")  # Default preference
        
        return recommendations
    
    async def generate_scaffolding_recommendation(self, analysis: DesignDocAnalysis) -> ScaffoldingRecommendation:
        """
        Generate a scaffolding recommendation based on design document analysis.
        
        Args:
            analysis: Results from design document analysis
            
        Returns:
            ScaffoldingRecommendation with suggested approach
        """
        try:
            # Determine primary technology stack
            primary_tech = self._determine_primary_technology(analysis)
            
            # Load appropriate template
            template = self._load_template(primary_tech, analysis.project_type)
            
            # Generate recommendation
            recommendation = ScaffoldingRecommendation(
                tech_stack=template.get("tech_stack", {}),
                project_structure=template.get("project_structure", {}),
                dependencies=template.get("dependencies", {}),
                reasoning=self._generate_reasoning(analysis, template),
                confidence_score=self._calculate_confidence_score(analysis, template),
                template_used=template.get("name", "Unknown"),
                approval_required=self._requires_approval(analysis),
                concerns=self._identify_concerns(analysis, template)
            )
            
            # Store recommendation in memory
            await self.memory_manager.store_memory(
                agent_id=self.agent_id,
                category="SCAFFOLDING_PATTERN",
                content=f"Scaffolding recommendation: {recommendation.template_used}",
                context={"recommendation": recommendation.__dict__}
            )
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error generating scaffolding recommendation: {e}")
            raise
    
    def _determine_primary_technology(self, analysis: DesignDocAnalysis) -> str:
        """Determine primary technology stack"""
        tech_hints = analysis.technology_hints
        
        if any(hint in tech_hints for hint in ["typescript", "javascript", "react", "nextjs"]):
            return "typescript"
        elif any(hint in tech_hints for hint in ["python", "fastapi", "django", "flask"]):
            return "python"
        else:
            # Default based on project type
            if analysis.project_type == "web_application":
                return "typescript"
            elif analysis.project_type in ["api_service", "cli_tool"]:
                return "python"
            else:
                return "typescript"  # Default
    
    def _load_template(self, technology: str, project_type: str) -> Dict[str, Any]:
        """Load appropriate scaffolding template"""
        template_file = None
        
        if technology == "typescript":
            if project_type == "web_application":
                template_file = self.templates_path / "typescript" / "nextjs-template.json"
        elif technology == "python":
            if project_type == "api_service":
                template_file = self.templates_path / "python" / "fastapi-template.json"
        
        if template_file and template_file.exists():
            with open(template_file, 'r') as f:
                return json.load(f)
        
        # Fallback to basic template
        return {
            "name": f"Basic {technology} Project",
            "tech_stack": self.framework_preferences.get(technology, {}),
            "project_structure": {"root": ["README.md", ".gitignore"]},
            "dependencies": {"production": {}, "development": {}}
        }
    
    def _generate_reasoning(self, analysis: DesignDocAnalysis, template: Dict[str, Any]) -> str:
        """Generate reasoning for the scaffolding recommendation"""
        reasoning_parts = [
            f"Project type: {analysis.project_type}",
            f"Complexity score: {analysis.complexity_score:.2f}",
            f"Technology stack: {template.get('name', 'Unknown')}",
            f"Requirements count: {len(analysis.requirements)}"
        ]
        
        if analysis.constraints:
            reasoning_parts.append(f"Constraints identified: {len(analysis.constraints)}")
        
        return ". ".join(reasoning_parts)
    
    def _calculate_confidence_score(self, analysis: DesignDocAnalysis, template: Dict[str, Any]) -> float:
        """Calculate confidence score for the recommendation"""
        base_score = 0.7  # Base confidence
        
        # Adjust based on technology hints match
        if analysis.technology_hints:
            tech_match = any(hint in template.get("tech_stack", {}) for hint in analysis.technology_hints)
            if tech_match:
                base_score += 0.2
        
        # Adjust based on complexity appropriateness
        if analysis.complexity_score < 0.5:
            base_score += 0.1  # Simple projects are easier to recommend for
        
        return min(base_score, 1.0)
    
    def _requires_approval(self, analysis: DesignDocAnalysis) -> bool:
        """Determine if PM approval is required"""
        return (
            analysis.complexity_score > 0.7 or
            len(analysis.constraints) > 3 or
            any(constraint.lower() in ["security", "performance", "scalability"] 
                for constraint in analysis.constraints)
        )
    
    def _identify_concerns(self, analysis: DesignDocAnalysis, template: Dict[str, Any]) -> List[str]:
        """Identify potential concerns with the recommendation"""
        concerns = []
        
        if analysis.complexity_score > 0.8:
            concerns.append("High complexity project may require additional architectural consideration")
        
        if not analysis.technology_hints:
            concerns.append("No specific technology preferences identified in requirements")
        
        if len(analysis.constraints) > 5:
            concerns.append("Multiple constraints may require custom configuration")
        
        return concerns
    
    async def suggest_to_pm(self, recommendation: ScaffoldingRecommendation, analysis: DesignDocAnalysis) -> str:
        """
        Suggest scaffolding approach to PM for approval.
        
        Args:
            recommendation: The scaffolding recommendation
            analysis: The design document analysis
            
        Returns:
            Suggestion message for PM
        """
        suggestion = f"""
## Scaffolding Recommendation

**Project Type:** {analysis.project_type}
**Template:** {recommendation.template_used}
**Confidence:** {recommendation.confidence_score:.1%}

### Technology Stack
- **Framework:** {recommendation.tech_stack.get('framework', 'TBD')}
- **Language:** {recommendation.tech_stack.get('language', 'TBD')}
- **Build Tools:** {recommendation.tech_stack.get('build_tools', 'TBD')}

### Reasoning
{recommendation.reasoning}

### Approval Required
{"Yes" if recommendation.approval_required else "No"}

### Concerns
{chr(10).join(f"- {concern}" for concern in recommendation.concerns) if recommendation.concerns else "None identified"}

### Next Steps
{"Awaiting PM approval before proceeding" if recommendation.approval_required else "Ready to proceed with scaffolding"}
        """
        
        # Create tracking ticket
        await self.trackdown_service.create_task(
            title=f"Scaffolding: {recommendation.template_used}",
            description=suggestion,
            priority="high" if recommendation.approval_required else "medium",
            labels=["scaffolding", "architecture", analysis.project_type]
        )
        
        return suggestion.strip()
    
    async def implement_scaffolding(self, recommendation: ScaffoldingRecommendation, project_path: str) -> bool:
        """
        Implement the approved scaffolding.
        
        Args:
            recommendation: The approved scaffolding recommendation
            project_path: Path where to create the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            project_dir = Path(project_path)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project structure
            self._create_project_structure(project_dir, recommendation.project_structure)
            
            # Generate configuration files
            self._generate_configuration_files(project_dir, recommendation)
            
            # Create basic files
            self._create_basic_files(project_dir, recommendation)
            
            # Store successful scaffolding pattern
            await self.memory_manager.store_memory(
                agent_id=self.agent_id,
                category="SCAFFOLDING_PATTERN",
                content=f"Successfully scaffolded {recommendation.template_used}",
                context={"project_path": project_path, "template": recommendation.template_used}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error implementing scaffolding: {e}")
            return False
    
    def _create_project_structure(self, project_dir: Path, structure: Dict[str, Any]):
        """Create the project directory structure"""
        for item_name, item_value in structure.items():
            item_path = project_dir / item_name
            
            if isinstance(item_value, dict):
                # Directory with subdirectories
                item_path.mkdir(exist_ok=True)
                self._create_project_structure(item_path, item_value)
            elif isinstance(item_value, list):
                # Directory with files
                item_path.mkdir(exist_ok=True)
                for file_name in item_value:
                    if file_name.endswith('/'):
                        # Subdirectory
                        (item_path / file_name.rstrip('/')).mkdir(exist_ok=True)
                    else:
                        # File
                        (item_path / file_name).touch()
    
    def _generate_configuration_files(self, project_dir: Path, recommendation: ScaffoldingRecommendation):
        """Generate configuration files based on the recommendation"""
        # This would generate actual configuration files
        # For now, just create placeholder files
        config_files = [
            "package.json" if "javascript" in recommendation.tech_stack.get("language", "") else "pyproject.toml",
            ".gitignore",
            "README.md"
        ]
        
        for config_file in config_files:
            (project_dir / config_file).touch()
    
    def _create_basic_files(self, project_dir: Path, recommendation: ScaffoldingRecommendation):
        """Create basic application files"""
        # This would create actual starter files
        # For now, just create placeholder files
        pass