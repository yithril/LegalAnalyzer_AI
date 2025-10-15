# Tests

## Structure

```
tests/
├── helpers/                      # Test utilities and fixtures
│   ├── file_samples.py          # Sample file data for different file types
│   └── mock_storage.py          # Mock MinIO storage client
├── services/                     # Service layer tests
│   ├── test_preprocessing_service.py
│   └── test_document_classifier_service.py
└── README.md                     # This file
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest tests/services/test_preprocessing_service.py
```

### Run specific test class:
```bash
pytest tests/services/test_preprocessing_service.py::TestPreprocessingService
```

### Run specific test:
```bash
pytest tests/services/test_preprocessing_service.py::TestPreprocessingService::test_detect_pdf_file
```

### Run with verbose output:
```bash
pytest -v
```

### Run with coverage:
```bash
pytest --cov=services --cov-report=html
```

## Test Helpers

### FileSamples

Provides realistic file byte sequences for testing file type detection:

```python
from tests.helpers import FileSamples

# Get sample PDF bytes
pdf_data = FileSamples.pdf()

# Get sample DOCX bytes
docx_data = FileSamples.docx()

# Available samples:
# - pdf()
# - docx()
# - doc()
# - txt()
# - html()
# - email_rfc822()  # For Enron-style emails
# - xml()
# - csv()
# - markdown()
# - unknown_binary()
```

### MockStorageClient

Mock implementation of MinIO storage for testing without actual S3/MinIO connection:

```python
from tests.helpers import MockStorageClient

# Create mock storage
storage = MockStorageClient()

# Add file to mock storage
storage.add_file("bucket-name", "path/to/file.pdf", pdf_data)

# Use in tests like real storage
data = await storage.download("bucket-name", "path/to/file.pdf")
partial = await storage.download_partial("bucket-name", "path/to/file.pdf", length=8192)
```

## Test Categories

### Unit Tests

Tests individual services/functions in isolation using mocks:
- `test_preprocessing_service.py` - File type detection logic

### Integration Tests

Tests multiple components working together:
- (Coming soon)

### End-to-End Tests

Tests complete workflows through the API:
- (Coming soon)

## Writing New Tests

### Basic Test Structure

```python
import pytest
from tests.helpers import MockStorageClient, FileSamples

@pytest.mark.asyncio
class TestYourService:
    """Test description."""
    
    async def test_your_feature(self):
        """Should do something specific."""
        # Arrange
        service = YourService()
        
        # Act
        result = await service.do_something()
        
        # Assert
        assert result == expected_value
```

### Async Tests

All async tests must:
1. Use `@pytest.mark.asyncio` decorator
2. Be declared as `async def`
3. Use `await` for async calls

### Database Tests

For tests that need database access:

```python
@pytest.fixture
async def db():
    """Set up in-memory database."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["core.models"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()

@pytest.mark.asyncio
async def test_with_database(db):
    """Test that uses database."""
    document = await Document.create(...)
    assert document.id is not None
```

### Using Fixtures

```python
@pytest.fixture
def mock_storage():
    """Create mock storage for tests."""
    return MockStorageClient()

@pytest.mark.asyncio
async def test_something(mock_storage):
    """Fixture is automatically injected."""
    mock_storage.add_file("bucket", "key", b"data")
    # ... use mock_storage in test
```

## Test Coverage

Current test coverage:
- ✅ PreprocessingService - File type detection
- ✅ DocumentClassifierService - Extension-based classification
- ⏳ DocumentService - File upload and validation (TODO)
- ⏳ CaseService - Case CRUD operations (TODO)
- ⏳ Text extractors (PDF, DOCX, TXT, HTML) (TODO)

## Continuous Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request
- Before deployment

## Troubleshooting

### Tests hang or timeout

Make sure you're using `@pytest.mark.asyncio` for async tests.

### Database errors

Ensure Tortoise ORM is properly initialized in fixtures:
```python
await Tortoise.init(...)
await Tortoise.generate_schemas()
```

### Import errors

Make sure you're running tests from the project root:
```bash
cd /path/to/backend
pytest
```

### Mock not working

Verify mock is injected as fixture parameter:
```python
async def test_something(mock_storage):  # ← Must match fixture name
    pass
```

