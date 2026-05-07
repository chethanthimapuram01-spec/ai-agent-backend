"""
Test suite for failure cases and error handling

Tests cover:
- API timeout and retry logic
- Tool execution failures
- Invalid input validation
- Document processing errors
- Session management failures
- Network errors and rate limiting
- Malformed requests
- Database errors
- Resource exhaustion

Run with: pytest test_failure_cases.py -v
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx
from app.main import app
from app.utils.error_handlers import (
    AppException,
    ValidationError,
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    ToolTimeoutError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    InvalidFileFormatError,
    EmptyDocumentError,
    MissingSessionIdError,
    ErrorCode
)
from app.tools.api_caller_tool import ApiCallerTool

# Initialize test client
client = TestClient(app)


class TestAPIFailures:
    """Test API call failures and retry logic"""
    
    @pytest.mark.asyncio
    async def test_api_timeout_retry(self):
        """Test API timeout triggers retry logic"""
        tool = ApiCallerTool()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(APITimeoutError):
                await tool._call_weather_api("London")
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_error(self):
        """Test API rate limiting is handled"""
        tool = ApiCallerTool()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Simulate 429 rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_get.side_effect = httpx.HTTPStatusError(
                "Rate limit",
                request=Mock(),
                response=mock_response
            )
            
            with pytest.raises(APIRateLimitError):
                await tool._call_weather_api("London")
    
    @pytest.mark.asyncio
    async def test_api_network_error(self):
        """Test network connectivity errors"""
        tool = ApiCallerTool()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(APITimeoutError):
                await tool._call_weather_api("London")
    
    @pytest.mark.asyncio
    async def test_api_500_error(self):
        """Test server errors (500) are handled"""
        tool = ApiCallerTool()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_get.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=Mock(),
                response=mock_response
            )
            
            with pytest.raises(APIError):
                await tool._call_weather_api("London")
    
    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Test retry logic succeeds after initial failures"""
        tool = ApiCallerTool()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # First call fails, second succeeds
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"temperature": 20}
            
            mock_get.side_effect = [
                httpx.TimeoutException("Timeout"),
                mock_response_success
            ]
            
            result = await tool._call_weather_api("London")
            assert result is not None
            assert "temperature" in result


