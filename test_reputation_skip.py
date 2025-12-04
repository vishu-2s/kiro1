"""
Test that reputation checks are skipped for large package counts.
"""

from tools.sbom_tools import check_vulnerable_packages
from unittest.mock import patch
import logging

# Enable logging to see messages
logging.basicConfig(level=logging.INFO)


def test_reputation_skipped_for_large_count():
    """Test that reputation checks are skipped when package count > 100."""
    
    print("Testing reputation skip for large package count...")
    
    # Create SBOM with 150 packages
    packages = [
        {"name": f"package-{i}", "version": "1.0.0", "ecosystem": "npm"}
        for i in range(150)
    ]
    
    sbom_data = {"packages": packages}
    
    # Mock reputation scorer to track if it's called
    with patch('tools.sbom_tools.ReputationScorer') as mock_scorer:
        mock_scorer.return_value.calculate_reputation.return_value = {
            'score': 0.8,
            'flags': []
        }
        
        # Run check with reputation enabled
        findings = check_vulnerable_packages(
            sbom_data, 
            use_osv=False,  # Disable OSV to focus on reputation
            check_reputation=True
        )
        
        # Reputation scorer should NOT be called for large package counts
        call_count = mock_scorer.return_value.calculate_reputation.call_count
        print(f"  Reputation scorer called {call_count} times")
        
        # Should be 0 because we skip for >100 packages
        assert call_count == 0, f"Expected 0 calls, got {call_count}"
        
    print("  ✓ Reputation checks skipped for 150 packages")


def test_reputation_runs_for_small_count():
    """Test that reputation checks run when package count <= 100."""
    
    print("\nTesting reputation runs for small package count...")
    
    # Create SBOM with 10 packages
    packages = [
        {"name": f"package-{i}", "version": "1.0.0", "ecosystem": "npm"}
        for i in range(10)
    ]
    
    sbom_data = {"packages": packages}
    
    # Mock reputation scorer and cache
    with patch('tools.sbom_tools.ReputationScorer') as mock_scorer, \
         patch('tools.sbom_tools.get_cache_manager') as mock_cache:
        
        mock_scorer.return_value.calculate_reputation.return_value = {
            'score': 0.8,
            'flags': []
        }
        mock_cache.return_value.get_reputation.return_value = None  # No cache
        
        # Run check with reputation enabled
        findings = check_vulnerable_packages(
            sbom_data, 
            use_osv=False,  # Disable OSV to focus on reputation
            check_reputation=True
        )
        
        # Reputation scorer SHOULD be called for small package counts
        call_count = mock_scorer.return_value.calculate_reputation.call_count
        print(f"  Reputation scorer called {call_count} times")
        
        # Should be 10 (one per package)
        assert call_count == 10, f"Expected 10 calls, got {call_count}"
        
    print("  ✓ Reputation checks ran for 10 packages")


if __name__ == "__main__":
    print("=" * 60)
    print("REPUTATION SKIP TESTS")
    print("=" * 60)
    print()
    
    try:
        test_reputation_skipped_for_large_count()
        test_reputation_runs_for_small_count()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nKey Findings:")
        print("  • Reputation checks skipped for >100 packages")
        print("  • Reputation checks run for ≤100 packages")
        print("  • This prevents slowdown on large projects")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
