"""Semantic chunking using Legal-BERT embeddings."""
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from services.models.extraction_models import ExtractedDocument, TextBlock
from services.chunking.models import Chunk, ChunkingResult


class SemanticChunker:
    """Semantic document chunking using legal-domain embeddings.
    
    Uses Legal-BERT to understand document structure and create semantically
    coherent chunks that respect topic boundaries.
    
    TODO: If we change embedding models, we need to:
    1. Update MODEL_NAME
    2. Update EMBEDDING_DIMENSION
    3. Create new Pinecone index with new dimension
    """
    
    # Hardcoded for Legal-BERT (can be made configurable later)
    MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
    EMBEDDING_DIMENSION = 768
    
    def __init__(
        self,
        max_tokens: int = 800,
        overlap_tokens: int = 100,
        similarity_threshold: float = 0.65
    ):
        """Initialize semantic chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between adjacent chunks
            similarity_threshold: Similarity below this = topic boundary
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.similarity_threshold = similarity_threshold
        
        print(f"Loading Legal-BERT model: {self.MODEL_NAME}...")
        self.model = SentenceTransformer(self.MODEL_NAME)
        print(f"Model loaded. Embedding dimension: {self.EMBEDDING_DIMENSION}")
    
    def chunk(
        self,
        extracted: ExtractedDocument,
        document_id: int,
        case_id: int,
        classification: str = None,
        content_category: str = None
    ) -> ChunkingResult:
        """Chunk a document using semantic boundaries.
        
        Args:
            extracted: Extracted document with blocks
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            content_category: Content category
            
        Returns:
            ChunkingResult with chunks
        """
        # Step 1: Flatten blocks
        blocks = self._flatten_blocks(extracted)
        
        if len(blocks) == 0:
            # Empty document - return empty result
            return ChunkingResult(
                document_id=document_id,
                case_id=case_id,
                total_chunks=0,
                chunks=[],
                metadata={"note": "No text blocks found"}
            )
        
        # Step 2: Embed blocks
        embeddings = self._embed_blocks(blocks)
        
        # Step 3: Find semantic boundaries
        boundaries = self._find_boundaries(embeddings)
        
        # Step 4: Create initial chunks
        chunks = self._create_chunks(
            blocks=blocks,
            boundaries=boundaries,
            document_id=document_id,
            case_id=case_id,
            filename=extracted.original_filename,
            classification=classification,
            content_category=content_category
        )
        
        # Step 5: Handle oversized chunks
        chunks = self._split_oversized_chunks(chunks)
        
        # Step 6: Add overlap
        chunks = self._add_overlap(chunks, blocks)
        
        # Build result
        return ChunkingResult(
            document_id=document_id,
            case_id=case_id,
            total_chunks=len(chunks),
            chunking_method="semantic_legal_bert",
            chunks=chunks,
            metadata={
                "total_blocks": len(blocks),
                "boundaries_detected": len(boundaries),
                "avg_chunk_tokens": sum(c.token_count for c in chunks) // len(chunks) if chunks else 0
            }
        )
    
    def _flatten_blocks(self, extracted: ExtractedDocument) -> List[Tuple[TextBlock, int]]:
        """Flatten pages into list of (block, page_number) tuples.
        
        Filters out noise blocks (headers, footers, images, empty text).
        
        Args:
            extracted: Extracted document
            
        Returns:
            List of (block, page_index) tuples
        """
        blocks = []
        
        for page in extracted.pages:
            for block in page.blocks:
                # Skip noise blocks
                if block.kind in ["header", "footer", "image"]:
                    continue
                
                # Skip empty blocks
                if not block.text or not block.text.strip():
                    continue
                
                blocks.append((block, page.page_index))
        
        return blocks
    
    def _embed_blocks(self, blocks: List[Tuple[TextBlock, int]]) -> np.ndarray:
        """Create embeddings for all blocks.
        
        Args:
            blocks: List of (block, page_index) tuples
            
        Returns:
            Array of embeddings (n_blocks, 768)
        """
        texts = [block.text for block, _ in blocks]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return np.array(embeddings)
    
    def _find_boundaries(self, embeddings: np.ndarray) -> List[int]:
        """Find semantic boundaries using cosine similarity.
        
        Args:
            embeddings: Block embeddings
            
        Returns:
            List of boundary indices (where to split)
        """
        if len(embeddings) <= 1:
            return []
        
        boundaries = []
        
        # Calculate similarity between adjacent blocks
        for i in range(len(embeddings) - 1):
            similarity = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            
            # Low similarity = topic boundary
            if similarity < self.similarity_threshold:
                boundaries.append(i + 1)  # Boundary after block i
        
        return boundaries
    
    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec_a: First vector
            vec_b: Second vector
            
        Returns:
            Similarity score (0 to 1)
        """
        return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    
    def _create_chunks(
        self,
        blocks: List[Tuple[TextBlock, int]],
        boundaries: List[int],
        document_id: int,
        case_id: int,
        filename: str,
        classification: str,
        content_category: str
    ) -> List[Chunk]:
        """Create chunks at semantic boundaries.
        
        Args:
            blocks: List of (block, page_index) tuples
            boundaries: Boundary indices
            document_id: Document ID
            case_id: Case ID
            filename: Original filename
            classification: Document classification
            content_category: Content category
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        
        # Add final boundary
        all_boundaries = boundaries + [len(blocks)]
        
        for chunk_idx, end in enumerate(all_boundaries):
            chunk_blocks = blocks[start:end]
            
            if not chunk_blocks:
                continue
            
            # Extract text and metadata
            texts = [block.text for block, _ in chunk_blocks]
            block_ids = [block.block_id for block, _ in chunk_blocks]
            page_numbers = list(set(page_idx for _, page_idx in chunk_blocks))
            page_numbers.sort()
            
            # Combine text
            chunk_text = "\n\n".join(texts)
            
            # Estimate tokens
            token_count = self._estimate_tokens(chunk_text)
            
            chunk = Chunk(
                chunk_index=chunk_idx,
                chunk_id=f"doc{document_id}_chunk{chunk_idx}",
                text=chunk_text,
                block_ids=block_ids,
                page_numbers=page_numbers,
                token_count=token_count,
                document_id=document_id,
                case_id=case_id,
                document_filename=filename,
                classification=classification,
                content_category=content_category
            )
            
            chunks.append(chunk)
            start = end
        
        return chunks
    
    def _split_oversized_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Split chunks that exceed token limit.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of chunks with oversized ones split
        """
        result = []
        
        for chunk in chunks:
            if chunk.token_count <= self.max_tokens:
                result.append(chunk)
            else:
                # Split into smaller chunks
                split_chunks = self._split_chunk(chunk)
                result.extend(split_chunks)
        
        # Re-index chunks
        for i, chunk in enumerate(result):
            chunk.chunk_index = i
            chunk.chunk_id = f"doc{chunk.document_id}_chunk{i}"
        
        return result
    
    def _split_chunk(self, chunk: Chunk) -> List[Chunk]:
        """Split a single oversized chunk.
        
        Args:
            chunk: Chunk to split
            
        Returns:
            List of smaller chunks
        """
        # Split text by paragraphs
        paragraphs = chunk.text.split("\n\n")
        
        sub_chunks = []
        current_text = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            
            if current_tokens + para_tokens > self.max_tokens and current_text:
                # Create sub-chunk
                sub_chunks.append("\n\n".join(current_text))
                current_text = [para]
                current_tokens = para_tokens
            else:
                current_text.append(para)
                current_tokens += para_tokens
        
        # Add final sub-chunk
        if current_text:
            sub_chunks.append("\n\n".join(current_text))
        
        # Convert to Chunk objects
        result = []
        for i, text in enumerate(sub_chunks):
            result.append(Chunk(
                chunk_index=chunk.chunk_index + i,
                chunk_id=f"{chunk.chunk_id}_sub{i}",
                text=text,
                block_ids=chunk.block_ids,  # Approximate
                page_numbers=chunk.page_numbers,
                token_count=self._estimate_tokens(text),
                document_id=chunk.document_id,
                case_id=chunk.case_id,
                document_filename=chunk.document_filename,
                classification=chunk.classification,
                content_category=chunk.content_category
            ))
        
        return result
    
    def _add_overlap(self, chunks: List[Chunk], blocks: List[Tuple[TextBlock, int]]) -> List[Chunk]:
        """Add overlap between adjacent chunks.
        
        Args:
            chunks: List of chunks
            blocks: Original blocks
            
        Returns:
            Chunks with overlap added
        """
        # For MVP, skip overlap - it's complex to implement correctly
        # TODO: Add overlap in future iteration
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Approximate token count
        """
        # Rough estimate: ~4 characters per token
        return max(1, len(text) // 4)

