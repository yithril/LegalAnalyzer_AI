"""Data Transfer Objects for authentication."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request DTO."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response DTO."""
    id: int
    email: str
    name: str
    role: str
    
    class Config:
        from_attributes = True

