"""Base tool interface for all agent tools"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from app.utils.error_handlers import (
    ToolError,
    ToolValidationError,
    ToolTimeoutError,
    log_error,
    create_error_response,
    ErrorCode,
    ErrorCategory
)

logger = logging.getLogger(__name__)


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
    
    def validate_input(self, **kwargs) -> None:
        """
        Validate input parameters against the tool's schema
        
        Args:
            **kwargs: Input parameters to validate
            
        Raises:
            ToolValidationError: If validation fails
        """
        required_params = self.metadata.input_schema.get("required", [])
        properties = self.metadata.input_schema.get("properties", {})
        validation_errors = {}
        
        # Check required parameters
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                validation_errors[param] = f"Required parameter '{param}' is missing"
        
        # Check parameter types and constraints
        for param, value in kwargs.items():
            if param in properties:
                prop_schema = properties[param]
                expected_type = prop_schema.get("type")
                
                # Type validation
                if expected_type and not self._check_type(value, expected_type):
                    validation_errors[param] = f"Expected type '{expected_type}', got '{type(value).__name__}'"
                
                # String length validation
                if expected_type == "string" and isinstance(value, str):
                    min_length = prop_schema.get("minLength")
                    max_length = prop_schema.get("maxLength")
                    if min_length and len(value) < min_length:
                        validation_errors[param] = f"String length must be at least {min_length}"
                    if max_length and len(value) > max_length:
                        validation_errors[param] = f"String length must not exceed {max_length}"
                
                # Number range validation
                if expected_type in ["number", "integer"] and isinstance(value, (int, float)):
                    minimum = prop_schema.get("minimum")
                    maximum = prop_schema.get("maximum")
                    if minimum is not None and value < minimum:
                        validation_errors[param] = f"Value must be at least {minimum}"
                    if maximum is not None and value > maximum:
                        validation_errors[param] = f"Value must not exceed {maximum}"
                
                # Enum validation
                enum_values = prop_schema.get("enum")
                if enum_values and value not in enum_values:
                    validation_errors[param] = f"Value must be one of {enum_values}"
        
        if validation_errors:
            raise ToolValidationError(
                tool_name=self.metadata.name,
                validation_errors=validation_errors
            )
    
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
        Safely execute the tool with validation and error handling
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Dictionary containing execution results or structured error information
        """
        try:
            # Validate input
            self.validate_input(**kwargs)
            
            # Execute tool
            result = await self.execute(**kwargs)
            
            # Ensure result has correct structure
            if not isinstance(result, dict):
                logger.warning(f"Tool {self.metadata.name} returned non-dict result, wrapping it")
                result = {"success": True, "result": result}
            
            if "success" not in result:
                result["success"] = True
            
            return result
            
        except ToolValidationError as e:
            # Input validation failed
            log_error(e, context={"tool": self.metadata.name, "inputs": kwargs})
            return {
                "success": False,
                "error": e.message,
                "error_code": e.error_code.value,
                "details": e.details,
                "result": None
            }
        
        except ToolError as e:
            # Tool-specific error
            log_error(e, context={"tool": self.metadata.name, "inputs": kwargs})
            return {
                "success": False,
                "error": e.message,
                "error_code": e.error_code.value,
                "details": e.details,
                "result": None
            }
        
        except Exception as e:
            # Unexpected error
            log_error(e, context={"tool": self.metadata.name, "inputs": kwargs})
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "error_code": ErrorCode.TOOL_EXECUTION_FAILED.value,
                "details": {"exception_type": type(e).__name__},
                "result": None
            }
