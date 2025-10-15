"""Prompt for email classification (spam detection and quality assessment)."""


def email_classification_prompt(email_content: str) -> str:
    """Generate prompt for LLM email classification.
    
    Args:
        email_content: The email text to analyze
        
    Returns:
        Formatted prompt string for the LLM
    """
    return f"""You are an email classifier. Analyze the email below and determine if it is spam.

EMAIL TO ANALYZE:
---
{email_content}
---

CLASSIFICATION CRITERIA:
- Spam/Junk: marketing emails, promotional content, scams, phishing, unwanted solicitations
- Substantive: legitimate business communication, work-related correspondence, meaningful exchanges

REQUIRED OUTPUT FORMAT:
You MUST respond with ONLY valid JSON. No other text. Use this EXACT structure:

{{
  "is_spam": true or false,
  "is_substantive": true or false,
  "confidence": integer from 0 to 10,
  "brief_reason": "short explanation here"
}}

EXAMPLES:
{{"is_spam": true, "is_substantive": false, "confidence": 9, "brief_reason": "marketing email"}}
{{"is_spam": false, "is_substantive": true, "confidence": 8, "brief_reason": "business communication"}}
{{"is_spam": false, "is_substantive": false, "confidence": 7, "brief_reason": "empty or trivial content"}}

NOW CLASSIFY THE EMAIL ABOVE. Return ONLY the JSON object, nothing else:"""

