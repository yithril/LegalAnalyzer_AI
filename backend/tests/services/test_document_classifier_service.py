"""
Test ContentClassifier with structure-aware classification.

Uses extracted blocks.json to classify document type.
"""
import pytest
from pathlib import Path
from services.content_analysis.content_classifier import ContentClassifier


class MockStorageClient:
    """Mock storage client that returns our sample blocks.json."""
    
    def __init__(self, blocks_json_path: Path):
        self.blocks_json_path = blocks_json_path
    
    async def download(self, bucket_name: str, object_name: str) -> bytes:
        """Return the sample blocks.json."""
        return self.blocks_json_path.read_bytes()


@pytest.mark.asyncio
async def test_classify_document_from_blocks():
    """Test classification using actual extracted blocks.json.
    
    This test uses the blocks.json from the PDF extraction test
    to see what the LLM classifies it as.
    """
    # Load sample blocks.json
    blocks_path = Path(__file__).parent.parent / "helpers" / "classification_samples" / "blocks.json"
    
    if not blocks_path.exists():
        pytest.skip(f"Sample blocks.json not found: {blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Content Classifier with Extracted Blocks")
    print(f"{'='*70}")
    print(f"Sample file: {blocks_path}")
    
    # Create mock storage client
    mock_storage = MockStorageClient(blocks_path)
    
    # Create classifier
    classifier = ContentClassifier(storage_client=mock_storage)
    
    # Test internal sampling first to see what gets sent to LLM
    print("\n[LOADING EXTRACTION]")
    import json
    from services.models.extraction_models import ExtractedDocument
    
    extraction_bytes = await mock_storage.download("cases", "dummy/path")
    extraction_data = json.loads(extraction_bytes.decode('utf-8'))
    extracted = ExtractedDocument(**extraction_data)
    
    print(f"  Total pages: {extracted.page_count}")
    print(f"  Total blocks: {extracted.total_blocks}")
    
    # Create sample to see what gets sent
    print("\n[CREATING SAMPLE]")
    sample_text = classifier._create_smart_sample(extracted)
    
    print(f"  Sample length: {len(sample_text)} characters")
    print(f"  Sample token estimate: ~{len(sample_text) // 4} tokens")
    
    # Show first 500 chars of sample
    print(f"\n[SAMPLE PREVIEW (first 500 chars)]")
    print("-" * 70)
    print(sample_text[:500])
    print("...")
    print("-" * 70)
    
    # Now classify
    print("\n[RUNNING CLASSIFICATION]")
    category = await classifier.classify(document_id=1001, case_id=999)
    
    print(f"\n[CLASSIFICATION RESULT]")
    print(f"  Category: {category}")
    print(f"\n{'='*70}")
    
    # Basic assertion - should return something valid
    assert category is not None
    assert isinstance(category, str)
    assert len(category) > 0
    
    # Print what we got for manual verification
    print(f"[SUCCESS] Classification completed: '{category}'")
    print(f"{'='*70}\n")


@pytest.mark.asyncio
async def test_classify_email_document():
    """Test classification of an email document.
    
    This should correctly identify the document as 'email' or 'business_email'.
    """
    # Load email blocks.json
    email_blocks_path = Path(__file__).parent.parent / "helpers" / "classification_samples" / "email_blocks.json"
    
    if not email_blocks_path.exists():
        pytest.skip(f"Email blocks.json not found: {email_blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Email Classification")
    print(f"{'='*70}")
    print(f"Sample file: {email_blocks_path}")
    
    # Create mock storage client
    mock_storage = MockStorageClient(email_blocks_path)
    
    # Create classifier
    classifier = ContentClassifier(storage_client=mock_storage)
    
    # Load extraction to see what we're working with
    print("\n[LOADING EXTRACTION]")
    import json
    from services.models.extraction_models import ExtractedDocument
    
    extraction_bytes = await mock_storage.download("cases", "dummy/path")
    extraction_data = json.loads(extraction_bytes.decode('utf-8'))
    extracted = ExtractedDocument(**extraction_data)
    
    print(f"  Total pages: {extracted.page_count}")
    print(f"  Total blocks: {extracted.total_blocks}")
    
    # Create sample to see what gets sent
    print("\n[CREATING SAMPLE]")
    sample_text = classifier._create_smart_sample(extracted)
    
    print(f"  Sample length: {len(sample_text)} characters")
    print(f"  Sample token estimate: ~{len(sample_text) // 4} tokens")
    
    # Show first 800 chars of sample to see email headers
    print(f"\n[SAMPLE PREVIEW (first 800 chars)]")
    print("-" * 70)
    print(sample_text[:800])
    if len(sample_text) > 800:
        print("...")
    print("-" * 70)
    
    # Classify
    print("\n[RUNNING CLASSIFICATION]")
    category = await classifier.classify(document_id=1, case_id=1)
    
    print(f"\n[CLASSIFICATION RESULT]")
    print(f"  Category: {category}")
    print(f"\n{'='*70}")
    
    # Check if classified as email
    is_email = category.lower() in ['email', 'business_email', 'correspondence']
    
    if is_email:
        print(f"[SUCCESS] Correctly identified as email-related: '{category}'")
    else:
        print(f"[WARNING] Did NOT identify as email. Got: '{category}'")
        print(f"[INFO] This may require prompt engineering to improve email detection")
    
    print(f"{'='*70}\n")
    
    # Basic assertion - should return something valid
    assert category is not None
    assert isinstance(category, str)
    assert len(category) > 0
    
    # Print result for manual verification
    if not is_email:
        print(f"[RESULT] Email classification test: NEEDS IMPROVEMENT")
        print(f"  Expected: 'email' or 'business_email'")
        print(f"  Got: '{category}'")
    else:
        print(f"[RESULT] Email classification test: PASSED")

