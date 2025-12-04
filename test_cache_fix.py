"""
Test cache file fix for Windows compatibility.
"""

import os
import json
from pathlib import Path
from update_constants import MaliciousPackageCache


def test_cache_save_windows_compatibility():
    """Test that cache save works on Windows when files already exist."""
    
    print("Testing cache save with existing files...")
    
    # Create test cache
    test_cache_file = "test_cache.json"
    cache = MaliciousPackageCache(cache_file=test_cache_file)
    
    # Test data
    test_data = {
        "npm": [
            {"name": "test-package", "version": "1.0.0", "reason": "test"}
        ]
    }
    
    # First save
    print("  First save...")
    success1 = cache.save_cache(test_data)
    assert success1, "First save failed"
    assert Path(test_cache_file).exists(), "Cache file not created"
    print("  ✓ First save successful")
    
    # Second save (should overwrite)
    print("  Second save (overwrite)...")
    test_data["npm"].append({"name": "another-package", "version": "2.0.0", "reason": "test2"})
    success2 = cache.save_cache(test_data)
    assert success2, "Second save failed"
    print("  ✓ Second save successful")
    
    # Verify content
    print("  Verifying content...")
    with open(test_cache_file, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded['malicious_packages']['npm']) == 2, "Content not updated"
    print("  ✓ Content verified")
    
    # Cleanup
    Path(test_cache_file).unlink()
    temp_file = Path(test_cache_file).with_suffix('.tmp')
    if temp_file.exists():
        temp_file.unlink()
    
    print("✅ Cache save test passed!")


def test_no_leftover_temp_files():
    """Test that no temp files are left behind."""
    
    print("\nTesting temp file cleanup...")
    
    test_cache_file = "test_cache2.json"
    cache = MaliciousPackageCache(cache_file=test_cache_file)
    
    test_data = {"npm": [{"name": "test", "version": "1.0.0", "reason": "test"}]}
    
    # Save multiple times
    for i in range(3):
        cache.save_cache(test_data)
    
    # Check for temp files
    temp_file = Path(test_cache_file).with_suffix('.tmp')
    assert not temp_file.exists(), "Temp file left behind"
    
    # Cleanup
    Path(test_cache_file).unlink()
    
    print("✅ No temp files left behind!")


if __name__ == "__main__":
    print("=" * 60)
    print("CACHE FIX TESTS")
    print("=" * 60)
    print(f"Platform: {os.name}")
    print()
    
    try:
        test_cache_save_windows_compatibility()
        test_no_leftover_temp_files()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
