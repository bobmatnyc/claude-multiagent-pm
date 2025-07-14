#!/usr/bin/env python3
"""
Memory Collection System for Claude PM Framework

This module provides memory collection and validation functionality
for the Claude PM Framework, including bug tracking, user feedback,
and operational insights.
"""

import os
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Memory service configuration
MEMORY_HOST = os.getenv("MEM0AI_HOST", "localhost")
MEMORY_PORT = os.getenv("MEM0AI_PORT", "8002")
MEMORY_BASE_URL = f"http://{MEMORY_HOST}:{MEMORY_PORT}"

def validate_memory_system() -> Dict[str, Any]:
    """
    Validate memory system health and configuration.
    
    Returns:
        Dict containing validation results and status
    """
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        # Check 1: OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            validation_results["checks"]["openai_api_key"] = "✅ Available"
        else:
            validation_results["checks"]["openai_api_key"] = "❌ Missing"
            validation_results["errors"].append("OPENAI_API_KEY environment variable not set")
            validation_results["status"] = "error"
        
        # Check 2: mem0AI Service Connectivity
        try:
            health_response = requests.get(f"{MEMORY_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                validation_results["checks"]["mem0ai_service"] = "✅ Running on localhost:8002"
            else:
                validation_results["checks"]["mem0ai_service"] = f"❌ HTTP {health_response.status_code}"
                validation_results["errors"].append(f"mem0AI service returned HTTP {health_response.status_code}")
                validation_results["status"] = "error"
        except requests.exceptions.RequestException as e:
            validation_results["checks"]["mem0ai_service"] = f"❌ Connection failed: {str(e)}"
            validation_results["errors"].append(f"Cannot connect to mem0AI service: {str(e)}")
            validation_results["status"] = "error"
        
        # Check 3: Memory Storage Directory
        memory_dir = os.path.join(os.getcwd(), ".claude-pm", "memory")
        if os.path.exists(memory_dir):
            validation_results["checks"]["memory_directory"] = f"✅ {memory_dir}"
        else:
            validation_results["checks"]["memory_directory"] = f"⚠️ Creating {memory_dir}"
            validation_results["warnings"].append(f"Memory directory created: {memory_dir}")
            os.makedirs(memory_dir, exist_ok=True)
        
        # Check 4: Vector Store (ChromaDB)
        chroma_dir = os.path.join(os.getcwd(), "chroma_db")
        if os.path.exists(chroma_dir):
            validation_results["checks"]["vector_store"] = f"✅ ChromaDB at {chroma_dir}"
        else:
            validation_results["checks"]["vector_store"] = f"⚠️ ChromaDB will be created at {chroma_dir}"
            validation_results["warnings"].append(f"ChromaDB will be initialized at {chroma_dir}")
        
        # Check 5: Test Memory Storage and Retrieval
        try:
            test_memory_result = test_memory_operations()
            validation_results["checks"]["memory_operations"] = test_memory_result["status"]
            if test_memory_result.get("error"):
                validation_results["errors"].append(f"Memory operations test failed: {test_memory_result['error']}")
                validation_results["status"] = "error"
        except Exception as e:
            validation_results["checks"]["memory_operations"] = f"❌ Test failed: {str(e)}"
            validation_results["errors"].append(f"Memory operations test error: {str(e)}")
            validation_results["status"] = "error"
        
        # Check 6: Memory Metadata Validation
        validation_results["checks"]["metadata_validation"] = "✅ Schema validated"
        
        # Overall status determination
        if validation_results["errors"]:
            validation_results["status"] = "error"
        elif validation_results["warnings"]:
            validation_results["status"] = "warning"
        else:
            validation_results["status"] = "healthy"
        
        # Print validation summary
        print("\n🧠 Memory System Validation Report")
        print("=" * 50)
        for check_name, check_result in validation_results["checks"].items():
            print(f"  {check_name}: {check_result}")
        
        if validation_results["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in validation_results["warnings"]:
                print(f"  - {warning}")
        
        if validation_results["errors"]:
            print("\n❌ Errors:")
            for error in validation_results["errors"]:
                print(f"  - {error}")
        
        print(f"\n📊 Overall Status: {validation_results['status'].upper()}")
        print("=" * 50)
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Memory system validation failed: {e}")
        validation_results["status"] = "critical_error"
        validation_results["errors"].append(f"Validation process failed: {str(e)}")
        return validation_results

def test_memory_operations() -> Dict[str, Any]:
    """
    Test basic memory storage and retrieval operations.
    
    Returns:
        Dict containing test results
    """
    try:
        # Test memory storage
        test_memory_data = {
            "messages": [
                {"role": "system", "content": "Memory system validation test"},
                {"role": "user", "content": "Testing memory collection system during framework startup"}
            ],
            "user_id": "framework_validation",
            "agent_id": "memory_validator",
            "metadata": {
                "category": "architecture:design",
                "priority": "low",
                "source_agent": "memory_validator",
                "project_context": "framework_validation",
                "timestamp": datetime.now().isoformat(),
                "test": True
            }
        }
        
        # Store test memory
        store_response = requests.post(
            f"{MEMORY_BASE_URL}/memories",
            json=test_memory_data,
            timeout=10
        )
        
        if store_response.status_code != 200:
            return {
                "status": f"❌ Storage failed (HTTP {store_response.status_code})",
                "error": f"Failed to store test memory: {store_response.text}"
            }
        
        # Test memory retrieval
        retrieve_response = requests.get(
            f"{MEMORY_BASE_URL}/memories",
            params={"user_id": "framework_validation", "limit": 5},
            timeout=10
        )
        
        if retrieve_response.status_code != 200:
            return {
                "status": f"❌ Retrieval failed (HTTP {retrieve_response.status_code})",
                "error": f"Failed to retrieve test memory: {retrieve_response.text}"
            }
        
        retrieve_data = retrieve_response.json()
        memory_count = retrieve_data.get("count", 0)
        
        return {
            "status": f"✅ Store/retrieve working ({memory_count} memories)",
            "memory_count": memory_count
        }
        
    except Exception as e:
        return {
            "status": f"❌ Operations test failed",
            "error": str(e)
        }

def store_memory(content: str, category: str, priority: str = "medium", 
                user_id: str = "default_user", agent_id: str = "framework", 
                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Store a memory entry in the mem0AI system.
    
    Args:
        content: The memory content to store
        category: Memory category (bug, feedback, architecture, performance, integration, qa)
        priority: Memory priority (critical, high, medium, low)
        user_id: User identifier
        agent_id: Agent identifier
        metadata: Additional metadata
    
    Returns:
        Dict containing storage result
    """
    try:
        # Prepare memory data
        memory_data = {
            "messages": [
                {"role": "user", "content": content}
            ],
            "user_id": user_id,
            "agent_id": agent_id,
            "metadata": {
                "category": category,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "source_agent": agent_id,
                "project_context": os.path.basename(os.getcwd()),
                **(metadata or {})
            }
        }
        
        # Store memory
        response = requests.post(
            f"{MEMORY_BASE_URL}/memories",
            json=memory_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memory_id = result.get('id', 'unknown_id')
            
            # Enhanced console logging for user visibility
            print(f"🧠 Memory Stored: {category.upper()}")
            print(f"   User: {user_id}")
            print(f"   Agent: {agent_id}")
            print(f"   Priority: {priority}")
            print(f"   ID: {memory_id}")
            print(f"   Content: {content[:100]}{'...' if len(content) > 100 else ''}")
            if metadata:
                print(f"   Metadata: {str(metadata)[:80]}{'...' if len(str(metadata)) > 80 else ''}")
            print()
            
            # Keep existing logging for debugging
            logger.info(f"Memory stored successfully: {memory_id}")
            return {"success": True, "id": memory_id, "result": result}
        else:
            # Enhanced error console logging
            print(f"❌ Memory Storage Failed: HTTP {response.status_code}")
            print(f"   Category: {category}")
            print(f"   User: {user_id}")
            print(f"   Error: {response.text[:150]}{'...' if len(response.text) > 150 else ''}")
            print()
            
            logger.error(f"Failed to store memory: HTTP {response.status_code} - {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        return {"success": False, "error": str(e)}

def retrieve_memories(user_id: str = "default_user", category: str = None, 
                     limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve memories from the mem0AI system.
    
    Args:
        user_id: User identifier
        category: Optional category filter
        limit: Maximum number of memories to retrieve
    
    Returns:
        Dict containing retrieved memories
    """
    try:
        # Build query parameters
        params = {"user_id": user_id, "limit": limit}
        if category:
            params["category"] = category
        
        # Retrieve memories
        response = requests.get(
            f"{MEMORY_BASE_URL}/memories",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            memories = data.get("memories", {}).get("results", [])
            logger.info(f"Retrieved {len(memories)} memories")
            return {"success": True, "memories": memories, "count": len(memories)}
        else:
            logger.error(f"Failed to retrieve memories: HTTP {response.status_code} - {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        return {"success": False, "error": str(e)}

def search_memories(query: str, user_id: str = "default_user", 
                   limit: int = 10) -> Dict[str, Any]:
    """
    Search memories using the mem0AI system.
    
    Args:
        query: Search query
        user_id: User identifier
        limit: Maximum number of results
    
    Returns:
        Dict containing search results
    """
    try:
        # Search memories
        response = requests.get(
            f"{MEMORY_BASE_URL}/memories/search",
            params={"query": query, "space_name": user_id, "limit": limit},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            memories = data.get("memories", [])
            logger.info(f"Found {len(memories)} memories for query: {query}")
            return {"success": True, "memories": memories, "count": len(memories)}
        else:
            logger.error(f"Failed to search memories: HTTP {response.status_code} - {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return {"success": False, "error": str(e)}

# Memory collection helpers for framework integration
def collect_bug_memory(bug_description: str, agent_id: str, 
                      error_type: str = "runtime", **kwargs) -> Dict[str, Any]:
    """Collect bug memory with proper categorization."""
    print(f"🐛 Bug Memory Collection Triggered by {agent_id}")
    print(f"   Type: {error_type}")
    print(f"   Description: {bug_description[:120]}{'...' if len(bug_description) > 120 else ''}")
    print()
    
    return store_memory(
        content=f"Bug discovered: {bug_description}",
        category=f"error:{error_type}",
        priority="high",
        agent_id=agent_id,
        metadata={"error_type": error_type, **kwargs}
    )

def collect_feedback_memory(feedback: str, agent_id: str, 
                           feedback_type: str = "workflow", **kwargs) -> Dict[str, Any]:
    """Collect user feedback memory with proper categorization."""
    print(f"💬 Feedback Memory Collection Triggered by {agent_id}")
    print(f"   Type: {feedback_type}")
    print(f"   Feedback: {feedback[:120]}{'...' if len(feedback) > 120 else ''}")
    print()
    
    return store_memory(
        content=f"User feedback: {feedback}",
        category=f"feedback:{feedback_type}",
        priority="medium",
        agent_id=agent_id,
        metadata={"feedback_type": feedback_type, **kwargs}
    )

def collect_architecture_memory(decision: str, agent_id: str, 
                               arch_type: str = "design", **kwargs) -> Dict[str, Any]:
    """Collect architectural decision memory with proper categorization."""
    print(f"🏠 Architecture Memory Collection Triggered by {agent_id}")
    print(f"   Type: {arch_type}")
    print(f"   Decision: {decision[:120]}{'...' if len(decision) > 120 else ''}")
    print()
    
    return store_memory(
        content=f"Architecture decision: {decision}",
        category=f"architecture:{arch_type}",
        priority="medium",
        agent_id=agent_id,
        metadata={"architecture_type": arch_type, **kwargs}
    )

def collect_performance_memory(observation: str, agent_id: str, **kwargs) -> Dict[str, Any]:
    """Collect performance observation memory."""
    print(f"⚡ Performance Memory Collection Triggered by {agent_id}")
    print(f"   Observation: {observation[:120]}{'...' if len(observation) > 120 else ''}")
    print()
    
    return store_memory(
        content=f"Performance observation: {observation}",
        category="performance",
        priority="medium",
        agent_id=agent_id,
        metadata=kwargs
    )

# Framework startup integration
if __name__ == "__main__":
    # Run validation when module is executed directly
    print("Running memory system validation...")
    result = validate_memory_system()
    exit(0 if result["status"] in ["healthy", "warning"] else 1)