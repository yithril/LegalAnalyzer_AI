"""Test Saul-Instruct client."""
import pytest
from services.summarization.saul_client import SaulClient


@pytest.mark.asyncio
async def test_saul_client_summarize():
    """Test Saul client basic summarization."""
    
    print(f"\n{'='*70}")
    print("Testing Saul-Instruct Client")
    print(f"{'='*70}")
    
    # Create client
    print("\n[INITIALIZING CLIENT]")
    client = SaulClient(device="cpu")  # Use CPU for testing
    
    # Test text
    test_text = """
    This Employment Agreement is entered into on January 1, 2024, between 
    ABC Corporation ("Employer") and John Smith ("Employee"). The Employee 
    agrees to perform duties as Software Engineer for a period of two years. 
    The base salary shall be $120,000 annually, payable bi-weekly. Benefits 
    include health insurance, 401(k) matching up to 5%, and 15 days paid vacation. 
    Either party may terminate this agreement with 30 days written notice.
    """
    
    # Test generic summarization
    print("\n[TESTING GENERIC SUMMARIZATION]")
    print(f"Input length: {len(test_text)} chars")
    
    summary = await client.summarize(test_text, max_length=50)
    
    print(f"\n[RESULT]")
    print(f"  Summary length: {len(summary)} chars")
    print(f"  Summary: {summary}")
    
    # Assertions
    assert len(summary) > 0, "Summary should not be empty"
    assert len(summary) < len(test_text), "Summary should be shorter than input"
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Saul client working!")
    print(f"{'='*70}\n")


@pytest.mark.asyncio
async def test_saul_client_contract_summarization():
    """Test Saul client with contract text."""
    
    print(f"\n{'='*70}")
    print("Testing Saul with Contract")
    print(f"{'='*70}")
    
    # Create client
    client = SaulClient(device="cpu")
    
    # Contract text
    contract_text = """
    TERMINATION CLAUSE: Either party may terminate this Agreement by providing 
    thirty (30) days written notice to the other party. Upon termination, the 
    Employee shall return all company property and confidential materials. The 
    Employer shall pay all earned but unpaid salary within fourteen (14) days 
    of the termination date. Non-compete provisions shall remain in effect for 
    twelve (12) months following termination.
    """
    
    print("\n[TESTING CONTRACT SUMMARIZATION]")
    
    # Single summarize method, optional document_type parameter
    summary = await client.summarize(contract_text, max_length=75, document_type="contract")
    
    print(f"\n[RESULT]")
    print(f"  Summary: {summary}")
    
    # Check summary mentions key legal elements
    summary_lower = summary.lower()
    
    print(f"\n[CHECKING KEY ELEMENTS]")
    has_termination = "terminat" in summary_lower
    has_notice = "notice" in summary_lower or "30" in summary or "days" in summary_lower
    
    print(f"  Mentions termination: {has_termination}")
    print(f"  Mentions notice period: {has_notice}")
    
    assert len(summary) > 0, "Summary should not be empty"
    
    print(f"\n[SUCCESS] Contract summarization working!")


@pytest.mark.asyncio
async def test_saul_health_check():
    """Test Saul client health check."""
    
    print(f"\n{'='*70}")
    print("Testing Saul Health Check")
    print(f"{'='*70}")
    
    client = SaulClient(device="cpu")
    
    print("\n[RUNNING HEALTH CHECK]")
    is_healthy = await client.health_check()
    
    print(f"  Health status: {'HEALTHY' if is_healthy else 'UNHEALTHY'}")
    print(f"  Model ready: {client.is_ready()}")
    
    assert is_healthy, "Client should pass health check"
    assert client.is_ready(), "Model should be loaded and ready"
    
    print(f"\n[SUCCESS] Health check passed!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

