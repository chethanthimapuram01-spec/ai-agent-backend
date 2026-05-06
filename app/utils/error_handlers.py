"""
Centralized error handling utilities and custom exceptions

Provides:
- Custom exception classes
- Structured error response formatting
- Error logging utilities
- Retry logic for transient failures
"""

import logging
import time
import functools
from typing import Dict, Any, Optional, Callable, Type, Tuple
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# ERROR CODES AND CATEGORIES
# ============================================================================

class ErrorCode(str, Enum):
    """Standard error codes for the application"""
    # Validation Errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    MISSING_SESSION_ID = "MISSING_SESSION_ID"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    
    # Tool Errors (5xx)
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_VALIDATION_FAILED = "TOOL_VALIDATION_FAILED"
    
    # API Errors (5xx)
    API_CONNECTION_ERROR = "API_CONNECTION_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_AUTHENTICATION_FAILED = "API_AUTHENTICATION_FAILED"
    
    # Document Errors (4xx/5xx)
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    
    # Workflow Errors (5xx)
    WORKFLOW_PLANNING_FAILED = "WORKFLOW_PLANNING_FAILED"
    WORKFLOW_EXECUTION_FAILED = "WORKFLOW_EXECUTION_FAILED"
    STEP_DEPENDENCY_FAILED = "STEP_DEPENDENCY_FAILED"
    
    # System Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    TOOL = "tool"
    API = "api"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    SYSTEM = "system"


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class AppException(Exception):
    """Base exception for all application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        category: ErrorCategory,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.details = details or {}
        self.http_status = http_status
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": True,
            "error_code": self.error_code.value,
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "http_status": self.http_status
        }


class ValidationError(AppException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            details=details,
            http_status=400
        )


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing"""
    
    def __init__(self, field: str, **kwargs):
        super().__init__(
            message=f"Required field '{field}' is missing",
            field=field,
            **kwargs
        )
        self.error_code = ErrorCode.MISSING_REQUIRED_FIELD


class InvalidFileFormatError(ValidationError):
    """Raised when file format is not supported"""
    
    def __init__(self, file_format: str, supported_formats: list, **kwargs):
        super().__init__(
            message=f"Unsupported file format: {file_format}",
            details={
                "received_format": file_format,
                "supported_formats": supported_formats
            },
            **kwargs
        )
        self.error_code = ErrorCode.INVALID_FILE_FORMAT


class EmptyDocumentError(ValidationError):
    """Raised when document is empty"""
    
    def __init__(self, document_id: Optional[str] = None, **kwargs):
        super().__init__(
            message="Document is empty or contains no text",
            details={"document_id": document_id} if document_id else {},
            **kwargs
        )
        self.error_code = ErrorCode.EMPTY_DOCUMENT


class MissingSessionIdError(ValidationError):
    """Raised when session ID is missing"""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="Session ID is required but was not provided",
            **kwargs
        )
        self.error_code = ErrorCode.MISSING_SESSION_ID


class ToolError(AppException):
    """Base exception for tool-related errors"""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if tool_name:
            details["tool_name"] = tool_name
        super().__init__(
            message=message,
            error_code=ErrorCode.TOOL_EXECUTION_FAILED,
            category=ErrorCategory.TOOL,
            details=details,
            http_status=500
        )


class ToolNotFoundError(ToolError):
    """Raised when tool is not found"""
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(
            message=f"Tool '{tool_name}' not found",
            tool_name=tool_name,
            **kwargs
        )
        self.error_code = ErrorCode.TOOL_NOT_FOUND
        self.http_status = 404


class ToolValidationError(ToolError):
    """Raised when tool input validation fails"""
    
    def __init__(self, tool_name: str, validation_errors: Dict[str, Any], **kwargs):
        super().__init__(
            message=f"Tool '{tool_name}' input validation failed",
            tool_name=tool_name,
            details={"validation_errors": validation_errors},
            **kwargs
        )
        self.error_code = ErrorCode.TOOL_VALIDATION_FAILED
        self.http_status = 400


class ToolTimeoutError(ToolError):
    """Raised when tool execution times out"""
    
    def __init__(self, tool_name: str, timeout: float, **kwargs):
        super().__init__(
            message=f"Tool '{tool_name}' execution timed out after {timeout}s",
            tool_name=tool_name,
            details={"timeout_seconds": timeout},
            **kwargs
        )
        self.error_code = ErrorCode.TOOL_TIMEOUT


class APIError(AppException):
    """Base exception for external API errors"""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(
            message=message,
            error_code=ErrorCode.API_CONNECTION_ERROR,
            category=ErrorCategory.API,
            details=details,
            http_status=502
        )


class APITimeoutError(APIError):
    """Raised when API request times out"""
    
    def __init__(self, endpoint: str, timeout: float, **kwargs):
        super().__init__(
            message=f"API request to '{endpoint}' timed out after {timeout}s",
            endpoint=endpoint,
            details={"timeout_seconds": timeout},
            **kwargs
        )
        self.error_code = ErrorCode.API_TIMEOUT


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, endpoint: str, retry_after: Optional[int] = None, **kwargs):
        details = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(
            message=f"API rate limit exceeded for '{endpoint}'",
            endpoint=endpoint,
            details=details,
            **kwargs
        )
        self.error_code = ErrorCode.API_RATE_LIMIT
        self.http_status = 429


