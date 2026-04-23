"""Document upload and management endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.document_service import document_service

router = APIRouter()


class UploadResponse(BaseModel):
    """Response schema for document upload"""
    file_id: str = Field(..., description="Unique file identifier")
    original_filename: str = Field(..., description="Original name of uploaded file")
    file_type: str = Field(..., description="File extension type")
    upload_time: str = Field(..., description="Upload timestamp")
    extracted_text_length: int = Field(..., description="Length of extracted text")
    file_size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Success message")


class DocumentDetailsResponse(BaseModel):
    """Response schema for document details with full text"""
    file_id: str
    metadata: Dict[str, Any]
    extracted_text: str
    text_preview: str


class DocumentMetadataResponse(BaseModel):
    """Response schema for document metadata only"""
    file_id: str
    original_filename: str
    stored_filename: str
    file_type: str
    upload_time: str
    extracted_text_length: int
    file_size: int


@router.post("/upload-doc", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document (PDF or DOCX)
    
    This endpoint:
    - Validates file type (PDF or DOCX only)
    - Saves the file with a unique name
    - Extracts text content
    - Stores metadata and extracted text
    
    Args:
        file: Uploaded file (PDF or DOCX)
        
    Returns:
        UploadResponse with file metadata and success message
    """
    # Validate file is provided
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no filename")
    
    # Check file size (limit to 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Process the file
        result = await document_service.save_and_process_file(
            file_content=file_content,
            filename=file.filename
        )
        
        metadata = result["metadata"]
        
        return {
            "file_id": metadata["file_id"],
            "original_filename": metadata["original_filename"],
            "file_type": metadata["file_type"],
            "upload_time": metadata["upload_time"],
            "extracted_text_length": metadata["extracted_text_length"],
            "file_size": metadata["file_size"],
            "message": "Document uploaded and processed successfully"
        }
        
    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentMetadataResponse])
async def list_documents():
    """
    List all uploaded documents (metadata only)
    
    Returns:
        List of document metadata
    """
    documents = document_service.get_all_documents()
    
    return [
        {
            "file_id": doc["file_id"],
            "original_filename": doc["original_filename"],
            "stored_filename": doc["stored_filename"],
            "file_type": doc["file_type"],
            "upload_time": doc["upload_time"],
            "extracted_text_length": doc["extracted_text_length"],
            "file_size": doc["file_size"]
        }
        for doc in documents
    ]


@router.get("/documents/{file_id}", response_model=DocumentDetailsResponse)
async def get_document_details(file_id: str):
    """
    Get document details including extracted text
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Document details with full extracted text
    """
    document = document_service.get_document(file_id)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID '{file_id}' not found")
    
    extracted_text = document["extracted_text"]
    
    return {
        "file_id": file_id,
        "metadata": document["metadata"],
        "extracted_text": extracted_text,
        "text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
    }


@router.get("/documents/{file_id}/text")
async def get_document_text(file_id: str):
    """
    Get only the extracted text for a document
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Extracted text as plain text
    """
    document = document_service.get_document(file_id)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID '{file_id}' not found")
    
    return {
        "file_id": file_id,
        "extracted_text": document["extracted_text"],
        "text_length": len(document["extracted_text"])
    }


@router.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """
    Delete a document
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Success message
    """
    success = document_service.delete_document(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID '{file_id}' not found")
    
    return {
        "message": f"Document '{file_id}' deleted successfully",
        "file_id": file_id
    }


@router.get("/documents/{file_id}/metadata")
async def get_document_metadata(file_id: str):
    """
    Get only the metadata for a document (without full text)
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Document metadata
    """
    document = document_service.get_document(file_id)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID '{file_id}' not found")
    
    return document["metadata"]
