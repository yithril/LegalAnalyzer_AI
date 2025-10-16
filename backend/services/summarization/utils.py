"""Utility functions for summarization."""


def is_legal_document(classification: str) -> bool:
    """Determine if a document is legal in nature based on classification.
    
    Args:
        classification: Document classification (e.g., "contract", "email", "report")
        
    Returns:
        True if document is legal, False otherwise
    """
    if not classification:
        return False
    
    LEGAL_TYPES = [
        "contract",
        "agreement", 
        "court_filing",
        "legal_document",
        "motion",
        "brief",
        "deposition",
        "pleading",
        "affidavit",
        "legal_memo",
        "legal_opinion",
        "statute",
        "regulation",
        "ordinance"
    ]
    
    classification_lower = classification.lower()
    return any(legal_type in classification_lower for legal_type in LEGAL_TYPES)

