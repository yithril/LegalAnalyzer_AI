"""Service for extracting timeline events from legal documents."""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from infrastructure.storage import StorageClient
from core.models.document import Document
from core.models.case import Case
from core.models.timeline import TimelineEvent
from services.models.extraction_models import ExtractedDocument
from services.summarization.llama_client import get_llama_client
from prompts.timeline.fact_extraction import fact_extraction_prompt
from prompts.timeline.legal_analysis import legal_analysis_prompt


class TemporalInfo(BaseModel):
    """Temporal information about an event."""
    date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD) or null")
    date_end: Optional[str] = Field(None, description="End date for ranges, or null")
    precision: str = Field("unknown", description="exact|day|month|year|approximate|unknown")
    original_text: Optional[str] = Field(None, description="Original date text from document")


class ExtractedFact(BaseModel):
    """A single factual event extracted from a document."""
    actors: Optional[List[str]] = Field(None, description="Who was involved")
    action: str = Field(..., description="What happened")
    object_affected: Optional[str] = Field(None, description="What was affected")
    temporal: TemporalInfo = Field(default_factory=TemporalInfo, description="When it happened")
    extracted_text: str = Field(..., description="Original text snippet from document")
    confidence: int = Field(50, ge=0, le=100, description="Confidence in extraction (0-100)")


class FactExtractionResult(BaseModel):
    """Result of fact extraction from a document."""
    events: List[ExtractedFact] = Field(default_factory=list, description="List of extracted events")


class LegalAnalysisResult(BaseModel):
    """Result of legal significance analysis for an event."""
    legal_significance_score: int = Field(..., ge=0, le=100, description="Legal significance score (0-100)")
    state_changes: List[str] = Field(default_factory=list, description="Categories of state change triggered")
    reasoning: str = Field(..., description="Explanation for the score")
    key_factors: List[str] = Field(default_factory=list, description="Key factors influencing the score")
    
    @property
    def timeline_worthy(self) -> bool:
        """Calculate if event is timeline-worthy based on score threshold."""
        return self.legal_significance_score >= 50


