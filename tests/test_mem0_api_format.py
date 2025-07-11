#!/usr/bin/env python3
"""
Test script to understand the correct mem0 API format
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_mem0_api():
    """Test the mem0 API with correct format"""
    base_url = "http://localhost:8002"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("Testing health check...")
        async with session.get(f"{base_url}/health") as response:
            print(f"Health check: {response.status}")
            if response.status == 200:
                health_data = await response.json()
                print(f"Health data: {health_data}")
        
        # Test 2: Try to create memory with correct format
        print("\nTesting memory creation...")
        
        # Based on the schema, we need to send messages in the correct format
        memory_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "I need to remember this important decision about microservices architecture."
                },
                {
                    "role": "assistant", 
                    "content": "I'll help you remember this decision about microservices architecture. This is a project-level architectural decision that will impact the overall system design."
                }
            ],
            "user_id": "claude_pm_framework",
            "agent_id": "pm_agent",
            "run_id": f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metadata": {
                "category": "project_decision",
                "project": "claude-multiagent-pm",
                "tags": ["architecture", "microservices", "test"],
                "framework_version": "4.5.0",
                "created_at": datetime.now().isoformat()
            }
        }
        
        async with session.post(f"{base_url}/memories", json=memory_data) as response:
            print(f"Memory creation status: {response.status}")
            response_data = await response.text()
            print(f"Response: {response_data}")
            
            if response.status == 200:
                created_memory = json.loads(response_data)
                print(f"Created memory: {created_memory}")
                
                # Test 3: Try to retrieve memories
                print("\nTesting memory retrieval...")
                
                # Get all memories
                async with session.get(f"{base_url}/memories") as response:
                    print(f"Memory retrieval status: {response.status}")
                    if response.status == 200:
                        memories = await response.json()
                        print(f"Retrieved memories: {json.dumps(memories, indent=2)}")
                
                # Test 4: Try to search memories  
                print("\nTesting memory search...")
                
                search_data = {
                    "query": "microservices architecture",
                    "user_id": "claude_pm_framework",
                    "limit": 10
                }
                
                async with session.post(f"{base_url}/memories/search", json=search_data) as response:
                    print(f"Memory search status: {response.status}")
                    if response.status == 200:
                        search_results = await response.json()
                        print(f"Search results: {json.dumps(search_results, indent=2)}")
                    else:
                        error_data = await response.text()
                        print(f"Search error: {error_data}")

if __name__ == "__main__":
    asyncio.run(test_mem0_api())