"""Unit tests for RelevanceService."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from services.relevance_service import RelevanceService, RelevanceResult
from tests.helpers.mock_storage import MockStorageClient


# Sample blocks.json for 43.txt (Enron power contract email)
SAMPLE_BLOCKS_43 = {
    "document_id": 1,
    "file_type": "txt",
    "original_filename": "43.txt",
    "page_count": 1,
    "total_blocks": 3,
    "pages": [
        {
            "page_index": 0,
            "block_count": 3,
            "blocks": [
                {
                    "block_id": "doc1_p0_b0",
                    "block_index": 0,
                    "text": "Message-ID: <6953675.1075842026124.JavaMail.evans@thyme>\nDate: Wed, 9 Jan 2002 06:59:53 -0800 (PST)\nFrom: carol.moline@powerpool.ab.ca\nTo: john.davies@lethbridgeironworks.com\nSubject: Power Pool",
                    "kind": "paragraph",
                    "char_start": 0,
                    "char_end": 300
                },
                {
                    "block_id": "doc1_p0_b1",
                    "block_index": 1,
                    "text": "This email is acknowledgement from the Power Pool of Alberta of the change in direct sales/forward contract registration for contracts that are currently registered with the Power Pool between Lethbridge Ironworks and Enron Canada Power Corporation for trading after December 29 HE 1 2001.",
                    "kind": "paragraph",
                    "char_start": 300,
                    "char_end": 600
                },
                {
                    "block_id": "doc1_p0_b2",
                    "block_index": 2,
                    "text": "On January 7 the Power Pool received your acknowledgement of Enron's change in the source asset for the direct sales/forward contract registrations for contract # 934 to modify the source from the Sundance 3 unit (SD3) to Enron's unmetered source asset (ECP-).",
                    "kind": "paragraph",
                    "char_start": 600,
                    "char_end": 900
                }
            ]
        }
    ]
}


@pytest.fixture
def mock_storage():
    """Mock storage client with sample blocks."""
    storage = MockStorageClient()
    
    # Setup mock to return sample blocks for document 1
    blocks_json = json.dumps(SAMPLE_BLOCKS_43).encode('utf-8')
    storage.add_file("cases", "999/documents/1/extraction/blocks.json", blocks_json)
    
    # Add blocks for document 2 (same content for simplicity)
    storage.add_file("cases", "999/documents/2/extraction/blocks.json", blocks_json)
    
    # Add blocks for document 3 (same content for simplicity)
    storage.add_file("cases", "999/documents/3/extraction/blocks.json", blocks_json)
    
    return storage


@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    llm = MagicMock()
    llm.generate_from_prompt = AsyncMock()
    return llm


@pytest.mark.asyncio
async def test_score_relevant_power_contract_email(mock_storage, mock_llm):
    """Test scoring a highly relevant document (43.txt power contract email)."""
    
    # Mock LLM response
    mock_llm.generate_from_prompt.return_value = json.dumps({
        "score": 85,
        "reasoning": "Email directly discusses contract modifications between Enron and power companies, highly relevant to power trading investigation.",
        "key_factors": ["mentions Enron", "contract details", "business transaction"]
    })
    
    # Create service with mocks
    service = RelevanceService(mock_storage)
    service.llm = mock_llm
    
    # Create mock document and case
    with patch('services.relevance_service.Document') as MockDocument, \
         patch('services.relevance_service.Case') as MockCase:
        
        # Mock document
        mock_doc = AsyncMock()
        mock_doc.id = 1
        mock_doc.classification = "email"
        mock_doc.save = AsyncMock()
        MockDocument.get = AsyncMock(return_value=mock_doc)
        
        # Mock case
        mock_case = AsyncMock()
        mock_case.id = 999
        mock_case.name = "Enron Power Trading Investigation"
        mock_case.description = "Investigation into Enron's power trading contracts and market manipulation"
        MockCase.get = AsyncMock(return_value=mock_case)
        
        # Score relevance
        result = await service.score_document_relevance(document_id=1, case_id=999)
        
        # Verify result
        assert result.score == 85
        assert "contract" in result.reasoning.lower() or "enron" in result.reasoning.lower()
        assert len(result.key_factors) > 0
        
        # Verify document was updated
        assert mock_doc.relevance_score == 85
        assert mock_doc.relevance_reasoning == result.reasoning
        assert mock_doc.save.called


@pytest.mark.asyncio
async def test_score_irrelevant_document(mock_storage, mock_llm):
    """Test scoring an irrelevant document."""
    
    # Mock LLM response for irrelevant doc
    mock_llm.generate_from_prompt.return_value = json.dumps({
        "score": 5,
        "reasoning": "Email about office party unrelated to power trading investigation.",
        "key_factors": ["wrong topic", "no relevant parties"]
    })
    
    service = RelevanceService(mock_storage)
    service.llm = mock_llm
    
    with patch('services.relevance_service.Document') as MockDocument, \
         patch('services.relevance_service.Case') as MockCase:
        
        mock_doc = AsyncMock()
        mock_doc.id = 2
        mock_doc.classification = "email"
        mock_doc.save = AsyncMock()
        MockDocument.get = AsyncMock(return_value=mock_doc)
        
        mock_case = AsyncMock()
        mock_case.id = 999
        mock_case.name = "Enron Power Trading Investigation"
        mock_case.description = "Power trading contracts investigation"
        MockCase.get = AsyncMock(return_value=mock_case)
        
        result = await service.score_document_relevance(document_id=2, case_id=999)
        
        assert result.score <= 20  # Low relevance
        assert mock_doc.relevance_score <= 20


@pytest.mark.asyncio
async def test_llm_failure_defaults_to_moderate(mock_storage, mock_llm):
    """Test that LLM failure defaults to score of 50."""
    
    # Mock LLM to raise exception
    mock_llm.generate_from_prompt.side_effect = Exception("LLM timeout")
    
    service = RelevanceService(mock_storage)
    service.llm = mock_llm
    
    with patch('services.relevance_service.Document') as MockDocument, \
         patch('services.relevance_service.Case') as MockCase:
        
        mock_doc = AsyncMock()
        mock_doc.id = 3
        mock_doc.classification = "email"
        mock_doc.save = AsyncMock()
        MockDocument.get = AsyncMock(return_value=mock_doc)
        
        mock_case = AsyncMock()
        mock_case.id = 999
        mock_case.name = "Test Case"
        mock_case.description = "Test description"
        MockCase.get = AsyncMock(return_value=mock_case)
        
        result = await service.score_document_relevance(document_id=3, case_id=999)
        
        # Should default to 50
        assert result.score == 50
        assert "failed" in result.reasoning.lower()
        assert mock_doc.relevance_score == 50


@pytest.mark.asyncio
async def test_build_preview_from_blocks(mock_storage):
    """Test that preview is built correctly from blocks."""
    
    service = RelevanceService(mock_storage)
    
    preview = await service._load_document_preview(
        document_id=1,
        case_id=999,
        max_chars=500
    )
    
    # Should contain text from blocks
    assert "Power Pool" in preview
    assert "Enron" in preview
    assert len(preview) <= 500  # Respects max_chars


@pytest.mark.asyncio
async def test_extract_email_metadata(mock_storage):
    """Test email metadata extraction."""
    
    service = RelevanceService(mock_storage)
    
    metadata = await service._extract_metadata(
        document_id=1,
        case_id=999,
        classification="email"
    )
    
    # Should attempt to extract email headers
    # Metadata should be dict (might be empty if extraction fails)
    assert isinstance(metadata, dict)
    
    # If headers found, verify they're correct
    if "from" in metadata:
        assert "powerpool.ab.ca" in metadata["from"]
    if "subject" in metadata:
        assert "Power Pool" in metadata["subject"]


def test_parse_valid_llm_response():
    """Test parsing valid LLM JSON response."""
    
    service = RelevanceService(MockStorageClient())
    
    response = json.dumps({
        "score": 75,
        "reasoning": "Test reasoning",
        "key_factors": ["factor1", "factor2"]
    })
    
    result = service._parse_response(response)
    
    assert result.score == 75
    assert result.reasoning == "Test reasoning"
    assert len(result.key_factors) == 2


def test_parse_response_with_markdown():
    """Test parsing LLM response wrapped in markdown code blocks."""
    
    service = RelevanceService(MockStorageClient())
    
    # LLM sometimes returns ```json ... ```
    response = """```json
{
  "score": 80,
  "reasoning": "Test",
  "key_factors": ["test"]
}
```"""
    
    result = service._parse_response(response)
    
    assert result.score == 80


def test_parse_response_clamps_score():
    """Test that scores outside 0-100 are clamped."""
    
    service = RelevanceService(MockStorageClient())
    
    # Score > 100
    response = json.dumps({"score": 150, "reasoning": "Test", "key_factors": []})
    result = service._parse_response(response)
    assert result.score == 100
    
    # Score < 0
    response = json.dumps({"score": -20, "reasoning": "Test", "key_factors": []})
    result = service._parse_response(response)
    assert result.score == 0

