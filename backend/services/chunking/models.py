"""Data models for document chunking."""
from typing import List, Optional
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Represents a semantic chunk of a document."""
    
    chunk_index: int = Field(..., description="Index of this chunk in the document (0-based)")
    chunk_id: str = Field(..., description="Unique identifier (e.g., 'doc123_chunk5')")
    text: str = Field(..., description="Full text content of the chunk")
    
    # Block references
    block_ids: List[str] = Field(default_factory=list, description="IDs of blocks in this chunk")
    page_numbers: List[int] = Field(default_factory=list, description="Page numbers this chunk spans")
    
    # Metrics
    token_count: int = Field(..., description="Approximate token count")
    
    # Metadata for Pinecone
    document_id: int = Field(..., description="Document ID")
    case_id: int = Field(..., description="Case ID")
    document_filename: Optional[str] = Field(None, description="Original filename")
    classification: Optional[str] = Field(None, description="Document classification")
    content_category: Optional[str] = Field(None, description="Content category from analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_index": 0,
                "chunk_id": "doc123_chunk0",
                "text": "Employment Agreement\n\nThis agreement made...",
                "block_ids": ["doc123_p0_b0", "doc123_p0_b1"],
                "page_numbers": [0, 1],
                "token_count": 650,
                "document_id": 123,
                "case_id": 456,
                "document_filename": "contract.pdf",
                "classification": "contract"
            }
        }


class ChunkingResult(BaseModel):
    """Result of chunking a document."""
    
    document_id: int = Field(..., description="Document ID")
    case_id: int = Field(..., description="Case ID")
    total_chunks: int = Field(..., description="Number of chunks created")
    chunking_method: str = Field(default="semantic_legal_bert", description="Chunking strategy used")
    chunks: List[Chunk] = Field(default_factory=list, description="List of chunks")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 123,
                "case_id": 456,
                "total_chunks": 15,
                "chunking_method": "semantic_legal_bert",
                "chunks": [],
                "metadata": {
                    "avg_chunk_size": 650,
                    "boundaries_detected": 14
                }
            }
        }

