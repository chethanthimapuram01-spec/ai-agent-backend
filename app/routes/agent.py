"""Agent endpoint for intelligent query processing"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.agents.agent_controller import agent_controller

router = APIRouter()


class AgentRequest(BaseModel):
    """Request schema for agent endpoint"""
    query: str = Field(..., description="User query to process")
    session_id: str = Field(..., description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")


class AgentResponse(BaseModel):
    """Response schema for agent endpoint"""
    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session identifier")
    timestamp: str = Field(..., description="Timestamp of response")
    success: bool = Field(..., description="Whether the request was successful")
    decision: Optional[Dict[str, Any]] = Field(None, description="Decision details")
    tool_results: Optional[Dict[str, Any]] = Field(None, description="Tool execution results if applicable")


@router.post("/agent", response_model=AgentResponse)
async def process_agent_query(request: AgentRequest):
    """
    Process query through agent workflow
    
    The agent will:
    1. Analyze the query
    2. Decide whether to use tools or respond directly
    3. Execute tools if needed
    4. Return a comprehensive response
    
    Args:
        request: AgentRequest containing query, session_id, and optional context
        
    Returns:
        AgentResponse with the agent's response and execution details
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")
    
    # Process through agent controller
    result = await agent_controller.process_query(
        query=request.query,
        session_id=request.session_id,
        context=request.context
    )
    
    # Format decision for response
    decision_info = None
    if result.get("decision"):
        decision = result["decision"]
        decision_info = {
            "use_tool": decision.use_tool,
            "tool_name": decision.tool_name,
            "reasoning": decision.reasoning,
            "timestamp": decision.timestamp
        }
    
    return {
        "response": result["response"],
        "session_id": result["session_id"],
        "timestamp": result["timestamp"],
        "success": result["success"],
        "decision": decision_info,
        "tool_results": result.get("tool_results")
    }


@router.get("/agent/history/{session_id}")
async def get_agent_history(session_id: str, limit: int = 10):
    """
    Get agent execution history for a session
    
    Args:
        session_id: Session identifier
        limit: Maximum number of records to return
        
    Returns:
        List of execution records
    """
    history = agent_controller.get_execution_history(
        session_id=session_id,
        limit=limit
    )
    
    return {
        "session_id": session_id,
        "count": len(history),
        "history": history
    }
