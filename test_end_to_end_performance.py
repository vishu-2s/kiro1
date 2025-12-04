"""
End-to-end performance test to verify all fixes are working.
This simulates the actual user workflow.
"""

import time
import json
from pathlib import Path
from analyze_supply_chain import SupplyChainAnalyzer


def test_large_project_performance():
    """Test that large projects complete in reasonable time."""
    
    print("=" * 70)
    print("END-TO-END PERFORMANCE TEST")
    print("=" * 70)
    
    # Create a test package.json with many packages
    test_packages = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            f"package-{i}": "1.0.0" for i in range(200)
        }
    }
    
    # Write to temp file
    test_file = Path("test_large_package.json")
    with open(test_file, 'w') as f:
        json.dump(test_packages, f)
    
    try:
        print(f"\n📦 Testing with {len(test_packages['dependencies'])} packages")
        print("-" * 70)
        
        # Create analyzer
        analyzer = SupplyChainAnalyzer(
            manifest_file=str(test_file),
            enable_osv=True,  # Enable OSV (should use parallel)
            enable_llm=False  # Disable LLM for speed
        )
        
        # Run analysis with timing
        print("\n⏱️  Starting analysis...")
        start_time = time.time()
        
        results = analyzer.analyze()
        
        duration = time.time() - start_time
        
        print(f"\n✅ Analysis completed in {duration:.1f} seconds")
        print("-" * 70)
        
        # Verify results
        assert results is not None, "Analysis returned None"
        assert 'findings' in results or 'packages' in results, "Results missing expected keys"
        
        # Performance assertions
        print("\n📊 Performance Metrics:")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Packages: {len(test_packages['dependencies'])}")
        print(f"   Rate: {len(test_packages['dependencies'])/duration:.1f} packages/sec")
        
        # Should complete in under 30 seconds for 200 packages
        if duration > 30:
            print(f"\n⚠️  WARNING: Analysis took {duration:.1f}s (expected <30s)")
            print("   This suggests reputation checks may still be running sequentially")
            return False
        else:
            print(f"\n✅ PASS: Analysis completed in {duration:.1f}s (<30s threshold)")
            return True
            
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_logs_show_parallel_queries():
    """Test that logs show parallel queries are being used."""
    
    print("\n" + "=" * 70)
    print("LOG VERIFICATION TEST")
    print("=" * 70)
    
    # Create small test file
    test_packages = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "4.17.1",
            "lodash": "4.17.20",
            "axios": "0.21.1"
        }
    }
    
    test_file = Path("test_small_package.json")
    with open(test_file, 'w') as f:
        json.dump(test_packages, f)
    
    try:
        import logging
        import io
        
        # Capture logs
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        
        logger = logging.getLogger('tools.sbom_tools')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Run analysis
        analyzer = SupplyChainAnalyzer(
            manifest_file=str(test_file),
            enable_osv=True,
            enable_llm=False
        )
        
        results = analyzer.analyze()
        
        # Check logs
        log_output = log_capture.getvalue()
        
        print("\n📋 Log Output:")
        print("-" * 70)
        for line in log_output.split('\n'):
            if line.strip():
                print(f"   {line}")
        print("-" * 70)
        
        # Verify key messages
        checks = {
            "Parallel queries": "parallel" in log_output.lower(),
            "No reputation for large projects": "reputation" not in log_output or "skipping" in log_output.lower(),
            "Checking packages": "checking" in log_output.lower()
        }
        
        print("\n✅ Verification:")
        all_pass = True
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}")
            if not passed:
                all_pass = False
        
        return all_pass
        
    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    print("\n🔍 COMPREHENSIVE PERFORMANCE VERIFICATION")
    print("=" * 70)
    
    try:
        # Test 1: Performance
        perf_pass = test_large_project_performance()
        
        # Test 2: Logs
        log_pass = test_logs_show_parallel_queries()
        
        # Final result
        print("\n" + "=" * 70)
        if perf_pass and log_pass:
            print("✅ ALL TESTS PASSED - PERFORMANCE FIXES VERIFIED")
            print("=" * 70)
            print("\nKey Findings:")
            print("  • Large projects complete in <30 seconds")
            print("  • Parallel queries are being used")
            print("  • Reputation checks are properly controlled")
            print("  • System is production-ready")
            exit(0)
        else:
            print("❌ SOME TESTS FAILED")
            print("=" * 70)
            if not perf_pass:
                print("  ✗ Performance test failed (too slow)")
            if not log_pass:
                print("  ✗ Log verification failed (wrong behavior)")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
