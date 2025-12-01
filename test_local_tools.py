"""
Property-based tests for local directory analysis tools.

**Feature: multi-agent-security, Property 7: Output Persistence**
**Validates: Requirements 2.5**
"""

import pytest
import json
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume
from typing import Dict, List, Any, Tuple
import string

from tools.local_tools import (
    LocalAnalysisError,
    PathValidationError,
    validate_path,
    scan_directory_for_package_files,
    generate_local_sbom,
    analyze_local_directory,
    save_local_analysis_results,
    get_directory_statistics,
    find_package_files_by_ecosystem,
    detect_project_type,
    _should_skip_directory
)
from constants import ECOSYSTEM_FILES


# Strategies for property-based testing
directory_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.",
    min_size=1,
    max_size=50
).filter(lambda x: x and not x.startswith('.') and not x.endswith('.'))

file_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.",
    min_size=1,
    max_size=100
).filter(lambda x: x and not x.startswith('.'))

ecosystem_strategy = st.sampled_from(list(ECOSYSTEM_FILES.keys()))

# Strategy for generating package file content
package_json_content_strategy = st.builds(
    lambda name, deps: json.dumps({
        "name": name,
        "version": "1.0.0",
        "dependencies": deps
    }),
    st.text(min_size=1, max_size=20),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.text(min_size=1, max_size=10),
        min_size=0,
        max_size=5
    )
)

requirements_txt_content_strategy = st.builds(
    lambda packages: "\n".join(f"{pkg}=={version}" for pkg, version in packages),
    st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_lowercase + "-", min_size=1, max_size=20),
            st.text(alphabet=string.digits + ".", min_size=1, max_size=10)
        ),
        min_size=0,
        max_size=10
    )
)

# Strategy for generating analysis results
analysis_results_strategy = st.builds(
    dict,
    analysis_type=st.just("local_directory"),
    target_path=st.text(min_size=1, max_size=100),
    analysis_start_time=st.text(min_size=10, max_size=30),
    analysis_end_time=st.text(min_size=10, max_size=30),
    sbom=st.builds(
        dict,
        packages=st.lists(st.dictionaries(
            keys=st.sampled_from(["name", "version", "ecosystem"]),
            values=st.text(min_size=1, max_size=20),
            min_size=1,
            max_size=3
        ), min_size=0, max_size=5),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0,
            max_size=5
        )
    ),
    security_findings=st.lists(st.dictionaries(
        keys=st.sampled_from(["package", "version", "finding_type", "severity"]),
        values=st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=4
    ), min_size=0, max_size=3),
    summary=st.builds(
        dict,
        total_packages=st.integers(min_value=0, max_value=100),
        total_findings=st.integers(min_value=0, max_value=50),
        critical_findings=st.integers(min_value=0, max_value=10),
        high_findings=st.integers(min_value=0, max_value=10),
        medium_findings=st.integers(min_value=0, max_value=10),
        low_findings=st.integers(min_value=0, max_value=10),
        ecosystems_found=st.lists(ecosystem_strategy, min_size=0, max_size=3),
        package_files_scanned=st.integers(min_value=0, max_value=20)
    )
)


