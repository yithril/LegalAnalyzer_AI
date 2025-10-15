"""
Tests for EmailAnalyzer using REAL email samples.

Tests classification of spam vs. legitimate business emails using actual
email files from the Enron dataset.
"""
import pytest
from pathlib import Path
from services.content_analysis import EmailAnalyzer, ContentCategory
from core.constants import SupportedFileType


@pytest.fixture
def email_analyzer():
    """Create EmailAnalyzer instance."""
    return EmailAnalyzer()


@pytest.fixture
def sample_files_dir():
    """Path to sample email files."""
    return Path(__file__).parent.parent / "helpers" / "sample_files"


def load_email_file(sample_files_dir: Path, filename: str) -> str:
    """Load email content from file."""
    file_path = sample_files_dir / filename
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.mark.asyncio
class TestEmailAnalyzer:
    """Test email classification with real emails."""
    
    async def test_detects_spam_email_1(self, email_analyzer, sample_files_dir):
        """Should detect spam.txt as spam."""
        # Load spam email
        spam_content = load_email_file(sample_files_dir, "spam.txt")
        
        # Analyze
        decision = await email_analyzer.analyze(spam_content, {"filename": "spam.txt"})
        
        # Verify it's classified as spam
        assert decision.should_process is False, "Spam should not be processed"
        assert decision.category == ContentCategory.SPAM_EMAIL, f"Expected SPAM_EMAIL, got {decision.category}"
        assert decision.confidence > 0.5, "Should have reasonable confidence"
        assert "spam" in decision.reasoning.lower(), f"Reasoning should mention spam: {decision.reasoning}"
        
        print(f"\n[PASS] Spam 1 detected: {decision.reasoning} (confidence: {decision.confidence:.2f})")
    
    async def test_detects_spam_email_2(self, email_analyzer, sample_files_dir):
        """Should detect spam2.txt as spam."""
        spam_content = load_email_file(sample_files_dir, "spam2.txt")
        
        decision = await email_analyzer.analyze(spam_content, {"filename": "spam2.txt"})
        
        assert decision.should_process is False, "Spam should not be processed"
        assert decision.category == ContentCategory.SPAM_EMAIL, f"Expected SPAM_EMAIL, got {decision.category}"
        assert decision.confidence > 0.5, "Should have reasonable confidence"
        
        print(f"\n[PASS] Spam 2 detected: {decision.reasoning} (confidence: {decision.confidence:.2f})")
    
    async def test_accepts_real_business_email_1(self, email_analyzer, sample_files_dir):
        """Should accept real_email.txt as legitimate."""
        real_content = load_email_file(sample_files_dir, "real_email.txt")
        
        decision = await email_analyzer.analyze(real_content, {"filename": "real_email.txt"})
        
        assert decision.should_process is True, "Real business email should be processed"
        assert decision.category == ContentCategory.BUSINESS_EMAIL, f"Expected BUSINESS_EMAIL, got {decision.category}"
        assert decision.confidence > 0.5, "Should have reasonable confidence"
        
        print(f"\n[PASS] Real email 1 accepted: {decision.reasoning} (confidence: {decision.confidence:.2f})")
    
    async def test_accepts_real_business_email_2(self, email_analyzer, sample_files_dir):
        """Should accept real_email2.txt as legitimate."""
        real_content = load_email_file(sample_files_dir, "real_email2.txt")
        
        decision = await email_analyzer.analyze(real_content, {"filename": "real_email2.txt"})
        
        assert decision.should_process is True, "Real business email should be processed"
        assert decision.category == ContentCategory.BUSINESS_EMAIL, f"Expected BUSINESS_EMAIL, got {decision.category}"
        assert decision.confidence > 0.5, "Should have reasonable confidence"
        
        print(f"\n[PASS] Real email 2 accepted: {decision.reasoning} (confidence: {decision.confidence:.2f})")
    
    async def test_can_analyze_detects_email_format(self, email_analyzer):
        """Should detect email format from headers."""
        email_content = """From: john@example.com
To: jane@example.com
Subject: Meeting Tomorrow
Date: Mon, 15 Oct 2024

Let's meet at 2pm."""
        
        # Should recognize this as email
        can_analyze = email_analyzer.can_analyze(SupportedFileType.TXT, email_content)
        assert can_analyze is True, "Should recognize email headers"
    
    async def test_can_analyze_rejects_non_email(self, email_analyzer):
        """Should not analyze non-email content."""
        non_email_content = """This is just a regular document.
It has no email headers.
Just plain text."""
        
        can_analyze = email_analyzer.can_analyze(SupportedFileType.TXT, non_email_content)
        assert can_analyze is False, "Should not recognize as email"
    
    async def test_all_emails_have_reasoning(self, email_analyzer, sample_files_dir):
        """All classifications should include reasoning."""
        emails = ["spam.txt", "spam2.txt", "real_email.txt", "real_email2.txt"]
        
        for email_file in emails:
            content = load_email_file(sample_files_dir, email_file)
            decision = await email_analyzer.analyze(content, {"filename": email_file})
            
            assert decision.reasoning, f"{email_file} should have reasoning"
            assert len(decision.reasoning) > 10, f"{email_file} reasoning should be descriptive"
            assert decision.confidence >= 0.0 and decision.confidence <= 1.0, \
                f"{email_file} confidence should be between 0 and 1"
    
    async def test_confidence_scores_are_reasonable(self, email_analyzer, sample_files_dir):
        """Confidence scores should be in reasonable range."""
        emails = ["spam.txt", "spam2.txt", "real_email.txt", "real_email2.txt"]
        
        confidences = []
        for email_file in emails:
            content = load_email_file(sample_files_dir, email_file)
            decision = await email_analyzer.analyze(content, {"filename": email_file})
            confidences.append(decision.confidence)
            
            # Confidence should be reasonable (not too low)
            assert decision.confidence >= 0.3, \
                f"{email_file} confidence too low: {decision.confidence}"
        
        # Average confidence should be decent
        avg_confidence = sum(confidences) / len(confidences)
        assert avg_confidence >= 0.5, f"Average confidence too low: {avg_confidence:.2f}"
        
        print(f"\n[INFO] Average confidence across all emails: {avg_confidence:.2f}")

