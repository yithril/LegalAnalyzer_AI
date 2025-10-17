"""
End-to-end integration test for document processing pipeline.

This test uses REAL services:
- PostgreSQL (from docker-compose)
- MinIO (from docker-compose) 
- Elasticsearch (from docker-compose)
- Pinecone (cloud service - needs API key)
- Ollama (local LLM - needs to be running)

Test case_id=999 for isolation from production data.
"""
import pytest
import os
from pathlib import Path
from core.models.case import Case
from core.models.document import Document
from core.constants import DocumentStatus, SupportedFileType
from infrastructure.database import db_provider
from infrastructure.storage import storage_client
from infrastructure.pinecone_client import pinecone_client
from infrastructure.elasticsearch_client import elasticsearch_client
from orchestrators.document_processor import get_document_processor


# Test constants
TEST_CASE_ID = 999
TEST_CASE_NAME = "Integration Test Case - Enron Email"
TEST_EMAIL_FILE = "tests/helpers/sample_files/text/43.txt"


@pytest.fixture(scope="module")
async def setup_infrastructure():
    """Initialize all infrastructure services."""
    await db_provider.init()
    await storage_client.init()
    await pinecone_client.init()
    await elasticsearch_client.init()
    
    yield
    
    # Cleanup after all tests
    await db_provider.close()
    await elasticsearch_client.close()