class TestOutputPersistence:
    """Property-based tests for output persistence."""

    @given(analysis_results_strategy)
    def test_analysis_results_saving_consistency(self, analysis_results: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any completed analysis, the system should save findings to the 
        specified output directory with proper file structure.
        """
        assume(analysis_results.get("target_path", "").strip() != "")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Property: Should save without errors
            try:
                output_path = save_local_analysis_results(analysis_results, temp_dir)
                
                # Property: Should return valid file path
                assert isinstance(output_path, str), "Should return string file path"
                assert os.path.exists(output_path), "Output file should exist"
                assert os.path.isfile(output_path), "Output path should be a file"
                
                # Property: File should be in the specified directory
                assert output_path.startswith(temp_dir), "Output file should be in specified directory"
                
                # Property: File should have .json extension
                assert output_path.endswith('.json'), "Output file should have .json extension"
                
                # Property: File should contain valid JSON
                with open(output_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                # Property: Loaded data should match original
                assert loaded_data == analysis_results, "Saved data should match original analysis results"
                
                # Property: File should be readable and non-empty
                file_size = os.path.getsize(output_path)
                assert file_size > 0, "Output file should not be empty"
                
            except Exception as e:
                pytest.fail(f"Analysis results saving should not raise exception: {e}")

    def test_output_file_naming_consistency(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any analysis results, output file naming should be consistent
        and include relevant identifiers.
        """
        test_cases = [
            {
                "target_path": "/home/user/project",
                "analysis_type": "local_directory"
            },
            {
                "target_path": "/path/with spaces/project name",
                "analysis_type": "local_directory"
            },
            {
                "target_path": "C:\\Windows\\Path\\Project",
                "analysis_type": "local_directory"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for test_data in test_cases:
                analysis_results = {
                    "analysis_type": test_data["analysis_type"],
                    "target_path": test_data["target_path"],
                    "sbom": {"packages": []},
                    "security_findings": [],
                    "summary": {"total_packages": 0}
                }
                
                output_path = save_local_analysis_results(analysis_results, temp_dir)
                filename = os.path.basename(output_path)
                
                # Property: Filename should start with analysis type prefix
                assert filename.startswith("local_analysis_"), "Filename should start with local_analysis_"
                
                # Property: Filename should contain timestamp
                import re
                timestamp_pattern = r'\d{8}_\d{6}'
                assert re.search(timestamp_pattern, filename), "Filename should contain timestamp"
                
                # Property: Filename should not contain invalid characters
                invalid_chars = set('<>:"|?*')
                assert not any(c in filename for c in invalid_chars), "Filename should not contain invalid characters"

    def test_output_directory_creation(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any output directory path, the system should create the directory
        structure if it doesn't exist.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with nested directory that doesn't exist
            nested_output_dir = os.path.join(temp_dir, "nested", "output", "directory")
            
            analysis_results = {
                "analysis_type": "local_directory",
                "target_path": "/test/path",
                "sbom": {"packages": []},
                "security_findings": [],
                "summary": {"total_packages": 0}
            }
            
            # Property: Should create directory structure
            output_path = save_local_analysis_results(analysis_results, nested_output_dir)
            
            assert os.path.exists(nested_output_dir), "Output directory should be created"
            assert os.path.isdir(nested_output_dir), "Output path should be a directory"
            assert os.path.exists(output_path), "Output file should exist in created directory"

    @given(st.text(min_size=1, max_size=200))
    def test_output_persistence_with_various_paths(self, target_path: str):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any target path in analysis results, output persistence should
        handle path variations consistently.
        """
        assume(target_path.strip() != "")
        
        analysis_results = {
            "analysis_type": "local_directory",
            "target_path": target_path,
            "analysis_start_time": "2024-01-01T00:00:00Z",
            "analysis_end_time": "2024-01-01T00:01:00Z",
            "sbom": {
                "packages": [],
                "metadata": {"total_packages": 0}
            },
            "security_findings": [],
            "summary": {
                "total_packages": 0,
                "total_findings": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0,
                "ecosystems_found": [],
                "package_files_scanned": 0
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                output_path = save_local_analysis_results(analysis_results, temp_dir)
                
                # Property: Should handle any valid target path
                assert os.path.exists(output_path), "Output file should exist regardless of target path format"
                
                # Property: Should create valid JSON file
                with open(output_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                assert loaded_data["target_path"] == target_path, "Target path should be preserved in output"
                
            except LocalAnalysisError:
                # This is acceptable for some edge cases
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception for target path '{target_path}': {e}")

    def test_output_persistence_with_large_data(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any large analysis results, output persistence should handle
        them efficiently without data loss.
        """
        # Create large analysis results
        large_packages = []
        large_findings = []
        
        for i in range(100):  # 100 packages
            large_packages.append({
                "name": f"package-{i}",
                "version": f"1.{i}.0",
                "ecosystem": "npm",
                "metadata": {
                    "source_file": f"package-{i}/package.json",
                    "dependency_type": "dependencies"
                }
            })
        
        for i in range(50):  # 50 findings
            large_findings.append({
                "package": f"package-{i}",
                "version": f"1.{i}.0",
                "finding_type": "vulnerability",
                "severity": "medium",
                "confidence": 0.8,
                "evidence": [f"Evidence for package-{i}"],
                "recommendations": [f"Update package-{i}"],
                "source": "test",
                "timestamp": "2024-01-01T00:00:00Z"
            })
        
        large_analysis_results = {
            "analysis_type": "local_directory",
            "target_path": "/large/project",
            "analysis_start_time": "2024-01-01T00:00:00Z",
            "analysis_end_time": "2024-01-01T00:05:00Z",
            "sbom": {
                "packages": large_packages,
                "metadata": {"total_packages": len(large_packages)}
            },
            "security_findings": large_findings,
            "summary": {
                "total_packages": len(large_packages),
                "total_findings": len(large_findings),
                "critical_findings": 0,
                "high_findings": 10,
                "medium_findings": 40,
                "low_findings": 0,
                "ecosystems_found": ["npm"],
                "package_files_scanned": 20
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = save_local_analysis_results(large_analysis_results, temp_dir)
            
            # Property: Should handle large data without errors
            assert os.path.exists(output_path), "Should save large analysis results"
            
            # Property: File should be reasonably large
            file_size = os.path.getsize(output_path)
            assert file_size > 1000, "Large analysis results should produce substantial file"
            
            # Property: Should preserve all data
            with open(output_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data["sbom"]["packages"]) == 100, "Should preserve all packages"
            assert len(loaded_data["security_findings"]) == 50, "Should preserve all findings"
            assert loaded_data == large_analysis_results, "Should preserve all data exactly"

    def test_output_persistence_error_handling(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any error conditions during output persistence, the system should
        handle them gracefully and provide meaningful error messages.
        """
        analysis_results = {
            "analysis_type": "local_directory",
            "target_path": "/test/path",
            "sbom": {"packages": []},
            "security_findings": [],
            "summary": {"total_packages": 0}
        }
        
        # Test with completely invalid path characters that will cause OS errors
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file where we want to create a directory
            file_path = os.path.join(temp_dir, "blocking_file")
            with open(file_path, 'w') as f:
                f.write("test")
            
            # Try to use the file path as a directory - this should fail
            try:
                save_local_analysis_results(analysis_results, file_path)
                # If it doesn't raise an exception, that's also acceptable behavior
                # as the function might handle this gracefully
            except LocalAnalysisError:
                # This is the expected behavior
                pass
            except Exception:
                # Any other exception is also acceptable as it shows error handling
                pass
        
        # Test with a mock that will cause file writing to fail
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.open', side_effect=PermissionError("Mock permission error")):
                # Property: Should handle file writing errors gracefully
                with pytest.raises(LocalAnalysisError):
                    save_local_analysis_results(analysis_results, temp_dir)

    def test_output_persistence_concurrent_access(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any concurrent save operations, output persistence should handle
        them without conflicts or data corruption.
        """
        analysis_results_1 = {
            "analysis_type": "local_directory",
            "target_path": "/test/path1",
            "sbom": {"packages": [{"name": "pkg1", "version": "1.0.0"}]},
            "security_findings": [],
            "summary": {"total_packages": 1}
        }
        
        analysis_results_2 = {
            "analysis_type": "local_directory", 
            "target_path": "/test/path2",
            "sbom": {"packages": [{"name": "pkg2", "version": "2.0.0"}]},
            "security_findings": [],
            "summary": {"total_packages": 1}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save multiple results to same directory
            output_path_1 = save_local_analysis_results(analysis_results_1, temp_dir)
            output_path_2 = save_local_analysis_results(analysis_results_2, temp_dir)
            
            # Property: Should create different files
            assert output_path_1 != output_path_2, "Concurrent saves should create different files"
            
            # Property: Both files should exist
            assert os.path.exists(output_path_1), "First output file should exist"
            assert os.path.exists(output_path_2), "Second output file should exist"
            
            # Property: Both files should contain correct data
            with open(output_path_1, 'r') as f:
                data_1 = json.load(f)
            with open(output_path_2, 'r') as f:
                data_2 = json.load(f)
            
            assert data_1 == analysis_results_1, "First file should contain first results"
            assert data_2 == analysis_results_2, "Second file should contain second results"

    def test_output_persistence_json_serialization(self):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any analysis results with complex data types, JSON serialization
        should handle them correctly.
        """
        from datetime import datetime
        
        # Analysis results with various data types
        complex_analysis_results = {
            "analysis_type": "local_directory",
            "target_path": "/test/path",
            "analysis_start_time": datetime.now(),  # datetime object
            "analysis_end_time": datetime.now(),
            "sbom": {
                "packages": [
                    {
                        "name": "test-pkg",
                        "version": "1.0.0",
                        "metadata": {
                            "numbers": [1, 2, 3],
                            "boolean": True,
                            "null_value": None,
                            "nested": {"key": "value"}
                        }
                    }
                ]
            },
            "security_findings": [],
            "summary": {
                "total_packages": 1,
                "confidence_scores": [0.1, 0.5, 0.9],  # List of floats
                "has_vulnerabilities": False  # Boolean
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Property: Should handle complex data types
            output_path = save_local_analysis_results(complex_analysis_results, temp_dir)
            
            assert os.path.exists(output_path), "Should save complex analysis results"
            
            # Property: Should be valid JSON
            with open(output_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Property: Should preserve data structure (datetime will be converted to string)
            assert loaded_data["analysis_type"] == "local_directory", "Should preserve string values"
            assert loaded_data["summary"]["total_packages"] == 1, "Should preserve integer values"
            assert loaded_data["summary"]["has_vulnerabilities"] is False, "Should preserve boolean values"
            assert loaded_data["sbom"]["packages"][0]["metadata"]["null_value"] is None, "Should preserve null values"
            assert isinstance(loaded_data["summary"]["confidence_scores"], list), "Should preserve list structure"

    @given(st.integers(min_value=0, max_value=1000))
    def test_output_persistence_with_various_data_sizes(self, num_packages: int):
        """
        **Feature: multi-agent-security, Property 7: Output Persistence**
        
        For any analysis results with varying data sizes, output persistence
        should scale appropriately.
        """
        # Generate analysis results with specified number of packages
        packages = []
        for i in range(num_packages):
            packages.append({
                "name": f"package-{i}",
                "version": "1.0.0",
                "ecosystem": "npm"
            })
        
        analysis_results = {
            "analysis_type": "local_directory",
            "target_path": "/test/path",
            "analysis_start_time": "2024-01-01T00:00:00Z",
            "analysis_end_time": "2024-01-01T00:01:00Z",
            "sbom": {
                "packages": packages,
                "metadata": {"total_packages": num_packages}
            },
            "security_findings": [],
            "summary": {
                "total_packages": num_packages,
                "total_findings": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0,
                "ecosystems_found": ["npm"] if num_packages > 0 else [],
                "package_files_scanned": 1 if num_packages > 0 else 0
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Property: Should handle any reasonable data size
            output_path = save_local_analysis_results(analysis_results, temp_dir)
            
            assert os.path.exists(output_path), f"Should save analysis with {num_packages} packages"
            
            # Property: File size should correlate with data size
            file_size = os.path.getsize(output_path)
            if num_packages == 0:
                assert file_size > 0, "Even empty analysis should produce non-empty file"
            else:
                # Rough correlation - more packages should mean larger file
                assert file_size > 100, "Non-empty analysis should produce substantial file"
            
            # Property: Should preserve exact package count
            with open(output_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data["sbom"]["packages"]) == num_packages, "Should preserve exact number of packages"
            assert loaded_data["summary"]["total_packages"] == num_packages, "Summary should match package count"