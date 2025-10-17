"""Integration test for RelevanceService with real LLM.

Uses real Ollama LLM to score actual document relevance.
Mocks database and storage, uses pre-extracted blocks from test_data.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from services.relevance_service import RelevanceService
from tests.helpers.mock_storage import MockStorageClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_scores_enron_power_email():
    """Test RelevanceService with REAL LLM on actual 43.txt email.
    
    This test:
    1. Uses real Ollama LLM (not mocked)
    2. Uses real blocks from S3 (if they exist from previous integration test)
    3. Mocks only the database (Document and Case models)
    4. Shows what the AI actually thinks about relevance
    
    Prerequisites:
    - Ollama running locally
    - Previous integration test created blocks.json in S3
    """
    
    print("\n" + "="*70)
    print("TESTING RELEVANCE SCORING WITH REAL LLM")
    print("="*70)
    
    # Load pre-extracted blocks for 43.txt
    blocks_file = Path("tests/helpers/test_data/43_blocks.json")
    with open(blocks_file, 'r') as f:
        blocks_data = json.load(f)
    
    # Create mock storage with pre-extracted blocks
    mock_storage = MockStorageClient()
    mock_storage.add_file(
        "cases",
        "999/documents/999/extraction/blocks.json",
        json.dumps(blocks_data).encode('utf-8')
    )
    print("[OK] Loaded pre-extracted blocks from test_data")
    
    # Create service with mocked storage but REAL LLM
    service = RelevanceService(mock_storage)
    
    # Mock database models
    with patch('services.relevance_service.Document') as MockDocument, \
         patch('services.relevance_service.Case') as MockCase:
        
        # Mock document (email about power contracts)
        mock_doc = AsyncMock()
        mock_doc.id = 999  # Use a known document from integration test
        mock_doc.classification = "email"
        mock_doc.save = AsyncMock()
        MockDocument.get = AsyncMock(return_value=mock_doc)
        
        # Mock case - Enron investigation (realistic description)
        mock_case = AsyncMock()
        mock_case.id = 999
        mock_case.name = "Alberta Energy Regulator v. Enron Canada"
        mock_case.description = (
            "This case involves allegations of market manipulation and improper "
            "power trading practices by Enron Canada Corporation in the Alberta "
            "power market between 2001-2002. The investigation focuses on contract "
            "modifications, source asset changes, and trading relationships with "
            "Alberta power companies including Lethbridge Ironworks and Power Pool "
            "of Alberta. Key issues include whether contract registrations were "
            "modified to circumvent market regulations."
        )
        MockCase.get = AsyncMock(return_value=mock_case)
        
        print(f"\nCase: {mock_case.name}")
        print(f"Description: {mock_case.description}")
        print(f"\nDocument: 43.txt (Enron power contract email)")
        print("Subject: Power Pool contract modification")
        print("\nCalling real LLM for relevance scoring...")
        print("-" * 70)
        
        # Score relevance with REAL LLM
        try:
            result = await service.score_document_relevance(
                document_id=999,
                case_id=999
            )
            
            print("\n" + "="*70)
            print("REAL LLM RELEVANCE SCORING RESULT")
            print("="*70)
            print(f"Relevance Score: {result.score}/100")
            print(f"\nReasoning:")
            print(f"  {result.reasoning}")
            print(f"\nKey Factors:")
            for factor in result.key_factors:
                print(f"  - {factor}")
            print("="*70)
            
            # Verify score is in valid range
            assert 0 <= result.score <= 100, f"Score out of range: {result.score}"
            
            # For this specific email about power contracts, expect high relevance
            # (But don't be too strict - LLM might score differently)
            assert result.score >= 40, \
                f"Expected moderate-to-high relevance for power contract email, got {result.score}"
            
            print(f"\n[SUCCESS] Test passed! LLM scored document as {result.score}/100")
            
            # Show what was saved to document
            assert mock_doc.relevance_score == result.score
            assert mock_doc.relevance_reasoning == result.reasoning
            print(f"[SUCCESS] Document updated with relevance score")
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            print("\nPossible issues:")
            print("  - Is Ollama running? (ollama serve)")
            print("  - Is llama3.1:8b model available? (ollama pull llama3.1:8b)")
            raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_irrelevant_case_context():
    """Test with same document but DIFFERENT case (should score lower).
    
    Same 43.txt email but case is about something completely different.
    Should demonstrate that relevance depends on case context.
    """
    
    # Load pre-extracted blocks
    blocks_file = Path("tests/helpers/test_data/43_blocks.json")
    with open(blocks_file, 'r') as f:
        blocks_data = json.load(f)
    
    # Create mock storage
    mock_storage = MockStorageClient()
    mock_storage.add_file(
        "cases",
        "999/documents/999/extraction/blocks.json",
        json.dumps(blocks_data).encode('utf-8')
    )
    
    service = RelevanceService(mock_storage)
    
    with patch('services.relevance_service.Document') as MockDocument, \
         patch('services.relevance_service.Case') as MockCase:
        
        mock_doc = AsyncMock()
        mock_doc.id = 999
        mock_doc.classification = "email"
        mock_doc.save = AsyncMock()
        MockDocument.get = AsyncMock(return_value=mock_doc)
        
        # Different case - unrelated topic
        mock_case = AsyncMock()
        mock_case.id = 999
        mock_case.name = "Smith v. Jones - Employment Discrimination"
        mock_case.description = (
            "This case involves allegations of wrongful termination and workplace "
            "harassment at Jones Retail Corporation. Jane Smith alleges she was "
            "discriminated against based on gender and subsequently terminated "
            "in retaliation for filing HR complaints between 2018-2020. The case "
            "centers on company HR policies, internal complaint procedures, and "
            "the termination decision-making process."
        )
        MockCase.get = AsyncMock(return_value=mock_case)
        
        print(f"\n" + "="*70)
        print("TESTING CONTEXT-DEPENDENT RELEVANCE")
        print("="*70)
        print(f"\nSame document (43.txt - power contract email)")
        print(f"Different case: {mock_case.name}")
        print(f"Description: {mock_case.description}")
        print("\nExpecting LOW relevance score (power contracts ≠ employment case)")
        print("-" * 70)
        
        result = await service.score_document_relevance(
            document_id=999,
            case_id=999
        )
        
        print(f"\nRelevance Score: {result.score}/100")
        print(f"Reasoning: {result.reasoning}")
        
        # Should score low for completely unrelated case
        assert result.score <= 30, \
            f"Expected low relevance for unrelated case, got {result.score}"
        
        print(f"\n[SUCCESS] Correctly scored as low relevance ({result.score}/100) for unrelated case!")

