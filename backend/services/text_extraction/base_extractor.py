"""Base class for text extraction strategies."""
from abc import ABC, abstractmethod
from services.models import DocumentType, ExtractedDocument


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
    async def extract(self, file_data: bytes, filename: str, document_id: int) -> ExtractedDocument:
        """
        Extract text and structure from document.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename (for extension checking)
            document_id: Database ID of the document
            
        Returns:
            ExtractedDocument with pages, blocks, and text
        """
        pass

