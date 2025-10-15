"""Base class for text extraction strategies."""
from abc import ABC, abstractmethod
from services.models import DocumentType


class BaseTextExtractor(ABC):
    """Abstract base class for text extraction strategies."""
    
    @abstractmethod
    def can_handle(self, doc_type: DocumentType) -> bool:
        """
        Check if this extractor can handle the given document type.
        
        Args:
            doc_type: The classified document type
            
        Returns:
            True if this extractor can handle this document type
        """
        pass
    
    @abstractmethod
    def extract(self, file_data: bytes, filename: str) -> str:
        """
        Extract text from document.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename (for extension checking)
            
        Returns:
            Extracted text content
        """
        pass

