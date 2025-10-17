"""MinIO storage client for S3-compatible object storage."""
from typing import Optional, BinaryIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from core.config import settings


class StorageClient:
    """Manages MinIO object storage operations.
    
    Each tenant will have their own bucket for complete isolation.
    For MVP, we'll use a default bucket.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: Optional[bool] = None
    ):
        """Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint. Uses settings if not provided.
            access_key: MinIO access key. Uses settings if not provided.
            secret_key: MinIO secret key. Uses settings if not provided.
            secure: Use HTTPS. Uses settings if not provided.
        """
        self.endpoint = endpoint or settings.minio_endpoint
        self.access_key = access_key or settings.minio_access_key
        self.secret_key = secret_key or settings.minio_secret_key
        self.secure = secure if secure is not None else settings.minio_secure
        self.client = None
        self.initialized = False
    
    async def init(self) -> None:
        """Initialize MinIO client.
        
        Call this on application startup.
        """
        if self.initialized:
            return
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        self.initialized = True
    
    async def create_bucket(self, bucket_name: str) -> None:
        """Create a bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to create bucket: {e}")
    
    async def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload a file to MinIO.
        
        Auto-creates bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket.
            object_name: Name/path of the object in the bucket.
            data: File data as bytes.
            content_type: MIME type of the file.
        
        Returns:
            The object name (key) of the uploaded file.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            from io import BytesIO
            
            # Auto-create bucket if it doesn't exist
            await self.create_bucket(bucket_name)
            
            self.client.put_object(
                bucket_name,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            raise RuntimeError(f"Failed to upload file: {e}")
    
    async def download(self, bucket_name: str, object_name: str) -> bytes:
        """Download a file from MinIO.
        
        Args:
            bucket_name: Name of the bucket.
            object_name: Name/path of the object in the bucket.
        
        Returns:
            File data as bytes.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Failed to download file: {e}")
    
    async def download_partial(
        self, 
        bucket_name: str, 
        object_name: str, 
        offset: int = 0, 
        length: int = 8192
    ) -> bytes:
        """Download only part of a file from MinIO (streaming/peeking).
        
        Useful for file type detection - only downloads first few KB.
        
        Args:
            bucket_name: Name of the bucket.
            object_name: Name/path of the object in the bucket.
            offset: Byte offset to start reading from (default 0 = beginning).
            length: Number of bytes to read (default 8KB).
        
        Returns:
            Partial file data as bytes.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            response = self.client.get_object(
                bucket_name, 
                object_name, 
                offset=offset, 
                length=length
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Failed to download partial file: {e}")
    
    async def delete(self, bucket_name: str, object_name: str) -> None:
        """Delete a file from MinIO.
        
        Args:
            bucket_name: Name of the bucket.
            object_name: Name/path of the object in the bucket.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            self.client.remove_object(bucket_name, object_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file: {e}")
    
    async def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expiry: int = 3600
    ) -> str:
        """Generate a presigned URL for temporary access to a file.
        
        Args:
            bucket_name: Name of the bucket.
            object_name: Name/path of the object in the bucket.
            expiry: URL expiry time in seconds (default 1 hour).
        
        Returns:
            Presigned URL string.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expiry)
            )
            return url
        except S3Error as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")
    
    async def list_objects(self, bucket_name: str, prefix: str = "") -> list:
        """List objects in a bucket.
        
        Args:
            bucket_name: Name of the bucket.
            prefix: Filter objects by prefix.
        
        Returns:
            List of object names.
        """
        if not self.initialized:
            raise RuntimeError("StorageClient not initialized. Call init() first.")
        
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise RuntimeError(f"Failed to list objects: {e}")
    
    async def health_check(self) -> bool:
        """Check if MinIO is reachable.
        
        Returns:
            True if connection is healthy, False otherwise.
        """
        if not self.initialized:
            return False
        
        try:
            self.client.list_buckets()
            return True
        except Exception:
            return False


# Singleton instance for FastAPI dependency injection
storage_client = StorageClient()

