# Quick Start Guide: Creating and Using Tools

## Creating a New Tool in 3 Steps

### Step 1: Create the Tool Class

Create a new file in `app/tools/` (e.g., `app/tools/weather_tool.py`):

```python
from typing import Dict, Any
from app.tools.base_tool import BaseTool, ToolMetadata

class WeatherTool(BaseTool):
    """Get weather information for a location"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="weather",
            description="Get current weather for a location",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units (celsius/fahrenheit)",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        location = kwargs.get("location")
        units = kwargs.get("units", "celsius")
        
        try:
            # Your implementation here
            # For now, return mock data
            weather_data = {
                "location": location,
                "temperature": 22 if units == "celsius" else 72,
                "units": units,
                "condition": "Sunny"
            }
            
            return {
                "success": True,
                "result": weather_data,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }
```

### Step 2: Register the Tool

In `app/main.py`, add your tool to the startup event:

```python
from app.tools.weather_tool import WeatherTool

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Agent Backend...")
    
    # Register tools
    calculator = CalculatorTool()
    text_analyzer = TextAnalyzerTool()
    weather = WeatherTool()  # Add your tool
    
    tool_registry.register(calculator)
    tool_registry.register(text_analyzer)
    tool_registry.register(weather)  # Register it
    
    logger.info(f"Registered {len(tool_registry.list_tool_names())} tools")
```

### Step 3: Test It!

```bash
# Start the server
uvicorn app.main:app --reload

# Test your tool
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather in Paris?",
    "session_id": "test123"
  }'
```

## Tool Development Tips

### Input Schema Best Practices

```python
input_schema={
    "type": "object",
    "properties": {
        "param_name": {
            "type": "string",              # string, number, integer, boolean, array, object
            "description": "Clear description",  # Help LLM understand
            "enum": ["option1", "option2"],      # Optional: limit choices
            "default": "default_value"           # Optional: default value
        }
    },
    "required": ["param_name"]  # List required parameters
}
```

### Error Handling

Always return the standard format:

```python
# Success
return {
    "success": True,
    "result": your_data,
    "error": None
}

# Failure
return {
    "success": False,
    "result": None,
    "error": "Descriptive error message"
}
```

### Validation

Use the built-in `validate_input` or `safe_execute`:

```python
# Method 1: Manual validation
is_valid, error = self.validate_input(**kwargs)
if not is_valid:
    return {"success": False, "result": None, "error": error}

# Method 2: Use safe_execute (recommended)
# The agent controller already uses this
result = await tool.safe_execute(**kwargs)
```

## Testing Tools Directly

### Test tool registration
```bash
curl http://localhost:8000/tools
```

### Get tool details
```bash
curl http://localhost:8000/tools/calculator
```

### Enable/Disable tools
```bash
# Disable
curl -X POST http://localhost:8000/tools/calculator/disable

# Enable
curl -X POST http://localhost:8000/tools/calculator/enable
```

## Common Tool Patterns

### 1. API Integration Tool

```python
import httpx

class APITool(BaseTool):
    async def execute(self, **kwargs):
        url = kwargs.get("url")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            return {
                "success": response.status_code == 200,
                "result": response.json() if response.status_code == 200 else None,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
```

### 2. Data Processing Tool

```python
class DataProcessorTool(BaseTool):
    async def execute(self, **kwargs):
        data = kwargs.get("data", [])
        operation = kwargs.get("operation")
        
        if operation == "sum":
            result = sum(data)
        elif operation == "average":
            result = sum(data) / len(data) if data else 0
        else:
            return {"success": False, "result": None, "error": "Unknown operation"}
        
        return {
            "success": True,
            "result": {"operation": operation, "value": result},
            "error": None
        }
```

### 3. Database Query Tool

```python
class DatabaseTool(BaseTool):
    async def execute(self, **kwargs):
        query = kwargs.get("query")
        
        try:
            # Execute database query
            # results = await db.fetch(query)
            results = []  # Placeholder
            
            return {
                "success": True,
                "result": {"rows": results, "count": len(results)},
                "error": None
            }
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}
```

## Debugging Tips

### 1. Check Tool Registration
```python
# In your code
from app.tools.tool_registry import tool_registry

print(tool_registry.list_tool_names())  # See all registered tools
```

### 2. Test Tool Directly
```python
# Test without agent
from app.tools.calculator import CalculatorTool

tool = CalculatorTool()
result = await tool.execute(operation="add", a=5, b=3)
print(result)
```

### 3. Check Execution History
```bash
curl http://localhost:8000/agent/history/test123
```

### 4. Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. ✅ Create your first tool
2. ✅ Test it with the agent
3. 📝 Add more tools as needed
4. 🔧 Customize agent decision logic
5. 📊 Monitor tool usage and performance

For more details, see [ARCHITECTURE.md](ARCHITECTURE.md)