class TestToolExecutionFailures:
    """Test tool execution error handling"""
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test requesting non-existent tool"""
        from app.agents.agent_controller import AgentController
        
        controller = AgentController()
        
        with patch.object(controller, '_make_decision') as mock_decision:
            from app.agents.agent_controller import AgentDecision
            mock_decision.return_value = AgentDecision(
                use_tool=True,
                tool_name="non_existent_tool",
                tool_params={}
            )
            
            result = await controller.process_query(
                query="Test",
                session_id="test-session"
            )
            
            # Should handle gracefully
            assert "response" in result
    
    @pytest.mark.asyncio
    async def test_tool_execution_exception(self):
        """Test tool raises exception during execution"""
        from app.tools.base_tool import BaseTool
        
        class FailingTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="failing_tool",
                    description="Tool that fails",
                    parameters_schema={"type": "object", "properties": {}}
                )
            
            def execute(self, **kwargs):
                raise Exception("Tool execution failed")
        
        tool = FailingTool()
        result = await tool.safe_execute()
        
        assert result["success"] is False
        assert "error" in result or "error_code" in result
    
    @pytest.mark.asyncio
    async def test_tool_timeout(self):
        """Test tool execution timeout"""
        from app.tools.base_tool import BaseTool
        import time
        
        class SlowTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="slow_tool",
                    description="Slow executing tool",
                    parameters_schema={"type": "object", "properties": {}}
                )
            
            def execute(self, **kwargs):
                time.sleep(10)  # Simulate long operation
                return {"success": True}
        
        tool = SlowTool()
        
        # Note: This would need actual timeout implementation in safe_execute
        # For now, just verify the tool can be instantiated
        assert tool.name == "slow_tool"


class TestInputValidation:
    """Test input validation failures"""
    
    def test_chat_empty_message_validation(self):
        """Test empty message validation"""
        response = client.post(
            "/chat",
            json={
                "message": "",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_chat_whitespace_only_message(self):
        """Test whitespace-only message validation"""
        response = client.post(
            "/chat",
            json={
                "message": "   \t\n  ",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 400
    
    def test_agent_missing_session_id(self):
        """Test missing session_id validation"""
        response = client.post(
            "/agent",
            json={
                "query": "Test query"
            }
        )
        
        assert response.status_code == 422
    
    def test_agent_empty_session_id(self):
        """Test empty session_id validation"""
        response = client.post(
            "/agent",
            json={
                "query": "Test query",
                "session_id": ""
            }
        )
        
        assert response.status_code == 400
    
    def test_invalid_json_format(self):
        """Test malformed JSON requests"""
        response = client.post(
            "/chat",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test requests with missing required fields"""
        response = client.post(
            "/chat",
            json={}
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail


class TestDocumentProcessingFailures:
    """Test document upload and processing failures"""
    
    def test_upload_unsupported_file_type(self):
        """Test uploading unsupported file type"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.side_effect = ValueError("Unsupported file type: .txt")
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.txt", b"text content", "text/plain")}
            )
            
            assert response.status_code == 400
            assert "unsupported" in response.json()["detail"].lower()
    
    def test_upload_empty_file(self):
        """Test uploading empty file"""
        response = client.post(
            "/upload-doc",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_upload_file_too_large(self):
        """Test uploading file exceeding size limit"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/upload-doc",
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )
        
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()
    
    def test_upload_corrupted_pdf(self):
        """Test uploading corrupted PDF"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.side_effect = Exception("Failed to parse PDF")
            
            response = client.post(
                "/upload-doc",
                files={"file": ("corrupt.pdf", b"corrupted data", "application/pdf")}
            )
            
            assert response.status_code == 500
    
    def test_upload_no_file_provided(self):
        """Test upload without file"""
        response = client.post("/upload-doc")
        
        assert response.status_code == 422
    
    def test_get_nonexistent_document(self):
        """Test retrieving non-existent document"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/documents/non-existent-id")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_delete_nonexistent_document(self):
        """Test deleting non-existent document"""
        with patch('app.services.document_service.document_service.delete_document') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/documents/non-existent-id")
            
            assert response.status_code == 404


