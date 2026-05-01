"""Workflow trace endpoints for monitoring and debugging"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.services.trace_logger import trace_logger

router = APIRouter()


class TraceResponse(BaseModel):
    """Single trace entry response"""
    task_id: str
    session_id: str
    step_number: int
    selected_tool: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: str
    execution_time_ms: Optional[float]
    error_message: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]


class TaskTracesResponse(BaseModel):
    """Response for task traces"""
    task_id: str
    trace_count: int
    traces: List[Dict[str, Any]]


class TaskSummaryResponse(BaseModel):
    """Task execution summary"""
    task_id: str
    session_id: Optional[str]
    total_steps: int
    completed_steps: int
    failed_steps: int
    pending_steps: int
    total_execution_time_ms: float
    tools_used: List[str]
    status: Optional[str]
    started_at: Optional[str]
    last_update: Optional[str]


@router.get("/workflow-trace/{task_id}", response_model=TaskTracesResponse)
async def get_workflow_traces(task_id: str):
    """
    Get all trace logs for a specific workflow task
    
    Returns complete execution trace showing:
    - Each step executed
    - Tool used at each step
    - Input and output data
    - Execution time
    - Success/failure status
    - Error messages (if any)
    
    This is essential for:
    - Debugging workflow issues
    - Performance monitoring
    - Understanding execution flow
    - Auditing tool usage
    
    Args:
        task_id: Workflow task identifier
        
    Returns:
        Complete trace history for the task
    """
    traces = trace_logger.get_task_traces(task_id)
    
    if not traces:
        raise HTTPException(
            status_code=404,
            detail=f"No traces found for task '{task_id}'"
        )
    
    return {
        "task_id": task_id,
        "trace_count": len(traces),
        "traces": traces
    }


@router.get("/workflow-trace/{task_id}/summary", response_model=TaskSummaryResponse)
async def get_task_summary(task_id: str):
    """
    Get execution summary for a workflow task
    
    Provides high-level statistics:
    - Total steps and their status
    - Overall execution time
    - Tools used
    - Success/failure status
    
    Args:
        task_id: Workflow task identifier
        
    Returns:
        Task execution summary
    """
    summary = trace_logger.get_task_summary(task_id)
    
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No traces found for task '{task_id}'"
        )
    
    return summary


@router.get("/workflow-traces/session/{session_id}")
async def get_session_traces(
    session_id: str,
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum traces to return")
):
    """
    Get all workflow traces for a session
    
    Returns traces from all workflows executed in this session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of traces to return
        
    Returns:
        List of traces for the session
    """
    traces = trace_logger.get_session_traces(session_id, limit=limit)
    
    return {
        "session_id": session_id,
        "trace_count": len(traces),
        "traces": traces
    }


@router.get("/workflow-traces/recent")
async def get_recent_traces(
    limit: int = Query(100, ge=1, le=1000, description="Maximum traces to return")
):
    """
    Get recent workflow traces across all tasks
    
    Useful for:
    - Monitoring recent activity
    - Debugging recent issues
    - System health overview
    
    Args:
        limit: Maximum number of traces to return
        
    Returns:
        Recent traces ordered by timestamp (newest first)
    """
    traces = trace_logger.get_recent_traces(limit=limit)
    
    return {
        "trace_count": len(traces),
        "traces": traces
    }


@router.delete("/workflow-trace/{task_id}")
async def delete_task_traces(task_id: str):
    """
    Delete all traces for a specific task
    
    Args:
        task_id: Workflow task identifier
        
    Returns:
        Success message
    """
    success = trace_logger.delete_task_traces(task_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete traces for task '{task_id}'"
        )
    
    return {
        "message": f"Traces for task '{task_id}' deleted successfully"
    }


@router.post("/workflow-traces/clear")
async def clear_all_traces():
    """
    Clear all workflow traces (use with caution!)
    
    This will delete all trace history from the database.
    
    Returns:
        Success message
    """
    success = trace_logger.clear_all_traces()
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to clear traces"
        )
    
    return {
        "message": "All workflow traces cleared successfully"
    }
