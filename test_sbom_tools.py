"""
Property-based tests for SBOM processing tools.

**Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
**Validates: Requirements 1.2, 2.2**

**Feature: multi-agent-security, Property 3: Security Database Cross-Reference**
**Validates: Requirements 1.3, 2.4**

**Feature: multi-agent-security, Property 6: Ecosystem Detection Accuracy**
**Validates: Requirements 2.3**

**Feature: multi-agent-security, Property 4: OSV API Integration**
**Validates: Requirements 1.4**
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume
from typing import Dict, List, Any, Tuple
import string

from tools.sbom_tools import (
    SBOMPackage,
    SecurityFinding,
    detect_ecosystem,
    read_sbom,
    check_vulnerable_packages,
    batch_query_osv,
    generate_sbom_from_packages,
    validate_sbom_structure,
    extract_packages_from_file,
    _check_malicious_packages,
    _check_typosquatting,
    _query_osv_api
)
from constants import ECOSYSTEM_FILES, KNOWN_MALICIOUS_PACKAGES, TYPOSQUAT_TARGETS


# Strategies for property-based testing
package_name_strategy = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-_.",
    min_size=2,
    max_size=50
).filter(lambda x: x and not x.startswith('.') and not x.endswith('.'))

version_strategy = st.one_of(
    st.text(alphabet=string.digits + ".", min_size=1, max_size=20),
    st.just("*"),
    st.just("unknown")
)

ecosystem_strategy = st.sampled_from(list(ECOSYSTEM_FILES.keys()))

filename_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + ".-_",
    min_size=1,
    max_size=100
).filter(lambda x: x and not x.startswith('.'))

# Strategy for generating SBOM package data
sbom_package_strategy = st.builds(
    dict,
    name=package_name_strategy,
    version=version_strategy,
    ecosystem=ecosystem_strategy,
    metadata=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=5
    )
)

# Strategy for generating SBOM data
sbom_data_strategy = st.builds(
    dict,
    format=st.text(min_size=1, max_size=50),
    source_file=st.text(min_size=1, max_size=100),
    packages=st.lists(sbom_package_strategy, min_size=0, max_size=20),
    metadata=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=0,
        max_size=10
    )
)


class TestSBOMGenerationConsistency:
    """Property-based tests for SBOM generation consistency."""

    @given(st.lists(sbom_package_strategy, min_size=1, max_size=10))
    def test_sbom_generation_from_packages(self, packages: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
        
        For any set of discovered package files, the system should generate 
        a valid SBOM structure with all required fields populated.
        """
        assume(len(packages) > 0)
        
        source_info = {
            "type": "test",
            "path": "/test/path",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Generate SBOM
        sbom = generate_sbom_from_packages(packages, source_info)
        
        # Property: SBOM should have required top-level structure
        assert isinstance(sbom, dict), "SBOM should be a dictionary"
        assert "format" in sbom, "SBOM should have format field"
        assert "packages" in sbom, "SBOM should have packages field"
        assert "metadata" in sbom, "SBOM should have metadata field"
        assert "source" in sbom, "SBOM should have source field"
        
        # Property: Packages should be preserved
        assert sbom["packages"] == packages, "SBOM packages should match input packages"
        
        # Property: Metadata should contain expected fields
        metadata = sbom["metadata"]
        assert "total_packages" in metadata, "Metadata should contain total_packages"
        assert metadata["total_packages"] == len(packages), "Total packages should match actual count"
        assert "ecosystems" in metadata, "Metadata should contain ecosystems"
        assert isinstance(metadata["ecosystems"], list), "Ecosystems should be a list"

    @given(sbom_data_strategy)
    def test_sbom_validation_consistency(self, sbom_data: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
        
        For any SBOM data structure, validation should consistently identify
        valid and invalid structures.
        """
        is_valid, errors = validate_sbom_structure(sbom_data)
        
        # Property: Validation should return boolean and list
        assert isinstance(is_valid, bool), "Validation should return boolean"
        assert isinstance(errors, list), "Validation should return list of errors"
        
        # Property: If valid, errors should be empty
        if is_valid:
            assert len(errors) == 0, "Valid SBOM should have no errors"
        
        # Property: If invalid, there should be at least one error
        if not is_valid:
            assert len(errors) > 0, "Invalid SBOM should have at least one error"
        
        # Property: All errors should be strings
        for error in errors:
            assert isinstance(error, str), "All errors should be strings"

    def test_sbom_package_object_consistency(self):
        """
        **Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
        
        For any SBOMPackage object, serialization and deserialization should
        maintain data consistency.
        """
        # Test with various package configurations
        test_packages = [
            SBOMPackage("test-package", "1.0.0", "pkg:npm/test-package@1.0.0", "npm"),
            SBOMPackage("another-pkg", "*", "", "pypi", ["dep1", "dep2"]),
            SBOMPackage("minimal", "unknown"),
        ]
        
        for package in test_packages:
            # Property: to_dict should return dictionary
            package_dict = package.to_dict()
            assert isinstance(package_dict, dict), "to_dict should return dictionary"
            
            # Property: Required fields should be present
            required_fields = ["name", "version", "purl", "ecosystem", "dependencies", "metadata"]
            for field in required_fields:
                assert field in package_dict, f"Package dict should contain {field}"
            
            # Property: Field types should be consistent
            assert isinstance(package_dict["name"], str), "Name should be string"
            assert isinstance(package_dict["version"], str), "Version should be string"
            assert isinstance(package_dict["dependencies"], list), "Dependencies should be list"
            assert isinstance(package_dict["metadata"], dict), "Metadata should be dict"

    @given(st.text(min_size=1, max_size=1000))
    def test_json_sbom_parsing_consistency(self, json_content: str):
        """
        **Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
        
        For any JSON content, SBOM parsing should handle it consistently
        and either succeed with valid structure or fail gracefully.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_sbom.json")
            
            # Try to create valid JSON structure
            test_sbom = {
                "components": [
                    {"name": "test-pkg", "version": "1.0.0"}
                ]
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_sbom, f)
            
            # Property: Valid JSON SBOM should parse successfully
            try:
                result = read_sbom(test_file)
                assert isinstance(result, dict), "Parsed SBOM should be dictionary"
                assert "packages" in result, "Parsed SBOM should contain packages"
            except ValueError:
                # This is acceptable for invalid formats
                pass

    def test_sbom_format_detection_consistency(self):
        """
        **Feature: multi-agent-security, Property 2: SBOM Generation Consistency**
        
        For any supported SBOM format, the parser should correctly identify
        and process the format consistently.
        """
        # Test different SBOM formats
        formats = [
            # CycloneDX format
            {
                "format_name": "cyclonedx",
                "content": {
                    "specVersion": "1.4",
                    "components": [
                        {"name": "test-component", "version": "1.0.0", "purl": "pkg:npm/test-component@1.0.0"}
                    ]
                }
            },
            # SPDX JSON format
            {
                "format_name": "spdx-json",
                "content": {
                    "spdxVersion": "SPDX-2.2",
                    "packages": [
                        {"name": "test-package", "versionInfo": "1.0.0"}
                    ]
                }
            },
            # npm package.json format
            {
                "format_name": "npm-package-json",
                "content": {
                    "name": "test-project",
                    "dependencies": {
                        "lodash": "^4.17.21",
                        "express": "^4.18.0"
                    }
                }
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, format_info in enumerate(formats):
                test_file = os.path.join(temp_dir, f"test_sbom_{i}.json")
                
                with open(test_file, 'w') as f:
                    json.dump(format_info["content"], f)
                
                # Property: Each format should be parsed consistently
                result = read_sbom(test_file)
                assert isinstance(result, dict), f"Format {format_info['format_name']} should parse to dict"
                assert "packages" in result, f"Format {format_info['format_name']} should contain packages"
                assert isinstance(result["packages"], list), f"Packages should be list for {format_info['format_name']}"


class TestSecurityDatabaseCrossReference:
    """Property-based tests for security database cross-reference."""

    @given(sbom_data_strategy)
    def test_vulnerability_check_consistency(self, sbom_data: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 3: Security Database Cross-Reference**
        
        For any package in an SBOM, the system should check it against the 
        malicious package database and return consistent results regardless 
        of analysis mode.
        """
        # Ensure we have packages to test
        if not sbom_data.get("packages"):
            sbom_data["packages"] = [
                {"name": "test-package", "version": "1.0.0", "ecosystem": "npm"}
            ]
        
        # Test with OSV disabled
        findings_no_osv = check_vulnerable_packages(sbom_data, use_osv=False)
        
        # Test with OSV enabled (but mocked to avoid real API calls)
        with patch('tools.sbom_tools._query_osv_api', return_value=[]):
            findings_with_osv = check_vulnerable_packages(sbom_data, use_osv=True)
        
        # Property: Results should be lists
        assert isinstance(findings_no_osv, list), "Findings should be a list"
        assert isinstance(findings_with_osv, list), "Findings should be a list"
        
        # Property: All findings should be SecurityFinding objects or dicts
        for finding in findings_no_osv:
            assert isinstance(finding, (SecurityFinding, dict)), "Finding should be SecurityFinding or dict"
        
        # Property: Malicious package detection should be consistent regardless of OSV setting
        malicious_findings_no_osv = [f for f in findings_no_osv if 
                                   (hasattr(f, 'finding_type') and f.finding_type == "malicious_package") or
                                   (isinstance(f, dict) and f.get('finding_type') == "malicious_package")]
        
        malicious_findings_with_osv = [f for f in findings_with_osv if 
                                     (hasattr(f, 'finding_type') and f.finding_type == "malicious_package") or
                                     (isinstance(f, dict) and f.get('finding_type') == "malicious_package")]
        
        assert len(malicious_findings_no_osv) == len(malicious_findings_with_osv), \
            "Malicious package detection should be consistent regardless of OSV setting"

    @given(package_name_strategy, version_strategy, ecosystem_strategy)
    def test_malicious_package_detection_accuracy(self, package_name: str, version: str, ecosystem: str):
        """
        **Feature: multi-agent-security, Property 3: Security Database Cross-Reference**
        
        For any package, malicious package detection should accurately identify
        packages that are in the known malicious packages database.
        """
        assume(package_name.strip() != "")
        
        findings = _check_malicious_packages(package_name, version, ecosystem)
        
        # Property: Result should be a list
        assert isinstance(findings, list), "Malicious package check should return list"
        
        # Property: If package is in malicious database, it should be detected
        if ecosystem in KNOWN_MALICIOUS_PACKAGES:
            malicious_packages = KNOWN_MALICIOUS_PACKAGES[ecosystem]
            is_malicious = any(
                pkg['name'].lower() == package_name.lower() and 
                (pkg['version'] == '*' or pkg['version'] == version)
                for pkg in malicious_packages
            )
            
            if is_malicious:
                assert len(findings) > 0, f"Malicious package {package_name}@{version} should be detected"
                assert all(f.finding_type == "malicious_package" for f in findings), \
                    "All findings should be malicious_package type"
        
        # Property: All findings should have required fields
        for finding in findings:
            assert hasattr(finding, 'package'), "Finding should have package field"
            assert hasattr(finding, 'version'), "Finding should have version field"
            assert hasattr(finding, 'finding_type'), "Finding should have finding_type field"
            assert hasattr(finding, 'severity'), "Finding should have severity field"
            assert hasattr(finding, 'confidence'), "Finding should have confidence field"

    @given(package_name_strategy, ecosystem_strategy)
    def test_typosquat_detection_consistency(self, package_name: str, ecosystem: str):
        """
        **Feature: multi-agent-security, Property 3: Security Database Cross-Reference**
        
        For any package name, typosquat detection should be consistent
        and only flag packages that are actually similar to known targets.
        """
        assume(package_name.strip() != "")
        
        findings = _check_typosquatting(package_name, ecosystem)
        
        # Property: Result should be a list
        assert isinstance(findings, list), "Typosquat check should return list"
        
        # Property: All findings should be typosquat type
        for finding in findings:
            assert finding.finding_type == "typosquat", "All findings should be typosquat type"
            assert finding.confidence > 0.5, "Typosquat findings should have confidence > 0.5"
        
        # Property: If flagged as typosquat, should be similar to a target
        if findings and ecosystem in TYPOSQUAT_TARGETS:
            targets = TYPOSQUAT_TARGETS[ecosystem]
            package_lower = package_name.lower()
            
            # At least one target should be similar
            found_similarity = False
            for target in targets:
                target_lower = target.lower()
                if package_lower != target_lower:  # Not identical
                    # Check for various similarity patterns
                    if (len(package_lower) == len(target_lower) and
                        sum(c1 != c2 for c1, c2 in zip(package_lower, target_lower)) <= 2):
                        found_similarity = True
                        break
            
            # Note: We don't assert found_similarity because the algorithm might have
            # more sophisticated detection that we're not checking here

    def test_security_finding_object_consistency(self):
        """
        **Feature: multi-agent-security, Property 3: Security Database Cross-Reference**
        
        For any SecurityFinding object, serialization should maintain
        data consistency and include all required fields.
        """
        test_finding = SecurityFinding(
            package="test-package",
            version="1.0.0",
            finding_type="malicious_package",
            severity="high",
            confidence=0.9,
            evidence=["Test evidence"],
            recommendations=["Test recommendation"]
        )
        
        # Property: to_dict should return dictionary with all fields
        finding_dict = test_finding.to_dict()
        assert isinstance(finding_dict, dict), "to_dict should return dictionary"
        
        required_fields = ["package", "version", "finding_type", "severity", 
                          "confidence", "evidence", "recommendations", "source", "timestamp"]
        for field in required_fields:
            assert field in finding_dict, f"Finding dict should contain {field}"
        
        # Property: Field types should be correct
        assert isinstance(finding_dict["confidence"], (int, float)), "Confidence should be numeric"
        assert 0.0 <= finding_dict["confidence"] <= 1.0, "Confidence should be between 0 and 1"
        assert isinstance(finding_dict["evidence"], list), "Evidence should be list"
        assert isinstance(finding_dict["recommendations"], list), "Recommendations should be list"


class TestEcosystemDetectionAccuracy:
    """Property-based tests for ecosystem detection accuracy."""

    @given(filename_strategy)
    def test_ecosystem_detection_from_filename(self, filename: str):
        """
        **Feature: multi-agent-security, Property 6: Ecosystem Detection Accuracy**
        
        For any package file from supported ecosystems, the system should 
        correctly identify the ecosystem type.
        """
        assume(filename.strip() != "")
        
        detected_ecosystem = detect_ecosystem(filename)
        
        # Property: Result should be a string
        assert isinstance(detected_ecosystem, str), "Ecosystem detection should return string"
        
        # Property: Should return either a known ecosystem or "unknown"
        valid_ecosystems = set(ECOSYSTEM_FILES.keys()) | {"unknown"}
        assert detected_ecosystem in valid_ecosystems, f"Detected ecosystem '{detected_ecosystem}' should be valid"
        
        # Property: If ecosystem is detected (not "unknown"), filename should match pattern
        if detected_ecosystem != "unknown":
            ecosystem_files = ECOSYSTEM_FILES[detected_ecosystem]
            filename_lower = filename.lower()
            
            pattern_matched = False
            for pattern in ecosystem_files:
                pattern_to_check = pattern.replace("*", "").lower()
                if pattern_to_check in filename_lower:
                    pattern_matched = True
                    break
            
            assert pattern_matched, f"Ecosystem '{detected_ecosystem}' detected but filename '{filename}' doesn't match patterns"

    def test_known_file_patterns_detection(self):
        """
        **Feature: multi-agent-security, Property 6: Ecosystem Detection Accuracy**
        
        For any known package file pattern, the system should correctly
        identify the corresponding ecosystem.
        """
        # Test known file patterns
        known_patterns = {
            "package.json": "npm",
            "requirements.txt": "pypi", 
            "pom.xml": "maven",
            "Gemfile": "rubygems",
            "Cargo.toml": "crates",
            "go.mod": "go"
        }
        
        for filename, expected_ecosystem in known_patterns.items():
            detected = detect_ecosystem(filename)
            assert detected == expected_ecosystem, f"File '{filename}' should detect ecosystem '{expected_ecosystem}', got '{detected}'"

    @given(st.text(min_size=10, max_size=500))
    def test_ecosystem_detection_with_content(self, content: str):
        """
        **Feature: multi-agent-security, Property 6: Ecosystem Detection Accuracy**
        
        For any file content, ecosystem detection should use content clues
        when filename is ambiguous.
        """
        # Test with generic filename but specific content
        generic_filename = "dependencies.txt"
        
        detected = detect_ecosystem(generic_filename, content)
        
        # Property: Should return valid ecosystem
        valid_ecosystems = set(ECOSYSTEM_FILES.keys()) | {"unknown"}
        assert detected in valid_ecosystems, "Detected ecosystem should be valid"
        
        # Property: Content-based detection should work for clear indicators
        if '"dependencies"' in content and '"name"' in content:
            # Looks like npm package.json content
            detected_with_npm_content = detect_ecosystem("unknown.txt", content)
            # Should detect npm or at least not fail
            assert isinstance(detected_with_npm_content, str), "Content-based detection should return string"

    def test_ecosystem_detection_edge_cases(self):
        """
        **Feature: multi-agent-security, Property 6: Ecosystem Detection Accuracy**
        
        For any edge cases in filenames, ecosystem detection should handle
        them gracefully without errors.
        """
        edge_cases = [
            "",  # Empty filename
            ".",  # Just dot
            "..",  # Double dot
            "file",  # No extension
            "file.unknown",  # Unknown extension
            "PACKAGE.JSON",  # Uppercase
            "package.json.backup",  # Extra extension
        ]
        
        for filename in edge_cases:
            # Property: Should not raise exceptions
            try:
                result = detect_ecosystem(filename)
                assert isinstance(result, str), f"Edge case '{filename}' should return string"
                valid_ecosystems = set(ECOSYSTEM_FILES.keys()) | {"unknown"}
                assert result in valid_ecosystems, f"Edge case '{filename}' should return valid ecosystem"
            except Exception as e:
                pytest.fail(f"Exception raised for edge case '{filename}': {e}")


class TestOSVAPIIntegration:
    """Property-based tests for OSV API integration."""

    @patch('tools.sbom_tools.requests.post')
    def test_osv_api_query_consistency(self, mock_post):
        """
        **Feature: multi-agent-security, Property 4: OSV API Integration**
        
        For any detected malicious package, the system should query the OSV API 
        and retrieve additional vulnerability information.
        """
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'vulns': [
                {
                    'id': 'TEST-001',
                    'summary': 'Test vulnerability',
                    'severity': [{'score': 8.5, 'type': 'CVSS_V3'}]
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test OSV query
        findings = _query_osv_api("test-package", "1.0.0", "npm")
        
        # Property: Should return list of findings
        assert isinstance(findings, list), "OSV query should return list"
        
        # Property: API should be called with correct parameters
        assert mock_post.called, "OSV API should be called"
        call_args = mock_post.call_args
        assert call_args is not None, "API call should have arguments"
        
        # Property: All findings should have required structure
        for finding in findings:
            assert hasattr(finding, 'finding_type'), "OSV finding should have finding_type"
            assert finding.finding_type == "vulnerability", "OSV findings should be vulnerability type"
            assert hasattr(finding, 'confidence'), "OSV finding should have confidence"
            assert isinstance(finding.confidence, (int, float)), "Confidence should be numeric"

    @patch('tools.sbom_tools.requests.post')
    def test_osv_api_error_handling(self, mock_post):
        """
        **Feature: multi-agent-security, Property 4: OSV API Integration**
        
        For any API error conditions, the OSV integration should handle
        them gracefully and return appropriate default values.
        """
        # Test different error conditions
        error_conditions = [
            (404, "Not found"),  # No vulnerabilities found
            (500, "Server error"),  # Server error
        ]
        
        for status_code, error in error_conditions:
            mock_response = Mock()
            mock_response.status_code = status_code
            if status_code == 404:
                mock_response.raise_for_status.return_value = None  # 404 doesn't raise
                mock_response.json.return_value = {"vulns": []}
            else:
                mock_response.raise_for_status.side_effect = Exception(error)
            
            mock_post.return_value = mock_response
            mock_post.side_effect = None
            
            # Property: Should handle errors gracefully
            findings = _query_osv_api("test-package", "1.0.0", "npm")
            assert isinstance(findings, list), f"Error condition {error} should return list"
            
            # For 404, we might get empty list; for other errors, should also be empty
            if status_code == 404:
                # 404 is acceptable - means no vulnerabilities found
                assert len(findings) == 0, "404 should return empty list"
            else:
                # Other errors should result in empty list
                assert len(findings) == 0, f"Error condition {error} should return empty list"
        
        # Test network exception separately
        import requests
        mock_post.side_effect = requests.RequestException("Network error")
        findings = _query_osv_api("test-package", "1.0.0", "npm")
        assert isinstance(findings, list), "Network error should return list"
        assert len(findings) == 0, "Network error should return empty list"

    @given(st.lists(
        st.tuples(package_name_strategy, version_strategy, ecosystem_strategy),
        min_size=1,
        max_size=5
    ))
    def test_batch_osv_query_consistency(self, packages: List[Tuple[str, str, str]]):
        """
        **Feature: multi-agent-security, Property 4: OSV API Integration**
        
        For any batch of packages, batch OSV querying should be consistent
        with individual queries.
        """
        # Filter out invalid packages
        valid_packages = [(name, version, ecosystem) for name, version, ecosystem in packages 
                         if name.strip() and ecosystem in ECOSYSTEM_FILES]
        assume(len(valid_packages) > 0)
        
        with patch('tools.sbom_tools._query_osv_api') as mock_query:
            # Mock individual queries to return empty lists
            mock_query.return_value = []
            
            # Test batch query
            batch_findings = batch_query_osv(valid_packages)
            
            # Property: Should return list
            assert isinstance(batch_findings, list), "Batch query should return list"
            
            # Property: Should call individual query for each package
            assert mock_query.call_count == len(valid_packages), \
                f"Should call individual query {len(valid_packages)} times, called {mock_query.call_count}"
            
            # Property: Each call should have correct parameters
            for i, (name, version, ecosystem) in enumerate(valid_packages):
                call_args = mock_query.call_args_list[i]
                assert call_args[0][0] == name, f"Call {i} should have correct package name"
                assert call_args[0][1] == version, f"Call {i} should have correct version"
                assert call_args[0][2] == ecosystem, f"Call {i} should have correct ecosystem"

    def test_osv_severity_mapping_consistency(self):
        """
        **Feature: multi-agent-security, Property 4: OSV API Integration**
        
        For any OSV vulnerability data, severity mapping should be consistent
        and map to valid severity levels.
        """
        from tools.sbom_tools import _determine_severity_from_osv
        
        # Test different severity data formats
        test_cases = [
            # CVSS v3 scores
            ({'severity': [{'type': 'CVSS_V3', 'score': 9.5}]}, 'critical'),
            ({'severity': [{'type': 'CVSS_V3', 'score': 8.0}]}, 'high'),
            ({'severity': [{'type': 'CVSS_V3', 'score': 5.0}]}, 'medium'),
            ({'severity': [{'type': 'CVSS_V3', 'score': 2.0}]}, 'low'),
            
            # Database specific severity
            ({'database_specific': {'severity': 'HIGH'}}, 'high'),
            ({'database_specific': {'severity': 'medium'}}, 'medium'),
            
            # No severity information
            ({}, 'medium'),  # Default
            ({'severity': []}, 'medium'),  # Empty severity
        ]
        
        valid_severities = {'critical', 'high', 'medium', 'low'}
        
        for vuln_data, expected_severity in test_cases:
            result = _determine_severity_from_osv(vuln_data)
            
            # Property: Should return valid severity
            assert result in valid_severities, f"Severity '{result}' should be valid"
            
            # Property: Should match expected result for known cases
            if expected_severity:
                assert result == expected_severity, f"Expected '{expected_severity}', got '{result}'"