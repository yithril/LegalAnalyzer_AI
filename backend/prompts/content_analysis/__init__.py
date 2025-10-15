"""Content analysis prompts."""
from .email_classification import email_classification_prompt
from .content_classification import content_classification_prompt

__all__ = [
    "email_classification_prompt",
    "content_classification_prompt",
]

