"""Mock storage client for testing."""
from typing import Dict, Optional


class MockStorageClient:
    """Mock MinIO storage client for testing.
    
    Stores files in memory instead of actually connecting to MinIO.
    """
    
    def __init__(self):
        """Initialize with in-memory storage."""
        self.initialized = True
        self.files: Dict[str, bytes] = {}  # Key format: "bucket/object_name"
    
    def _make_key(self, bucket_name: str, object_name: str) -> str:
        """Create storage key from bucket and object name."""
        return f"{bucket_name}/{object_name}"
    
    async def init(self) -> None:
        """Mock initialization."""
        self.initialized = True
    
    async def create_bucket(self, bucket_name: str) -> None:
        """Mock bucket creation."""
        pass  # No-op for mock
    
    async def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Mock file upload - stores in memory."""
        key = self._make_key(bucket_name, object_name)
        self.files[key] = data
        return object_name
    
    async def download(self, bucket_name: str, object_name: str) -> bytes:
        """Mock file download - retrieves from memory."""
        key = self._make_key(bucket_name, object_name)
        if key not in self.files:
            raise RuntimeError(f"File not found: {key}")
        return self.files[key]
    
    async def download_partial(
        self,
        bucket_name: str,
        object_name: str,
        offset: int = 0,
        length: int = 8192
    ) -> bytes:
        """Mock partial download - returns first N bytes."""
        key = self._make_key(bucket_name, object_name)
        if key not in self.files:
            raise RuntimeError(f"File not found: {key}")
        
        full_data = self.files[key]
        return full_data[offset:offset + length]
    
    async def delete(self, bucket_name: str, object_name: str) -> None:
        """Mock file deletion."""
        key = self._make_key(bucket_name, object_name)
        if key in self.files:
            del self.files[key]
    
    async def health_check(self) -> bool:
        """Mock health check."""
        return self.initialized
    
    def add_file(self, bucket_name: str, object_name: str, data: bytes) -> None:
        """Helper method to add files to mock storage for testing."""
        key = self._make_key(bucket_name, object_name)
        self.files[key] = data
    
    def clear(self) -> None:
        """Clear all stored files."""
        self.files.clear()

