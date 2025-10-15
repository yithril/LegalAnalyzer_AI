"""Case service for handling case operations."""
from fastapi import HTTPException
from core.models.case import Case
from dtos.case_dto import CaseCreateRequest


class CaseService:
    """Service for case CRUD operations."""
    
    async def create_case(self, request: CaseCreateRequest) -> Case:
        """Create a new case.
        
        Args:
            request: Case creation details
            
        Returns:
            Case: The created case record
        """
        case = await Case.create(
            name=request.name,
            description=request.description
        )
        return case
    
    async def get_case(self, case_id: int) -> Case:
        """Get a case by ID.
        
        Args:
            case_id: The ID of the case
            
        Returns:
            Case: The case record
            
        Raises:
            HTTPException: If case not found
        """
        case = await Case.get_or_none(id=case_id)
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case with ID {case_id} not found")
        
        return case
    
    async def list_cases(self) -> list[Case]:
        """List all cases.
        
        Returns:
            List of all case records
        """
        cases = await Case.all()
        return cases

