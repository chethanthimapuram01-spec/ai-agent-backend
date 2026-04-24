"""Embedding service for text chunking and embeddings generation"""
import logging
from typing import List, Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


class TextChunk:
    """Represents a chunk of text with metadata"""
    
    def __init__(
        self,
        chunk_id: str,
        text: str,
        document_id: str,
        source_filename: str,
        chunk_index: int,
        start_char: int,
        end_char: int
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.document_id = document_id
        self.source_filename = source_filename
        self.chunk_index = chunk_index
        self.start_char = start_char
        self.end_char = end_char
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "document_id": self.document_id,
            "source_filename": self.source_filename,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "text_length": len(self.text)
        }


class EmbeddingService:
    """Service for text chunking and embedding generation"""
    
    # Default chunking parameters
    DEFAULT_CHUNK_SIZE = 500  # characters
    DEFAULT_CHUNK_OVERLAP = 100  # characters
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        """
        Initialize embedding service
        
        Args:
            chunk_size: Size of each text chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(
            f"EmbeddingService initialized - chunk_size: {chunk_size}, "
            f"overlap: {chunk_overlap}"
        )
    
    def split_text_into_chunks(
        self,
        text: str,
        document_id: str,
        source_filename: str
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to split
            document_id: ID of the source document
            source_filename: Name of the source file
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for document {document_id}")
            return []
        
        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0
        
        while start < text_length:
            # Calculate end position
            end = min(start + self.chunk_size, text_length)
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Only create chunk if it has content
            if chunk_text:
                # Generate unique chunk ID
                chunk_id = self._generate_chunk_id(
                    document_id,
                    chunk_index,
                    chunk_text
                )
                
                chunk = TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    document_id=document_id,
                    source_filename=source_filename,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end
                )
                
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop for very small texts
            if start <= 0 and chunk_index > 0:
                break
        
        logger.info(
            f"Split document {document_id} into {len(chunks)} chunks "
            f"(text length: {text_length})"
        )
        
        return chunks
    
    def _generate_chunk_id(
        self,
        document_id: str,
        chunk_index: int,
        chunk_text: str
    ) -> str:
        """
        Generate a unique ID for a chunk
        
        Args:
            document_id: Parent document ID
            chunk_index: Index of the chunk
            chunk_text: Text content of the chunk
            
        Returns:
            Unique chunk ID
        """
        # Create hash from document_id, index, and text content
        content = f"{document_id}_{chunk_index}_{chunk_text[:50]}"
        hash_value = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return f"{document_id}_chunk_{chunk_index}_{hash_value}"
    
    def split_text_by_sentences(
        self,
        text: str,
        document_id: str,
        source_filename: str,
        max_chunk_size: Optional[int] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks by sentences (alternative method)
        
        This method respects sentence boundaries for better semantic coherence.
        
        Args:
            text: Full text to split
            document_id: ID of the source document
            source_filename: Name of the source file
            max_chunk_size: Maximum chunk size (uses default if None)
            
        Returns:
            List of TextChunk objects
        """
        if max_chunk_size is None:
            max_chunk_size = self.chunk_size
        
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        start_char = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size and we have content
            if current_length + sentence_length > max_chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk)
                end_char = start_char + len(chunk_text)
                
                chunk_id = self._generate_chunk_id(
                    document_id,
                    chunk_index,
                    chunk_text
                )
                
                chunk = TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    document_id=document_id,
                    source_filename=source_filename,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char
                )
                
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap (keep last sentence)
                if self.chunk_overlap > 0 and len(current_chunk) > 1:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                    start_char = end_char - current_length
                else:
                    current_chunk = []
                    current_length = 0
                    start_char = end_char
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk if there's content
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            end_char = start_char + len(chunk_text)
            
            chunk_id = self._generate_chunk_id(
                document_id,
                chunk_index,
                chunk_text
            )
            
            chunk = TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                document_id=document_id,
                source_filename=source_filename,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=end_char
            )
            
            chunks.append(chunk)
        
        logger.info(
            f"Split document {document_id} into {len(chunks)} chunks "
            f"using sentence-based splitting"
        )
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        This is a simple implementation. For better results, use NLP libraries.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        import re
        
        # Simple sentence splitting by common terminators
        # This can be improved with libraries like spaCy or nltk
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about chunks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_length": 0,
                "min_chunk_length": 0,
                "max_chunk_length": 0
            }
        
        chunk_lengths = [len(chunk.text) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths),
            "total_text_length": sum(chunk_lengths)
        }


# Singleton instance
embedding_service = EmbeddingService()
