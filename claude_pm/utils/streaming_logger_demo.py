#!/usr/bin/env python3
"""
Streaming Logger Demonstration - Claude Multi-Agent PM Framework

This module demonstrates the single-line streaming INFO logger for cleaner
startup output. Shows how to implement progress indicators that update in place
while preserving error and warning visibility.
"""

import time
import asyncio
from typing import List

from ..core.logging_config import setup_streaming_logger, finalize_streaming_logs


def demo_streaming_startup():
    """
    Demonstrate streaming logger during a simulated startup process.
    """
    # Setup streaming logger
    logger = setup_streaming_logger("startup_demo")
    
    startup_tasks = [
        "Initializing framework components",
        "Loading agent configurations",
        "Validating memory system",
        "Checking service dependencies", 
        "Establishing database connections",
        "Starting background services",
        "Finalizing startup sequence"
    ]
    
    try:
        logger.info("🚀 Starting Claude PM Framework...")
        time.sleep(0.5)
        
        for i, task in enumerate(startup_tasks, 1):
            # Show progress with streaming INFO messages
            logger.info(f"[{i}/{len(startup_tasks)}] {task}...")
            
            # Simulate some work
            time.sleep(0.3)
            
            # Simulate an occasional warning (should appear on new line)
            if i == 3:
                logger.warning("Memory system using fallback configuration")
                
            # Simulate an error (should appear on new line)
            if i == 5:
                logger.error("Database connection timeout - retrying...")
                
        # Final status message
        logger.info("✅ Claude PM Framework startup complete")
        
        # Ensure final message stays visible
        finalize_streaming_logs(logger)
        
        print("\n🎉 Framework ready for operations!")
        
    except KeyboardInterrupt:
        # Ensure we finalize streaming on interruption
        finalize_streaming_logs(logger)
        logger.error("Startup cancelled by user")
        print()


async def demo_async_streaming_startup():
    """
    Demonstrate streaming logger with async operations.
    """
    logger = setup_streaming_logger("async_startup_demo")
    
    startup_operations = [
        ("Loading configuration", 0.2),
        ("Initializing services", 0.4),
        ("Starting memory system", 0.3),
        ("Validating dependencies", 0.2),
        ("Creating agent profiles", 0.5),
        ("Establishing connections", 0.3),
        ("Completing initialization", 0.1)
    ]
    
    try:
        logger.info("🔄 Async startup sequence initiated...")
        await asyncio.sleep(0.2)
        
        for i, (operation, duration) in enumerate(startup_operations, 1):
            logger.info(f"⚡ [{i}/{len(startup_operations)}] {operation}...")
            await asyncio.sleep(duration)
            
            # Simulate occasional issues
            if i == 4:
                logger.warning("Some dependencies are outdated")
            
        logger.info("✨ Async startup sequence completed successfully")
        finalize_streaming_logs(logger)
        
        print("\n🚀 Async framework initialization complete!")
        
    except Exception as e:
        finalize_streaming_logs(logger)
        logger.error(f"Async startup failed: {e}")
        print()


def demo_mixed_logging():
    """
    Demonstrate mixed logging levels with streaming.
    """
    logger = setup_streaming_logger("mixed_demo")
    
    logger.info("Starting mixed logging demonstration...")
    time.sleep(0.5)
    
    logger.info("Processing configuration files...")
    time.sleep(0.3)
    
    logger.warning("Configuration file missing - using defaults")
    
    logger.info("Initializing database connections...")
    time.sleep(0.4)
    
    logger.error("Primary database unavailable - switching to backup")
    
    logger.info("Loading user preferences...")
    time.sleep(0.2)
    
    logger.info("Validating system requirements...")
    time.sleep(0.3)
    
    logger.info("✅ System initialization complete")
    finalize_streaming_logs(logger)
    
    print("\n📋 Mixed logging demonstration finished")


def demo_progress_indicator():
    """
    Demonstrate progress indicator style logging.
    """
    logger = setup_streaming_logger("progress_demo")
    
    total_items = 25
    
    try:
        logger.info("📦 Processing items...")
        
        for i in range(1, total_items + 1):
            percentage = (i / total_items) * 100
            progress_bar = "█" * (i // 2) + "░" * ((total_items - i) // 2)
            
            logger.info(f"Progress: [{progress_bar}] {percentage:.1f}% ({i}/{total_items})")
            time.sleep(0.1)
            
            # Simulate occasional issues
            if i == 10:
                logger.warning("Item 10 required special handling")
            if i == 20:
                logger.error("Item 20 failed validation - skipping")
        
        logger.info("✅ All items processed successfully")
        finalize_streaming_logs(logger)
        
        print("\n🎯 Progress demonstration complete!")
        
    except KeyboardInterrupt:
        finalize_streaming_logs(logger)
        logger.error("Progress cancelled by user")
        print()


if __name__ == "__main__":
    print("🧪 Streaming Logger Demonstrations\n")
    
    print("1. Basic Streaming Startup:")
    demo_streaming_startup()
    print()
    
    print("2. Mixed Logging Levels:")
    demo_mixed_logging()
    print()
    
    print("3. Progress Indicator:")
    demo_progress_indicator()
    print()
    
    print("4. Async Streaming Startup:")
    asyncio.run(demo_async_streaming_startup())
    print()
    
    print("✨ All demonstrations complete!")