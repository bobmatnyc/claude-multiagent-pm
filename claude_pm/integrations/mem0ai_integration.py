"""
mem0AI Integration for Claude PM Framework.

Provides seamless integration with mem0AI service running on port 8002
for intelligent project memory management and context preservation.
"""

import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from ..core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Mem0AIConfig:
    """Configuration for mem0AI integration."""
    host: str = "localhost"
    port: int = 8002
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    api_key: Optional[str] = None


class Mem0AIIntegration:
    """
    Integration with mem0AI service for intelligent memory management.
    
    Provides high-level interface for:
    - Project memory spaces
    - Context preservation
    - Memory-driven decision making
    - Intelligent retrieval
    """
    
    def __init__(self, config: Optional[Mem0AIConfig] = None):
        """Initialize mem0AI integration."""
        self.config = config or Mem0AIConfig()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        # Memory categories for Claude PM
        self.categories = {
            "project_decision": "Project-level architectural and design decisions",
            "code_pattern": "Successful code patterns and implementations", 
            "error_solution": "Bug fixes and troubleshooting solutions",
            "team_preference": "Team coding standards and preferences",
            "performance_optimization": "Performance improvements and benchmarks",
            "integration_knowledge": "Integration patterns and configurations"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> bool:
        """Connect to mem0AI service."""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {}
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            
            # Test connection
            if await self._health_check():
                self._connected = True
                logger.info(f"Connected to mem0AI service at {self.base_url}")
                return True
            else:
                logger.error("mem0AI service health check failed")
                await self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to mem0AI service: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from mem0AI service."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        logger.info("Disconnected from mem0AI service")
    
    async def _health_check(self) -> bool:
        """Check if mem0AI service is healthy."""
        try:
            if not self._session:
                return False
            
            async with self._session.get(f"{self.base_url}/health") as response:
                return response.status == 200
                
        except Exception as e:
            logger.debug(f"mem0AI health check failed: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to mem0AI service."""
        return self._connected and self._session is not None
    
    async def _retry_request(self, request_func, *args, **kwargs):
        """Retry a request with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await request_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.debug(f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.config.max_retries} attempts: {e}")
        
        raise last_exception
    
    # Project Memory Space Management
    
    async def create_project_space(self, project_name: str, description: str = "") -> bool:
        """Create a memory space for a project."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return False
        
        try:
            data = {
                "space_name": project_name,
                "description": description or f"Memory space for Claude PM project: {project_name}",
                "metadata": {
                    "project": project_name,
                    "created_by": "claude_pm_framework",
                    "created_at": datetime.now().isoformat(),
                    "framework_version": "3.0.0"
                }
            }
            
            async def make_request():
                async with self._session.post(f"{self.base_url}/spaces", json=data) as response:
                    if response.status in [200, 201, 409]:  # 409 = already exists
                        logger.info(f"Project memory space created/verified: {project_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create project space: {response.status} - {error_text}")
                        return False
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error creating project space {project_name}: {e}")
            return False
    
    async def delete_project_space(self, project_name: str) -> bool:
        """Delete a project memory space."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return False
        
        try:
            async def make_request():
                async with self._session.delete(f"{self.base_url}/spaces/{project_name}") as response:
                    if response.status in [200, 204, 404]:  # 404 = already deleted
                        logger.info(f"Project memory space deleted: {project_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete project space: {response.status} - {error_text}")
                        return False
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error deleting project space {project_name}: {e}")
            return False
    
    # Memory Management
    
    async def store_memory(
        self,
        project_name: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store a memory in the project space."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return None
        
        # Validate category
        if category not in self.categories:
            logger.warning(f"Unknown memory category: {category}. Known categories: {list(self.categories.keys())}")
        
        try:
            memory_data = {
                "content": content,
                "space_name": project_name,
                "metadata": {
                    "category": category,
                    "category_description": self.categories.get(category, ""),
                    "tags": tags or [],
                    "project": project_name,
                    "stored_at": datetime.now().isoformat(),
                    "framework_version": "3.0.0",
                    **(metadata or {})
                }
            }
            
            async def make_request():
                async with self._session.post(f"{self.base_url}/memories", json=memory_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        memory_id = result.get("id")
                        logger.info(f"Memory stored in {project_name}: {memory_id}")
                        return memory_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to store memory: {response.status} - {error_text}")
                        return None
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error storing memory in {project_name}: {e}")
            return None
    
    async def retrieve_memories(
        self,
        project_name: str,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from project space."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return []
        
        try:
            params = {
                "query": query,
                "space_name": project_name,
                "limit": limit,
                "include_metadata": True
            }
            
            if category:
                params["category"] = category
            
            if tags:
                params["tags"] = ",".join(tags)
            
            async def make_request():
                async with self._session.get(f"{self.base_url}/memories/search", params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        memories = result.get("memories", [])
                        logger.debug(f"Retrieved {len(memories)} memories for query '{query}' in {project_name}")
                        return memories
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to retrieve memories: {response.status} - {error_text}")
                        return []
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error retrieving memories from {project_name}: {e}")
            return []
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return None
        
        try:
            async def make_request():
                async with self._session.get(f"{self.base_url}/memories/{memory_id}") as response:
                    if response.status == 200:
                        memory = await response.json()
                        logger.debug(f"Retrieved memory: {memory_id}")
                        return memory
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get memory {memory_id}: {response.status} - {error_text}")
                        return None
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return False
        
        try:
            update_data = {"id": memory_id}
            
            if content is not None:
                update_data["content"] = content
            
            if tags is not None or metadata is not None:
                current_metadata = metadata or {}
                if tags is not None:
                    current_metadata["tags"] = tags
                current_metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadata"] = current_metadata
            
            async def make_request():
                async with self._session.put(f"{self.base_url}/memories/{memory_id}", json=update_data) as response:
                    if response.status == 200:
                        logger.info(f"Memory updated: {memory_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update memory {memory_id}: {response.status} - {error_text}")
                        return False
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        if not self.is_connected():
            logger.error("Not connected to mem0AI service")
            return False
        
        try:
            async def make_request():
                async with self._session.delete(f"{self.base_url}/memories/{memory_id}") as response:
                    if response.status in [200, 204, 404]:  # 404 = already deleted
                        logger.info(f"Memory deleted: {memory_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete memory {memory_id}: {response.status} - {error_text}")
                        return False
            
            return await self._retry_request(make_request)
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    # High-level convenience methods
    
    async def store_project_decision(
        self,
        project_name: str,
        decision: str,
        context: str,
        reasoning: str,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Store a project decision memory."""
        content = f"""
Decision: {decision}

Context: {context}

Reasoning: {reasoning}
""".strip()
        
        return await self.store_memory(
            project_name,
            content,
            "project_decision",
            tags or ["decision", "architecture"],
            {
                "decision": decision,
                "context": context,
                "reasoning": reasoning,
                "decision_type": "architectural"
            }
        )
    
    async def store_code_pattern(
        self,
        project_name: str,
        pattern_name: str,
        code: str,
        description: str,
        use_cases: List[str],
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Store a code pattern memory."""
        content = f"""
Pattern: {pattern_name}

Description: {description}

Use Cases:
{chr(10).join(f"- {use_case}" for use_case in use_cases)}

Code:
```
{code}
```
""".strip()
        
        return await self.store_memory(
            project_name,
            content,
            "code_pattern",
            tags or ["pattern", "code", "reusable"],
            {
                "pattern_name": pattern_name,
                "description": description,
                "use_cases": use_cases,
                "code": code,
                "language": "python"  # Could be detected
            }
        )
    
    async def store_error_solution(
        self,
        project_name: str,
        error_description: str,
        solution: str,
        root_cause: str,
        prevention: str,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Store an error solution memory."""
        content = f"""
Error: {error_description}

Root Cause: {root_cause}

Solution: {solution}

Prevention: {prevention}
""".strip()
        
        return await self.store_memory(
            project_name,
            content,
            "error_solution",
            tags or ["error", "solution", "debugging"],
            {
                "error": error_description,
                "solution": solution,
                "root_cause": root_cause,
                "prevention": prevention,
                "severity": "medium"  # Could be specified
            }
        )
    
    async def find_similar_decisions(self, project_name: str, current_decision: str) -> List[Dict[str, Any]]:
        """Find similar past decisions to inform current decision making."""
        return await self.retrieve_memories(
            project_name,
            current_decision,
            category="project_decision",
            limit=5
        )
    
    async def find_applicable_patterns(self, project_name: str, use_case: str) -> List[Dict[str, Any]]:
        """Find code patterns applicable to a specific use case."""
        return await self.retrieve_memories(
            project_name,
            use_case,
            category="code_pattern",
            limit=5
        )
    
    async def find_error_solutions(self, project_name: str, error_description: str) -> List[Dict[str, Any]]:
        """Find solutions for similar errors."""
        return await self.retrieve_memories(
            project_name,
            error_description,
            category="error_solution",
            limit=3
        )
    
    async def get_project_statistics(self, project_name: str) -> Dict[str, Any]:
        """Get statistics about project memories."""
        try:
            stats = {
                "total_memories": 0,
                "by_category": {},
                "recent_activity": 0
            }
            
            # Get memories for each category
            for category in self.categories.keys():
                memories = await self.retrieve_memories(
                    project_name,
                    "",  # Empty query to get all
                    category=category,
                    limit=1000  # High limit to get count
                )
                
                count = len(memories)
                stats["by_category"][category] = count
                stats["total_memories"] += count
                
                # Count recent activity (last 7 days)
                recent_cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
                for memory in memories:
                    stored_at = memory.get("metadata", {}).get("stored_at", "")
                    if stored_at:
                        try:
                            stored_time = datetime.fromisoformat(stored_at).timestamp()
                            if stored_time > recent_cutoff:
                                stats["recent_activity"] += 1
                        except ValueError:
                            pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting project statistics for {project_name}: {e}")
            return {"error": str(e)}


# Factory function for easy instantiation
def create_mem0ai_integration(
    host: str = "localhost",
    port: int = 8002,
    timeout: int = 30,
    api_key: Optional[str] = None
) -> Mem0AIIntegration:
    """Create a mem0AI integration with specified configuration."""
    config = Mem0AIConfig(
        host=host,
        port=port,
        timeout=timeout,
        api_key=api_key
    )
    return Mem0AIIntegration(config)