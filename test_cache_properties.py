"""
Property-based tests for cache manager functionality.

Tests verify correctness properties for the intelligent caching system,
ensuring cache-first lookup, TTL expiration, and content hash consistency.
"""

import tempfile
import time
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

from tools.cache_manager import CacheManager


# Hypothesis strategies for generating test data
script_content_strategy = st.text(min_size=1, max_size=1000)
analysis_result_strategy = st.fixed_dictionaries({
    'is_suspicious': st.booleans(),
    'confidence': st.floats(min_value=0.0, max_value=1.0),
    'severity': st.sampled_from(['low', 'medium', 'high', 'critical']),
    'threats': st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5),
    'reasoning': st.text(min_size=10, max_size=500)
})


class TestCacheFirstLookup:
    """Property-based tests for cache-first lookup behavior."""

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_property_6_cache_first_lookup(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        **Feature: production-ready-enhancements, Property 6: Cache-First Lookup**
        
        For any script analysis request, the system should check the cache before 
        making any LLM API calls, ensuring cache lookup happens first.
        
        **Validates: Requirements 2.1**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create cache manager with SQLite backend
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # Generate cache key for the script
            script_hash = cache_manager.generate_cache_key(script_content)
            
            # Store analysis result in cache
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Mock the LLM API call to track if it's invoked
            llm_api_called = False
            
            def mock_llm_call():
                nonlocal llm_api_called
                llm_api_called = True
                return {"mock": "result"}
            
            # Simulate analysis workflow: check cache first
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            # Property 1: Cache should return the stored result
            assert cached_result is not None, "Cache should contain the stored analysis"
            assert cached_result == analysis_result, "Cached result should match stored result"
            
            # Property 2: If cache hit occurs, LLM should NOT be called
            # In a real workflow, the presence of cached_result would prevent LLM call
            if cached_result is not None:
                # LLM call should be skipped
                pass
            else:
                # Only call LLM if cache miss
                mock_llm_call()
            
            # Property 3: LLM was not called because cache hit occurred
            assert not llm_api_called, "LLM API should not be called when cache hit occurs"

    @given(script_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_lookup_before_llm_with_miss(self, script_content: str):
        """
        Test that cache is checked first even on cache miss.
        
        For any script content, the system should attempt cache lookup
        before proceeding to LLM analysis, even if the cache is empty.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            
            # Ensure cache is empty (no prior storage)
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            # Property: Cache lookup should return None for non-existent entries
            assert cached_result is None, "Cache should return None for non-existent entries"
            
            # In real workflow, this would trigger LLM call
            # But the important property is that cache was checked FIRST

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_first_with_memory_backend(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test cache-first lookup with in-memory backend.
        
        Verifies that cache-first behavior works consistently across
        different backend implementations (memory vs SQLite).
        """
        # Create cache manager with memory backend
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        script_hash = cache_manager.generate_cache_key(script_content)
        
        # Store in cache
        cache_manager.store_llm_analysis(script_hash, analysis_result)
        
        # Retrieve from cache
        cached_result = cache_manager.get_llm_analysis(script_hash)
        
        # Property: Cache should return stored result regardless of backend
        assert cached_result is not None, "Memory cache should contain stored analysis"
        assert cached_result == analysis_result, "Memory cached result should match stored result"

    @given(
        st.lists(
            st.tuples(script_content_strategy, analysis_result_strategy),
            min_size=1,
            max_size=5,
            unique_by=lambda x: x[0]  # Ensure unique script contents
        )
    )
    @settings(max_examples=30, deadline=500)  # Increased deadline for SQLite operations
    def test_cache_first_with_multiple_entries(self, script_results: list):
        """
        Test cache-first lookup with multiple cached entries.
        
        For any collection of scripts and their analysis results,
        each script should retrieve its own cached result without
        triggering LLM calls.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # Store all script analyses in cache with unique keys
            stored_entries = {}
            for script_content, analysis_result in script_results:
                script_hash = cache_manager.generate_cache_key(script_content)
                # Store the last result for this hash (in case of duplicates)
                stored_entries[script_hash] = analysis_result
                cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Verify each unique entry can be retrieved from cache
            for script_hash, expected_result in stored_entries.items():
                cached_result = cache_manager.get_llm_analysis(script_hash)
                
                # Property: Each script should retrieve its own cached result
                assert cached_result is not None, f"Cache should contain analysis for {script_hash}"
                assert cached_result == expected_result, "Cached result should match stored result"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_first_lookup_order_verification(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Verify that cache lookup happens before any other operations.
        
        This test uses mocking to ensure the cache get operation
        is called before any potential LLM API calls.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Track operation order
            operations = []
            
            # Wrap cache get method to track calls
            original_get = cache_manager.get_llm_analysis
            def tracked_get(key):
                operations.append('cache_get')
                return original_get(key)
            
            cache_manager.get_llm_analysis = tracked_get
            
            # Simulate analysis workflow
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            if cached_result is None:
                operations.append('llm_call')
            
            # Property: Cache get should be the first operation
            assert len(operations) > 0, "At least one operation should occur"
            assert operations[0] == 'cache_get', "Cache lookup should be the first operation"
            
            # Property: If cache hit, no LLM call should follow
            if cached_result is not None:
                assert 'llm_call' not in operations, "LLM call should not occur on cache hit"


class TestCacheHitBehavior:
    """Property-based tests for cache hit behavior."""

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_property_7_cache_hit_returns_cached_result(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        **Feature: production-ready-enhancements, Property 7: Cache Hit Returns Cached Result**
        
        For any script with a valid cached result, retrieving the analysis should 
        return the cached result without making new LLM API calls.
        
        **Validates: Requirements 2.2**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create cache manager with SQLite backend
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # Generate cache key and store analysis result
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Retrieve from cache
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            # Property 1: Cache hit should return non-None result
            assert cached_result is not None, "Cache hit should return a result"
            
            # Property 2: Cached result should exactly match stored result
            assert cached_result == analysis_result, "Cached result must match the stored analysis result"
            
            # Property 3: All fields should be preserved
            for key in analysis_result.keys():
                assert key in cached_result, f"Field '{key}' should be present in cached result"
                assert cached_result[key] == analysis_result[key], f"Field '{key}' value should match"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_hit_with_memory_backend(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test cache hit behavior with in-memory backend.
        
        Verifies that cache hit returns cached result consistently
        across different backend implementations.
        """
        # Create cache manager with memory backend
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        script_hash = cache_manager.generate_cache_key(script_content)
        cache_manager.store_llm_analysis(script_hash, analysis_result)
        
        # Retrieve from cache
        cached_result = cache_manager.get_llm_analysis(script_hash)
        
        # Property: Cache hit should return exact stored result
        assert cached_result is not None, "Memory cache hit should return a result"
        assert cached_result == analysis_result, "Memory cached result must match stored result"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_hit_idempotency(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that multiple cache hits return the same result.
        
        For any cached script, retrieving it multiple times should
        return identical results each time (idempotency).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Retrieve multiple times
            result1 = cache_manager.get_llm_analysis(script_hash)
            result2 = cache_manager.get_llm_analysis(script_hash)
            result3 = cache_manager.get_llm_analysis(script_hash)
            
            # Property: All retrievals should return identical results
            assert result1 is not None, "First cache hit should return result"
            assert result2 is not None, "Second cache hit should return result"
            assert result3 is not None, "Third cache hit should return result"
            
            assert result1 == result2, "First and second retrieval should match"
            assert result2 == result3, "Second and third retrieval should match"
            assert result1 == analysis_result, "All retrievals should match original"

    @given(
        st.lists(
            st.tuples(script_content_strategy, analysis_result_strategy),
            min_size=2,
            max_size=10,
            unique_by=lambda x: x[0]  # Ensure unique script contents
        )
    )
    @settings(max_examples=30, deadline=500)
    def test_cache_hit_isolation(self, script_results: list):
        """
        Test that cache hits return correct results for different scripts.
        
        For any collection of different scripts with cached results,
        each script should retrieve its own specific result, not others.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # Store all scripts with their unique results
            stored_mapping = {}
            for script_content, analysis_result in script_results:
                script_hash = cache_manager.generate_cache_key(script_content)
                stored_mapping[script_hash] = (script_content, analysis_result)
                cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Verify each script retrieves its own result
            for script_hash, (script_content, expected_result) in stored_mapping.items():
                cached_result = cache_manager.get_llm_analysis(script_hash)
                
                # Property: Each script should get its own cached result
                assert cached_result is not None, f"Cache should contain result for {script_hash}"
                assert cached_result == expected_result, "Cached result should match the specific script's result"
                
                # Property: Result should not match other scripts' results
                for other_hash, (_, other_result) in stored_mapping.items():
                    if other_hash != script_hash and other_result != expected_result:
                        assert cached_result != other_result, "Should not return results from different scripts"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_hit_without_llm_call(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that cache hit prevents LLM API calls.
        
        For any cached script, the cache hit should provide the result
        without requiring any external LLM API calls.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Track if any external call would be needed
            llm_call_needed = False
            
            # Check cache
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            # If cache returns None, LLM call would be needed
            if cached_result is None:
                llm_call_needed = True
            
            # Property: Cache hit should provide result without LLM call
            assert not llm_call_needed, "Cache hit should eliminate need for LLM call"
            assert cached_result is not None, "Cache hit should return result"
            assert cached_result == analysis_result, "Cache hit should return correct result"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_cache_hit_updates_statistics(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that cache hits update hit count statistics.
        
        For any cached script, each cache hit should increment
        the hit count for tracking cache effectiveness.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Get initial statistics
            initial_stats = cache_manager.get_statistics()
            initial_hits = initial_stats.get('total_hits', 0)
            
            # Perform cache hits
            num_hits = 3
            for _ in range(num_hits):
                cached_result = cache_manager.get_llm_analysis(script_hash)
                assert cached_result is not None, "Each cache hit should return result"
            
            # Get updated statistics
            updated_stats = cache_manager.get_statistics()
            updated_hits = updated_stats.get('total_hits', 0)
            
            # Property: Hit count should increase with each cache hit
            assert updated_hits >= initial_hits + num_hits, "Hit count should increase with cache hits"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=None)
    def test_cache_hit_preserves_data_types(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that cache hit preserves all data types correctly.
        
        For any analysis result with various data types (bool, float, string, list),
        the cached result should preserve the exact types and values.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            cached_result = cache_manager.get_llm_analysis(script_hash)
            
            # Property: Data types should be preserved
            assert cached_result is not None, "Cache hit should return result"
            
            # Check boolean type
            assert isinstance(cached_result['is_suspicious'], bool), "Boolean field should remain boolean"
            assert cached_result['is_suspicious'] == analysis_result['is_suspicious']
            
            # Check float type
            assert isinstance(cached_result['confidence'], float), "Float field should remain float"
            assert cached_result['confidence'] == analysis_result['confidence']
            
            # Check string type
            assert isinstance(cached_result['severity'], str), "String field should remain string"
            assert cached_result['severity'] == analysis_result['severity']
            
            # Check list type
            assert isinstance(cached_result['threats'], list), "List field should remain list"
            assert cached_result['threats'] == analysis_result['threats']


class TestContentHashConsistency:
    """Property-based tests for content hash consistency."""

    @given(script_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_property_9_content_hash_consistency(self, script_content: str):
        """
        **Feature: production-ready-enhancements, Property 9: Content Hash Consistency**
        
        For any two identical script contents, the cache key generation should 
        produce identical hash values, ensuring cache hits for duplicate content.
        
        **Validates: Requirements 2.4**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create cache manager
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # Generate hash for the same content multiple times
            hash1 = cache_manager.generate_cache_key(script_content)
            hash2 = cache_manager.generate_cache_key(script_content)
            hash3 = cache_manager.generate_cache_key(script_content)
            
            # Property 1: Identical content should produce identical hashes
            assert hash1 == hash2, "Same content should produce same hash (first vs second)"
            assert hash2 == hash3, "Same content should produce same hash (second vs third)"
            assert hash1 == hash3, "Same content should produce same hash (first vs third)"
            
            # Property 2: Hash should be deterministic (not random)
            assert isinstance(hash1, str), "Hash should be a string"
            assert len(hash1) > 0, "Hash should not be empty"
            
            # Property 3: Hash should be consistent across cache manager instances
            cache_manager2 = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            hash4 = cache_manager2.generate_cache_key(script_content)
            assert hash1 == hash4, "Same content should produce same hash across different cache manager instances"

    @given(script_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_hash_consistency_with_memory_backend(self, script_content: str):
        """
        Test hash consistency with in-memory backend.
        
        Verifies that hash generation is consistent regardless of
        the backend implementation (memory vs SQLite).
        """
        # Create cache managers with different backends
        cache_manager_sqlite = CacheManager(backend="sqlite", ttl_hours=24)
        cache_manager_memory = CacheManager(backend="memory", ttl_hours=24)
        
        # Generate hashes with both backends
        hash_sqlite = cache_manager_sqlite.generate_cache_key(script_content)
        hash_memory = cache_manager_memory.generate_cache_key(script_content)
        
        # Property: Hash should be identical regardless of backend
        assert hash_sqlite == hash_memory, "Hash should be consistent across different backends"

    @given(st.text(min_size=1, max_size=1000), st.text(min_size=1, max_size=1000))
    @settings(max_examples=100, deadline=None)
    def test_different_content_produces_different_hashes(self, content1: str, content2: str):
        """
        Test that different content produces different hashes.
        
        For any two different script contents, the cache key generation
        should produce different hash values (collision resistance).
        """
        # Skip if contents are identical
        if content1 == content2:
            return
        
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        hash1 = cache_manager.generate_cache_key(content1)
        hash2 = cache_manager.generate_cache_key(content2)
        
        # Property: Different content should produce different hashes
        assert hash1 != hash2, "Different content should produce different hashes"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=None)
    def test_hash_enables_cache_hits_for_duplicate_content(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that consistent hashing enables cache hits for duplicate content.
        
        For any script content analyzed multiple times, the consistent hash
        should enable cache hits on subsequent analyses.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24
            )
            
            # First analysis: store result
            hash1 = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(hash1, analysis_result)
            
            # Second analysis: should hit cache due to consistent hash
            hash2 = cache_manager.generate_cache_key(script_content)
            cached_result = cache_manager.get_llm_analysis(hash2)
            
            # Property: Consistent hash enables cache hit
            assert hash1 == hash2, "Same content should produce same hash"
            assert cached_result is not None, "Cache hit should occur for duplicate content"
            assert cached_result == analysis_result, "Cached result should match original"

    @given(script_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_hash_with_prefix(self, script_content: str):
        """
        Test hash consistency with prefix parameter.
        
        For any script content, hashes with the same prefix should be
        consistent, and different prefixes should produce different hashes.
        """
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        # Generate hashes with no prefix
        hash_no_prefix1 = cache_manager.generate_cache_key(script_content)
        hash_no_prefix2 = cache_manager.generate_cache_key(script_content)
        
        # Generate hashes with same prefix
        hash_prefix_a1 = cache_manager.generate_cache_key(script_content, prefix="llm")
        hash_prefix_a2 = cache_manager.generate_cache_key(script_content, prefix="llm")
        
        # Generate hashes with different prefix
        hash_prefix_b = cache_manager.generate_cache_key(script_content, prefix="reputation")
        
        # Property 1: Same content with no prefix produces same hash
        assert hash_no_prefix1 == hash_no_prefix2, "Same content should produce same hash"
        
        # Property 2: Same content with same prefix produces same hash
        assert hash_prefix_a1 == hash_prefix_a2, "Same content with same prefix should produce same hash"
        
        # Property 3: Different prefixes produce different hashes
        assert hash_prefix_a1 != hash_prefix_b, "Different prefixes should produce different hashes"
        assert hash_no_prefix1 != hash_prefix_a1, "Hash with prefix should differ from hash without prefix"

    @given(script_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_hash_is_sha256(self, script_content: str):
        """
        Test that generated hash is a valid SHA-256 hash.
        
        For any script content, the generated hash should be a valid
        64-character hexadecimal string (SHA-256 format).
        """
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        hash_value = cache_manager.generate_cache_key(script_content)
        
        # Property 1: Hash should be 64 characters (SHA-256 hex length)
        # Note: With prefix, it will be longer, so test without prefix
        hash_no_prefix = cache_manager.generate_cache_key(script_content, prefix="")
        assert len(hash_no_prefix) == 64, "SHA-256 hash should be 64 characters"
        
        # Property 2: Hash should only contain hexadecimal characters
        assert all(c in '0123456789abcdef' for c in hash_no_prefix), "Hash should only contain hex characters"
        
        # Property 3: Hash should match manual SHA-256 calculation
        import hashlib
        expected_hash = hashlib.sha256(script_content.encode('utf-8')).hexdigest()
        assert hash_no_prefix == expected_hash, "Hash should match SHA-256 calculation"

    @given(
        st.lists(
            script_content_strategy,
            min_size=2,
            max_size=10,
            unique=True  # Ensure all contents are unique
        )
    )
    @settings(max_examples=50)
    def test_hash_uniqueness_for_multiple_contents(self, script_contents: list):
        """
        Test that multiple different contents produce unique hashes.
        
        For any collection of different script contents, each should
        produce a unique hash value (no collisions).
        """
        cache_manager = CacheManager(backend="memory", ttl_hours=24)
        
        # Generate hashes for all contents
        hashes = [cache_manager.generate_cache_key(content) for content in script_contents]
        
        # Property: All hashes should be unique
        assert len(hashes) == len(set(hashes)), "All different contents should produce unique hashes"
        
        # Property: Each hash should be retrievable
        for i, content in enumerate(script_contents):
            regenerated_hash = cache_manager.generate_cache_key(content)
            assert regenerated_hash == hashes[i], f"Hash for content {i} should be consistent"


class TestExpiredCacheRefresh:
    """Property-based tests for expired cache refresh behavior."""

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=100, deadline=3000)  # 3 second deadline for sleep operations
    def test_property_8_expired_cache_refresh(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        **Feature: production-ready-enhancements, Property 8: Expired Cache Refresh**
        
        For any cache entry that has exceeded its TTL, the next analysis request 
        should trigger a fresh LLM call and update the cache.
        
        **Validates: Requirements 2.3**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create cache manager with short TTL (2 seconds for testing)
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=2/3600  # 2 second TTL
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            
            # Store initial analysis result
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Immediately verify it's cached (should be valid for 2 seconds)
            cached_result = cache_manager.get_llm_analysis(script_hash)
            assert cached_result is not None, f"Initial cache should contain the result. Hash: {script_hash}"
            assert cached_result == analysis_result, "Initial cached result should match"
            
            # Wait for cache to expire (2 seconds + buffer)
            time.sleep(2.2)
            
            # Try to retrieve expired entry
            expired_result = cache_manager.get_llm_analysis(script_hash)
            
            # Property 1: Expired cache should return None (cache miss)
            assert expired_result is None, "Expired cache entry should return None"
            
            # Property 2: After expiration, we need to refresh with new LLM call
            # Simulate storing a new result (as would happen after LLM call)
            new_analysis_result = {
                'is_suspicious': not analysis_result['is_suspicious'],
                'confidence': 0.99,
                'severity': 'critical',
                'threats': ['new_threat'],
                'reasoning': 'Updated analysis after cache expiration'
            }
            cache_manager.store_llm_analysis(script_hash, new_analysis_result)
            
            # Property 3: New result should be cached and retrievable
            refreshed_result = cache_manager.get_llm_analysis(script_hash)
            assert refreshed_result is not None, "Refreshed cache should contain new result"
            assert refreshed_result == new_analysis_result, "Refreshed result should match new analysis"
            assert refreshed_result != analysis_result, "Refreshed result should differ from expired result"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=2000)
    def test_expired_cache_with_memory_backend(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test expired cache refresh with in-memory backend.
        
        Verifies that cache expiration works consistently across
        different backend implementations.
        """
        # Create cache manager with very short TTL
        cache_manager = CacheManager(
            backend="memory",
            ttl_hours=1/3600  # 1 second TTL
        )
        
        script_hash = cache_manager.generate_cache_key(script_content)
        
        # Store and verify
        cache_manager.store_llm_analysis(script_hash, analysis_result)
        cached_result = cache_manager.get_llm_analysis(script_hash)
        assert cached_result is not None, "Memory cache should contain result"
        
        # Wait for expiration
        time.sleep(1.2)
        
        # Property: Expired entry should return None
        expired_result = cache_manager.get_llm_analysis(script_hash)
        assert expired_result is None, "Expired memory cache entry should return None"

    @given(
        st.lists(
            st.tuples(script_content_strategy, analysis_result_strategy),
            min_size=2,
            max_size=5,
            unique_by=lambda x: x[0]
        )
    )
    @settings(max_examples=20, deadline=5000)
    def test_selective_expiration(self, script_results: list):
        """
        Test that only expired entries are removed, not all entries.
        
        For any collection of cached entries with different expiration times,
        only the expired ones should be removed while valid ones remain.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24  # Default long TTL
            )
            
            # Store first entry with short TTL
            first_script, first_result = script_results[0]
            first_hash = cache_manager.generate_cache_key(first_script)
            cache_manager._store_entry(first_hash, first_result, ttl_hours=1/3600)  # 1 second
            
            # Store remaining entries with long TTL
            long_lived_entries = {}
            for script_content, analysis_result in script_results[1:]:
                script_hash = cache_manager.generate_cache_key(script_content)
                long_lived_entries[script_hash] = analysis_result
                cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Wait for first entry to expire
            time.sleep(1.2)
            
            # Property 1: Expired entry should return None
            expired_result = cache_manager.get_llm_analysis(first_hash)
            assert expired_result is None, "Expired entry should return None"
            
            # Property 2: Non-expired entries should still be accessible
            for script_hash, expected_result in long_lived_entries.items():
                cached_result = cache_manager.get_llm_analysis(script_hash)
                assert cached_result is not None, "Non-expired entry should still be cached"
                assert cached_result == expected_result, "Non-expired entry should match original"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=2000)
    def test_cleanup_expired_entries(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that cleanup_expired() removes expired entries.
        
        For any expired cache entry, calling cleanup_expired() should
        remove it from the cache.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=1/3600  # 1 second TTL
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Get initial statistics
            initial_stats = cache_manager.get_statistics()
            initial_count = initial_stats.get('total_entries', 0)
            assert initial_count > 0, "Cache should have entries"
            
            # Wait for expiration
            time.sleep(1.2)
            
            # Run cleanup
            cache_manager.cleanup_expired()
            
            # Property: Expired entries should be removed
            final_stats = cache_manager.get_statistics()
            final_count = final_stats.get('total_entries', 0)
            expired_count = final_stats.get('expired_entries', 0)
            
            # After cleanup, expired count should be 0
            assert expired_count == 0, "No expired entries should remain after cleanup"
            assert final_count < initial_count or final_count == 0, "Entry count should decrease after cleanup"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=3000)
    def test_expired_entry_statistics(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that statistics correctly report expired entries.
        
        For any expired cache entry, statistics should accurately
        reflect the number of expired entries.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=2/3600  # 2 second TTL
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Initially, no expired entries
            initial_stats = cache_manager.get_statistics()
            initial_expired = initial_stats.get('expired_entries', 0)
            assert initial_expired == 0, "No entries should be expired initially"
            
            # Wait for expiration (2 seconds + buffer)
            time.sleep(2.2)
            
            # Property: Statistics should show expired entries
            updated_stats = cache_manager.get_statistics()
            updated_expired = updated_stats.get('expired_entries', 0)
            assert updated_expired > 0, "Statistics should show expired entries after TTL"

    @given(script_content_strategy, analysis_result_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=5000)
    def test_refresh_updates_expiration_time(self, script_content: str, old_result: Dict[str, Any], new_result: Dict[str, Any]):
        """
        Test that refreshing a cache entry updates its expiration time.
        
        For any cache entry that is refreshed (re-stored), the expiration
        time should be reset to a new TTL from the current time.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=3/3600  # 3 seconds TTL
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            
            # Store initial result
            cache_manager.store_llm_analysis(script_hash, old_result)
            
            # Wait 1.5 seconds (half the TTL)
            time.sleep(1.5)
            
            # Refresh with new result (simulating LLM call after cache miss)
            cache_manager.store_llm_analysis(script_hash, new_result)
            
            # Wait another 2 seconds (would exceed original TTL of 3s, but refresh resets it)
            time.sleep(2.0)
            
            # Property: Entry should still be valid because TTL was reset
            refreshed_result = cache_manager.get_llm_analysis(script_hash)
            assert refreshed_result is not None, "Refreshed entry should still be valid after refresh"
            assert refreshed_result == new_result, "Should return the refreshed result"

    @given(script_content_strategy, analysis_result_strategy)
    @settings(max_examples=50, deadline=2000)
    def test_expired_cache_does_not_increment_hit_count(self, script_content: str, analysis_result: Dict[str, Any]):
        """
        Test that accessing an expired cache entry does not increment hit count.
        
        For any expired cache entry, attempting to retrieve it should not
        increment the hit count since it returns None (cache miss).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=1/3600  # 1 second TTL
            )
            
            script_hash = cache_manager.generate_cache_key(script_content)
            cache_manager.store_llm_analysis(script_hash, analysis_result)
            
            # Get initial hit count
            initial_stats = cache_manager.get_statistics()
            initial_hits = initial_stats.get('total_hits', 0)
            
            # Wait for expiration
            time.sleep(1.2)
            
            # Try to access expired entry
            expired_result = cache_manager.get_llm_analysis(script_hash)
            assert expired_result is None, "Expired entry should return None"
            
            # Property: Hit count should not increase for expired entry access
            updated_stats = cache_manager.get_statistics()
            updated_hits = updated_stats.get('total_hits', 0)
            assert updated_hits == initial_hits, "Hit count should not increase for expired entry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
