"""
Test suite for error handling and validation

Tests:
- Custom exception creation and formatting
- Input validation utilities
- Retry logic for API calls
- Structured error responses
- Tool input validation
"""

import asyncio
import time
from app.utils.error_handlers import (
    # Exceptions
    ValidationError,
    MissingRequiredFieldError,
    InvalidFileFormatError,
    EmptyDocumentError,
    MissingSessionIdError,
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    DocumentError,
    WorkflowError,
    # Utilities
    validate_required_fields,
    validate_session_id,
    validate_file_format,
    validate_non_empty_text,
    create_error_response,
    exception_to_response,
    retry_on_exception,
    # Enums
    ErrorCode,
    ErrorCategory
)


def test_custom_exceptions():
    """Test custom exception creation and formatting"""
    print("=" * 80)
    print("TEST: Custom Exceptions")
    print("=" * 80)
    
    # Test ValidationError
    try:
        raise ValidationError("Invalid input provided", field="email")
    except ValidationError as e:
        error_dict = e.to_dict()
        print("✓ ValidationError created successfully")
        print(f"  Error Code: {error_dict['error_code']}")
        print(f"  Category: {error_dict['category']}")
        print(f"  Message: {error_dict['message']}")
        print(f"  HTTP Status: {error_dict['http_status']}")
        print(f"  Details: {error_dict['details']}")
        assert error_dict['http_status'] == 400
        assert error_dict['category'] == 'validation'
    
    # Test ToolError
    try:
        raise ToolNotFoundError("document_query")
    except ToolNotFoundError as e:
        error_dict = e.to_dict()
        print("\n✓ ToolNotFoundError created successfully")
        print(f"  Error Code: {error_dict['error_code']}")
        print(f"  Tool: {error_dict['details']['tool_name']}")
        print(f"  HTTP Status: {error_dict['http_status']}")
        assert error_dict['http_status'] == 404
        assert error_dict['error_code'] == 'TOOL_NOT_FOUND'
    
    # Test APIError
    try:
        raise APITimeoutError(endpoint="https://api.example.com", timeout=10.0)
    except APITimeoutError as e:
        error_dict = e.to_dict()
        print("\n✓ APITimeoutError created successfully")
        print(f"  Error Code: {error_dict['error_code']}")
        print(f"  Endpoint: {error_dict['details']['endpoint']}")
        print(f"  Timeout: {error_dict['details']['timeout_seconds']}s")
        assert error_dict['error_code'] == 'API_TIMEOUT'
    
    print()


