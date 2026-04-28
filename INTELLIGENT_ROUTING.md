# Intelligent Agent Routing System

## Overview

The AgentController now features intelligent routing logic that automatically determines the best way to handle user queries without requiring manual endpoint selection.

## Query Classification

The system classifies queries into four types:

### 1. Direct Response
Simple questions that don't require external data or documents.

**Examples:**
- "What is AI?"
- "Explain machine learning"
- "Hello, how are you?"

**Handling:** LLM responds directly without using tools.

### 2. Document Question
Questions about uploaded documents or content (RAG queries).

**Examples:**
- "Summarize the uploaded contract"
- "What does the document say about pricing?"
- "Find information about deadlines in the uploaded files"

**Tool Used:** `document_query`

**How it works:**
1. Performs semantic search over document chunks
2. Retrieves relevant context
3. Generates answer using LLM with retrieved context
4. Returns answer with source citations

### 3. API Request
Questions requiring external API data.

**Examples:**
- "Get weather for London"
- "What's the Bitcoin price?"
- "Fetch user data from the API"

**Tool Used:** `api_caller`

**Supported Endpoints:**
- `weather` - Get weather data for a city
- `crypto` - Get cryptocurrency prices
- `placeholder` - Fetch sample data from JSONPlaceholder API

### 4. Multi-Step Task
Complex queries requiring multiple operations or tools.

**Examples:**
- "Get weather and summarize it"
- "Read document and compare with weather impact"
- "Fetch data from API and analyze it"

**Handling:** Multi-step orchestration workflow:
1. Executes first tool
2. Accumulates context from results
3. Synthesizes final answer using LLM

## Architecture

### Components

1. **AgentController** (`app/agents/agent_controller.py`)
   - Main orchestrator for query processing
   - Handles decision-making and execution
   - Supports multi-step workflows

2. **DocumentQueryTool** (`app/tools/document_query_tool.py`)
   - RAG-based document querying
   - Semantic search over uploaded documents
   - Context-aware answer generation

3. **AgentDecision** (Data class)
   - Represents routing decisions
   - Tracks query type and multi-step status

4. **QueryType** (Constants)
   - DIRECT
   - DOCUMENT
   - API
   - MULTI_STEP

### Decision Flow

```
User Query
    ↓
AgentController.process_query()
    ↓
_make_decision()
    ↓
Build decision prompt with available tools
    ↓
LLM analyzes query and selects action
    ↓
_parse_decision_response()
    ↓
Classify query type
    ↓
Execute appropriate handler:
    - _execute_direct_response()
    - _execute_with_tool()
    - _execute_multi_step()
    ↓
Format and return response
```

## API Usage

### Endpoint: POST /agent

**Request:**
```json
{
  "query": "Summarize the uploaded contract",
  "session_id": "user123",
  "context": {}  // optional
}
```

**Response:**
```json
{
  "response": "The contract outlines... [answer with sources]",
  "session_id": "user123",
  "timestamp": "2026-04-29T10:30:00Z",
  "success": true,
  "decision": {
    "use_tool": true,
    "tool_name": "document_query",
    "query_type": "document",
    "is_multi_step": false,
    "reasoning": "Query about uploaded documents"
  },
  "tool_results": {
    "answer": "...",
    "sources": [...],
    "chunks_used": 5
  }
}
```

## Example Queries and Routing

### Example 1: Direct Response
**Query:** `"What is machine learning?"`

**Routing:**
- Type: DIRECT
- Tool: None
- Response: LLM generates educational response

### Example 2: Document Query
**Query:** `"Summarize the uploaded contract"`

**Routing:**
- Type: DOCUMENT
- Tool: document_query
- Process:
  1. Semantic search for "contract" content
  2. Retrieve top 5 relevant chunks
  3. LLM generates summary with context
  4. Return answer with source citations

### Example 3: API Request
**Query:** `"Get weather for London"`

**Routing:**
- Type: API
- Tool: api_caller
- Parameters:
  ```json
  {
    "endpoint": "weather",
    "city": "London"
  }
  ```

### Example 4: Multi-Step Task
**Query:** `"Get weather and summarize its impact"`

**Routing:**
- Type: MULTI_STEP
- First Tool: api_caller (weather)
- Process:
  1. Execute weather API call
  2. Accumulate weather data context
  3. Synthesize impact summary using LLM
  4. Return comprehensive response

## Decision Prompt

The system uses a structured prompt to guide the LLM's routing decisions:

```
You are an intelligent routing agent. Analyze the user query and determine the best action.

User Query: "{query}"

Available Tools:
[Tool descriptions with schemas]

Query Classification Guidelines:
1. DIRECT RESPONSE - Simple questions...
2. DOCUMENT QUESTION - Questions about uploaded documents...
3. API REQUEST - Questions requiring external API data...
4. MULTI-STEP TASK - Complex queries requiring multiple operations...

Response Format:
- Direct response: DIRECT: [your helpful response]
- Tool usage: TOOL: [tool_name] | PARAMS: {...} | REASON: [explanation]
```

## Logging and Observability

All routing decisions are logged with:
- Query type classification
- Tool selection reasoning
- Multi-step detection
- Execution success/failure
- Timestamp and session tracking

**Log Example:**
```json
{
  "timestamp": "2026-04-29T10:30:00Z",
  "session_id": "user123",
  "query": "Summarize the uploaded contract",
  "use_tool": true,
  "tool_name": "document_query",
  "query_type": "document",
  "is_multi_step": false,
  "reasoning": "Query requires document analysis"
}
```

## Configuration

### Registering Tools

Tools are registered in `app/main.py` on startup:

```python
@app.on_event("startup")
async def startup_event():
    calculator = CalculatorTool()
    text_analyzer = TextAnalyzerTool()
    api_caller = ApiCallerTool()
    document_query = DocumentQueryTool()
    
    tool_registry.register(calculator)
    tool_registry.register(text_analyzer)
    tool_registry.register(api_caller)
    tool_registry.register(document_query)
```

### Tool Requirements

Each tool must implement:
- `metadata` property with name, description, input_schema
- `execute(**kwargs)` async method
- Return format: `{"success": bool, "result": Any, "error": Optional[str]}`

## Benefits

1. **No Manual Endpoint Selection** - Users send queries to a single `/agent` endpoint
2. **Intelligent Tool Selection** - LLM chooses the right tool based on query intent
3. **Multi-Step Support** - Handles complex workflows automatically
4. **Source Citations** - Document queries include source references
5. **Comprehensive Logging** - Full observability of routing decisions
6. **Extensible** - Easy to add new tools and query types

## Future Enhancements

- [ ] Advanced multi-step planning with dependency graphs
- [ ] Tool chaining based on output/input compatibility
- [ ] Confidence scoring for routing decisions
- [ ] Caching for repeated queries
- [ ] A/B testing different routing strategies
- [ ] User feedback integration for routing improvements
