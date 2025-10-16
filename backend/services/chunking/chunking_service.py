"""Chunking service for orchestrating document chunking pipeline."""
import json
from infrastructure.storage import StorageClient
from infrastructure.pinecone_client import PineconeClient
from core.models.document import Document
from core.constants import DocumentStatus
from services.models.extraction_models import ExtractedDocument
from services.chunking.semantic_chunker import SemanticChunker
from services.chunking.models import ChunkingResult


class ChunkingService:
    """Orchestrates document chunking and storage.
    
    Pipeline:
    1. Load blocks.json from S3
    2. Run semantic chunker
    3. Save chunks.json to S3 (backup)
    4. Generate embeddings and store in Pinecone
    5. Update document status
    """
    
    # Pinecone index configuration
    # TODO: Move to config if we support multiple environments
    INDEX_NAME = "legal-docs-dev"
    EMBEDDING_DIMENSION = 768  # Legal-BERT dimension
    
    def __init__(self, storage_client: StorageClient, pinecone_client: PineconeClient):
        """Initialize chunking service.
        
        Args:
            storage_client: S3 storage client
            pinecone_client: Pinecone vector DB client
        """
        self.storage = storage_client
        self.pinecone = pinecone_client
        self.chunker = SemanticChunker()
    
    async def chunk_document(
        self,
        document_id: int,
        case_id: int,
        classification: str = None,
        content_category: str = None
    ) -> ChunkingResult:
        """Chunk a document and store in Pinecone.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            content_category: Content category
            
        Returns:
            ChunkingResult with chunks
        """
        # Update status
        document = await Document.get(id=document_id)
        document.status = DocumentStatus.CHUNKING
        await document.save()
        
        try:
            # Step 1: Load extraction from S3
            print(f"[Chunking] Loading extraction for doc {document_id}...")
            extracted = await self._load_extraction(document_id, case_id)
            
            # Step 2: Run semantic chunker
            print(f"[Chunking] Creating semantic chunks...")
            result = self.chunker.chunk(
                extracted=extracted,
                document_id=document_id,
                case_id=case_id,
                classification=classification,
                content_category=content_category
            )
            
            print(f"[Chunking] Created {result.total_chunks} chunks")
            
            # Step 3: Save chunks.json to S3 (backup)
            print(f"[Chunking] Saving chunks.json to S3...")
            await self._save_chunks_to_s3(result, document_id, case_id)
            
            # Step 4: Store in Pinecone
            print(f"[Chunking] Storing chunks in Pinecone...")
            await self._store_in_pinecone(result)
            
            # Step 5: Update document status
            document.status = DocumentStatus.EMBEDDING  # Or COMPLETED if no embedding step
            await document.save()
            
            print(f"[Chunking] Document {document_id} chunking complete!")
            return result
            
        except Exception as e:
            # Mark as failed
            document.status = DocumentStatus.FAILED
            document.processing_error = f"Chunking failed: {str(e)}"
            await document.save()
            raise
    
    async def _load_extraction(self, document_id: int, case_id: int) -> ExtractedDocument:
        """Load blocks.json from S3.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            ExtractedDocument
        """
        extraction_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
        
        extraction_bytes = await self.storage.download(
            bucket_name="cases",
            object_name=extraction_key
        )
        
        extraction_data = json.loads(extraction_bytes.decode('utf-8'))
        return ExtractedDocument(**extraction_data)
    
    async def _save_chunks_to_s3(self, result: ChunkingResult, document_id: int, case_id: int) -> None:
        """Save chunks.json to S3 as backup.
        
        Args:
            result: Chunking result
            document_id: Document ID
            case_id: Case ID
        """
        chunks_key = f"{case_id}/documents/{document_id}/chunks/chunks.json"
        
        # Convert to JSON
        chunks_json = result.model_dump_json(indent=2)
        
        await self.storage.upload(
            bucket_name="cases",
            object_name=chunks_key,
            data=chunks_json.encode('utf-8')
        )
    
    async def _store_in_pinecone(self, result: ChunkingResult) -> None:
        """Store chunks in Pinecone with embeddings.
        
        Args:
            result: Chunking result
        """
        # Ensure index exists
        await self._ensure_index_exists()
        
        # Generate embeddings for all chunks
        texts = [chunk.text for chunk in result.chunks]
        embeddings = self.chunker.model.encode(texts, show_progress_bar=False)
        
        # Prepare vectors for Pinecone
        vectors = []
        for i, chunk in enumerate(result.chunks):
            vector = {
                "id": chunk.chunk_id,
                "values": embeddings[i].tolist(),
                "metadata": {
                    "case_id": chunk.case_id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text[:1000],  # Store preview (Pinecone metadata limit)
                    "document_filename": chunk.document_filename,
                    "classification": chunk.classification,
                    "page_numbers": chunk.page_numbers,
                    "block_ids": chunk.block_ids,
                    "token_count": chunk.token_count,
                    "content_category": chunk.content_category
                }
            }
            vectors.append(vector)
        
        # Upsert to Pinecone (batch of 100 at a time)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            await self.pinecone.upsert_vectors(
                index_name=self.INDEX_NAME,
                vectors=batch
            )
        
        print(f"[Pinecone] Stored {len(vectors)} vectors in index '{self.INDEX_NAME}'")
    
    async def _ensure_index_exists(self) -> None:
        """Ensure Pinecone index exists, create if not.
        
        This is idempotent - safe to call multiple times.
        """
        await self.pinecone.create_index(
            index_name=self.INDEX_NAME,
            dimension=self.EMBEDDING_DIMENSION,
            metric="cosine"
        )

