"""Service-level models and enums."""
from enum import Enum


class DocumentType(str, Enum):
    """Document classification types for processing strategy."""
    TEXT_EXTRACTABLE = "text_extractable"
    OCR_NEEDED = "ocr_needed"
    MULTIMODAL = "multimodal"
    UNKNOWN = "unknown"

