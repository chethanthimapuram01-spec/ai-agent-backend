"""Chat endpoint for user-AI interactions"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.chat_service import chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    message: str = Field(..., description="User message to send to the AI")
    session_id: str = Field(..., description="Session identifier for tracking conversations")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    reply: str = Field(..., description="AI assistant's response")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Status of the request (success/error)")
    timestamp: Optional[str] = Field(None, description="Timestamp of the response")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint to process user messages and return AI responses
    
    Args:
        request: ChatRequest containing message and session_id
        
    Returns:
        ChatResponse with AI reply, session_id, and status
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")
    
    # Process the message through the chat service
    response = await chat_service.process_message(
        message=request.message,
        session_id=request.session_id
    )
    
    return response
