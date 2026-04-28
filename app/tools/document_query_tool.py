"""Document Query Tool - Query uploaded documents using RAG"""
from typing import Dict, Any, Optional
from app.tools.base_tool import BaseTool, ToolMetadata
from app.services.vector_store_service import vector_store_service
from app.services.chat_service import chat_service
import logging

logger = logging.getLogger(__name__)


class DocumentQueryTool(BaseTool):
    """
    Tool for querying uploaded documents using RAG (Retrieval-Augmented Generation)
    
    This tool:
    1. Performs semantic search over document chunks
    2. Retrieves relevant context
    3. Uses LLM to generate answer based on retrieved context
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="document_query",
            description="Query uploaded documents to answer questions based on their content. Use this for questions about uploaded contracts, reports, PDFs, or any document content.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or query about the documents"
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Optional: Specific document ID to search within (omit to search all documents)"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of relevant chunks to retrieve (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute document query using RAG
        
        Args:
            query: The question about documents
            document_id: Optional specific document to query
            n_results: Number of chunks to retrieve (default: 5)
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        query = kwargs.get("query")
        document_id = kwargs.get("document_id")
        n_results = kwargs.get("n_results", 5)
        
        if not query:
            return {
                "success": False,
                "result": None,
                "error": "Query parameter is required"
            }
        
        try:
            # Step 1: Retrieve relevant document chunks
            search_result = vector_store_service.query_similar_chunks(
                query_text=query,
                n_results=n_results,
                document_id=document_id
            )
            
            if not search_result["success"]:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Document search failed: {search_result.get('error', 'Unknown error')}"
                }
            
            results = search_result.get("results", [])
            
            if not results:
                return {
                    "success": True,
                    "result": {
                        "answer": "No relevant information found in the uploaded documents.",
                        "sources": [],
                        "query": query
                    },
                    "error": None
                }
            
            # Step 2: Build context from retrieved chunks
            context = self._build_context(results)
            
            # Step 3: Generate answer using LLM with context
            answer = await self._generate_answer(query, context)
            
            # Step 4: Format sources
            sources = self._format_sources(results)
            
            return {
                "success": True,
                "result": {
                    "answer": answer,
                    "sources": sources,
                    "query": query,
                    "chunks_used": len(results)
                },
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error executing document query: {str(e)}", exc_info=True)
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }
    
    def _build_context(self, results: list) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []
        for idx, result in enumerate(results, 1):
            metadata = result["metadata"]
            text = result["text"]
            source = metadata.get("source_filename", "Unknown")
            
            context_parts.append(
                f"[Source {idx}: {source}]\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with retrieved context"""
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided document excerpts.

Document Excerpts:
{context}

User Question: {query}

Instructions:
- Answer based ONLY on the information in the document excerpts above
- If the excerpts don't contain relevant information, say so clearly
- Be concise and accurate
- Cite which source(s) you used if possible

Answer:"""
        
        try:
            llm_response = await chat_service.process_message(
                message=prompt,
                session_id="document_query"
            )
            return llm_response.get("reply", "Unable to generate answer")
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Error generating answer: {str(e)}"
    
    def _format_sources(self, results: list) -> list:
        """Format source information for response"""
        sources = []
        for result in results:
            metadata = result["metadata"]
            sources.append({
                "filename": metadata.get("source_filename", "Unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "document_id": metadata.get("document_id", "Unknown"),
                "text_preview": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
            })
        return sources
