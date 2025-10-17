"""
JWT Authentication for FastAPI using NextAuth JWT tokens.
"""

import os
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi_nextauth_jwt import NextAuthJWT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize JWT handler with shared secret
JWT = NextAuthJWT(secret=os.getenv("AUTH_SECRET"))

# Type alias for dependency injection
JWTPayload = Annotated[dict, Depends(JWT)]

def get_current_user_id(jwt: JWTPayload) -> str:
    """Extract user ID from JWT payload."""
    user_id = jwt.get("sub") or jwt.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    return str(user_id)

def get_current_user_email(jwt: JWTPayload) -> str:
    """Extract user email from JWT payload."""
    email = jwt.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email"
        )
    return email

# Convenience type aliases for common use cases
CurrentUserID = Annotated[str, Depends(get_current_user_id)]
CurrentUserEmail = Annotated[str, Depends(get_current_user_email)]
