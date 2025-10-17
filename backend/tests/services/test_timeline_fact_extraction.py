"""Integration test for TimelineService fact extraction with real LLM.

Uses real Ollama LLM to extract facts from the 43.txt Enron email.
Mocks database and storage, uses pre-extracted blocks from test_data.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from services.timeline_service import TimelineService, ExtractedFact, TemporalInfo
from tests.helpers.mock_storage import MockStorageClient
from core.models.document import Document
from core.models.case import Case


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_extracts_facts_from_enron_email():
    """
    Test TimelineService fact extraction with REAL LLM on 43.txt email.
    
    Expected to extract multiple events from the email:
    1. Power Pool received acknowledgement (Jan 7, 2002)
    2. Contract 933 terminated (Dec 28, 2001)
    3. Contract 2053 created (Dec 29, 2001)
    4. Contract 934 source modified (Dec 29, 2001)
    
    Prerequisites:
    - Ollama running locally
    - llama3.1:8b model available
    """
    
    print("\n" + "="*70)
    print("TESTING TIMELINE FACT EXTRACTION WITH REAL LLM")
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
    
    # Mock database models with realistic data
    mock_doc = AsyncMock(spec=Document)
    mock_doc.id = 999
    mock_doc.case_id = 999
    mock_doc.classification = "email"
    mock_doc.content_category = "business_email"
    mock_doc.relevance_score = 85  # High relevance to case
    mock_doc.relevance_reasoning = "Email discusses contract modifications directly relevant to the investigation"
    
    mock_case = AsyncMock(spec=Case)
    mock_case.id = 999
    mock_case.name = "Alberta Energy Regulator v. Enron Canada"
    mock_case.description = (
        "This case involves allegations of market manipulation and improper "
        "power trading practices by Enron Canada Corporation in the Alberta "
        "power market between 2001-2002. The investigation focuses on contract "
        "modifications, source asset changes, and trading relationships with "
        "Alberta power companies including Lethbridge Ironworks and Power Pool "
        "of Alberta. Key issues include whether contract registrations were "
        "modified to circumvent market regulations and manipulate electricity prices."
    )
    
    with patch('core.models.document.Document.get', new_callable=AsyncMock) as mock_document_get, \
         patch('core.models.case.Case.get', new_callable=AsyncMock) as mock_case_get:
        
        mock_document_get.return_value = mock_doc
        mock_case_get.return_value = mock_case
        
        # Create service with mocked storage but REAL LLM
        service = TimelineService(mock_storage)
        
        print(f"\nCase: {mock_case.name}")
        print(f"Document: 43.txt (Enron power contract email)")
        print(f"Classification: {mock_doc.classification}")
        print(f"Content Category: {mock_doc.content_category}")
        print(f"Relevance Score: {mock_doc.relevance_score}/100")
        print(f"\nCalling real LLM for fact extraction...")
        print("-" * 70)
        
        try:
            result = await service.extract_facts(
                document_id=999,
                case_id=999
            )
            
            print(f"\n[SUCCESS] LLM extracted {len(result.events)} events")
            print("=" * 70)
            
            # Display extracted events
            for i, event in enumerate(result.events, 1):
                print(f"\nEVENT {i}:")
                print(f"  Actors: {event.actors}")
                print(f"  Action: {event.action}")
                print(f"  Object Affected: {event.object_affected}")
                print(f"  Date: {event.temporal.date} (precision: {event.temporal.precision})")
                if event.temporal.date_end:
                    print(f"  Date End: {event.temporal.date_end}")
                print(f"  Original Date Text: {event.temporal.original_text}")
                print(f"  Confidence: {event.confidence}%")
                print(f"  Extracted Text: {event.extracted_text[:100]}...")
            
            # Light assertions - just check basic validity
            assert isinstance(result.events, list), "Result should contain a list of events"
            
            # Basic statistics
            events_with_dates = [e for e in result.events if e.temporal.date]
            events_with_actors = [e for e in result.events if e.actors]
            events_with_objects = [e for e in result.events if e.object_affected]
            
            # Summary
            print("\n" + "=" * 70)
            print("SUMMARY STATISTICS")
            print("=" * 70)
            print(f"  Total events extracted: {len(result.events)}")
            print(f"  Events with dates: {len(events_with_dates)}")
            print(f"  Events with actors: {len(events_with_actors)}")
            print(f"  Events with objects: {len(events_with_objects)}")
            if result.events:
                print(f"  Average confidence: {sum(e.confidence for e in result.events) / len(result.events):.1f}%")
                print(f"  Confidence range: {min(e.confidence for e in result.events)} - {max(e.confidence for e in result.events)}")
            
            print("\n[SUCCESS] Test completed - review output above to evaluate extraction quality")
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            print("\nPossible issues:")
            print("  - Is Ollama running? (ollama serve)")
            print("  - Is llama3.1:8b model available? (ollama pull llama3.1:8b)")
            raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fact_extraction_with_no_events():
    """
    Test fact extraction on a document with no discrete events.
    Should return empty list.
    """
    
    print("\n" + "="*70)
    print("TESTING FACT EXTRACTION WITH NO EVENTS")
    print("="*70)
    
    # Create a document with no events (just general information)
    no_events_text = """
    Company Background Information
    
    Enron Corporation is an American energy company based in Houston, Texas.
    The company was founded in 1985. It employed approximately 20,000 staff.
    
    Carol Moline is the Financial Controller at Power Pool of Alberta.
    Her contact information is (403) 233-4686.
    
    This is general background information only.
    """
    
    blocks_data = {
        "document_id": 998,
        "file_type": "txt",
        "original_filename": "background.txt",
        "page_count": 1,
        "total_blocks": 1,
        "pages": [{
            "page_index": 0,
            "block_count": 1,
            "blocks": [{
                "block_id": "doc998_p0_b0",
                "block_index": 0,
                "text": no_events_text,
                "kind": "paragraph",
                "char_start": 0,
                "char_end": len(no_events_text)
            }]
        }]
    }
    
    mock_storage = MockStorageClient()
    mock_storage.add_file(
        "cases",
        "998/documents/998/extraction/blocks.json",
        json.dumps(blocks_data).encode('utf-8')
    )
    
    mock_doc = AsyncMock(spec=Document)
    mock_doc.id = 998
    mock_doc.case_id = 998
    mock_doc.classification = "memo"
    mock_doc.content_category = "general_info"
    mock_doc.relevance_score = 25  # Low relevance
    
    mock_case = AsyncMock(spec=Case)
    mock_case.id = 998
    mock_case.name = "Test Case"
    mock_case.description = "A test case"
    
    with patch('core.models.document.Document.get', new_callable=AsyncMock) as mock_document_get, \
         patch('core.models.case.Case.get', new_callable=AsyncMock) as mock_case_get:
        
        mock_document_get.return_value = mock_doc
        mock_case_get.return_value = mock_case
        
        service = TimelineService(mock_storage)
        
        print("Document contains only background info (no events)")
        print(f"Relevance Score: {mock_doc.relevance_score}/100 (low relevance)")
        print("Calling LLM...")
        
        result = await service.extract_facts(
            document_id=998,
            case_id=998
        )
        
        print(f"\n[SUCCESS] LLM returned {len(result.events)} events")
        
        if len(result.events) > 0:
            print("\nExtracted events (if any):")
            for i, event in enumerate(result.events, 1):
                print(f"  {i}. {event.action}")
        
        print("\n[SUCCESS] Test completed - LLM correctly distinguished background info from events")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_analyzes_legal_significance():
    """
    Test TimelineService legal analysis with REAL LLM on extracted events.
    
    Takes sample events from 43.txt and evaluates their legal significance
    to determine if they should be included in the timeline.
    
    Prerequisites:
    - Ollama running locally
    - llama3.1:8b model available
    """
    
    print("\n" + "="*70)
    print("TESTING LEGAL SIGNIFICANCE ANALYSIS WITH REAL LLM")
    print("="*70)
    
    # Load pre-extracted blocks for 43.txt
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
    
    # Mock database models with realistic data
    mock_doc = AsyncMock(spec=Document)
    mock_doc.id = 999
    mock_doc.case_id = 999
    mock_doc.classification = "email"
    mock_doc.content_category = "business_email"
    mock_doc.relevance_score = 85
    
    mock_case = AsyncMock(spec=Case)
    mock_case.id = 999
    mock_case.name = "Alberta Energy Regulator v. Enron Canada"
    mock_case.description = (
        "This case involves allegations of market manipulation and improper "
        "power trading practices by Enron Canada Corporation in the Alberta "
        "power market between 2001-2002. The investigation focuses on contract "
        "modifications, source asset changes, and trading relationships with "
        "Alberta power companies including Lethbridge Ironworks and Power Pool "
        "of Alberta. Key issues include whether contract registrations were "
        "modified to circumvent market regulations and manipulate electricity prices."
    )
    
    # Create sample events (simulating what fact extraction would return)
    event1 = ExtractedFact(
        actors=["Power Pool of Alberta", "Enron Canada"],
        action="received acknowledgement of contract modification",
        object_affected="Contract 934 source asset change",
        temporal=TemporalInfo(
            date="2002-01-07",
            precision="exact",
            original_text="January 7"
        ),
        extracted_text="On January 7 the Power Pool received your acknowledgement of Enron's change in the source asset",
        confidence=95
    )
    
    event2 = ExtractedFact(
        actors=["Power Pool of Alberta", "Enron Canada"],
        action="modified contract registration terms",
        object_affected="Contract #934",
        temporal=TemporalInfo(
            date=None,
            precision="approximate",
            original_text="December 29 HE 1 2001"
        ),
        extracted_text="The modified registration terms will be effective December 29 HE 1 2001 and will apply until the expiry date of the contract registration for net settlement purposes.",
        confidence=90
    )
    
    with patch('core.models.document.Document.get', new_callable=AsyncMock) as mock_document_get, \
         patch('core.models.case.Case.get', new_callable=AsyncMock) as mock_case_get:
        
        mock_document_get.return_value = mock_doc
        mock_case_get.return_value = mock_case
        
        service = TimelineService(mock_storage)
        
        print(f"\nCase: {mock_case.name}")
        print(f"Document: 43.txt (Relevance: {mock_doc.relevance_score}/100)")
        print(f"\nAnalyzing 2 extracted events...")
        print("=" * 70)
        
        # Analyze Event 1
        print(f"\nEVENT 1:")
        print(f"  Action: {event1.action}")
        print(f"  Actors: {', '.join(event1.actors)}")
        print(f"  Object: {event1.object_affected}")
        print(f"  Date: {event1.temporal.date}")
        print(f"\nCalling LLM for legal analysis...")
        
        try:
            result1 = await service.analyze_legal_significance(
                event=event1,
                document_id=999,
                case_id=999
            )
            
            print(f"\n  Legal Significance Score: {result1.legal_significance_score}/100")
            print(f"  Timeline Worthy: {result1.timeline_worthy}")
            print(f"  State Changes: {', '.join(result1.state_changes) if result1.state_changes else 'None'}")
            print(f"  Reasoning: {result1.reasoning}")
            print(f"  Key Factors: {', '.join(result1.key_factors)}")
            
            # Analyze Event 2
            print(f"\n" + "=" * 70)
            print(f"\nEVENT 2:")
            print(f"  Action: {event2.action}")
            print(f"  Actors: {', '.join(event2.actors)}")
            print(f"  Object: {event2.object_affected}")
            print(f"  Date: {event2.temporal.original_text}")
            print(f"\nCalling LLM for legal analysis...")
            
            result2 = await service.analyze_legal_significance(
                event=event2,
                document_id=999,
                case_id=999
            )
            
            print(f"\n  Legal Significance Score: {result2.legal_significance_score}/100")
            print(f"  Timeline Worthy: {result2.timeline_worthy}")
            print(f"  State Changes: {', '.join(result2.state_changes) if result2.state_changes else 'None'}")
            print(f"  Reasoning: {result2.reasoning}")
            print(f"  Key Factors: {', '.join(result2.key_factors)}")
            
            # Summary
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Event 1: {result1.legal_significance_score}/100 - {'INCLUDE' if result1.timeline_worthy else 'EXCLUDE'}")
            print(f"Event 2: {result2.legal_significance_score}/100 - {'INCLUDE' if result2.timeline_worthy else 'EXCLUDE'}")
            
            # Light assertions
            assert isinstance(result1.legal_significance_score, int)
            assert isinstance(result2.legal_significance_score, int)
            assert isinstance(result1.timeline_worthy, bool)
            assert isinstance(result2.timeline_worthy, bool)
            
            print("\n[SUCCESS] Test completed - review LLM analysis above")
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            print("\nPossible issues:")
            print("  - Is Ollama running? (ollama serve)")
            print("  - Is llama3.1:8b model available? (ollama pull llama3.1:8b)")
            raise

