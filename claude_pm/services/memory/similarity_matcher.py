"""
Similarity Matcher

This module implements semantic and pattern-based memory matching for intelligent
memory retrieval. It provides multiple similarity algorithms and ranking strategies
to find the most relevant memories for any given context.
"""

import re
import math
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import Counter

from .interfaces.models import MemoryItem, MemoryCategory


class SimilarityAlgorithm(str, Enum):
    """Available similarity algorithms."""

    COSINE = "cosine"  # Cosine similarity with TF-IDF
    JACCARD = "jaccard"  # Jaccard similarity for sets
    LEVENSHTEIN = "levenshtein"  # Edit distance similarity
    SEMANTIC = "semantic"  # Semantic similarity (embeddings)
    PATTERN = "pattern"  # Pattern-based matching
    HYBRID = "hybrid"  # Combination of multiple algorithms


@dataclass
class SimilarityResult:
    """Result of similarity matching."""

    memory_id: str
    similarity_score: float
    algorithm_used: SimilarityAlgorithm
    match_details: Dict[str, Any]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "memory_id": self.memory_id,
            "similarity_score": self.similarity_score,
            "algorithm_used": self.algorithm_used.value,
            "match_details": self.match_details,
            "confidence": self.confidence,
        }


@dataclass
class MatchingConfig:
    """Configuration for similarity matching."""

    default_algorithm: SimilarityAlgorithm = SimilarityAlgorithm.HYBRID
    min_similarity_threshold: float = 0.1
    max_similarity_threshold: float = 1.0
    enable_fuzzy_matching: bool = True
    enable_stemming: bool = True
    enable_stop_word_removal: bool = True
    pattern_weight: float = 0.3
    semantic_weight: float = 0.4
    text_weight: float = 0.3
    category_boost: float = 0.1  # Boost for same category matches
    tag_boost: float = 0.15  # Boost for tag matches
    temporal_decay: float = 0.02  # Decay factor for older memories

    def validate(self):
        """Validate configuration values."""
        if not (0.0 <= self.min_similarity_threshold <= 1.0):
            raise ValueError("min_similarity_threshold must be between 0.0 and 1.0")

        if not (0.0 <= self.max_similarity_threshold <= 1.0):
            raise ValueError("max_similarity_threshold must be between 0.0 and 1.0")

        if self.min_similarity_threshold > self.max_similarity_threshold:
            raise ValueError(
                "min_similarity_threshold cannot be greater than max_similarity_threshold"
            )

        weights_sum = self.pattern_weight + self.semantic_weight + self.text_weight
        if not (0.8 <= weights_sum <= 1.2):  # Allow some tolerance
            raise ValueError("Pattern, semantic, and text weights should sum to approximately 1.0")


