"""
Simple test for report generator to verify functionality.
"""

import pytest
from datetime import datetime
from report_generator import SecurityReportGenerator
from analyze_supply_chain import AnalysisResult, AnalysisMetadata, AnalysisSummary


def test_report_generator_creation():
    """Test that SecurityReportGenerator can be created."""
    generator = SecurityReportGenerator()
    assert generator is not None
    assert hasattr(generator, 'report_id')
    assert isinstance(generator.report_id, str)
    assert len(generator.report_id) > 0


def test_comprehensive_report_generation():
    """Test comprehensive report generation with minimal data."""
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
    
    # Generate comprehensive report
    generator = SecurityReportGenerator()
    report = generator.generate_comprehensive_report(analysis_result)
    
    # Verify report structure
    assert report is not None
    assert hasattr(report, 'analysis_result')
    assert hasattr(report, 'risk_assessment')
    assert hasattr(report, 'attack_classification')
    assert hasattr(report, 'remediation_plan')
    assert hasattr(report, 'timeline')
    assert hasattr(report, 'stakeholder_guidance')
    assert hasattr(report, 'report_metadata')
    
    # Verify risk assessment
    risk = report.risk_assessment
    assert risk.overall_risk_level in ["critical", "high", "medium", "low", "none"]
    assert 0.0 <= risk.risk_score <= 10.0
    assert isinstance(risk.attack_vectors, list)
    assert isinstance(risk.business_impact, str)
    assert len(risk.business_impact) > 0


