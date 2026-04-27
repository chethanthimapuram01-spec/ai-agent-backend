# API Caller Tool - HTTP API Examples

This file contains example HTTP requests to test the ApiCallerTool via the FastAPI endpoints.

## Prerequisites

1. Start the backend server:
```bash
cd ai-agent-backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. The server should be running at `http://localhost:8000`

## Available Endpoints

### 1. List All Tools

Get information about all registered tools:

```bash
curl -X GET http://localhost:8000/tools
```

### 2. Get ApiCallerTool Information

Get detailed information about the api_caller tool:

```bash
curl -X GET http://localhost:8000/tools/api_caller
```

### 3. List Enabled Tools

Get list of all enabled tools:

```bash
curl -X GET http://localhost:8000/tools/enabled
```

## Using the ApiCallerTool via Agent

### Weather API Examples

**Get weather for Hyderabad:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-1",
    "query": "What is the weather in Hyderabad?"
  }'
```

**Get weather for London:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-2",
    "query": "Tell me the current weather in London"
  }'
```

**Get weather for New York:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-3",
    "query": "How is the weather in New York?"
  }'
```

### Cryptocurrency API Examples

**Get Bitcoin price:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-4",
    "query": "What is the current price of Bitcoin?"
  }'
```

**Get Ethereum price:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-5",
    "query": "Show me the price of Ethereum"
  }'
```

**Get Dogecoin price:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-6",
    "query": "What is Dogecoin trading at?"
  }'
```

### JSONPlaceholder API Examples

**Get list of posts:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-7",
    "query": "Show me some sample posts from the API"
  }'
```

**Get specific user:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-8",
    "query": "Get user information for user ID 5"
  }'
```

**Get list of todos:**
```bash
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-9",
    "query": "Fetch some todo items from the placeholder API"
  }'
```

## Direct Tool Execution (if endpoint exists)

If your system has a direct tool execution endpoint, you can call tools directly:

### Weather API Direct Call

```bash
curl -X POST http://localhost:8000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "api_caller",
    "parameters": {
      "endpoint": "weather",
      "city": "Hyderabad"
    }
  }'
```

### Crypto API Direct Call

```bash
curl -X POST http://localhost:8000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "api_caller",
    "parameters": {
      "endpoint": "crypto",
      "crypto_id": "bitcoin"
    }
  }'
```

### Placeholder API Direct Call

```bash
curl -X POST http://localhost:8000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "api_caller",
    "parameters": {
      "endpoint": "placeholder",
      "resource": "users",
      "id": "1"
    }
  }'
```

## PowerShell Examples (Windows)

For Windows PowerShell users:

### Weather API:
```powershell
$body = @{
    session_id = "test-session-1"
    query = "What is the weather in Hyderabad?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/agent/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Crypto API:
```powershell
$body = @{
    session_id = "test-session-2"
    query = "What is the price of Bitcoin?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/agent/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## Python Requests Examples

```python
import requests

# Weather API
response = requests.post(
    "http://localhost:8000/agent/execute",
    json={
        "session_id": "test-session-1",
        "query": "What is the weather in Hyderabad?"
    }
)
print(response.json())

# Crypto API
response = requests.post(
    "http://localhost:8000/agent/execute",
    json={
        "session_id": "test-session-2",
        "query": "Get the price of Ethereum"
    }
)
print(response.json())

# Placeholder API
response = requests.post(
    "http://localhost:8000/agent/execute",
    json={
        "session_id": "test-session-3",
        "query": "Show me sample posts"
    }
)
print(response.json())
```

## Testing Multiple Tools

The agent now has multiple tools (calculator, text_analyzer, api_caller). Test that it can choose the right tool:

```bash
# Should use calculator
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "multi-tool-1",
    "query": "What is 25 multiplied by 4?"
  }'

# Should use text_analyzer
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "multi-tool-2",
    "query": "Analyze this text: Hello world, this is a test"
  }'

# Should use api_caller
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "multi-tool-3",
    "query": "What is the weather in Mumbai?"
  }'
```

## Expected Response Format

All API caller tool responses follow this format:

```json
{
  "success": true,
  "result": {
    "tool_name": "api_caller",
    "status": "success",
    "data": {
      // Endpoint-specific data here
    }
  },
  "error": null
}
```

## Troubleshooting

1. **Connection refused**: Make sure the backend server is running
2. **404 Not Found**: Check the endpoint URL is correct
3. **Tool not found**: Ensure ApiCallerTool is registered (check startup logs)
4. **Timeout errors**: API might be slow or down, try again later
5. **Invalid response**: Check if the external API is available

## Health Check

Verify the server is running:
```bash
curl http://localhost:8000/health
```

## API Documentation

View auto-generated API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
