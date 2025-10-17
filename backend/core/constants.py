"""Application constants and thresholds."""
from enum import Enum

# Document Processing Thresholds
RELEVANCE_SCORE_TIMELINE_THRESHOLD = 60  # Only extract timeline events from docs with relevance >= 60
LEGAL_SIGNIFICANCE_TIMELINE_THRESHOLD = 50  # Save timeline events with score >= 50


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    ANALYZING = "analyzing"
    SCORING_RELEVANCE = "scoring_relevance"
    INDEXING = "indexing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"
    FILTERED_OUT = "filtered_out"


class SupportedFileType(str, Enum):
    """Supported file types for document processing."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    DOC = "doc"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
