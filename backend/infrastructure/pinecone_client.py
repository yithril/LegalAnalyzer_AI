"""Pinecone vector database client for document embeddings."""
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from core.config import settings


class PineconeClient:
    """Manages Pinecone vector database operations.
    
    Each tenant will have their own index for complete isolation.
    For MVP, we'll use a single default index.
    """
    
    def __init__(self, api_key: Optional[str] = None, environment: Optional[str] = None):
        """Initialize Pinecone client.
        
        Args:
            api_key: Pinecone API key. Uses settings if not provided.
            environment: Pinecone environment/region. Uses settings if not provided.
        """
        self.api_key = api_key or settings.pinecone_api_key
        self.environment = environment or settings.pinecone_environment
        self.client = None
        self.initialized = False
    
    async def init(self) -> None:
        """Initialize Pinecone connection.
        
        Call this on application startup.
        """
        if self.initialized or not self.api_key:
            return
        
        self.client = Pinecone(api_key=self.api_key)
        self.initialized = True
    
    async def create_index(
        self,
        index_name: str,
        dimension: int = 384,  # Default for all-MiniLM-L6-v2 embeddings
        metric: str = "cosine"
    ) -> None:
        """Create a new Pinecone index if it doesn't exist.
        
        Args:
            index_name: Name of the index to create.
            dimension: Vector dimension size.
            metric: Similarity metric (cosine, euclidean, or dotproduct).
        """
        if not self.initialized:
            raise RuntimeError("PineconeClient not initialized. Call init() first.")
        
        # Check if index already exists
        existing_indexes = self.client.list_indexes()
        if index_name in [idx.name for idx in existing_indexes]:
            return
        
        # Create serverless index
        self.client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region=self.environment)
        )
    
    async def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, int]:
        """Insert or update vectors in the index.
        
        Args:
            index_name: Name of the index.
            vectors: List of vector dictionaries with id, values, and optional metadata.
                     Format: [{"id": "doc1_chunk1", "values": [...], "metadata": {...}}]
            namespace: Optional namespace for multi-tenancy within an index.
        
        Returns:
            Dictionary with upsert count.
        """
        if not self.initialized:
            raise RuntimeError("PineconeClient not initialized. Call init() first.")
        
        index = self.client.Index(index_name)
        result = index.upsert(vectors=vectors, namespace=namespace)
        
        return {"upserted_count": result.upserted_count}
    
    async def query(
        self,
        index_name: str,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Query the index for similar vectors.
        
        Args:
            index_name: Name of the index.
            vector: Query vector (embedding).
            top_k: Number of results to return.
            filter: Optional metadata filter.
            namespace: Optional namespace to query.
            include_metadata: Whether to include metadata in results.
        
        Returns:
            List of matches with id, score, and optional metadata.
        """
        if not self.initialized:
            raise RuntimeError("PineconeClient not initialized. Call init() first.")
        
        index = self.client.Index(index_name)
        results = index.query(
            vector=vector,
            top_k=top_k,
            filter=filter,
            namespace=namespace,
            include_metadata=include_metadata
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata if include_metadata else None
            }
            for match in results.matches
        ]
    
    async def delete(
        self,
        index_name: str,
        ids: Optional[List[str]] = None,
        delete_all: bool = False,
        namespace: str = "",
        filter: Optional[Dict[str, Any]] = None
    ) -> None:
        """Delete vectors from the index.
        
        Args:
            index_name: Name of the index.
            ids: List of vector IDs to delete.
            delete_all: If True, delete all vectors in namespace.
            namespace: Optional namespace.
            filter: Optional metadata filter for deletion.
        """
        if not self.initialized:
            raise RuntimeError("PineconeClient not initialized. Call init() first.")
        
        index = self.client.Index(index_name)
        
        if delete_all:
            index.delete(delete_all=True, namespace=namespace)
        elif ids:
            index.delete(ids=ids, namespace=namespace)
        elif filter:
            index.delete(filter=filter, namespace=namespace)
    
    async def health_check(self) -> bool:
        """Check if Pinecone is reachable.
        
        Returns:
            True if connection is healthy, False otherwise.
        """
        if not self.initialized or not self.api_key:
            return False
        
        try:
            self.client.list_indexes()
            return True
        except Exception:
            return False


# Singleton instance for FastAPI dependency injection
pinecone_client = PineconeClient()

