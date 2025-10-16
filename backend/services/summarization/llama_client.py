"""Llama client for text summarization via Ollama."""
from typing import Optional
from ollama import AsyncClient
from services.summarization.base_summarizer import BaseSummarizer
from core.config import settings


class LlamaClient(BaseSummarizer):
    """Client for Llama via Ollama.
    
    Much simpler than Saul since Ollama provides native async support
    and handles model management, optimization, and resource allocation.
    
    Faster than Saul on CPU due to Ollama's optimizations (quantization,
    llama.cpp inference engine).
    """
    
    def __init__(self, model_name: str = None):
        """Initialize Llama client.
        
        Args:
            model_name: Ollama model name (e.g., 'llama3.1:8b', 'llama3.1:70b')
        """
        self.model_name = model_name or settings.ollama_model
        self.client = AsyncClient(host=settings.ollama_base_url)
        self._ready = True  # Ollama handles model loading lazily
    
    async def summarize(self, text: str, max_length: int = 150, document_type: str = None) -> str:
        """Summarize text (for BaseSummarizer compatibility).
        
        Note: Prefer using generate_from_prompt() for more control.
        
        Args:
            text: Text to summarize
            max_length: Maximum words in summary
            document_type: Not used
            
        Returns:
            Summary text
        """
        # Simple default prompt
        prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}\n\nSummary:"
        return await self.generate_from_prompt(prompt, max_tokens=max_length * 2)
    
    async def generate_from_prompt(self, prompt_text: str, max_tokens: int = 150) -> str:
        """Generate text from a custom prompt.
        
        This is the main method - pass your own formatted prompt.
        
        Args:
            prompt_text: The prompt text
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        response = await self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            options={
                "num_predict": max_tokens,  # Max tokens to generate
                "temperature": 0.3,  # Lower temperature for more focused summaries
            }
        )
        
        return response['message']['content'].strip()
    
    def is_ready(self) -> bool:
        """Check if client is ready.
        
        Returns:
            True (Ollama handles model management)
        """
        return self._ready
    
    async def health_check(self) -> bool:
        """Perform health check on Ollama.
        
        Returns:
            True if Ollama is reachable, False otherwise
        """
        try:
            # Try to list models as health check
            await self.client.list()
            return True
        except Exception as e:
            print(f"[Llama] Health check failed: {e}")
            return False


# Singleton instance
_llama_instance: Optional[LlamaClient] = None


def get_llama_client() -> LlamaClient:
    """Get or create the singleton Llama client instance.
    
    Returns:
        LlamaClient instance
    """
    global _llama_instance
    
    if _llama_instance is None:
        _llama_instance = LlamaClient()
    
    return _llama_instance

