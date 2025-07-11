#!/usr/bin/env python3
"""
Test OpenAI API key validation
"""

import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

async def test_openai_key():
    """Test OpenAI API key validity"""
    # Load environment from .env file
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False
        
    print(f"✅ OpenAI API key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test the key with OpenAI API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple test request
    test_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"OpenAI API response status: {response.status}")
                response_text = await response.text()
                
                if response.status == 200:
                    print("✅ OpenAI API key is valid")
                    return True
                else:
                    print(f"❌ OpenAI API key validation failed: {response_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing OpenAI API key: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_openai_key())