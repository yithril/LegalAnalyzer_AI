"""Document summarization service using map-reduce pattern."""
import json
from datetime import datetime
from typing import List
from infrastructure.storage import StorageClient
from infrastructure.elasticsearch_client import ElasticsearchClient
from core.models.document import Document
from core.constants import DocumentStatus
from core.config import settings
from services.summarization.llama_client import get_llama_client
from services.chunking.models import Chunk, ChunkingResult
from prompts.summarization import chunk_summarization_prompt, executive_summary_prompt


class SummarizationService:
    """Document summarization using map-reduce pattern.
    
    Process:
    1. Load chunks from S3
    2. Summarize each chunk (map)
    3. Combine chunk summaries into executive summary (reduce)
    4. Store in Elasticsearch
    5. Update document tracking
    """
    
    def __init__(self, storage_client: StorageClient, elasticsearch_client: ElasticsearchClient):
        """Initialize summarization service.
        
        Args:
            storage_client: S3 storage client
            elasticsearch_client: Elasticsearch client
        """
        self.storage = storage_client
        self.elasticsearch = elasticsearch_client
        self.llm = get_llama_client()  # Using Llama for speed (can swap to Saul later)
    
    async def summarize_document(self, document_id: int, case_id: int) -> str:
        """Create summary of a document and store in Elasticsearch.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            Executive summary text
        """
        print(f"[Summarization] Starting summarization for doc {document_id}...")
        
        # Load document
        document = await Document.get(id=document_id)
        
        # Load chunks from S3
        chunks = await self._load_chunks(document_id, case_id)
        
        if not chunks:
            print(f"[Summarization] No chunks found for doc {document_id}")
            return "No content to summarize"
        
        print(f"[Summarization] Loaded {len(chunks)} chunks")
        
        # Step 1: Summarize each chunk (map)
        print(f"[Summarization] Summarizing {len(chunks)} chunks...")
        chunk_summaries = await self._summarize_chunks(chunks)
        
        # Step 2: Create executive summary (reduce)
        print(f"[Summarization] Creating executive summary...")
        executive_summary = await self._create_executive_summary(
            chunk_summaries=chunk_summaries,
            classification=document.classification or "document"
        )
        
        # Step 3: Store in Elasticsearch
        print(f"[Summarization] Storing in Elasticsearch...")
        await self._store_in_elasticsearch(
            document_id=document_id,
            case_id=case_id,
            document=document,
            executive_summary=executive_summary,
            chunk_summaries=chunk_summaries,
            total_chunks=len(chunks)
        )
        
        # Step 4: Update document
        document.has_summary = True
        document.summarized_at = datetime.now()
        await document.save()
        
        print(f"[Summarization] Complete! Summary: {len(executive_summary)} chars")
        
        return executive_summary
    
    async def _load_chunks(self, document_id: int, case_id: int) -> List[Chunk]:
        """Load chunks from S3.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            List of chunks
        """
        chunks_key = f"{case_id}/documents/{document_id}/chunks/chunks.json"
        
        try:
            chunks_bytes = await self.storage.download(
                bucket_name="cases",
                object_name=chunks_key
            )
            chunks_data = json.loads(chunks_bytes.decode('utf-8'))
            chunking_result = ChunkingResult(**chunks_data)
            return chunking_result.chunks
        except Exception as e:
            print(f"[Summarization] Failed to load chunks: {e}")
            return []
    
    async def _summarize_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Summarize each chunk using chunk summarization prompt.
        
        Args:
            chunks: List of chunks to summarize
            
        Returns:
            List of chunk summaries
        """
        summaries = []
        
        for i, chunk in enumerate(chunks):
            print(f"[Summarization] Chunk {i+1}/{len(chunks)}...")
            
            # Build prompt for this chunk
            prompt = chunk_summarization_prompt(chunk.text, max_words=75)
            
            # Generate summary
            summary = await self.llm.generate_from_prompt(prompt, max_tokens=100)
            summaries.append(summary)
        
        return summaries
    
    async def _create_executive_summary(
        self,
        chunk_summaries: List[str],
        classification: str
    ) -> str:
        """Create executive summary from chunk summaries.
        
        Args:
            chunk_summaries: List of chunk summaries
            classification: Document classification
            
        Returns:
            Executive summary text
        """
        # Build executive summary prompt
        prompt = executive_summary_prompt(
            chunk_summaries=chunk_summaries,
            classification=classification,
            max_words=200
        )
        
        # Generate executive summary
        executive_summary = await self.llm.generate_from_prompt(prompt, max_tokens=300)
        
        return executive_summary
    
    async def _store_in_elasticsearch(
        self,
        document_id: int,
        case_id: int,
        document: Document,
        executive_summary: str,
        chunk_summaries: List[str],
        total_chunks: int
    ) -> None:
        """Update document in Elasticsearch with summary.
        
        Updates the existing document in "documents" index (created by DocumentIndexingService).
        Adds summary fields to the existing full_text/blocks document.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            document: Document model instance
            executive_summary: Executive summary text
            chunk_summaries: List of chunk summaries
            total_chunks: Number of chunks
        """
        # Ensure index exists
        await self.elasticsearch.create_index("documents")
        
        # Prepare update payload (only summary fields)
        update_payload = {
            "doc": {
                "executive_summary": executive_summary,
                "chunk_summaries": chunk_summaries,
                "total_chunks": total_chunks,
                "summarized_at": datetime.now().isoformat()
            }
        }
        
        # Update existing document (upsert in case indexing hasn't happened yet)
        await self.elasticsearch.client.update(
            index="documents",
            id=f"doc_{document_id}",
            body=update_payload,
            doc_as_upsert=True  # Create if doesn't exist (defensive)
        )
        
        print(f"[Elasticsearch] Updated doc {document_id} with summary")

