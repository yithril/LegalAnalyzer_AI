"""Data Transfer Objects for document operations."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentUploadResponse(BaseModel):
    """Response returned after successful document upload."""
    
    id: int
    case_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    minio_bucket: str
    minio_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows converting from Tortoise models


class DocumentDetailResponse(BaseModel):
    """Detailed document information."""
    
    id: int
    case_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    classification: Optional[str] = None
    content_category: Optional[str] = None
    has_summary: bool = False
    minio_bucket: str
    minio_key: str
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response for document list queries."""
    
    total: int
    documents: list[DocumentDetailResponse]
    
    class Config:
        from_attributes = True

