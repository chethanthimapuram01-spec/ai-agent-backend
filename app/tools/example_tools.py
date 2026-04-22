"""Example tool implementations"""
from typing import Dict, Any
from app.tools.base_tool import BaseTool, ToolMetadata


class CalculatorTool(BaseTool):
    """Example tool: Simple calculator"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            description="Performs basic arithmetic operations (add, subtract, multiply, divide)",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute calculator operation"""
        operation = kwargs.get("operation")
        a = kwargs.get("a")
        b = kwargs.get("b")
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {
                        "success": False,
                        "result": None,
                        "error": "Division by zero is not allowed"
                    }
                result = a / b
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Unknown operation: {operation}"
                }
            
            return {
                "success": True,
                "result": {
                    "operation": operation,
                    "input": {"a": a, "b": b},
                    "output": result
                },
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }


class TextAnalyzerTool(BaseTool):
    """Example tool: Text analysis"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="text_analyzer",
            description="Analyzes text and returns statistics (word count, character count, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze"
                    }
                },
                "required": ["text"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute text analysis"""
        text = kwargs.get("text", "")
        
        try:
            words = text.split()
            sentences = text.split('.')
            
            analysis = {
                "character_count": len(text),
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
                "unique_words": len(set(word.lower() for word in words))
            }
            
            return {
                "success": True,
                "result": analysis,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }
