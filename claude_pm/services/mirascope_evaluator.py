"""
Mirascope Evaluation Integration
===============================

This service integrates Mirascope for automatic prompt evaluation and assessment.
It provides comprehensive evaluation metrics for agent responses, focusing on:
- Correctness, Relevance, Completeness, Clarity, and Helpfulness
- Performance optimization with caching and async processing
- Integration with existing correction capture system

Key Features:
- Automatic response evaluation using Mirascope
- Comprehensive scoring system (0-100 scale)
- Integration with correction capture data
- Performance optimization with caching
- Async evaluation processing
- Configurable evaluation criteria and providers

Implementation Notes:
- Uses Mirascope as lightweight alternative to LangChain
- Integrates with existing OpenAI/Claude API systems
- Target performance: <100ms evaluation overhead
- Designed for all agent types (Engineer, QA, Ops, etc.)
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
import hashlib
import uuid

from claude_pm.core.config import Config
from claude_pm.services.correction_capture import CorrectionData, CorrectionType

logger = logging.getLogger(__name__)

# Try to import Mirascope components
try:
    from mirascope.anthropic import AnthropicCall
    from mirascope.openai import OpenAICall
    from mirascope.core import BaseCallResponse, BaseModel
    from pydantic import BaseModel as PydanticBaseModel
    MIRASCOPE_AVAILABLE = True
except ImportError:
    logger.warning("Mirascope not available. Install with: pip install mirascope")
    MIRASCOPE_AVAILABLE = False
    # Fallback classes for type hints
    class AnthropicCall: pass
    class OpenAICall: pass
    class BaseCallResponse: pass
    class PydanticBaseModel: pass


class EvaluationProvider(Enum):
    """Supported evaluation providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AUTO = "auto"  # Automatically choose based on available API keys


class EvaluationCriteria(Enum):
    """Evaluation criteria for response assessment."""
    CORRECTNESS = "correctness"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    HELPFULNESS = "helpfulness"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"


