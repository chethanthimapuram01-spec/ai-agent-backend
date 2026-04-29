"""Workflow endpoints for multi-step task execution"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.agents.workflow_executor import workflow_executor

router = APIRouter()


class WorkflowRequest(BaseModel):
    """Request schema for workflow execution"""
    query: str = Field(..., description="Complex query requiring multi-step execution")
    session_id: str = Field(..., description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")


class WorkflowResponse(BaseModel):
    """Response schema for workflow execution"""
    success: bool = Field(..., description="Whether workflow completed successfully")
    workflow_id: str = Field(..., description="Unique workflow identifier")
    response: Optional[str] = Field(None, description="Final synthesized response")
    error: Optional[str] = Field(None, description="Error message if failed")
    workflow_state: Dict[str, Any] = Field(..., description="Complete workflow state")


class WorkflowStateResponse(BaseModel):
    """Response schema for workflow state query"""
    workflow_id: str
    status: str
    query: str
    steps: List[Dict[str, Any]]
    intermediate_data: Dict[str, Any]
    final_result: Optional[str]
    created_at: str
    completed_at: Optional[str]


@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a multi-step workflow
    
    This endpoint handles complex queries that require:
    - Multiple tool invocations
    - Data passing between steps
    - Sequential or dependent operations
    - Final result synthesis
    
    Example queries:
    - "Find details from the uploaded document, call weather API, and generate a recommendation"
    - "Get Bitcoin price, analyze the trend, and summarize findings"
    - "Read contract terms, fetch relevant regulations, and provide compliance analysis"
    
    The workflow executor will:
    1. Analyze the task
    2. Create an execution plan
    3. Execute steps sequentially
    4. Pass intermediate data between steps
    5. Generate a final comprehensive answer
    
    Args:
        request: WorkflowRequest with query and session info
        
    Returns:
        WorkflowResponse with execution results and state
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")
    
    # Execute workflow
    result = await workflow_executor.execute_workflow(
        query=request.query,
        session_id=request.session_id,
        context=request.context
    )
    
    return result


@router.get("/workflow/{workflow_id}", response_model=WorkflowStateResponse)
async def get_workflow_state(workflow_id: str):
    """
    Get the state of a specific workflow
    
    Retrieves detailed information about a workflow execution including:
    - Current status
    - All steps and their results
    - Intermediate data
    - Final result (if completed)
    
    Args:
        workflow_id: Unique workflow identifier
        
    Returns:
        WorkflowStateResponse with complete workflow state
    """
    workflow_state = workflow_executor.get_workflow_state(workflow_id)
    
    if not workflow_state:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found"
        )
    
    return workflow_state.to_dict()


@router.get("/workflow")
async def list_workflows(session_id: Optional[str] = None):
    """
    List all workflows, optionally filtered by session
    
    Args:
        session_id: Optional session ID to filter workflows
        
    Returns:
        List of workflow summaries
    """
    workflows = workflow_executor.list_workflows(session_id=session_id)
    
    return {
        "count": len(workflows),
        "workflows": workflows
    }
