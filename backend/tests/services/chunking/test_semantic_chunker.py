"""Unit tests for semantic chunking."""
import pytest
import json
from pathlib import Path
from services.chunking.semantic_chunker import SemanticChunker
from services.models.extraction_models import ExtractedDocument


@pytest.mark.asyncio
async def test_semantic_chunker_with_pdf():
    """Test semantic chunker with PDF report blocks."""
    
    # Load PDF blocks sample
    blocks_path = Path(__file__).parent.parent.parent / "helpers" / "classification_samples" / "blocks.json"
    
    if not blocks_path.exists():
        pytest.skip(f"Blocks sample not found: {blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Semantic Chunker with PDF")
    print(f"{'='*70}")
    
    # Load extraction
    print("\n[LOADING EXTRACTION]")
    with open(blocks_path, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    extracted = ExtractedDocument(**extraction_data)
    print(f"  Pages: {extracted.page_count}")
    print(f"  Total blocks: {extracted.total_blocks}")
    
    # Create chunker
    print("\n[INITIALIZING CHUNKER]")
    chunker = SemanticChunker(
        max_tokens=800,
        overlap_tokens=100,
        similarity_threshold=0.65
    )
    
    # Run chunking
    print("\n[RUNNING CHUNKING]")
    result = chunker.chunk(
        extracted=extracted,
        document_id=123,
        case_id=456,
        classification="report",
        content_category="business_document"
    )
    
    print(f"\n[CHUNKING RESULTS]")
    print(f"  Total chunks: {result.total_chunks}")
    print(f"  Chunking method: {result.chunking_method}")
    print(f"  Avg chunk tokens: {result.metadata.get('avg_chunk_tokens')}")
    print(f"  Boundaries detected: {result.metadata.get('boundaries_detected')}")
    
    # Show first few chunks
    print(f"\n[CHUNK DETAILS]")
    for i, chunk in enumerate(result.chunks[:3]):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Tokens: {chunk.token_count}")
        print(f"  Pages: {chunk.page_numbers}")
        print(f"  Blocks: {len(chunk.block_ids)}")
        print(f"  Text preview: {chunk.text[:150]}...")
    
    if result.total_chunks > 3:
        print(f"\n... and {result.total_chunks - 3} more chunks")
    
    print(f"\n{'='*70}")
    
    # Assertions
    assert result.total_chunks > 0, "Should create at least one chunk"
    assert result.document_id == 123
    assert result.case_id == 456
    assert result.chunking_method == "semantic_legal_bert"
    
    # Check chunk properties
    for chunk in result.chunks:
        assert chunk.chunk_id.startswith("doc123_chunk")
        assert chunk.token_count > 0
        assert len(chunk.text) > 0
        assert chunk.document_id == 123
        assert chunk.case_id == 456
        assert chunk.classification == "report"
    
    # Check token limits (with some tolerance for estimation errors)
    for chunk in result.chunks:
        assert chunk.token_count <= 850, f"Chunk {chunk.chunk_id} exceeds token limit: {chunk.token_count}"
    
    print(f"[SUCCESS] All assertions passed!")


@pytest.mark.asyncio
async def test_semantic_chunker_with_email():
    """Test semantic chunker with simple email."""
    
    # Load email blocks sample
    blocks_path = Path(__file__).parent.parent.parent / "helpers" / "content_analysis_samples" / "email_blocks.json"
    
    if not blocks_path.exists():
        pytest.skip(f"Email blocks not found: {blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Semantic Chunker with Email")
    print(f"{'='*70}")
    
    # Load extraction
    with open(blocks_path, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    extracted = ExtractedDocument(**extraction_data)
    
    # Create chunker
    chunker = SemanticChunker()
    
    # Run chunking
    result = chunker.chunk(
        extracted=extracted,
        document_id=1,
        case_id=1,
        classification="email"
    )
    
    print(f"\n[RESULTS]")
    print(f"  Total chunks: {result.total_chunks}")
    print(f"  Chunk 0 tokens: {result.chunks[0].token_count if result.chunks else 'N/A'}")
    
    # Email is small - should be 1 chunk
    assert result.total_chunks == 1, "Small email should be single chunk"
    assert result.chunks[0].page_numbers == [0]
    
    print(f"[SUCCESS] Email chunking correct!")


@pytest.mark.asyncio
async def test_chunker_handles_empty_document():
    """Test that chunker handles document with no text blocks gracefully."""
    
    print(f"\n{'='*70}")
    print("Testing Empty Document Handling")
    print(f"{'='*70}")
    
    # Create empty extraction (only images/headers)
    extraction_data = {
        "model": "page_blocks.v1",
        "version": "extraction.v1",
        "document_id": 999,
        "file_type": "pdf",
        "original_filename": "empty.pdf",
        "page_count": 1,
        "total_blocks": 2,
        "pages": [{
            "page_index": 0,
            "block_count": 2,
            "blocks": [
                {"block_index": 0, "text": "", "kind": "header", "token_estimate": 0},
                {"block_index": 1, "text": "", "kind": "image", "token_estimate": 0}
            ]
        }],
        "extraction_metadata": {}
    }
    
    extracted = ExtractedDocument(**extraction_data)
    
    chunker = SemanticChunker()
    result = chunker.chunk(extracted, document_id=999, case_id=1)
    
    print(f"  Result: {result.total_chunks} chunks")
    assert result.total_chunks == 0, "Empty document should produce no chunks"
    assert "No text blocks found" in result.metadata.get("note", "")
    
    print(f"[SUCCESS] Empty document handled correctly!")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])

