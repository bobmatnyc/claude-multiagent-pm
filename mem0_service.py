#!/usr/bin/env python3
"""
Simple mem0 REST API Service
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from mem0 import Memory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Mem0 REST APIs (Simple)", version="1.0.0")

# Initialize mem0 memory
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 1500,
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "host": "localhost",
            "port": 8000,
            "path": "./chroma_db",
            "collection_name": "mem0_collection"
        }
    },
    # Optional: graph_store can be omitted if not needed
    # "graph_store": {
    #     "provider": "neo4j",
    #     "config": {
    #         "url": "bolt://localhost:7687",
    #         "username": "neo4j",
    #         "password": "password"
    #     }
    # }
}

# In-memory storage fallback (temporary solution for persistent storage issue)
MEMORY_STORAGE = {}
MEMORY_COUNTER = 0

def add_to_memory_storage(user_id, content, metadata):
    """Add memory to in-memory storage as fallback."""
    global MEMORY_COUNTER
    MEMORY_COUNTER += 1
    memory_id = f"mem_{MEMORY_COUNTER}"
    
    if user_id not in MEMORY_STORAGE:
        MEMORY_STORAGE[user_id] = []
    
    memory_item = {
        "id": memory_id,
        "content": content,
        "metadata": metadata,
        "created_at": datetime.now().isoformat(),
        "user_id": user_id
    }
    
    MEMORY_STORAGE[user_id].append(memory_item)
    logger.info(f"Added memory {memory_id} to in-memory storage for user {user_id}")
    return memory_id

def get_memories_from_storage(user_id=None, query=None, limit=10):
    """Get memories from in-memory storage."""
    all_memories = []
    
    if user_id:
        all_memories = MEMORY_STORAGE.get(user_id, [])
    else:
        for memories in MEMORY_STORAGE.values():
            all_memories.extend(memories)
    
    # Simple text search if query provided
    if query:
        filtered = []
        for memory in all_memories:
            content = memory.get("content", "").lower()
            metadata_str = str(memory.get("metadata", {})).lower()
            if query.lower() in content or query.lower() in metadata_str:
                filtered.append(memory)
        all_memories = filtered
    
    return all_memories[:limit]

# Initialize memory with simpler configuration
try:
    # Try the simpler dictionary-based configuration first
    simple_config = {
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "mem0_collection",
                "path": "./chroma_db"
            }
        }
    }
    memory = Memory(config=simple_config)
    logger.info("Memory initialized with simple ChromaDB configuration")
    logger.info(f"Memory object type after simple init: {type(memory)}")
    logger.info(f"Memory object methods: {[m for m in dir(memory) if not m.startswith('_')]}")
except Exception as e:
    logger.error(f"Failed to initialize memory with simple config: {e}")
    # Try advanced configuration
    try:
        from mem0.configs.base import MemoryConfig, VectorStoreConfig
        from mem0.configs.vector_stores.chroma import ChromaDbConfig
        
        # Create ChromaDB configuration
        chroma_config = ChromaDbConfig(
            collection_name="mem0_collection",
            path="./chroma_db"
        )
        
        # Create vector store configuration
        vector_store_config = VectorStoreConfig(
            provider="chroma",
            config=chroma_config.model_dump()
        )
        
        # Create memory configuration
        memory_config = MemoryConfig(
            vector_store=vector_store_config
        )
        
        # Initialize memory with ChromaDB configuration
        memory = Memory(config=memory_config)
        logger.info("Memory initialized with advanced ChromaDB configuration")
        logger.info(f"Memory object type after advanced init: {type(memory)}")
        logger.info(f"Memory object methods: {[m for m in dir(memory) if not m.startswith('_')]}")
    except Exception as e2:
        logger.error(f"Failed to initialize memory with advanced config: {e2}")
        # Try to create a minimal memory instance
        try:
            memory = Memory()
            logger.info("Memory initialized with default configuration as fallback")
        except Exception as e3:
            logger.error(f"Failed to initialize memory with default config: {e3}")
            memory = None

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class MemoryCreate(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MemorySearch(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    limit: Optional[int] = 10

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mem0ai-simple"}

@app.get("/")
async def home():
    """Redirect to the OpenAPI documentation."""
    return {"message": "Mem0 REST API is running", "docs": "/docs"}

@app.post("/memories")
async def add_memory(memory_data: MemoryCreate):
    """Store new memories."""
    global memory
    try:
        # Debug: Check memory object at start of request
        logger.info(f"DEBUG: Memory object type at start of POST: {type(memory)}")
        if not hasattr(memory, 'add'):
            logger.error("DEBUG: Memory object missing 'add' method at start of POST request")
            raise HTTPException(status_code=500, detail="Memory service not properly initialized")
        # Convert messages to a format mem0 can understand
        messages_text = []
        for msg in memory_data.messages:
            messages_text.append(f"{msg.role}: {msg.content}")
        
        # Combine messages into a single text
        combined_text = "\n".join(messages_text)
        
        # Create memory add request
        add_data = {
            "messages": [{"role": "user", "content": combined_text}],
            "user_id": memory_data.user_id or "default_user",
            "agent_id": memory_data.agent_id or "default_agent",
            "run_id": memory_data.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metadata": memory_data.metadata or {}
        }
        
        # Add memory using mem0 - try minimal approach first
        logger.info(f"Calling memory.add() with: {add_data}")
        
        # Try a simpler add call first
        try:
            simple_result = memory.add(
                messages=add_data["messages"],
                user_id=add_data["user_id"]
            )
            logger.info(f"Simple memory.add() result: {simple_result}")
            
            # If simple approach works, try with metadata
            if simple_result.get("results"):
                result = simple_result
            else:
                # Try with full parameters
                result = memory.add(**add_data)
                logger.info(f"Full memory.add() result: {result}")
        except Exception as add_error:
            logger.error(f"Error during memory.add(): {add_error}")
            result = {"error": str(add_error)}
        
        # If mem0 isn't working (empty results), use fallback storage
        if not result.get("results"):
            logger.info("mem0 returned empty results, using fallback in-memory storage")
            content = add_data["messages"][0]["content"] if add_data["messages"] else ""
            fallback_id = add_to_memory_storage(
                user_id=add_data["user_id"],
                content=content,
                metadata=add_data.get("metadata", {})
            )
            result = {"results": [{"id": fallback_id}], "fallback": True}
        
        # Check total memories after adding (but don't log the full result to avoid excessive output)
        try:
            all_memories = memory.get_all(user_id=add_data.get("user_id", "default_user"))
            logger.info(f"get_all() returned type: {type(all_memories)}")
            total_count = len(all_memories.get("results", [])) if isinstance(all_memories, dict) else len(all_memories) if isinstance(all_memories, list) else 0
            logger.info(f"Total memories after add: {total_count}")
        except Exception as get_all_error:
            logger.warning(f"Error checking total memories: {get_all_error}")
            # Don't fail the request if we can't get the count
        
        return {
            "id": result.get("id") or "generated_id",
            "message": "Memory added successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories")
async def get_memories(user_id: Optional[str] = None, limit: int = 10):
    """Get all memories for a user."""
    global memory
    try:
        # Try to get memories from mem0 first (only if memory is available)
        memories = {"results": []}
        if memory:
            memories = memory.get_all(user_id=user_id or "default_user")
        
        # If mem0 returns empty results, try fallback storage
        if isinstance(memories, dict) and not memories.get("results"):
            logger.info("mem0 get_all() returned empty, using fallback storage")
            fallback_memories = get_memories_from_storage(user_id=user_id, limit=limit)
            return {
                "memories": {"results": fallback_memories},
                "count": len(fallback_memories),
                "source": "fallback"
            }
        
        # Limit results for mem0 response
        if isinstance(memories, list):
            memories = memories[:limit]
        
        return {
            "memories": memories,
            "count": len(memories) if isinstance(memories, list) else 0,
            "source": "mem0"
        }
        
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/search")
async def search_memories(search_data: MemorySearch):
    """Search memories."""
    global memory
    try:
        # Try mem0 search first (only if memory is available and query is not empty)
        results = []
        if memory and search_data.query.strip():  # Don't search with empty queries to avoid OpenAI API errors
            results = memory.search(
                query=search_data.query,
                user_id=search_data.user_id or "default_user",
                agent_id=search_data.agent_id,
                limit=search_data.limit or 10
            )
        
        # If mem0 search returns empty, try fallback storage
        if not results or (isinstance(results, list) and len(results) == 0):
            logger.info("mem0 search returned empty, using fallback storage")
            fallback_results = get_memories_from_storage(
                user_id=search_data.user_id,
                query=search_data.query,
                limit=search_data.limit or 10
            )
            return {
                "memories": fallback_results,
                "count": len(fallback_results),
                "query": search_data.query,
                "source": "fallback"
            }
        
        # Format response to match integration expectations
        if isinstance(results, dict) and "results" in results:
            raw_results = results["results"]
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []
        
        # Transform mem0 format to framework format
        formatted_results = []
        for memory in raw_results:
            if memory:  # Skip None entries
                formatted_memory = {
                    "id": memory.get("id", ""),
                    "content": memory.get("memory", memory.get("content", "")),
                    "metadata": memory.get("metadata") or {},
                    "created_at": memory.get("created_at", ""),
                    "user_id": memory.get("user_id", ""),
                    "score": memory.get("score", 0)
                }
                formatted_results.append(formatted_memory)
            
        return {
            "memories": formatted_results,
            "count": len(formatted_results),
            "query": search_data.query,
            "source": "mem0"
        }
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/search")
async def get_memories_search(query: str, space_name: Optional[str] = None, limit: int = 10, include_metadata: str = "true", category: Optional[str] = None):
    """Search memories via GET endpoint (for integration compatibility)."""
    global memory
    try:
        # Check if memory object is properly initialized
        if not memory:
            logger.error("Memory object is not initialized")
            return {"memories": [], "count": 0, "query": query, "error": "Memory not initialized"}
        
        # Try mem0 search first (only if memory is available and query is not empty)
        results = []
        if query.strip():  # Don't search with empty queries to avoid OpenAI API errors
            try:
                results = memory.search(
                    query=query,
                    user_id=space_name or "default_user",
                    limit=limit
                )
            except AttributeError as e:
                logger.error(f"Memory object missing search method: {e}")
                logger.error(f"Memory object type: {type(memory)}")
                logger.error(f"Memory object attributes: {dir(memory) if memory else 'None'}")
                # Fall back to storage search
                fallback_results = get_memories_from_storage(
                    user_id=space_name,
                    query=query,
                    limit=limit
                )
                return {
                    "memories": fallback_results,
                    "count": len(fallback_results),
                    "query": query,
                    "source": "fallback_due_to_error"
                }
        
        # If mem0 search returns empty, try fallback storage
        if not results or (isinstance(results, list) and len(results) == 0):
            logger.info("mem0 GET search returned empty, using fallback storage")
            fallback_results = get_memories_from_storage(
                user_id=space_name,
                query=query,
                limit=limit
            )
            
            # Filter by category if specified
            if category and fallback_results:
                filtered = []
                for memory in fallback_results:
                    memory_category = memory.get("metadata", {}).get("category")
                    if memory_category == category:
                        filtered.append(memory)
                fallback_results = filtered
            
            return {
                "memories": fallback_results,
                "count": len(fallback_results),
                "query": query,
                "source": "fallback"
            }
        
        # Format response to match integration expectations
        if isinstance(results, dict) and "results" in results:
            raw_results = results["results"]
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []
        
        # Transform mem0 format to framework format
        formatted_results = []
        for memory in raw_results:
            if memory:  # Skip None entries
                formatted_memory = {
                    "id": memory.get("id", ""),
                    "content": memory.get("memory", memory.get("content", "")),
                    "metadata": memory.get("metadata") or {},
                    "created_at": memory.get("created_at", ""),
                    "user_id": memory.get("user_id", ""),
                    "score": memory.get("score", 0)
                }
                formatted_results.append(formatted_memory)
            
        return {
            "memories": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "source": "mem0"
        }
        
    except Exception as e:
        logger.error(f"Error in GET search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory."""
    try:
        # Delete memory
        result = memory.delete(memory_id=memory_id)
        
        return {
            "message": "Memory deleted successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory."""
    try:
        # This might not be directly supported by mem0, so we'll search for it
        # For now, return a placeholder
        return {
            "id": memory_id,
            "message": "Memory retrieval by ID not directly supported",
            "error": "Feature not implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("MEM0_PORT", "8002"))
    host = os.getenv("MEM0_HOST", "localhost")
    
    logger.info(f"Starting mem0 service on {host}:{port}")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        exit(1)
    
    uvicorn.run(app, host=host, port=port, log_level="info")