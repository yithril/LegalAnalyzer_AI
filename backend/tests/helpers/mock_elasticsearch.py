"""Mock Elasticsearch client for testing."""
from typing import List, Dict, Any, Optional


class MockElasticsearchClient:
    """Mock Elasticsearch client for testing.
    
    Stores documents in memory instead of connecting to real Elasticsearch.
    """
    
    def __init__(self):
        """Initialize with in-memory storage."""
        self.initialized = False
        self.indices: Dict[str, Dict[str, Any]] = {}  # index_name -> {mappings, settings}
        self.documents: Dict[str, Dict[str, Any]] = {}  # index_name -> {doc_id: document}
    
    async def init(self) -> None:
        """Mock initialization."""
        self.initialized = True
    
    async def close(self) -> None:
        """Mock close."""
        self.initialized = False
    
    async def create_index(self, index_name: str, mappings: Dict[str, Any] = None) -> None:
        """Mock index creation."""
        if index_name not in self.indices:
            self.indices[index_name] = {"mappings": mappings or {}}
            self.documents[index_name] = {}
    
    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock document indexing - stores in memory."""
        if index_name not in self.documents:
            self.documents[index_name] = {}
        
        self.documents[index_name][doc_id] = document
        
        return {
            "_id": doc_id,
            "_index": index_name,
            "result": "created"
        }
    
    async def search(
        self,
        index_name: str,
        query: str,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Mock search - returns all documents (for testing)."""
        if index_name not in self.documents:
            return []
        
        results = []
        for doc_id, doc in self.documents[index_name].items():
            results.append({
                "id": doc_id,
                "score": 1.0,
                "document": doc,
                "highlights": {}
            })
        
        return results[:size]
    
    async def delete_document(self, index_name: str, doc_id: str) -> None:
        """Mock document deletion."""
        if index_name in self.documents and doc_id in self.documents[index_name]:
            del self.documents[index_name][doc_id]
    
    async def health_check(self) -> bool:
        """Mock health check."""
        return self.initialized
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Helper to get a document for testing."""
        if index_name not in self.documents:
            return None
        return self.documents[index_name].get(doc_id)
    
    def get_document_count(self, index_name: str) -> int:
        """Helper to count documents in an index."""
        return len(self.documents.get(index_name, {}))
    
    def clear(self) -> None:
        """Clear all indices and documents."""
        self.indices.clear()
        self.documents.clear()

