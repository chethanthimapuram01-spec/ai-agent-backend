# Agent Architecture Documentation

## Overview

This backend implements a reusable agent architecture with clean separation between LLM logic and tool execution. The system allows AI agents to intelligently decide whether to use tools or respond directly to user queries.

## Architecture Components

### 1. BaseTool Interface (`app/tools/base_tool.py`)

Abstract base class that all tools must inherit from.

**Key Features:**
- Tool metadata (name, description, input schema, version)
- Input validation based on JSON schema
- Safe execution with error handling
- Type checking for parameters

**Tool Metadata:**
```python
class ToolMetadata:
    name: str                    # Unique tool identifier
    description: str             # What the tool does
    input_schema: Dict[str, Any] # JSON schema for inputs
    version: str                 # Tool version
    enabled: bool                # Enable/disable flag
```

**Required Methods:**
- `metadata` property: Returns ToolMetadata
- `execute(**kwargs)`: Performs the tool's action

### 2. ToolRegistry (`app/tools/tool_registry.py`)

Centralized singleton registry for managing all tools.

**Capabilities:**
- Register/unregister tools
- Enable/disable tools dynamically
- Retrieve tools by name
- List all tools or only enabled tools
- Get tool metadata

**Usage:**
```python
from app.tools.tool_registry import tool_registry

# Register a tool
tool_registry.register(my_tool)

# Get a tool
tool = tool_registry.get_tool("calculator")

# List enabled tools
enabled = tool_registry.get_enabled_tools()
```

### 3. AgentController (`app/agents/agent_controller.py`)

Orchestrates the agent execution flow with intelligent decision-making.

**Execution Flow:**
1. **Receive Query**: User sends a query with session context
2. **Analyze & Decide**: Agent analyzes query and available tools
3. **Make Decision**: 
   - Use LLM to decide: direct response vs tool usage
   - Select appropriate tool if needed
   - Extract tool parameters
4. **Execute**: 
   - Execute selected tool with validation
   - OR generate direct LLM response
5. **Log & Return**: Log decision and return formatted response

**Decision Process:**
- Builds prompt with available tool descriptions
- Uses LLM to analyze whether tools are needed
- Parses LLM response to extract decision
- Validates tool availability and parameters

**Decision Logging:**
All decisions are logged with:
- Timestamp
- Session ID
- Query
- Decision (use_tool, tool_name, reasoning)
- Execution results

## API Endpoints

### Agent Endpoints

#### POST `/agent`
Process query through intelligent agent workflow.

**Request:**
```json
{
  "query": "Calculate 15 + 27",
  "session_id": "user123",
  "context": {}
}
```

**Response:**
```json
{
  "response": "I used the 'calculator' tool to help with your request...",
  "session_id": "user123",
  "timestamp": "2026-04-23T10:30:00.000Z",
  "success": true,
  "decision": {
    "use_tool": true,
    "tool_name": "calculator",
    "reasoning": "User wants to perform arithmetic",
    "timestamp": "2026-04-23T10:30:00.000Z"
  },
  "tool_results": {
    "success": true,
    "result": {"operation": "add", "input": {"a": 15, "b": 27}, "output": 42}
  }
}
```

#### GET `/agent/history/{session_id}`
Get execution history for a session.

**Parameters:**
- `session_id`: Session identifier
- `limit`: Max records (default: 10)

### Tools Management Endpoints

#### GET `/tools`
List all registered tools with metadata.

#### GET `/tools/enabled`
List names of enabled tools only.

#### GET `/tools/{tool_name}`
Get detailed information about a specific tool.

#### POST `/tools/{tool_name}/enable`
Enable a tool.

#### POST `/tools/{tool_name}/disable`
Disable a tool.

### Chat Endpoint

#### POST `/chat`
Direct chat with LLM (no agent orchestration).

## Creating Custom Tools

### Step 1: Inherit from BaseTool

```python
from app.tools.base_tool import BaseTool, ToolMetadata
from typing import Dict, Any

class MyCustomTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="Does something useful",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "number",
                        "description": "Second parameter"
                    }
                },
                "required": ["param1"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2", 0)
        
        # Your tool logic here
        result = f"Processed: {param1} with {param2}"
        
        return {
            "success": True,
            "result": result,
            "error": None
        }
```

### Step 2: Register the Tool

```python
from app.tools.tool_registry import tool_registry

# Create instance
my_tool = MyCustomTool()

# Register
tool_registry.register(my_tool)
```

### Step 3: Tool is Ready
The agent will automatically:
- Discover the tool when analyzing queries
- Include it in decision-making
- Execute it when appropriate

## Example Tools Included

### 1. CalculatorTool
Performs basic arithmetic operations.

**Operations:** add, subtract, multiply, divide

**Input:**
- `operation`: string (add|subtract|multiply|divide)
- `a`: number
- `b`: number

### 2. TextAnalyzerTool
Analyzes text and returns statistics.

**Input:**
- `text`: string

**Output:**
- character_count
- word_count
- sentence_count
- average_word_length
- unique_words

## Design Principles

### Clean Separation of Concerns
- **Tools**: Self-contained, reusable functionality
- **Registry**: Centralized tool management
- **Agent**: Orchestration and decision-making
- **LLM Service**: Natural language processing

### Extensibility
- Easy to add new tools (inherit BaseTool)
- Tools can be enabled/disabled at runtime
- Pluggable architecture

### Robustness
- Input validation at multiple levels
- Error handling in tool execution
- Safe execution wrapper
- Comprehensive logging

### Observability
- All decisions logged with reasoning
- Execution history tracking
- Tool usage analytics

## Configuration

### Environment Variables
```bash
# Required for real LLM responses
OPENAI_API_KEY=your_api_key_here

# Optional: Logging level
LOG_LEVEL=INFO
```

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Access API documentation
# http://localhost:8000/docs
```

## Testing Examples

### Test Calculator Tool
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 50 divided by 5?",
    "session_id": "test123"
  }'
```

### Test Text Analyzer Tool
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this text: Hello world, this is a test.",
    "session_id": "test123"
  }'
```

### Test Direct Response
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "session_id": "test123"
  }'
```

### List Available Tools
```bash
curl http://localhost:8000/tools
```

## Future Enhancements

- [ ] Conversation history management
- [ ] Multi-tool chaining
- [ ] Streaming responses
- [ ] Tool parameter extraction from natural language
- [ ] Tool metrics and usage analytics
- [ ] Custom tool discovery from external sources
- [ ] Per-session tool filtering
- [ ] Tool rate limiting
- [ ] Tool result caching
