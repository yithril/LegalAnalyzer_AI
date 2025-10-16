"""Test document processing orchestrator."""
import pytest
from pathlib import Path
from tests.helpers import MockStorageClient, MockPineconeClient, MockElasticsearchClient
from orchestrators.document_processor import DocumentProcessor
from services.extraction_service import ExtractionService
from services.content_analysis.content_classifier import ContentClassifier
from services.content_analysis_service import ContentAnalysisService
from services.chunking.chunking_service import ChunkingService
from services.summarization.summarization_service import SummarizationService


@pytest.mark.asyncio
async def test_document_processor_initialization():
    """Test document processor initializes with all services.
    
    This verifies the dependency injection pattern and that
    all services are properly wired together.
    """
    
    print(f"\n{'='*70}")
    print("Testing Document Processor - Initialization")
    print(f"{'='*70}")
    
    # Setup mocks
    mock_storage = MockStorageClient()
    mock_pinecone = MockPineconeClient()
    mock_es = MockElasticsearchClient()
    
    await mock_pinecone.init()
    await mock_es.init()
    
    print("\n[SETUP]")
    print(f"  Mock storage: Initialized")
    print(f"  Mock Pinecone: Initialized")
    print(f"  Mock Elasticsearch: Initialized")
    
    # Create services (following DI pattern)
    print("\n[CREATING SERVICES]")
    extraction_service = ExtractionService(mock_storage)
    classifier = ContentClassifier(mock_storage)
    analyzer = ContentAnalysisService(mock_storage)
    chunker = ChunkingService(mock_storage, mock_pinecone)
    summarizer = SummarizationService(mock_storage, mock_es)
    
    print(f"  ExtractionService: Created")
    print(f"  ContentClassifier: Created")
    print(f"  ContentAnalysisService: Created")
    print(f"  ChunkingService: Created")
    print(f"  SummarizationService: Created")
    
    # Create orchestrator
    print("\n[CREATING ORCHESTRATOR]")
    processor = DocumentProcessor(
        extraction_service=extraction_service,
        classifier=classifier,
        analyzer=analyzer,
        chunker=chunker,
        summarizer=summarizer
    )
    
    print(f"  DocumentProcessor: Created")
    
    # Verify all services are wired
    print("\n[VERIFICATION]")
    assert processor.extraction_service is not None, "Extraction service should be set"
    assert processor.classifier is not None, "Classifier should be set"
    assert processor.analyzer is not None, "Analyzer should be set"
    assert processor.chunker is not None, "Chunker should be set"
    assert processor.summarizer is not None, "Summarizer should be set"
    
    print(f"  All services properly injected")
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Orchestrator initialized correctly")
    print(f"{'='*70}\n")
    print(f"[INFO] Full end-to-end pipeline test requires:")
    print(f"  - Database connection")
    print(f"  - Actual Document records")
    print(f"  - Integration test environment")
    print(f"\n  Individual steps are tested in their respective service tests.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

