# Document Upload Feature

## Overview

The document upload feature allows users to upload PDF and DOCX files, extract text content, and store the results for later retrieval. The system automatically:

- Validates file types (PDF and DOCX only)
- Generates unique filenames to prevent collisions
- Extracts text from uploaded documents
- Stores metadata (filename, upload time, text length, file size)
- Provides REST API for document management

## API Endpoints

### Upload Document

**POST** `/upload-doc`

Upload and process a PDF or DOCX document.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Response:**
```json
{
  "file_id": "a1b2c3d4e5f6",
  "original_filename": "my-document.pdf",
  "file_type": ".pdf",
  "upload_time": "2026-04-23T10:30:00.000000",
  "extracted_text_length": 1542,
  "file_size": 245760,
  "message": "Document uploaded and processed successfully"
}
```

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/upload-doc \
  -F "file=@/path/to/document.pdf"
```

**Example with Python:**
```python
import requests

url = "http://localhost:8000/upload-doc"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Example with JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload-doc', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### List All Documents

**GET** `/documents`

Get metadata for all uploaded documents.

**Response:**
```json
[
  {
    "file_id": "a1b2c3d4e5f6",
    "original_filename": "document.pdf",
    "stored_filename": "20260423_103000_a1b2c3d4e5f6.pdf",
    "file_type": ".pdf",
    "upload_time": "2026-04-23T10:30:00.000000",
    "extracted_text_length": 1542,
    "file_size": 245760
  }
]
```

### Get Document Details

**GET** `/documents/{file_id}`

Get full document details including extracted text.

**Response:**
```json
{
  "file_id": "a1b2c3d4e5f6",
  "metadata": {
    "file_id": "a1b2c3d4e5f6",
    "original_filename": "document.pdf",
    "stored_filename": "20260423_103000_a1b2c3d4e5f6.pdf",
    "file_type": ".pdf",
    "upload_time": "2026-04-23T10:30:00.000000",
    "extracted_text_length": 1542,
    "file_size": 245760
  },
  "extracted_text": "Full text content here...",
  "text_preview": "First 500 characters..."
}
```

### Get Document Text Only

**GET** `/documents/{file_id}/text`

Get only the extracted text.

**Response:**
```json
{
  "file_id": "a1b2c3d4e5f6",
  "extracted_text": "Full text content...",
  "text_length": 1542
}
```

### Get Document Metadata

**GET** `/documents/{file_id}/metadata`

Get only the metadata (without text).

### Delete Document

**DELETE** `/documents/{file_id}`

Delete a document and its associated file.

**Response:**
```json
{
  "message": "Document 'a1b2c3d4e5f6' deleted successfully",
  "file_id": "a1b2c3d4e5f6"
}
```

## File Validation

### Supported File Types
- PDF (`.pdf`)
- DOCX (`.docx`)

### File Size Limit
- Maximum: **10 MB**

### Validation Errors

**Unsupported file type:**
```json
{
  "detail": "Unsupported file type. Supported: .pdf, .docx"
}
```

**File too large:**
```json
{
  "detail": "File size exceeds maximum limit of 10.0MB"
}
```

**Empty file:**
```json
{
  "detail": "File is empty"
}
```

## Text Extraction

### PDF Files
- Uses `pypdf` library
- Extracts text from all pages
- Handles multi-page documents
- Logs warnings for pages that fail extraction
- Concatenates text from all pages

### DOCX Files
- Uses `python-docx` library
- Extracts text from paragraphs
- Extracts text from tables
- Preserves document structure

## Storage

### File Storage
- Files are saved in the `uploads/` directory
- Unique filenames generated: `YYYYMMDD_HHMMSS_uniqueid.ext`
- Example: `20260423_103000_a1b2c3d4e5.pdf`

### Metadata Storage
Currently stored in-memory (for development):
- Production: Use a database (PostgreSQL, MongoDB, etc.)
- Includes: file_id, original_filename, stored_filename, file_type, upload_time, extracted_text_length, file_size

### Text Storage
Currently stored in-memory with metadata:
- Production: Use a vector database for semantic search
- Full extracted text is preserved
- Can be used for RAG, search, summarization, etc.

## Error Handling

All endpoints include comprehensive error handling:

- **400 Bad Request**: Invalid input, unsupported file type, file too large
- **404 Not Found**: Document ID not found
- **500 Internal Server Error**: File processing errors, disk errors

## Integration Examples

### Complete Upload Flow

```python
import requests
import json

# 1. Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/upload-doc", files=files)
    result = response.json()
    file_id = result["file_id"]
    print(f"Uploaded: {file_id}")

# 2. Get extracted text
text_response = requests.get(f"http://localhost:8000/documents/{file_id}/text")
text_data = text_response.json()
print(f"Text length: {text_data['text_length']}")

# 3. List all documents
docs_response = requests.get("http://localhost:8000/documents")
documents = docs_response.json()
print(f"Total documents: {len(documents)}")

# 4. Delete document
delete_response = requests.delete(f"http://localhost:8000/documents/{file_id}")
print(delete_response.json()["message"])
```

### Use with Agent System

You can integrate document upload with the agent system:

```python
# 1. Upload document
upload_response = requests.post(
    "http://localhost:8000/upload-doc",
    files={"file": open("contract.pdf", "rb")}
)
file_id = upload_response.json()["file_id"]

# 2. Get extracted text
text_response = requests.get(f"http://localhost:8000/documents/{file_id}/text")
document_text = text_response.json()["extracted_text"]

# 3. Query agent about the document
agent_response = requests.post(
    "http://localhost:8000/agent",
    json={
        "query": f"Summarize this document: {document_text[:2000]}",
        "session_id": "user123"
    }
)
print(agent_response.json()["response"])
```

## Testing

### Test with Sample PDF

```bash
# Create a simple test PDF first, then:
curl -X POST http://localhost:8000/upload-doc \
  -F "file=@test.pdf"
```

### Test with Sample DOCX

```bash
curl -X POST http://localhost:8000/upload-doc \
  -F "file=@test.docx"
```

### List Uploaded Documents

```bash
curl http://localhost:8000/documents
```

### Get Document Text

```bash
curl http://localhost:8000/documents/{file_id}/text
```

## Production Considerations

### Database Integration

Replace in-memory storage with a database:

```python
# PostgreSQL example
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    file_id = Column(String, primary_key=True)
    original_filename = Column(String)
    stored_filename = Column(String)
    file_type = Column(String)
    upload_time = Column(DateTime)
    extracted_text = Column(Text)
    extracted_text_length = Column(Integer)
    file_size = Column(Integer)
```

### Cloud Storage

For scalability, use cloud storage (S3, Azure Blob, GCS):

```python
import boto3

s3_client = boto3.client('s3')

# Upload to S3
s3_client.upload_fileobj(
    file_content,
    'my-bucket',
    stored_filename
)
```

### Vector Database

For semantic search capabilities:

```python
from chromadb import Client

chroma_client = Client()
collection = chroma_client.create_collection("documents")

# Add document
collection.add(
    documents=[extracted_text],
    metadatas=[{"file_id": file_id, "filename": filename}],
    ids=[file_id]
)

# Semantic search
results = collection.query(
    query_texts=["contract terms"],
    n_results=5
)
```

## Next Steps

1. ✅ Upload and process documents
2. 📝 Integrate with vector database for semantic search
3. 🤖 Create tools for document-based agent queries
4. 📊 Add document analytics and insights
5. 🔍 Implement full-text search
6. 🗄️ Add database persistence
7. ☁️ Integrate cloud storage

## API Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