class SimilarityMatcher:
    """
    Advanced similarity matching for memory retrieval.

    This class implements multiple similarity algorithms to find relevant memories
    based on content, patterns, semantic meaning, and context. It provides
    flexible ranking and filtering capabilities for optimal memory retrieval.
    """

    def __init__(self, config: Optional[MatchingConfig] = None):
        """
        Initialize the similarity matcher.

        Args:
            config: Configuration for matching algorithms
        """
        self.config = config or MatchingConfig()
        self.config.validate()
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self.matching_stats = {
            "total_matches": 0,
            "matches_by_algorithm": {algo.value: 0 for algo in SimilarityAlgorithm},
            "average_match_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Simple cache for computed similarities
        self._similarity_cache: Dict[str, float] = {}
        self._cache_max_size = 10000

        # Pre-compiled regex patterns for text processing
        self._word_pattern = re.compile(r"\b\w+\b", re.IGNORECASE)
        self._stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "will",
            "with",
            "the",
            "this",
            "but",
            "they",
            "have",
            "had",
            "what",
            "said",
            "each",
            "which",
            "their",
            "time",
            "if",
        }

    def calculate_similarity(
        self,
        query_text: str,
        memory: MemoryItem,
        query_context: Optional[Dict[str, Any]] = None,
        algorithm: Optional[SimilarityAlgorithm] = None,
    ) -> SimilarityResult:
        """
        Calculate similarity between query and memory.

        Args:
            query_text: Text to match against
            memory: Memory item to compare
            query_context: Additional context for matching
            algorithm: Specific algorithm to use (uses default if None)

        Returns:
            SimilarityResult: Similarity calculation result
        """
        algorithm = algorithm or self.config.default_algorithm
        self.matching_stats["total_matches"] += 1
        self.matching_stats["matches_by_algorithm"][algorithm.value] += 1

        # Check cache first
        cache_key = self._generate_cache_key(query_text, memory, algorithm)
        if cache_key in self._similarity_cache:
            self.matching_stats["cache_hits"] += 1
            return SimilarityResult(
                memory_id=memory.id,
                similarity_score=self._similarity_cache[cache_key],
                algorithm_used=algorithm,
                match_details={"cached": True},
                confidence=0.8,
            )

        self.matching_stats["cache_misses"] += 1

        # Calculate similarity based on algorithm
        if algorithm == SimilarityAlgorithm.COSINE:
            result = self._calculate_cosine_similarity(query_text, memory, query_context)
        elif algorithm == SimilarityAlgorithm.JACCARD:
            result = self._calculate_jaccard_similarity(query_text, memory, query_context)
        elif algorithm == SimilarityAlgorithm.LEVENSHTEIN:
            result = self._calculate_levenshtein_similarity(query_text, memory, query_context)
        elif algorithm == SimilarityAlgorithm.SEMANTIC:
            result = self._calculate_semantic_similarity(query_text, memory, query_context)
        elif algorithm == SimilarityAlgorithm.PATTERN:
            result = self._calculate_pattern_similarity(query_text, memory, query_context)
        elif algorithm == SimilarityAlgorithm.HYBRID:
            result = self._calculate_hybrid_similarity(query_text, memory, query_context)
        else:
            # Fallback to cosine similarity
            result = self._calculate_cosine_similarity(query_text, memory, query_context)

        # Cache the result
        self._cache_similarity(cache_key, result.similarity_score)

        return result

    def rank_memories_by_similarity(
        self,
        query_text: str,
        memories: List[MemoryItem],
        query_context: Optional[Dict[str, Any]] = None,
        algorithm: Optional[SimilarityAlgorithm] = None,
        limit: int = 10,
    ) -> List[Tuple[MemoryItem, SimilarityResult]]:
        """
        Rank memories by similarity to query.

        Args:
            query_text: Text to match against
            memories: List of memories to rank
            query_context: Additional context for matching
            algorithm: Specific algorithm to use
            limit: Maximum number of results to return

        Returns:
            List[Tuple[MemoryItem, SimilarityResult]]: Ranked memories with scores
        """
        results = []

        for memory in memories:
            similarity_result = self.calculate_similarity(
                query_text, memory, query_context, algorithm
            )

            # Apply thresholds
            if (
                self.config.min_similarity_threshold
                <= similarity_result.similarity_score
                <= self.config.max_similarity_threshold
            ):
                results.append((memory, similarity_result))

        # Sort by similarity score (descending)
        results.sort(key=lambda x: x[1].similarity_score, reverse=True)

        return results[:limit]

    def find_similar_patterns(
        self,
        memory: MemoryItem,
        candidate_memories: List[MemoryItem],
        pattern_threshold: float = 0.7,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Find memories with similar patterns to the given memory.

        Args:
            memory: Reference memory to find patterns for
            candidate_memories: List of memories to search through
            pattern_threshold: Minimum pattern similarity threshold

        Returns:
            List[Tuple[MemoryItem, float]]: Memories with pattern similarity scores
        """
        similar_patterns = []

        for candidate in candidate_memories:
            if candidate.id == memory.id:
                continue

            # Calculate pattern similarity
            pattern_score = self._calculate_pattern_match_score(memory, candidate)

            if pattern_score >= pattern_threshold:
                similar_patterns.append((candidate, pattern_score))

        # Sort by pattern score (descending)
        similar_patterns.sort(key=lambda x: x[1], reverse=True)

        return similar_patterns

    def _calculate_cosine_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """Calculate cosine similarity using TF-IDF."""
        # Tokenize and process text
        query_tokens = self._tokenize_text(query_text)
        memory_tokens = self._tokenize_text(memory.content)

        # Create TF-IDF vectors
        all_tokens = set(query_tokens + memory_tokens)

        query_tf = self._calculate_tf(query_tokens)
        memory_tf = self._calculate_tf(memory_tokens)

        # Calculate IDF (simplified - using just these two documents)
        idf = {}
        for token in all_tokens:
            doc_freq = sum([1 for tokens in [query_tokens, memory_tokens] if token in tokens])
            idf[token] = math.log(2 / doc_freq) if doc_freq > 0 else 0

        # Create TF-IDF vectors
        query_vector = [query_tf.get(token, 0) * idf[token] for token in all_tokens]
        memory_vector = [memory_tf.get(token, 0) * idf[token] for token in all_tokens]

        # Calculate cosine similarity
        dot_product = sum(q * m for q, m in zip(query_vector, memory_vector))
        query_magnitude = math.sqrt(sum(q * q for q in query_vector))
        memory_magnitude = math.sqrt(sum(m * m for m in memory_vector))

        if query_magnitude == 0 or memory_magnitude == 0:
            similarity = 0.0
        else:
            similarity = dot_product / (query_magnitude * memory_magnitude)

        # Apply boosts
        similarity = self._apply_boosts(similarity, query_text, memory, query_context)

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(similarity, 1.0),
            algorithm_used=SimilarityAlgorithm.COSINE,
            match_details={
                "query_tokens": len(query_tokens),
                "memory_tokens": len(memory_tokens),
                "common_tokens": len(set(query_tokens) & set(memory_tokens)),
            },
            confidence=0.8,
        )

    def _calculate_jaccard_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """Calculate Jaccard similarity for sets."""
        query_tokens = set(self._tokenize_text(query_text))
        memory_tokens = set(self._tokenize_text(memory.content))

        intersection = query_tokens & memory_tokens
        union = query_tokens | memory_tokens

        if len(union) == 0:
            similarity = 0.0
        else:
            similarity = len(intersection) / len(union)

        # Apply boosts
        similarity = self._apply_boosts(similarity, query_text, memory, query_context)

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(similarity, 1.0),
            algorithm_used=SimilarityAlgorithm.JACCARD,
            match_details={
                "intersection_size": len(intersection),
                "union_size": len(union),
                "jaccard_coefficient": similarity,
            },
            confidence=0.7,
        )

    def _calculate_levenshtein_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """Calculate similarity based on edit distance."""
        # Use first 200 characters to avoid performance issues
        query_substr = query_text[:200].lower()
        memory_substr = memory.content[:200].lower()

        edit_distance = self._levenshtein_distance(query_substr, memory_substr)
        max_length = max(len(query_substr), len(memory_substr))

        if max_length == 0:
            similarity = 1.0
        else:
            similarity = 1.0 - (edit_distance / max_length)

        # Apply boosts
        similarity = self._apply_boosts(similarity, query_text, memory, query_context)

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(similarity, 1.0),
            algorithm_used=SimilarityAlgorithm.LEVENSHTEIN,
            match_details={
                "edit_distance": edit_distance,
                "max_length": max_length,
                "similarity_ratio": similarity,
            },
            confidence=0.6,
        )

    def _calculate_semantic_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """
        Calculate semantic similarity.

        Note: This is a simplified implementation. In production, this would
        use word embeddings or transformer models for true semantic similarity.
        """
        # For now, use a combination of word overlap and conceptual similarity
        query_tokens = self._tokenize_text(query_text)
        memory_tokens = self._tokenize_text(memory.content)

        # Find conceptually related terms
        conceptual_matches = self._find_conceptual_matches(query_tokens, memory_tokens)

        # Combine with word overlap
        word_overlap = len(set(query_tokens) & set(memory_tokens))
        total_words = len(set(query_tokens) | set(memory_tokens))

        if total_words == 0:
            similarity = 0.0
        else:
            overlap_score = word_overlap / total_words
            conceptual_score = conceptual_matches / max(len(query_tokens), 1)
            similarity = 0.7 * overlap_score + 0.3 * conceptual_score

        # Apply boosts
        similarity = self._apply_boosts(similarity, query_text, memory, query_context)

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(similarity, 1.0),
            algorithm_used=SimilarityAlgorithm.SEMANTIC,
            match_details={
                "word_overlap": word_overlap,
                "conceptual_matches": conceptual_matches,
                "overlap_score": overlap_score,
                "conceptual_score": conceptual_score,
            },
            confidence=0.9,
        )

    def _calculate_pattern_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """Calculate similarity based on patterns and structure."""
        pattern_score = self._calculate_pattern_match_score_text(query_text, memory.content)

        # Apply boosts
        pattern_score = self._apply_boosts(pattern_score, query_text, memory, query_context)

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(pattern_score, 1.0),
            algorithm_used=SimilarityAlgorithm.PATTERN,
            match_details={"pattern_match_score": pattern_score},
            confidence=0.75,
        )

    def _calculate_hybrid_similarity(
        self, query_text: str, memory: MemoryItem, query_context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """Calculate hybrid similarity using multiple algorithms."""
        # Calculate individual similarities
        cosine_result = self._calculate_cosine_similarity(query_text, memory, query_context)
        semantic_result = self._calculate_semantic_similarity(query_text, memory, query_context)
        pattern_result = self._calculate_pattern_similarity(query_text, memory, query_context)

        # Weighted combination
        hybrid_score = (
            self.config.text_weight * cosine_result.similarity_score
            + self.config.semantic_weight * semantic_result.similarity_score
            + self.config.pattern_weight * pattern_result.similarity_score
        )

        return SimilarityResult(
            memory_id=memory.id,
            similarity_score=min(hybrid_score, 1.0),
            algorithm_used=SimilarityAlgorithm.HYBRID,
            match_details={
                "cosine_score": cosine_result.similarity_score,
                "semantic_score": semantic_result.similarity_score,
                "pattern_score": pattern_result.similarity_score,
                "weights": {
                    "text": self.config.text_weight,
                    "semantic": self.config.semantic_weight,
                    "pattern": self.config.pattern_weight,
                },
            },
            confidence=0.9,
        )

    def _apply_boosts(
        self,
        base_similarity: float,
        query_text: str,
        memory: MemoryItem,
        query_context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Apply various boosts to the base similarity score."""
        boosted_score = base_similarity

        # Category boost
        if query_context and "category" in query_context:
            if memory.category.value == query_context["category"]:
                boosted_score += self.config.category_boost

        # Tag boost
        query_lower = query_text.lower()
        for tag in memory.tags:
            if tag.lower() in query_lower:
                boosted_score += self.config.tag_boost
                break  # Only apply once

        # Temporal decay for older memories
        if self.config.temporal_decay > 0:
            age_days = memory.get_age_seconds() / (24 * 3600)
            decay_factor = 1.0 - min(age_days * self.config.temporal_decay, 0.5)
            boosted_score *= decay_factor

        return boosted_score

    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words with optional processing."""
        if not text:
            return []

        # Extract words
        words = self._word_pattern.findall(text.lower())

        # Remove stop words if enabled
        if self.config.enable_stop_word_removal:
            words = [word for word in words if word not in self._stop_words]

        # Simple stemming if enabled (remove common suffixes)
        if self.config.enable_stemming:
            words = [self._simple_stem(word) for word in words]

        return words

    def _simple_stem(self, word: str) -> str:
        """Simple stemming by removing common suffixes."""
        suffixes = ["ing", "ed", "er", "est", "ly", "s"]

        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[: -len(suffix)]

        return word

    def _calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Calculate term frequency."""
        tf = {}
        total_tokens = len(tokens)

        if total_tokens == 0:
            return tf

        token_counts = Counter(tokens)

        for token, count in token_counts.items():
            tf[token] = count / total_tokens

        return tf

    def _find_conceptual_matches(self, query_tokens: List[str], memory_tokens: List[str]) -> int:
        """Find conceptually related terms between token lists."""
        # Simple conceptual matching using predefined relationships
        conceptual_groups = {
            "error": ["bug", "issue", "problem", "failure", "exception"],
            "deploy": ["deployment", "release", "publish", "launch"],
            "test": ["testing", "validation", "verification", "check"],
            "code": ["programming", "development", "implementation"],
            "fix": ["resolve", "solve", "repair", "correct"],
            "performance": ["speed", "optimization", "efficiency"],
        }

        matches = 0

        for query_token in query_tokens:
            for memory_token in memory_tokens:
                # Direct match
                if query_token == memory_token:
                    continue

                # Check conceptual groups
                for group_key, group_terms in conceptual_groups.items():
                    if (
                        (query_token in group_terms and memory_token in group_terms)
                        or (query_token == group_key and memory_token in group_terms)
                        or (query_token in group_terms and memory_token == group_key)
                    ):
                        matches += 1
                        break

        return matches

    def _calculate_pattern_match_score(self, memory1: MemoryItem, memory2: MemoryItem) -> float:
        """Calculate pattern similarity between two memories."""
        # Compare structure patterns
        structure_score = self._compare_structure_patterns(memory1.content, memory2.content)

        # Compare tag patterns
        tag_score = self._compare_tag_patterns(memory1.tags, memory2.tags)

        # Compare metadata patterns
        metadata_score = self._compare_metadata_patterns(memory1.metadata, memory2.metadata)

        # Weighted combination
        return 0.5 * structure_score + 0.3 * tag_score + 0.2 * metadata_score

    def _calculate_pattern_match_score_text(self, text1: str, text2: str) -> float:
        """Calculate pattern similarity between two text strings."""
        return self._compare_structure_patterns(text1, text2)

    def _compare_structure_patterns(self, text1: str, text2: str) -> float:
        """Compare structural patterns in text."""
        # Extract structural features
        features1 = self._extract_structure_features(text1)
        features2 = self._extract_structure_features(text2)

        # Calculate similarity
        common_features = set(features1.keys()) & set(features2.keys())

        if not common_features:
            return 0.0

        similarity = 0.0
        for feature in common_features:
            # Normalize feature values and compare
            val1 = features1[feature]
            val2 = features2[feature]

            if val1 == 0 and val2 == 0:
                feature_similarity = 1.0
            elif val1 == 0 or val2 == 0:
                feature_similarity = 0.0
            else:
                feature_similarity = 1.0 - abs(val1 - val2) / max(val1, val2)

            similarity += feature_similarity

        return similarity / len(common_features)

    def _extract_structure_features(self, text: str) -> Dict[str, float]:
        """Extract structural features from text."""
        if not text:
            return {}

        features = {}

        # Length features
        features["length"] = len(text)
        features["word_count"] = len(text.split())
        features["sentence_count"] = text.count(".") + text.count("!") + text.count("?")

        # Character patterns
        features["uppercase_ratio"] = sum(1 for c in text if c.isupper()) / len(text)
        features["digit_ratio"] = sum(1 for c in text if c.isdigit()) / len(text)
        features["punctuation_ratio"] = sum(
            1 for c in text if not c.isalnum() and not c.isspace()
        ) / len(text)

        # Code-like patterns
        features["bracket_count"] = text.count("(") + text.count("[") + text.count("{")
        features["quote_count"] = text.count('"') + text.count("'")
        features["newline_count"] = text.count("\n")

        return features

    def _compare_tag_patterns(self, tags1: List[str], tags2: List[str]) -> float:
        """Compare tag patterns between memories."""
        if not tags1 and not tags2:
            return 1.0

        if not tags1 or not tags2:
            return 0.0

        set1 = set(tags1)
        set2 = set(tags2)

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    def _compare_metadata_patterns(
        self, metadata1: Dict[str, Any], metadata2: Dict[str, Any]
    ) -> float:
        """Compare metadata patterns between memories."""
        if not metadata1 and not metadata2:
            return 1.0

        if not metadata1 or not metadata2:
            return 0.0

        # Compare keys
        keys1 = set(metadata1.keys())
        keys2 = set(metadata2.keys())

        common_keys = keys1 & keys2
        all_keys = keys1 | keys2

        if not all_keys:
            return 1.0

        key_similarity = len(common_keys) / len(all_keys)

        # Compare values for common keys
        value_similarity = 0.0
        if common_keys:
            for key in common_keys:
                val1 = str(metadata1[key])
                val2 = str(metadata2[key])

                if val1 == val2:
                    value_similarity += 1.0
                else:
                    # Simple string similarity
                    value_similarity += self._string_similarity(val1, val2)

            value_similarity /= len(common_keys)

        return 0.6 * key_similarity + 0.4 * value_similarity

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity."""
        if str1 == str2:
            return 1.0

        if not str1 or not str2:
            return 0.0

        # Use simple character overlap
        set1 = set(str1.lower())
        set2 = set(str2.lower())

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    def _levenshtein_distance(self, str1: str, str2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if not str1:
            return len(str2)
        if not str2:
            return len(str1)

        # Create distance matrix
        rows = len(str1) + 1
        cols = len(str2) + 1
        dist = [[0] * cols for _ in range(rows)]

        # Initialize first row and column
        for i in range(1, rows):
            dist[i][0] = i
        for j in range(1, cols):
            dist[0][j] = j

        # Fill in the rest of the matrix
        for i in range(1, rows):
            for j in range(1, cols):
                if str1[i - 1] == str2[j - 1]:
                    cost = 0
                else:
                    cost = 1

                dist[i][j] = min(
                    dist[i - 1][j] + 1,  # deletion
                    dist[i][j - 1] + 1,  # insertion
                    dist[i - 1][j - 1] + cost,  # substitution
                )

        return dist[rows - 1][cols - 1]

    def _generate_cache_key(
        self, query_text: str, memory: MemoryItem, algorithm: SimilarityAlgorithm
    ) -> str:
        """Generate cache key for similarity calculation."""
        # Use a simple hash of the key components
        key_components = f"{query_text}:{memory.id}:{algorithm.value}"
        return str(hash(key_components))

    def _cache_similarity(self, cache_key: str, similarity: float):
        """Cache similarity score."""
        if len(self._similarity_cache) >= self._cache_max_size:
            # Simple LRU: remove 25% of oldest entries
            items_to_remove = self._cache_max_size // 4
            keys_to_remove = list(self._similarity_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self._similarity_cache[key]

        self._similarity_cache[cache_key] = similarity

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.matching_stats.copy()

        # Add cache statistics
        stats["cache_size"] = len(self._similarity_cache)
        total_requests = self.matching_stats["cache_hits"] + self.matching_stats["cache_misses"]
        if total_requests > 0:
            stats["cache_hit_rate"] = (self.matching_stats["cache_hits"] / total_requests) * 100
        else:
            stats["cache_hit_rate"] = 0.0

        return stats

    def clear_cache(self):
        """Clear the similarity cache."""
        self._similarity_cache.clear()
        self.logger.info("Similarity cache cleared")

    def reset_stats(self):
        """Reset performance statistics."""
        self.matching_stats = {
            "total_matches": 0,
            "matches_by_algorithm": {algo.value: 0 for algo in SimilarityAlgorithm},
            "average_match_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def get_config(self) -> MatchingConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, config: MatchingConfig):
        """
        Update configuration.

        Args:
            config: New configuration
        """
        config.validate()
        self.config = config
        self.logger.info("Similarity matching configuration updated")
