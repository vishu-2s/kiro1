"""
Property-based tests for comprehensive reporting system.

**Feature: multi-agent-security, Property 17: Comprehensive Reporting**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

**Feature: multi-agent-security, Property 18: Dual Output Format**
**Validates: Requirements 7.5**
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume
from typing import Dict, List, Any
import string
from datetime import datetime
from dataclasses import asdict

from report_generator import (
    SecurityReportGenerator,
    ComprehensiveReport,
    RiskAssessment,
    AttackClassification,
    RemediationPlan,
    Timeline,
    StakeholderGuidance,
    create_security_report,
    generate_executive_summary
)
from analyze_supply_chain import (
    AnalysisResult,
    AnalysisMetadata,
    AnalysisSummary,
    SupplyChainAnalyzer
)


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

# Strategy for generating analysis metadata
analysis_metadata_strategy = st.builds(
    AnalysisMetadata,
    analysis_id=st.text(min_size=10, max_size=50),
    analysis_type=st.sampled_from(["github_repository", "local_directory", "sbom_file"]),
    target=st.text(min_size=5, max_size=100),
    start_time=st.just(datetime.now().isoformat()),
    end_time=st.just(datetime.now().isoformat()),
    total_packages=st.integers(min_value=0, max_value=1000),
    total_findings=st.integers(min_value=0, max_value=100),
    confidence_threshold=st.floats(min_value=0.0, max_value=1.0),
    osv_enabled=st.booleans(),
    visual_analysis_enabled=st.booleans()
)

# Strategy for generating analysis summary
def analysis_summary_strategy(findings_list):
    """Generate analysis summary that matches the findings."""
    total_findings = len(findings_list)
    
    # Count findings by severity
    critical_count = sum(1 for f in findings_list if f.get("severity") == "critical")
    high_count = sum(1 for f in findings_list if f.get("severity") == "high")
    medium_count = sum(1 for f in findings_list if f.get("severity") == "medium")
    low_count = sum(1 for f in findings_list if f.get("severity") == "low")
    
    # Count finding types
    finding_types = {}
    for finding in findings_list:
        finding_type = finding.get("finding_type", "unknown")
        finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
    
    # Count confidence distribution
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for finding in findings_list:
        confidence = finding.get("confidence", 0.5)
        if confidence >= 0.8:
            confidence_dist["high"] += 1
        elif confidence >= 0.5:
            confidence_dist["medium"] += 1
        else:
            confidence_dist["low"] += 1
    
    return AnalysisSummary(
        total_packages=max(1, total_findings),  # At least 1 package if there are findings
        total_findings=total_findings,
        critical_findings=critical_count,
        high_findings=high_count,
        medium_findings=medium_count,
        low_findings=low_count,
        ecosystems_analyzed=["npm", "pypi"] if total_findings > 0 else ["npm"],
        finding_types=finding_types,
        confidence_distribution=confidence_dist
    )

# Strategy for generating complete analysis results
@st.composite
def analysis_result_strategy(draw):
    """Generate complete AnalysisResult with consistent data."""
    findings = draw(st.lists(security_finding_strategy, min_size=0, max_size=20))
    metadata = draw(analysis_metadata_strategy)
    summary = analysis_summary_strategy(findings)
    
    # Update metadata to match summary
    metadata.total_findings = summary.total_findings
    
    return AnalysisResult(
        metadata=metadata,
        summary=summary,
        sbom_data=draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.lists(st.text())),
            min_size=0, max_size=10
        )),
        security_findings=findings,
        suspicious_activities=draw(st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(st.text(), st.floats(), st.booleans()),
                min_size=1, max_size=10
            ),
            min_size=0, max_size=5
        )),
        recommendations=draw(st.lists(st.text(min_size=10, max_size=200), min_size=0, max_size=10)),
        raw_data=None
    )


class TestComprehensiveReporting:
    """Property-based tests for comprehensive reporting."""

    @given(analysis_result_strategy())
    def test_comprehensive_report_structure_consistency(self, analysis_result: AnalysisResult):
        """
        **Feature: multi-agent-security, Property 17: Comprehensive Reporting**
        
        For any completed analysis, the system should generate reports with risk assessment,
        attack classification, containment steps, remediation plans, timeline, and 
        stakeholder guidance.
        """
        assume(isinstance(analysis_result, AnalysisResult))
        
        # Generate comprehensive report
        generator = SecurityReportGenerator()
        report = generator.generate_comprehensive_report(analysis_result)
        
        # Property: Report should be ComprehensiveReport object
        assert isinstance(report, ComprehensiveReport), "Report should be ComprehensiveReport object"
        
        # Property: All required top-level components should be present
        assert hasattr(report, 'analysis_result'), "Report should have analysis_result"
        assert hasattr(report, 'risk_assessment'), "Report should have risk_assessment"
        assert hasattr(report, 'attack_classification'), "Report should have attack_classification"
        assert hasattr(report, 'remediation_plan'), "Report should have remediation_plan"
        assert hasattr(report, 'timeline'), "Report should have timeline"
        assert hasattr(report, 'stakeholder_guidance'), "Report should have stakeholder_guidance"
        assert hasattr(report, 'report_metadata'), "Report should have report_metadata"
        
        # Property: Risk assessment should have required fields
        risk = report.risk_assessment
        assert isinstance(risk, RiskAssessment), "Risk assessment should be RiskAssessment object"
        assert hasattr(risk, 'overall_risk_level'), "Risk should have overall_risk_level"
        assert hasattr(risk, 'risk_score'), "Risk should have risk_score"
        assert hasattr(risk, 'attack_vectors'), "Risk should have attack_vectors"
        assert hasattr(risk, 'business_impact'), "Risk should have business_impact"
        assert hasattr(risk, 'likelihood'), "Risk should have likelihood"
        assert hasattr(risk, 'risk_factors'), "Risk should have risk_factors"
        assert hasattr(risk, 'mitigation_priority'), "Risk should have mitigation_priority"
        
        # Property: Risk level should be valid
        valid_risk_levels = ["critical", "high", "medium", "low", "none"]
        assert risk.overall_risk_level in valid_risk_levels, f"Risk level should be one of {valid_risk_levels}"
        
        # Property: Risk score should be in valid range
        assert 0.0 <= risk.risk_score <= 10.0, "Risk score should be between 0.0 and 10.0"

    def test_dual_format_file_generation(self):
        """
        **Feature: multi-agent-security, Property 18: Dual Output Format**
        
        For any analysis result, both JSON and HTML files should be generated
        and saved successfully.
        """
        # Create test analysis result
        test_metadata = AnalysisMetadata(
            analysis_id="test_analysis_123",
            analysis_type="test",
            target="test_target",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_packages=10,
            total_findings=5,
            confidence_threshold=0.7,
            osv_enabled=True,
            visual_analysis_enabled=False
        )
        
        test_summary = AnalysisSummary(
            total_packages=10,
            total_findings=5,
            critical_findings=1,
            high_findings=2,
            medium_findings=1,
            low_findings=1,
            ecosystems_analyzed=["npm", "pypi"],
            finding_types={"vulnerability": 3, "malicious_package": 2},
            confidence_distribution={"high": 3, "medium": 2, "low": 0}
        )
        
        test_findings = [
            {
                "package": "test-pkg",
                "version": "1.0.0",
                "finding_type": "vulnerability",
                "severity": "high",
                "confidence": 0.9,
                "evidence": ["Test evidence"],
                "recommendations": ["Test recommendation"],
                "source": "test",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        analysis_result = AnalysisResult(
            metadata=test_metadata,
            summary=test_summary,
            sbom_data={"packages": []},
            security_findings=test_findings,
            suspicious_activities=[],
            recommendations=["Test recommendation"],
            raw_data=None
        )
        
        # Property: Dual format generation should work
        with tempfile.TemporaryDirectory() as temp_dir:
            result_paths = create_security_report(
                analysis_result, 
                output_format="both",
                output_dir=temp_dir
            )
            
            # Property: Both formats should be generated
            assert "json" in result_paths, "JSON report should be generated"
            assert "html" in result_paths, "HTML report should be generated"
            
            # Property: Files should exist
            assert os.path.exists(result_paths["json"]), "JSON file should exist"
            assert os.path.exists(result_paths["html"]), "HTML file should exist"
            
            # Property: Files should not be empty
            json_size = os.path.getsize(result_paths["json"])
            html_size = os.path.getsize(result_paths["html"])
            
            assert json_size > 0, "JSON file should not be empty"
            assert html_size > 0, "HTML file should not be empty"


class TestDualOutputFormat:
    """Property-based tests for dual output format."""

    @given(analysis_result_strategy())
    def test_json_output_format_consistency(self, analysis_result: AnalysisResult):
        """
        **Feature: multi-agent-security, Property 18: Dual Output Format**
        
        For any completed analysis, the system should generate both JSON and HTML reports
        with consistent data.
        """
        assume(isinstance(analysis_result, AnalysisResult))
        
        generator = SecurityReportGenerator()
        comprehensive_report = generator.generate_comprehensive_report(analysis_result)
        
        # Property: JSON serialization should work without errors
        try:
            report_dict = asdict(comprehensive_report)
            json_str = json.dumps(report_dict, default=str)
            assert isinstance(json_str, str), "JSON serialization should produce string"
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")
        
        # Property: JSON should be deserializable
        try:
            deserialized = json.loads(json_str)
            assert isinstance(deserialized, dict), "Deserialized JSON should be dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON deserialization failed: {e}")
        
        # Property: Deserialized structure should have expected keys
        expected_keys = {
            "analysis_result", "risk_assessment", "attack_classification",
            "remediation_plan", "timeline", "stakeholder_guidance", "report_metadata"
        }
        assert set(deserialized.keys()) == expected_keys, "JSON should have all expected top-level keys"

    def test_executive_summary_generation(self):
        """
        **Feature: multi-agent-security, Property 17: Comprehensive Reporting**
        
        For any analysis result, executive summary should provide concise
        overview of key findings and risk level.
        """
        # Create test analysis result
        test_metadata = AnalysisMetadata(
            analysis_id="test_exec_summary",
            analysis_type="test",
            target="test_target",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_packages=50,
            total_findings=8,
            confidence_threshold=0.7,
            osv_enabled=True,
            visual_analysis_enabled=False
        )
        
        test_summary = AnalysisSummary(
            total_packages=50,
            total_findings=8,
            critical_findings=2,
            high_findings=3,
            medium_findings=2,
            low_findings=1,
            ecosystems_analyzed=["npm", "pypi", "maven"],
            finding_types={"vulnerability": 5, "malicious_package": 3},
            confidence_distribution={"high": 5, "medium": 3, "low": 0}
        )
        
        analysis_result = AnalysisResult(
            metadata=test_metadata,
            summary=test_summary,
            sbom_data={"packages": []},
            security_findings=[],
            suspicious_activities=[],
            recommendations=["Test recommendation"],
            raw_data=None
        )
        
        # Property: Executive summary should be generated
        exec_summary = generate_executive_summary(analysis_result)
        
        assert isinstance(exec_summary, str), "Executive summary should be string"
        assert len(exec_summary) > 0, "Executive summary should not be empty"
        
        # Property: Executive summary should contain key information
        exec_lower = exec_summary.lower()
        assert "8" in exec_summary, "Executive summary should mention total findings"
        assert "50" in exec_summary, "Executive summary should mention total packages"
        assert "critical" in exec_lower or "high" in exec_lower, "Executive summary should mention risk level"