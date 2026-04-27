# API Caller Tool Documentation

## Overview

The **ApiCallerTool** is a versatile tool that enables AI agents to fetch data from external REST APIs. It supports multiple endpoints including weather data, placeholder API data, and cryptocurrency prices.

## Features

- **Multiple API Support**: Weather, JSONPlaceholder, and Cryptocurrency APIs
- **Async HTTP Calls**: Built with `httpx` for efficient async operations
- **Normalized Output**: Consistent response format across all endpoints
- **Error Handling**: Comprehensive error handling with meaningful error messages
- **Input Validation**: Schema-based input validation

## Supported Endpoints

### 1. Weather API (`endpoint: "weather"`)

Fetches real-time weather information for any city using wttr.in API.

**Required Parameters:**
- `city` (string): Name of the city

**Example Input:**
```json
{
  "endpoint": "weather",
  "city": "Hyderabad"
}
```

**Example Output:**
```json
{
  "success": true,
  "result": {
    "tool_name": "api_caller",
    "status": "success",
    "data": {
      "location": "Hyderabad",
      "temperature_c": "28",
      "temperature_f": "82",
      "weather_description": "Partly cloudy",
      "humidity": "65",
      "feels_like_c": "30",
      "feels_like_f": "86",
      "wind_speed_kmph": "15",
      "pressure": "1013",
      "visibility": "10",
      "uv_index": "7"
    }
  },
  "error": null
}
```

### 2. JSONPlaceholder API (`endpoint: "placeholder"`)

Fetches sample data from JSONPlaceholder - a free fake REST API for testing and prototyping.

**Required Parameters:**
- `resource` (string): Type of resource - one of: `posts`, `users`, `comments`, `albums`, `todos`

**Optional Parameters:**
- `id` (string): Specific resource ID

**Example Input (List):**
```json
{
  "endpoint": "placeholder",
  "resource": "posts"
}
```

**Example Output (List):**
```json
{
  "success": true,
  "result": {
    "tool_name": "api_caller",
    "status": "success",
    "data": {
      "resource": "posts",
      "count": 100,
      "items": [
        {
          "userId": 1,
          "id": 1,
          "title": "sunt aut facere...",
          "body": "quia et suscipit..."
        }
        // ... first 5 items
      ]
    }
  },
  "error": null
}
```

**Example Input (Single Item):**
```json
{
  "endpoint": "placeholder",
  "resource": "users",
  "id": "1"
}
```

**Example Output (Single Item):**
```json
{
  "success": true,
  "result": {
    "tool_name": "api_caller",
    "status": "success",
    "data": {
      "resource": "users",
      "id": "1",
      "data": {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        "address": {...},
        "phone": "1-770-736-8031 x56442",
        "website": "hildegard.org",
        "company": {...}
      }
    }
  },
  "error": null
}
```

### 3. Cryptocurrency API (`endpoint: "crypto"`)

Fetches real-time cryptocurrency prices from CoinGecko API.

**Required Parameters:**
- `crypto_id` (string): Cryptocurrency identifier (e.g., `bitcoin`, `ethereum`, `cardano`, `solana`, `dogecoin`)

**Example Input:**
```json
{
  "endpoint": "crypto",
  "crypto_id": "bitcoin"
}
```

**Example Output:**
```json
{
  "success": true,
  "result": {
    "tool_name": "api_caller",
    "status": "success",
    "data": {
      "cryptocurrency": "bitcoin",
      "price_usd": 67250.50,
      "price_eur": 61800.25,
      "price_inr": 5587125.75,
      "change_24h_usd": 2.45,
      "market_cap_usd": 1318456789012
    }
  },
  "error": null
}
```

## Error Handling

When an error occurs, the tool returns a normalized error response:

```json
{
  "success": false,
  "result": {
    "tool_name": "api_caller",
    "status": "error",
    "data": null
  },
  "error": "Error message describing what went wrong"
}
```

## Usage Examples

### Via API Endpoint

```bash
# Call the agent with the API caller tool
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "query": "What is the weather in Hyderabad?",
    "tool_override": {
      "tool_name": "api_caller",
      "params": {
        "endpoint": "weather",
        "city": "Hyderabad"
      }
    }
  }'
```

### Programmatic Usage

```python
from app.tools.api_caller_tool import ApiCallerTool

# Initialize the tool
api_caller = ApiCallerTool()

# Weather example
weather_result = await api_caller.execute(
    endpoint="weather",
    city="Hyderabad"
)

# Crypto example
crypto_result = await api_caller.execute(
    endpoint="crypto",
    crypto_id="ethereum"
)

# Placeholder example
posts_result = await api_caller.execute(
    endpoint="placeholder",
    resource="posts"
)
```

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "endpoint": {
      "type": "string",
      "description": "The API endpoint to call",
      "enum": ["weather", "placeholder", "crypto"]
    },
    "city": {
      "type": "string",
      "description": "City name for weather endpoint (required for weather)"
    },
    "resource": {
      "type": "string",
      "description": "Resource type for placeholder endpoint",
      "enum": ["posts", "users", "comments", "albums", "todos"]
    },
    "id": {
      "type": "string",
      "description": "Resource ID for placeholder endpoint (optional)"
    },
    "crypto_id": {
      "type": "string",
      "description": "Cryptocurrency ID for crypto endpoint"
    }
  },
  "required": ["endpoint"]
}
```

## Agent Integration

The ApiCallerTool is automatically registered on application startup and available to all AI agents. Agents can use natural language queries, and the system will automatically:

1. Detect when external API data is needed
2. Select the appropriate endpoint
3. Extract required parameters from the query
4. Execute the API call
5. Format and return the results

### Example Agent Queries:

- "What's the weather like in Hyderabad?"
- "Get the price of Bitcoin"
- "Show me some sample posts from the API"
- "What's the temperature in London?"
- "Get user information for user ID 5"

## Technical Details

- **HTTP Client**: Uses `httpx.AsyncClient` for non-blocking async operations
- **Timeout**: 10 seconds per API call
- **Data Normalization**: All responses are normalized to a consistent format
- **Logging**: Comprehensive logging for debugging and monitoring
- **Error Types**: Handles HTTP errors, network errors, and validation errors

## Adding New API Endpoints

To add a new endpoint, update the `API_CONFIGS` dictionary in `api_caller_tool.py`:

```python
API_CONFIGS = {
    "your_endpoint": {
        "base_url": "https://api.example.com/...",
        "method": "GET",
        "description": "Description of what this endpoint does"
    }
}
```

Then implement the corresponding handler method following the pattern of existing methods.

## Dependencies

- `httpx`: Async HTTP client (already in requirements.txt)
- FastAPI and Pydantic: For input validation and API integration

## Limitations

- **Rate Limiting**: Public APIs may have rate limits
- **Timeout**: 10-second timeout per request
- **Free Tier**: Uses free tiers of APIs (may have usage limits)
- **Data Size**: Large responses are limited to first 5 items for list endpoints

## Future Enhancements

- [ ] Add more API endpoints (news, stocks, etc.)
- [ ] Support for POST/PUT requests
- [ ] Custom headers and authentication
- [ ] Response caching
- [ ] Configurable timeouts
- [ ] Retry logic for failed requests
