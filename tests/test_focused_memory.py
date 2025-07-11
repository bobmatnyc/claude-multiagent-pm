#!/usr/bin/env python3
"""
Focused Memory Backend Testing

This script tests specific memory backend issues identified in the comprehensive test.
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.services.memory.backends.sqlite_backend import SQLiteBackend
from claude_pm.services.memory.backends.tinydb_backend import TinyDBBackend
# # from claude_pm.services.memory.backends.memory_backend import InMemoryBackend  # InMemory backend removed  # InMemory backend removed
from claude_pm.services.memory.interfaces.models import MemoryCategory, MemoryQuery

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_tinydb_isolated():
    """Test TinyDB backend in isolation."""
    logger.info("Testing TinyDB backend isolation...")
    
    temp_dir = tempfile.mkdtemp()
    tinydb_path = os.path.join(temp_dir, "isolated_test.json")
    
    try:
        # Try to import TinyDB directly
        from tinydb import TinyDB
        logger.info("✅ TinyDB import successful")
        
        # Create TinyDB instance directly
        db = TinyDB(tinydb_path)
        logger.info("✅ TinyDB instance created")
        
        # Test basic operations
        doc_id = db.insert({"test": "data"})
        logger.info(f"✅ Document inserted with ID: {doc_id}")
        
        docs = db.all()
        logger.info(f"✅ Retrieved {len(docs)} documents")
        
        db.close()
        
        # Now test our backend
        backend = TinyDBBackend({"db_path": tinydb_path})
        
        # Check initialization
        success = await backend.initialize()
        logger.info(f"Backend initialization: {success}")
        
        # Check health
        health = await backend.health_check()
        logger.info(f"Backend health check: {health}")
        
        if success and health:
            # Test memory operations
            memory_id = await backend.add_memory(
                "test_project",
                "Test content",
                MemoryCategory.PROJECT,
                ["test"],
                {"test": True}
            )
            logger.info(f"✅ Memory added: {memory_id}")
            
            memory = await backend.get_memory("test_project", memory_id)
            logger.info(f"✅ Memory retrieved: {memory.content if memory else 'None'}")
        
        await backend.cleanup()
        
    except Exception as e:
        logger.error(f"❌ TinyDB test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

async def test_sqlite_isolated():
    """Test SQLite backend in isolation."""
    logger.info("Testing SQLite backend isolation...")
    
    temp_dir = tempfile.mkdtemp()
    sqlite_path = os.path.join(temp_dir, "isolated_test.db")
    
    try:
        backend = SQLiteBackend({
            "db_path": sqlite_path,
            "enable_fts": True,
            "enable_wal": True
        })
        
        # Check initialization
        success = await backend.initialize()
        logger.info(f"Backend initialization: {success}")
        
        # Check health
        health = await backend.health_check()
        logger.info(f"Backend health check: {health}")
        
        if success and health:
            # Test basic add
            memory_id = await backend.add_memory(
                "test_project",
                "Test content for searching",
                MemoryCategory.PROJECT,
                ["test"],
                {"test": True}
            )
            logger.info(f"✅ Memory added: {memory_id}")
            
            # Test get
            memory = await backend.get_memory("test_project", memory_id)
            logger.info(f"✅ Memory retrieved: {memory.content if memory else 'None'}")
            
            # Test search without FTS first
            query = MemoryQuery(query="", limit=10)  # Empty query
            results = await backend.search_memories("test_project", query)
            logger.info(f"✅ Empty search results: {len(results)}")
            
            # Test search with content
            query = MemoryQuery(query="content", limit=10)
            results = await backend.search_memories("test_project", query)
            logger.info(f"✅ Content search results: {len(results)}")
            
            # Test update
            updated = await backend.update_memory(
                "test_project",
                memory_id,
                content="Updated content"
            )
            logger.info(f"✅ Memory updated: {updated}")
            
            # Test search after update
            query = MemoryQuery(query="Updated", limit=10)
            results = await backend.search_memories("test_project", query)
            logger.info(f"✅ Updated search results: {len(results)}")
        
        await backend.cleanup()
        
    except Exception as e:
        logger.error(f"❌ SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

async def test_inmemory_isolated():
    # """Test InMemory backend in isolation."""  # InMemory backend removed
    # logger.info("Testing InMemory backend isolation...")  # InMemory backend removed
    
    try:
        # backend = InMemoryBackend({  # InMemory backend removed
            "max_memory_size": 100,
            "enable_expiration": False
        })
        
        # Check initialization
        success = await backend.initialize()
        logger.info(f"Backend initialization: {success}")
        
        # Check health
        health = await backend.health_check()
        logger.info(f"Backend health check: {health}")
        
        if success and health:
            # Test basic operations
            memory_id = await backend.add_memory(
                "test_project",
                "Test content",
                MemoryCategory.PROJECT,
                ["test"],
                {"test": True}
            )
            logger.info(f"✅ Memory added: {memory_id}")
            
            memory = await backend.get_memory("test_project", memory_id)
            logger.info(f"✅ Memory retrieved: {memory.content if memory else 'None'}")
            
            # Test search
            query = MemoryQuery(query="content", limit=10)
            results = await backend.search_memories("test_project", query)
            logger.info(f"✅ Search results: {len(results)}")
            
            # Test statistics
            stats = await backend.get_memory_stats("test_project")
            logger.info(f"✅ Statistics: {stats}")
        
        await backend.cleanup()
        
    except Exception as e:
        # logger.error(f"❌ InMemory test failed: {e}")  # InMemory backend removed
        import traceback
        traceback.print_exc()

async def main():
    """Run focused tests."""
    logger.info("Starting focused memory backend tests...")
    
    await test_inmemory_isolated()
    await test_tinydb_isolated()
    await test_sqlite_isolated()
    
    logger.info("Focused tests completed!")

if __name__ == "__main__":
    asyncio.run(main())