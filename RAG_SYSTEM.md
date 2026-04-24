# RAG System - Semantic Document Search

## Overview

This RAG (Retrieval-Augmented Generation) system enables semantic search over uploaded documents. When you upload a document:

1. **Text Extraction** - Extract text from PDF/DOCX files
2. **Chunking** - Split text into overlapping chunks (500 chars with 100 char overlap)
3. **Embedding** - Generate embeddings for each chunk using ChromaDB
4. **Storage** - Store chunks with metadata in vector database
5. **Query** - Semantic search to find relevant chunks

## Architecture

```
Document Upload → Text Extraction → Chunking → Embeddings → ChromaDB
                                                                  ↓
User Query → Embedding → Similarity Search → Top K Chunks → Response
```

## Components

### 1. EmbeddingService (`app/services/embedding_service.py`)

Handles text chunking with configurable parameters.

**Features:**
- Configurable chunk size (default: 500 characters)
- Configurable overlap (default: 100 characters)
- Unique chunk IDs with metadata
- Sentence-based chunking option
- Chunk statistics

**Chunk Metadata:**
- `chunk_id` - Unique identifier
- `document_id` - Parent document ID
- `source_filename` - Original file name
- `chunk_index` - Position in document
- `start_char` - Start position in original text
- `end_char` - End position in original text
- `text_length` - Length of chunk text

### 2. VectorStoreService (`app/services/vector_store_service.py`)

Manages ChromaDB for vector storage and similarity search.

**Features:**
- Automatic embedding generation via ChromaDB
- Persistent storage in `chroma_db/` directory
- Semantic similarity search
- Filter by document ID
- CRUD operations on chunks
- Collection statistics

### 3. Enhanced DocumentService

Automatically creates and stores chunks when documents are uploaded.

**Updated Flow:**
1. Upload document
2. Extract text
3. Create chunks
4. Store chunks in vector database
5. Return metadata + chunk count

## API Endpoints

### Query Documents

#### POST `/query-doc`

Perform semantic search over all documents.

**Request:**
```json
{
  "query": "What are the key terms in the contract?",
  "document_id": "optional-filter-by-doc-id",
  "n_results": 5
}
```

**Response:**
```json
{
  "query": "What are the key terms in the contract?",
  "results": [
    {
      "chunk_id": "abc123_chunk_0_hash",
      "text": "Key terms include payment schedule...",
      "document_id": "abc123",
      "source_filename": "contract.pdf",
      "chunk_index": 0,
      "start_char": 0,
      "end_char": 500,
      "distance": 0.234
    }
  ],
  "count": 5,
  "success": true
}
```

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/query-doc \
  -H "Content-Type: application/json" \
  -d '{
    "query": "payment terms",
    "n_results": 3
  }'
```

**Example with Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/query-doc",
    json={
        "query": "What are the requirements?",
        "n_results": 5
    }
)

results = response.json()
for chunk in results["results"]:
    print(f"Document: {chunk['source_filename']}")
    print(f"Text: {chunk['text'][:100]}...")
    print(f"Distance: {chunk['distance']}")
    print("---")
```

#### GET `/query-doc/search`

Simple GET method for queries (useful for browser testing).

**Example:**
```bash
curl "http://localhost:8000/query-doc/search?q=contract+terms&n_results=3"
```

### Get Document Chunks

#### GET `/documents/{document_id}/chunks`

Get all chunks for a specific document.

**Response:**
```json
{
  "document_id": "abc123",
  "chunks": [
    {
      "chunk_id": "abc123_chunk_0_hash",
      "text": "Chunk text here...",
      "metadata": {
        "document_id": "abc123",
        "source_filename": "document.pdf",
        "chunk_index": 0,
        "start_char": 0,
        "end_char": 500
      }
    }
  ],
  "count": 15,
  "success": true
}
```

### Vector Store Statistics

#### GET `/vector-store/stats`

Get statistics about the vector database.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_chunks": 127,
    "unique_documents_sampled": 8,
    "collection_name": "document_chunks",
    "persist_directory": "./chroma_db"
  }
}
```

### Clear Vector Store

#### POST `/vector-store/clear`

**WARNING:** Deletes all chunks from the vector database!

## Configuration

### Chunk Size Settings

Modify in `app/services/embedding_service.py`:

```python
# Default settings
DEFAULT_CHUNK_SIZE = 500      # characters
DEFAULT_CHUNK_OVERLAP = 100   # characters

# Create custom instance
custom_service = EmbeddingService(
    chunk_size=1000,
    chunk_overlap=200
)
```

### Choosing Chunk Size

| Document Type | Recommended Chunk Size | Overlap |
|--------------|----------------------|---------|
| Short documents (emails, notes) | 300-500 | 50-100 |
| Medium documents (articles) | 500-800 | 100-150 |
| Long documents (books, reports) | 800-1200 | 150-200 |
| Code documentation | 400-600 | 100 |

**Factors to consider:**
- **Smaller chunks** = More precise matches, but may lose context
- **Larger chunks** = More context, but less precise
- **More overlap** = Better context preservation, more storage
- **Less overlap** = Less redundancy, faster search

## Complete Workflow Example

### 1. Upload a Document

```bash
curl -X POST http://localhost:8000/upload-doc \
  -F "file=@research_paper.pdf"
