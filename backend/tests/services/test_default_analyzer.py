"""
Tests for DefaultAnalyzer.

Tests the fallback analyzer that handles documents without specific analyzers.
Should only filter obvious junk (empty, corrupted), not relevancy.
"""
import pytest
from services.content_analysis import DefaultAnalyzer, ContentCategory
from core.constants import SupportedFileType


@pytest.fixture
def default_analyzer():
    """Create DefaultAnalyzer instance."""
    return DefaultAnalyzer()


@pytest.mark.asyncio
class TestDefaultAnalyzer:
    """Test default analyzer fallback behavior."""
    
    async def test_accepts_normal_text_document(self, default_analyzer):
        """Should accept normal text content."""
        content = """This is a memo about the quarterly results.
        
The revenue for Q3 was $5M, up from $4M in Q2.
We need to discuss the budget allocation for next quarter.
Please review the attached spreadsheet."""
        
        decision = await default_analyzer.analyze(content, {"filename": "memo.txt"})
        
        assert decision.should_process is True
        assert decision.category == ContentCategory.UNKNOWN
        assert decision.confidence > 0.5
        assert "valid content" in decision.reasoning.lower()
    
    async def test_rejects_empty_file(self, default_analyzer):
        """Should reject completely empty files."""
        content = ""
        
        decision = await default_analyzer.analyze(content, {"filename": "empty.txt"})
        
        assert decision.should_process is False
        assert decision.category == ContentCategory.JUNK
        assert "empty" in decision.reasoning.lower()
        assert decision.confidence > 0.8
    
    async def test_rejects_whitespace_only_file(self, default_analyzer):
        """Should reject files with only whitespace."""
        content = "   \n\n  \t\t  \n   "
        
        decision = await default_analyzer.analyze(content, {"filename": "blank.txt"})
        
        assert decision.should_process is False
        assert decision.category == ContentCategory.JUNK
        assert "empty" in decision.reasoning.lower() or "minimal" in decision.reasoning.lower()
    
    async def test_rejects_very_short_file(self, default_analyzer):
        """Should reject files with very little content."""
        content = "Hi"
        
        decision = await default_analyzer.analyze(content, {"filename": "short.txt"})
        
        assert decision.should_process is False
        assert decision.category == ContentCategory.JUNK
        assert decision.confidence > 0.8
    
    async def test_accepts_file_just_above_minimum(self, default_analyzer):
        """Should accept files just above the minimum length threshold."""
        # Create content just over 50 chars
        content = "This is a test document with enough content to pass the minimum length check."
        
        decision = await default_analyzer.analyze(content, {"filename": "test.txt"})
        
        assert decision.should_process is True
        assert decision.category == ContentCategory.UNKNOWN
    
    async def test_rejects_corrupted_binary_content(self, default_analyzer):
        """Should reject content that's mostly binary/non-printable."""
        # Mostly binary with minimal text (less than 30% readable)
        binary_data = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f" * 50
        content = binary_data + "text"  # Only ~4 readable chars out of 650+
        
        decision = await default_analyzer.analyze(content, {"filename": "corrupt.bin"})
        
        assert decision.should_process is False
        assert decision.category == ContentCategory.JUNK
        assert "corrupted" in decision.reasoning.lower() or "binary" in decision.reasoning.lower()
    
    async def test_accepts_long_readable_content(self, default_analyzer):
        """Should accept longer documents with readable content."""
        content = """
        Meeting Notes - Project Status Update
        
        Date: October 15, 2024
        Attendees: John, Jane, Bob
        
        Discussion Points:
        1. Project timeline is on track
        2. Budget review scheduled for next week
        3. Client feedback has been positive
        
        Action Items:
        - John to prepare presentation
        - Jane to review contracts
        - Bob to update project plan
        
        Next meeting: October 22, 2024
        """
        
        decision = await default_analyzer.analyze(content, {"filename": "meeting_notes.txt"})
        
        assert decision.should_process is True
        assert decision.category == ContentCategory.UNKNOWN
        assert decision.confidence >= 0.5
    
    async def test_can_analyze_always_returns_true(self, default_analyzer):
        """Should accept any file type as fallback."""
        # Test various file types
        file_types = [SupportedFileType.PDF, SupportedFileType.TXT, 
                     SupportedFileType.DOCX, SupportedFileType.HTML]
        
        for file_type in file_types:
            can_analyze = default_analyzer.can_analyze(file_type, "some content")
            assert can_analyze is True, f"Should handle {file_type} as fallback"
    
    async def test_accepts_content_with_special_characters(self, default_analyzer):
        """Should accept content with special characters and formatting."""
        content = """
        Contract Review Notes
        
        § 1.1 - Definitions are clear
        § 2.3 - Payment terms: $100,000 + 5% fee
        
        Issues found:
        • Ambiguous termination clause
        • Missing force majeure provision
        
        Recommendation: Request amendments before signing.
        """
        
        decision = await default_analyzer.analyze(content, {"filename": "review.txt"})
        
        assert decision.should_process is True
        assert decision.category == ContentCategory.UNKNOWN
    
    async def test_confidence_levels_are_reasonable(self, default_analyzer):
        """All decisions should have reasonable confidence levels."""
        test_cases = [
            ("", 0.9),  # Empty - high confidence it's junk
            ("Valid content here with enough text to pass", 0.6),  # Valid - moderate confidence
            ("\x00" * 100, 0.8),  # Binary - high confidence it's junk
        ]
        
        for content, min_confidence in test_cases:
            decision = await default_analyzer.analyze(content, {})
            assert decision.confidence >= min_confidence, \
                f"Confidence {decision.confidence} too low for: {content[:20]}"
            assert decision.confidence <= 1.0, "Confidence cannot exceed 1.0"
    
    async def test_reasoning_always_provided(self, default_analyzer):
        """All decisions should include reasoning."""
        test_contents = [
            "",
            "Valid content",
            "\x00\x00\x00",
            "A" * 1000,
        ]
        
        for content in test_contents:
            decision = await default_analyzer.analyze(content, {})
            assert decision.reasoning, "Reasoning should always be provided"
            assert len(decision.reasoning) > 10, "Reasoning should be descriptive"

