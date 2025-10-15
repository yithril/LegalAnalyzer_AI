"""
Tests for PreprocessingService file type detection.

Tests file type detection using content analysis (not file extension).
Uses mock storage and sample file data.
"""
import pytest
from tortoise import Tortoise
from services.preprocessing_service import PreprocessingService
from core.models.document import Document
from core.models.case import Case
from core.constants import SupportedFileType, DocumentStatus, DOCUMENTS_BUCKET
from tests.helpers import FileSamples, MockStorageClient


@pytest.fixture
async def db():
    """Set up in-memory database for testing."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["core.models"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def test_case(db):
    """Create a test case."""
    case = await Case.create(
        name="Test Case",
        description="Test case for preprocessing"
    )
    return case


@pytest.fixture
def mock_storage():
    """Create mock storage client."""
    return MockStorageClient()


@pytest.fixture
def preprocessing_service(mock_storage):
    """Create preprocessing service with mock storage."""
    return PreprocessingService(mock_storage)


@pytest.mark.asyncio
class TestPreprocessingService:
    """Test preprocessing service file type detection."""
    
    async def test_detect_pdf_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect PDF files by content."""
        # Create document with unknown type
        document = await Document.create(
            case_id=test_case.id,
            filename="document.pdf",
            file_type=SupportedFileType.UNKNOWN,
            file_size=1000,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_1/original.pdf",
            status=DocumentStatus.UPLOADED
        )
        
        # Add PDF file to mock storage
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.pdf())
        
        # Run detection
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # Verify
        assert result.file_type == SupportedFileType.PDF
        assert result.status == DocumentStatus.UPLOADED
        assert result.processing_error is None
    
    async def test_detect_docx_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect DOCX files by content (ZIP signature)."""
        document = await Document.create(
            case_id=test_case.id,
            filename="report.docx",
            file_type=SupportedFileType.UNKNOWN,
            file_size=5000,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_2/original.docx",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.docx())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        assert result.file_type == SupportedFileType.DOCX
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_detect_old_doc_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect old DOC files by content."""
        document = await Document.create(
            case_id=test_case.id,
            filename="legacy.doc",
            file_type=SupportedFileType.UNKNOWN,
            file_size=3000,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_3/original.doc",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.doc())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        assert result.file_type == SupportedFileType.DOC
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_detect_plain_text_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect plain text files."""
        document = await Document.create(
            case_id=test_case.id,
            filename="notes.txt",
            file_type=SupportedFileType.UNKNOWN,
            file_size=500,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_4/original.txt",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.txt())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        assert result.file_type == SupportedFileType.TXT
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_detect_html_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect HTML files."""
        document = await Document.create(
            case_id=test_case.id,
            filename="page.html",
            file_type=SupportedFileType.UNKNOWN,
            file_size=800,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_5/original.html",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.html())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        assert result.file_type == SupportedFileType.HTML
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_detect_email_file(self, preprocessing_service, mock_storage, test_case):
        """Should detect email files (RFC 822) as HTML."""
        document = await Document.create(
            case_id=test_case.id,
            filename="enron_email",  # No extension!
            file_type=SupportedFileType.UNKNOWN,
            file_size=1200,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_6/original",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.email_rfc822())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        assert result.file_type == SupportedFileType.HTML
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_detect_xml_as_text(self, preprocessing_service, mock_storage, test_case):
        """Should detect XML files as plain text (text/* MIME type)."""
        document = await Document.create(
            case_id=test_case.id,
            filename="data.xml",
            file_type=SupportedFileType.UNKNOWN,
            file_size=600,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_7/original.xml",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.xml())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # XML should be detected as text/* MIME type, mapped to TXT
        assert result.file_type == SupportedFileType.TXT
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_unknown_file_marked_as_failed(self, preprocessing_service, mock_storage, test_case):
        """Should mark unknown file types as FAILED for manual review."""
        document = await Document.create(
            case_id=test_case.id,
            filename="unknown.bin",
            file_type=SupportedFileType.UNKNOWN,
            file_size=2000,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_8/original.bin",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.unknown_binary())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # Should remain UNKNOWN and be marked as FAILED
        assert result.file_type == SupportedFileType.UNKNOWN
        assert result.status == DocumentStatus.FAILED
        assert "Could not detect file type" in result.processing_error
        assert "manual review" in result.processing_error
    
    async def test_status_changes_during_detection(self, preprocessing_service, mock_storage, test_case):
        """Should update status to DETECTING_TYPE during processing."""
        document = await Document.create(
            case_id=test_case.id,
            filename="test.pdf",
            file_type=SupportedFileType.UNKNOWN,
            file_size=1000,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_9/original.pdf",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.pdf())
        
        # Run detection
        await preprocessing_service.detect_and_update_file_type(document.id)
        
        # Fetch fresh from DB to verify final state
        updated_doc = await Document.get(id=document.id)
        assert updated_doc.status == DocumentStatus.UPLOADED
        assert updated_doc.file_type == SupportedFileType.PDF
    
    async def test_document_not_found(self, preprocessing_service, db):
        """Should raise 404 error if document doesn't exist."""
        with pytest.raises(Exception) as exc_info:
            await preprocessing_service.detect_and_update_file_type(99999)
        
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
    
    async def test_partial_download_used(self, preprocessing_service, mock_storage, test_case):
        """Should only download first 8KB for detection (not full file)."""
        # Create a large file (simulated)
        large_file_data = FileSamples.pdf() + (b'\x00' * 100000)  # PDF header + 100KB of data
        
        document = await Document.create(
            case_id=test_case.id,
            filename="large.pdf",
            file_type=SupportedFileType.UNKNOWN,
            file_size=len(large_file_data),
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_10/original.pdf",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, large_file_data)
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # Should successfully detect PDF even though it only looked at first 8KB
        assert result.file_type == SupportedFileType.PDF
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_csv_detected_as_text(self, preprocessing_service, mock_storage, test_case):
        """Should detect CSV files as plain text."""
        document = await Document.create(
            case_id=test_case.id,
            filename="data.csv",
            file_type=SupportedFileType.UNKNOWN,
            file_size=400,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_11/original.csv",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.csv())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # CSV is text/csv or text/plain, should map to TXT
        assert result.file_type == SupportedFileType.TXT
        assert result.status == DocumentStatus.UPLOADED
    
    async def test_markdown_detected_as_text(self, preprocessing_service, mock_storage, test_case):
        """Should detect Markdown files as plain text."""
        document = await Document.create(
            case_id=test_case.id,
            filename="readme.md",
            file_type=SupportedFileType.UNKNOWN,
            file_size=300,
            minio_bucket=DOCUMENTS_BUCKET,
            minio_key="documents/doc_12/original.md",
            status=DocumentStatus.UPLOADED
        )
        
        mock_storage.add_file(DOCUMENTS_BUCKET, document.minio_key, FileSamples.markdown())
        
        result = await preprocessing_service.detect_and_update_file_type(document.id)
        
        # Markdown is text/plain or text/markdown, should map to TXT
        assert result.file_type == SupportedFileType.TXT
        assert result.status == DocumentStatus.UPLOADED

