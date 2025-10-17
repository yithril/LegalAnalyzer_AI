"""Service for scoring document relevance to a legal case."""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from infrastructure.storage import StorageClient
from core.models.document import Document
from core.models.case import Case
from services.models.extraction_models import ExtractedDocument
from services.summarization.llama_client import get_llama_client
from prompts.relevance import case_relevance_prompt


class RelevanceResult(BaseModel):
    """Result of relevance scoring."""
    score: int = Field(..., ge=0, le=100, description="Relevance score 0-100")
    reasoning: str = Field(..., description="Brief explanation of score")
    key_factors: list[str] = Field(default_factory=list, description="Key factors considered")


class RelevanceService:
    """Scores document relevance to a case using LLM analysis.
    
    Workflow:
    1. Load case description
    2. Load document preview (first ~2000 chars)
    3. Build prompt with case context
    4. Call LLM to score relevance (0-100)
    5. Parse and validate response
    6. Update document with score
    """
    
    def __init__(self, storage_client: StorageClient):
        """Initialize with storage client.
        
        Args:
            storage_client: S3 storage client for loading documents
        """
        self.storage = storage_client
        self.llm = get_llama_client()
    
    async def score_document_relevance(
        self,
        document_id: int,
        case_id: int
    ) -> RelevanceResult:
        """Score how relevant a document is to its case.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            
        Returns:
            RelevanceResult with score and reasoning
        """
        print(f"[Relevance] Scoring document {document_id} for case {case_id}...")
        
        # Load document and case
        document = await Document.get(id=document_id)
        case = await Case.get(id=case_id)
        
        # Load document preview
        preview = await self._load_document_preview(document_id, case_id)
        
        # Extract metadata for emails
        metadata = await self._extract_metadata(document_id, case_id, document.classification)
        
        # Build prompt
        prompt = case_relevance_prompt(
            case_name=case.name,
            case_description=case.description or "No description provided",
            document_preview=preview,
            classification=document.classification or "unknown",
            document_metadata=metadata
        )
        
        # Call LLM with JSON format enforcement
        try:
            # Use Ollama's JSON mode for guaranteed JSON output
            llm_response = await self.llm.client.chat(
                model='llama3.1:8b',
                messages=[{'role': 'user', 'content': prompt}],
                format='json',  # Ollama's JSON mode - guarantees valid JSON
                options={'temperature': 0.3, 'num_predict': 200}
            )
            
            response = llm_response['message']['content']
            result = self._parse_response(response)
            
            # Update document
            document.relevance_score = result.score
            document.relevance_reasoning = result.reasoning
            document.relevance_scored_at = datetime.now()
            await document.save()
            
            print(f"[Relevance] Score: {result.score}/100 - {result.reasoning}")
            return result
            
        except Exception as e:
            print(f"[Relevance] Scoring failed: {e}")
            # Default to moderate relevance if LLM fails
            default_result = RelevanceResult(
                score=50,
                reasoning="Automatic scoring failed - defaulted to moderate relevance",
                key_factors=["llm_error"]
            )
            document.relevance_score = 50
            document.relevance_reasoning = str(e)
            await document.save()
            return default_result
    
    async def _load_document_preview(
        self,
        document_id: int,
        case_id: int,
        max_chars: int = 2000
    ) -> str:
        """Load first ~2000 characters from document for preview.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            max_chars: Maximum characters to load
            
        Returns:
            Document preview text
        """
        # Load blocks from S3
        blocks_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
        blocks_bytes = await self.storage.download(
            bucket_name="cases",
            object_name=blocks_key
        )
        blocks_data = json.loads(blocks_bytes.decode('utf-8'))
        extracted = ExtractedDocument(**blocks_data)
        
        # Build preview from first blocks
        parts = []
        char_count = 0
        
        for page in extracted.pages[:2]:  # First 2 pages
            for block in page.blocks:
                if block.text and block.text.strip():
                    parts.append(block.text)
                    char_count += len(block.text)
                    
                    if char_count >= max_chars:
                        break
            
            if char_count >= max_chars:
                break
        
        preview = "\n\n".join(parts)
        return preview[:max_chars]  # Truncate to exact limit
    
    async def _extract_metadata(
        self,
        document_id: int,
        case_id: int,
        classification: Optional[str]
    ) -> Dict[str, Any]:
        """Extract metadata from document (especially emails).
        
        For emails, extract from/to/subject from header block.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            classification: Document classification
            
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        # Only extract email metadata for email documents
        if classification and "email" in classification.lower():
            try:
                blocks_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
                blocks_bytes = await self.storage.download(
                    bucket_name="cases",
                    object_name=blocks_key
                )
                blocks_data = json.loads(blocks_bytes.decode('utf-8'))
                extracted = ExtractedDocument(**blocks_data)
                
                # Look in first block for email headers
                if extracted.pages and extracted.pages[0].blocks:
                    first_block_text = extracted.pages[0].blocks[0].text
                    
                    # Simple header extraction (could be more sophisticated)
                    for line in first_block_text.split('\n')[:20]:  # First 20 lines
                        if line.startswith('From:'):
                            metadata['from'] = line.replace('From:', '').strip()
                        elif line.startswith('To:'):
                            metadata['to'] = line.replace('To:', '').strip()
                        elif line.startswith('Subject:'):
                            metadata['subject'] = line.replace('Subject:', '').strip()
                        elif line.startswith('Date:'):
                            metadata['date'] = line.replace('Date:', '').strip()
            except:
                pass  # If metadata extraction fails, just return empty
        
        return metadata
    
    def _parse_response(self, response: str) -> RelevanceResult:
        """Parse LLM response into RelevanceResult.
        
        Args:
            response: LLM response (should be JSON)
            
        Returns:
            RelevanceResult
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith('```'):
                # Remove ```json and ``` markers
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:].strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Validate and create result
            return RelevanceResult(
                score=max(0, min(100, int(data.get('score', 50)))),  # Clamp to 0-100
                reasoning=data.get('reasoning', 'No reasoning provided'),
                key_factors=data.get('key_factors', [])
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}\nResponse: {response}")