def test_dual_output_format():
    """
    **Feature: multi-agent-security, Property 18: Dual Output Format**
    **Validates: Requirements 7.5**
    
    Test that both JSON and HTML reports can be generated.
    """
    # Create test analysis result
    test_metadata = AnalysisMetadata(
        analysis_id="test_dual_format",
        analysis_type="test",
        target="test_target",
        start_time=datetime.now().isoformat(),
        end_time=datetime.now().isoformat(),
        total_packages=5,
        total_findings=3,
        confidence_threshold=0.7,
        osv_enabled=True,
        visual_analysis_enabled=False
    )
    
    test_summary = AnalysisSummary(
        total_packages=5,
        total_findings=3,
        critical_findings=0,
        high_findings=1,
        medium_findings=2,
        low_findings=0,
        ecosystems_analyzed=["npm"],
        finding_types={"vulnerability": 2, "typosquat": 1},
        confidence_distribution={"high": 2, "medium": 1, "low": 0}
    )
    
    test_findings = [
        {
            "package": "test-pkg-1",
            "version": "1.0.0",
            "finding_type": "vulnerability",
            "severity": "high",
            "confidence": 0.9,
            "evidence": ["CVE-2023-1234"],
            "recommendations": ["Update to version 1.0.1"],
            "source": "test",
            "timestamp": datetime.now().isoformat()
        },
        {
            "package": "test-pkg-2",
            "version": "2.0.0",
            "finding_type": "typosquat",
            "severity": "medium",
            "confidence": 0.8,
            "evidence": ["Similar to popular package"],
            "recommendations": ["Verify package legitimacy"],
            "source": "test",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    analysis_result = AnalysisResult(
        metadata=test_metadata,
        summary=test_summary,
        sbom_data={"packages": [{"name": "test-pkg-1", "version": "1.0.0"}]},
        security_findings=test_findings,
        suspicious_activities=[],
        recommendations=["Review all findings", "Update vulnerable packages"],
        raw_data=None
    )
    
    # Test dual format generation
    from report_generator import create_security_report
    import tempfile
    import os
    import json
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate both formats
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
        
        # Property: JSON file should be valid JSON
        with open(result_paths["json"], 'r') as f:
            json_data = json.load(f)
            assert isinstance(json_data, dict), "JSON file should contain valid JSON object"
            
            # Property: JSON should have expected structure
            expected_keys = {
                "analysis_result", "risk_assessment", "attack_classification",
                "remediation_plan", "timeline", "stakeholder_guidance", "report_metadata"
            }
            assert set(json_data.keys()) == expected_keys, "JSON should have all expected top-level keys"
        
        # Property: HTML file should contain HTML tags and key information
        with open(result_paths["html"], 'r') as f:
            html_content = f.read()
            html_lower = html_content.lower()
            
            # Basic HTML structure
            assert "<html" in html_lower, "HTML file should contain HTML tags"
            assert "<head>" in html_lower, "HTML should have head section"
            assert "<body>" in html_lower, "HTML should have body section"
            assert "</html>" in html_lower, "HTML should close html tag"
            
            # Required sections
            required_sections = [
                "executive summary",
                "risk assessment", 
                "attack classification",
                "detailed findings",
                "remediation plan",
                "timeline",
                "stakeholder communication"
            ]
            
            for section in required_sections:
                assert section in html_lower, f"HTML should contain '{section}' section"
            
            # Key data should be present
            assert "test_dual_format" in html_content, "HTML should contain analysis ID"
            assert "3" in html_content, "HTML should show total findings"
            assert "test-pkg-1" in html_content, "HTML should show package names"


def test_json_only_format():
    """
    **Feature: multi-agent-security, Property 18: Dual Output Format**
    **Validates: Requirements 7.5**
    
    Test that JSON-only reports can be generated.
    """
    # Create minimal test analysis result
    test_metadata = AnalysisMetadata(
        analysis_id="test_json_only",
        analysis_type="test",
        target="test_target",
        start_time=datetime.now().isoformat(),
        end_time=datetime.now().isoformat(),
        total_packages=1,
        total_findings=1,
        confidence_threshold=0.5,
        osv_enabled=False,
        visual_analysis_enabled=False
    )
    
    test_summary = AnalysisSummary(
        total_packages=1,
        total_findings=1,
        critical_findings=0,
        high_findings=0,
        medium_findings=1,
        low_findings=0,
        ecosystems_analyzed=["npm"],
        finding_types={"vulnerability": 1},
        confidence_distribution={"high": 0, "medium": 1, "low": 0}
    )
    
    analysis_result = AnalysisResult(
        metadata=test_metadata,
        summary=test_summary,
        sbom_data={"packages": []},
        security_findings=[{
            "package": "test-pkg",
            "version": "1.0.0",
            "finding_type": "vulnerability",
            "severity": "medium",
            "confidence": 0.7,
            "evidence": ["Test evidence"],
            "recommendations": ["Test recommendation"],
            "source": "test",
            "timestamp": datetime.now().isoformat()
        }],
        suspicious_activities=[],
        recommendations=["Test recommendation"],
        raw_data=None
    )
    
    from report_generator import create_security_report
    import tempfile
    import os
    import json
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate JSON only
        result_paths = create_security_report(
            analysis_result, 
            output_format="json",
            output_dir=temp_dir
        )
        
        # Property: Only JSON should be generated
        assert "json" in result_paths, "JSON report should be generated"
        assert "html" not in result_paths, "HTML report should not be generated"
        
        # Property: JSON file should exist and be valid
        assert os.path.exists(result_paths["json"]), "JSON file should exist"
        
        with open(result_paths["json"], 'r') as f:
            json_data = json.load(f)
            assert isinstance(json_data, dict), "JSON file should contain valid JSON object"
            assert json_data["analysis_result"]["metadata"]["analysis_id"] == "test_json_only"


def test_html_only_format():
    """
    **Feature: multi-agent-security, Property 18: Dual Output Format**
    **Validates: Requirements 7.5**
    
    Test that HTML-only reports can be generated.
    """
    # Create minimal test analysis result
    test_metadata = AnalysisMetadata(
        analysis_id="test_html_only",
        analysis_type="test",
        target="test_target",
        start_time=datetime.now().isoformat(),
        end_time=datetime.now().isoformat(),
        total_packages=1,
        total_findings=0,
        confidence_threshold=0.5,
        osv_enabled=False,
        visual_analysis_enabled=False
    )
    
    test_summary = AnalysisSummary(
        total_packages=1,
        total_findings=0,
        critical_findings=0,
        high_findings=0,
        medium_findings=0,
        low_findings=0,
        ecosystems_analyzed=["npm"],
        finding_types={},
        confidence_distribution={"high": 0, "medium": 0, "low": 0}
    )
    
    analysis_result = AnalysisResult(
        metadata=test_metadata,
        summary=test_summary,
        sbom_data={"packages": []},
        security_findings=[],
        suspicious_activities=[],
        recommendations=[],
        raw_data=None
    )
    
    from report_generator import create_security_report
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate HTML only
        result_paths = create_security_report(
            analysis_result, 
            output_format="html",
            output_dir=temp_dir
        )
        
        # Property: Only HTML should be generated
        assert "html" in result_paths, "HTML report should be generated"
        assert "json" not in result_paths, "JSON report should not be generated"
        
        # Property: HTML file should exist and be valid
        assert os.path.exists(result_paths["html"]), "HTML file should exist"
        
        with open(result_paths["html"], 'r') as f:
            html_content = f.read()
            assert "<html" in html_content.lower(), "HTML file should contain HTML tags"
            assert "test_html_only" in html_content, "HTML should contain analysis ID"