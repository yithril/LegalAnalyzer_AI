"""Prompt for extracting factual events from legal documents."""
from typing import Optional, Dict, Any


def fact_extraction_prompt(
    case_name: str,
    case_description: str,
    document_classification: str,
    document_text: str,
    document_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a prompt for extracting factual events from a document.
    
    The LLM should identify discrete events and extract:
    - Who (actors)
    - What (action)
    - What was affected (object)
    - When (temporal information)
    - Where in document (text snippet)
    
    Args:
        case_name: Name of the legal case
        case_description: Description of what the case is about
        document_classification: Type of document (email, contract, memo, etc.)
        document_text: Full text content of the document
        document_metadata: Optional metadata (email headers, dates, etc.)
        
    Returns:
        Formatted prompt string for the LLM
    """
    
    metadata_section = ""
    if document_metadata:
        metadata_section = "\nDOCUMENT METADATA:\n"
        for key, value in document_metadata.items():
            metadata_section += f"{key.title()}: {value}\n"
    
    prompt = f"""You are a legal assistant extracting factual events from documents for timeline construction.

CASE CONTEXT:
Case Name: {case_name}
Case Description: {case_description}

DOCUMENT TO ANALYZE:
Document Type: {document_classification}{metadata_section}

DOCUMENT TEXT:
---
{document_text}
---

YOUR TASK:
Extract ALL discrete events from this document. An event is something that happened at a specific time.

For EACH event, extract the 5 W's:
1. WHO - Actors involved (people, companies, organizations)
2. WHAT - The action that occurred (signed, sent, modified, approved, etc.)
3. WHAT AFFECTED - The object/subject of the action (contract, email, asset, etc.)
4. WHEN - Temporal information (exact date, date range, or "unknown" if not specified)
5. WHERE - Extract the exact text snippet from the document that describes this event

EXTRACTION RULES:
- Extract MULTIPLE events if document describes multiple distinct actions
- Include events even if some fields are missing (use null for unknown)
- Focus on ACTIONS that occurred, not general statements or background info
- If no clear events exist, return an empty list
- Be precise with dates - extract exact dates when available
- For date ranges, provide both start and end
- If only month/year given, note the precision level

EXAMPLES OF EVENTS:
[YES] "On Jan 7, Power Pool received acknowledgement" -> Event
[YES] "Contract 933 terminated Dec 28 HE 24" -> Event  
[NO] "Carol Moline is Financial Controller" -> NOT an event (just info)
[NO] "Please give me a call" -> NOT an event (request, not action)

OUTPUT INSTRUCTIONS:
You MUST return ONLY the JSON object below. 
Do NOT include any explanatory text, markdown formatting, or other content.
Just the raw JSON starting with {{ and ending with }}.

If no events found, return: {{"events": []}}

JSON SCHEMA:
{{
  "events": [
    {{
      "actors": ["Actor 1", "Actor 2"],  // List of strings or null
      "action": "verb phrase describing what happened",  // Required string
      "object_affected": "what was impacted",  // String or null
      "temporal": {{
        "date": "YYYY-MM-DD",  // ISO date string or null
        "date_end": "YYYY-MM-DD",  // For ranges, or null
        "precision": "exact",  // Must be one of: exact|day|month|year|approximate|unknown
        "original_text": "Dec 29 HE 1 2001"  // Exact date text from document
      }},
      "extracted_text": "verbatim quote from document",  // Required string
      "confidence": 85  // Integer 0-100
    }}
  ]
}}

EXAMPLE OUTPUT:
{{
  "events": [
    {{
      "actors": ["Power Pool of Alberta", "Enron Canada"],
      "action": "received acknowledgement of contract modification",
      "object_affected": "Contract 934 source asset change",
      "temporal": {{
        "date": "2002-01-07",
        "date_end": null,
        "precision": "exact",
        "original_text": "January 7"
      }},
      "extracted_text": "On January 7 the Power Pool received your acknowledgement of Enron's change in the source asset",
      "confidence": 95
    }}
  ]
}}"""
    
    return prompt

