# Session Store & Context Management

## Overview

The Session Store provides comprehensive session management, conversation history tracking, and context-aware interactions. It automatically stores all user messages, assistant responses, and tool executions, enabling:

- **Conversation continuity** - The agent remembers previous interactions
- **Context-aware responses** - Decisions based on conversation history
- **Tool execution tracking** - Complete audit trail of all tools used
- **Session management** - Multiple concurrent user sessions

## Architecture

### Core Components

#### 1. SessionStore
Central storage for all session data.

**Key Features:**
- Thread-safe session management
- Automatic message storage
- Tool execution tracking
- Context retrieval for LLM
- Session lifecycle management

#### 2. Data Structures

**ChatMessage:**
```python
@dataclass
class ChatMessage:
    role: MessageRole  # USER, ASSISTANT, SYSTEM, TOOL
    content: str
    timestamp: str
    metadata: Dict[str, Any]
```

**ToolExecution:**
```python
@dataclass
class ToolExecution:
    tool_name: str
    tool_params: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    timestamp: str
```

**SessionData:**
```python
@dataclass
class SessionData:
    session_id: str
    messages: List[ChatMessage]
    tool_executions: List[ToolExecution]
    metadata: Dict[str, Any]
    created_at: str
    last_activity: str
```

## Integration

### Automatic Storage

The system automatically stores:

1. **User Messages** - Every user query
2. **Assistant Responses** - All agent responses
3. **Tool Outputs** - Tool executions with parameters and results
4. **System Messages** - Internal system communications

### Flow Diagram

```
User Query
    ↓
session_store.add_user_message()
    ↓
Agent processes query with context
    ├─ Retrieves recent messages
    ├─ Injects into decision prompt
    └─ LLM makes context-aware decision
    ↓
Tool executed (if needed)
    ↓
session_store.add_tool_output()
    ↓
Response generated
    ↓
session_store.add_assistant_message()
    ↓
Response returned to user
```

## Usage Examples

### Example 1: Context-Aware Conversation

**Query 1:**
```
User: "My name is Alice and I'm working on a project"
```

**Stored in session:**
```json
{
  "role": "user",
  "content": "My name is Alice and I'm working on a project",
  "timestamp": "2026-05-01T10:00:00Z"
}
```

**Query 2:**
```
User: "What's my name?"
```

**Context injected into agent:**
```
Recent Conversation Context:
USER: My name is Alice and I'm working on a project
ASSISTANT: That's great! How can I help you with your project?

User Query: "What's my name?"
```

**Agent Response:**
```
"Your name is Alice, as you mentioned earlier!"
```

### Example 2: Tool Execution Tracking

**Query:**
```
User: "Get the weather for London"
```

**Agent executes tool and stores:**
```json
{
  "tool_name": "api_caller",
  "tool_params": {
    "endpoint": "weather",
    "city": "London"
  },
  "result": {
    "temperature": "15°C",
    "condition": "Cloudy"
  },
  "success": true,
  "timestamp": "2026-05-01T10:05:00Z"
}
```

**Also stored as tool message:**
```json
{
  "role": "tool",
  "content": "Tool 'api_caller' executed. Result: {\"temperature\": \"15°C\"...}",
  "metadata": {
    "tool_name": "api_caller",
    "success": true
  }
}
```

### Example 3: Multi-Turn Interaction

**Conversation:**
```
User: "Upload my contract document"
Assistant: "Document uploaded successfully"

User: "What are the payment terms?"
Assistant: [Queries document with context]

User: "Get weather for the delivery location"
Assistant: [Uses API with context from document]

User: "Based on both, what do you recommend?"
Assistant: [Synthesizes with full conversation context]
```

All interactions stored and available for context in each subsequent query.

## API Endpoints

### GET /session/{session_id}/summary

Get session summary with statistics.

**Response:**
```json
{
  "session_id": "user123",
  "message_count": 12,
  "tool_execution_count": 3,
  "created_at": "2026-05-01T10:00:00Z",
  "last_activity": "2026-05-01T10:30:00Z",
  "duration_minutes": 30.0
}
```

### GET /session/{session_id}/history?limit=10

Get conversation history.

**Response:**
```json
{
  "session_id": "user123",
  "message_count": 4,
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2026-05-01T10:00:00Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you?",
      "timestamp": "2026-05-01T10:00:01Z",
      "metadata": {
        "query_type": "direct",
        "used_tool": false
      }
    }
  ]
}
```

