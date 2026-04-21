"""Chat service for LLM interactions"""
import os
from datetime import datetime
from typing import Dict, Any
from openai import OpenAI


class ChatService:
    """Service to handle chat interactions with LLM"""
    
    def __init__(self):
        """Initialize the chat service"""
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.use_placeholder = not api_key
    
    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message and get LLM response
        
        Args:
            message: User message text
            session_id: Session identifier
            
        Returns:
            Dictionary with reply, session_id, and status
        """
        try:
            if self.use_placeholder:
                # Placeholder response when OpenAI is not configured
                reply = self._get_placeholder_response(message)
            else:
                # Call OpenAI API
                reply = await self._get_openai_response(message)
            
            return {
                "reply": reply,
                "session_id": session_id,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "reply": f"Error processing message: {str(e)}",
                "session_id": session_id,
                "status": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_placeholder_response(self, message: str) -> str:
        """
        Generate a placeholder response when OpenAI is not configured
        
        Args:
            message: User message text
            
        Returns:
            Placeholder response string
        """
        responses = {
            "hello": "Hello! I'm a placeholder AI assistant. Configure OPENAI_API_KEY to enable real AI responses.",
            "summarize": "Sure, I can help with that. (This is a placeholder response - configure OpenAI to get real summaries)",
            "default": f"I received your message: '{message[:50]}...' (Placeholder mode - set OPENAI_API_KEY for AI responses)"
        }
        
        message_lower = message.lower()
        if "hello" in message_lower or "hi" in message_lower:
            return responses["hello"]
        elif "summarize" in message_lower:
            return responses["summarize"]
        else:
            return responses["default"]
    
    async def _get_openai_response(self, message: str) -> str:
        """
        Get response from OpenAI API
        
        Args:
            message: User message text
            
        Returns:
            AI-generated response string
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content


# Singleton instance
chat_service = ChatService()
