"""Query endpoints for semantic search over documents"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.vector_store_service import vector_store_service

router = APIRouter()


class QueryRequest(BaseModel):
    """Request schema for document query"""
    query: str = Field(..., description="Query text to search for")
    document_id: Optional[str] = Field(None, description="Optional: Filter results by specific document ID")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of results to return (1-20)")


class ChunkResult(BaseModel):
    """Schema for a single chunk result"""
    chunk_id: str
    text: str
    document_id: str
    source_filename: str
    chunk_index: int
    start_char: int
    end_char: int
    distance: Optional[float] = None


class QueryResponse(BaseModel):
    """Response schema for query endpoint"""
    query: str
    results: List[ChunkResult]
    count: int
    success: bool


@router.post("/query-doc", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using semantic search
    
    This endpoint:
    - Performs semantic search over all document chunks
    - Returns the most relevant text chunks
    - Can optionally filter by specific document
    - Uses ChromaDB's embedding-based similarity search
    
    Args:
        request: QueryRequest with query text and optional filters
        
    Returns:
        QueryResponse with relevant text chunks
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Perform semantic search
    search_result = vector_store_service.query_similar_chunks(
        query_text=request.query,
        n_results=request.n_results,
        document_id=request.document_id
    )
    
    if not search_result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {search_result.get('error', 'Unknown error')}"
        )
    
    # Format results
    formatted_results = []
    for result in search_result["results"]:
        metadata = result["metadata"]
        formatted_results.append({
            "chunk_id": result["chunk_id"],
            "text": result["text"],
            "document_id": metadata["document_id"],
            "source_filename": metadata["source_filename"],
            "chunk_index": metadata["chunk_index"],
            "start_char": metadata["start_char"],
            "end_char": metadata["end_char"],
            "distance": result.get("distance")
        })
    
    return {
        "query": request.query,
        "results": formatted_results,
        "count": len(formatted_results),
        "success": True
    }


@router.get("/query-doc/search")
async def query_documents_get(
    q: str = Query(..., description="Query text"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Query documents using GET method (for simple queries)
    
    Args:
        q: Query text
        document_id: Optional document ID filter
        n_results: Number of results to return
        
    Returns:
        Query results
    """
    request = QueryRequest(
        query=q,
        document_id=document_id,
        n_results=n_results
    )
    
    return await query_documents(request)


@router.get("/vector-store/stats")
async def get_vector_store_stats():
    """
    Get statistics about the vector store
    
    Returns:
        Vector store statistics including total chunks and documents
    """
    stats = vector_store_service.get_collection_stats()
    
    return {
        "success": True,
        "stats": stats
    }


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """
    Get all chunks for a specific document
    
    Args:
        document_id: Document ID
        
    Returns:
        List of all chunks for the document
    """
    chunks = vector_store_service.get_chunks_by_document(document_id)
    
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=f"No chunks found for document '{document_id}'"
        )
    
    return {
        "document_id": document_id,
        "chunks": chunks,
        "count": len(chunks),
        "success": True
    }


@router.post("/vector-store/clear")
async def clear_vector_store():
    """
    Clear all data from the vector store
    
    WARNING: This will delete all chunks for all documents!
    Use with caution.
    
    Returns:
        Operation result
    """
    result = vector_store_service.clear_collection()
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear vector store: {result.get('error')}"
        )
    
    return result
