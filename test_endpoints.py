"""
Test suite for API endpoints: health, chat, and document routes

Tests cover:
- Health check endpoint
- Chat endpoint with valid/invalid inputs
- Document upload and validation
- Document retrieval and listing
- Document deletion

Run with: pytest test_endpoints.py -v
"""
import pytest
import asyncio
import io
from fastapi.testclient import TestClient
from fastapi import UploadFile
from unittest.mock import Mock, patch, AsyncMock
from app.main import app
from app.services.chat_service import chat_service
from app.services.document_service import document_service

# Initialize test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self):
        """Test health endpoint returns healthy status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert data["message"] == "Service is running"
    
    def test_health_check_structure(self):
        """Test health endpoint response structure"""
        response = client.get("/health")
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "message" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)


class TestChatEndpoint:
    """Test chat endpoint functionality"""
    
    def test_chat_success(self):
        """Test successful chat interaction"""
        with patch('app.services.chat_service.chat_service.process_message') as mock_process:
            # Mock the chat service response
            mock_process.return_value = {
                "reply": "Hello! How can I help you?",
                "session_id": "test-session-123",
                "status": "success",
                "timestamp": "2026-05-08T10:00:00"
            }
            
            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "session_id": "test-session-123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["session_id"] == "test-session-123"
            assert "reply" in data
    
    def test_chat_empty_message(self):
        """Test chat with empty message returns 400"""
        response = client.post(
            "/chat",
            json={
                "message": "",
                "session_id": "test-session-123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_chat_whitespace_message(self):
        """Test chat with whitespace-only message returns 400"""
        response = client.post(
            "/chat",
            json={
                "message": "   ",
                "session_id": "test-session-123"
            }
        )
        
        assert response.status_code == 400
    
    def test_chat_empty_session_id(self):
        """Test chat with empty session_id returns 400"""
        response = client.post(
            "/chat",
            json={
                "message": "Hello",
                "session_id": ""
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "session" in data["detail"].lower()
    
    def test_chat_missing_message(self):
        """Test chat with missing message field returns 422"""
        response = client.post(
            "/chat",
            json={
                "session_id": "test-session-123"
            }
        )
        
        assert response.status_code == 422
    
    def test_chat_missing_session_id(self):
        """Test chat with missing session_id field returns 422"""
        response = client.post(
            "/chat",
            json={
                "message": "Hello"
            }
        )
        
        assert response.status_code == 422
    
    def test_chat_invalid_json(self):
        """Test chat with invalid JSON returns 422"""
        response = client.post(
            "/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestDocumentUploadEndpoint:
    """Test document upload functionality"""
    
    def test_upload_pdf_success(self):
        """Test successful PDF upload"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nTest PDF content"
        
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.return_value = {
                "metadata": {
                    "file_id": "test-file-123",
                    "original_filename": "test.pdf",
                    "file_type": ".pdf",
                    "upload_time": "2026-05-08T10:00:00",
                    "extracted_text_length": 100,
                    "file_size": len(pdf_content)
                }
            }
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.pdf", pdf_content, "application/pdf")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == "test-file-123"
            assert data["original_filename"] == "test.pdf"
            assert data["file_type"] == ".pdf"
            assert "message" in data
    
    def test_upload_docx_success(self):
        """Test successful DOCX upload"""
        # Create a mock DOCX file (simplified)
        docx_content = b"PK\x03\x04" + b"\x00" * 100  # DOCX files are ZIP archives
        
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.return_value = {
                "metadata": {
                    "file_id": "test-file-456",
                    "original_filename": "test.docx",
                    "file_type": ".docx",
                    "upload_time": "2026-05-08T10:00:00",
                    "extracted_text_length": 150,
                    "file_size": len(docx_content)
                }
            }
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["original_filename"] == "test.docx"
    
    def test_upload_no_file(self):
        """Test upload without file returns 422"""
        response = client.post("/upload-doc")
        assert response.status_code == 422
    
    def test_upload_empty_file(self):
        """Test upload of empty file returns 400 or 500"""
        response = client.post(
            "/upload-doc",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        
        # Accept either 400 (validation error) or 500 (processing error)
        assert response.status_code in [400, 500]
        data = response.json()
        assert "detail" in data
    
    def test_upload_file_too_large(self):
        """Test upload of file exceeding size limit"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/upload-doc",
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )
        
        # Accept either 400 (validation error) or 500 (processing error)
        # Large file upload might timeout or cause server error
        assert response.status_code in [400, 413, 500]
        data = response.json()
        assert "detail" in data
    
    def test_upload_invalid_file_type(self):
        """Test upload of unsupported file type returns 400"""
        with patch('app.services.document_service.document_service.save_and_process_file') as mock_save:
            mock_save.side_effect = ValueError("Unsupported file type")
            
            response = client.post(
                "/upload-doc",
                files={"file": ("test.txt", b"text content", "text/plain")}
            )
            
            assert response.status_code == 400


class TestDocumentRetrievalEndpoint:
    """Test document retrieval endpoints"""
    
    def test_list_documents_empty(self):
        """Test listing documents when none exist"""
        with patch('app.services.document_service.document_service.get_all_documents') as mock_list:
            mock_list.return_value = []
            
            response = client.get("/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
    
    def test_list_documents_success(self):
        """Test listing documents with results"""
        with patch('app.services.document_service.document_service.get_all_documents') as mock_list:
            mock_list.return_value = [
                {
                    "file_id": "file-1",
                    "original_filename": "doc1.pdf",
                    "stored_filename": "stored1.pdf",
                    "file_type": ".pdf",
                    "upload_time": "2026-05-08T10:00:00",
                    "extracted_text_length": 100,
                    "file_size": 1024
                },
                {
                    "file_id": "file-2",
                    "original_filename": "doc2.docx",
                    "stored_filename": "stored2.docx",
                    "file_type": ".docx",
                    "upload_time": "2026-05-08T11:00:00",
                    "extracted_text_length": 200,
                    "file_size": 2048
                }
            ]
            
            response = client.get("/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["file_id"] == "file-1"
            assert data[1]["file_id"] == "file-2"
    
    def test_get_document_details_success(self):
        """Test getting document details"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = {
                "file_id": "file-123",
                "metadata": {
                    "original_filename": "test.pdf",
                    "file_type": ".pdf"
                },
                "extracted_text": "This is the full extracted text from the document."
            }
            
            response = client.get("/documents/file-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == "file-123"
            assert "metadata" in data
            assert "extracted_text" in data
            assert "text_preview" in data
    
    def test_get_document_not_found(self):
        """Test getting non-existent document returns 404"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/documents/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_get_document_text_success(self):
        """Test getting document text only"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = {
                "extracted_text": "Sample text content"
            }
            
            response = client.get("/documents/file-123/text")
            
            assert response.status_code == 200
            data = response.json()
            assert "extracted_text" in data
            assert "text_length" in data
            assert data["extracted_text"] == "Sample text content"
    
    def test_get_document_text_not_found(self):
        """Test getting text for non-existent document returns 404"""
        with patch('app.services.document_service.document_service.get_document') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/documents/non-existent/text")
            
            assert response.status_code == 404


class TestDocumentDeletionEndpoint:
    """Test document deletion functionality"""
    
    def test_delete_document_success(self):
        """Test successful document deletion"""
        with patch('app.services.document_service.document_service.delete_document') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/documents/file-123")
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["file_id"] == "file-123"
            assert "deleted" in data["message"].lower()
    
    def test_delete_document_not_found(self):
        """Test deleting non-existent document returns 404"""
        with patch('app.services.document_service.document_service.delete_document') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/documents/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
