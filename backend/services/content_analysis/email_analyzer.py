"""Email content analyzer using LLM for spam/quality detection."""
import json
from ollama import AsyncClient
from core.constants import SupportedFileType
from prompts.content_analysis import email_classification_prompt
from .base_analyzer import ContentAnalyzer, FilterDecision, ContentCategory


class EmailAnalyzer(ContentAnalyzer):
    """Analyzes email content using LLM.
    
    Detects spam and determines if email contains substantive business content.
    Uses Llama 3.1 8B for fast classification.
    """
    
    def can_analyze(self, file_type: SupportedFileType, content_preview: str) -> bool:
        """Check if content looks like an email.
        
        Looks for standard email headers: From, To, Subject, Date.
        
        Args:
            file_type: Detected file type (HTML or TXT usually for emails)
            content_preview: First ~500 chars
            
        Returns:
            True if content appears to be an email
        """
        # Email markers to look for
        email_markers = ["From:", "To:", "Subject:", "Date:"]
        
        # Check first 500 chars for email headers
        preview_upper = content_preview[:500].upper()
        marker_count = sum(1 for marker in email_markers if marker.upper() in preview_upper)
        
        # Need at least 2 markers to be confident it's an email
        return marker_count >= 2
    
    async def analyze(self, content_sample: str, metadata: dict) -> FilterDecision:
        """Use LLM to classify email and determine if it should be processed.
        
        Args:
            content_sample: Email content (first 50KB or so)
            metadata: Document metadata
            
        Returns:
            FilterDecision indicating if email should be processed
        """
        # Truncate to first 2000 chars for efficiency
        # (Most spam/quality signals are in the beginning)
        sample = content_sample[:2000]
        
        # Build prompt using imported prompt function
        prompt = email_classification_prompt(sample)
        
        # Call LLM using async client
        client = AsyncClient()
        response = await client.chat(
            model='llama3.1:8b',  # Use 8B model for speed
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        # Parse LLM response
        try:
            result = json.loads(response['message']['content'])
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return as unknown/junk
            return FilterDecision(
                should_process=False,
                category=ContentCategory.JUNK,
                reasoning=f"LLM returned invalid JSON: {str(e)}",
                confidence=0.3
            )
        
        # Validate required fields exist
        required_fields = ['is_spam', 'is_substantive', 'confidence']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            return FilterDecision(
                should_process=False,
                category=ContentCategory.JUNK,
                reasoning=f"LLM response missing fields: {', '.join(missing_fields)}",
                confidence=0.3
            )
        
        # Decision logic based on LLM classification
        if result['is_spam']:
            return FilterDecision(
                should_process=False,
                category=ContentCategory.SPAM_EMAIL,
                reasoning=f"Spam detected: {result.get('brief_reason', 'spam indicators present')}",
                confidence=result['confidence'] / 10.0
            )
        
        if result['is_substantive']:
            return FilterDecision(
                should_process=True,
                category=ContentCategory.BUSINESS_EMAIL,
                reasoning="Substantive business email",
                confidence=result['confidence'] / 10.0
            )
        
        # Not spam but not substantive either (empty/trivial/auto-reply)
        return FilterDecision(
            should_process=False,
            category=ContentCategory.JUNK,
            reasoning=f"Not substantive: {result.get('brief_reason', 'trivial content')}",
            confidence=result['confidence'] / 10.0
        )

