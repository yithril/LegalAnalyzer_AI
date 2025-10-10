"""Base model for all database models."""
from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    """Base model with common fields for all models."""
    
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        abstract = True

