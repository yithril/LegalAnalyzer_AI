"""Document indexing service for Elasticsearch full-text search."""
import json
from typing import List, Dict, Any
from infrastructure.storage import StorageClient
from infrastructure.elasticsearch_client import ElasticsearchClient
from core.models.document import Document


class DocumentIndexingService:
    """Prepares and indexes documents in Elasticsearch for keyword search.
    
    Single Responsibility:
    - Take blocks from S3
    - Build full_text (concatenate all block texts)
    - Flatten blocks structure
    - Index to Elasticsearch
    
    Does NOT handle summaries - that's SummarizationService's job.
    """
    
    def __init__(self, storage_client: StorageClient, elasticsearch_client: ElasticsearchClient):
        """Initialize indexing service.
        
        Args:
            storage_client: S3 storage client
            elasticsearch_client: Elasticsearch client
        """
        self.storage = storage_client
        self.es = elasticsearch_client
    
    def build_full_text(self, blocks_data: dict) -> str:
        """Build searchable full_text from blocks.
        
        Concatenates all block texts with double newlines for readability.
        
        Args:
            blocks_data: Parsed blocks.json structure with pages and blocks
            
        Returns:
            Full document text as single searchable string
        """
        text_parts = []
        
        for page in blocks_data.get("pages", []):
            for block in page.get("blocks", []):
                text_parts.append(block["text"])
        
        # Join with double newline (paragraph separation)
        return "\n\n".join(text_parts)
    
    def flatten_blocks(self, blocks_data: dict) -> List[Dict[str, Any]]:
        """Flatten page/block structure into flat array.
        
        Takes nested structure:
          pages[0].blocks[0] = {...}
          pages[0].blocks[1] = {...}
          pages[1].blocks[0] = {...}
        
        Returns flat array:
          [block0, block1, block2, ...]
        
        Keeps ALL fields from original blocks - no filtering.
        
        Args:
            blocks_data: Parsed blocks.json structure
            
        Returns:
            Flat list of all blocks from all pages
        """
        flattened = []
        
        for page in blocks_data.get("pages", []):
            for block in page.get("blocks", []):
                # Keep entire block as-is - no filtering
                flattened.append(block)
        
        return flattened
    
    async def index_document_content(
        self, 
        document_id: int, 
        case_id: int
    ) -> None:
        """Index document content in Elasticsearch for keyword search.
        
        Loads blocks from S3, builds full_text, and indexes everything.
        
        Args:
            document_id: Document ID
            case_id: Case ID
        """
        print(f"[Indexing] Starting Elasticsearch indexing for doc {document_id}...")
        
        # Load document metadata
        document = await Document.get(id=document_id)
        
        # Load blocks from S3
        blocks_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
        blocks_bytes = await self.storage.download(
            bucket_name="cases",
            object_name=blocks_key
        )
        blocks_data = json.loads(blocks_bytes.decode('utf-8'))
        
        # Build searchable full_text
        full_text = self.build_full_text(blocks_data)
        print(f"[Indexing] Built full_text: {len(full_text)} characters")
        
        # Flatten blocks structure
        flattened_blocks = self.flatten_blocks(blocks_data)
        print(f"[Indexing] Flattened {len(flattened_blocks)} blocks")
        
        # Prepare Elasticsearch document
        es_document = {
            "document_id": document_id,
            "case_id": case_id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "classification": document.classification,
            "content_category": document.content_category,
            "created_at": document.created_at.isoformat(),
            "status": document.status,
            
            # Relevance scoring
            "relevance_score": document.relevance_score,
            "relevance_reasoning": document.relevance_reasoning,
            
            # Searchable content
            "full_text": full_text,
            
            # Structure for navigation (flattened blocks - ALL fields preserved)
            "blocks": flattened_blocks
        }
        
        # Ensure index exists
        await self.es.create_index("documents")
        
        # Index document
        await self.es.index_document(
            index_name="documents",
            doc_id=f"doc_{document_id}",
            document=es_document
        )
        
        print(f"[Indexing] Indexed document {document_id} in Elasticsearch")

