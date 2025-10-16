"""Data Transfer Objects for case operations."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CaseCreateRequest(BaseModel):
    """Request to create a new case."""
    
    name: str
    description: Optional[str] = None


class CaseUpdateRequest(BaseModel):
    """Request to update a case."""
    
    name: Optional[str] = None
    description: Optional[str] = None


class CaseResponse(BaseModel):
    """Response for case operations."""
    
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

