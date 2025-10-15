"""
Tests for DocumentClassifierService using REAL implementation.

Simple extension-based classification for MVP.
No mocks - tests real service logic.
"""
from services import DocumentClassifierService, DocumentType


class TestDocumentClassifierService:
    """Test document classification based on file extension."""
    
    def setup_method(self):
        """Set up test instance - using REAL service, not mocked."""
        self.classifier = DocumentClassifierService()
    
    def test_classify_pdf_returns_text_extractable(self):
        """PDF files should be classified as TEXT_EXTRACTABLE."""
        result = self.classifier.classify("contract.pdf")
        assert result == DocumentType.TEXT_EXTRACTABLE
    
    def test_classify_docx_returns_text_extractable(self):
        """DOCX files should be classified as TEXT_EXTRACTABLE."""
        result = self.classifier.classify("memo.docx")
        assert result == DocumentType.TEXT_EXTRACTABLE
    
    def test_classify_txt_returns_text_extractable(self):
        """TXT files should be classified as TEXT_EXTRACTABLE."""
        result = self.classifier.classify("notes.txt")
        assert result == DocumentType.TEXT_EXTRACTABLE
    
    def test_classify_jpg_returns_ocr_needed(self):
        """Image files should be classified as OCR_NEEDED."""
        result = self.classifier.classify("scan.jpg")
        assert result == DocumentType.OCR_NEEDED
    
    def test_classify_png_returns_ocr_needed(self):
        """PNG files should be classified as OCR_NEEDED."""
        result = self.classifier.classify("screenshot.png")
        assert result == DocumentType.OCR_NEEDED
    
    def test_classify_unknown_extension_returns_unknown(self):
        """Unknown file types should return UNKNOWN."""
        result = self.classifier.classify("file.xyz")
        assert result == DocumentType.UNKNOWN
    
    def test_extension_matching_is_case_insensitive(self):
        """File extension matching should be case-insensitive."""
        assert self.classifier.classify("doc.PDF") == DocumentType.TEXT_EXTRACTABLE
        assert self.classifier.classify("doc.Docx") == DocumentType.TEXT_EXTRACTABLE
        assert self.classifier.classify("img.JPG") == DocumentType.OCR_NEEDED

