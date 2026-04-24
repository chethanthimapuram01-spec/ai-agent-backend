"""Vector store service using ChromaDB for document chunks"""
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.services.embedding_service import TextChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for storing and querying document chunks using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB vector store
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or get collection for document chunks
        self.collection = self.client.get_or_create_collection(
            name="document_chunks",
            metadata={"description": "Document text chunks with embeddings"}
        )
        
        logger.info(f"VectorStoreService initialized with persist_directory: {persist_directory}")
        logger.info(f"Collection 'document_chunks' has {self.collection.count()} items")
    
    def add_chunks(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Add text chunks to the vector store
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            Dictionary with operation results
        """
        if not chunks:
            logger.warning("No chunks provided to add")
            return {
                "success": False,
                "chunks_added": 0,
                "error": "No chunks provided"
            }
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = [
                {
                    "document_id": chunk.document_id,
                    "source_filename": chunk.source_filename,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "text_length": len(chunk.text)
                }
                for chunk in chunks
            ]
            
            # Add to collection (ChromaDB automatically generates embeddings)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
            return {
                "success": True,
                "chunks_added": len(chunks),
                "document_id": chunks[0].document_id if chunks else None,
                "collection_size": self.collection.count()
            }
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            return {
                "success": False,
                "chunks_added": 0,
                "error": str(e)
            }
    
    def query_similar_chunks(
        self,
        query_text: str,
        n_results: int = 5,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query for similar chunks using semantic search
        
        Args:
            query_text: Query text to search for
            n_results: Number of results to return
            document_id: Optional filter by document ID
            
        Returns:
            Dictionary with query results
        """
        try:
            # Build where clause for filtering
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "chunk_id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(
                f"Query executed - found {len(formatted_results)} results "
                f"for query: '{query_text[:50]}...'"
            )
            
            return {
                "success": True,
                "query": query_text,
                "results": formatted_results,
                "count": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            return {
                "success": False,
                "query": query_text,
                "results": [],
                "count": 0,
                "error": str(e)
            }
    
    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document
        
        Args:
            document_id: Document ID to filter by
            
        Returns:
            List of chunks with metadata
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            chunks = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    chunks.append({
                        "chunk_id": results['ids'][i],
                        "text": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    })
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting chunks by document: {str(e)}")
            return []
    
    def delete_document_chunks(self, document_id: str) -> Dict[str, Any]:
        """
        Delete all chunks for a specific document
        
        Args:
            document_id: Document ID to delete chunks for
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results['ids']:
                logger.info(f"No chunks found for document {document_id}")
                return {
                    "success": True,
                    "chunks_deleted": 0,
                    "message": "No chunks found for this document"
                }
            
            # Delete the chunks
            self.collection.delete(
                where={"document_id": document_id}
            )
            
            chunks_deleted = len(results['ids'])
            logger.info(f"Deleted {chunks_deleted} chunks for document {document_id}")
            
            return {
                "success": True,
                "chunks_deleted": chunks_deleted,
                "collection_size": self.collection.count()
            }
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            return {
                "success": False,
                "chunks_deleted": 0,
                "error": str(e)
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            total_count = self.collection.count()
            
            # Get sample of documents to analyze
            sample = self.collection.get(limit=100)
            
            # Count unique documents
            unique_docs = set()
            if sample['metadatas']:
                unique_docs = set(meta.get('document_id') for meta in sample['metadatas'])
            
            return {
                "total_chunks": total_count,
                "unique_documents_sampled": len(unique_docs),
                "collection_name": self.collection.name,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "total_chunks": 0,
                "error": str(e)
            }
    
    def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all data from the collection (use with caution)
        
        Returns:
            Dictionary with operation results
        """
        try:
            # Delete the collection
            self.client.delete_collection(name="document_chunks")
            
            # Recreate it
            self.collection = self.client.get_or_create_collection(
                name="document_chunks",
                metadata={"description": "Document text chunks with embeddings"}
            )
            
            logger.warning("Collection cleared - all chunks deleted")
            
            return {
                "success": True,
                "message": "Collection cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
vector_store_service = VectorStoreService()
