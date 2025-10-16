"""Mock Pinecone client for testing."""
from typing import List, Dict, Any, Optional


class MockPineconeClient:
    """Mock Pinecone client for testing.
    
    Stores vectors in memory instead of actually connecting to Pinecone.
    """
    
    def __init__(self):
        """Initialize with in-memory storage."""
        self.initialized = False
        self.indexes: Dict[str, Dict[str, Any]] = {}  # index_name -> config
        self.vectors: Dict[str, List[Dict]] = {}  # index_name -> list of vectors
    
    async def init(self) -> None:
        """Mock initialization."""
        self.initialized = True
    
    async def create_index(
        self,
        index_name: str,
        dimension: int = 768,
        metric: str = "cosine"
    ) -> None:
        """Mock index creation."""
        if index_name not in self.indexes:
            self.indexes[index_name] = {
                "dimension": dimension,
                "metric": metric
            }
            self.vectors[index_name] = []
    
    async def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, int]:
        """Mock vector upsert - stores in memory."""
        if index_name not in self.vectors:
            raise RuntimeError(f"Index not found: {index_name}")
        
        # Store vectors
        for vector in vectors:
            # Remove existing vector with same ID
            self.vectors[index_name] = [
                v for v in self.vectors[index_name] if v["id"] != vector["id"]
            ]
            # Add new vector
            self.vectors[index_name].append(vector)
        
        return {"upserted_count": len(vectors)}
    
    async def query(
        self,
        index_name: str,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "",
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Mock query - returns dummy results."""
        if index_name not in self.vectors:
            return []
        
        # For testing, just return first top_k vectors
        results = []
        for i, vec in enumerate(self.vectors[index_name][:top_k]):
            results.append({
                "id": vec["id"],
                "score": 0.95 - (i * 0.05),  # Dummy scores
                "metadata": vec.get("metadata") if include_metadata else None
            })
        
        return results
    
    async def delete(
        self,
        index_name: str,
        ids: Optional[List[str]] = None,
        delete_all: bool = False,
        namespace: str = "",
        filter: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mock vector deletion."""
        if index_name not in self.vectors:
            return
        
        if delete_all:
            self.vectors[index_name] = []
        elif ids:
            self.vectors[index_name] = [
                v for v in self.vectors[index_name] if v["id"] not in ids
            ]
    
    async def health_check(self) -> bool:
        """Mock health check."""
        return self.initialized
    
    def get_vector_count(self, index_name: str) -> int:
        """Helper to get vector count for testing."""
        return len(self.vectors.get(index_name, []))
    
    def get_vector(self, index_name: str, vector_id: str) -> Optional[Dict]:
        """Helper to get a specific vector for testing."""
        if index_name not in self.vectors:
            return None
        
        for vec in self.vectors[index_name]:
            if vec["id"] == vector_id:
                return vec
        
        return None
    
    def clear(self) -> None:
        """Clear all indexes and vectors."""
        self.indexes.clear()
        self.vectors.clear()

