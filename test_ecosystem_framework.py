"""
Integration tests for the ecosystem analyzer framework.
"""

import pytest
import os
from pathlib import Path

# Import analyzers to trigger auto-registration
import tools.npm_analyzer
import tools.python_analyzer
from tools.ecosystem_analyzer import get_registry, get_analyzer, detect_ecosystem


def test_registry_initialization():
    """Test that the registry is properly initialized."""
    registry = get_registry()
    assert registry is not None
    ecosystems = registry.get_all_ecosystems()
    assert 'npm' in ecosystems
    assert 'pypi' in ecosystems


def test_npm_analyzer_registration():
    """Test that npm analyzer is registered."""
    analyzer = get_analyzer('npm')
    assert analyzer is not None
    assert analyzer.ecosystem_name == 'npm'


def test_python_analyzer_registration():
    """Test that Python analyzer is registered."""
    analyzer = get_analyzer('pypi')
    assert analyzer is not None
    assert analyzer.ecosystem_name == 'pypi'


def test_npm_manifest_detection():
    """Test npm manifest file detection."""
    analyzer = get_analyzer('npm')
    
    # Test with test_nested_deps directory
    if os.path.exists('test_nested_deps'):
        files = analyzer.detect_manifest_files('test_nested_deps')
        assert len(files) > 0
        assert any('package.json' in f for f in files)


def test_npm_dependency_extraction():
    """Test npm dependency extraction."""
    analyzer = get_analyzer('npm')
    
    # Test with sample package.json
    if os.path.exists('artifacts/sample-package.json'):
        deps = analyzer.extract_dependencies('artifacts/sample-package.json')
        assert len(deps) > 0
        assert all('name' in d for d in deps)
        assert all('version' in d for d in deps)
        assert all('ecosystem' in d for d in deps)


def test_python_dependency_extraction():
    """Test Python dependency extraction."""
    analyzer = get_analyzer('pypi')
    
    # Test with sample requirements.txt
    if os.path.exists('artifacts/sample-requirements.txt'):
        deps = analyzer.extract_dependencies('artifacts/sample-requirements.txt')
        assert len(deps) > 0
        assert all('name' in d for d in deps)
        assert all('ecosystem' in d for d in deps)


def test_ecosystem_auto_detection():
    """Test automatic ecosystem detection."""
    # Test with npm project
    if os.path.exists('test_nested_deps'):
        ecosystem = detect_ecosystem('test_nested_deps')
        assert ecosystem == 'npm'


def test_npm_registry_url():
    """Test npm registry URL generation."""
    analyzer = get_analyzer('npm')
    
    # Test regular package
    url = analyzer.get_registry_url('express')
    assert url == 'https://registry.npmjs.org/express'
    
    # Test scoped package
    url = analyzer.get_registry_url('@babel/core')
    assert '%40babel' in url


def test_python_registry_url():
    """Test Python registry URL generation."""
    analyzer = get_analyzer('pypi')
    
    url = analyzer.get_registry_url('requests')
    assert url == 'https://pypi.org/pypi/requests/json'


def test_npm_malicious_patterns():
    """Test npm malicious pattern retrieval."""
    analyzer = get_analyzer('npm')
    patterns = analyzer.get_malicious_patterns()
    
    assert 'critical' in patterns
    assert 'high' in patterns
    assert 'medium' in patterns
    assert len(patterns['critical']) > 0


def test_python_malicious_patterns():
    """Test Python malicious pattern retrieval."""
    analyzer = get_analyzer('pypi')
    patterns = analyzer.get_malicious_patterns()
    
    assert 'critical' in patterns
    assert 'high' in patterns
    assert 'medium' in patterns
    assert len(patterns['critical']) > 0


def test_npm_install_script_analysis():
    """Test npm install script analysis."""
    analyzer = get_analyzer('npm')
    
    # Test with test_nested_deps if it exists
    if os.path.exists('test_nested_deps'):
        findings = analyzer.analyze_install_scripts('test_nested_deps')
        # Should return a list (may be empty if no malicious scripts)
        assert isinstance(findings, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
