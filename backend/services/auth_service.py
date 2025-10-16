"""Authentication service for user login."""
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from core.models.user import User

# Argon2 password hasher
ph = PasswordHasher()


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using Argon2.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return ph.hash(password)
    
    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password_hash: The stored hash
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            ph.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        user = await User.get_or_none(email=email.lower())
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not AuthService.verify_password(user.password_hash, password):
            return None
        
        return user

