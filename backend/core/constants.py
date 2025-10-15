"""Application-wide constants."""
from enum import Enum


class SupportedFileType(str, Enum):
    """Supported document file types for MVP.
    
    Currently supporting only pure text extractable formats.
    OCR and multimodal formats will be added in later phases.
    """
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    HTML = "html"
    UNKNOWN = "unknown"  # Placeholder for files that need preprocessing


# File type to MIME type mapping
FILE_TYPE_MIME_MAPPING = {
    SupportedFileType.PDF: "application/pdf",
    SupportedFileType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    SupportedFileType.DOC: "application/msword",
    SupportedFileType.TXT: "text/plain",
    SupportedFileType.HTML: "text/html",
}


# File validation limits
MAX_FILE_SIZE_MB = 50  # Maximum file size in megabytes
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# MinIO bucket name for documents
DOCUMENTS_BUCKET = "legal-documents"


class DocumentStatus(str, Enum):
    """Document processing status.
    
    Tracks where the document is in the processing pipeline.
    """
    UPLOADED = "uploaded"  # File successfully uploaded to MinIO
    DETECTING_TYPE = "detecting_type"  # Detecting file type from content (for files without extension)
    ANALYZING_CONTENT = "analyzing_content"  # Running content analysis (spam detection, quality check)
    FILTERED_OUT = "filtered_out"  # Document filtered out (spam, low quality, etc.) - will not be processed further
    VALIDATING = "validating"  # Running security/format checks
    EXTRACTING_BLOCKS = "extracting_blocks"  # Extracting layout blocks from document
    EXTRACTING_METADATA = "extracting_metadata"  # LLM extracting court metadata
    CHUNKING = "chunking"  # Creating semantic chunks
    EMBEDDING = "embedding"  # Generating vector embeddings
    COMPLETED = "completed"  # Fully processed and searchable
    FAILED = "failed"  # Processing failed