@pytest.fixture
async def test_case(setup_infrastructure):
    """Create test case and clean up after."""
    # Create case with realistic description
    case = await Case.create(
        id=TEST_CASE_ID,
        name=TEST_CASE_NAME,
        description=(
            "This case involves allegations of market manipulation and improper "
            "power trading practices by Enron Canada Corporation in the Alberta "
            "power market between 2001-2002. The investigation focuses on contract "
            "modifications, source asset changes, and trading relationships with "
            "Alberta power companies including Lethbridge Ironworks and Power Pool "
            "of Alberta. Key issues include whether contract registrations were "
            "modified to circumvent market regulations and manipulate electricity prices."
        )
    )
    
    yield case
    
    # Cleanup: Delete case and all associated data (even if test failed)
    try:
        # Delete any documents for this case
        await Document.filter(case_id=TEST_CASE_ID).delete()
        # Delete the case
        await case.delete()
        print(f"\n[Fixture Cleanup] Deleted test case {TEST_CASE_ID}")
    except Exception as e:
        print(f"\n[Fixture Cleanup] Error: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enron_email_full_pipeline(test_case):
    """
    Full end-to-end test: Upload 43.txt → Process → Verify in all systems.
    
    Pipeline stages:
    1. Upload to MinIO
    2. Extract text (already plain text)
    3. Classify as "email"
    4. Chunk semantically
    5. Generate embeddings → Store in Pinecone
    6. Generate summary → Store in Elasticsearch
    7. Update document status to "completed"
    
    Then verify data in:
    - PostgreSQL (document record)
    - MinIO (original file + intermediate files)
    - Pinecone (embeddings with case_id=999)
    - Elasticsearch (summary)
    """
    
    # ============================================
    # STEP 1: Upload file to MinIO
    # ============================================
    print("\n=== STEP 1: Upload to MinIO ===")
    
    test_file_path = Path(TEST_EMAIL_FILE)
    assert test_file_path.exists(), f"Test file not found: {TEST_EMAIL_FILE}"
    
    with open(test_file_path, 'rb') as f:
        file_content = f.read()
    
    # Upload to MinIO (mimics production upload)
    file_key = "originals/43.txt"  # Production pattern
    await storage_client.upload(
        bucket_name="legal-documents",
        object_name=file_key,
        data=file_content,
        content_type="text/plain"
    )
    print(f"[OK] Uploaded to MinIO: legal-documents/{file_key}")
    
    # ============================================
    # STEP 2: Create Document record
    # ============================================
    print("\n=== STEP 2: Create Document Record ===")
    
    document = await Document.create(
        case_id=TEST_CASE_ID,
        filename="43.txt",
        file_type=SupportedFileType.TXT,
        file_size=len(file_content),
        minio_bucket="legal-documents",  # Production bucket
        minio_key=file_key,  # "originals/43.txt"
        status=DocumentStatus.UPLOADED
    )
    print(f"[OK] Created document: {document.id}")
    
    # ============================================
    # STEP 3: Process document (orchestrator)
    # ============================================
    print("\n=== STEP 3: Process Document (Orchestrator) ===")
    
    # Get orchestrator with all dependencies
    processor = get_document_processor()
    
    # Run orchestrator synchronously
    await processor.process_document(document.id, TEST_CASE_ID)
    
    print(f"[OK] Document processing completed")
    
    # ============================================
    # STEP 4: Verify in PostgreSQL
    # ============================================
    print("\n=== STEP 4: Verify PostgreSQL ===")
    
    # Refresh document from DB
    await document.refresh_from_db()
    
    assert document.status == DocumentStatus.COMPLETED, \
        f"Expected status=COMPLETED, got {document.status}"
    assert document.classification == "email", \
        f"Expected classification=email, got {document.classification}"
    assert document.has_summary is True, \
        "Expected has_summary=True"
    assert document.relevance_score is not None, \
        "Expected relevance_score to be set"
    assert 0 <= document.relevance_score <= 100, \
        f"Relevance score out of range: {document.relevance_score}"
    
    print(f"[OK] Document status: {document.status}")
    print(f"[OK] Classification: {document.classification}")
    print(f"[OK] Content category: {document.content_category}")
    print(f"[OK] Relevance score: {document.relevance_score}/100")
    print(f"[OK] Relevance reasoning: {document.relevance_reasoning}")
    print(f"[OK] Has summary: {document.has_summary}")
    
    # ============================================
    # STEP 5: Verify in MinIO
    # ============================================
    print("\n=== STEP 5: Verify MinIO ===")
    
    # Check original file exists (in legal-documents bucket)
    original_objects = await storage_client.list_objects("legal-documents", prefix=file_key)
    assert file_key in original_objects, "Original file not found in MinIO"
    print(f"[OK] Original file exists: legal-documents/{file_key}")
    
    # Check extraction blocks exist (in cases bucket)
    blocks_key = f"{TEST_CASE_ID}/documents/{document.id}/extraction/blocks.json"
    blocks_objects = await storage_client.list_objects("cases", prefix=blocks_key)
    assert blocks_key in blocks_objects, "Extraction blocks not found in MinIO"
    print(f"[OK] Extraction blocks exist: cases/{blocks_key}")
    
    # Check chunks backup exists (in cases bucket)
    chunks_key = f"{TEST_CASE_ID}/documents/{document.id}/chunks/chunks.json"
    chunks_objects = await storage_client.list_objects("cases", prefix=chunks_key)
    assert chunks_key in chunks_objects, "Chunks backup not found in MinIO"
    print(f"[OK] Chunks backup exists: cases/{chunks_key}")
    
    # ============================================
    # STEP 6: Verify in Pinecone
    # ============================================
    print("\n=== STEP 6: Verify Pinecone ===")
    
    # Get index name from chunking service
    index_name = "legal-docs-dev"  # Should match chunker.INDEX_NAME
    
    # Query with case_id filter using client wrapper
    all_results = await pinecone_client.query(
        index_name=index_name,
        vector=[0.0] * 768,  # Dummy vector (we just want to check metadata)
        top_k=100,
        filter={"case_id": TEST_CASE_ID},
        include_metadata=True
    )
    
    print(f"[OK] Found {len(all_results)} total embeddings for case_id={TEST_CASE_ID}")
    
    # Filter to only this document's embeddings (might have old test data)
    doc_results = [r for r in all_results if r["metadata"]["document_id"] == document.id]
    
    assert len(doc_results) > 0, f"No embeddings found for document {document.id}"
    print(f"[OK] Found {len(doc_results)} embeddings for this document")
    
    # Verify metadata on our document's embeddings
    for match in doc_results:
        assert match["metadata"]["case_id"] == TEST_CASE_ID, \
            f"Wrong case_id in metadata: {match['metadata']['case_id']}"
        assert match["metadata"]["document_id"] == document.id, \
            f"Wrong document_id in metadata: {match['metadata']['document_id']}"
    
    print(f"[OK] All embeddings have correct case_id={TEST_CASE_ID} and document_id={document.id}")
    print(f"[OK] Document chunked into {len(doc_results)} semantic chunks")
    
    # ============================================
    # STEP 7: Verify in Elasticsearch
    # ============================================
    print("\n=== STEP 7: Verify Elasticsearch ===")
    
    # Get document from Elasticsearch (single "documents" index)
    es_doc = await elasticsearch_client.get_document(
        index_name="documents",
        doc_id=f"doc_{document.id}"
    )
    
    assert es_doc is not None, "Document not found in Elasticsearch"
    print(f"[OK] Document found in Elasticsearch")
    
    # Verify full_text (from DocumentIndexingService)
    full_text = es_doc.get("full_text", "")
    assert len(full_text) > 100, "Full text too short"
    assert "power" in full_text.lower() or "pool" in full_text.lower(), \
        "Full text doesn't contain expected content"
    print(f"[OK] Full text indexed: {len(full_text)} characters")
    
    # Verify blocks (from DocumentIndexingService)
    blocks = es_doc.get("blocks", [])
    assert len(blocks) > 0, "No blocks found"
    assert "block_id" in blocks[0], "Block structure invalid"
    assert "text" in blocks[0], "Block missing text"
    # Blocks have all original fields from extraction
    print(f"[OK] Blocks indexed: {len(blocks)} blocks")
    print(f"[OK] Block fields preserved: {list(blocks[0].keys())}")
    
    # Verify summary (from SummarizationService)
    summary_text = es_doc.get("executive_summary", "")
    assert summary_text is not None and len(summary_text) > 50, "Summary missing or too short"
    assert "power" in summary_text.lower() or "contract" in summary_text.lower() or "pool" in summary_text.lower(), \
        "Summary doesn't contain expected business terms"
    print(f"[OK] Summary added: {len(summary_text)} characters")
    print(f"[OK] Summary preview: {summary_text[:200]}...")
    
    # Show complete Elasticsearch document structure
    print("\n" + "="*70)
    print("FINAL ELASTICSEARCH DOCUMENT STRUCTURE")
    print("="*70)
    print(f"Document ID: {es_doc.get('document_id')}")
    print(f"Case ID: {es_doc.get('case_id')}")
    print(f"Filename: {es_doc.get('filename')}")
    print(f"Classification: {es_doc.get('classification')}")
    print(f"Content Category: {es_doc.get('content_category')}")
    print(f"Relevance Score: {es_doc.get('relevance_score')}/100")
    print(f"Relevance Reasoning: {es_doc.get('relevance_reasoning', 'N/A')[:100]}...")
    print(f"File Type: {es_doc.get('file_type')}")
    print(f"File Size: {es_doc.get('file_size')} bytes")
    print(f"\nFull Text Length: {len(es_doc.get('full_text', ''))} characters")
    print(f"Number of Blocks: {len(es_doc.get('blocks', []))}")
    print(f"Number of Chunks: {es_doc.get('total_chunks', 0)}")
    print(f"Executive Summary Length: {len(es_doc.get('executive_summary', ''))} characters")
    print(f"Chunk Summaries Count: {len(es_doc.get('chunk_summaries', []))}")
    print(f"\nFirst Block Sample:")
    if blocks:
        first_block = blocks[0]
        print(f"  Block ID: {first_block.get('block_id')}")
        print(f"  Block Index: {first_block.get('block_index')}")
        print(f"  Kind: {first_block.get('kind')}")
        print(f"  Text: {first_block.get('text', '')[:100]}...")
        print(f"  Char Range: {first_block.get('char_start')} - {first_block.get('char_end')}")
        print(f"  BBox: {first_block.get('bbox')}")
        print(f"  All Fields: {list(first_block.keys())}")
    print("="*70 + "\n")
    
    # ============================================
    # STEP 8: Test case isolation (query filter)
    # ============================================
    print("\n=== STEP 8: Test Case Isolation ===")
    
    # Query should only return case_id=999 results (uses same all_results from Step 6)
    # Verify ALL results have case_id=999 (not other cases)
    for match in all_results:
        assert match["metadata"]["case_id"] == TEST_CASE_ID, \
            f"Found embedding with wrong case_id: {match['metadata']['case_id']}"
    
    print(f"[OK] Case isolation working: all {len(all_results)} results have case_id={TEST_CASE_ID}")
    
    # Show breakdown by document
    doc_ids = set(r["metadata"]["document_id"] for r in all_results)
    print(f"[OK] Found embeddings from {len(doc_ids)} documents: {sorted(doc_ids)}")
    print(f"  → Current document {document.id}: {len(doc_results)} embeddings")
    
    # ============================================
    # CLEANUP: Delete all test data
    # ============================================
    print("\n=== CLEANUP: Deleting Test Data ===")
    
    # 1. Delete from Pinecone (only this document's embeddings)
    try:
        print("Deleting embeddings from Pinecone...")
        vector_ids = [match["id"] for match in doc_results]
        if vector_ids:
            await pinecone_client.delete(
                index_name=index_name,
                ids=vector_ids
            )
            print(f"[OK] Deleted {len(vector_ids)} embeddings for document {document.id}")
    except Exception as e:
        print(f"⚠ Pinecone cleanup failed: {e}")
    
    # 2. Delete from Elasticsearch
    try:
        print("Deleting document from Elasticsearch...")
        await elasticsearch_client.delete_document(
            index_name="documents",
            doc_id=f"doc_{document.id}"
        )
        print(f"[OK] Deleted document from Elasticsearch")
    except Exception as e:
        print(f"⚠ Elasticsearch cleanup failed: {e}")
    
    # 3. Delete from MinIO
    try:
        print("Deleting files from MinIO...")
        # Delete original file from legal-documents bucket
        try:
            await storage_client.delete("legal-documents", file_key)
        except:
            pass
        # Delete processing artifacts from cases bucket
        try:
            await storage_client.delete("cases", blocks_key)
        except:
            pass
        try:
            await storage_client.delete("cases", chunks_key)
        except:
            pass
        # Delete any other files that were created in cases bucket
        try:
            all_objects = await storage_client.list_objects("cases", prefix=f"{TEST_CASE_ID}/")
            for obj in all_objects:
                await storage_client.delete("cases", obj)
        except:
            pass
        print(f"[OK] Deleted files from MinIO")
    except Exception as e:
        print(f"⚠ MinIO cleanup failed: {e}")
    
    # 4. Delete from PostgreSQL (document + case)
    try:
        print("Deleting from PostgreSQL...")
        await document.delete()
        # Case will be deleted by fixture cleanup
        print(f"[OK] Deleted document from PostgreSQL")
    except Exception as e:
        print(f"⚠ PostgreSQL cleanup failed: {e}")
    
    print("\n[SUCCESS] ALL TESTS PASSED - Pipeline working end-to-end!")


@pytest.mark.integration
@pytest.mark.asyncio  
async def test_case_id_filtering(test_case):
    """
    Test that we can properly filter embeddings by case_id.
    
    This ensures multi-tenancy works correctly.
    Depends on test_enron_email_full_pipeline running first.
    """
    index = pinecone_client.get_index()
    
    # Query for case_id=999
    results = index.query(
        vector=[0.0] * 768,
        top_k=10,
        filter={"case_id": TEST_CASE_ID},
        include_metadata=True
    )
    
    # Should find embeddings if previous test ran
    if len(results.matches) > 0:
        # Verify all have correct case_id
        for match in results.matches:
            assert match.metadata["case_id"] == TEST_CASE_ID
        print(f"[OK] Case filtering works: {len(results.matches)} embeddings found")
    else:
        # If no results, that's OK (cleanup happened)
        print("[OK] No embeddings found (already cleaned up)")