def test_validation_utilities():
    """Test input validation utilities"""
    print("=" * 80)
    print("TEST: Validation Utilities")
    print("=" * 80)
    
    # Test validate_required_fields
    print("Testing validate_required_fields...")
    data = {"name": "John", "age": 30}
    try:
        validate_required_fields(data, ["name", "age"])
        print("✓ Valid data passed validation")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    try:
        validate_required_fields(data, ["name", "email"])
        print("✗ Should have raised MissingRequiredFieldError")
    except MissingRequiredFieldError as e:
        print(f"✓ Correctly caught missing field: {e.message}")
    
    # Test validate_session_id
    print("\nTesting validate_session_id...")
    try:
        result = validate_session_id("valid_session_123")
        print(f"✓ Valid session ID accepted: {result}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    try:
        validate_session_id("")
        print("✗ Should have raised MissingSessionIdError")
    except MissingSessionIdError as e:
        print(f"✓ Correctly caught empty session ID: {e.message}")
    
    try:
        validate_session_id(None)
        print("✗ Should have raised MissingSessionIdError")
    except MissingSessionIdError as e:
        print(f"✓ Correctly caught None session ID: {e.message}")
    
    # Test validate_file_format
    print("\nTesting validate_file_format...")
    supported = ['.pdf', '.docx', '.txt']
    try:
        result = validate_file_format("document.pdf", supported)
        print(f"✓ Valid file format accepted: {result}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    try:
        validate_file_format("image.jpg", supported)
        print("✗ Should have raised InvalidFileFormatError")
    except InvalidFileFormatError as e:
        print(f"✓ Correctly caught invalid format: {e.message}")
        print(f"  Supported: {e.details['supported_formats']}")
    
    # Test validate_non_empty_text
    print("\nTesting validate_non_empty_text...")
    try:
        result = validate_non_empty_text("Hello, world!", "message")
        print(f"✓ Non-empty text accepted: {result}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    try:
        validate_non_empty_text("   ", "message")
        print("✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"✓ Correctly caught empty text: {e.message}")
    
    print()


def test_error_responses():
    """Test structured error response creation"""
    print("=" * 80)
    print("TEST: Structured Error Responses")
    print("=" * 80)
    
    # Test create_error_response
    error_response = create_error_response(
        error_code=ErrorCode.TOOL_EXECUTION_FAILED,
        message="Tool execution failed",
        category=ErrorCategory.TOOL,
        details={"tool_name": "api_caller", "reason": "timeout"},
        request_id="req_12345"
    )
    
    print("✓ Error response created successfully")
    print(f"  Error: {error_response['error']}")
    print(f"  Error Code: {error_response['error_code']}")
    print(f"  Category: {error_response['category']}")
    print(f"  Message: {error_response['message']}")
    print(f"  Details: {error_response['details']}")
    print(f"  Timestamp: {error_response['timestamp']}")
    print(f"  Request ID: {error_response['request_id']}")
    
    assert error_response['error'] == True
    assert error_response['error_code'] == 'TOOL_EXECUTION_FAILED'
    assert error_response['category'] == 'tool'
    
    # Test exception_to_response with custom exception
    print("\nTesting exception_to_response...")
    try:
        raise ToolValidationError(
            tool_name="calculator",
            validation_errors={"param1": "Required field missing"}
        )
    except ToolValidationError as e:
        response = exception_to_response(e, request_id="req_67890")
        print("✓ Custom exception converted to response")
        print(f"  Error Code: {response['error_code']}")
        print(f"  Message: {response['message']}")
        print(f"  Request ID: {response['request_id']}")
    
    # Test exception_to_response with standard exception
    try:
        raise ValueError("Something went wrong")
    except ValueError as e:
        response = exception_to_response(e)
        print("\n✓ Standard exception converted to response")
        print(f"  Error Code: {response['error_code']}")
        print(f"  Message: {response['message']}")
        print(f"  Exception Type: {response['details']['exception_type']}")
        assert response['error_code'] == 'INTERNAL_ERROR'
    
    print()


def test_retry_logic():
    """Test retry decorator functionality"""
    print("=" * 80)
    print("TEST: Retry Logic")
    print("=" * 80)
    
    # Test successful retry after failures
    attempt_count = 0
    
    @retry_on_exception(
        max_attempts=3,
        delay=0.1,
        backoff=2.0,
        exceptions=(ValueError,)
    )
    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            print(f"  Attempt {attempt_count}: Raising ValueError")
            raise ValueError(f"Attempt {attempt_count} failed")
        print(f"  Attempt {attempt_count}: Success!")
        return "Success"
    
    print("Testing retry with eventual success...")
    start = time.time()
    result = flaky_function()
    duration = time.time() - start
    
    print(f"✓ Function succeeded after {attempt_count} attempts")
    print(f"  Result: {result}")
    print(f"  Total time: {duration:.2f}s")
    assert result == "Success"
    assert attempt_count == 3
    
    # Test retry exhaustion
    attempt_count_fail = 0
    
    @retry_on_exception(
        max_attempts=2,
        delay=0.1,
        exceptions=(RuntimeError,)
    )
    def always_fail():
        nonlocal attempt_count_fail
        attempt_count_fail += 1
        print(f"  Attempt {attempt_count_fail}: Raising RuntimeError")
        raise RuntimeError("Always fails")
    
    print("\nTesting retry exhaustion...")
    try:
        always_fail()
        print("✗ Should have raised RuntimeError")
    except RuntimeError as e:
        print(f"✓ Correctly raised error after {attempt_count_fail} attempts")
        print(f"  Error: {e}")
        assert attempt_count_fail == 2
    
    print()


def test_tool_input_validation():
    """Test tool input validation"""
    print("=" * 80)
    print("TEST: Tool Input Validation")
    print("=" * 80)
    
    # Simulate tool validation
    from app.tools.base_tool import BaseTool, ToolMetadata
    
    class TestTool(BaseTool):
        @property
        def metadata(self) -> ToolMetadata:
            return ToolMetadata(
                name="test_tool",
                description="A test tool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 3, "maxLength": 50},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150},
                        "status": {"type": "string", "enum": ["active", "inactive"]}
                    },
                    "required": ["name", "age"]
                }
            )
        
        async def execute(self, **kwargs):
            return {"success": True, "result": kwargs}
    
    tool = TestTool()
    
    # Valid input
    print("Testing valid input...")
    try:
        tool.validate_input(name="John", age=30, status="active")
        print("✓ Valid input passed validation")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Missing required field
    print("\nTesting missing required field...")
    try:
        tool.validate_input(name="John")
        print("✗ Should have raised ToolValidationError")
    except ToolValidationError as e:
        print(f"✓ Correctly caught missing field: {e.message}")
        print(f"  Validation errors: {e.details['validation_errors']}")
    
    # Invalid type
    print("\nTesting invalid type...")
    try:
        tool.validate_input(name="John", age="thirty")
        print("✗ Should have raised ToolValidationError")
    except ToolValidationError as e:
        print(f"✓ Correctly caught invalid type: {e.message}")
    
    # String length violation
    print("\nTesting string length violation...")
    try:
        tool.validate_input(name="Jo", age=30)  # Too short
        print("✗ Should have raised ToolValidationError")
    except ToolValidationError as e:
        print(f"✓ Correctly caught length violation: {e.message}")
        print(f"  Validation errors: {e.details['validation_errors']}")
    
    # Enum violation
    print("\nTesting enum violation...")
    try:
        tool.validate_input(name="John", age=30, status="pending")
        print("✗ Should have raised ToolValidationError")
    except ToolValidationError as e:
        print(f"✓ Correctly caught enum violation: {e.message}")
    
    # Number range violation
    print("\nTesting number range violation...")
    try:
        tool.validate_input(name="John", age=200)
        print("✗ Should have raised ToolValidationError")
    except ToolValidationError as e:
        print(f"✓ Correctly caught range violation: {e.message}")
    
    print()


def run_all_tests():
    """Run all error handling tests"""
    print("\n🧪 Error Handling & Validation Test Suite\n")
    
    test_custom_exceptions()
    test_validation_utilities()
    test_error_responses()
    test_retry_logic()
    test_tool_input_validation()
    
    print("=" * 80)
    print("✅ All Tests Completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