```

**Response:**
```json
{
  "file_id": "abc123",
  "original_filename": "research_paper.pdf",
  "file_type": ".pdf",
  "upload_time": "2026-04-25T10:00:00",
  "extracted_text_length": 12500,
  "file_size": 456789,
  "chunks_created": 25,
  "message": "Document uploaded and processed successfully"
}
```

### 2. Query the Document

```bash
curl -X POST http://localhost:8000/query-doc \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main hypothesis?",
    "document_id": "abc123",
    "n_results": 3
  }'
```

**Response:**
```json
{
  "query": "What is the main hypothesis?",
  "results": [
    {
      "chunk_id": "abc123_chunk_5",
      "text": "The main hypothesis of this study is that...",
      "document_id": "abc123",
      "source_filename": "research_paper.pdf",
      "chunk_index": 5,
      "distance": 0.123
    }
  ],
  "count": 3,
  "success": true
}
```

### 3. Query Across All Documents

```bash
curl -X POST http://localhost:8000/query-doc \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning applications",
    "n_results": 10
  }'
```

This searches across ALL uploaded documents.

## Integration with Agent System

Combine RAG with the agent system for intelligent document Q&A:

```python
import requests

# 1. Upload document
upload_response = requests.post(
    "http://localhost:8000/upload-doc",
    files={"file": open("document.pdf", "rb")}
)
file_id = upload_response.json()["file_id"]

# 2. Query for relevant chunks
query_response = requests.post(
    "http://localhost:8000/query-doc",
    json={
        "query": "What are the main risks?",
        "document_id": file_id,
        "n_results": 3
    }
)

# 3. Extract relevant text
chunks = query_response.json()["results"]
context = "\n".join([chunk["text"] for chunk in chunks])

# 4. Ask agent with context
agent_response = requests.post(
    "http://localhost:8000/agent",
    json={
        "query": f"Based on this context: {context}\n\nWhat are the main risks?",
        "session_id": "user123"
    }
)

print(agent_response.json()["response"])
```

## Advanced Usage

### Sentence-Based Chunking

For better semantic boundaries:

```python
from app.services.embedding_service import embedding_service

chunks = embedding_service.split_text_by_sentences(
    text=extracted_text,
    document_id=file_id,
    source_filename=filename,
    max_chunk_size=600
)
```

### Custom Chunk Metadata

Add custom metadata to chunks:

```python
# When adding to vector store
vector_store_service.collection.add(
    ids=[chunk.chunk_id],
    documents=[chunk.text],
    metadatas=[{
        "document_id": chunk.document_id,
        "source_filename": chunk.source_filename,
        "custom_field": "custom_value",
        "tags": ["important", "contract"]
    }]
)
```

### Filter by Multiple Criteria

```python
# Query with complex filters
results = vector_store_service.collection.query(
    query_texts=["search query"],
    where={
        "$and": [
            {"document_id": {"$eq": "abc123"}},
            {"chunk_index": {"$gte": 5}}
        ]
    },
    n_results=5
)
```

## Performance Optimization

### Batch Processing

For multiple documents:

```python
for file in files:
    # Upload and chunk documents in batch
    # ChromaDB handles embedding generation efficiently
    pass
```

### Chunking Strategy

```python
# Get chunk statistics
stats = embedding_service.get_chunk_statistics(chunks)
print(f"Average chunk length: {stats['avg_chunk_length']}")
print(f"Total chunks: {stats['total_chunks']}")

# Adjust if needed
if stats['avg_chunk_length'] < 300:
    # Chunks too small, increase chunk_size
    pass
```

## Troubleshooting

### Empty Results

**Problem:** Query returns no results.

**Solutions:**
1. Check if documents are uploaded: `GET /documents`
2. Verify chunks exist: `GET /documents/{file_id}/chunks`
3. Check vector store: `GET /vector-store/stats`
4. Try broader query terms

### Poor Search Quality

**Problem:** Results not relevant.

**Solutions:**
1. Adjust chunk size (try 600-800 characters)
2. Increase overlap (try 150-200 characters)
3. Use sentence-based chunking
4. Rephrase query to be more specific

### Storage Issues

**Problem:** ChromaDB taking too much space.

**Solutions:**
1. Clear old documents
2. Reduce chunk overlap
3. Increase chunk size (fewer chunks)
4. Implement retention policy

## Production Considerations

### Database Migration

Replace in-memory storage with PostgreSQL:

```python
# Store chunks metadata in database
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.file_id"))
    text = Column(Text)
    chunk_index = Column(Integer)
    # ... other fields
```

### Scaling ChromaDB

For production scale:

```python
# Use ChromaDB client-server mode
import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(
    host="chromadb-server",
    port=8000
)
```

### Monitoring

Track key metrics:
- Query latency
- Chunk retrieval accuracy
- Storage size
- Number of queries per document

## Next Steps

1. ✅ Upload documents and query them
2. 📊 Integrate with agent for Q&A
3. 🔍 Fine-tune chunk size for your use case
4. 🗄️ Add database persistence
5. 📈 Implement analytics and monitoring
6. 🚀 Scale with distributed ChromaDB

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.
