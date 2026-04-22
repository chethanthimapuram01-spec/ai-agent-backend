"""Base tool interface for all agent tools"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """Metadata schema for tools"""
    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Brief description of what the tool does")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema defining the expected input parameters")
    version: str = Field(default="1.0.0", description="Tool version")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")


class BaseTool(ABC):
    """
    Abstract base class for all tools
    
    All tools must inherit from this class and implement:
    - metadata property: Returns ToolMetadata
    - execute method: Performs the tool's action
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """
        Return tool metadata including name, description, and input schema
        
        Returns:
            ToolMetadata object with tool information
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's main functionality
        
        Args:
            **kwargs: Input parameters as defined in the tool's input schema
            
        Returns:
            Dictionary containing:
                - success: bool - whether execution was successful
                - result: Any - the tool's output
                - error: Optional[str] - error message if failed
        """
        pass
    
    def validate_input(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters against the tool's schema
        
        Args:
            **kwargs: Input parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_params = self.metadata.input_schema.get("required", [])
        properties = self.metadata.input_schema.get("properties", {})
        
        # Check required parameters
        for param in required_params:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"
        
        # Check parameter types
        for param, value in kwargs.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type:
                    if not self._check_type(value, expected_type):
                        return False, f"Parameter '{param}' has incorrect type. Expected: {expected_type}"
        
        return True, None
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if value matches expected type
        
        Args:
            value: Value to check
            expected_type: Expected JSON schema type
            
        Returns:
            True if type matches, False otherwise
        """
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with validation and error handling
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Dictionary with execution results
        """
        # Validate input
        is_valid, error_msg = self.validate_input(**kwargs)
        if not is_valid:
            return {
                "success": False,
                "result": None,
                "error": f"Input validation failed: {error_msg}"
            }
        
        # Execute tool
        try:
            return await self.execute(**kwargs)
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Tool execution failed: {str(e)}"
            }
