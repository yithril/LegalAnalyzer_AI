"""Factory to select the appropriate text extraction strategy."""
from typing import List
from services.models import DocumentType
from services.text_extraction.base_extractor import BaseTextExtractor
from services.text_extraction.text_extractor import TextExtractor
from services.text_extraction.ocr_extractor import OCRExtractor


class ExtractionStrategyFactory:
    """Factory to get the right extraction strategy based on document type."""
    
    def __init__(self):
        """Initialize with available extraction strategies."""
        self._strategies: List[BaseTextExtractor] = [
            TextExtractor(),
            OCRExtractor(),
        ]
    
    def get_strategy(self, doc_type: DocumentType) -> BaseTextExtractor:
        """
        Get the appropriate extraction strategy for the document type.
        
        Args:
            doc_type: The classified document type
            
        Returns:
            The extraction strategy that can handle this document type
            
        Raises:
            ValueError: If no strategy can handle this document type
        """
        for strategy in self._strategies:
            if strategy.can_handle(doc_type):
                return strategy
        
        raise ValueError(f"No extraction strategy available for document type: {doc_type}")

