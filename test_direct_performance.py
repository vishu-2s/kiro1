"""
Direct test of check_vulnerable_packages performance.
"""

import time
from tools.sbom_tools import check_vulnerable_packages


def test_performance_with_reputation_disabled():
    """Test that disabling reputation makes it fast."""
    
    print("=" * 70)
    print("DIRECT PERFORMANCE TEST")
    print("=" * 70)
    
    # Create SBOM with 200 packages
    packages = [
        {"name": f"package-{i}", "version": "1.0.0", "ecosystem": "npm"}
        for i in range(200)
    ]
    
    sbom_data = {"packages": packages}
    
    print(f"\n📦 Testing with {len(packages)} packages")
    print("-" * 70)
    
    # Test 1: With reputation (should skip for >100)
    print("\n1️⃣  Test with check_reputation=True (should skip)")
    start = time.time()
    findings1 = check_vulnerable_packages(
        sbom_data,
        use_osv=False,  # Disable OSV to isolate reputation
        check_reputation=True
    )
    duration1 = time.time() - start
    print(f"   Duration: {duration1:.1f}s")
    print(f"   Findings: {len(findings1)}")
    
    # Test 2: With reputation explicitly disabled
    print("\n2️⃣  Test with check_reputation=False")
    start = time.time()
    findings2 = check_vulnerable_packages(
        sbom_data,
        use_osv=False,
        check_reputation=False
    )
    duration2 = time.time() - start
    print(f"   Duration: {duration2:.1f}s")
    print(f"   Findings: {len(findings2)}")
    
    # Both should be fast (<5 seconds)
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    
    if duration1 < 5 and duration2 < 5:
        print(f"✅ PASS: Both tests completed quickly")
        print(f"   Test 1 (reputation=True): {duration1:.1f}s")
        print(f"   Test 2 (reputation=False): {duration2:.1f}s")
        print(f"\n   Reputation skip is working correctly!")
        return True
    else:
        print(f"❌ FAIL: Tests took too long")
        print(f"   Test 1 (reputation=True): {duration1:.1f}s (expected <5s)")
        print(f"   Test 2 (reputation=False): {duration2:.1f}s (expected <5s)")
        if duration1 > 5:
            print(f"\n   ⚠️  Reputation checks are NOT being skipped!")
        return False


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    try:
        success = test_performance_with_reputation_disabled()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
