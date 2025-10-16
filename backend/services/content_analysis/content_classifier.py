"""Content classifier for categorizing documents.

Determines what type of content a document contains (email, contract, memo, etc.)
Uses extracted document structure (blocks) for intelligent classification.
"""
import json
from ollama import AsyncClient
from infrastructure.storage import StorageClient
from core.models.document import Document
from services.models.extraction_models import ExtractedDocument
from prompts.content_analysis import content_classification_prompt


class ContentClassifier:
    """Classifies document content using extracted structure (blocks).
    
    Uses document blocks, pages, and metadata for intelligent classification.
    Advantages over raw text sampling:
    - Skips cover pages and noise (headers/footers)
    - Samples from multiple sections for long documents
    - Uses block metadata (headings, structure) for context
    """
    
    def __init__(self, storage_client: StorageClient):
        """Initialize classifier with storage client."""
        self.storage = storage_client
        self.llm_client = AsyncClient()
    
    async def classify(self, document_id: int, case_id: int) -> str:
        """Classify document content into a category.
        
        Args:
            document_id: ID of document to classify
            case_id: ID of case (for S3 path)
            
        Returns:
            Category string (e.g., "email", "contract", "memo", "unknown")
        """
        # Load extraction result from S3
        extraction_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
        
        try:
            extraction_bytes = await self.storage.download(
                bucket_name="cases",  # Assuming case bucket
                object_name=extraction_key
            )
            extraction_data = json.loads(extraction_bytes.decode('utf-8'))
            extracted = ExtractedDocument(**extraction_data)
        except Exception as e:
            # Extraction not available or failed to load
            print(f"Failed to load extraction for doc {document_id}: {e}")
            return "unknown"
        
        # Create intelligent sample from blocks
        sample_text = self._create_smart_sample(extracted)
        
        # If sample is too small, might be unreadable
        if len(sample_text.strip()) < 100:
            return "unreadable"
        
        # Classify using LLM
        return await self._classify_with_llm(sample_text)
    
    def _create_smart_sample(self, extracted: ExtractedDocument) -> str:
        """Create an intelligent sample from extracted document.
        
        Strategy:
        1. Find first "substantive" page (skip cover pages)
        2. Sample from beginning and middle (if long doc)
        3. Filter out headers/footers
        4. Include structure hints for LLM
        
        Args:
            extracted: Extracted document with pages and blocks
            
        Returns:
            Text sample with structure context
        """
        parts = []
        
        # Add document metadata for context
        parts.append(f"[Document: {extracted.page_count} pages, {extracted.total_blocks} blocks]")
        
        # Find substantive pages (skip cover pages with few text blocks)
        substantive_pages = []
        for page in extracted.pages:
            # Count non-noise blocks
            text_blocks = [
                b for b in page.blocks 
                if b.kind not in ['image', 'header', 'footer'] and b.text.strip()
            ]
            
            # Page is substantive if it has 3+ blocks OR 200+ tokens
            if len(text_blocks) >= 3 or (page.token_estimate or 0) > 200:
                substantive_pages.append(page)
        
        if not substantive_pages:
            # No substantive pages found - use first page anyway
            substantive_pages = extracted.pages[:1] if extracted.pages else []
        
        # Determine sampling strategy based on doc length
        # With 5000 token limit, we can afford to sample more generously
        if len(substantive_pages) <= 5:
            # Short doc - use all substantive pages
            pages_to_sample = substantive_pages
        elif len(substantive_pages) <= 15:
            # Medium doc - first 3 pages (get more context)
            pages_to_sample = substantive_pages[:3]
        else:
            # Long doc - beginning, middle, and a page from later section
            middle_idx = len(substantive_pages) // 2
            later_idx = int(len(substantive_pages) * 0.75)
            pages_to_sample = [
                substantive_pages[0],
                substantive_pages[middle_idx],
                substantive_pages[later_idx]
            ]
            parts.append("[Note: Long document, sampled from beginning, middle, and later section]")
        
        # Extract text from sampled pages
        token_count = 0
        max_tokens = 5000  # Maximize context for local model (no cost concern)
        
        for page in pages_to_sample:
            parts.append(f"\n--- Page {page.page_index + 1} ---")
            
            for block in page.blocks:
                # Skip noise blocks
                if block.kind in ['image', 'header', 'footer']:
                    continue
                
                # Skip empty blocks
                if not block.text or not block.text.strip():
                    continue
                
                # Check token limit
                if token_count + (block.token_estimate or 0) > max_tokens:
                    break
                
                # Add block with kind hint if it's structural
                if block.kind in ['heading', 'title']:
                    parts.append(f"[{block.kind.upper()}]: {block.text}")
                else:
                    parts.append(block.text)
                
                token_count += block.token_estimate or 0
            
            if token_count >= max_tokens:
                break
        
        return "\n".join(parts)
    
    async def _classify_with_llm(self, sample_text: str) -> str:
        """Use LLM to classify based on structured sample.
        
        Args:
            sample_text: Text sample with structure hints
            
        Returns:
            Category string
        """
        # Build prompt using existing prompt function
        prompt = content_classification_prompt(sample_text)
        
        try:
            # Call LLM
            response = await self.llm_client.chat(
                model='llama3.1:8b',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            
            # Parse response
            result = json.loads(response['message']['content'])
            
            # Validate and extract category
            if 'category' not in result:
                return "unknown"
            
            return result['category']
            
        except Exception as e:
            # If LLM fails for any reason, return unknown
            print(f"Classification LLM failed: {e}")
            return "unknown"

