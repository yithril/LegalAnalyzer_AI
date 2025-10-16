"""Case controller for HTTP endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends
from dtos.case_dto import CaseCreateRequest, CaseUpdateRequest, CaseResponse
from services.case_service import CaseService
from core.dependencies import require_auth


router = APIRouter(prefix="/cases", tags=["cases"])


def get_case_service() -> CaseService:
    """Dependency injection for CaseService."""
    return CaseService()


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(
    request: CaseCreateRequest,
    service: CaseService = Depends(get_case_service),
    user: Annotated[dict, Depends(require_auth)] = None
) -> CaseResponse:
    """Create a new case.
    
    Args:
        request: Case creation details
        service: Injected case service
        user: Authenticated user from JWT
        
    Returns:
        CaseResponse: The created case
    """
    # You can access user info: user.get("sub"), user.get("email"), etc.
    case = await service.create_case(request)
    return CaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    service: CaseService = Depends(get_case_service),
    user: Annotated[dict, Depends(require_auth)] = None
) -> CaseResponse:
    """Get case details by ID.
    
    Args:
        case_id: The ID of the case
        service: Injected case service
        user: Authenticated user from JWT
        
    Returns:
        CaseResponse: Case details
        
    Raises:
        HTTPException 404: If case not found
    """
    case = await service.get_case(case_id)
    return CaseResponse.model_validate(case)


@router.get("/", response_model=list[CaseResponse])
async def list_cases(
    service: CaseService = Depends(get_case_service),
    user: Annotated[dict, Depends(require_auth)] = None
) -> list[CaseResponse]:
    """List all cases.
    
    Args:
        service: Injected case service
        user: Authenticated user from JWT
        
    Returns:
        List of all cases
    """
    cases = await service.list_cases()
    return [CaseResponse.model_validate(case) for case in cases]


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    request: CaseUpdateRequest,
    service: CaseService = Depends(get_case_service),
    user: Annotated[dict, Depends(require_auth)] = None
) -> CaseResponse:
    """Update a case.
    
    Args:
        case_id: The ID of the case to update
        request: Update request with fields to change
        service: Injected case service
        user: Authenticated user from JWT
        
    Returns:
        CaseResponse: The updated case
        
    Raises:
        HTTPException 404: If case not found
    """
    case = await service.update_case(case_id, request)
    return CaseResponse.model_validate(case)


@router.delete("/{case_id}", status_code=204)
async def delete_case(
    case_id: int,
    service: CaseService = Depends(get_case_service),
    user: Annotated[dict, Depends(require_auth)] = None
):
    """Delete a case.
    
    Args:
        case_id: The ID of the case to delete
        service: Injected case service
        user: Authenticated user from JWT
        
    Raises:
        HTTPException 404: If case not found
    """
    await service.delete_case(case_id)
