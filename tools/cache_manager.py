"""
Intelligent caching system for Multi-Agent Security Analysis System.
Provides SQLite-based caching for LLM analysis results and package reputation data.
"""

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from contextlib import contextmanager


class CacheManager:
    """
    Manages intelligent caching of LLM analysis results and reputation data.
    
    Features:
    - SQLite backend for persistent storage
    - Content-based hashing (SHA-256) for cache keys
    - TTL-based expiration
    - LRU eviction when storage limits are exceeded
    - Graceful fallback on errors
    """
    
    def __init__(
        self,
        backend: str = "sqlite",
        cache_dir: str = ".cache",
        ttl_hours: int = 168,  # 7 days default
        max_size_mb: int = 100
    ):
        """
        Initialize cache manager.
        
        Args:
            backend: Cache backend type ("sqlite", "memory")
            cache_dir: Directory for cache storage
            ttl_hours: Time-to-live for cache entries in hours
            max_size_mb: Maximum cache size in megabytes
        """
        self.backend = backend
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.max_size_mb = max_size_mb
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if backend == "sqlite":
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.cache_dir / "analysis_cache.db"
            self._init_database()
        elif backend == "memory":
            # In-memory cache only
            pass
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def _init_database(self):
        """Initialize SQLite database with schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL,
                        hit_count INTEGER DEFAULT 0,
                        last_accessed INTEGER NOT NULL,
                        size_bytes INTEGER NOT NULL
                    )
                """)
                
                # Create index for expiration queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON cache_entries(expires_at)
                """)
                
                # Create index for LRU eviction
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_last_accessed 
                    ON cache_entries(last_accessed)
                """)
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Warning: Failed to initialize cache database: {e}")
            # Fall back to memory cache
            self.backend = "memory"
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            yield conn
        finally:
            conn.close()
    
    def generate_cache_key(self, content: str, prefix: str = "") -> str:
        """
        Generate SHA-256 hash for cache key.
        
        Args:
            content: Content to hash
            prefix: Optional prefix for key namespacing
            
        Returns:
            SHA-256 hash string
        """
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        
        if prefix:
            return f"{prefix}:{hash_str}"
        return hash_str
    
    def get_llm_analysis(self, script_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached LLM analysis result.
        
        Args:
            script_hash: Hash of the script content
            
        Returns:
            Cached analysis result or None if not found/expired
        """
        return self._get_entry(script_hash)
    
    def store_llm_analysis(self, script_hash: str, result: Dict[str, Any]):
        """
        Store LLM analysis result with TTL.
        
        Args:
            script_hash: Hash of the script content
            result: Analysis result to cache
        """
        self._store_entry(script_hash, result, self.ttl_hours)
    
    def get_reputation(self, package_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached reputation data.
        
        Args:
            package_key: Package identifier (ecosystem:package:version)
            
        Returns:
            Cached reputation data or None if not found/expired
        """
        return self._get_entry(package_key)
    
    def store_reputation(self, package_key: str, reputation_data: Dict[str, Any], ttl_hours: int = 24):
        """
        Store package reputation data with custom TTL.
        
        Args:
            package_key: Package identifier (ecosystem:package:version)
            reputation_data: Reputation data to cache
            ttl_hours: Time-to-live in hours (default: 24 hours)
        """
        self._store_entry(package_key, reputation_data, ttl_hours)
    
    def _get_entry(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Internal method to retrieve cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if self.backend == "memory":
            return self._get_from_memory(key)
        elif self.backend == "sqlite":
            return self._get_from_sqlite(key)
        return None
    
    def _store_entry(self, key: str, value: Dict[str, Any], ttl_hours: int):
        """
        Internal method to store cache entry.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_hours: Time-to-live in hours
        """
        if self.backend == "memory":
            self._store_in_memory(key, value, ttl_hours)
        elif self.backend == "sqlite":
            self._store_in_sqlite(key, value, ttl_hours)
    
    def _get_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Get entry from in-memory cache."""
        if key not in self.memory_cache:
            return None
        
        entry = self.memory_cache[key]
        
        # Check expiration
        if time.time() > entry['expires_at']:
            del self.memory_cache[key]
            return None
        
        # Update hit count and last accessed
        entry['hit_count'] += 1
        entry['last_accessed'] = time.time()
        
        return entry['value']
    
    def _store_in_memory(self, key: str, value: Dict[str, Any], ttl_hours: int):
        """Store entry in in-memory cache."""
        now = time.time()
        expires_at = now + (ttl_hours * 3600)
        
        self.memory_cache[key] = {
            'value': value,
            'created_at': now,
            'expires_at': expires_at,
            'hit_count': 0,
            'last_accessed': now
        }
    
    def _get_from_sqlite(self, key: str) -> Optional[Dict[str, Any]]:
        """Get entry from SQLite cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = int(time.time())
                
                # Get entry and check expiration
                cursor.execute("""
                    SELECT value, expires_at 
                    FROM cache_entries 
                    WHERE key = ? AND expires_at > ?
                """, (key, now))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                value_json, expires_at = row
                
                # Update hit count and last accessed
                cursor.execute("""
                    UPDATE cache_entries 
                    SET hit_count = hit_count + 1, last_accessed = ?
                    WHERE key = ?
                """, (now, key))
                
                conn.commit()
                
                return json.loads(value_json)
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"Warning: Cache retrieval failed: {e}")
            return None
    
    def _store_in_sqlite(self, key: str, value: Dict[str, Any], ttl_hours: int):
        """Store entry in SQLite cache."""
        try:
            now = int(time.time())
            expires_at = now + (ttl_hours * 3600)
            value_json = json.dumps(value)
            size_bytes = len(value_json.encode('utf-8'))
            
            # Check if we need to evict entries
            self._evict_if_needed(size_bytes)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or replace entry
                cursor.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, expires_at, hit_count, last_accessed, size_bytes)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                """, (key, value_json, now, expires_at, now, size_bytes))
                
                conn.commit()
                
        except (sqlite3.Error, TypeError, ValueError) as e:
            print(f"Warning: Cache storage failed: {e}")
            # Continue without caching
    
    def _evict_if_needed(self, new_entry_size: int):
        """
        Evict old entries using LRU strategy if cache size exceeds limit.
        
        Args:
            new_entry_size: Size of the new entry to be added
        """
        if self.backend != "sqlite":
            return
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate current cache size
                cursor.execute("SELECT SUM(size_bytes) FROM cache_entries")
                result = cursor.fetchone()
                current_size = result[0] if result[0] else 0
                
                max_size_bytes = self.max_size_mb * 1024 * 1024
                
                # Check if we need to evict
                if current_size + new_entry_size > max_size_bytes:
                    # Calculate how much space we need to free
                    space_needed = (current_size + new_entry_size) - max_size_bytes
                    
                    # Get entries ordered by last accessed (LRU)
                    cursor.execute("""
                        SELECT key, size_bytes 
                        FROM cache_entries 
                        ORDER BY last_accessed ASC
                    """)
                    
                    entries_to_delete = []
                    freed_space = 0
                    
                    for key, size_bytes in cursor.fetchall():
                        entries_to_delete.append(key)
                        freed_space += size_bytes
                        
                        if freed_space >= space_needed:
                            break
                    
                    # Delete the entries
                    if entries_to_delete:
                        placeholders = ','.join('?' * len(entries_to_delete))
                        cursor.execute(
                            f"DELETE FROM cache_entries WHERE key IN ({placeholders})",
                            entries_to_delete
                        )
                        conn.commit()
                        
        except sqlite3.Error as e:
            print(f"Warning: Cache eviction failed: {e}")
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        if self.backend == "memory":
            now = time.time()
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry['expires_at'] <= now
            ]
            for key in expired_keys:
                del self.memory_cache[key]
                
        elif self.backend == "sqlite":
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    now = int(time.time())
                    
                    cursor.execute(
                        "DELETE FROM cache_entries WHERE expires_at <= ?",
                        (now,)
                    )
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"Warning: Cache cleanup failed: {e}")
    
    def invalidate(self, key: str):
        """
        Manually invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if self.backend == "memory":
            if key in self.memory_cache:
                del self.memory_cache[key]
                
        elif self.backend == "sqlite":
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"Warning: Cache invalidation failed: {e}")
    
    def clear_all(self):
        """Clear all cache entries."""
        if self.backend == "memory":
            self.memory_cache.clear()
            
        elif self.backend == "sqlite":
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cache_entries")
                    conn.commit()
                    
            except sqlite3.Error as e:
                print(f"Warning: Cache clear failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics (size, entries, hit rate, etc.)
        """
        if self.backend == "memory":
            total_entries = len(self.memory_cache)
            total_hits = sum(entry['hit_count'] for entry in self.memory_cache.values())
            
            return {
                'backend': 'memory',
                'total_entries': total_entries,
                'total_hits': total_hits,
                'size_bytes': 0,  # Not tracked for memory cache
                'max_size_mb': self.max_size_mb
            }
            
        elif self.backend == "sqlite":
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get total entries
                    cursor.execute("SELECT COUNT(*) FROM cache_entries")
                    total_entries = cursor.fetchone()[0]
                    
                    # Get total size
                    cursor.execute("SELECT SUM(size_bytes) FROM cache_entries")
                    result = cursor.fetchone()
                    total_size = result[0] if result[0] else 0
                    
                    # Get total hits
                    cursor.execute("SELECT SUM(hit_count) FROM cache_entries")
                    result = cursor.fetchone()
                    total_hits = result[0] if result[0] else 0
                    
                    # Get expired entries count
                    now = int(time.time())
                    cursor.execute(
                        "SELECT COUNT(*) FROM cache_entries WHERE expires_at <= ?",
                        (now,)
                    )
                    expired_entries = cursor.fetchone()[0]
                    
                    return {
                        'backend': 'sqlite',
                        'total_entries': total_entries,
                        'expired_entries': expired_entries,
                        'total_hits': total_hits,
                        'size_bytes': total_size,
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'max_size_mb': self.max_size_mb,
                        'utilization_percent': round((total_size / (self.max_size_mb * 1024 * 1024)) * 100, 2)
                    }
                    
            except sqlite3.Error as e:
                print(f"Warning: Failed to get cache statistics: {e}")
                return {'error': str(e)}
        
        return {}


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    backend: str = "sqlite",
    cache_dir: str = ".cache",
    ttl_hours: int = 168,
    max_size_mb: int = 100
) -> CacheManager:
    """
    Get or create global cache manager instance.
    
    Args:
        backend: Cache backend type
        cache_dir: Directory for cache storage
        ttl_hours: Default TTL in hours
        max_size_mb: Maximum cache size in MB
        
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager(
            backend=backend,
            cache_dir=cache_dir,
            ttl_hours=ttl_hours,
            max_size_mb=max_size_mb
        )
    
    return _cache_manager