### GET /session/{session_id}/tools

Get tool execution history.

**Response:**
```json
{
  "session_id": "user123",
  "execution_count": 2,
  "executions": [
    {
      "tool_name": "api_caller",
      "tool_params": {"endpoint": "weather", "city": "London"},
      "result": {"temperature": "15°C"},
      "success": true,
      "timestamp": "2026-05-01T10:05:00Z"
    }
  ]
}
```

### GET /session/{session_id}/context?limit=10

Get recent context in OpenAI format.

**Response:**
```json
{
  "session_id": "user123",
  "context_size": 3,
  "context": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    {"role": "user", "content": "Help me"}
  ]
}
```

### GET /sessions

List all active sessions.

**Response:**
```json
{
  "session_count": 5,
  "sessions": ["user123", "user456", "user789"]
}
```

### DELETE /session/{session_id}

Delete a session.

**Response:**
```json
{
  "message": "Session 'user123' deleted successfully"
}
```

## Code Integration

### ChatService Integration

```python
# Automatically stores messages and uses history
async def process_message(
    self,
    message: str,
    session_id: str,
    use_history: bool = True,
    max_history: int = 10
):
    # Store user message
    self.session_store.add_user_message(session_id, message)
    
    # Build context with history
    context_messages = self._build_context(
        session_id, message, use_history, max_history
    )
    
    # Get LLM response with context
    reply = await self._get_openai_response(context_messages)
    
    # Store assistant response
    self.session_store.add_assistant_message(session_id, reply)
    
    return {"reply": reply}
```

### AgentController Integration

```python
# Injects context into decision-making
async def _make_decision(self, query: str, session_id: str):
    # Get recent conversation context
    recent_context = self._get_recent_context(session_id, limit=5)
    
    # Build decision prompt with context
    decision_prompt = self._build_decision_prompt(
        query, tool_descriptions, recent_context
    )
    
    # Make context-aware decision
    decision = await chat_service.process_message(
        message=decision_prompt,
        session_id=f"agent_decision_{session_id}"
    )
```

### Tool Execution Tracking

```python
# Automatically tracks tool usage
async def _execute_with_tool(self, query, decision, session_id):
    # Execute tool
    tool_result = await tool.safe_execute(**decision.tool_params)
    
    # Store in session
    session_store.add_tool_output(
        session_id=session_id,
        tool_name=decision.tool_name,
        tool_params=decision.tool_params,
        result=tool_result,
        success=tool_result["success"]
    )
```

## Benefits

✅ **Conversation Continuity** - Users don't have to repeat information  
✅ **Context-Aware Decisions** - Agent makes better choices with history  
✅ **Complete Audit Trail** - All messages and tools tracked  
✅ **Multi-Session Support** - Concurrent users with isolated sessions  
✅ **Automatic Storage** - No manual session management needed  
✅ **Flexible Retrieval** - Get history, tools, or context as needed  
✅ **OpenAI Compatible** - Context in format ready for LLM  

## Configuration

### Message Limits

Control how much history to include:

```python
# Get last 5 messages for context
context = session_store.get_recent_context(
    session_id="user123",
    message_limit=5
)

# Get last 20 messages for history
history = session_store.get_conversation_history(
    session_id="user123",
    limit=20
)
```

### Context Injection

Configure context inclusion in chat:

```python
# With history (default)
result = await chat_service.process_message(
    message="What did I ask before?",
    session_id="user123",
    use_history=True,
    max_history=10
)

# Without history
result = await chat_service.process_message(
    message="New topic",
    session_id="user123",
    use_history=False
)
```

## Testing

Run the test suite:

```bash
python test_session_store.py
```

Tests include:
- Basic session creation and storage
- Message history retrieval
- Tool execution tracking
- Context-aware conversations
- Multi-session management

## Performance Considerations

- **In-Memory Storage**: Current implementation uses in-memory dict
- **Scaling**: For production, consider:
  - Redis for distributed sessions
  - PostgreSQL for persistent storage
  - Message TTL/expiration
  - Session cleanup policies

## Future Enhancements

- [ ] Persistent storage (database)
- [ ] Session expiration policies
- [ ] Message summarization for long conversations
- [ ] Export conversation history
- [ ] Session search and filtering
- [ ] Analytics and insights
- [ ] Cross-session memory (user profiles)
