"""User model."""
from enum import Enum
from tortoise import fields
from core.models.base import BaseModel


class UserRole(str, Enum):
    """User role enumeration."""
    ANALYST = "analyst"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(BaseModel):
    """User model for authentication and authorization."""
    
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255)
    role = fields.CharEnumField(UserRole, default=UserRole.USER)
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "users"
    
    def __str__(self):
        return f"User(email={self.email}, role={self.role})"