class DocumentError(AppException):
    """Base exception for document-related errors"""
    
    def __init__(self, message: str, document_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if document_id:
            details["document_id"] = document_id
        super().__init__(
            message=message,
            error_code=ErrorCode.DOCUMENT_PROCESSING_FAILED,
            category=ErrorCategory.DOCUMENT,
            details=details,
            http_status=500
        )


class DocumentNotFoundError(DocumentError):
    """Raised when document is not found"""
    
    def __init__(self, document_id: str, **kwargs):
        super().__init__(
            message=f"Document '{document_id}' not found",
            document_id=document_id,
            **kwargs
        )
        self.error_code = ErrorCode.DOCUMENT_NOT_FOUND
        self.http_status = 404


class WorkflowError(AppException):
    """Base exception for workflow-related errors"""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if workflow_id:
            details["workflow_id"] = workflow_id
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKFLOW_EXECUTION_FAILED,
            category=ErrorCategory.WORKFLOW,
            details=details,
            http_status=500
        )


# ============================================================================
# STRUCTURED ERROR RESPONSE
# ============================================================================

class ErrorResponse(BaseModel):
    """Structured error response model"""
    error: bool = True
    error_code: str = Field(description="Error code for programmatic handling")
    category: str = Field(description="Error category")
    message: str = Field(description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: Optional[str] = Field(default=None, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "error_code": "TOOL_EXECUTION_FAILED",
                "category": "tool",
                "message": "Tool 'api_caller' execution failed",
                "details": {
                    "tool_name": "api_caller",
                    "reason": "Connection timeout"
                },
                "timestamp": "2026-05-06T10:00:00Z",
                "request_id": "req_12345"
            }
        }


def create_error_response(
    error_code: ErrorCode,
    message: str,
    category: ErrorCategory,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a structured error response
    
    Args:
        error_code: Error code enum
        message: Human-readable error message
        category: Error category enum
        details: Additional error details
        request_id: Request ID for tracking
        
    Returns:
        Structured error response dictionary
    """
    from datetime import datetime
    
    return {
        "error": True,
        "error_code": error_code.value,
        "category": category.value,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id
    }


def exception_to_response(exception: Exception, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert any exception to a structured error response
    
    Args:
        exception: The exception to convert
        request_id: Optional request ID for tracking
        
    Returns:
        Structured error response dictionary
    """
    if isinstance(exception, AppException):
        response = exception.to_dict()
        if request_id:
            response["request_id"] = request_id
        return response
    
    # Handle unknown exceptions
    from datetime import datetime
    return {
        "error": True,
        "error_code": ErrorCode.INTERNAL_ERROR.value,
        "category": ErrorCategory.SYSTEM.value,
        "message": str(exception) or "An unexpected error occurred",
        "details": {"exception_type": type(exception).__name__},
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id
    }


# ============================================================================
# RETRY LOGIC
# ============================================================================

def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_func: Optional[Callable] = None
):
    """
    Decorator that retries a function on specific exceptions
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
        logger_func: Optional logging function
        
    Example:
        @retry_on_exception(max_attempts=3, delay=1.0, exceptions=(APIError,))
        async def fetch_data():
            # This will retry up to 3 times on APIError
            return await api_call()
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        # Last attempt failed, re-raise
                        if logger_func:
                            logger_func(
                                f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    # Log retry attempt
                    if logger_func:
                        logger_func(
                            f"Function {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # Should never reach here, but just in case
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        if logger_func:
                            logger_func(
                                f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                            )
                        raise
                    
                    if logger_func:
                        logger_func(
                            f"Function {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# INPUT VALIDATION UTILITIES
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present in data
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        MissingRequiredFieldError: If any required field is missing
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            raise MissingRequiredFieldError(field)


def validate_session_id(session_id: Optional[str]) -> str:
    """
    Validate session ID is provided and not empty
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Validated session ID
        
    Raises:
        MissingSessionIdError: If session ID is missing or empty
    """
    if not session_id or not session_id.strip():
        raise MissingSessionIdError()
    return session_id.strip()


def validate_file_format(filename: str, supported_formats: list) -> str:
    """
    Validate file format is supported
    
    Args:
        filename: Name of the file
        supported_formats: List of supported file extensions (e.g., ['.pdf', '.txt'])
        
    Returns:
        Validated filename
        
    Raises:
        InvalidFileFormatError: If file format is not supported
    """
    import os
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in supported_formats:
        raise InvalidFileFormatError(file_ext, supported_formats)
    
    return filename


def validate_non_empty_text(text: str, field_name: str = "text") -> str:
    """
    Validate text is not empty
    
    Args:
        text: Text to validate
        field_name: Name of the field for error message
        
    Returns:
        Validated text
        
    Raises:
        ValidationError: If text is empty
    """
    if not text or not text.strip():
        raise ValidationError(
            message=f"{field_name} cannot be empty",
            field=field_name
        )
    return text.strip()


# ============================================================================
# ERROR LOGGING UTILITIES
# ============================================================================

def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """
    Log error with context information
    
    Args:
        error: Exception to log
        context: Additional context information
        level: Log level (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, level, logger.error)
    
    if isinstance(error, AppException):
        log_func(
            f"[{error.error_code.value}] {error.message}",
            extra={
                "error_code": error.error_code.value,
                "category": error.category.value,
                "details": error.details,
                "context": context or {}
            }
        )
    else:
        log_func(
            f"Unexpected error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context or {}
            },
            exc_info=True
        )


def safe_execute(
    func: Callable,
    *args,
    error_message: str = "Operation failed",
    log_errors: bool = True,
    **kwargs
) -> Tuple[bool, Any]:
    """
    Safely execute a function and return (success, result) tuple
    
    Args:
        func: Function to execute
        *args: Positional arguments for function
        error_message: Error message if execution fails
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for function
        
    Returns:
        Tuple of (success: bool, result: Any or Exception)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        if log_errors:
            log_error(e, context={"function": func.__name__})
        return False, e
