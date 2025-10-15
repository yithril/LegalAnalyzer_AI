"""Base class for content analyzers using strategy pattern."""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from enum import Enum
from core.constants import SupportedFileType


class ContentCategory(str, Enum):
    """Content category classification.
    
    Identifies what type of content a document contains.
    """
    BUSINESS_EMAIL = "business_email"
    SPAM_EMAIL = "spam_email"
    LEGAL_DOCUMENT = "legal_document"
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    COVER_PAGE_ONLY = "cover_page_only"
    JUNK = "junk"
    UNKNOWN = "unknown"


class FilterDecision(BaseModel):
    """Decision about whether to process a document.
    
    This is the output of all content analyzers.
    """
    
    # The main decision - should this document be processed?
    should_process: bool
    
    # What category of content is this?
    category: ContentCategory
    
    # Why was this decision made? (for logging/debugging)
    reasoning: str
    
    # Confidence level (0.0 to 1.0)
    confidence: float


class ContentAnalyzer(ABC):
    """Base class for content analyzers.
    
    Uses strategy pattern - different analyzers for different content types.
    Each analyzer decides if it can handle content, then analyzes it.
    """
    
    @abstractmethod
    def can_analyze(self, file_type: SupportedFileType, content_preview: str) -> bool:
        """Determine if this analyzer can handle the content.
        
        Args:
            file_type: The detected file type
            content_preview: First ~500 characters of content
            
        Returns:
            True if this analyzer can handle this content type
        """
        pass
    
    @abstractmethod
    async def analyze(self, content_sample: str, metadata: dict) -> FilterDecision:
        """Analyze content and decide if it should be processed.
        
        Args:
            content_sample: Larger sample of content (e.g., first 50KB)
            metadata: Document metadata (filename, file_type, etc.)
            
        Returns:
            FilterDecision with should_process flag and reasoning
        """
        pass

