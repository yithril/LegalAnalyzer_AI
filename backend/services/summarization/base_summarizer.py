"""Base interface for text summarization models."""
from abc import ABC, abstractmethod


class BaseSummarizer(ABC):
    """Abstract base class for summarization models.
    
    Implementations can use different models (Saul, Llama, Claude, etc.)
    but provide the same interface for the rest of the application.
    """
    
    @abstractmethod
    async def summarize(self, text: str, max_length: int = 150, document_type: str = None) -> str:
        """Summarize the given text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in tokens
            document_type: Optional document type for prompt optimization (e.g., "contract", "email")
            
        Returns:
            Summary text
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the model is loaded and ready to use.
        
        Returns:
            True if model is ready, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check on the model.
        
        Returns:
            True if model is healthy, False otherwise
        """
        pass

