"""Document model for tracking uploaded documents."""
from tortoise import fields
from core.models.base import BaseModel
from core.constants import DocumentStatus, SupportedFileType


class Document(BaseModel):
    """Document model representing an uploaded legal document.
    
    Tracks the document through the entire processing pipeline from
    upload to completion.
    
    Note: BaseModel already provides id, created_at, updated_at
    """
    
    # Relationship to case - every document belongs to a case
    case = fields.ForeignKeyField("models.Case", related_name="documents")
    
    # Basic file information
    filename = fields.CharField(max_length=255)
    file_type = fields.CharEnumField(SupportedFileType)
    file_size = fields.BigIntField()  # Size in bytes
    
    # Storage location in MinIO
    minio_bucket = fields.CharField(max_length=100)
    minio_key = fields.CharField(max_length=500)  # Full path/key in MinIO
    
    # Processing status - tracks where document is in the pipeline
    status = fields.CharEnumField(DocumentStatus, default=DocumentStatus.UPLOADED)
    processing_error = fields.TextField(null=True)  # If processing fails, error details here
    
    # Classification results
    classification = fields.CharField(max_length=50, null=True)  # e.g., "email", "contract", "report"
    
    # Content analysis results (from content_analysis pipeline)
    content_category = fields.CharField(max_length=50, null=True)  # ContentCategory enum value
    filter_confidence = fields.FloatField(null=True)  # 0.0 to 1.0
    filter_reasoning = fields.TextField(null=True)  # Why filtered in/out
    
    # Summarization tracking (summary stored in Elasticsearch)
    has_summary = fields.BooleanField(default=False)  # Quick check if summarized
    summarized_at = fields.DatetimeField(null=True)  # When summarization completed
    
    class Meta:
        table = "documents"
    
    def __str__(self):
        return f"Document(id={self.id}, filename={self.filename}, case_id={self.case_id}, status={self.status})"

