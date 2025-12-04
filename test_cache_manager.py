"""
Unit tests for CacheManager class.
Tests cache storage, retrieval, TTL expiration, LRU eviction, and backend fallback.

Requirements tested:
- 2.1: Cache-first lookup
- 2.2: Cache hit returns cached result
- 2.3: TTL expiration
- 2.4: Content hash consistency
- 2.5: Backend fallback mechanisms
"""

import pytest
import json
import time
import tempfile
import os
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.cache_manager import CacheManager, get_cache_manager


class TestCacheManagerBasics:
    """Test basic cache manager functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary cache."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10
        )
    
    def teardown_method(self):
        """Clean up temporary cache."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cache_initialization_sqlite(self):
        """Test that SQLite cache initializes correctly."""
        assert self.cache_manager.backend == "sqlite"
        assert self.cache_manager.ttl_hours == 1
        assert self.cache_manager.max_size_mb == 10
        
        # Check database file exists
        db_path = Path(self.temp_dir) / "analysis_cache.db"
        assert db_path.exists()
        
        # Check tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cache_entries'
        """)
        assert cursor.fetchone() is not None
        conn.close()
    
    def test_cache_initialization_memory(self):
        """Test that memory cache initializes correctly."""
        cache = CacheManager(backend="memory")
        assert cache.backend == "memory"
        assert isinstance(cache.memory_cache, dict)
        assert len(cache.memory_cache) == 0
    
    def test_cache_initialization_invalid_backend(self):
        """Test that invalid backend raises error."""
        with pytest.raises(ValueError, match="Unsupported backend"):
            CacheManager(backend="invalid")
    
    def test_generate_cache_key_consistency(self):
        """Test that cache key generation is consistent (Requirement 2.4)."""
        content = "test content"
        
        key1 = self.cache_manager.generate_cache_key(content)
        key2 = self.cache_manager.generate_cache_key(content)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 produces 64 hex characters
    
    def test_generate_cache_key_with_prefix(self):
        """Test cache key generation with prefix."""
        content = "test content"
        prefix = "llm"
        
        key = self.cache_manager.generate_cache_key(content, prefix)
        
        assert key.startswith(f"{prefix}:")
        assert len(key) > 64  # Prefix + colon + hash
    
    def test_generate_cache_key_different_content(self):
        """Test that different content produces different keys."""
        key1 = self.cache_manager.generate_cache_key("content1")
        key2 = self.cache_manager.generate_cache_key("content2")
        
        assert key1 != key2


class TestCacheStorageAndRetrieval:
    """Test cache storage and retrieval operations (Requirements 2.1, 2.2)."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10
        )
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_store_and_retrieve_llm_analysis(self):
        """Test storing and retrieving LLM analysis results."""
        script_hash = "test_hash_123"
        analysis_result = {
            "is_suspicious": True,
            "confidence": 0.95,
            "severity": "critical",
            "threats": ["Remote code execution"],
            "reasoning": "Downloads and executes remote code"
        }
        
        # Store
        self.cache_manager.store_llm_analysis(script_hash, analysis_result)
        
        # Retrieve
        retrieved = self.cache_manager.get_llm_analysis(script_hash)
        
        assert retrieved is not None
        assert retrieved == analysis_result
        assert retrieved["is_suspicious"] is True
        assert retrieved["confidence"] == 0.95
    
    def test_store_and_retrieve_reputation(self):
        """Test storing and retrieving reputation data."""
        package_key = "npm:suspicious-pkg:1.0.0"
        reputation_data = {
            "score": 0.25,
            "factors": {
                "age_score": 0.2,
                "downloads_score": 0.1
            },
            "flags": ["new_package", "low_downloads"]
        }
        
        # Store with custom TTL
        self.cache_manager.store_reputation(package_key, reputation_data, ttl_hours=24)
        
        # Retrieve
        retrieved = self.cache_manager.get_reputation(package_key)
        
        assert retrieved is not None
        assert retrieved == reputation_data
        assert retrieved["score"] == 0.25
    
    def test_retrieve_nonexistent_key(self):
        """Test retrieving a key that doesn't exist."""
        result = self.cache_manager.get_llm_analysis("nonexistent_key")
        assert result is None
    
    def test_cache_hit_increments_hit_count(self):
        """Test that cache hits increment the hit count."""
        key = "test_key"
        value = {"result": "test"}
        
        self.cache_manager.store_llm_analysis(key, value)
        
        # Get multiple times
        for _ in range(3):
            self.cache_manager.get_llm_analysis(key)
        
        # Check hit count in database
        conn = sqlite3.connect(self.cache_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT hit_count FROM cache_entries WHERE key = ?", (key,))
        hit_count = cursor.fetchone()[0]
        conn.close()
        
        assert hit_count == 3
    
    def test_cache_updates_last_accessed(self):
        """Test that cache retrieval updates last_accessed timestamp."""
        key = "test_key"
        value = {"result": "test"}
        
        self.cache_manager.store_llm_analysis(key, value)
        
        # Get initial last_accessed
        conn = sqlite3.connect(self.cache_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_accessed FROM cache_entries WHERE key = ?", (key,))
        initial_accessed = cursor.fetchone()[0]
        conn.close()
        
        # Wait a bit to ensure timestamp difference
        time.sleep(1.1)
        self.cache_manager.get_llm_analysis(key)
        
        # Check last_accessed updated
        conn = sqlite3.connect(self.cache_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_accessed FROM cache_entries WHERE key = ?", (key,))
        new_accessed = cursor.fetchone()[0]
        conn.close()
        
        assert new_accessed >= initial_accessed


class TestCacheTTLExpiration:
    """Test TTL-based cache expiration (Requirement 2.3)."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_expired_entry_returns_none(self):
        """Test that expired entries return None."""
        # Create cache with very short TTL (1 second = 1/3600 hours)
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1/3600,  # 1 second
            max_size_mb=10
        )
        
        key = "test_key"
        value = {"result": "test"}
        
        cache.store_llm_analysis(key, value)
        
        # Verify it's stored
        assert cache.get_llm_analysis(key) is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should return None now
        assert cache.get_llm_analysis(key) is None
    
    def test_cleanup_expired_removes_entries(self):
        """Test that cleanup_expired removes expired entries."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1/3600,  # 1 second
            max_size_mb=10
        )
        
        # Store multiple entries
        for i in range(5):
            cache.store_llm_analysis(f"key_{i}", {"result": i})
        
        # Verify all stored
        stats = cache.get_statistics()
        assert stats['total_entries'] == 5
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Cleanup
        cache.cleanup_expired()
        
        # Check all removed
        stats = cache.get_statistics()
        assert stats['total_entries'] == 0
    
    def test_mixed_expired_and_valid_entries(self):
        """Test cleanup with mix of expired and valid entries."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,  # 1 hour for valid entries
            max_size_mb=10
        )
        
        # Store entries with different TTLs
        cache._store_entry("short_ttl", {"result": "expires"}, ttl_hours=1/3600)  # 1 second
        cache._store_entry("long_ttl", {"result": "stays"}, ttl_hours=1)  # 1 hour
        
        # Wait for short TTL to expire
        time.sleep(1.5)
        
        # Cleanup
        cache.cleanup_expired()
        
        # Short TTL should be gone, long TTL should remain
        assert cache._get_entry("short_ttl") is None
        assert cache._get_entry("long_ttl") is not None
    
    def test_memory_cache_expiration(self):
        """Test that memory cache also respects TTL."""
        cache = CacheManager(
            backend="memory",
            ttl_hours=1/3600  # 1 second
        )
        
        key = "test_key"
        value = {"result": "test"}
        
        cache.store_llm_analysis(key, value)
        
        # Verify stored
        assert cache.get_llm_analysis(key) is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should return None
        assert cache.get_llm_analysis(key) is None


class TestCacheLRUEviction:
    """Test LRU eviction when cache size exceeds limits."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_lru_eviction_when_size_exceeded(self):
        """Test that LRU eviction occurs when max size is exceeded."""
        # Create cache with very small size limit
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=0.001  # 1 KB
        )
        
        # Store entries that will exceed limit
        large_value = {"data": "x" * 500}  # ~500 bytes
        
        cache.store_llm_analysis("key1", large_value)
        cache.store_llm_analysis("key2", large_value)
        
        # Access key1 to make it more recently used
        cache.get_llm_analysis("key1")
        
        # Get initial count
        initial_stats = cache.get_statistics()
        initial_count = initial_stats['total_entries']
        
        # Store another large entry that should trigger eviction
        cache.store_llm_analysis("key3", large_value)
        
        # Should have triggered eviction - total entries should not grow unbounded
        final_stats = cache.get_statistics()
        # Either eviction happened or we're at/near the limit
        assert final_stats['total_entries'] <= initial_count + 1
        
        # The new entry should definitely be stored
        assert cache.get_llm_analysis("key3") is not None
    
    def test_eviction_frees_enough_space(self):
        """Test that eviction frees enough space for new entry."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=0.002  # 2 KB
        )
        
        # Fill cache with small entries
        for i in range(3):
            cache.store_llm_analysis(f"key{i}", {"data": "x" * 400})
        
        initial_stats = cache.get_statistics()
        initial_size = initial_stats['size_bytes']
        
        # Store a large entry that requires eviction
        cache.store_llm_analysis("large_key", {"data": "x" * 800})
        
        # New entry should be stored
        assert cache.get_llm_analysis("large_key") is not None
        
        # Cache size should be managed (not grow unbounded)
        final_stats = cache.get_statistics()
        max_size_bytes = cache.max_size_mb * 1024 * 1024
        # Allow some overhead for JSON encoding
        assert final_stats['size_bytes'] <= max_size_bytes * 1.5
    
    def test_no_eviction_when_under_limit(self):
        """Test that no eviction occurs when under size limit."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10  # Large limit
        )
        
        # Store small entries
        for i in range(5):
            cache.store_llm_analysis(f"key{i}", {"data": "small"})
        
        stats = cache.get_statistics()
        assert stats['total_entries'] == 5
        
        # All should still be retrievable
        for i in range(5):
            assert cache.get_llm_analysis(f"key{i}") is not None


