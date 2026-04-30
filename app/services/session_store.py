"""Session store for managing chat history and context"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Represents a single chat message"""
    role: MessageRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    def to_openai_format(self) -> Dict[str, str]:
        """Convert to OpenAI message format"""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class ToolExecution:
    """Represents a tool execution event"""
    tool_name: str
    tool_params: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "result": self.result,
            "success": self.success,
            "timestamp": self.timestamp
        }


@dataclass
class SessionData:
    """Represents a complete session with chat history"""
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    messages: List[ChatMessage] = field(default_factory=list)
    tool_executions: List[ToolExecution] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the session"""
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_activity = datetime.utcnow().isoformat()
        logger.info(f"Added {role.value} message to session {self.session_id}")
    
    def add_tool_execution(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        result: Dict[str, Any],
        success: bool
    ):
        """Add a tool execution record"""
        execution = ToolExecution(
            tool_name=tool_name,
            tool_params=tool_params,
            result=result,
            success=success
        )
        self.tool_executions.append(execution)
        self.last_activity = datetime.utcnow().isoformat()
        logger.info(f"Added tool execution '{tool_name}' to session {self.session_id}")
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages"""
        return self.messages[-limit:] if self.messages else []
    
    def get_messages_for_context(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent messages in OpenAI format for context"""
        recent_messages = self.get_recent_messages(limit)
        return [msg.to_openai_format() for msg in recent_messages]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "tool_execution_count": len(self.tool_executions),
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "duration_minutes": self._calculate_duration()
        }
    
    def _calculate_duration(self) -> float:
        """Calculate session duration in minutes"""
        try:
            start = datetime.fromisoformat(self.created_at)
            end = datetime.fromisoformat(self.last_activity)
            duration = (end - start).total_seconds() / 60
            return round(duration, 2)
        except:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "messages": [msg.to_dict() for msg in self.messages],
            "tool_executions": [exec.to_dict() for exec in self.tool_executions],
            "metadata": self.metadata
        }


class SessionStore:
    """
    Session store for managing chat history and context
    
    Features:
    - Store chat messages by session
    - Track tool executions
    - Retrieve recent context
    - Manage session metadata
    - Support for conversation history
    """
    
    def __init__(self):
        """Initialize the session store"""
        self.sessions: Dict[str, SessionData] = {}
        logger.info("SessionStore initialized")
    
    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionData:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata
            
        Returns:
            SessionData object
        """
        if session_id in self.sessions:
            logger.info(f"Session {session_id} already exists, returning existing session")
            return self.sessions[session_id]
        
        session = SessionData(
            session_id=session_id,
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData object or None if not found
        """
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> SessionData:
        """
        Get existing session or create new one
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData object
        """
        if session_id in self.sessions:
            return self.sessions[session_id]
        return self.create_session(session_id)
    
    def add_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a user message to session
        
        Args:
            session_id: Session identifier
            content: Message content
            metadata: Optional message metadata
        """
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.USER, content, metadata)
    
    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add an assistant message to session
        
        Args:
            session_id: Session identifier
            content: Message content
            metadata: Optional message metadata
        """
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.ASSISTANT, content, metadata)
    
    def add_system_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a system message to session
        
        Args:
            session_id: Session identifier
            content: Message content
            metadata: Optional message metadata
        """
        session = self.get_or_create_session(session_id)
        session.add_message(MessageRole.SYSTEM, content, metadata)
    
    def add_tool_output(
        self,
        session_id: str,
        tool_name: str,
        tool_params: Dict[str, Any],
        result: Dict[str, Any],
        success: bool
    ):
        """
        Add a tool execution record to session
        
        Args:
            session_id: Session identifier
            tool_name: Name of the tool executed
            tool_params: Parameters passed to the tool
            result: Tool execution result
            success: Whether execution was successful
        """
        session = self.get_or_create_session(session_id)
        session.add_tool_execution(tool_name, tool_params, result, success)
        
        # Also add as a tool message for context
        tool_summary = f"Tool '{tool_name}' executed. Result: {json.dumps(result, indent=2)[:200]}..."
        session.add_message(
            MessageRole.TOOL,
            tool_summary,
            metadata={
                "tool_name": tool_name,
                "success": success
            }
        )
    
    def get_recent_context(
        self,
        session_id: str,
        message_limit: int = 10,
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context for LLM
        
        Args:
            session_id: Session identifier
            message_limit: Maximum number of messages to retrieve
            include_system: Whether to include system messages
            
        Returns:
            List of messages in OpenAI format
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.get_messages_for_context(message_limit)
        
        if not include_system:
            messages = [msg for msg in messages if msg.get("role") != "system"]
        
        return messages
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete conversation history
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages if limit is None else session.messages[-limit:]
        return [msg.to_dict() for msg in messages]
    
    def get_tool_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tool execution history
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of executions
            
        Returns:
            List of tool execution dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        executions = session.tool_executions if limit is None else session.tool_executions[-limit:]
        return [exec.to_dict() for exec in executions]
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session summary
        
        Args:
            session_id: Session identifier
            
        Returns:
            Summary dictionary or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.get_conversation_summary()
    
    def list_sessions(self) -> List[str]:
        """
        List all session IDs
        
        Returns:
            List of session IDs
        """
        return list(self.sessions.keys())
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def clear_all_sessions(self):
        """Clear all sessions"""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared {count} sessions")


# Singleton instance
session_store = SessionStore()
