"""Document processing orchestrator - manages complete pipeline."""
import json
from datetime import datetime
from core.models.document import Document
from core.constants import DocumentStatus
from infrastructure.storage import storage_client
from infrastructure.pinecone_client import pinecone_client
from infrastructure.elasticsearch_client import elasticsearch_client
from services.extraction_service import ExtractionService
from services.content_analysis.content_classifier import ContentClassifier
from services.content_analysis_service import ContentAnalysisService
from services.relevance_service import RelevanceService
from services.document_indexing_service import DocumentIndexingService
from services.chunking.chunking_service import ChunkingService
from services.summarization.summarization_service import SummarizationService


class DocumentProcessor:
    """Orchestrates complete document processing pipeline.
    
    Pipeline:
    1. Extract → blocks.json to S3
    2. Classify → Document.classification
    3. Analyze → Filter spam/junk or continue
    4. Score Relevance → 0-100 (how important to case)
    5. Index → full_text + blocks to Elasticsearch
    6. Chunk → chunks.json + Pinecone vectors
    7. Summarize → Update Elasticsearch with summary
    8. Complete → Mark COMPLETED
    
    Error Handling:
    - Required steps (extract, chunk): Failure → FAILED
    - Optional steps (classify, relevance, index, summarize): Failure → Log + continue
    - Filter step (analyze): should_process=False → FILTERED_OUT
    """
    
    def __init__(
        self,
        extraction_service: ExtractionService,
        classifier: ContentClassifier,
        analyzer: ContentAnalysisService,
        relevance_service: RelevanceService,
        indexer: DocumentIndexingService,
        chunker: ChunkingService,
        summarizer: SummarizationService
    ):
        """Initialize document processor with services.
        
        Args:
            extraction_service: Extraction service
            classifier: Content classifier
            analyzer: Content analysis service
            relevance_service: Relevance scoring service
            indexer: Document indexing service
            chunker: Chunking service
            summarizer: Summarization service
        """
        self.extraction_service = extraction_service
        self.classifier = classifier
        self.analyzer = analyzer
        self.relevance_service = relevance_service
        self.indexer = indexer
        self.chunker = chunker
        self.summarizer = summarizer
    
    async def process_document(self, document_id: int, case_id: int) -> None:
        """Process document through complete pipeline.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        print(f"\n{'='*70}")
        print(f"[Pipeline] Starting processing for document {document_id}")
        print(f"{'='*70}\n")
        
        try:
            # Step 1: Extract (REQUIRED)
            await self._step_extract(document_id, case_id)
            
            # Step 2: Classify (OPTIONAL - continue if fails)
            classification = await self._step_classify(document_id, case_id)
            
            # Step 3: Analyze (REQUIRED for filtering)
            should_continue, content_category = await self._step_analyze(document_id, case_id, classification)
            if not should_continue:
                document = await Document.get(id=document_id)
                document.status = DocumentStatus.FILTERED_OUT
                await document.save()
                print(f"[Pipeline] Document {document_id} filtered out - stopping")
                return
            
            # Step 4: Score Relevance (OPTIONAL - determines processing depth)
            await self._step_score_relevance(document_id, case_id)
            
            # Step 5: Index in Elasticsearch (OPTIONAL - makes document searchable)
            await self._step_index(document_id, case_id)
            
            # Step 6: Chunk (REQUIRED)
            await self._step_chunk(document_id, case_id, classification, content_category)
            
            # Step 7: Summarize (OPTIONAL - continue if fails)
            await self._step_summarize(document_id, case_id)
            
            # Step 8: Mark complete
            await self._mark_complete(document_id)
            
            print(f"\n{'='*70}")
            print(f"[Pipeline] Document {document_id} processing COMPLETE!")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n[Pipeline] Processing failed for document {document_id}: {e}")
            raise
    
    async def _step_extract(self, document_id: int, case_id: int) -> None:
        """Step 1: Extract blocks from document.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        try:
            print(f"[Step 1] Extracting blocks...")
            
            # Extraction service handles everything
            await self.extraction_service.extract_document(document_id, case_id)
            
        except Exception as e:
            await self._handle_failure(document_id, "extraction", str(e))
            raise
    
    async def _step_classify(self, document_id: int, case_id: int) -> str:
        """Step 2: Classify document type.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            Classification string
        """
        document = await Document.get(id=document_id)
        
        try:
            print(f"[Step 2] Classifying document...")
            document.status = DocumentStatus.CLASSIFYING
            await document.save()
            
            # Classify
            classification = await self.classifier.classify(document_id, case_id)
            
            # Save to document
            document.classification = classification
            await document.save()
            
            print(f"[Step 2] Classification complete - '{classification}'")
            return classification
            
        except Exception as e:
            # Classification is optional - log and continue
            print(f"[Step 2] Classification failed: {e}")
            document.classification = "unknown"
            await document.save()
            return "unknown"
    
    async def _step_analyze(self, document_id: int, case_id: int, classification: str) -> tuple[bool, str]:
        """Step 3: Analyze content (spam detection, etc.)
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            
        Returns:
            Tuple of (should_continue, content_category)
        """
        document = await Document.get(id=document_id)
        
        try:
            print(f"[Step 3] Analyzing content...")
            
            # Analyze
            decision = await self.analyzer.analyze_document(document_id, case_id, classification)
            
            # Save content category to document
            document.content_category = decision.category.value
            document.filter_confidence = decision.confidence
            document.filter_reasoning = decision.reasoning
            await document.save()
            
            if not decision.should_process:
                print(f"[Step 3] Document filtered out - {decision.reasoning}")
                return (False, decision.category.value)
            
            print(f"[Step 3] Content analysis complete - {decision.category.value}")
            return (True, decision.category.value)
            
        except Exception as e:
            await self._handle_failure(document_id, "content_analysis", str(e))
            raise
    
    async def _step_score_relevance(self, document_id: int, case_id: int) -> None:
        """Step 4: Score document relevance to the case (0-100).
        
        Determines how important this document is to the case.
        Only runs on documents that passed content analysis.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        try:
            print(f"[Step 4] Scoring document relevance...")
            
            # Score relevance
            result = await self.relevance_service.score_document_relevance(
                document_id=document_id,
                case_id=case_id
            )
            
            print(f"[Step 4] Relevance score: {result.score}/100")
            
        except Exception as e:
            # Relevance scoring is optional - log and continue
            print(f"[Step 4] Relevance scoring failed: {e}")
            # Document continues processing with null relevance score
    
    async def _step_index(self, document_id: int, case_id: int) -> None:
        """Step 5: Index document content in Elasticsearch.
        
        Makes document searchable via keyword search.
        Loads blocks, builds full_text, indexes everything.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        try:
            print(f"[Step 5] Indexing document content in Elasticsearch...")
            
            # Index full_text and blocks
            await self.indexer.index_document_content(
                document_id=document_id,
                case_id=case_id
            )
            
            print(f"[Step 5] Document indexed - now searchable via keyword search")
            
        except Exception as e:
            # Indexing is optional - log and continue
            print(f"[Step 5] Elasticsearch indexing failed: {e}")
            # Don't fail pipeline - document can still be processed
    
    async def _step_chunk(self, document_id: int, case_id: int, classification: str, content_category: str = None) -> None:
        """Step 6: Create semantic chunks.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            content_category: Content category from analysis
        """
        try:
            print(f"[Step 6] Creating chunks...")
            
            # Chunk (this also stores in Pinecone)
            result = await self.chunker.chunk_document(
                document_id=document_id,
                case_id=case_id,
                classification=classification,
                content_category=content_category
            )
            
            print(f"[Step 6] Chunking complete - {result.total_chunks} chunks created")
            
        except Exception as e:
            await self._handle_failure(document_id, "chunking", str(e))
            raise
    
    async def _step_summarize(self, document_id: int, case_id: int) -> None:
        """Step 7: Generate summaries.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        document = await Document.get(id=document_id)
        
        try:
            print(f"[Step 7] Generating summaries...")
            document.status = DocumentStatus.SUMMARIZING
            await document.save()
            
            # Summarize (stores in Elasticsearch)
            executive_summary = await self.summarizer.summarize_document(
                document_id=document_id,
                case_id=case_id
            )
            
            print(f"[Step 7] Summarization complete - {len(executive_summary)} chars")
            
        except Exception as e:
            # Summarization is optional - log and continue
            print(f"[Step 7] Summarization failed: {e}")
            document.has_summary = False
            await document.save()
    
    async def _mark_complete(self, document_id: int) -> None:
        """Mark document as fully processed.
        
        Args:
            document_id: Document ID
        """
        document = await Document.get(id=document_id)
        document.status = DocumentStatus.COMPLETED
        document.processing_error = None  # Clear any old errors
        await document.save()
        
        print(f"[Pipeline] Document {document_id} marked as COMPLETED")
    
    async def _handle_failure(self, document_id: int, step: str, error: str) -> None:
        """Handle processing failure.
        
        Args:
            document_id: Document ID
            step: Which step failed
            error: Error message
        """
        document = await Document.get(id=document_id)
        
        error_data = {
            "step": step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        document.status = DocumentStatus.FAILED
        document.processing_error = json.dumps(error_data)
        await document.save()
        
        print(f"[Pipeline] Document {document_id} marked as FAILED at step '{step}'")
        print(f"[Pipeline] Error: {error}")


# Dependency injection factory
def get_document_processor() -> DocumentProcessor:
    """Create DocumentProcessor with all dependencies injected.
    
    Uses singleton infrastructure clients from infrastructure package.
    
    Returns:
        DocumentProcessor instance
    """
    # Initialize services with infrastructure clients
    extraction_service = ExtractionService(storage_client)
    classifier = ContentClassifier(storage_client)
    analyzer = ContentAnalysisService(storage_client)
    relevance_service = RelevanceService(storage_client)
    indexer = DocumentIndexingService(storage_client, elasticsearch_client)
    chunker = ChunkingService(storage_client, pinecone_client)
    summarizer = SummarizationService(storage_client, elasticsearch_client)
    
    # Create orchestrator with services
    return DocumentProcessor(
        extraction_service=extraction_service,
        classifier=classifier,
        analyzer=analyzer,
        relevance_service=relevance_service,
        indexer=indexer,
        chunker=chunker,
        summarizer=summarizer
    )

