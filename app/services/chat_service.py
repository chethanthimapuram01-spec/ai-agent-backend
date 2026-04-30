"""Chat service for LLM interactions"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.services.session_store import session_store, MessageRole


class ChatService:
    """Service to handle chat interactions with LLM"""
    
    def __init__(self):
        """Initialize the chat service"""
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.use_placeholder = not api_key
        self.session_store = session_store
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        use_history: bool = True,
        max_history: int = 10
    ) -> Dict[str, Any]:
        """
        Process a user message and get LLM response with conversation history
        
        Args:
            message: User message text
            session_id: Session identifier
            use_history: Whether to include conversation history
            max_history: Maximum number of historical messages to include
            
        Returns:
            Dictionary with reply, session_id, and status
        """
        try:
            # Store user message
            self.session_store.add_user_message(session_id, message)
            
            if self.use_placeholder:
                # Placeholder response when OpenAI is not configured
                reply = self._get_placeholder_response(message)
            else:
                # Build context with history
                context_messages = self._build_context(session_id, message, use_history, max_history)
                
                # Call OpenAI API with context
                reply = await self._get_openai_response(context_messages)
            
            # Store assistant response
            self.session_store.add_assistant_message(session_id, reply)
            
            return {
                "reply": reply,
                "session_id": session_id,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            # Still store the error
            self.session_store.add_assistant_message(
                session_id,
                error_msg,
                metadata={"error": True}
            )
            return {
                "reply": error_msg,
                "session_id": session_id,
                "status": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _build_context(
        self,
        session_id: str,
        current_message: str,
        use_history: bool,
        max_history: int
    ) -> List[Dict[str, str]]:
        """Build context messages including history"""
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant."
        })
        
        # Add conversation history if requested
        if use_history:
            history = self.session_store.get_recent_context(
                session_id,
                message_limit=max_history,
                include_system=False
            )
            # Don't include the current user message (it was just added to store)
            # Filter it out and add separately
            history = [msg for msg in history if msg.get("role") != "user" or msg.get("content") != current_message]
            messages.extend(history)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
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
    
    async def _get_openai_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get response from OpenAI API with conversation context
        
        Args:
            messages: List of messages in OpenAI format (with history)
            
        Returns:
            AI-generated response string
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content


# Singleton instance
chat_service = ChatService()
