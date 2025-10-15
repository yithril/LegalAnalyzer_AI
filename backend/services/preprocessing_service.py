"""Preprocessing service for file type detection and validation."""
import magic
from fastapi import HTTPException
from core.models.document import Document
from core.constants import SupportedFileType, DocumentStatus
from infrastructure.storage import StorageClient


class PreprocessingService:
    """Service for detecting file types and preprocessing documents.
    
    This service handles files with unknown or missing extensions by peeking
    at the file content to detect the actual type.
    """
    
    # How many bytes to download for file type detection
    # 8KB is usually enough to identify any file type
    PEEK_SIZE_BYTES = 8192
    
    def __init__(self, storage_client: StorageClient):
        """Initialize with storage client dependency."""
        self.storage = storage_client
    
    async def detect_and_update_file_type(self, document_id: int) -> Document:
        """Detect file type by peeking at file content.
        
        This method:
        1. Loads document from database
        2. Downloads first few KB from MinIO (streaming, not full file)
        3. Uses python-magic to detect MIME type
        4. Maps MIME type to our supported file types
        5. Updates document record with detected type
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Document: Updated document record with detected file type
            
        Raises:
            HTTPException: If document not found or type detection fails
        """
        # Step 1: Load document from database
        document = await Document.get_or_none(id=document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        # Update status to show we're detecting type
        document.status = DocumentStatus.DETECTING_TYPE
        await document.save()
        
        try:
            # Step 2: Peek at first few KB (streaming - doesn't download full file!)
            file_sample = await self.storage.download_partial(
                bucket_name=document.minio_bucket,
                object_name=document.minio_key,
                offset=0,
                length=self.PEEK_SIZE_BYTES
            )
            
            # Step 3: Detect MIME type using magic
            detected_type = self._detect_file_type(file_sample, document.filename)
            
            # Step 4: Update document with detected type
            if detected_type == SupportedFileType.UNKNOWN:
                # Could not detect file type - mark for manual review
                document.file_type = detected_type
                document.status = DocumentStatus.FAILED
                document.processing_error = f"Could not detect file type for '{document.filename}'. File will need manual review."
                await document.save()
            else:
                # Successfully detected - ready for extraction
                document.file_type = detected_type
                document.status = DocumentStatus.UPLOADED
                await document.save()
            
            return document
            
        except Exception as e:
            # If detection fails, mark as failed
            document.status = DocumentStatus.FAILED
            document.processing_error = f"File type detection failed: {str(e)}"
            await document.save()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to detect file type: {str(e)}"
            )
    
    def _detect_file_type(self, file_sample: bytes, filename: str) -> SupportedFileType:
        """Detect file type from content using python-magic.
        
        Args:
            file_sample: First few KB of the file
            filename: Original filename (for logging)
            
        Returns:
            SupportedFileType: Detected file type or UNKNOWN if can't detect
        """
        # Get MIME type from file content
        mime_type = magic.from_buffer(file_sample, mime=True)
        
        # Map MIME types to our supported types
        detected_type = self._map_mime_to_file_type(mime_type)
        
        # If we can't figure it out, just leave it as UNKNOWN
        # Don't try to guess - if python-magic doesn't know, we don't know
        return detected_type
    
    def _map_mime_to_file_type(self, mime_type: str) -> SupportedFileType:
        """Map MIME type to our supported file types.
        
        Args:
            mime_type: MIME type from python-magic
            
        Returns:
            SupportedFileType: Mapped file type or UNKNOWN if not recognized
        """
        # Direct MIME type mappings
        mime_mappings = {
            'application/pdf': SupportedFileType.PDF,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': SupportedFileType.DOCX,
            'application/zip': SupportedFileType.DOCX,  # DOCX files are ZIPs, python-magic may detect as generic ZIP
            'application/msword': SupportedFileType.DOC,
            'application/x-cfb': SupportedFileType.DOC,  # Old DOC format (Compound File Binary)
            'text/plain': SupportedFileType.TXT,
            'text/html': SupportedFileType.HTML,
            'message/rfc822': SupportedFileType.HTML,  # Email files (like Enron emails)
        }
        
        if mime_type in mime_mappings:
            return mime_mappings[mime_type]
        
        # If python-magic says it's text/*, treat as plain text
        if mime_type.startswith('text/'):
            return SupportedFileType.TXT
        
        # If we don't recognize it, mark as UNKNOWN
        # Don't guess - let the user/orchestrator handle unknown files
        return SupportedFileType.UNKNOWN

