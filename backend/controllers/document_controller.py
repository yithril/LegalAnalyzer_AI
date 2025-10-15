"""Document controller for HTTP endpoints."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from dtos.document_dto import DocumentUploadResponse
from services.document_service import DocumentService
from infrastructure.storage import storage_client


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency injection for DocumentService."""
    return DocumentService(storage_client)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """Upload a document for processing.
    
    This endpoint:
    1. Validates that the case exists
    2. Validates the file (size, type, content)
    3. Uploads it to MinIO storage
    4. Creates a database record with status 'uploaded'
    
    Args:
        case_id: The ID of the case this document belongs to
        file: The file to upload (PDF, DOCX, DOC, or TXT)
        
    Returns:
        DocumentUploadResponse: Details of the uploaded document
        
    Raises:
        HTTPException 404: If case not found
        HTTPException 400: If file validation fails
        HTTPException 500: If upload or database operation fails
    """
    document = await service.upload_document(file, case_id)
    
    return DocumentUploadResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(document_id: int):
    """Get document details by ID.
    
    Args:
        document_id: The ID of the document
        
    Returns:
        DocumentUploadResponse: Document details
        
    Raises:
        HTTPException 404: If document not found
    """
    from core.models.document import Document
    
    document = await Document.get_or_none(id=document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    return DocumentUploadResponse.model_validate(document)

