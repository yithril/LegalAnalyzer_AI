"""Authentication controller for login endpoints."""
from fastapi import APIRouter, HTTPException, status
from dtos.auth_dto import LoginRequest, LoginResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate a user and return user information.
    
    NextAuth.js on the frontend will handle creating the JWT session.
    This endpoint just validates credentials and returns user info.
    
    Args:
        request: Login credentials (email and password)
        
    Returns:
        LoginResponse: User information if authentication succeeds
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
    user = await AuthService.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return LoginResponse(
        id=user.id,
        email=user.email,
        name=user.full_name,
        role=user.role.value
    )

