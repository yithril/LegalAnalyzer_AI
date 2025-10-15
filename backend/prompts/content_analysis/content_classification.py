"""Prompt for classifying document content type."""


def content_classification_prompt(content_sample: str) -> str:
    """Generate prompt for LLM content classification.
    
    Args:
        content_sample: Text sample from document
        
    Returns:
        Formatted prompt string for the LLM
    """
    return f"""You are a document classifier. Analyze the document sample below and determine what type of content it is.

DOCUMENT SAMPLE TO ANALYZE:
---
{content_sample}
---

COMMON CATEGORIES (but not limited to these):
- email: Email correspondence, messages
- contract: Legal contracts, agreements, terms of service
- court_filing: Court documents, motions, briefs, orders
- memo: Internal memos, notes, communications
- letter: Formal letters, correspondence
- financial_record: Bank statements, financial reports, invoices
- meeting_notes: Meeting minutes, notes, agendas
- presentation: Slides, presentations, decks
- report: Reports, analyses, summaries
- spreadsheet_data: Tabular data, lists
- form: Forms, applications, questionnaires
- certificate: Certificates, licenses, credentials
- policy: Policies, procedures, guidelines
- other: If none of the above fit, provide a descriptive category

INSTRUCTIONS:
1. Look at the structure, headers, and content
2. Determine the most appropriate category
3. If none of the common categories fit, create a descriptive category name (e.g., "company_policy", "training_material")
4. Provide your confidence level (0-10)

REQUIRED OUTPUT FORMAT:
You MUST respond with ONLY valid JSON. No other text. Use this EXACT structure:

{{
  "category": "category_name_here",
  "confidence": integer from 0 to 10,
  "reasoning": "brief explanation of classification"
}}

EXAMPLES:
{{"category": "email", "confidence": 9, "reasoning": "email headers and correspondence format"}}
{{"category": "contract", "confidence": 8, "reasoning": "legal agreement with parties and terms"}}
{{"category": "memo", "confidence": 7, "reasoning": "internal communication format"}}
{{"category": "unreadable", "confidence": 9, "reasoning": "content appears to be scanned image or corrupted text"}}

NOW CLASSIFY THE DOCUMENT ABOVE. Return ONLY the JSON object, nothing else:"""

