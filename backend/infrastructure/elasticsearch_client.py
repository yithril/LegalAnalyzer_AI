"""Elasticsearch client for full-text search on summaries."""
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch
from core.config import settings


class ElasticsearchClient:
    """Manages Elasticsearch operations for document summaries.
    
    Used for full-text search across document summaries, enabling
    fast keyword-based retrieval and highlighting.
    """
    
    def __init__(self, elasticsearch_url: Optional[str] = None):
        """Initialize Elasticsearch client.
        
        Args:
            elasticsearch_url: Elasticsearch URL. Uses settings if not provided.
        """
        self.url = elasticsearch_url or settings.elasticsearch_url
        self.client: Optional[AsyncElasticsearch] = None
        self.initialized = False
    
    async def init(self) -> None:
        """Initialize Elasticsearch connection.
        
        Call this on application startup.
        """
        if self.initialized:
            return
        
        self.client = AsyncElasticsearch([self.url])
        self.initialized = True
        
        print(f"[Elasticsearch] Connected to {self.url}")
    
    async def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            self.initialized = False
    
    async def create_index(self, index_name: str, mappings: Dict[str, Any] = None) -> None:
        """Create an Elasticsearch index if it doesn't exist.
        
        Args:
            index_name: Name of the index
            mappings: Optional field mappings
        """
        if not self.initialized:
            raise RuntimeError("ElasticsearchClient not initialized. Call init() first.")
        
        # Check if index exists
        exists = await self.client.indices.exists(index=index_name)
        
        if exists:
            return
        
        # Default mappings for summaries if not provided
        if mappings is None:
            mappings = {
                "properties": {
                    "document_id": {"type": "integer"},
                    "case_id": {"type": "integer"},
                    "classification": {"type": "keyword"},
                    "filename": {"type": "keyword"},
                    "executive_summary": {"type": "text"},
                    "chunk_summaries": {"type": "text"},
                    "created_at": {"type": "date"}
                }
            }
        
        # Create index
        await self.client.indices.create(
            index=index_name,
            mappings=mappings
        )
        
        print(f"[Elasticsearch] Created index: {index_name}")
    
    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Index a document for search.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            document: Document data to index
            
        Returns:
            Indexing result
        """
        if not self.initialized:
            raise RuntimeError("ElasticsearchClient not initialized. Call init() first.")
        
        result = await self.client.index(
            index=index_name,
            id=doc_id,
            document=document
        )
        
        return result
    
    async def search(
        self,
        index_name: str,
        query: str,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search documents with full-text query.
        
        Args:
            index_name: Index to search
            query: Search query text
            size: Number of results to return
            filters: Optional filters (e.g., {"case_id": 123})
            
        Returns:
            List of search results with highlights
        """
        if not self.initialized:
            raise RuntimeError("ElasticsearchClient not initialized. Call init() first.")
        
        # Build search body
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["executive_summary^2", "chunk_summaries"],  # Boost executive summary
                                "type": "best_fields"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "executive_summary": {},
                    "chunk_summaries": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = [{"term": {k: v}} for k, v in filters.items()]
            search_body["query"]["bool"]["filter"] = filter_clauses
        
        # Execute search
        response = await self.client.search(
            index=index_name,
            body=search_body,
            size=size
        )
        
        # Format results
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "document": hit["_source"],
                "highlights": hit.get("highlight", {})
            })
        
        return results
    
    async def delete_document(self, index_name: str, doc_id: str) -> None:
        """Delete a document from the index.
        
        Args:
            index_name: Index name
            doc_id: Document ID to delete
        """
        if not self.initialized:
            raise RuntimeError("ElasticsearchClient not initialized. Call init() first.")
        
        await self.client.delete(
            index=index_name,
            id=doc_id,
            ignore=[404]  # Don't error if document doesn't exist
        )
    
    async def health_check(self) -> bool:
        """Check if Elasticsearch is reachable and healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            health = await self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False


# Singleton instance for FastAPI dependency injection
elasticsearch_client = ElasticsearchClient()