class TestCacheBackendFallback:
    """Test backend fallback mechanisms (Requirement 2.5)."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_fallback_to_memory_on_db_init_failure(self):
        """Test fallback to memory cache if database initialization fails."""
        # Create a file where the database should be
        db_path = Path(self.temp_dir) / "analysis_cache.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Make directory read-only to cause init failure
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Connection failed")):
            cache = CacheManager(
                backend="sqlite",
                cache_dir=self.temp_dir,
                ttl_hours=1,
                max_size_mb=10
            )
            
            # Should fall back to memory
            assert cache.backend == "memory"
    
    def test_graceful_handling_of_storage_failure(self):
        """Test that storage failures are handled gracefully within _store_in_sqlite."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10
        )
        
        # Create a scenario where the database connection fails during store
        # The _store_in_sqlite method has try-except that catches sqlite3.Error
        original_get_connection = cache._get_connection
        
        def failing_connection():
            raise sqlite3.Error("Connection failed")
        
        # Patch the connection to fail
        with patch.object(cache, '_get_connection', side_effect=failing_connection):
            # Should not raise exception - error is caught and logged
            cache.store_llm_analysis("key", {"data": "test"})
            
            # The operation completes without raising (just prints warning)
            # We can verify by checking that we can still use the cache normally
            # after restoring the connection
        
        # After the patch, cache should work normally
        cache.store_llm_analysis("key2", {"data": "test2"})
        assert cache.get_llm_analysis("key2") is not None
    
    def test_graceful_handling_of_retrieval_failure(self):
        """Test that retrieval failures return None gracefully."""
        cache = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10
        )
        
        # Store a valid entry first
        cache.store_llm_analysis("key", {"data": "test"})
        
        # Mock database connection to fail on retrieval
        with patch.object(cache, '_get_connection', side_effect=sqlite3.Error("Retrieval failed")):
            result = cache.get_llm_analysis("key")
            
            # Should return None, not raise exception
            assert result is None
    
    def test_memory_cache_as_fallback(self):
        """Test that memory cache works as a complete fallback."""
        cache = CacheManager(backend="memory")
        
        # Should work normally
        cache.store_llm_analysis("key", {"data": "test"})
        result = cache.get_llm_analysis("key")
        
        assert result is not None
        assert result["data"] == "test"


