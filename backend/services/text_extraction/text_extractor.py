"""Text extraction strategy for TEXT_EXTRACTABLE documents (PDF, DOCX, TXT)."""
from services.models import DocumentType
from services.text_extraction.base_extractor import BaseTextExtractor


class TextExtractor(BaseTextExtractor):
    """Extract text from PDFs, DOCX, and TXT files."""
    
    def can_handle(self, doc_type: DocumentType) -> bool:
        """Handle TEXT_EXTRACTABLE documents."""
        return doc_type == DocumentType.TEXT_EXTRACTABLE
    
    def extract(self, file_data: bytes, filename: str) -> str:
        """
        Extract text from document.
        
        TODO: Implement extraction for:
        - PDF (PyMuPDF)
        - DOCX (python-docx)
        - TXT (decode bytes)
        """
        # Stub - will implement later
        raise NotImplementedError("Text extraction not yet implemented")

