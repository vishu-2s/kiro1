"""
Property-based tests for core analysis engine.

**Feature: multi-agent-security, Property 5: Structured Output Generation**
**Validates: Requirements 1.5**
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any
import string
from datetime import datetime

from analyze_supply_chain import (
    SupplyChainAnalyzer,
    AnalysisResult,
    AnalysisMetadata,
    AnalysisSummary,
    AnalysisError,
    create_analyzer,
    analyze_target
)
from tools.sbom_tools import SecurityFinding, SBOMPackage


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

ecosystem_strategy = st.sampled_from(["npm", "pypi", "maven", "rubygems", "crates", "go"])

severity_strategy = st.sampled_from(["critical", "high", "medium", "low"])

confidence_strategy = st.floats(min_value=0.0, max_value=1.0)

finding_type_strategy = st.sampled_from([
    "malicious_package", "vulnerability", "typosquat", "suspicious_activity"
])

# Strategy for generating security findings
security_finding_strategy = st.builds(
    dict,
    package=package_name_strategy,
    version=version_strategy,
    finding_type=finding_type_strategy,
    severity=severity_strategy,
    confidence=confidence_strategy,
    evidence=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5),
    recommendations=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=3),
    source=st.text(min_size=1, max_size=50),
    timestamp=st.just(datetime.now().isoformat())
)

# Strategy for generating SBOM package data
sbom_package_strategy = st.builds(
    dict,
    name=package_name_strategy,
    version=version_strategy,
    ecosystem=ecosystem_strategy,
    purl=st.text(min_size=0, max_size=100),
    dependencies=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5),
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


class TestStructuredOutputGeneration:
    """Property-based tests for structured output generation."""

    @given(sbom_data_strategy, st.lists(security_finding_strategy, min_size=0, max_size=10))
    @settings(deadline=None)
    def test_analysis_result_structure_consistency(self, sbom_data: Dict[str, Any], 
                                                  findings: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any completed analysis, the system should generate findings in valid 
        JSON format with all required fields.
        """
        assume(isinstance(sbom_data, dict))
        assume(isinstance(findings, list))
        
        # Create analyzer
        analyzer = SupplyChainAnalyzer(confidence_threshold=0.0)  # Accept all findings
        
        # Mock the security analysis to return our test findings
        with patch.object(analyzer, '_analyze_sbom_security') as mock_analyze:
            # Convert dict findings to SecurityFinding objects
            security_findings = []
            for finding_dict in findings:
                finding = SecurityFinding(
                    package=finding_dict["package"],
                    version=finding_dict["version"],
                    finding_type=finding_dict["finding_type"],
                    severity=finding_dict["severity"],
                    confidence=finding_dict["confidence"],
                    evidence=finding_dict["evidence"],
                    recommendations=finding_dict["recommendations"],
                    source=finding_dict["source"]
                )
                security_findings.append(finding)
            
            mock_analyze.return_value = security_findings
            
            # Mock suspicious activity detection
            with patch.object(analyzer, '_detect_suspicious_activities') as mock_suspicious:
                mock_suspicious.return_value = []
                
                # Compile analysis result
                start_time = datetime.now()
                end_time = datetime.now()
                
                result = analyzer._compile_analysis_result(
                    analysis_type="test",
                    target="test_target",
                    start_time=start_time,
                    end_time=end_time,
                    sbom_data=sbom_data,
                    security_findings=security_findings,
                    suspicious_activities=[],
                    raw_data=None
                )
        
        # Property: Result should be AnalysisResult object
        assert isinstance(result, AnalysisResult), "Result should be AnalysisResult object"
        
        # Property: All required top-level fields should be present
        assert hasattr(result, 'metadata'), "Result should have metadata field"
        assert hasattr(result, 'summary'), "Result should have summary field"
        assert hasattr(result, 'sbom_data'), "Result should have sbom_data field"
        assert hasattr(result, 'security_findings'), "Result should have security_findings field"
        assert hasattr(result, 'suspicious_activities'), "Result should have suspicious_activities field"
        assert hasattr(result, 'recommendations'), "Result should have recommendations field"
        
        # Property: Metadata should have required fields
        metadata = result.metadata
        assert isinstance(metadata, AnalysisMetadata), "Metadata should be AnalysisMetadata object"
        assert hasattr(metadata, 'analysis_id'), "Metadata should have analysis_id"
        assert hasattr(metadata, 'analysis_type'), "Metadata should have analysis_type"
        assert hasattr(metadata, 'target'), "Metadata should have target"
        assert hasattr(metadata, 'start_time'), "Metadata should have start_time"
        assert hasattr(metadata, 'end_time'), "Metadata should have end_time"
        assert hasattr(metadata, 'total_packages'), "Metadata should have total_packages"
        assert hasattr(metadata, 'total_findings'), "Metadata should have total_findings"
        
        # Property: Summary should have required fields
        summary = result.summary
        assert isinstance(summary, AnalysisSummary), "Summary should be AnalysisSummary object"
        assert hasattr(summary, 'total_packages'), "Summary should have total_packages"
        assert hasattr(summary, 'total_findings'), "Summary should have total_findings"
        assert hasattr(summary, 'critical_findings'), "Summary should have critical_findings"
        assert hasattr(summary, 'high_findings'), "Summary should have high_findings"
        assert hasattr(summary, 'medium_findings'), "Summary should have medium_findings"
        assert hasattr(summary, 'low_findings'), "Summary should have low_findings"
        assert hasattr(summary, 'ecosystems_analyzed'), "Summary should have ecosystems_analyzed"
        assert hasattr(summary, 'finding_types'), "Summary should have finding_types"
        
        # Property: Security findings should be list of dictionaries
        assert isinstance(result.security_findings, list), "Security findings should be list"
        for finding in result.security_findings:
            assert isinstance(finding, dict), "Each finding should be dictionary"
            
            # Required finding fields
            required_fields = ["package", "version", "finding_type", "severity", 
                             "confidence", "evidence", "recommendations", "source", "timestamp"]
            for field in required_fields:
                assert field in finding, f"Finding should contain {field} field"
        
        # Property: Recommendations should be list of strings
        assert isinstance(result.recommendations, list), "Recommendations should be list"
        for recommendation in result.recommendations:
            assert isinstance(recommendation, str), "Each recommendation should be string"
        
        # Property: SBOM data should match input
        assert result.sbom_data == sbom_data, "SBOM data should match input"

    @given(sbom_data_strategy)
    @settings(deadline=None)
    def test_json_serialization_consistency(self, sbom_data: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any analysis result, JSON serialization should produce valid JSON
        that can be deserialized back to equivalent structure.
        """
        assume(isinstance(sbom_data, dict))
        
        # Create analyzer and generate result
        analyzer = SupplyChainAnalyzer()
        
        with patch.object(analyzer, '_analyze_sbom_security') as mock_analyze:
            mock_analyze.return_value = []
            
            with patch.object(analyzer, '_detect_suspicious_activities') as mock_suspicious:
                mock_suspicious.return_value = []
                
                start_time = datetime.now()
                end_time = datetime.now()
                
                result = analyzer._compile_analysis_result(
                    analysis_type="test",
                    target="test_target",
                    start_time=start_time,
                    end_time=end_time,
                    sbom_data=sbom_data,
                    security_findings=[],
                    suspicious_activities=[],
                    raw_data=None
                )
        
        # Property: Result should be serializable to JSON
        try:
            from dataclasses import asdict
            result_dict = asdict(result)
            json_str = json.dumps(result_dict, default=str)
            assert isinstance(json_str, str), "JSON serialization should produce string"
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")
        
        # Property: Serialized JSON should be deserializable
        try:
            deserialized = json.loads(json_str)
            assert isinstance(deserialized, dict), "Deserialized JSON should be dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON deserialization failed: {e}")
        
        # Property: Deserialized structure should have same top-level keys
        expected_keys = {"metadata", "summary", "sbom_data", "security_findings", 
                        "suspicious_activities", "recommendations", "raw_data"}
        assert set(deserialized.keys()) == expected_keys, "Deserialized structure should have expected keys"

    def test_analysis_result_field_types(self):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any analysis result, all fields should have correct types and
        satisfy data validation constraints.
        """
        # Create test data
        test_sbom = {
            "format": "test-sbom",
            "packages": [
                {"name": "test-pkg", "version": "1.0.0", "ecosystem": "npm"}
            ],
            "metadata": {"total_packages": 1}
        }
        
        test_finding = SecurityFinding(
            package="test-pkg",
            version="1.0.0",
            finding_type="vulnerability",
            severity="high",
            confidence=0.8,
            evidence=["Test evidence"],
            recommendations=["Test recommendation"]
        )
        
        analyzer = SupplyChainAnalyzer()
        
        with patch.object(analyzer, '_analyze_sbom_security') as mock_analyze:
            mock_analyze.return_value = [test_finding]
            
            with patch.object(analyzer, '_detect_suspicious_activities') as mock_suspicious:
                mock_suspicious.return_value = []
                
                start_time = datetime.now()
                end_time = datetime.now()
                
                result = analyzer._compile_analysis_result(
                    analysis_type="test",
                    target="test_target",
                    start_time=start_time,
                    end_time=end_time,
                    sbom_data=test_sbom,
                    security_findings=[test_finding],
                    suspicious_activities=[],
                    raw_data=None
                )
        
        # Property: Metadata field types
        assert isinstance(result.metadata.analysis_id, str), "Analysis ID should be string"
        assert isinstance(result.metadata.analysis_type, str), "Analysis type should be string"
        assert isinstance(result.metadata.target, str), "Target should be string"
        assert isinstance(result.metadata.start_time, str), "Start time should be string"
        assert isinstance(result.metadata.end_time, str), "End time should be string"
        assert isinstance(result.metadata.total_packages, int), "Total packages should be integer"
        assert isinstance(result.metadata.total_findings, int), "Total findings should be integer"
        assert isinstance(result.metadata.confidence_threshold, (int, float)), "Confidence threshold should be numeric"
        assert isinstance(result.metadata.osv_enabled, bool), "OSV enabled should be boolean"
        assert isinstance(result.metadata.visual_analysis_enabled, bool), "Visual analysis enabled should be boolean"
        
        # Property: Summary field types
        assert isinstance(result.summary.total_packages, int), "Total packages should be integer"
        assert isinstance(result.summary.total_findings, int), "Total findings should be integer"
        assert isinstance(result.summary.critical_findings, int), "Critical findings should be integer"
        assert isinstance(result.summary.high_findings, int), "High findings should be integer"
        assert isinstance(result.summary.medium_findings, int), "Medium findings should be integer"
        assert isinstance(result.summary.low_findings, int), "Low findings should be integer"
        assert isinstance(result.summary.ecosystems_analyzed, list), "Ecosystems should be list"
        assert isinstance(result.summary.finding_types, dict), "Finding types should be dict"
        assert isinstance(result.summary.confidence_distribution, dict), "Confidence distribution should be dict"
        
        # Property: Numeric constraints
        assert result.metadata.total_packages >= 0, "Total packages should be non-negative"
        assert result.metadata.total_findings >= 0, "Total findings should be non-negative"
        assert 0.0 <= result.metadata.confidence_threshold <= 1.0, "Confidence threshold should be 0-1"
        
        # Property: Summary consistency
        severity_sum = (result.summary.critical_findings + result.summary.high_findings + 
                       result.summary.medium_findings + result.summary.low_findings)
        assert severity_sum == result.summary.total_findings, "Severity counts should sum to total findings"

    @given(st.lists(security_finding_strategy, min_size=1, max_size=10))
    @settings(deadline=None)
    def test_finding_aggregation_consistency(self, findings: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any set of security findings, aggregation and summary statistics
        should be calculated correctly and consistently.
        """
        assume(len(findings) > 0)
        
        # Convert to SecurityFinding objects
        security_findings = []
        for finding_dict in findings:
            finding = SecurityFinding(
                package=finding_dict["package"],
                version=finding_dict["version"],
                finding_type=finding_dict["finding_type"],
                severity=finding_dict["severity"],
                confidence=finding_dict["confidence"],
                evidence=finding_dict["evidence"],
                recommendations=finding_dict["recommendations"],
                source=finding_dict["source"]
            )
            security_findings.append(finding)
        
        analyzer = SupplyChainAnalyzer()
        
        with patch.object(analyzer, '_analyze_sbom_security') as mock_analyze:
            mock_analyze.return_value = security_findings
            
            with patch.object(analyzer, '_detect_suspicious_activities') as mock_suspicious:
                mock_suspicious.return_value = []
                
                test_sbom = {"packages": [], "metadata": {}}
                start_time = datetime.now()
                end_time = datetime.now()
                
                result = analyzer._compile_analysis_result(
                    analysis_type="test",
                    target="test_target",
                    start_time=start_time,
                    end_time=end_time,
                    sbom_data=test_sbom,
                    security_findings=security_findings,
                    suspicious_activities=[],
                    raw_data=None
                )
        
        # Property: Total findings should match input count
        assert result.summary.total_findings == len(findings), "Total findings should match input count"
        
        # Property: Severity counts should be accurate
        expected_critical = sum(1 for f in findings if f["severity"] == "critical")
        expected_high = sum(1 for f in findings if f["severity"] == "high")
        expected_medium = sum(1 for f in findings if f["severity"] == "medium")
        expected_low = sum(1 for f in findings if f["severity"] == "low")
        
        assert result.summary.critical_findings == expected_critical, "Critical count should be accurate"
        assert result.summary.high_findings == expected_high, "High count should be accurate"
        assert result.summary.medium_findings == expected_medium, "Medium count should be accurate"
        assert result.summary.low_findings == expected_low, "Low count should be accurate"
        
        # Property: Finding type counts should be accurate
        expected_types = {}
        for finding in findings:
            finding_type = finding["finding_type"]
            expected_types[finding_type] = expected_types.get(finding_type, 0) + 1
        
        assert result.summary.finding_types == expected_types, "Finding type counts should be accurate"
        
        # Property: Confidence distribution should be accurate
        expected_confidence = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            confidence = finding["confidence"]
            if confidence >= 0.8:
                expected_confidence["high"] += 1
            elif confidence >= 0.5:
                expected_confidence["medium"] += 1
            else:
                expected_confidence["low"] += 1
        
        assert result.summary.confidence_distribution == expected_confidence, "Confidence distribution should be accurate"

    def test_save_analysis_result_consistency(self):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any analysis result, saving to file should produce valid JSON
        that can be loaded back with identical structure.
        """
        # Create test result
        analyzer = SupplyChainAnalyzer()
        
        test_sbom = {
            "format": "test-sbom",
            "packages": [{"name": "test-pkg", "version": "1.0.0", "ecosystem": "npm"}],
            "metadata": {"total_packages": 1}
        }
        
        with patch.object(analyzer, '_analyze_sbom_security') as mock_analyze:
            mock_analyze.return_value = []
            
            with patch.object(analyzer, '_detect_suspicious_activities') as mock_suspicious:
                mock_suspicious.return_value = []
                
                start_time = datetime.now()
                end_time = datetime.now()
                
                result = analyzer._compile_analysis_result(
                    analysis_type="test",
                    target="test_target",
                    start_time=start_time,
                    end_time=end_time,
                    sbom_data=test_sbom,
                    security_findings=[],
                    suspicious_activities=[],
                    raw_data=None
                )
        
        # Property: Save and load should preserve structure
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_result.json")
            
            # Save result
            saved_path = analyzer.save_analysis_result(result, output_path)
            assert saved_path == output_path, "Saved path should match requested path"
            assert os.path.exists(output_path), "Output file should exist"
            
            # Load and verify
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            # Property: Loaded data should be dictionary
            assert isinstance(loaded_data, dict), "Loaded data should be dictionary"
            
            # Property: Should have all expected top-level keys
            expected_keys = {"metadata", "summary", "sbom_data", "security_findings", 
                           "suspicious_activities", "recommendations", "raw_data"}
            assert set(loaded_data.keys()) == expected_keys, "Loaded data should have expected keys"
            
            # Property: Metadata should be preserved
            metadata = loaded_data["metadata"]
            assert metadata["analysis_type"] == "test", "Analysis type should be preserved"
            assert metadata["target"] == "test_target", "Target should be preserved"
            
            # Property: SBOM data should be preserved
            assert loaded_data["sbom_data"] == test_sbom, "SBOM data should be preserved"

    def test_analyzer_creation_consistency(self):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any analyzer configuration, creation should produce consistent
        analyzer instances with expected properties.
        """
        # Test default creation
        analyzer1 = create_analyzer()
        assert isinstance(analyzer1, SupplyChainAnalyzer), "Should create SupplyChainAnalyzer instance"
        assert hasattr(analyzer1, 'analysis_id'), "Should have analysis_id"
        assert hasattr(analyzer1, 'confidence_threshold'), "Should have confidence_threshold"
        assert hasattr(analyzer1, 'enable_osv'), "Should have enable_osv"
        
        # Test with custom parameters
        analyzer2 = create_analyzer(confidence_threshold=0.8, enable_osv=False)
        assert analyzer2.confidence_threshold == 0.8, "Should use custom confidence threshold"
        assert analyzer2.enable_osv == False, "Should use custom OSV setting"
        
        # Property: Different instances should have different analysis IDs
        assert analyzer1.analysis_id != analyzer2.analysis_id, "Different instances should have different IDs"
        
        # Property: Analysis IDs should be strings
        assert isinstance(analyzer1.analysis_id, str), "Analysis ID should be string"
        assert isinstance(analyzer2.analysis_id, str), "Analysis ID should be string"
        
        # Property: Analysis IDs should not be empty
        assert len(analyzer1.analysis_id) > 0, "Analysis ID should not be empty"
        assert len(analyzer2.analysis_id) > 0, "Analysis ID should not be empty"

    def test_error_handling_consistency(self):
        """
        **Feature: multi-agent-security, Property 5: Structured Output Generation**
        
        For any error conditions, the system should handle them gracefully
        and provide meaningful error messages.
        """
        analyzer = SupplyChainAnalyzer()
        
        # Test invalid target handling
        with pytest.raises(AnalysisError):
            analyze_target("invalid://not-a-real-url", analysis_type="auto")
        
        # Test invalid analysis type
        with pytest.raises(AnalysisError):
            analyze_target("test_target", analysis_type="invalid_type")
        
        # Property: Error messages should be strings
        try:
            analyze_target("invalid://not-a-real-url", analysis_type="auto")
        except AnalysisError as e:
            assert isinstance(str(e), str), "Error message should be string"
            assert len(str(e)) > 0, "Error message should not be empty"