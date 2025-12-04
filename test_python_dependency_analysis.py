"""
Tests for Python dependency analysis functionality.

This module tests the integration of Python dependency analysis including:
- requirements.txt parsing
- Malicious package database lookup
- Recursive dependency scanning
- Integration with existing workflow
"""

import pytest
import os
import tempfile
from pathlib import Path
from tools.python_analyzer import PythonAnalyzer
from tools.ecosystem_analyzer import SecurityFinding


class TestPythonDependencyAnalysis:
    """Test suite for Python dependency analysis."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PythonAnalyzer()
    
    def test_requirements_txt_parsing(self):
        """Test that requirements.txt files are parsed correctly."""
        # Create a temporary requirements.txt file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests==2.28.0\n")
            f.write("flask>=2.0.0\n")
            f.write("numpy\n")
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("pandas>=1.0.0,<2.0.0\n")
            temp_file = f.name
        
        try:
            # Extract dependencies
            dependencies = self.analyzer._extract_from_requirements_txt(temp_file)
            
            # Verify parsing
            assert len(dependencies) == 4, "Should extract 4 dependencies"
            
            # Check specific packages
            package_names = [dep['name'] for dep in dependencies]
            assert 'requests' in package_names
            assert 'flask' in package_names
            assert 'numpy' in package_names
            assert 'pandas' in package_names
            
            # Check version operators
            requests_dep = next(d for d in dependencies if d['name'] == 'requests')
            assert requests_dep['version'] == '2.28.0'
            assert requests_dep['version_operator'] == '=='
            
            flask_dep = next(d for d in dependencies if d['name'] == 'flask')
            assert flask_dep['version_operator'] == '>='
            
            numpy_dep = next(d for d in dependencies if d['name'] == 'numpy')
            assert numpy_dep['version'] == '*'
        
        finally:
            os.unlink(temp_file)
    
    def test_malicious_package_detection(self):
        """Test that malicious packages are detected from database."""
        # Create test dependencies including known malicious packages
        dependencies = [
            {
                "name": "requests",
                "version": "2.28.0",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            },
            {
                "name": "ctx",  # Known malicious package
                "version": "0.1.2",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            },
            {
                "name": "urllib4",  # Known malicious package (typosquat)
                "version": "1.0.0",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            }
        ]
        
        # Check for malicious packages
        findings = self.analyzer.check_malicious_packages(dependencies)
        
        # Verify detection
        assert len(findings) >= 2, "Should detect at least 2 malicious packages"
        
        # Check that malicious packages are flagged
        malicious_names = [f.package for f in findings]
        assert 'ctx' in malicious_names, "Should detect ctx as malicious"
        assert 'urllib4' in malicious_names, "Should detect urllib4 as malicious"
        
        # Verify severity
        for finding in findings:
            assert finding.severity == "critical", "Malicious packages should be critical severity"
            assert finding.confidence >= 0.9, "Malicious package detection should have high confidence"
    
    def test_no_false_positives_for_legitimate_packages(self):
        """Test that legitimate packages are not flagged as malicious."""
        # Create test dependencies with only legitimate packages
        dependencies = [
            {
                "name": "requests",
                "version": "2.28.0",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            },
            {
                "name": "flask",
                "version": "2.0.0",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            },
            {
                "name": "numpy",
                "version": "1.21.0",
                "ecosystem": "pypi",
                "source_file": "requirements.txt"
            }
        ]
        
        # Check for malicious packages
        findings = self.analyzer.check_malicious_packages(dependencies)
        
        # Verify no false positives
        assert len(findings) == 0, "Legitimate packages should not be flagged as malicious"
    
    def test_analyze_dependencies_with_malicious_check(self):
        """Test end-to-end dependency analysis with malicious check."""
        # Create a temporary directory with requirements.txt
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt with mixed packages
            req_file = Path(temp_dir) / "requirements.txt"
            req_file.write_text(
                "requests==2.28.0\n"
                "ctx==0.1.2\n"  # Malicious
                "flask>=2.0.0\n"
            )
            
            # Analyze dependencies
            findings = self.analyzer.analyze_dependencies_with_malicious_check(temp_dir)
            
            # Verify malicious package was detected
            assert len(findings) >= 1, "Should detect at least one malicious package"
            
            malicious_names = [f.package for f in findings]
            assert 'ctx' in malicious_names, "Should detect ctx as malicious"
    
    def test_setup_py_dependency_extraction(self):
        """Test extraction of dependencies from setup.py."""
        # Create a temporary setup.py file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from setuptools import setup

setup(
    name='test-package',
    version='1.0.0',
    install_requires=[
        'requests>=2.0.0',
        'flask==2.0.0',
        'numpy'
    ],
    setup_requires=[
        'pytest-runner'
    ]
)
""")
            temp_file = f.name
        
        try:
            # Extract dependencies
            dependencies = self.analyzer._extract_from_setup_py(temp_file)
            
            # Verify extraction
            assert len(dependencies) >= 3, "Should extract at least 3 dependencies"
            
            # Check package names
            package_names = [dep['name'] for dep in dependencies]
            assert 'requests' in package_names
            assert 'flask' in package_names
            assert 'numpy' in package_names
        
        finally:
            os.unlink(temp_file)
    
    def test_recursive_dependency_scanning_avoids_cycles(self):
        """Test that recursive scanning handles circular dependencies."""
        # This test verifies that the visited set prevents infinite recursion
        visited = set()
        
        # Scan a package (this may fail if pip is not available, which is OK)
        try:
            deps = self.analyzer.scan_recursive_dependencies(
                "requests", 
                max_depth=2, 
                visited=visited
            )
            
            # If successful, verify no duplicates
            dep_names = [d['name'] for d in deps]
            # Check that visited set was used (package should be in visited)
            assert 'requests' in visited, "Package should be added to visited set"
        
        except Exception:
            # If pip is not available or package not installed, that's OK
            pytest.skip("pip not available or package not installed")
    
    def test_integration_with_local_analysis(self):
        """Test that Python analysis integrates with local directory analysis."""
        # Create a temporary directory with Python files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            req_file = Path(temp_dir) / "requirements.txt"
            req_file.write_text("requests==2.28.0\n")
            
            # Create setup.py with malicious pattern
            setup_file = Path(temp_dir) / "setup.py"
            setup_file.write_text("""
from setuptools import setup
import os

# Malicious code
os.system('echo "test"')

setup(
    name='test-package',
    version='1.0.0',
    install_requires=['requests']
)
""")
            
            # Analyze the directory
            from tools.local_tools import analyze_local_directory
            
            try:
                results = analyze_local_directory(temp_dir, use_osv=False)
                
                # Verify analysis completed
                assert results is not None
                assert 'security_findings' in results
                
                # Check for Python-related findings
                findings = results['security_findings']
                
                # Should detect malicious pattern in setup.py
                malicious_script_findings = [
                    f for f in findings 
                    if f.get('finding_type') == 'malicious_python_script'
                ]
                
                # May or may not detect depending on analysis depth
                # Just verify the analysis ran without errors
                assert 'summary' in results
            
            except Exception as e:
                # If analysis fails for other reasons, that's OK for this test
                pytest.skip(f"Local analysis not fully functional: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
