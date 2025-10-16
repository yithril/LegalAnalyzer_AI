"""Document service for handling document operations."""
import os
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from core.models.document import Document
from core.constants import (
    SupportedFileType, 
    DocumentStatus, 
    MAX_FILE_SIZE_BYTES,
    DOCUMENTS_BUCKET
)
from infrastructure.storage import StorageClient


class DocumentService:
    """Service for document upload and processing operations."""
    
    def __init__(self, storage_client: StorageClient):
        """Initialize with storage client dependency."""
        self.storage = storage_client
    
    async def upload_document(self, file: UploadFile, case_id: int) -> Document:
        """Upload a document, validate it, store in MinIO, and create DB record.
        
        Args:
            file: The uploaded file from FastAPI
            case_id: The ID of the case this document belongs to
            
        Returns:
            Document: The created document record
            
        Raises:
            HTTPException: If validation fails or upload fails
        """
        # Validate that the case exists
        from core.models.case import Case
        case = await Case.get_or_none(id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        # Step 1: Validate the file
        await self._validate_file(file)
        
        # Step 2: Read file contents
        file_contents = await file.read()
        file_size = len(file_contents)
        
        # Step 3: Detect file type from extension
        file_extension = self._get_file_extension(file.filename)
        file_type = self._validate_file_type(file_extension)
        
        # Step 4: Create a unique key for MinIO storage
        # We'll use a simple pattern for now: originals/{filename}
        # Later we can make it more sophisticated like: documents/doc_{id}/original.{ext}
        minio_key = f"originals/{file.filename}"
        
        # Step 5: Ensure bucket exists
        await self.storage.create_bucket(DOCUMENTS_BUCKET)
        
        # Step 6: Upload to MinIO
        try:
            await self.storage.upload(
                bucket_name=DOCUMENTS_BUCKET,
                object_name=minio_key,
                data=file_contents,
                content_type=file.content_type or "application/octet-stream"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to storage: {str(e)}"
            )
        
        # Step 7: Create database record
        document = await Document.create(
            case_id=case_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key=minio_key,
            status=DocumentStatus.UPLOADED
        )
        
        return document
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate file before processing.
        
        Args:
            file: The uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        # Check if file exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        # Note: We need to read the file to check size, then reset the pointer
        file_contents = await file.read()
        file_size = len(file_contents)
        await file.seek(0)  # Reset file pointer for later reading
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if file_size > MAX_FILE_SIZE_BYTES:
            max_size_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename.
        
        Args:
            filename: The name of the file
            
        Returns:
            File extension without the dot (e.g., 'pdf', 'docx')
        """
        _, ext = os.path.splitext(filename)
        return ext.lstrip('.').lower()
    
    def _validate_file_type(self, extension: str) -> SupportedFileType:
        """Validate that file type is supported.
        
        Args:
            extension: File extension without dot (empty string if no extension)
            
        Returns:
            SupportedFileType: The validated file type (or UNKNOWN if needs detection)
            
        Raises:
            HTTPException: If file type is explicitly unsupported
        """
        # No extension or empty extension -> needs preprocessing
        if not extension:
            return SupportedFileType.UNKNOWN
        
        try:
            return SupportedFileType(extension)
        except ValueError:
            # Unknown extension -> needs preprocessing to detect
            return SupportedFileType.UNKNOWN
    
    async def list_documents(
        self,
        case_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Document], int]:
        """List documents for a case with optional filtering.
        
        Args:
            case_id: Case ID to filter by
            status: Optional status filter (e.g., "processing", "completed", "failed")
            limit: Maximum number of documents to return
            offset: Number of documents to skip (for pagination)
            
        Returns:
            Tuple of (documents list, total count)
        """
        # Build query
        query = Document.filter(case_id=case_id)
        
        # Apply status filter if provided
        if status:
            if status == "processing":
                # Show documents currently being processed
                query = query.filter(
                    status__in=[
                        DocumentStatus.EXTRACTING_BLOCKS,
                        DocumentStatus.CLASSIFYING,
                        DocumentStatus.ANALYZING_CONTENT,
                        DocumentStatus.CHUNKING,
                        DocumentStatus.SUMMARIZING
                    ]
                )
            elif status == "incomplete":
                # Show everything not completed or filtered
                query = query.exclude(
                    status__in=[DocumentStatus.COMPLETED, DocumentStatus.FILTERED_OUT]
                )
            else:
                # Direct status match
                query = query.filter(status=status)
        
        # Get total count
        total = await query.count()
        
        # Get documents with pagination
        documents = await query.order_by('-created_at').offset(offset).limit(limit).all()
        
        return documents, total

