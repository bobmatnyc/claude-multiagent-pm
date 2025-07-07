"""
SQLite checkpointing implementation for LangGraph workflows.

Provides persistent state management using SQLite backend, enabling
workflow recovery and continuation across sessions.
"""

import asyncio
import sqlite3
import json
import os
from typing import Any, Dict, Optional, Iterator, Tuple
from datetime import datetime, timezone
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from pathlib import Path

try:
    from ....core.logging_config import get_logger
except ImportError:
    # Fallback for testing
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class SQLiteCheckpointer:
    """
    Enhanced SQLite checkpointer for Claude PM workflows.
    
    Extends LangGraph's SqliteSaver with Claude PM specific features:
    - Memory integration tracking
    - Agent execution metrics
    - Workflow analytics
    """
    
    def __init__(self, db_path: str, table_name: str = "checkpoints"):
        """
        Initialize SQLite checkpointer.
        
        Args:
            db_path: Path to SQLite database file
            table_name: Name of the table to store checkpoints
        """
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize LangGraph SqliteSaver
        self.saver = SqliteSaver.from_conn_string(f"sqlite:///{self.db_path}")
        
        # Initialize our custom tables
        self._init_custom_tables()
        
    def _init_custom_tables(self) -> None:
        """Initialize custom tables for Claude PM metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Workflow metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workflow_id TEXT NOT NULL,
                        agent_name TEXT,
                        execution_time_ms INTEGER,
                        tokens_used INTEGER,
                        cost_usd REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                # Agent performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_name TEXT NOT NULL,
                        workflow_id TEXT NOT NULL,
                        task_type TEXT,
                        success BOOLEAN,
                        confidence_score REAL,
                        execution_time_ms INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Memory integration tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workflow_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        memory_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info(f"Initialized custom tables in {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize custom tables: {e}")
            raise
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> None:
        """Store checkpoint asynchronously."""
        return await asyncio.to_thread(
            self.saver.put,
            config,
            checkpoint,
            metadata
        )
    
    async def aget(
        self,
        config: Dict[str, Any]
    ) -> Optional[Checkpoint]:
        """Retrieve checkpoint asynchronously."""
        return await asyncio.to_thread(
            self.saver.get,
            config
        )
    
    async def alist(
        self,
        config: Dict[str, Any],
        before: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Iterator[Tuple[Dict[str, Any], Checkpoint]]:
        """List checkpoints asynchronously."""
        return await asyncio.to_thread(
            self.saver.list,
            config,
            before=before,
            limit=limit
        )
    
    def record_agent_execution(
        self,
        workflow_id: str,
        agent_name: str,
        execution_time_ms: int,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record agent execution metrics.
        
        Args:
            workflow_id: Workflow identifier
            agent_name: Name of the executing agent
            execution_time_ms: Execution time in milliseconds
            tokens_used: Number of tokens consumed
            cost_usd: Cost in USD
            metadata: Additional metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO workflow_metrics 
                    (workflow_id, agent_name, execution_time_ms, tokens_used, cost_usd, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    workflow_id,
                    agent_name,
                    execution_time_ms,
                    tokens_used,
                    cost_usd,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to record agent execution: {e}")
    
    def record_agent_performance(
        self,
        workflow_id: str,
        agent_name: str,
        task_type: str,
        success: bool,
        confidence_score: float,
        execution_time_ms: int
    ) -> None:
        """Record agent performance metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_performance
                    (workflow_id, agent_name, task_type, success, confidence_score, execution_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    workflow_id,
                    agent_name,
                    task_type,
                    success,
                    confidence_score,
                    execution_time_ms
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to record agent performance: {e}")
    
    def record_memory_usage(
        self,
        workflow_id: str,
        memory_type: str,
        operation: str,
        memory_id: Optional[str] = None
    ) -> None:
        """Record memory system usage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memory_usage
                    (workflow_id, memory_type, operation, memory_id)
                    VALUES (?, ?, ?, ?)
                """, (workflow_id, memory_type, operation, memory_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to record memory usage: {e}")
    
    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a workflow."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get execution metrics
                cursor.execute("""
                    SELECT 
                        agent_name,
                        SUM(execution_time_ms) as total_time,
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as execution_count
                    FROM workflow_metrics 
                    WHERE workflow_id = ?
                    GROUP BY agent_name
                """, (workflow_id,))
                
                agent_metrics = {row['agent_name']: dict(row) for row in cursor.fetchall()}
                
                # Get performance metrics
                cursor.execute("""
                    SELECT 
                        agent_name,
                        task_type,
                        AVG(confidence_score) as avg_confidence,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM agent_performance
                    WHERE workflow_id = ?
                    GROUP BY agent_name, task_type
                """, (workflow_id,))
                
                performance_metrics = {}
                for row in cursor.fetchall():
                    agent = row['agent_name']
                    if agent not in performance_metrics:
                        performance_metrics[agent] = {}
                    performance_metrics[agent][row['task_type']] = {
                        'avg_confidence': row['avg_confidence'],
                        'success_rate': row['success_rate']
                    }
                
                return {
                    'agent_metrics': agent_metrics,
                    'performance_metrics': performance_metrics
                }
                
        except Exception as e:
            logger.error(f"Failed to get workflow metrics: {e}")
            return {}
    
    def cleanup_old_checkpoints(self, retention_days: int = 30) -> int:
        """Clean up old checkpoints beyond retention period."""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old checkpoints (would need LangGraph table schema)
                # For now, clean up our custom tables
                cursor.execute("""
                    DELETE FROM workflow_metrics 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_metrics = cursor.rowcount
                
                cursor.execute("""
                    DELETE FROM agent_performance 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_performance = cursor.rowcount
                
                cursor.execute("""
                    DELETE FROM memory_usage 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_memory = cursor.rowcount
                
                conn.commit()
                
                total_deleted = deleted_metrics + deleted_performance + deleted_memory
                logger.info(f"Cleaned up {total_deleted} old records")
                return total_deleted
                
        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints: {e}")
            return 0


def create_checkpointer(
    db_path: Optional[str] = None,
    table_name: str = "checkpoints"
) -> SQLiteCheckpointer:
    """
    Factory function to create a SQLite checkpointer.
    
    Args:
        db_path: Path to SQLite database file. If None, uses default location.
        table_name: Name of the table to store checkpoints
        
    Returns:
        SQLiteCheckpointer: Configured checkpointer instance
    """
    if db_path is None:
        # Use default path from Claude PM config
        db_path = Path.cwd() / ".claude-pm" / "checkpoints.db"
    
    return SQLiteCheckpointer(str(db_path), table_name)