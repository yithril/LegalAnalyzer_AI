"""Test Llama client via Ollama."""
import pytest
from services.summarization.llama_client import LlamaClient


@pytest.mark.asyncio
async def test_llama_client_basic():
    """Test Llama client basic summarization."""
    
    print(f"\n{'='*70}")
    print("Testing Llama Client (via Ollama)")
    print(f"{'='*70}")
    
    # Create client (use 8B for testing - faster and more available)
    print("\n[INITIALIZING CLIENT]")
    client = LlamaClient(model_name="llama3.1:8b")
    print(f"  Model: {client.model_name}")
    print(f"  Ready: {client.is_ready()}")
    
    # Test text
    test_text = """
    This Employment Agreement is entered into on January 1, 2024, between 
    ABC Corporation ("Employer") and John Smith ("Employee"). The Employee 
    agrees to perform duties as Software Engineer for a period of two years. 
    The base salary shall be $120,000 annually, payable bi-weekly. Benefits 
    include health insurance, 401(k) matching up to 5%, and 15 days paid vacation. 
    Either party may terminate this agreement with 30 days written notice.
    """
    
    # Test basic summarization
    print("\n[TESTING BASIC SUMMARIZATION]")
    print(f"  Input length: {len(test_text)} chars")
    
    summary = await client.summarize(test_text, max_length=50)
    
    print(f"\n[RESULT]")
    print(f"  Summary length: {len(summary)} chars")
    print(f"  Summary: {summary}")
    
    # Assertions
    assert len(summary) > 0, "Summary should not be empty"
    assert len(summary) < len(test_text), "Summary should be shorter than input"
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Llama client working!")
    print(f"{'='*70}\n")


@pytest.mark.asyncio
async def test_llama_with_custom_prompt():
    """Test Llama client with custom prompt."""
    
    print(f"\n{'='*70}")
    print("Testing Llama with Custom Prompt")
    print(f"{'='*70}")
    
    client = LlamaClient()
    
    # Contract text
    contract_text = """
    TERMINATION CLAUSE: Either party may terminate this Agreement by providing 
    thirty (30) days written notice to the other party. Upon termination, the 
    Employee shall return all company property and confidential materials. The 
    Employer shall pay all earned but unpaid salary within fourteen (14) days 
    of the termination date. Non-compete provisions shall remain in effect for 
    twelve (12) months following termination.
    """
    
    # Custom legal-focused prompt
    prompt = """Summarize the following legal clause, focusing on key obligations and timelines:

{text}

Summary:""".format(text=contract_text)
    
    print("\n[TESTING CUSTOM PROMPT]")
    summary = await client.generate_from_prompt(prompt, max_tokens=100)
    
    print(f"\n[RESULT]")
    print(f"  Summary: {summary}")
    
    # Check it mentions key elements
    summary_lower = summary.lower()
    has_termination = "terminat" in summary_lower
    has_notice = "30" in summary or "notice" in summary_lower
    
    print(f"\n[KEY ELEMENTS CHECK]")
    print(f"  Mentions termination: {has_termination}")
    print(f"  Mentions notice period: {has_notice}")
    
    assert len(summary) > 0, "Summary should not be empty"
    
    print(f"\n[SUCCESS] Custom prompt working!")


@pytest.mark.asyncio
async def test_llama_health_check():
    """Test Llama health check."""
    
    print(f"\n{'='*70}")
    print("Testing Llama Health Check")
    print(f"{'='*70}")
    
    client = LlamaClient()
    
    print("\n[RUNNING HEALTH CHECK]")
    is_healthy = await client.health_check()
    
    print(f"  Health status: {'HEALTHY' if is_healthy else 'UNHEALTHY'}")
    print(f"  Client ready: {client.is_ready()}")
    
    assert is_healthy, "Ollama should be reachable"
    assert client.is_ready(), "Client should be ready"
    
    print(f"\n[SUCCESS] Health check passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