@dataclass
class EvaluationScore:
    """Individual evaluation score for a specific criterion."""
    criterion: EvaluationCriteria
    score: float  # 0-100 scale
    explanation: str
    confidence: float  # 0-1 scale
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EvaluationResult:
    """Complete evaluation result for a response."""
    evaluation_id: str
    agent_type: str
    response_text: str
    context: Dict[str, Any]
    overall_score: float  # 0-100 scale
    criterion_scores: List[EvaluationScore]
    evaluation_time_ms: float
    provider: EvaluationProvider
    correction_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['provider'] = self.provider.value
        data['criterion_scores'] = [
            {
                **asdict(score),
                'criterion': score.criterion.value
            }
            for score in self.criterion_scores
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create from dictionary."""
        data['provider'] = EvaluationProvider(data['provider'])
        data['criterion_scores'] = [
            EvaluationScore(
                criterion=EvaluationCriteria(score_data['criterion']),
                score=score_data['score'],
                explanation=score_data['explanation'],
                confidence=score_data['confidence'],
                timestamp=score_data['timestamp']
            )
            for score_data in data['criterion_scores']
        ]
        return cls(**data)


@dataclass
class EvaluationConfig:
    """Configuration for evaluation system."""
    provider: EvaluationProvider = EvaluationProvider.AUTO
    criteria: List[EvaluationCriteria] = field(default_factory=lambda: [
        EvaluationCriteria.CORRECTNESS,
        EvaluationCriteria.RELEVANCE,
        EvaluationCriteria.COMPLETENESS,
        EvaluationCriteria.CLARITY,
        EvaluationCriteria.HELPFULNESS
    ])
    enable_caching: bool = True
    cache_ttl_hours: int = 24
    max_concurrent_evaluations: int = 10
    timeout_seconds: int = 30
    enable_async_processing: bool = True
    batch_size: int = 5
    model_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.criteria:
            self.criteria = [EvaluationCriteria.CORRECTNESS]


class EvaluationPrompt(PydanticBaseModel):
    """Structured evaluation prompt for Mirascope."""
    task_context: str
    agent_response: str
    evaluation_criteria: List[str]
    expected_format: str


class MirascopeEvaluator:
    """
    Mirascope-based evaluation system for agent responses.
    
    Provides comprehensive evaluation using multiple criteria and
    integrates with the correction capture system.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Mirascope evaluator.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("enable_evaluation", True) and MIRASCOPE_AVAILABLE
        
        if not MIRASCOPE_AVAILABLE:
            logger.warning("Mirascope not available. Evaluation system disabled.")
            self.enabled = False
            return
            
        self.evaluation_config = self._create_evaluation_config()
        self.cache: Dict[str, EvaluationResult] = {}
        self.session_id = str(uuid.uuid4())
        
        # Initialize storage
        self.storage_path = Path(self.config.get("evaluation_storage_path", "~/.claude-pm/training")).expanduser()
        self.evaluations_dir = self.storage_path / "evaluations"
        self.evaluations_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize provider
        self.provider = self._initialize_provider()
        
        # Performance tracking
        self.evaluation_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        if self.enabled:
            logger.info(f"Mirascope evaluator initialized with provider: {self.provider}")
        else:
            logger.info("Mirascope evaluator disabled")
    
    def _create_evaluation_config(self) -> EvaluationConfig:
        """Create evaluation configuration from main config."""
        provider_str = self.config.get("evaluation_provider", "auto")
        try:
            provider = EvaluationProvider(provider_str)
        except ValueError:
            logger.warning(f"Invalid evaluation provider: {provider_str}, using AUTO")
            provider = EvaluationProvider.AUTO
        
        criteria_list = self.config.get("evaluation_criteria", [
            "correctness", "relevance", "completeness", "clarity", "helpfulness"
        ])
        
        try:
            criteria = [EvaluationCriteria(c) for c in criteria_list]
        except ValueError as e:
            logger.warning(f"Invalid evaluation criteria: {e}, using defaults")
            criteria = [EvaluationCriteria.CORRECTNESS, EvaluationCriteria.RELEVANCE]
        
        return EvaluationConfig(
            provider=provider,
            criteria=criteria,
            enable_caching=self.config.get("evaluation_caching_enabled", True),
            cache_ttl_hours=self.config.get("evaluation_cache_ttl_hours", 24),
            max_concurrent_evaluations=self.config.get("evaluation_max_concurrent", 10),
            timeout_seconds=self.config.get("evaluation_timeout_seconds", 30),
            enable_async_processing=self.config.get("evaluation_async_enabled", True),
            batch_size=self.config.get("evaluation_batch_size", 5),
            model_config=self.config.get("evaluation_model_config", {})
        )
    
    def _initialize_provider(self) -> EvaluationProvider:
        """Initialize evaluation provider based on configuration."""
        if self.evaluation_config.provider == EvaluationProvider.AUTO:
            # Auto-detect based on available API keys
            openai_key = self.config.get("openai_api_key") or self.config.get("OPENAI_API_KEY")
            anthropic_key = self.config.get("anthropic_api_key") or self.config.get("ANTHROPIC_API_KEY")
            
            if anthropic_key:
                return EvaluationProvider.ANTHROPIC
            elif openai_key:
                return EvaluationProvider.OPENAI
            else:
                logger.warning("No API keys found for evaluation providers. Using OpenAI as fallback.")
                return EvaluationProvider.OPENAI
        else:
            return self.evaluation_config.provider
    
    def _generate_cache_key(self, agent_type: str, response_text: str, context: Dict[str, Any]) -> str:
        """Generate cache key for evaluation result."""
        # Create deterministic hash from inputs
        content = f"{agent_type}:{response_text}:{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[EvaluationResult]:
        """Get cached evaluation result if available and valid."""
        if not self.evaluation_config.enable_caching:
            return None
        
        if cache_key not in self.cache:
            return None
        
        result = self.cache[cache_key]
        
        # Check if cache entry is still valid
        cache_time = datetime.fromisoformat(result.timestamp)
        ttl = timedelta(hours=self.evaluation_config.cache_ttl_hours)
        
        if datetime.now() - cache_time > ttl:
            # Remove expired entry
            del self.cache[cache_key]
            return None
        
        self.cache_hits += 1
        return result
    
    def _cache_result(self, cache_key: str, result: EvaluationResult) -> None:
        """Cache evaluation result."""
        if self.evaluation_config.enable_caching:
            self.cache[cache_key] = result
    
    async def _create_evaluation_call(self, prompt: EvaluationPrompt) -> Union[AnthropicCall, OpenAICall]:
        """Create appropriate evaluation call based on provider."""
        if self.provider == EvaluationProvider.ANTHROPIC:
            return AnthropicCall(
                model=self.evaluation_config.model_config.get("anthropic_model", "claude-3-haiku-20240307"),
                messages=[{
                    "role": "user",
                    "content": self._create_evaluation_prompt(prompt)
                }]
            )
        else:  # OpenAI
            return OpenAICall(
                model=self.evaluation_config.model_config.get("openai_model", "gpt-4o-mini"),
                messages=[{
                    "role": "user",
                    "content": self._create_evaluation_prompt(prompt)
                }]
            )
    
    def _create_evaluation_prompt(self, prompt: EvaluationPrompt) -> str:
        """Create evaluation prompt text."""
        criteria_text = ", ".join(prompt.evaluation_criteria)
        
        return f"""
You are an expert evaluator for AI agent responses. Evaluate the following agent response based on these criteria: {criteria_text}.

TASK CONTEXT:
{prompt.task_context}

AGENT RESPONSE TO EVALUATE:
{prompt.agent_response}

EVALUATION INSTRUCTIONS:
For each criterion, provide:
1. A score from 0-100 (where 100 is perfect)
2. A brief explanation of the score
3. A confidence level from 0-1 (how confident you are in this score)

{prompt.expected_format}

Please provide a structured evaluation focusing on practical utility and accuracy.
"""
    
    def _parse_evaluation_response(self, response_text: str, agent_type: str, original_response: str, context: Dict[str, Any]) -> EvaluationResult:
        """Parse evaluation response into structured result."""
        # This is a simplified parser - in practice, you'd want more robust parsing
        # or use Mirascope's structured output features
        
        evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Basic score extraction (this would be more sophisticated in practice)
        scores = []
        overall_score = 75.0  # Default fallback
        
        try:
            # Parse the response text to extract scores
            # This is a simplified implementation - you'd want more robust parsing
            lines = response_text.split('\n')
            current_criterion = None
            current_score = None
            current_explanation = ""
            current_confidence = 0.8
            
            for line in lines:
                line = line.strip()
                if any(crit.value in line.lower() for crit in self.evaluation_config.criteria):
                    if current_criterion and current_score is not None:
                        # Save previous criterion
                        scores.append(EvaluationScore(
                            criterion=current_criterion,
                            score=current_score,
                            explanation=current_explanation,
                            confidence=current_confidence
                        ))
                    
                    # Start new criterion
                    for crit in self.evaluation_config.criteria:
                        if crit.value in line.lower():
                            current_criterion = crit
                            break
                    
                    # Try to extract score from line
                    import re
                    score_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if score_match:
                        current_score = float(score_match.group(1))
                        if current_score > 100:
                            current_score = min(current_score, 100)
                    
                elif current_criterion and 'explanation' in line.lower():
                    current_explanation = line.replace('explanation:', '').strip()
                elif current_criterion and 'confidence' in line.lower():
                    conf_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if conf_match:
                        current_confidence = float(conf_match.group(1))
                        if current_confidence > 1:
                            current_confidence = current_confidence / 100
            
            # Don't forget the last criterion
            if current_criterion and current_score is not None:
                scores.append(EvaluationScore(
                    criterion=current_criterion,
                    score=current_score,
                    explanation=current_explanation,
                    confidence=current_confidence
                ))
            
            # Calculate overall score
            if scores:
                overall_score = sum(score.score for score in scores) / len(scores)
            
        except Exception as e:
            logger.error(f"Error parsing evaluation response: {e}")
            # Fallback to basic scores
            for criterion in self.evaluation_config.criteria:
                scores.append(EvaluationScore(
                    criterion=criterion,
                    score=75.0,
                    explanation="Automatic fallback score due to parsing error",
                    confidence=0.5
                ))
        
        return EvaluationResult(
            evaluation_id=evaluation_id,
            agent_type=agent_type,
            response_text=original_response,
            context=context,
            overall_score=overall_score,
            criterion_scores=scores,
            evaluation_time_ms=0,  # Will be set by caller
            provider=self.provider
        )
    
    async def evaluate_response(
        self,
        agent_type: str,
        response_text: str,
        context: Dict[str, Any],
        correction_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate agent response using Mirascope.
        
        Args:
            agent_type: Type of agent that produced the response
            response_text: The response to evaluate
            context: Context information about the task
            correction_id: Optional correction ID if this is from a correction
            
        Returns:
            Evaluation result
        """
        if not self.enabled:
            logger.debug("Evaluation disabled, returning mock result")
            return self._create_mock_result(agent_type, response_text, context)
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(agent_type, response_text, context)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result:
                logger.debug(f"Using cached evaluation result for {agent_type}")
                return cached_result
            
            self.cache_misses += 1
            
            # Create evaluation prompt
            task_description = context.get("task_description", "No task description provided")
            criteria_names = [crit.value for crit in self.evaluation_config.criteria]
            
            prompt = EvaluationPrompt(
                task_context=task_description,
                agent_response=response_text,
                evaluation_criteria=criteria_names,
                expected_format="Provide scores and explanations for each criterion."
            )
            
            # Create and execute evaluation call
            call = await self._create_evaluation_call(prompt)
            response = await call.call()
            
            # Parse response
            result = self._parse_evaluation_response(
                response.content,
                agent_type,
                response_text,
                context
            )
            
            # Set timing and correction ID
            evaluation_time = (time.time() - start_time) * 1000
            result.evaluation_time_ms = evaluation_time
            result.correction_id = correction_id
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Store result
            await self._store_evaluation_result(result)
            
            # Track performance
            self.evaluation_times.append(evaluation_time)
            
            logger.info(f"Evaluated {agent_type} response in {evaluation_time:.2f}ms (score: {result.overall_score:.1f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed for {agent_type}: {e}")
            evaluation_time = (time.time() - start_time) * 1000
            
            # Return fallback result
            result = self._create_mock_result(agent_type, response_text, context)
            result.evaluation_time_ms = evaluation_time
            result.correction_id = correction_id
            
            return result
    
    def _create_mock_result(self, agent_type: str, response_text: str, context: Dict[str, Any]) -> EvaluationResult:
        """Create mock evaluation result when evaluation is disabled or fails."""
        evaluation_id = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        scores = []
        for criterion in self.evaluation_config.criteria:
            scores.append(EvaluationScore(
                criterion=criterion,
                score=75.0,
                explanation="Mock evaluation - system disabled or failed",
                confidence=0.5
            ))
        
        return EvaluationResult(
            evaluation_id=evaluation_id,
            agent_type=agent_type,
            response_text=response_text,
            context=context,
            overall_score=75.0,
            criterion_scores=scores,
            evaluation_time_ms=0,
            provider=self.provider
        )
    
    async def _store_evaluation_result(self, result: EvaluationResult) -> None:
        """Store evaluation result to file."""
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{result.agent_type}_eval_{timestamp}_{result.evaluation_id}.json"
            
            # Store in evaluations directory
            eval_file = self.evaluations_dir / filename
            
            # Write evaluation data
            with open(eval_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.debug(f"Stored evaluation result to {eval_file}")
            
        except Exception as e:
            logger.error(f"Failed to store evaluation result: {e}")
    
    async def evaluate_correction(self, correction_data: CorrectionData) -> EvaluationResult:
        """
        Evaluate a correction from the correction capture system.
        
        Args:
            correction_data: Correction data to evaluate
            
        Returns:
            Evaluation result
        """
        context = correction_data.context.copy()
        context["correction_type"] = correction_data.correction_type.value
        context["user_correction"] = correction_data.user_correction
        context["original_response"] = correction_data.original_response
        
        return await self.evaluate_response(
            agent_type=correction_data.agent_type,
            response_text=correction_data.original_response,
            context=context,
            correction_id=correction_data.correction_id
        )
    
    async def batch_evaluate_corrections(self, corrections: List[CorrectionData]) -> List[EvaluationResult]:
        """
        Batch evaluate multiple corrections.
        
        Args:
            corrections: List of corrections to evaluate
            
        Returns:
            List of evaluation results
        """
        if not corrections:
            return []
        
        results = []
        
        if self.evaluation_config.enable_async_processing:
            # Process in batches to avoid overwhelming the API
            batch_size = self.evaluation_config.batch_size
            
            for i in range(0, len(corrections), batch_size):
                batch = corrections[i:i + batch_size]
                
                # Create evaluation tasks
                tasks = [self.evaluate_correction(correction) for correction in batch]
                
                # Run batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch evaluation error: {result}")
                    else:
                        results.append(result)
                
                # Add small delay between batches
                if i + batch_size < len(corrections):
                    await asyncio.sleep(0.1)
        else:
            # Sequential processing
            for correction in corrections:
                try:
                    result = await self.evaluate_correction(correction)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Sequential evaluation error: {e}")
        
        logger.info(f"Batch evaluated {len(results)} corrections")
        return results
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """Get statistics about evaluation performance."""
        if not self.evaluation_times:
            return {
                "total_evaluations": 0,
                "average_time_ms": 0,
                "cache_hit_rate": 0,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "enabled": self.enabled
            }
        
        return {
            "total_evaluations": len(self.evaluation_times),
            "average_time_ms": sum(self.evaluation_times) / len(self.evaluation_times),
            "min_time_ms": min(self.evaluation_times),
            "max_time_ms": max(self.evaluation_times),
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(self.cache),
            "enabled": self.enabled,
            "provider": self.provider.value,
            "criteria_count": len(self.evaluation_config.criteria)
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear evaluation cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        
        return {
            "cache_cleared": True,
            "entries_removed": cache_size,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_evaluations(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old evaluation files.
        
        Args:
            days_to_keep: Number of days to keep evaluations
            
        Returns:
            Cleanup summary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            removed_files = []
            total_size_removed = 0
            
            if self.evaluations_dir.exists():
                for eval_file in self.evaluations_dir.glob("*.json"):
                    try:
                        # Check file modification time
                        file_time = datetime.fromtimestamp(eval_file.stat().st_mtime)
                        
                        if file_time < cutoff_date:
                            file_size = eval_file.stat().st_size
                            eval_file.unlink()
                            removed_files.append(str(eval_file))
                            total_size_removed += file_size
                            
                    except Exception as e:
                        logger.error(f"Failed to process {eval_file}: {e}")
            
            logger.info(f"Evaluation cleanup completed: removed {len(removed_files)} files, {total_size_removed} bytes")
            
            return {
                "removed_files": len(removed_files),
                "total_size_removed": total_size_removed,
                "cutoff_date": cutoff_date.isoformat(),
                "files_removed": removed_files if len(removed_files) < 20 else removed_files[:20] + ["..."]
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old evaluations: {e}")
            return {"error": str(e)}


# Helper functions for easy integration
async def evaluate_agent_response(
    agent_type: str,
    response_text: str,
    context: Dict[str, Any],
    config: Optional[Config] = None
) -> EvaluationResult:
    """
    Quick evaluation of agent response.
    
    Args:
        agent_type: Type of agent
        response_text: Response to evaluate
        context: Task context
        config: Optional configuration
        
    Returns:
        Evaluation result
    """
    evaluator = MirascopeEvaluator(config)
    return await evaluator.evaluate_response(agent_type, response_text, context)


async def evaluate_correction_data(
    correction_data: CorrectionData,
    config: Optional[Config] = None
) -> EvaluationResult:
    """
    Evaluate correction data.
    
    Args:
        correction_data: Correction to evaluate
        config: Optional configuration
        
    Returns:
        Evaluation result
    """
    evaluator = MirascopeEvaluator(config)
    return await evaluator.evaluate_correction(correction_data)


def initialize_evaluation_system(config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize the evaluation system and return status."""
    try:
        evaluator = MirascopeEvaluator(config)
        stats = evaluator.get_evaluation_statistics()
        
        return {
            "initialized": True,
            "enabled": evaluator.enabled,
            "provider": evaluator.provider.value if evaluator.enabled else "none",
            "storage_path": str(evaluator.storage_path),
            "statistics": stats,
            "mirascope_available": MIRASCOPE_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize evaluation system: {e}")
        return {"initialized": False, "error": str(e)}


if __name__ == "__main__":
    # Test the evaluation system
    print("Testing Mirascope Evaluation System")
    print("=" * 50)
    
    # Initialize system
    init_result = initialize_evaluation_system()
    print(f"Initialization: {init_result['initialized']}")
    print(f"Enabled: {init_result['enabled']}")
    print(f"Provider: {init_result['provider']}")
    print(f"Mirascope Available: {init_result['mirascope_available']}")
    
    if init_result['initialized']:
        # Test evaluation
        async def test_evaluation():
            result = await evaluate_agent_response(
                agent_type="engineer",
                response_text="def hello(): print('Hello, World!')",
                context={
                    "task_description": "Create a hello function",
                    "agent_type": "engineer"
                }
            )
            
            print(f"Evaluation ID: {result.evaluation_id}")
            print(f"Overall Score: {result.overall_score:.1f}")
            print(f"Evaluation Time: {result.evaluation_time_ms:.2f}ms")
            print(f"Criteria Scores: {len(result.criterion_scores)}")
            
            for score in result.criterion_scores:
                print(f"  {score.criterion.value}: {score.score:.1f} ({score.explanation})")
        
        # Run async test
        asyncio.run(test_evaluation())
    else:
        print(f"Initialization failed: {init_result.get('error', 'Unknown error')}")