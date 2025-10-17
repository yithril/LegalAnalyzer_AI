"""FastAPI dependencies for authentication and authorization."""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from core.auth import JWT, JWTPayload


# Required authentication - raises 401 if not authenticated
async def require_auth(jwt: JWTPayload) -> dict:
    """
    Require authentication for an endpoint.
    
    Returns the decoded JWT payload if valid.
    Raises 401 if authentication fails.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: Annotated[dict, Depends(require_auth)]):
            return {"user_id": user.get("sub"), "email": user.get("email")}
    """
    if not jwt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return jwt


# Optional authentication - returns None if not authenticated
async def optional_auth(jwt: JWTPayload) -> Optional[dict]:
    """
    Optional authentication for an endpoint.
    
    Returns the decoded JWT payload if valid, None otherwise.
    Does not raise exceptions.
    
    Usage:
        @app.get("/maybe-protected")
        async def route(user: Annotated[Optional[dict], Depends(optional_auth)]):
            if user:
                return {"message": f"Hello {user.get('email')}"}
            return {"message": "Hello guest"}
    """
    return jwt if jwt else None
