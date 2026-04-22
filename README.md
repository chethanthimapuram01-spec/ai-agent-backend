# AI Agent Backend

A powerful, production-ready backend service for building AI agents with intelligent tool orchestration and LLM integration.

## 🚀 Features

- **Intelligent Agent System**: Automatically decides when to use tools vs direct responses
- **Tool Registry**: Centralized management of reusable tools
- **Clean Architecture**: Clear separation between LLM logic and tool execution
- **OpenAI Integration**: Ready-to-use LLM integration with placeholder mode
- **RESTful API**: FastAPI-based endpoints for chat, agent, and tool management
- **Extensible**: Easy to add custom tools with standardized interface
- **Production-Ready**: Comprehensive logging, error handling, and validation

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Creating Custom Tools](#creating-custom-tools)
- [Documentation](#documentation)
- [Examples](#examples)

## 🏃 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-agent-backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
export OPENAI_API_KEY=your_api_key_here

# Run the server
uvicorn app.main:app --reload
```

### Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🏗️ Architecture

### Core Components

1. **BaseTool** (`app/tools/base_tool.py`)
   - Abstract interface for all tools
   - Automatic input validation
   - Standardized metadata and execution

2. **ToolRegistry** (`app/tools/tool_registry.py`)
   - Singleton pattern for centralized tool management
   - Enable/disable tools dynamically
   - Query available tools

3. **AgentController** (`app/agents/agent_controller.py`)
   - Orchestrates agent execution flow
   - Intelligent decision-making (tool vs direct response)
   - Execution history tracking
   - Comprehensive logging

4. **ChatService** (`app/services/chat_service.py`)
   - OpenAI integration
   - Placeholder mode for development
   - Conversation management

### Data Flow

```
User Query → AgentController → Decision Engine → Tool/LLM → Response
                    ↓
              ToolRegistry
                    ↓
              Available Tools
```

## 📡 API Endpoints

### Agent Endpoints

#### `POST /agent`
Intelligent query processing with tool orchestration.

**Request:**
```json
{
  "query": "Calculate 15 + 27",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "response": "I used the 'calculator' tool...",
  "session_id": "user123",
  "success": true,
  "decision": {
    "use_tool": true,
    "tool_name": "calculator",
    "reasoning": "Math operation detected"
  },
  "tool_results": {...}
}
```

#### `GET /agent/history/{session_id}`
Get execution history for a session.

### Chat Endpoints

#### `POST /chat`
Direct LLM chat without agent orchestration.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "session_id": "abc123"
}
```

### Tool Management Endpoints

- `GET /tools` - List all registered tools
- `GET /tools/enabled` - List enabled tools
- `GET /tools/{tool_name}` - Get tool details
- `POST /tools/{tool_name}/enable` - Enable a tool
- `POST /tools/{tool_name}/disable` - Disable a tool

### Health Check

- `GET /health` - Service health status

## 🔧 Creating Custom Tools

### 1. Create Tool Class

```python
from typing import Dict, Any
from app.tools.base_tool import BaseTool, ToolMetadata

class MyTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="What this tool does",
            input_schema={
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        result = kwargs.get("param")
        return {
            "success": True,
            "result": result,
            "error": None
        }
```

### 2. Register Tool

In `app/main.py`:
```python
from app.tools.my_tool import MyTool

@app.on_event("startup")
async def startup_event():
    my_tool = MyTool()
    tool_registry.register(my_tool)
```

### 3. Use It!

The agent automatically discovers and uses your tool when appropriate.

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation
- **[TOOLS_GUIDE.md](TOOLS_GUIDE.md)** - Quick start guide for creating tools
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when server is running)

## 💡 Examples

### Example 1: Using the Calculator Tool

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 42 multiplied by 7?",
    "session_id": "test"
  }'
```

### Example 2: Using the Text Analyzer Tool

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this: The quick brown fox jumps",
    "session_id": "test"
  }'
```

### Example 3: Direct Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AI?",
    "session_id": "test"
  }'
```

### Example 4: List Available Tools

```bash
curl http://localhost:8000/tools
```

## 🔌 Built-in Tools

### CalculatorTool
Performs basic arithmetic operations.
- Operations: add, subtract, multiply, divide
- Input: operation, a, b

### TextAnalyzerTool
Analyzes text statistics.
- Returns: word count, character count, sentence count, etc.
- Input: text

## 🛠️ Development

### Project Structure

```
ai-agent-backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agent_controller.py    # Main agent orchestration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py              # Health check endpoint
│   │   ├── chat.py                # Chat endpoints
│   │   ├── agent.py               # Agent endpoints
│   │   └── tools.py               # Tool management endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py        # LLM service
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py           # Tool interface
│   │   ├── tool_registry.py       # Tool registry
│   │   └── example_tools.py       # Example tools
│   ├── utils/
│   │   └── __init__.py
│   └── main.py                     # FastAPI app
├── ARCHITECTURE.md                 # Detailed docs
├── TOOLS_GUIDE.md                  # Tool creation guide
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Run tests (when test suite is added)
pytest

# Run with coverage
pytest --cov=app
```

### Logging

Logs are configured in `app/main.py`. Default level: INFO

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🌟 Key Design Principles

1. **Separation of Concerns**: Tools, agents, and LLM logic are decoupled
2. **Extensibility**: Easy to add new tools without modifying core code
3. **Type Safety**: Pydantic models for request/response validation
4. **Observability**: Comprehensive logging and execution history
5. **Developer Experience**: Clear APIs, good documentation, examples

## 🤝 Contributing

1. Create your tool following the BaseTool interface
2. Register it in the tool registry
3. Add tests for your tool
4. Update documentation

## 📝 License

[Add your license here]

## 🔗 Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation
- See [TOOLS_GUIDE.md](TOOLS_GUIDE.md) for tool development help

---

**Made with ❤️ for AI agent development**