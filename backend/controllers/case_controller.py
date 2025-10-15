"""Case controller for HTTP endpoints."""
from fastapi import APIRouter, Depends
from dtos.case_dto import CaseCreateRequest, CaseResponse
from services.case_service import CaseService


router = APIRouter(prefix="/cases", tags=["cases"])


def get_case_service() -> CaseService:
    """Dependency injection for CaseService."""
    return CaseService()


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(
    request: CaseCreateRequest,
    service: CaseService = Depends(get_case_service)
) -> CaseResponse:
    """Create a new case.
    
    Args:
        request: Case creation details
        service: Injected case service
        
    Returns:
        CaseResponse: The created case
    """
    case = await service.create_case(request)
    return CaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    service: CaseService = Depends(get_case_service)
) -> CaseResponse:
    """Get case details by ID.
    
    Args:
        case_id: The ID of the case
        service: Injected case service
        
    Returns:
        CaseResponse: Case details
        
    Raises:
        HTTPException 404: If case not found
    """
    case = await service.get_case(case_id)
    return CaseResponse.model_validate(case)


@router.get("/", response_model=list[CaseResponse])
async def list_cases(
    service: CaseService = Depends(get_case_service)
) -> list[CaseResponse]:
    """List all cases.
    
    Args:
        service: Injected case service
        
    Returns:
        List of all cases
    """
    cases = await service.list_cases()
    return [CaseResponse.model_validate(case) for case in cases]

