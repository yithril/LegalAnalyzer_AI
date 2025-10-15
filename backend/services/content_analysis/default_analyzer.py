"""Default analyzer for documents without specific analyzers.

Only filters obvious junk (empty, corrupted). Cannot determine relevancy
without full document context, so passes most content through.
"""
from core.constants import SupportedFileType
from .base_analyzer import ContentAnalyzer, FilterDecision, ContentCategory


class DefaultAnalyzer(ContentAnalyzer):
    """Fallback analyzer for documents without specific filtering rules.
    
    Philosophy: At preprocessing stage, only filter OBVIOUS junk.
    Relevancy analysis requires full document context (happens after extraction).
    
    Filters out:
    - Empty or near-empty files
    - Corrupted/unreadable content
    - Files that are mostly binary garbage
    
    Passes through:
    - Any readable text content (memos, reports, notes, etc.)
    - Content where relevancy can't be determined without full context
    """
    
    # Minimum content length to be considered valid
    MIN_CONTENT_LENGTH = 50
    
    # Minimum ratio of printable characters
    MIN_READABLE_RATIO = 0.3
    
    def can_analyze(self, file_type: SupportedFileType, content_preview: str) -> bool:
        """Default analyzer handles everything (fallback).
        
        This analyzer is always tried last - it accepts any content that
        didn't match a more specific analyzer.
        
        Returns:
            Always True (catchall)
        """
        return True
    
    async def analyze(self, content_sample: str, metadata: dict) -> FilterDecision:
        """Perform minimal filtering - only reject obvious junk.
        
        Args:
            content_sample: Text sample to analyze
            metadata: Document metadata
            
        Returns:
            FilterDecision - only rejects empty/corrupted content
        """
        # Strip whitespace for accurate length check
        content_stripped = content_sample.strip()
        
        # Check 1: Is file empty or nearly empty?
        if len(content_stripped) < self.MIN_CONTENT_LENGTH:
            return FilterDecision(
                should_process=False,
                category=ContentCategory.JUNK,
                reasoning=f"File appears empty or has minimal content ({len(content_stripped)} chars)",
                confidence=0.95
            )
        
        # Check 2: Is content readable (not corrupted/binary)?
        if len(content_sample) > 0:
            printable_count = sum(1 for c in content_sample if c.isprintable() or c.isspace())
            readable_ratio = printable_count / len(content_sample)
            
            if readable_ratio < self.MIN_READABLE_RATIO:
                return FilterDecision(
                    should_process=False,
                    category=ContentCategory.JUNK,
                    reasoning=f"Content appears corrupted or binary (only {readable_ratio:.0%} readable)",
                    confidence=0.90
                )
        
        # Content looks valid - let it through
        # We can't determine relevancy without full document context
        return FilterDecision(
            should_process=True,
            category=ContentCategory.UNKNOWN,
            reasoning="Valid content detected, no specific analyzer available",
            confidence=0.70
        )

