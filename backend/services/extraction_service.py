"""Extraction service for document text and layout extraction."""
import json
from infrastructure.storage import StorageClient
from core.models.document import Document
from core.constants import DocumentStatus
from services.text_extraction.extraction_strategy_factory import ExtractionStrategyFactory
from services.models.extraction_models import ExtractedDocument


class ExtractionService:
    """Service for extracting text and layout from documents.
    
    Handles:
    - Loading file from S3
    - Running extraction
    - Saving blocks.json to S3
    - Updating document status
    """
    
    def __init__(self, storage_client: StorageClient):
        """Initialize extraction service.
        
        Args:
            storage_client: S3 storage client
        """
        self.storage = storage_client
        self.extractor = ExtractionStrategyFactory()
    
    async def extract_document(self, document_id: int, case_id: int) -> ExtractedDocument:
        """Extract text and layout from document.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            ExtractedDocument with pages and blocks
        """
        # Load document
        document = await Document.get(id=document_id)
        
        # Update status
        document.status = DocumentStatus.EXTRACTING_BLOCKS
        await document.save()
        
        print(f"[Extraction] Extracting document {document_id}...")
        
        try:
            # Download file from S3
            file_data = await self.storage.download(
                bucket_name=document.minio_bucket,
                object_name=document.minio_key
            )
            
            # Extract
            extracted = await self.extractor.extract(
                file_data=file_data,
                filename=document.filename,
                document_id=document_id
            )
            
            # Save blocks.json to S3
            extraction_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
            extraction_json = extracted.model_dump_json(indent=2)
            
            await self.storage.upload(
                bucket_name="cases",
                object_name=extraction_key,
                data=extraction_json.encode('utf-8')
            )
            
            print(f"[Extraction] Complete - {extracted.page_count} pages, {extracted.total_blocks} blocks")
            
            return extracted
            
        except Exception as e:
            # Let orchestrator handle the failure
            print(f"[Extraction] Failed: {e}")
            raise

