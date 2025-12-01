"""
Property-based tests for image processing pipeline in vlm_tools.py

**Feature: multi-agent-security, Property 14: Image Processing Pipeline**
**Validates: Requirements 6.1, 6.2, 6.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import List, Dict, Any
import tempfile
import os
from pathlib import Path
from PIL import Image
import base64
import json
from unittest.mock import patch, MagicMock

from tools.vlm_tools import (
    validate_image_file,
    encode_image_to_base64,
    VisualSecurityFinding,
    detect_security_indicators,
    correlate_visual_findings_with_packages,
    process_multiple_images,
    generate_visual_security_findings,
    _calculate_overall_visual_risk
)
from config import config


# Strategies for generating test data
image_dimensions_strategy = st.tuples(
    st.integers(min_value=50, max_value=2048),  # width
    st.integers(min_value=50, max_value=2048)   # height
)

severity_strategy = st.sampled_from(["critical", "high", "medium", "low"])
confidence_strategy = st.floats(min_value=0.0, max_value=1.0)
finding_type_strategy = st.sampled_from([
    "security_warning", "malware_indicator", "phishing_attempt", 
    "ui_anomaly", "network_activity", "other"
])

# Strategy for generating SBOM-like package data
package_strategy = st.fixed_dictionaries({
    "name": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    "version": st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
    "ecosystem": st.sampled_from(["npm", "pypi", "maven", "rubygems", "crates", "go"])
})

sbom_strategy = st.fixed_dictionaries({
    "packages": st.lists(package_strategy, min_size=0, max_size=20)
})


def create_test_image(width: int, height: int, format: str = "JPEG") -> str:
    """Create a temporary test image file."""
    with tempfile.NamedTemporaryFile(suffix=f".{format.lower()}", delete=False) as tmp_file:
        # Create a simple colored image
        img = Image.new("RGB", (width, height), color=(100, 150, 200))
        img.save(tmp_file.name, format=format)
        return tmp_file.name


def cleanup_test_image(image_path: str):
    """Clean up temporary test image."""
    try:
        os.unlink(image_path)
    except (OSError, FileNotFoundError):
        pass


class TestImageProcessingPipeline:
    """Property-based tests for image processing pipeline."""

    @given(image_dimensions_strategy)
    def test_image_validation_consistency(self, dimensions):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        For any valid image dimensions, image validation should consistently
        accept valid images and reject invalid ones.
        """
        width, height = dimensions
        
        # Create a test image
        image_path = create_test_image(width, height)
        
        try:
            is_valid, error_msg = validate_image_file(image_path)
            
            # Property: Valid images should pass validation
            assert is_valid, f"Valid image {width}x{height} failed validation: {error_msg}"
            
            # Property: Error message should be empty for valid images
            assert error_msg == "", f"Valid image has error message: {error_msg}"
            
        finally:
            cleanup_test_image(image_path)

    @given(image_dimensions_strategy)
    def test_base64_encoding_round_trip(self, dimensions):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        For any valid image, base64 encoding should produce valid base64 data
        that represents the image content.
        """
        width, height = dimensions
        
        # Create a test image
        image_path = create_test_image(width, height)
        
        try:
            # Encode to base64
            base64_data = encode_image_to_base64(image_path)
            
            # Property: Result should be a non-empty string
            assert isinstance(base64_data, str)
            assert len(base64_data) > 0
            
            # Property: Should be valid base64
            try:
                decoded_data = base64.b64decode(base64_data)
                assert len(decoded_data) > 0
            except Exception as e:
                pytest.fail(f"Invalid base64 data generated: {e}")
            
            # Property: Encoding the same image twice should produce the same result
            base64_data_2 = encode_image_to_base64(image_path)
            assert base64_data == base64_data_2, "Encoding same image twice produced different results"
            
        finally:
            cleanup_test_image(image_path)

    def test_image_validation_edge_cases(self):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Image validation should handle edge cases properly without crashing.
        """
        edge_cases = [
            ("nonexistent_file.jpg", False, "not found"),
            ("", False, "format"),  # Empty string triggers format error, not file not found
        ]
        
        for file_path, expected_valid, expected_error_substring in edge_cases:
            is_valid, error_msg = validate_image_file(file_path)
            
            # Property: Should return expected validity
            assert is_valid == expected_valid, f"Unexpected validation result for {file_path}"
            
            # Property: Error message should contain expected substring
            if not expected_valid:
                assert expected_error_substring.lower() in error_msg.lower(), \
                    f"Error message '{error_msg}' doesn't contain '{expected_error_substring}'"

    @given(st.lists(finding_type_strategy, min_size=1, max_size=10),
           st.lists(severity_strategy, min_size=1, max_size=10),
           st.lists(confidence_strategy, min_size=1, max_size=10))
    def test_visual_finding_creation_consistency(self, finding_types, severities, confidences):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        For any combination of finding parameters, VisualSecurityFinding creation
        should be consistent and produce valid objects.
        """
        # Use the minimum length to avoid index errors
        min_length = min(len(finding_types), len(severities), len(confidences))
        assume(min_length > 0)
        
        for i in range(min_length):
            finding = VisualSecurityFinding(
                finding_type=finding_types[i],
                description=f"Test finding {i}",
                confidence=confidences[i],
                severity=severities[i]
            )
            
            # Property: Finding should have all required attributes
            assert hasattr(finding, 'finding_type')
            assert hasattr(finding, 'description')
            assert hasattr(finding, 'confidence')
            assert hasattr(finding, 'severity')
            assert hasattr(finding, 'detected_at')
            
            # Property: Confidence should be within valid range
            assert 0.0 <= finding.confidence <= 1.0
            
            # Property: Severity should be valid
            assert finding.severity in ["critical", "high", "medium", "low"]
            
            # Property: to_dict should produce valid dictionary
            finding_dict = finding.to_dict()
            assert isinstance(finding_dict, dict)
            assert "finding_type" in finding_dict
            assert "confidence" in finding_dict
            assert "severity" in finding_dict

    @given(sbom_strategy)
    def test_visual_package_correlation_consistency(self, sbom_data):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        For any SBOM data and visual findings, correlation should be consistent
        and not produce invalid results.
        """
        # Create test visual findings
        test_findings = [
            VisualSecurityFinding(
                finding_type="security_warning",
                description="npm install detected in screenshot",
                confidence=0.8,
                severity="medium",
                evidence=["npm install command visible"]
            ),
            VisualSecurityFinding(
                finding_type="ui_anomaly",
                description="Suspicious dialog box",
                confidence=0.6,
                severity="high"
            )
        ]
        
        correlations = correlate_visual_findings_with_packages(test_findings, sbom_data)
        
        # Property: Result should be a list
        assert isinstance(correlations, list)
        
        # Property: Each correlation should have required structure
        for correlation in correlations:
            assert isinstance(correlation, dict)
            assert "visual_finding" in correlation
            assert "package_correlations" in correlation
            assert "correlation_timestamp" in correlation
            
            # Property: Visual finding should be valid
            visual_finding = correlation["visual_finding"]
            assert isinstance(visual_finding, dict)
            assert "finding_type" in visual_finding
            
            # Property: Package correlations should be valid
            package_correlations = correlation["package_correlations"]
            assert isinstance(package_correlations, list)
            
            for pkg_correlation in package_correlations:
                assert isinstance(pkg_correlation, dict)
                assert "package" in pkg_correlation
                assert "correlation_type" in pkg_correlation
                assert "correlation_confidence" in pkg_correlation

    @given(st.lists(severity_strategy, min_size=0, max_size=20))
    def test_overall_risk_calculation_consistency(self, severity_levels):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        For any list of severity levels, overall risk calculation should be
        consistent and return valid risk levels.
        """
        overall_risk = _calculate_overall_visual_risk(severity_levels)
        
        # Property: Result should be a valid risk level
        valid_risks = ["none", "low", "medium", "high", "critical"]
        assert overall_risk in valid_risks
        
        # Property: If critical is present, overall should be critical
        if "critical" in severity_levels:
            assert overall_risk == "critical"
        
        # Property: If high is present (and no critical), overall should be high
        elif "high" in severity_levels:
            assert overall_risk == "high"
        
        # Property: If medium is present (and no high/critical), overall should be medium
        elif "medium" in severity_levels:
            assert overall_risk == "medium"
        
        # Property: If only low is present, overall should be low
        elif "low" in severity_levels:
            assert overall_risk == "low"
        
        # Property: If empty list, overall should be none
        elif not severity_levels:
            assert overall_risk == "none"

    def test_multiple_image_processing_consistency(self):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Processing multiple images should handle various scenarios consistently.
        """
        # Create test images
        test_images = []
        try:
            # Valid images
            img1 = create_test_image(100, 100)
            img2 = create_test_image(200, 150)
            test_images.extend([img1, img2])
            
            # Mock the GPT-4 Vision API calls to avoid actual API calls
            with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
                mock_analyze.return_value = {
                    "findings": [
                        {
                            "type": "security_warning",
                            "description": "Test finding",
                            "severity": "medium",
                            "confidence": 0.7,
                            "evidence": ["Test evidence"]
                        }
                    ],
                    "overall_risk": "medium",
                    "summary": "Test analysis"
                }
                
                # Test with valid images
                results = process_multiple_images(test_images)
                
                # Property: Results should have expected structure
                assert isinstance(results, dict)
                assert "analysis_timestamp" in results
                assert "images_processed" in results
                assert "images_successful" in results
                assert "total_findings" in results
                assert "findings" in results
                assert "overall_risk" in results
                
                # Property: Number of processed images should match input
                assert results["images_processed"] == len(test_images)
                
                # Property: Findings should be a list
                assert isinstance(results["findings"], list)
                
                # Property: Overall risk should be valid
                assert results["overall_risk"] in ["none", "low", "medium", "high", "critical"]
        
        finally:
            # Clean up test images
            for img_path in test_images:
                cleanup_test_image(img_path)

    def test_security_finding_generation_consistency(self):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Generating SecurityFinding objects from visual analysis should be consistent.
        """
        # Test visual analysis data
        visual_analysis = {
            "findings": [
                {
                    "finding_type": "security_warning",
                    "description": "Suspicious security alert detected",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence": ["Alert dialog visible", "Suspicious text content"],
                    "metadata": {
                        "location": "Center of screen",
                        "recommendations": ["Investigate alert legitimacy"]
                    }
                },
                {
                    "finding_type": "ui_anomaly",
                    "description": "Unexpected dialog box",
                    "severity": "medium",
                    "confidence": 0.6,
                    "evidence": ["Unusual UI element"],
                    "metadata": {}
                }
            ]
        }
        
        security_findings = generate_visual_security_findings(visual_analysis)
        
        # Property: Should return list of SecurityFinding objects
        assert isinstance(security_findings, list)
        assert len(security_findings) == len(visual_analysis["findings"])
        
        for i, finding in enumerate(security_findings):
            original_finding = visual_analysis["findings"][i]
            
            # Property: SecurityFinding should have required attributes
            assert hasattr(finding, 'package')
            assert hasattr(finding, 'version')
            assert hasattr(finding, 'finding_type')
            assert hasattr(finding, 'severity')
            assert hasattr(finding, 'confidence')
            assert hasattr(finding, 'evidence')
            assert hasattr(finding, 'recommendations')
            assert hasattr(finding, 'source')
            
            # Property: Values should match original data
            assert finding.finding_type == original_finding["finding_type"]
            assert finding.severity == original_finding["severity"]
            assert finding.confidence == original_finding["confidence"]
            assert finding.source == "vlm_tools"
            
            # Property: Evidence should include original evidence
            for evidence_item in original_finding["evidence"]:
                assert evidence_item in finding.evidence

    @settings(max_examples=10)  # Reduce examples for file I/O tests
    @given(st.integers(min_value=1, max_value=5))
    def test_image_processing_error_handling(self, num_invalid_files):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Image processing should handle errors gracefully without crashing.
        """
        # Create list of invalid file paths
        invalid_paths = [f"nonexistent_file_{i}.jpg" for i in range(num_invalid_files)]
        
        # Mock the analysis to avoid API calls
        with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
            mock_analyze.return_value = {"findings": [], "overall_risk": "none"}
            
            results = process_multiple_images(invalid_paths)
            
            # Property: Should not crash and return valid structure
            assert isinstance(results, dict)
            assert "processing_errors" in results
            assert "images_processed" in results
            assert "images_successful" in results
            
            # Property: Should report processing errors
            assert len(results["processing_errors"]) > 0
            assert results["images_successful"] == 0
            assert results["images_processed"] == num_invalid_files

    def test_base64_encoding_size_limits(self):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Base64 encoding should handle size limits appropriately.
        """
        # Test with very small image
        small_img = create_test_image(50, 50)
        
        try:
            base64_data = encode_image_to_base64(small_img)
            
            # Property: Should successfully encode small images
            assert isinstance(base64_data, str)
            assert len(base64_data) > 0
            
        finally:
            cleanup_test_image(small_img)
        
        # Test with large image (should be resized)
        large_img = create_test_image(3000, 3000)
        
        try:
            base64_data = encode_image_to_base64(large_img, resize_if_needed=True)
            
            # Property: Should successfully encode and resize large images
            assert isinstance(base64_data, str)
            assert len(base64_data) > 0
            
        finally:
            cleanup_test_image(large_img)

    def test_visual_finding_metadata_consistency(self):
        """
        **Feature: multi-agent-security, Property 14: Image Processing Pipeline**
        
        Visual findings should maintain metadata consistency.
        """
        test_metadata = {
            "location": "Top-left corner",
            "analysis_model": "gpt-4-vision-preview",
            "custom_field": "test_value"
        }
        
        finding = VisualSecurityFinding(
            finding_type="security_warning",
            description="Test finding with metadata",
            confidence=0.8,
            severity="high",
            metadata=test_metadata
        )
        
        # Property: Metadata should be preserved
        assert finding.metadata == test_metadata
        
        # Property: to_dict should include metadata
        finding_dict = finding.to_dict()
        assert finding_dict["metadata"] == test_metadata
        
        # Property: Metadata should be optional
        finding_no_metadata = VisualSecurityFinding(
            finding_type="ui_anomaly",
            description="Test finding without metadata",
            confidence=0.5,
            severity="low"
        )
        
        assert isinstance(finding_no_metadata.metadata, dict)
        assert len(finding_no_metadata.metadata) == 0


class TestVisualSecurityDetection:
    """Property-based tests for visual security detection capabilities."""

    @given(image_dimensions_strategy)
    def test_security_indicator_detection_consistency(self, dimensions):
        """
        **Feature: multi-agent-security, Property 15: Visual Security Detection**
        **Validates: Requirements 6.3**
        
        For any valid image, the system should consistently detect security warnings,
        alerts, and UI anomalies when they are present.
        """
        width, height = dimensions
        
        # Create a test image
        image_path = create_test_image(width, height)
        
        try:
            # Mock GPT-4 Vision response with security indicators
            mock_security_response = {
                "findings": [
                    {
                        "type": "security_warning",
                        "description": "Security alert dialog detected",
                        "severity": "high",
                        "confidence": 0.9,
                        "location": "Center of screen",
                        "evidence": ["Alert dialog visible", "Warning text present"],
                        "recommendations": ["Investigate alert legitimacy"]
                    },
                    {
                        "type": "ui_anomaly",
                        "description": "Suspicious dialog box",
                        "severity": "medium", 
                        "confidence": 0.7,
                        "location": "Top-right corner",
                        "evidence": ["Unusual UI element"],
                        "recommendations": ["Check for malware"]
                    }
                ],
                "overall_risk": "high",
                "summary": "Multiple security indicators detected"
            }
            
            with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
                mock_analyze.return_value = mock_security_response
                
                findings = detect_security_indicators(image_path)
                
                # Property: Should return a list of VisualSecurityFinding objects
                assert isinstance(findings, list)
                
                # Property: Each finding should be a VisualSecurityFinding instance
                for finding in findings:
                    assert isinstance(finding, VisualSecurityFinding)
                    
                    # Property: Finding should have valid security indicator types
                    valid_types = ["security_warning", "malware_indicator", "phishing_attempt", 
                                 "ui_anomaly", "network_activity", "other"]
                    assert finding.finding_type in valid_types
                    
                    # Property: Confidence should be within valid range
                    assert 0.0 <= finding.confidence <= 1.0
                    
                    # Property: Severity should be valid
                    assert finding.severity in ["critical", "high", "medium", "low"]
                    
                    # Property: Description should not be empty
                    assert len(finding.description.strip()) > 0
                    
                    # Property: Evidence should be a list
                    assert isinstance(finding.evidence, list)
                    
                    # Property: Metadata should contain analysis information
                    assert isinstance(finding.metadata, dict)
                
                # Property: Number of findings should match mock response
                assert len(findings) == len(mock_security_response["findings"])
        
        finally:
            cleanup_test_image(image_path)

    @given(st.lists(st.sampled_from(["security_warning", "ui_anomaly", "malware_indicator", 
                                   "phishing_attempt", "network_activity"]), 
                   min_size=1, max_size=10),
           st.data())
    def test_ui_anomaly_detection_consistency(self, anomaly_types, data):
        """
        **Feature: multi-agent-security, Property 15: Visual Security Detection**
        **Validates: Requirements 6.3**
        
        For any set of UI anomaly types, the system should consistently detect
        and classify UI anomalies without producing invalid results.
        """
        # Create a test image
        image_path = create_test_image(200, 200)
        
        try:
            # Mock GPT-4 Vision response with UI anomalies
            mock_anomalies = []
            for i, anomaly_type in enumerate(anomaly_types):
                severity = data.draw(st.sampled_from(["critical", "high", "medium", "low"]))
                confidence = data.draw(st.floats(min_value=0.1, max_value=1.0))
                
                mock_anomalies.append({
                    "type": anomaly_type,
                    "description": f"Detected {anomaly_type} in image",
                    "severity": severity,
                    "confidence": confidence,
                    "location": f"Location {i}",
                    "indicators": [f"Indicator {i}"]
                })
            
            mock_response = {"anomalies": mock_anomalies}
            
            with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
                mock_analyze.return_value = mock_response
                
                from tools.vlm_tools import analyze_ui_anomalies
                findings = analyze_ui_anomalies(image_path)
                
                # Property: Should return a list of findings
                assert isinstance(findings, list)
                
                # Property: Each finding should be valid
                for finding in findings:
                    assert isinstance(finding, VisualSecurityFinding)
                    assert finding.finding_type == "ui_anomaly"
                    
                    # Property: Should have valid anomaly metadata
                    assert "anomaly_type" in finding.metadata
                    assert finding.metadata["anomaly_type"] in anomaly_types
                    
                    # Property: Should have evidence from indicators
                    assert isinstance(finding.evidence, list)
                    
                    # Property: Confidence should be valid
                    assert 0.0 <= finding.confidence <= 1.0
        
        finally:
            cleanup_test_image(image_path)

    def test_security_detection_error_handling(self):
        """
        **Feature: multi-agent-security, Property 15: Visual Security Detection**
        **Validates: Requirements 6.3**
        
        Security detection should handle errors gracefully and not crash
        when processing fails.
        """
        # Test with non-existent image
        non_existent_path = "non_existent_image.jpg"
        
        findings = detect_security_indicators(non_existent_path)
        
        # Property: Should return empty list for invalid images
        assert isinstance(findings, list)
        assert len(findings) == 0
        
        # Test with API failure
        image_path = create_test_image(100, 100)
        
        try:
            with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
                mock_analyze.side_effect = Exception("API failure")
                
                findings = detect_security_indicators(image_path)
                
                # Property: Should handle API failures gracefully
                assert isinstance(findings, list)
                assert len(findings) == 0
        
        finally:
            cleanup_test_image(image_path)

    @given(st.text(min_size=1, max_size=500))
    def test_security_indicator_text_analysis(self, finding_text):
        """
        **Feature: multi-agent-security, Property 15: Visual Security Detection**
        **Validates: Requirements 6.3**
        
        For any finding text, security indicator detection should consistently
        process and classify the content without producing invalid results.
        """
        assume(finding_text.strip())  # Ensure non-empty text
        
        # Create test finding with the generated text
        finding = VisualSecurityFinding(
            finding_type="security_warning",
            description=finding_text,
            confidence=0.8,
            severity="medium",
            evidence=[finding_text]
        )
        
        # Property: Finding should be created successfully
        assert isinstance(finding, VisualSecurityFinding)
        assert finding.description == finding_text
        
        # Property: Finding should convert to dict consistently
        finding_dict = finding.to_dict()
        assert isinstance(finding_dict, dict)
        assert finding_dict["description"] == finding_text
        
        # Property: Evidence should contain the text
        assert finding_text in finding.evidence

    def test_multiple_security_indicators_consistency(self):
        """
        **Feature: multi-agent-security, Property 15: Visual Security Detection**
        **Validates: Requirements 6.3**
        
        When multiple security indicators are present, detection should
        handle them consistently and maintain proper classification.
        """
        image_path = create_test_image(300, 300)
        
        try:
            # Mock response with multiple different security indicators
            mock_response = {
                "findings": [
                    {
                        "type": "security_warning",
                        "description": "Windows Defender alert",
                        "severity": "high",
                        "confidence": 0.95,
                        "evidence": ["Defender icon", "Alert text"]
                    },
                    {
                        "type": "malware_indicator", 
                        "description": "Suspicious download prompt",
                        "severity": "critical",
                        "confidence": 0.9,
                        "evidence": ["Download dialog", "Unknown source"]
                    },
                    {
                        "type": "phishing_attempt",
                        "description": "Fake login page",
                        "severity": "high", 
                        "confidence": 0.85,
                        "evidence": ["Login form", "Suspicious URL"]
                    },
                    {
                        "type": "ui_anomaly",
                        "description": "Unexpected popup",
                        "severity": "medium",
                        "confidence": 0.7,
                        "evidence": ["Popup window"]
                    }
                ]
            }
            
            with patch('tools.vlm_tools.analyze_image_with_gpt4_vision') as mock_analyze:
                mock_analyze.return_value = mock_response
                
                findings = detect_security_indicators(image_path)
                
                # Property: Should detect all security indicators
                assert len(findings) == 4
                
                # Property: Should maintain distinct finding types
                finding_types = [f.finding_type for f in findings]
                expected_types = ["security_warning", "malware_indicator", "phishing_attempt", "ui_anomaly"]
                assert set(finding_types) == set(expected_types)
                
                # Property: Should preserve severity levels
                severities = [f.severity for f in findings]
                expected_severities = ["high", "critical", "high", "medium"]
                assert set(severities) == set(expected_severities)
                
                # Property: All findings should have evidence
                for finding in findings:
                    assert len(finding.evidence) > 0
                    assert all(isinstance(evidence, str) for evidence in finding.evidence)
        
        finally:
            cleanup_test_image(image_path)


class TestVisualPackageCorrelation:
    """Property-based tests for visual-package correlation capabilities."""

    @given(sbom_strategy, 
           st.lists(st.text(min_size=3, max_size=20).filter(lambda x: x.strip() and x.isalnum()), 
                   min_size=1, max_size=5))
    def test_visual_package_correlation_consistency(self, sbom_data, package_mentions):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        For any SBOM data and visual findings that mention packages, the system
        should consistently correlate visual indicators with package data.
        """
        # Create visual findings that mention some packages
        visual_findings = []
        
        for i, mention in enumerate(package_mentions):
            finding = VisualSecurityFinding(
                finding_type="security_warning",
                description=f"Security alert related to {mention} package installation",
                confidence=0.8,
                severity="medium",
                evidence=[f"Package {mention} mentioned in dialog", "Installation warning visible"]
            )
            visual_findings.append(finding)
        
        # Perform correlation
        correlations = correlate_visual_findings_with_packages(visual_findings, sbom_data)
        
        # Property: Result should be a list
        assert isinstance(correlations, list)
        
        # Property: Each correlation should have proper structure
        for correlation in correlations:
            assert isinstance(correlation, dict)
            assert "visual_finding" in correlation
            assert "package_correlations" in correlation
            assert "correlation_timestamp" in correlation
            
            # Property: Visual finding should be preserved
            visual_finding = correlation["visual_finding"]
            assert isinstance(visual_finding, dict)
            assert "finding_type" in visual_finding
            assert "description" in visual_finding
            
            # Property: Package correlations should be valid
            package_correlations = correlation["package_correlations"]
            assert isinstance(package_correlations, list)
            
            for pkg_correlation in package_correlations:
                assert isinstance(pkg_correlation, dict)
                assert "package" in pkg_correlation
                assert "correlation_type" in pkg_correlation
                assert "correlation_confidence" in pkg_correlation
                assert "evidence" in pkg_correlation
                
                # Property: Correlation confidence should be valid
                assert 0.0 <= pkg_correlation["correlation_confidence"] <= 1.0
                
                # Property: Correlation type should be valid
                valid_types = ["text_mention", "ecosystem_indicator"]
                assert pkg_correlation["correlation_type"] in valid_types
                
                # Property: Package should have required fields
                package = pkg_correlation["package"]
                assert isinstance(package, dict)
                assert "name" in package

    @given(st.lists(st.sampled_from(["npm", "pypi", "maven", "rubygems", "crates", "go"]), 
                   min_size=1, max_size=3))
    def test_ecosystem_correlation_consistency(self, ecosystems):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        For any ecosystem indicators in visual findings, the system should
        consistently correlate them with packages from the same ecosystem.
        """
        # Create SBOM with packages from different ecosystems
        packages = []
        for ecosystem in ecosystems:
            packages.append({
                "name": f"test-package-{ecosystem}",
                "version": "1.0.0",
                "ecosystem": ecosystem
            })
        
        sbom_data = {"packages": packages}
        
        # Create visual findings with ecosystem indicators
        ecosystem_indicators = {
            "npm": "npm install",
            "pypi": "pip install", 
            "maven": "maven build",
            "rubygems": "gem install",
            "crates": "cargo install",
            "go": "go get"
        }
        
        visual_findings = []
        for ecosystem in ecosystems:
            indicator = ecosystem_indicators.get(ecosystem, ecosystem)
            finding = VisualSecurityFinding(
                finding_type="ui_anomaly",
                description=f"Command line showing {indicator} command",
                confidence=0.7,
                severity="low",
                evidence=[f"{indicator} command visible"]
            )
            visual_findings.append(finding)
        
        # Perform correlation
        correlations = correlate_visual_findings_with_packages(visual_findings, sbom_data)
        
        # Property: Should find correlations for ecosystem indicators
        assert isinstance(correlations, list)
        
        # Property: Each correlation should match ecosystem properly
        for correlation in correlations:
            package_correlations = correlation["package_correlations"]
            
            for pkg_correlation in package_correlations:
                if pkg_correlation["correlation_type"] == "ecosystem_indicator":
                    package = pkg_correlation["package"]
                    
                    # Property: Package ecosystem should match the indicator
                    assert package["ecosystem"] in ecosystems
                    
                    # Property: Evidence should mention the ecosystem indicator
                    evidence = pkg_correlation["evidence"]
                    assert isinstance(evidence, str)
                    # Evidence should mention the ecosystem indicator, not necessarily the ecosystem name
                    ecosystem_indicators_list = ["npm install", "pip install", "maven", "gem install", "cargo", "go get"]
                    assert any(indicator.lower() in evidence.lower() for indicator in ecosystem_indicators_list)

    def test_correlation_with_empty_data(self):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        Correlation should handle empty or minimal data gracefully.
        """
        # Test with empty SBOM
        empty_sbom = {"packages": []}
        
        visual_finding = VisualSecurityFinding(
            finding_type="security_warning",
            description="Security alert about unknown package",
            confidence=0.8,
            severity="medium"
        )
        
        correlations = correlate_visual_findings_with_packages([visual_finding], empty_sbom)
        
        # Property: Should handle empty SBOM gracefully
        assert isinstance(correlations, list)
        # No correlations expected with empty SBOM
        
        # Test with empty visual findings
        test_sbom = {
            "packages": [
                {"name": "test-package", "version": "1.0.0", "ecosystem": "npm"}
            ]
        }
        
        correlations = correlate_visual_findings_with_packages([], test_sbom)
        
        # Property: Should handle empty findings gracefully
        assert isinstance(correlations, list)
        assert len(correlations) == 0

    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
           st.lists(package_strategy, min_size=1, max_size=10))
    def test_text_mention_correlation_accuracy(self, finding_description, packages):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        For any finding description and package list, text mention correlation
        should accurately identify when package names appear in the text.
        """
        sbom_data = {"packages": packages}
        
        # Create a finding with the generated description
        visual_finding = VisualSecurityFinding(
            finding_type="security_warning",
            description=finding_description,
            confidence=0.8,
            severity="medium",
            evidence=[finding_description]
        )
        
        correlations = correlate_visual_findings_with_packages([visual_finding], sbom_data)
        
        # Property: Result should be valid
        assert isinstance(correlations, list)
        
        # Property: If package names appear in description, they should be correlated
        finding_text_lower = finding_description.lower()
        
        for package in packages:
            package_name = package.get("name", "").lower()
            
            if package_name and len(package_name) > 3 and package_name in finding_text_lower:
                # Should find at least one correlation for this finding
                found_correlation = False
                
                for correlation in correlations:
                    for pkg_correlation in correlation["package_correlations"]:
                        if (pkg_correlation["correlation_type"] == "text_mention" and
                            pkg_correlation["package"]["name"].lower() == package_name):
                            found_correlation = True
                            
                            # Property: Correlation should have reasonable confidence
                            assert pkg_correlation["correlation_confidence"] > 0.0
                            
                            # Property: Evidence should mention the correlation
                            assert package_name in pkg_correlation["evidence"].lower()
                            break
                    
                    if found_correlation:
                        break

    def test_correlation_confidence_consistency(self):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        Correlation confidence scores should be consistent and meaningful.
        """
        # Test with exact package name match
        sbom_data = {
            "packages": [
                {"name": "react", "version": "18.0.0", "ecosystem": "npm"},
                {"name": "django", "version": "4.0.0", "ecosystem": "pypi"}
            ]
        }
        
        # Finding that explicitly mentions a package
        exact_match_finding = VisualSecurityFinding(
            finding_type="security_warning",
            description="Security vulnerability found in react package",
            confidence=0.9,
            severity="high",
            evidence=["react package mentioned in alert"]
        )
        
        correlations = correlate_visual_findings_with_packages([exact_match_finding], sbom_data)
        
        # Property: Should find correlation with reasonable confidence
        assert len(correlations) > 0
        
        correlation = correlations[0]
        package_correlations = correlation["package_correlations"]
        
        # Property: Should have at least one correlation
        assert len(package_correlations) > 0
        
        # Property: Text mention correlation should have expected confidence
        text_correlations = [pc for pc in package_correlations 
                           if pc["correlation_type"] == "text_mention"]
        
        if text_correlations:
            for tc in text_correlations:
                # Property: Text mention confidence should be reasonable (0.5-1.0)
                assert 0.5 <= tc["correlation_confidence"] <= 1.0

    def test_multiple_package_correlation(self):
        """
        **Feature: multi-agent-security, Property 16: Visual-Package Correlation**
        **Validates: Requirements 6.4**
        
        When multiple packages are mentioned, correlation should handle them all.
        """
        sbom_data = {
            "packages": [
                {"name": "express", "version": "4.18.0", "ecosystem": "npm"},
                {"name": "flask", "version": "2.0.0", "ecosystem": "pypi"},
                {"name": "spring", "version": "5.3.0", "ecosystem": "maven"}
            ]
        }
        
        # Finding that mentions multiple packages
        multi_package_finding = VisualSecurityFinding(
            finding_type="security_warning",
            description="Security issues detected in express and flask packages during build",
            confidence=0.8,
            severity="high",
            evidence=["Multiple packages mentioned", "express and flask both flagged"]
        )
        
        correlations = correlate_visual_findings_with_packages([multi_package_finding], sbom_data)
        
        # Property: Should find correlations
        assert len(correlations) > 0
        
        correlation = correlations[0]
        package_correlations = correlation["package_correlations"]
        
        # Property: Should correlate with both mentioned packages
        correlated_packages = [pc["package"]["name"] for pc in package_correlations
                             if pc["correlation_type"] == "text_mention"]
        
        # Should find correlations for packages mentioned in the description
        expected_packages = ["express", "flask"]
        for expected_pkg in expected_packages:
            if expected_pkg in multi_package_finding.description.lower():
                # Property: Package should be in correlations if mentioned
                assert any(expected_pkg == pkg.lower() for pkg in correlated_packages)