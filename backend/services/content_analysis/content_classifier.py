"""Content classifier for categorizing documents.

Determines what type of content a document contains (email, contract, memo, etc.)
Uses LLM with multiple fallback strategies to handle edge cases.
"""
import json
from typing import Optional
from ollama import AsyncClient
from infrastructure.storage import StorageClient
from core.models.document import Document
from core.constants import DocumentStatus
from prompts.content_analysis import content_classification_prompt


class ClassificationResult:
    """Result from classification attempt."""
    
    def __init__(self, category: str, confidence: float, is_confident: bool = None):
        self.category = category
        self.confidence = confidence
        # Auto-determine if confident (>= 0.7)
        self.is_confident = is_confident if is_confident is not None else (confidence >= 0.7)


class ContentClassifier:
    """Classifies document content into categories.
    
    Uses multiple sampling strategies to handle edge cases:
    1. First section (0-50KB) - most documents
    2. Middle section (future) - for documents with blank first pages
    3. OCR (future) - for scanned/image documents
    
    Public interface is simple: classify() returns a category string.
    Internal strategies are tried sequentially until confident classification.
    """
    
    # Sample sizes for different strategies
    FIRST_SECTION_SIZE = 50_000  # 50KB - first attempt
    MIDDLE_SECTION_OFFSET = 100_000  # Skip first 100KB if blank
    MIDDLE_SECTION_SIZE = 50_000  # 50KB from middle
    
    def __init__(self, storage_client: StorageClient):
        """Initialize classifier with storage client."""
        self.storage = storage_client
        self.llm_client = AsyncClient()
    
    async def classify(self, document_id: int) -> str:
        """Classify document content into a category.
        
        Tries multiple strategies internally to handle edge cases.
        
        Args:
            document_id: ID of document to classify
            
        Returns:
            Category string (e.g., "email", "contract", "memo", "unreadable")
        """
        document = await Document.get(id=document_id)
        
        # Strategy 1: Try first section (handles 95% of cases)
        result = await self._try_first_section(document)
        if result.is_confident:
            return result.category
        
        # Strategy 2 (future): Try middle section (blank first page)
        # result = await self._try_middle_section(document)
        # if result.is_confident:
        #     return result.category
        
        # Strategy 3 (future): OCR for scanned documents
        # if document.file_type == "pdf":
        #     result = await self._try_ocr(document)
        #     if result.is_confident:
        #         return result.category
        
        # All strategies exhausted - return whatever we got or "unreadable"
        if result.category and result.category != "uncertain":
            return result.category
        
        return "unreadable"
    
    async def _try_first_section(self, document: Document) -> ClassificationResult:
        """Strategy 1: Classify from first 50KB of document.
        
        Args:
            document: Document model instance
            
        Returns:
            ClassificationResult with category and confidence
        """
        try:
            # Download first section (or entire file if smaller)
            content_bytes = await self.storage.download_partial(
                bucket_name=document.minio_bucket,
                object_name=document.minio_key,
                offset=0,
                length=self.FIRST_SECTION_SIZE
            )
            
            # Decode to text
            text_sample = content_bytes.decode('utf-8', errors='ignore')
            
            # Check if mostly blank/whitespace
            if len(text_sample.strip()) < 100:
                # Too little content to classify
                return ClassificationResult(
                    category="uncertain",
                    confidence=0.3,
                    is_confident=False
                )
            
            # Ask LLM to classify
            return await self._classify_with_llm(text_sample)
            
        except Exception as e:
            # If download or processing fails
            return ClassificationResult(
                category="uncertain",
                confidence=0.1,
                is_confident=False
            )
    
    async def _classify_with_llm(self, text_sample: str) -> ClassificationResult:
        """Use LLM to classify content.
        
        Args:
            text_sample: Text content to classify
            
        Returns:
            ClassificationResult with category and confidence
        """
        # Build prompt
        prompt = content_classification_prompt(text_sample)
        
        # Call LLM
        response = await self.llm_client.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        # Parse response
        try:
            result = json.loads(response['message']['content'])
            
            # Validate required fields
            if 'category' not in result or 'confidence' not in result:
                return ClassificationResult(
                    category="uncertain",
                    confidence=0.2,
                    is_confident=False
                )
            
            return ClassificationResult(
                category=result['category'],
                confidence=result['confidence'] / 10.0  # Convert 0-10 to 0.0-1.0
            )
            
        except json.JSONDecodeError:
            # LLM returned invalid JSON
            return ClassificationResult(
                category="uncertain",
                confidence=0.2,
                is_confident=False
            )
    
    # Future strategies (placeholders for extensibility)
    
    async def _try_middle_section(self, document: Document) -> ClassificationResult:
        """Strategy 2: Skip first pages, classify from middle section.
        
        Useful for documents with blank cover pages.
        
        Args:
            document: Document model instance
            
        Returns:
            ClassificationResult with category and confidence
        """
        # TODO: Implement when needed
        # Similar to _try_first_section but with offset
        return ClassificationResult(category="uncertain", confidence=0.0, is_confident=False)
    
    async def _try_ocr(self, document: Document) -> ClassificationResult:
        """Strategy 3: Use OCR for scanned/image documents.
        
        Args:
            document: Document model instance
            
        Returns:
            ClassificationResult with category and confidence
        """
        # TODO: Implement in Phase 2 when OCR is added
        return ClassificationResult(category="uncertain", confidence=0.0, is_confident=False)

