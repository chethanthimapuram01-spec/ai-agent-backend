"""Workflow trace logging system for tracking execution"""
import json
import sqlite3
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TraceStatus(Enum):
    """Status of a trace step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowTrace:
    """
    Represents a single trace entry in workflow execution
    
    Tracks every step with complete details for debugging and monitoring
    """
    task_id: str
    session_id: str
    step_number: int
    selected_tool: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: TraceStatus
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary"""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "step_number": self.step_number,
            "selected_tool": self.selected_tool,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class TraceLogger:
    """
    Workflow trace logger with SQLite storage
    
    Features:
    - Persistent SQLite storage
    - Step-by-step execution tracking
    - Performance monitoring
    - Error tracking
    - Query by task_id or session_id
    """
    
    def __init__(self, db_path: str = "./traces.db"):
        """
        Initialize trace logger with SQLite database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"TraceLogger initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database and create tables if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create traces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                selected_tool TEXT,
                input_data TEXT NOT NULL,
                output_data TEXT,
                status TEXT NOT NULL,
                execution_time_ms REAL,
                error_message TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                UNIQUE(task_id, step_number)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_id 
            ON workflow_traces(task_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON workflow_traces(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON workflow_traces(timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
    
    def log_trace(self, trace: WorkflowTrace) -> bool:
        """
        Log a workflow trace to database
        
        Args:
            trace: WorkflowTrace object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO workflow_traces 
                (task_id, session_id, step_number, selected_tool, input_data, 
                 output_data, status, execution_time_ms, error_message, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace.task_id,
                trace.session_id,
                trace.step_number,
                trace.selected_tool,
                json.dumps(trace.input_data),
                json.dumps(trace.output_data) if trace.output_data else None,
                trace.status.value,
                trace.execution_time_ms,
                trace.error_message,
                trace.timestamp,
                json.dumps(trace.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(
                f"Logged trace: task_id={trace.task_id}, "
                f"step={trace.step_number}, tool={trace.selected_tool}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error logging trace: {str(e)}", exc_info=True)
            return False
    
    def get_task_traces(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all traces for a specific task
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of trace dictionaries ordered by step_number
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM workflow_traces 
                WHERE task_id = ?
                ORDER BY step_number ASC
            """, (task_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            traces = []
            for row in rows:
                trace = dict(row)
                # Parse JSON fields
                trace['input_data'] = json.loads(trace['input_data'])
                trace['output_data'] = json.loads(trace['output_data']) if trace['output_data'] else None
                trace['metadata'] = json.loads(trace['metadata']) if trace['metadata'] else {}
                traces.append(trace)
            
            return traces
            
        except Exception as e:
            logger.error(f"Error getting task traces: {str(e)}", exc_info=True)
            return []
    
    def get_session_traces(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all traces for a specific session
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of traces
            
        Returns:
            List of trace dictionaries ordered by timestamp
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM workflow_traces 
                WHERE session_id = ?
                ORDER BY timestamp DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (session_id,))
            rows = cursor.fetchall()
            conn.close()
            
            traces = []
            for row in rows:
                trace = dict(row)
                trace['input_data'] = json.loads(trace['input_data'])
                trace['output_data'] = json.loads(trace['output_data']) if trace['output_data'] else None
                trace['metadata'] = json.loads(trace['metadata']) if trace['metadata'] else {}
                traces.append(trace)
            
            return traces
            
        except Exception as e:
            logger.error(f"Error getting session traces: {str(e)}", exc_info=True)
            return []
    
    def get_recent_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent traces across all tasks
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of trace dictionaries ordered by timestamp (newest first)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM workflow_traces 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            traces = []
            for row in rows:
                trace = dict(row)
                trace['input_data'] = json.loads(trace['input_data'])
                trace['output_data'] = json.loads(trace['output_data']) if trace['output_data'] else None
                trace['metadata'] = json.loads(trace['metadata']) if trace['metadata'] else {}
                traces.append(trace)
            
            return traces
            
        except Exception as e:
            logger.error(f"Error getting recent traces: {str(e)}", exc_info=True)
            return []
    
    def get_task_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary statistics for a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Summary dictionary with statistics or None if not found
        """
        traces = self.get_task_traces(task_id)
        
        if not traces:
            return None
        
        total_steps = len(traces)
        completed_steps = sum(1 for t in traces if t['status'] == 'completed')
        failed_steps = sum(1 for t in traces if t['status'] == 'failed')
        total_time = sum(t['execution_time_ms'] or 0 for t in traces)
        
        tools_used = [t['selected_tool'] for t in traces if t['selected_tool']]
        
        return {
            "task_id": task_id,
            "session_id": traces[0]['session_id'] if traces else None,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "pending_steps": total_steps - completed_steps - failed_steps,
            "total_execution_time_ms": total_time,
            "tools_used": tools_used,
            "status": traces[-1]['status'] if traces else None,
            "started_at": traces[0]['timestamp'] if traces else None,
            "last_update": traces[-1]['timestamp'] if traces else None
        }
    
    def delete_task_traces(self, task_id: str) -> bool:
        """
        Delete all traces for a specific task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM workflow_traces WHERE task_id = ?", (task_id,))
            
            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()
            
            logger.info(f"Deleted {deleted_count} traces for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting task traces: {str(e)}", exc_info=True)
            return False
    
    def clear_all_traces(self) -> bool:
        """
        Clear all traces from database (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM workflow_traces")
            
            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()
            
            logger.info(f"Cleared all traces ({deleted_count} records)")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing traces: {str(e)}", exc_info=True)
            return False


# Singleton instance
trace_logger = TraceLogger()
