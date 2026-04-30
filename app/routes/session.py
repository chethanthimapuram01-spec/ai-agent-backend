"""Session management endpoints"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.services.session_store import session_store

router = APIRouter()


class SessionSummary(BaseModel):
    """Session summary response"""
    session_id: str
    message_count: int
    tool_execution_count: int
    created_at: str
    last_activity: str
    duration_minutes: float


class MessageResponse(BaseModel):
    """Chat message response"""
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]


class ToolExecutionResponse(BaseModel):
    """Tool execution response"""
    tool_name: str
    tool_params: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    timestamp: str


@router.get("/session/{session_id}/summary", response_model=SessionSummary)
async def get_session_summary(session_id: str):
    """
    Get summary of a session
    
    Returns:
    - Message count
    - Tool execution count
    - Created and last activity timestamps
    - Session duration
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionSummary with session statistics
    """
    summary = session_store.get_session_summary(session_id)
    
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    
    return summary


@router.get("/session/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of messages")
):
    """
    Get conversation history for a session
    
    Returns all messages (user, assistant, system, tool) in chronological order.
    
    Args:
        session_id: Session identifier
        limit: Optional limit on number of messages
        
    Returns:
        List of messages with role, content, timestamp, and metadata
    """
    history = session_store.get_conversation_history(session_id, limit=limit)
    
    if not history:
        # Check if session exists
        session = session_store.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history
    }


@router.get("/session/{session_id}/tools")
async def get_tool_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of executions")
):
    """
    Get tool execution history for a session
    
    Returns all tool executions with parameters, results, and success status.
    
    Args:
        session_id: Session identifier
        limit: Optional limit on number of executions
        
    Returns:
        List of tool executions
    """
    tool_history = session_store.get_tool_history(session_id, limit=limit)
    
    if not tool_history:
        # Check if session exists
        session = session_store.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )
    
    return {
        "session_id": session_id,
        "execution_count": len(tool_history),
        "executions": tool_history
    }


@router.get("/session/{session_id}/context")
async def get_recent_context(
    session_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent messages")
):
    """
    Get recent conversation context in OpenAI format
    
    Useful for understanding current conversation state.
    Returns messages in format ready for LLM consumption.
    
    Args:
        session_id: Session identifier
        limit: Number of recent messages to retrieve
        
    Returns:
        List of messages in OpenAI format
    """
    context = session_store.get_recent_context(session_id, message_limit=limit)
    
    return {
        "session_id": session_id,
        "context_size": len(context),
        "context": context
    }


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    
    Returns:
        List of session IDs
    """
    sessions = session_store.list_sessions()
    
    return {
        "session_count": len(sessions),
        "sessions": sessions
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and all its data
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    deleted = session_store.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    
    return {
        "message": f"Session '{session_id}' deleted successfully"
    }


@router.post("/sessions/clear")
async def clear_all_sessions():
    """
    Clear all sessions (use with caution!)
    
    Returns:
        Success message
    """
    session_store.clear_all_sessions()
    
    return {
        "message": "All sessions cleared successfully"
    }
