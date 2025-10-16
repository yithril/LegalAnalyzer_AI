"""Document controller for HTTP endpoints."""
from typing import Optional, Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from dtos.document_dto import DocumentUploadResponse, DocumentDetailResponse, DocumentListResponse
from services.document_service import DocumentService
from infrastructure.storage import storage_client
from orchestrators import get_document_processor
from core.dependencies import require_auth


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency injection for DocumentService."""
    return DocumentService(storage_client)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    case_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    user: Annotated[dict, Depends(require_auth)] = None
) -> DocumentUploadResponse:
    """Upload a document for processing.
    
    This endpoint:
    1. Validates that the case exists
    2. Validates the file (size, type, content)
    3. Uploads it to MinIO storage
    4. Creates a database record with status 'uploaded'
    5. Triggers background processing pipeline
    
    Args:
        case_id: The ID of the case this document belongs to
        file: The file to upload (PDF, DOCX, DOC, or TXT)
        background_tasks: FastAPI background tasks
        
    Returns:
        DocumentUploadResponse: Details of the uploaded document
        
    Raises:
        HTTPException 404: If case not found
        HTTPException 400: If file validation fails
        HTTPException 500: If upload or database operation fails
    """
    # Upload file and create document record
    document = await service.upload_document(file, case_id)
    
    # Trigger processing pipeline in background
    processor = get_document_processor()
    background_tasks.add_task(
        processor.process_document,
        document_id=document.id,
        case_id=case_id
    )
    
    return DocumentUploadResponse.model_validate(document)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    case_id: int = Query(..., description="Case ID to filter documents"),
    status: Optional[str] = Query(None, description="Filter by status: 'processing', 'completed', 'failed', 'incomplete', or specific status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    service: DocumentService = Depends(get_document_service),
    user: Annotated[dict, Depends(require_auth)] = None
):
    """List documents for a case with optional filtering.
    
    Useful for showing:
    - Processing queue (status=processing or status=incomplete)
    - Completed documents (status=completed)
    - Failed documents (status=failed)
    - All documents (no status filter)
    
    Args:
        case_id: Case ID
        status: Optional status filter
        limit: Max results (default 100)
        offset: Pagination offset (default 0)
        
    Returns:
        DocumentListResponse with documents and total count
    """
    documents, total = await service.list_documents(
        case_id=case_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # Convert to DTOs
    document_dtos = [DocumentDetailResponse.model_validate(doc) for doc in documents]
    
    return DocumentListResponse(
        total=total,
        documents=document_dtos
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: int,
    user: Annotated[dict, Depends(require_auth)] = None
):
    """Get document details and processing status by ID.
    
    Args:
        document_id: The ID of the document
        
    Returns:
        DocumentDetailResponse: Document details with current status
        
    Raises:
        HTTPException 404: If document not found
    """
    from core.models.document import Document
    
    document = await Document.get_or_none(id=document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    return DocumentDetailResponse.model_validate(document)



