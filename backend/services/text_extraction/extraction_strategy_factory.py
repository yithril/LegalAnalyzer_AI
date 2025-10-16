"""Factory to select the appropriate text extraction strategy."""
import os
from services.models import ExtractedDocument
from services.text_extraction.text_extractor import TextExtractor
from services.text_extraction.pdf_extractor import PDFExtractor
from services.text_extraction.ocr_extractor import OCRExtractor


class ExtractionStrategyFactory:
    """Factory to route files to the correct extractor based on file extension."""
    
    def __init__(self):
        """Initialize with available extraction strategies."""
        self._extractors = {
            'txt': TextExtractor(),
            'pdf': PDFExtractor(),
            'docx': None,  # TODO: Implement DOCX extractor
            'doc': None,   # TODO: Implement DOC extractor
        }
    
    def get_extractor(self, filename: str):
        """
        Get the appropriate extractor for the file.
        
        Args:
            filename: Original filename with extension
            
        Returns:
            The extractor that can handle this file type
            
        Raises:
            ValueError: If file extension is not supported
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lstrip('.').lower()
        
        extractor = self._extractors.get(ext)
        
        if extractor is None:
            if ext in self._extractors:
                raise NotImplementedError(f"{ext.upper()} extraction not yet implemented")
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
        
        return extractor
    
    async def extract(self, file_data: bytes, filename: str, document_id: int) -> ExtractedDocument:
        """
        Extract text from document using the appropriate strategy.
        
        Routes based on file extension and delegates to specific extractor.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename (with extension)
            document_id: Database ID of the document
            
        Returns:
            ExtractedDocument with pages, blocks, and text
            
        Raises:
            ValueError: If file extension is not supported
            NotImplementedError: If extractor for file type not yet implemented
        """
        extractor = self.get_extractor(filename)
        return await extractor.extract(file_data, filename, document_id)

