"""Saul-Instruct client for legal text summarization."""
import asyncio
from typing import Optional
from functools import partial
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from services.summarization.base_summarizer import BaseSummarizer


class SaulClient(BaseSummarizer):
    """Client for Saul-Instruct legal language model.
    
    Wraps the Saul-Instruct model from HuggingFace Transformers with:
    - Simple async interface
    - Legal-specific prompting
    - Resource management
    - Thread-safe execution
    """
    
    MODEL_NAME = "Equall/Saul-Instruct-v1"
    
    def __init__(self, device: str = "auto"):
        """Initialize Saul client.
        
        Args:
            device: Device to run model on ('auto', 'cpu', 'cuda')
        """
        self.device = device
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self._loaded = False
        self._loading = False
    
    async def _load_model(self):
        """Load Saul model and tokenizer (runs in thread pool)."""
        if self._loaded or self._loading:
            return
        
        self._loading = True
        
        print(f"[Saul] Loading model: {self.MODEL_NAME}")
        print(f"[Saul] Device: {self.device}")
        
        # Run in thread pool since model loading is CPU-bound
        loop = asyncio.get_event_loop()
        
        # Load tokenizer
        self.tokenizer = await loop.run_in_executor(
            None,
            partial(
                AutoTokenizer.from_pretrained,
                self.MODEL_NAME
            )
        )
        
        # Set pad_token if not set (required for generation)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = await loop.run_in_executor(
            None,
            partial(
                AutoModelForCausalLM.from_pretrained,
                self.MODEL_NAME,
                device_map=self.device,
                low_cpu_mem_usage=True
            )
        )
        
        self._loaded = True
        self._loading = False
        
        print(f"[Saul] Model loaded successfully!")
        print(f"[Saul] Memory usage: {torch.cuda.memory_allocated() / 1e9:.2f} GB" if torch.cuda.is_available() else "[Saul] Running on CPU")
    
    async def summarize(self, text: str, max_length: int = 150, document_type: str = None) -> str:
        """Summarize text with a prompt string (for BaseSummarizer compatibility).
        
        Note: This method exists for interface compatibility but is less flexible.
        Prefer using generate_from_prompt() directly with your own prompts.
        
        Args:
            text: Text to summarize
            max_length: Maximum tokens in summary
            document_type: Not used
            
        Returns:
            Summary text
        """
        if not self._loaded:
            await self._load_model()
        
        # Simple default prompt
        prompt = f"Summarize the following text concisely:\n\n{text}\n\nSummary:"
        formatted = self._format_prompt(prompt)
        return await self._generate(formatted, max_length)
    
    async def generate_from_prompt(self, prompt_text: str, max_tokens: int = 150) -> str:
        """Generate text from a custom prompt.
        
        This is the main method to use - pass your own formatted prompt.
        
        Args:
            prompt_text: The prompt text (not yet formatted with chat template)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self._loaded:
            await self._load_model()
        
        formatted_prompt = self._format_prompt(prompt_text)
        return await self._generate(formatted_prompt, max_tokens)
    
    def _format_prompt(self, prompt_text: str) -> str:
        """Format prompt text with Saul's chat template.
        
        Args:
            prompt_text: Raw prompt text
            
        Returns:
            Formatted prompt with chat template applied
        """
        messages = [{
            "role": "user",
            "content": prompt_text
        }]
        
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    
    async def _generate(self, prompt: str, max_new_tokens: int) -> str:
        """Generate text using the model (runs in thread pool).
        
        Args:
            prompt: Formatted prompt
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Run generation in thread pool (CPU/GPU-bound)
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            None,
            partial(self._generate_sync, prompt, max_new_tokens)
        )
        
        return result
    
    def _generate_sync(self, prompt: str, max_new_tokens: int) -> str:
        """Synchronous generation (called from thread pool).
        
        Args:
            prompt: Formatted prompt
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Tokenize (no padding needed for single input)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Move to device
        if torch.cuda.is_available() and self.device != "cpu":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,
                do_sample=False,  # Deterministic for consistency
                pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id else self.tokenizer.eos_token_id
            )
        
        # Decode
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part (after [/INST])
        # Saul's chat template uses [INST] ... [/INST] format
        if "[/INST]" in full_output:
            generated_text = full_output.split("[/INST]")[-1].strip()
        elif "SUMMARY:" in full_output:
            generated_text = full_output.split("SUMMARY:")[-1].strip()
        else:
            # Fallback: just return everything
            generated_text = full_output.strip()
        
        return generated_text
    
    def is_ready(self) -> bool:
        """Check if model is loaded and ready.
        
        Returns:
            True if ready, False otherwise
        """
        return self._loaded and self.model is not None and self.tokenizer is not None
    
    async def health_check(self) -> bool:
        """Perform health check.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.is_ready():
                await self._load_model()
            
            # Try a simple generation
            test_summary = await self.summarize("This is a test.", max_length=10)
            return len(test_summary) > 0
            
        except Exception as e:
            print(f"[Saul] Health check failed: {e}")
            return False


# Singleton instance (load once, use everywhere)
_saul_instance: Optional[SaulClient] = None


def get_saul_client() -> SaulClient:
    """Get or create the singleton Saul client instance.
    
    Returns:
        SaulClient instance
    """
    global _saul_instance
    
    if _saul_instance is None:
        _saul_instance = SaulClient()
    
    return _saul_instance

