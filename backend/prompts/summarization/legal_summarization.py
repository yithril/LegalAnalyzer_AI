"""Prompts for legal document summarization."""
from typing import List


def chunk_summarization_prompt(text: str, max_words: int = 75) -> str:
    """Generate prompt for summarizing a single chunk.
    
    Args:
        text: Chunk text to summarize
        max_words: Maximum words in summary
        
    Returns:
        Formatted prompt for the LLM
    """
    return f"""You are a legal document analyst. Summarize the following document section.

Focus on key information:
- Main topics and subjects
- Important facts, dates, or numbers
- Key parties or entities mentioned
- Critical obligations, rights, or terms

TEXT:
{text}

OUTPUT FORMAT:
Provide ONLY a clear, factual summary in {max_words} words or less. Be specific and use concrete terms that will be useful for searching later. Do not include preamble or meta-commentary.

SUMMARY:"""


def executive_summary_prompt(chunk_summaries: List[str], classification: str = "document", max_words: int = 200) -> str:
    """Generate prompt for creating executive summary from chunk summaries.
    
    Args:
        chunk_summaries: List of chunk summaries to synthesize
        classification: Document classification (e.g., "contract", "email")
        max_words: Maximum words in executive summary
        
    Returns:
        Formatted prompt for the LLM
    """
    # Combine summaries with section labels
    combined = "\n\n".join([
        f"Section {i+1}: {summary}"
        for i, summary in enumerate(chunk_summaries)
    ])
    
    return f"""You are a legal document analyst. Create a comprehensive executive summary of this {classification}.

Below are summaries of each section:

{combined}

OUTPUT FORMAT:
Write a clear, comprehensive executive summary ({max_words} words or less) that:
- Captures the main purpose and content of the document
- Includes specific names, dates, amounts, and key terms
- Uses clear, searchable language (avoid vague terms)
- Presents information in a flowing narrative (not bullet points)

Be specific and factual. This summary will be used for search, so include concrete details.

EXECUTIVE SUMMARY:"""

