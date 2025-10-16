"""Content analysis service to filter out unwanted documents.

Runs AFTER extraction and classification to determine if document should be processed.
Uses classification result to route to appropriate analyzer (email → EmailAnalyzer, etc.)
"""
import json
from infrastructure.storage import StorageClient
from core.models.document import Document
from core.constants import DocumentStatus
from services.models.extraction_models import ExtractedDocument
from services.content_analysis.email_analyzer import EmailAnalyzer
from services.content_analysis.default_analyzer import DefaultAnalyzer
from services.content_analysis.base_analyzer import FilterDecision


class ContentAnalysisService:
    """Analyzes documents to determine if they should be processed or filtered out.
    
    Workflow:
    1. Load extraction (blocks.json)
    2. Use classification to pick analyzer
    3. Create sample from blocks
    4. Run analyzer to get FilterDecision
    5. Update document status (FILTERED_OUT or continue)
    """
    
    def __init__(self, storage_client: StorageClient):
        """Initialize with storage client."""
        self.storage = storage_client
        self.email_analyzer = EmailAnalyzer()
        self.default_analyzer = DefaultAnalyzer()
    
    async def analyze_document(self, document_id: int, case_id: int, classification: str) -> FilterDecision:
        """Analyze document to determine if it should be processed.
        
        Args:
            document_id: Document ID
            case_id: Case ID (for S3 path)
            classification: Classification result (e.g., "email", "contract")
            
        Returns:
            FilterDecision with should_process flag
        """
        # Load document record
        document = await Document.get(id=document_id)
        document.status = DocumentStatus.ANALYZING_CONTENT
        await document.save()
        
        try:
            # Load extraction from S3
            extraction_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
            extraction_bytes = await self.storage.download(
                bucket_name="cases",
                object_name=extraction_key
            )
            extraction_data = json.loads(extraction_bytes.decode('utf-8'))
            extracted = ExtractedDocument(**extraction_data)
            
            # Create content sample from blocks
            content_sample = self._create_sample_from_blocks(extracted)
            
            # Select analyzer based on classification
            analyzer = self._select_analyzer(classification, content_sample)
            
            # Build metadata
            metadata = {
                "document_id": document_id,
                "filename": document.filename,
                "file_type": document.file_type,
                "classification": classification,
                "page_count": extracted.page_count,
                "total_blocks": extracted.total_blocks
            }
            
            # Run analysis
            decision = await analyzer.analyze(content_sample, metadata)
            
            # Update document with decision
            document.content_category = decision.category.value
            document.filter_confidence = decision.confidence
            document.filter_reasoning = decision.reasoning
            
            if not decision.should_process:
                # Mark for deletion
                document.status = DocumentStatus.FILTERED_OUT
            else:
                # Ready for next stage (chunking)
                document.status = DocumentStatus.COMPLETED  # Or CHUNKING when that exists
            
            await document.save()
            
            return decision
            
        except Exception as e:
            # If analysis fails, log error but don't block processing
            document.status = DocumentStatus.FAILED
            document.processing_error = f"Content analysis failed: {str(e)}"
            await document.save()
            raise
    
    def _select_analyzer(self, classification: str, content_preview: str) -> object:
        """Select the appropriate analyzer based on classification.
        
        Args:
            classification: Document classification (e.g., "email", "contract")
            content_preview: First bit of content for analyzer.can_analyze()
            
        Returns:
            Appropriate analyzer instance
        """
        # Route based on classification
        classification_lower = classification.lower()
        
        # Email-related classifications → EmailAnalyzer
        if any(term in classification_lower for term in ['email', 'correspondence', 'message']):
            return self.email_analyzer
        
        # Everything else → DefaultAnalyzer (minimal filtering)
        # DefaultAnalyzer only filters obvious junk (empty/corrupted)
        return self.default_analyzer
    
    def _create_sample_from_blocks(self, extracted: ExtractedDocument, max_chars: int = 10000) -> str:
        """Create a content sample from extracted blocks for analysis.
        
        Similar to classification sampling but simpler - just get text.
        
        Args:
            extracted: Extracted document with blocks
            max_chars: Maximum characters to include
            
        Returns:
            Text sample for analysis
        """
        parts = []
        char_count = 0
        
        # Sample from first few pages
        for page in extracted.pages[:3]:  # First 3 pages should be enough
            for block in page.blocks:
                # Skip non-text blocks
                if block.kind in ['image', 'header', 'footer']:
                    continue
                
                if not block.text or not block.text.strip():
                    continue
                
                # Add block text
                parts.append(block.text)
                char_count += len(block.text)
                
                if char_count >= max_chars:
                    break
            
            if char_count >= max_chars:
                break
        
        return "\n\n".join(parts)


# Convenience function
async def analyze_document(document_id: int, case_id: int, classification: str, storage_client: StorageClient) -> FilterDecision:
    """Convenience function to analyze a document.
    
    Args:
        document_id: Document ID
        case_id: Case ID
        classification: Classification result
        storage_client: Storage client instance
        
    Returns:
        FilterDecision
    """
    service = ContentAnalysisService(storage_client)
    return await service.analyze_document(document_id, case_id, classification)

