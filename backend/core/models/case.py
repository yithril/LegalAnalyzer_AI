"""Case model for organizing documents."""
from tortoise import fields
from core.models.base import BaseModel


class Case(BaseModel):
    """Case model representing a legal case.
    
    Documents are organized under cases. Keep it minimal for now.
    
    Note: BaseModel already provides id, created_at, updated_at
    """
    
    # Basic case information
    name = fields.CharField(max_length=255)  # e.g., "Smith v. Jones"
    description = fields.TextField(null=True)  # Optional case description
    
    # Relationship to documents (reverse relation)
    # Access via: case.documents.all()
    
    class Meta:
        table = "cases"
    
    def __str__(self):
        return f"Case(id={self.id}, name={self.name})"

