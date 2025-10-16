"""OCR extraction strategy for scanned documents (Phase 2)."""
from services.models import DocumentType, ExtractedDocument
from services.text_extraction.base_extractor import BaseTextExtractor


class OCRExtractor(BaseTextExtractor):
    """Extract text from scanned images using OCR (Phase 2)."""
    
    def can_handle(self, doc_type: DocumentType) -> bool:
        """Handle OCR_NEEDED documents."""
        return doc_type == DocumentType.OCR_NEEDED
    
    async def extract(self, file_data: bytes, filename: str, document_id: int) -> ExtractedDocument:
        """
        Extract text using OCR.
        
        TODO Phase 2: Implement OCR extraction using:
        - pytesseract (basic OCR)
        - OR Azure Document Intelligence (better quality)
        """
        # Stub for Phase 2
        raise NotImplementedError("OCR extraction coming in Phase 2")

