# Streaming Logger Implementation Guide

## Overview

The Claude PM Framework now includes a **Single-Line Streaming Logger** that provides cleaner startup output by showing INFO messages on a single line that updates in place, while preserving the visibility of WARNING and ERROR messages on separate lines.

## Key Features

- **Single-line INFO streaming**: Progress messages update in place using carriage returns
- **Preserved error visibility**: WARNING and ERROR messages always appear on new lines
- **Clean startup experience**: Reduces visual clutter during framework initialization
- **Automatic finalization**: Ensures final status messages remain visible

## Implementation

### Core Components

1. **StreamingHandler** (`claude_pm/core/logging_config.py`):
   - Custom logging handler that manages single-line streaming for INFO messages
   - Handles different log levels appropriately
   - Maintains line state to ensure proper output formatting

2. **Setup Functions**:
   - `setup_streaming_logger()`: Convenience function for quick streaming logger setup
   - `setup_logging()`: Enhanced with `use_streaming` parameter
   - `finalize_streaming_logs()`: Ensures final messages remain visible

### Usage Examples

#### Basic Streaming Logger Setup

```python
from claude_pm.core.logging_config import setup_streaming_logger, finalize_streaming_logs

# Setup streaming logger
logger = setup_streaming_logger("my_service")

# Use streaming INFO messages
logger.info("🚀 Starting initialization...")
logger.info("📁 Loading configuration...")
logger.info("🔧 Setting up services...")

# Errors and warnings appear on new lines
logger.warning("Configuration file missing - using defaults")
logger.error("Database connection failed - retrying...")

# Final status
logger.info("✅ Initialization complete")

# Ensure final message stays visible
finalize_streaming_logs(logger)
```

#### Advanced Setup with Custom Configuration

```python
from claude_pm.core.logging_config import setup_logging

# Setup with streaming enabled
logger = setup_logging(
    name="advanced_service",
    level="INFO",
    use_streaming=True,
    use_rich=False  # Disable rich formatting for streaming
)

# Use the logger normally
logger.info("Processing items...")
finalize_streaming_logs(logger)
```

#### Progress Indicator Pattern

```python
from claude_pm.core.logging_config import setup_streaming_logger, finalize_streaming_logs
import time

logger = setup_streaming_logger("progress_demo")

total_items = 100
for i in range(1, total_items + 1):
    percentage = (i / total_items) * 100
    progress_bar = "█" * (i // 5) + "░" * ((total_items - i) // 5)
    
    logger.info(f"Progress: [{progress_bar}] {percentage:.1f}% ({i}/{total_items})")
    time.sleep(0.05)  # Simulate work

logger.info("✅ Processing complete")
finalize_streaming_logs(logger)
```

## Integration Examples

### Framework Startup Integration

The streaming logger is integrated into key framework startup processes:

1. **Installation State Detection** (`claude_pm/utils/installation_state.py`):
   ```python
   async def detect_installation_state(self) -> InstallationState:
       logger = setup_streaming_logger("installation_detector")
       
       logger.info("🔍 Detecting framework installation state...")
       logger.info("📁 Checking global configuration directory...")
       logger.info("🔧 Validating required components...")
       logger.info("⚙️  Validating configuration files...")
       logger.info("🧠 Checking memory system configuration...")
       logger.info("✅ Framework installation state detection complete")
       
       finalize_streaming_logs(logger)
   ```

2. **CLI Directory Context** (`claude_pm/cli/cli_utils.py`):
   ```python
   def _display_directory_context_streaming():
       streaming_logger = setup_streaming_logger("directory_context")
       
       streaming_logger.info(f"📂 Working Directory: {working_dir}")
       streaming_logger.info(f"🔧 Framework Path: {claude_pm_path}")
       streaming_logger.info("✅ Directory context loaded")
       
       finalize_streaming_logs(streaming_logger)
   ```

### Service Integration Pattern

For any service that performs multi-step initialization:

```python
class MyService:
    def __init__(self):
        self.logger = setup_streaming_logger(f"{self.__class__.__name__}")
    
    async def initialize(self):
        try:
            self.logger.info("🚀 Starting service initialization...")
            
            # Step 1
            self.logger.info("📦 Loading configuration...")
            await self._load_config()
            
            # Step 2
            self.logger.info("🔗 Establishing connections...")
            await self._connect()
            
            # Step 3
            self.logger.info("🛠️  Setting up resources...")
            await self._setup_resources()
            
            self.logger.info("✅ Service initialization complete")
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            raise
        finally:
            finalize_streaming_logs(self.logger)
```

## Best Practices

### 1. Use Streaming for Sequential Operations
Perfect for multi-step processes where you want to show progress:
- Framework initialization
- Configuration loading
- Service startup
- Batch processing
- Data migration

### 2. Always Call finalize_streaming_logs()
Ensure final messages remain visible:
```python
try:
    # ... streaming operations
    logger.info("✅ Operation complete")
finally:
    finalize_streaming_logs(logger)
```

### 3. Include Status Indicators
Use emojis and clear status indicators:
- 🚀 Starting/Launching
- 📁 File operations
- 🔧 Configuration
- 🧠 Memory/Data operations
- 🔗 Connections
- ✅ Success
- ⚠️ Warnings
- ❌ Errors

### 4. Handle Interruptions
Ensure streaming is finalized even on interruption:
```python
try:
    # ... streaming operations
except KeyboardInterrupt:
    finalize_streaming_logs(logger)
    logger.error("Operation cancelled by user")
    raise
```

### 5. Keep INFO Messages Concise
Since INFO messages stream on one line, keep them short and descriptive:
```python
# Good
logger.info("🔧 Loading configuration...")

# Avoid - too verbose for single line
logger.info("Loading configuration from /very/long/path/config.json with validation...")
```

## Log Level Behavior

| Level | Behavior |
|-------|----------|
| `INFO` | Streams on single line with carriage return |
| `WARNING` | Always appears on new line |
| `ERROR` | Always appears on new line |
| `CRITICAL` | Always appears on new line |
| `DEBUG` | Follows same pattern as INFO |

## Testing

Use the provided test script to see streaming logger in action:

```bash
python test_streaming_logger.py
```

Or run the demo module directly:

```python
from claude_pm.utils.streaming_logger_demo import demo_streaming_startup
demo_streaming_startup()
```

## Performance Considerations

- Streaming logger has minimal performance overhead
- Uses efficient carriage return mechanism
- No significant impact on logging performance
- Memory usage remains constant

## Compatibility

- Works with all Python 3.7+ versions
- Compatible with existing logging configurations
- Can be mixed with rich logging and file logging
- Terminal agnostic (works in various terminal environments)

## Memory Collection Integration

The streaming logger automatically integrates with the framework's memory collection system for tracking operational insights and user feedback about logging clarity and verbosity improvements.