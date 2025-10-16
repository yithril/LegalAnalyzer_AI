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
from services.chunking.chunking_service import ChunkingService
from services.summarization.summarization_service import SummarizationService


class DocumentProcessor:
    """Orchestrates complete document processing pipeline.
    
    Pipeline:
    1. Extract → blocks.json to S3
    2. Classify → Document.classification
    3. Analyze → Filter spam/junk or continue
    4. Chunk → chunks.json + Pinecone vectors
    5. Summarize → Elasticsearch
    6. Complete → Mark COMPLETED
    
    Error Handling:
    - Required steps (extract, chunk): Failure → FAILED
    - Optional steps (classify, summarize): Failure → Log + continue
    - Filter step (analyze): should_process=False → FILTERED_OUT
    """
    
    def __init__(
        self,
        extraction_service: ExtractionService,
        classifier: ContentClassifier,
        analyzer: ContentAnalysisService,
        chunker: ChunkingService,
        summarizer: SummarizationService
    ):
        """Initialize document processor with services.
        
        Args:
            extraction_service: Extraction service
            classifier: Content classifier
            analyzer: Content analysis service
            chunker: Chunking service
            summarizer: Summarization service
        """
        self.extraction_service = extraction_service
        self.classifier = classifier
        self.analyzer = analyzer
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
            should_continue = await self._step_analyze(document_id, case_id, classification)
            if not should_continue:
                print(f"[Pipeline] Document {document_id} filtered out - stopping")
                return
            
            # Step 4: Chunk (REQUIRED)
            await self._step_chunk(document_id, case_id, classification)
            
            # Step 5: Summarize (OPTIONAL - continue if fails)
            await self._step_summarize(document_id, case_id)
            
            # Step 6: Mark complete
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
    
    async def _step_analyze(self, document_id: int, case_id: int, classification: str) -> bool:
        """Step 3: Analyze content (spam detection, etc.)
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            
        Returns:
            True if should continue processing, False if filtered out
        """
        try:
            print(f"[Step 3] Analyzing content...")
            
            # Analyze
            decision = await self.analyzer.analyze_document(document_id, case_id, classification)
            
            if not decision.should_process:
                print(f"[Step 3] Document filtered out - {decision.reasoning}")
                return False
            
            print(f"[Step 3] Content analysis complete - proceeding")
            return True
            
        except Exception as e:
            await self._handle_failure(document_id, "content_analysis", str(e))
            raise
    
    async def _step_chunk(self, document_id: int, case_id: int, classification: str) -> None:
        """Step 4: Create semantic chunks.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
        """
        try:
            print(f"[Step 4] Creating chunks...")
            
            # Chunk (this also stores in Pinecone)
            result = await self.chunker.chunk_document(
                document_id=document_id,
                case_id=case_id,
                classification=classification
            )
            
            print(f"[Step 4] Chunking complete - {result.total_chunks} chunks created")
            
        except Exception as e:
            await self._handle_failure(document_id, "chunking", str(e))
            raise
    
    async def _step_summarize(self, document_id: int, case_id: int) -> None:
        """Step 5: Generate summaries.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        document = await Document.get(id=document_id)
        
        try:
            print(f"[Step 5] Generating summaries...")
            document.status = DocumentStatus.SUMMARIZING
            await document.save()
            
            # Summarize (stores in Elasticsearch)
            executive_summary = await self.summarizer.summarize_document(
                document_id=document_id,
                case_id=case_id
            )
            
            print(f"[Step 5] Summarization complete - {len(executive_summary)} chars")
            
        except Exception as e:
            # Summarization is optional - log and continue
            print(f"[Step 5] Summarization failed: {e}")
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
    chunker = ChunkingService(storage_client, pinecone_client)
    summarizer = SummarizationService(storage_client, elasticsearch_client)
    
    # Create orchestrator with services
    return DocumentProcessor(
        extraction_service=extraction_service,
        classifier=classifier,
        analyzer=analyzer,
        chunker=chunker,
        summarizer=summarizer
    )