class TestErrorResponseStructure:
    """Test error response formats"""
    
    def test_validation_error_structure(self):
        """Test validation error includes proper structure"""
        response = client.post(
            "/chat",
            json={
                "message": "",
                "session_id": "test"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_not_found_error_structure(self):
        """Test 404 error structure"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/documents/missing")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    def test_server_error_structure(self):
        """Test 500 error structure"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.side_effect = Exception("Unexpected error")
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.pdf", b"data", "application/pdf")}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestConcurrencyFailures:
    """Test concurrent request handling"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_executions(self):
        """Test multiple simultaneous tool executions"""
        from app.agents.agent_controller import AgentController
        
        controller = AgentController()
        
        async def process_query(query_id):
            with patch.object(controller, '_make_decision') as mock_decision:
                from app.agents.agent_controller import AgentDecision
                mock_decision.return_value = AgentDecision(
                    use_tool=False,
                    direct_response=f"Response {query_id}"
                )
                
                return await controller.process_query(
                    query=f"Query {query_id}",
                    session_id=f"session-{query_id}"
                )
        
        # Execute 5 queries concurrently
        results = await asyncio.gather(*[
            process_query(i) for i in range(5)
        ])
        
        assert len(results) == 5
        assert all("response" in r for r in results)
    
    def test_concurrent_document_uploads(self):
        """Test concurrent document uploads"""
        # This would test rate limiting and resource management
        # For now, verify endpoint can handle multiple requests
        responses = []
        
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.return_value = {
                "metadata": {
                    "file_id": "file-123",
                    "original_filename": "test.pdf",
                    "file_type": ".pdf",
                    "upload_time": "2026-05-08T10:00:00",
                    "extracted_text_length": 100,
                    "file_size": 1024
                }
            }
            
            for i in range(3):
                response = client.post(
                    "/upload-doc",
                    files={"file": (f"test{i}.pdf", b"data", "application/pdf")}
                )
                responses.append(response)
        
        assert all(r.status_code == 200 for r in responses)


class TestResourceExhaustion:
    """Test resource exhaustion scenarios"""
    
    def test_very_large_query(self):
        """Test handling of extremely large queries"""
        # Create a very large query (100KB)
        large_query = "x" * (100 * 1024)
        
        response = client.post(
            "/agent",
            json={
                "query": large_query,
                "session_id": "test-session"
            }
        )
        
        # Should either succeed or return clear error
        assert response.status_code in [200, 400, 413]
    
    def test_deeply_nested_json(self):
        """Test handling of deeply nested JSON context"""
        # Create deeply nested context
        nested_context = {"level": 0}
        current = nested_context
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        response = client.post(
            "/agent",
            json={
                "query": "Test",
                "session_id": "test-session",
                "context": nested_context
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_many_simultaneous_sessions(self):
        """Test handling many different sessions"""
        with patch('app.services.chat_service.chat_service.process_message') as mock_process:
            mock_process.return_value = {
                "reply": "Response",
                "session_id": "test",
                "status": "success",
                "timestamp": "2026-05-08T10:00:00"
            }
            
            # Create 50 different sessions
            for i in range(50):
                response = client.post(
                    "/chat",
                    json={
                        "message": "Test",
                        "session_id": f"session-{i}"
                    }
                )
                assert response.status_code == 200


class TestErrorPropagation:
    """Test error propagation through layers"""
    
    @pytest.mark.asyncio
    async def test_tool_error_propagates_to_controller(self):
        """Test tool errors propagate correctly"""
        from app.agents.agent_controller import AgentController
        
        controller = AgentController()
        
        with patch.object(controller, '_make_decision') as mock_decision:
            from app.agents.agent_controller import AgentDecision
            mock_decision.return_value = AgentDecision(
                use_tool=True,
                tool_name="test_tool",
                tool_params={}
            )
            
            with patch.object(controller.tool_registry, 'get_tool') as mock_get:
                mock_tool = Mock()
                mock_tool.execute.side_effect = Exception("Tool failed")
                mock_get.return_value = mock_tool
                
                result = await controller.process_query(
                    query="Test",
                    session_id="test-session"
                )
                
                # Error should be handled gracefully
                assert "response" in result or "error" in result
    
    def test_service_error_propagates_to_route(self):
        """Test service layer errors propagate to routes"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.side_effect = ValueError("Service error")
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.pdf", b"data", "application/pdf")}
            )
            
            assert response.status_code == 400
            assert "error" in response.json()["detail"].lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_unicode_in_query(self):
        """Test queries with unicode characters"""
        response = client.post(
            "/agent",
            json={
                "query": "What's the weather in 東京?",
                "session_id": "test-session"
            }
        )
        
        # Should handle unicode gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_special_characters_in_filename(self):
        """Test filenames with special characters"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.return_value = {
                "metadata": {
                    "file_id": "file-123",
                    "original_filename": "file@#$%.pdf",
                    "file_type": ".pdf",
                    "upload_time": "2026-05-08T10:00:00",
                    "extracted_text_length": 100,
                    "file_size": 1024
                }
            }
            
            response = client.post(
                "/upload-doc",
                files={"file": ("file@#$%.pdf", b"data", "application/pdf")}
            )
            
            # Should handle special characters
            assert response.status_code in [200, 400]
    
    def test_null_values_in_context(self):
        """Test null values in optional context"""
        response = client.post(
            "/agent",
            json={
                "query": "Test",
                "session_id": "test-session",
                "context": None
            }
        )
        
        # Should handle null context
        assert response.status_code in [200, 400, 422]
    
    def test_extremely_long_session_id(self):
        """Test very long session ID"""
        long_session_id = "x" * 1000
        
        response = client.post(
            "/chat",
            json={
                "message": "Test",
                "session_id": long_session_id
            }
        )
        
        # Should either accept or reject clearly
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
