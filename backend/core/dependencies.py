"""FastAPI dependencies for authentication and authorization."""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from core.auth import JWT


# Required authentication - raises 401 if not authenticated
async def require_auth(jwt: Annotated[dict, Depends(JWT)]) -> dict:
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
async def optional_auth(jwt: Annotated[dict, Depends(JWT)]) -> Optional[dict]:
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


def get_user_id(jwt: Annotated[dict, Depends(require_auth)]) -> str:
    """
    Extract user ID from JWT.
    
    Usage:
        @app.get("/my-profile")
        async def profile(user_id: Annotated[str, Depends(get_user_id)]):
            return {"user_id": user_id}
    """
    user_id = jwt.get("sub") or jwt.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    return user_id


def get_user_email(jwt: Annotated[dict, Depends(require_auth)]) -> Optional[str]:
    """
    Extract user email from JWT.
    
    Usage:
        @app.get("/my-email")
        async def email(user_email: Annotated[str, Depends(get_user_email)]):
            return {"email": user_email}
    """
    return jwt.get("email")