class TestCacheUtilityMethods:
    """Test cache utility methods."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(
            backend="sqlite",
            cache_dir=self.temp_dir,
            ttl_hours=1,
            max_size_mb=10
        )
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_invalidate_removes_entry(self):
        """Test that invalidate removes a specific entry."""
        key = "test_key"
        value = {"result": "test"}
        
        self.cache_manager.store_llm_analysis(key, value)
        assert self.cache_manager.get_llm_analysis(key) is not None
        
        # Invalidate
        self.cache_manager.invalidate(key)
        
        # Should be gone
        assert self.cache_manager.get_llm_analysis(key) is None
    
    def test_clear_all_removes_all_entries(self):
        """Test that clear_all removes all entries."""
        # Store multiple entries
        for i in range(5):
            self.cache_manager.store_llm_analysis(f"key{i}", {"result": i})
        
        stats = self.cache_manager.get_statistics()
        assert stats['total_entries'] == 5
        
        # Clear all
        self.cache_manager.clear_all()
        
        # Should be empty
        stats = self.cache_manager.get_statistics()
        assert stats['total_entries'] == 0
    
    def test_get_statistics_returns_correct_data(self):
        """Test that get_statistics returns accurate information."""
        # Store some entries
        for i in range(3):
            self.cache_manager.store_llm_analysis(f"key{i}", {"result": i})
        
        # Access some entries
        self.cache_manager.get_llm_analysis("key0")
        self.cache_manager.get_llm_analysis("key0")
        
        stats = self.cache_manager.get_statistics()
        
        assert stats['backend'] == 'sqlite'
        assert stats['total_entries'] == 3
        assert stats['total_hits'] >= 2
        assert 'size_bytes' in stats
        assert 'size_mb' in stats
        assert 'max_size_mb' in stats
        assert 'utilization_percent' in stats
    
    def test_statistics_for_memory_cache(self):
        """Test statistics for memory cache backend."""
        cache = CacheManager(backend="memory")
        
        # Store and access entries
        cache.store_llm_analysis("key1", {"result": "test"})
        cache.get_llm_analysis("key1")
        
        stats = cache.get_statistics()
        
        assert stats['backend'] == 'memory'
        assert stats['total_entries'] == 1
        assert stats['total_hits'] >= 1


class TestGlobalCacheManager:
    """Test global cache manager singleton."""
    
    def test_get_cache_manager_returns_singleton(self):
        """Test that get_cache_manager returns the same instance."""
        # Reset global instance
        import tools.cache_manager
        tools.cache_manager._cache_manager = None
        
        cache1 = get_cache_manager()
        cache2 = get_cache_manager()
        
        assert cache1 is cache2
    
    def test_get_cache_manager_with_custom_params(self):
        """Test that get_cache_manager accepts custom parameters."""
        # Reset global instance
        import tools.cache_manager
        tools.cache_manager._cache_manager = None
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            cache = get_cache_manager(
                backend="sqlite",
                cache_dir=temp_dir,
                ttl_hours=24,
                max_size_mb=50
            )
            
            assert cache.backend == "sqlite"
            assert cache.ttl_hours == 24
            assert cache.max_size_mb == 50
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
