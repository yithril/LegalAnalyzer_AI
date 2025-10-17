"""Prompt for scoring document relevance to a legal case."""


def case_relevance_prompt(
    case_name: str,
    case_description: str,
    document_preview: str,
    classification: str,
    document_metadata: dict = None
) -> str:
    """Generate prompt for LLM to score document relevance to a case.
    
    Args:
        case_name: Name of the legal case (e.g., "Smith v. Jones")
        case_description: Description of what the case is about
        document_preview: First ~2000 characters of the document
        classification: Document type ("email", "contract", etc.)
        document_metadata: Optional metadata (from, to, subject for emails, etc.)
        
    Returns:
        Formatted prompt string for LLM
    """
    
    # Build metadata section if available
    metadata_section = ""
    if document_metadata:
        metadata_section = "\nDOCUMENT METADATA:\n"
        if document_metadata.get("from"):
            metadata_section += f"From: {document_metadata['from']}\n"
        if document_metadata.get("to"):
            metadata_section += f"To: {document_metadata['to']}\n"
        if document_metadata.get("subject"):
            metadata_section += f"Subject: {document_metadata['subject']}\n"
        if document_metadata.get("date"):
            metadata_section += f"Date: {document_metadata['date']}\n"
    
    prompt = f"""You are a legal assistant analyzing document relevance for a case.

CASE INFORMATION:
Name: {case_name}
Description: {case_description}

DOCUMENT TO ANALYZE:
Type: {classification}{metadata_section}

CONTENT PREVIEW (first ~2000 characters):
{document_preview}

TASK:
Score this document's relevance to the case on a scale of 0-100.

SCORING GUIDE:
0-20: Completely unrelated 
  - Office gossip, personal emails, lunch plans
  - Topics unrelated to case issues
  - No connection to case parties or subject matter

21-40: Minimal relevance
  - General company policies not specific to case
  - Tangential mentions of parties
  - Background information only
  - May be from different timeframe but provides minimal context

41-60: Moderate relevance  
  - Related parties or topics mentioned
  - Provides useful context or background
  - May be before/after case timeframe but establishes relevant history
  - Helps understand case circumstances

61-80: Significant relevance
  - Directly mentions case parties, issues, or events
  - Strong topic/subject matter alignment
  - Useful supporting evidence
  - Timeframe alignment is a plus but not required

81-100: Critical relevance
  - Key evidence directly related to case claims
  - Smoking gun documents
  - Core contracts, decisions, or communications
  - Essential to case narrative
  - Direct involvement of case parties in case issues

IMPORTANT: 
- Focus on relevance to THIS SPECIFIC CASE, not general legal importance
- Consider multiple factors: parties, topics, events, relationships
- Timeframe is ONE factor - documents before/after case period can still be highly relevant
- Historical context and background can be valuable even from earlier periods
- Be balanced - don't over-score tangential content or under-score valuable context

CRITICAL: You MUST return ONLY the JSON object below. Do NOT include any explanatory text, markdown, or other content. Just the raw JSON.

{{
  "score": <integer 0-100>,
  "reasoning": "<brief 1-2 sentence explanation>",
  "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"]
}}"""
    
    return prompt

