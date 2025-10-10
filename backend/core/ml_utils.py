"""Machine Learning utilities for local AI models.

All models run locally - no external API calls.
"""
from typing import List
import ollama
from sentence_transformers import SentenceTransformer
from core.config import settings


# Lazy load models to avoid loading on import
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get the sentence transformer model for embeddings.
    
    Lazy loads on first use.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


async def call_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    model: str = None
) -> str:
    """Call local LLM via Ollama.
    
    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt for context
        temperature: Sampling temperature (0-1)
        model: Optional model override, defaults to config
    
    Returns:
        The LLM response text
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    response = ollama.chat(
        model=model or settings.ollama_model,
        messages=messages,
        options={"temperature": temperature}
    )
    
    return response['message']['content']


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts.
    
    Used for vector search/RAG (add when needed).
    
    Args:
        texts: List of text strings to embed
    
    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()

