#!/usr/bin/env python3
import asyncio
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.project_service import ProjectService

async def test_datetime_fix():
    service = ProjectService()
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create test file
        (temp_dir / 'test.txt').write_text('test')
        
        # Test the fixed method
        result = await service._get_last_activity(temp_dir)
        
        # Parse and check timezone awareness
        dt = datetime.fromisoformat(result.replace('Z', '+00:00'))
        print(f'✅ DateTime operations timezone-aware: {dt.tzinfo is not None}')
        print(f'✅ Result: {result}')
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test_datetime_fix())