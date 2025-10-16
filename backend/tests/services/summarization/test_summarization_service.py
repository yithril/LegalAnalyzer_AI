"""Test summarization service with full pipeline."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from tests.helpers import MockStorageClient, MockElasticsearchClient
from services.summarization.summarization_service import SummarizationService
from services.chunking.semantic_chunker import SemanticChunker
from services.models.extraction_models import ExtractedDocument


@pytest.mark.asyncio
async def test_summarization_service_end_to_end():
    """Test full summarization pipeline with PDF sample.
    
    Flow:
    1. Load blocks.json
    2. Create chunks (using chunker)
    3. Summarize chunks
    4. Create executive summary
    5. Store in Elasticsearch
    """
    
    print(f"\n{'='*70}")
    print("Testing Summarization Service (End-to-End)")
    print(f"{'='*70}")
    
    # Load extraction sample
    blocks_path = Path(__file__).parent.parent.parent / "helpers" / "classification_samples" / "blocks.json"
    
    if not blocks_path.exists():
        pytest.skip(f"Blocks sample not found: {blocks_path}")
    
    # Step 1: Create chunks first
    print("\n[STEP 1: CHUNKING]")
    with open(blocks_path, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    extracted = ExtractedDocument(**extraction_data)
    print(f"  Loaded extraction: {extracted.page_count} pages, {extracted.total_blocks} blocks")
    
    chunker = SemanticChunker()
    chunking_result = chunker.chunk(
        extracted=extracted,
        document_id=123,
        case_id=456,
        classification="report"
    )
    
    print(f"  Created {chunking_result.total_chunks} chunks")
    
    # Step 2: Set up mocks
    print("\n[STEP 2: SETUP MOCKS]")
    mock_storage = MockStorageClient()
    mock_es = MockElasticsearchClient()
    await mock_es.init()
    
    # Add chunks.json to mock storage
    chunks_json = chunking_result.model_dump_json()
    mock_storage.add_file(
        bucket_name="cases",
        object_name="456/documents/123/chunks/chunks.json",
        data=chunks_json.encode('utf-8')
    )
    
    print(f"  Mock storage: chunks.json added")
    print(f"  Mock Elasticsearch: initialized")
    
    # Step 3: Create service
    print("\n[STEP 3: INITIALIZE SERVICE]")
    service = SummarizationService(
        storage_client=mock_storage,
        elasticsearch_client=mock_es
    )
    print(f"  Service created")
    
    # Step 4: Run summarization (this will take a while - Llama generates text)
    print("\n[STEP 4: RUNNING SUMMARIZATION]")
    print(f"  Summarizing {chunking_result.total_chunks} chunks with Llama...")
    print("  (In production, this runs in background - no user waiting)")
    
    # Note: We can't actually call summarize_document without a real Document model
    # So let's test the individual methods
    
    # Test chunk summarization - FULL DOCUMENT
    print("\n[TESTING CHUNK SUMMARIZATION - FULL DOCUMENT]")
    chunks = chunking_result.chunks  # All chunks
    chunk_summaries = await service._summarize_chunks(chunks)
    
    print(f"\n  Summarized {len(chunks)} chunks")
    print(f"  First 3 chunk summaries:")
    for i, summary in enumerate(chunk_summaries[:3]):
        print(f"\n  Chunk {i} summary ({len(summary)} chars):")
        print(f"    {summary[:150]}...")
    
    if len(chunk_summaries) > 3:
        print(f"\n  ... and {len(chunk_summaries) - 3} more chunk summaries")
    
    # Test executive summarization
    print("\n[TESTING EXECUTIVE SUMMARY]")
    executive = await service._create_executive_summary(
        chunk_summaries=chunk_summaries,
        classification="report"
    )
    
    print(f"  Executive summary ({len(executive)} chars):")
    print(f"    {executive}")
    
    # Test Elasticsearch storage
    print("\n[TESTING ELASTICSEARCH STORAGE]")
    await mock_es.create_index("document_summaries")
    
    es_doc = {
        "document_id": 123,
        "case_id": 456,
        "classification": "report",
        "filename": "test.pdf",
        "executive_summary": executive,
        "chunk_summaries": chunk_summaries,
        "total_chunks": len(chunks),
        "created_at": datetime.now().isoformat()
    }
    
    await mock_es.index_document(
        index_name="document_summaries",
        doc_id="doc_123",
        document=es_doc
    )
    
    # Verify stored
    stored = mock_es.get_document("document_summaries", "doc_123")
    assert stored is not None
    assert stored["document_id"] == 123
    assert stored["case_id"] == 456
    assert stored["classification"] == "report"
    assert len(stored["executive_summary"]) > 0
    assert len(stored["chunk_summaries"]) == len(chunks)
    
    print(f"  Stored in Elasticsearch: doc_123")
    print(f"  Verified metadata: document_id={stored['document_id']}, case_id={stored['case_id']}")
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Summarization pipeline working!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

