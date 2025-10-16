"""Test content analysis service that filters unwanted documents."""
import pytest
from pathlib import Path
from services.content_analysis_service import ContentAnalysisService


class MockStorageClient:
    """Mock storage client for testing."""
    
    def __init__(self, blocks_json_path: Path):
        self.blocks_json_path = blocks_json_path
    
    async def download(self, bucket_name: str, object_name: str) -> bytes:
        """Return the sample blocks.json."""
        return self.blocks_json_path.read_bytes()


@pytest.mark.asyncio
async def test_legitimate_business_email():
    """Test that legitimate business email is NOT filtered out.
    
    Should return should_process=True.
    """
    # Load legitimate email blocks.json
    email_blocks_path = Path(__file__).parent.parent / "helpers" / "content_analysis_samples" / "email_blocks.json"
    
    if not email_blocks_path.exists():
        pytest.skip(f"Email blocks.json not found: {email_blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Legitimate Business Email")
    print(f"{'='*70}")
    print(f"Sample file: {email_blocks_path}")
    
    # Create service with mock storage
    mock_storage = MockStorageClient(email_blocks_path)
    service = ContentAnalysisService(storage_client=mock_storage)
    
    # Load extraction
    print("\n[LOADING EXTRACTION]")
    import json
    from services.models.extraction_models import ExtractedDocument
    
    extraction_bytes = await mock_storage.download("cases", "dummy/path")
    extraction_data = json.loads(extraction_bytes.decode('utf-8'))
    extracted = ExtractedDocument(**extraction_data)
    
    print(f"  Pages: {extracted.page_count}")
    print(f"  Blocks: {extracted.total_blocks}")
    
    # Create sample
    print("\n[CREATING SAMPLE]")
    sample = service._create_sample_from_blocks(extracted)
    print(f"  Sample length: {len(sample)} characters")
    print(f"  Preview: {sample[:200]}...")
    
    # Analyze with EmailAnalyzer
    print("\n[RUNNING EMAIL ANALYZER]")
    email_analyzer = service._select_analyzer("email", sample)
    decision = await email_analyzer.analyze(sample, {"filename": "email.txt"})
    
    print(f"\n[ANALYSIS RESULT]")
    print(f"  should_process: {decision.should_process}")
    print(f"  category: {decision.category}")
    print(f"  confidence: {decision.confidence:.2f}")
    print(f"  reasoning: {decision.reasoning}")
    
    # Legitimate business email should be processed
    assert decision.should_process is True, f"Expected legitimate email to pass through, but got: {decision.reasoning}"
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Legitimate email correctly passed through")
    print(f"{'='*70}\n")


@pytest.mark.asyncio
async def test_spam_email_filtered():
    """Test that spam email IS filtered out.
    
    Should return should_process=False.
    """
    # Load spam blocks.json
    spam_blocks_path = Path(__file__).parent.parent / "helpers" / "content_analysis_samples" / "spam_blocks.json"
    
    if not spam_blocks_path.exists():
        pytest.skip(f"Spam blocks.json not found: {spam_blocks_path}")
    
    print(f"\n{'='*70}")
    print("Testing Spam Email Detection")
    print(f"{'='*70}")
    print(f"Sample file: {spam_blocks_path}")
    
    # Create service with mock storage
    mock_storage = MockStorageClient(spam_blocks_path)
    service = ContentAnalysisService(storage_client=mock_storage)
    
    # Load extraction
    print("\n[LOADING EXTRACTION]")
    import json
    from services.models.extraction_models import ExtractedDocument
    
    extraction_bytes = await mock_storage.download("cases", "dummy/path")
    extraction_data = json.loads(extraction_bytes.decode('utf-8'))
    extracted = ExtractedDocument(**extraction_data)
    
    print(f"  Pages: {extracted.page_count}")
    print(f"  Blocks: {extracted.total_blocks}")
    
    # Create sample
    print("\n[CREATING SAMPLE]")
    sample = service._create_sample_from_blocks(extracted)
    print(f"  Sample length: {len(sample)} characters")
    print(f"  Preview: {sample[:200]}...")
    
    # Analyze with EmailAnalyzer
    print("\n[RUNNING EMAIL ANALYZER]")
    email_analyzer = service._select_analyzer("email", sample)
    decision = await email_analyzer.analyze(sample, {"filename": "spam.txt"})
    
    print(f"\n[ANALYSIS RESULT]")
    print(f"  should_process: {decision.should_process}")
    print(f"  category: {decision.category}")
    print(f"  confidence: {decision.confidence:.2f}")
    print(f"  reasoning: {decision.reasoning}")
    
    # Spam should be filtered out
    if decision.should_process:
        print(f"\n[WARNING] Spam was NOT filtered out!")
        print(f"  This may need prompt engineering in email_analyzer")
    else:
        print(f"\n[SUCCESS] Spam correctly filtered out!")
    
    print(f"{'='*70}\n")
    
    # Assert (but show why if it fails)
    assert decision.should_process is False, f"Expected spam to be filtered, but got: {decision.reasoning}"


@pytest.mark.asyncio
async def test_analyzer_routing():
    """Test that different classifications route to correct analyzers."""
    
    mock_storage = MockStorageClient(Path("dummy"))
    service = ContentAnalysisService(storage_client=mock_storage)
    
    # Test various classifications
    test_cases = [
        ("email", "EmailAnalyzer"),
        ("business_email", "EmailAnalyzer"),
        ("correspondence", "EmailAnalyzer"),
        ("contract", "DefaultAnalyzer"),
        ("report", "DefaultAnalyzer"),
        ("memo", "DefaultAnalyzer"),
        ("unknown", "DefaultAnalyzer"),
    ]
    
    print(f"\n{'='*70}")
    print("Testing Analyzer Routing")
    print(f"{'='*70}")
    
    for classification, expected_analyzer in test_cases:
        analyzer = service._select_analyzer(classification, "sample content")
        actual_analyzer = analyzer.__class__.__name__
        
        status = "PASS" if actual_analyzer == expected_analyzer else "FAIL"
        print(f"  [{status}] '{classification}' => {actual_analyzer}")
        
        assert actual_analyzer == expected_analyzer, f"Expected {expected_analyzer}, got {actual_analyzer}"
    
    print(f"{'='*70}\n")