class TimelineService:
    """Service for extracting timeline events from documents."""
    
    def __init__(self, storage_client: StorageClient):
        """Initialize timeline service."""
        self.storage = storage_client
        self.llm = get_llama_client()
        self.PREVIEW_MAX_CHARS = 4000  # More text for fact extraction
    
    async def extract_facts(
        self,
        document_id: int,
        case_id: int
    ) -> FactExtractionResult:
        """
        Extract factual events from a document.
        
        This is the first step in timeline construction - pure fact extraction.
        The legal analysis agent will later evaluate which facts are timeline-worthy.
        
        Args:
            document_id: Document to extract from
            case_id: Case context
            
        Returns:
            FactExtractionResult with list of extracted events (0-N)
        """
        print(f"[Timeline] Extracting facts from document {document_id}...")
        
        # Load document and case
        document = await Document.get(id=document_id)
        case = await Case.get(id=case_id)
        
        # Load full document text (or preview if too long)
        document_text = await self._load_document_text(document_id, case_id)
        
        # Extract metadata (especially for emails)
        metadata = await self._extract_metadata(document_id, case_id, document.classification)
        
        # Build prompt
        prompt = fact_extraction_prompt(
            case_name=case.name,
            case_description=case.description or "No description provided",
            document_classification=document.classification or "unknown",
            document_text=document_text,
            document_metadata=metadata
        )
        
        # Call LLM
        try:
            llm_response = await self.llm.client.chat(
                model='llama3.1:8b',
                messages=[{'role': 'user', 'content': prompt}],
                format='json',  # Force JSON output
                options={'temperature': 0.2, 'num_predict': 800}  # Low temp for factual extraction
            )
            
            response = llm_response['message']['content']
            result = self._parse_response(response)
            
            print(f"[Timeline] Extracted {len(result.events)} events from document {document_id}")
            return result
            
        except Exception as e:
            print(f"[Timeline] Error extracting facts from document {document_id}: {e}")
            # Return empty result on error
            return FactExtractionResult(events=[])
    
    async def _load_document_text(self, document_id: int, case_id: int, max_chars: int = 4000) -> str:
        """
        Load document text from blocks.
        
        Args:
            document_id: Document ID
            case_id: Case ID
            max_chars: Maximum characters to load
            
        Returns:
            Document text (full or truncated)
        """
        blocks_key = f"{case_id}/documents/{document_id}/extraction/blocks.json"
        blocks_bytes = await self.storage.download(
            bucket_name="cases",
            object_name=blocks_key
        )
        blocks_data = json.loads(blocks_bytes.decode('utf-8'))
        extracted = ExtractedDocument(**blocks_data)
        
        # Concatenate all blocks
        text_parts = []
        char_count = 0
        
        for page in extracted.pages:
            for block in page.blocks:
                if block.text and block.text.strip():
                    text_to_add = block.text
                    if char_count + len(text_to_add) > max_chars:
                        text_to_add = text_to_add[:max_chars - char_count]
                        text_parts.append(text_to_add)
                        text_parts.append("\n\n[Document truncated for length...]")
                        return "\n\n".join(text_parts)
                    
                    text_parts.append(text_to_add)
                    char_count += len(text_to_add)
        
        return "\n\n".join(text_parts)
    
    async def _extract_metadata(
        self,
        document_id: int,
        case_id: int,
        classification: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract metadata from document (especially email headers).
        
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
                    
                    # Extract common headers
                    for line in first_block_text.split('\n')[:20]:
                        if line.startswith('From:'):
                            metadata['from'] = line.replace('From:', '').strip()
                        elif line.startswith('To:'):
                            metadata['to'] = line.replace('To:', '').strip()
                        elif line.startswith('Subject:'):
                            metadata['subject'] = line.replace('Subject:', '').strip()
                        elif line.startswith('Date:'):
                            metadata['date'] = line.replace('Date:', '').strip()
                        elif line.startswith('Cc:'):
                            metadata['cc'] = line.replace('Cc:', '').strip()
            except:
                pass  # If metadata extraction fails, return empty
        
        return metadata
    
    def _parse_response(self, response_str: str) -> FactExtractionResult:
        """
        Parse LLM's JSON response for fact extraction.
        
        Args:
            response_str: JSON string from LLM
            
        Returns:
            FactExtractionResult with extracted events
        """
        # Remove markdown code blocks if present
        if response_str.startswith("```json") and response_str.endswith("```"):
            response_str = response_str[7:-3].strip()
        elif response_str.startswith("```") and response_str.endswith("```"):
            response_str = response_str[3:-3].strip()
        
        try:
            data = json.loads(response_str)
            return FactExtractionResult(**data)
        except Exception as e:
            print(f"[Timeline] Failed to parse LLM response: {e}")
            print(f"[Timeline] Response was: {response_str[:200]}...")
            return FactExtractionResult(events=[])
    
    async def analyze_legal_significance(
        self,
        event: ExtractedFact,
        document_id: int,
        case_id: int
    ) -> LegalAnalysisResult:
        """
        Analyze the legal significance of an extracted event.
        
        Determines whether the event changes the legal state of the case
        and should be included in the timeline.
        
        Args:
            event: The extracted event to analyze
            document_id: Source document ID
            case_id: Case context
            
        Returns:
            LegalAnalysisResult with score and decision
        """
        print(f"[Timeline] Analyzing legal significance of event: {event.action[:50]}...")
        
        # Load document and case
        document = await Document.get(id=document_id)
        case = await Case.get(id=case_id)
        
        # Load full document text for context
        full_context = await self._load_document_text(document_id, case_id)
        
        # Build prompt
        prompt = legal_analysis_prompt(
            case_name=case.name,
            case_description=case.description or "No description provided",
            document_classification=document.classification or "unknown",
            event_actors=", ".join(event.actors) if event.actors else "Unknown",
            event_action=event.action,
            event_object=event.object_affected or "Not specified",
            event_date=event.temporal.date or event.temporal.original_text or "Date unknown",
            full_document_context=full_context
        )
        
        # Call LLM
        try:
            llm_response = await self.llm.client.chat(
                model='llama3.1:8b',
                messages=[{'role': 'user', 'content': prompt}],
                format='json',  # Force JSON output
                options={'temperature': 0.3, 'num_predict': 300}
            )
            
            response = llm_response['message']['content']
            result = self._parse_legal_analysis(response)
            
            print(f"[Timeline] Legal significance score: {result.legal_significance_score}/100 "
                  f"(timeline_worthy: {result.timeline_worthy})")
            
            return result
            
        except Exception as e:
            print(f"[Timeline] Error analyzing legal significance: {e}")
            # Default to not including in timeline on error
            return LegalAnalysisResult(
                legal_significance_score=0,
                state_changes=[],
                reasoning="Analysis failed - defaulting to not timeline-worthy",
                key_factors=["error"]
            )
    
    def _parse_legal_analysis(self, response_str: str) -> LegalAnalysisResult:
        """
        Parse LLM's JSON response for legal analysis.
        
        Args:
            response_str: JSON string from LLM
            
        Returns:
            LegalAnalysisResult
        """
        # Remove markdown code blocks if present
        if response_str.startswith("```json") and response_str.endswith("```"):
            response_str = response_str[7:-3].strip()
        elif response_str.startswith("```") and response_str.endswith("```"):
            response_str = response_str[3:-3].strip()
        
        try:
            data = json.loads(response_str)
            return LegalAnalysisResult(**data)
        except Exception as e:
            print(f"[Timeline] Failed to parse legal analysis response: {e}")
            print(f"[Timeline] Response was: {response_str[:200]}...")
            return LegalAnalysisResult(
                legal_significance_score=0,
                state_changes=[],
                reasoning="Failed to parse LLM response",
                key_factors=["parse_error"]
            )
    
    async def save_timeline_event(
        self,
        extracted_fact: ExtractedFact,
        legal_analysis: LegalAnalysisResult,
        document_id: int,
        case_id: int
    ) -> Optional[TimelineEvent]:
        """
        Save a timeline event to the database.
        
        Only saves if legal_analysis.timeline_worthy is True (score >= 50).
        
        Args:
            extracted_fact: Facts extracted from document
            legal_analysis: Legal significance analysis
            document_id: Source document ID
            case_id: Case ID
            
        Returns:
            TimelineEvent if saved, None if not timeline-worthy
        """
        # Check if timeline-worthy
        if not legal_analysis.timeline_worthy:
            print(f"[Timeline] Event not saved - score {legal_analysis.legal_significance_score} below threshold")
            return None
        
        print(f"[Timeline] Saving timeline event (score: {legal_analysis.legal_significance_score}/100)...")
        
        # Parse date if available
        event_date = None
        if extracted_fact.temporal.date:
            try:
                event_date = datetime.strptime(extracted_fact.temporal.date, "%Y-%m-%d").date()
            except:
                pass  # Keep as None if parsing fails
        
        event_date_end = None
        if extracted_fact.temporal.date_end:
            try:
                event_date_end = datetime.strptime(extracted_fact.temporal.date_end, "%Y-%m-%d").date()
            except:
                pass
        
        # Create timeline event
        timeline_event = await TimelineEvent.create(
            case_id=case_id,
            document_id=document_id,
            # Facts
            actors=extracted_fact.actors,
            action=extracted_fact.action,
            object_affected=extracted_fact.object_affected,
            # Temporal
            event_date=event_date,
            event_date_end=event_date_end,
            date_precision=extracted_fact.temporal.precision,
            date_original_text=extracted_fact.temporal.original_text,
            # Legal analysis
            legal_significance_score=legal_analysis.legal_significance_score,
            state_changes=legal_analysis.state_changes,
            legal_reasoning=legal_analysis.reasoning,
            key_factors=legal_analysis.key_factors,
            # Context
            extracted_text=extracted_fact.extracted_text,
            extraction_confidence=extracted_fact.confidence
        )
        
        print(f"[Timeline] Saved timeline event {timeline_event.id}: {timeline_event.action[:50]}")
        return timeline_event

