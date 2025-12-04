"""
Tests for main entry point integration (Task 6).

Validates Requirements 2.1-2.5, 14.1-14.5:
- Rule-based detection integration
- GitHub repo cloning and local directory support
- Input mode auto-detection
- Agent analysis integration
- Performance metrics collection
"""

import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

from analyze_supply_chain import (
    clone_github_repo,
    detect_input_mode,
    detect_ecosystem,
    find_manifest_file,
    RuleBasedDetectionEngine,
    analyze_project_hybrid,
    _generate_simple_report
)
from agents.types import Finding


class TestInputModeDetection:
    """Test input mode auto-detection (Requirement 2.3)."""
    
    def test_detect_github_url_https(self):
        """Test detection of GitHub HTTPS URL."""
        target = "https://github.com/user/repo"
        mode = detect_input_mode(target)
        assert mode == "github"
    
    def test_detect_github_url_http(self):
        """Test detection of GitHub HTTP URL."""
        target = "http://github.com/user/repo"
        mode = detect_input_mode(target)
        assert mode == "github"
    
    def test_detect_github_url_git(self):
        """Test detection of GitHub git URL."""
        target = "git@github.com:user/repo.git"
        mode = detect_input_mode(target)
        assert mode == "github"
    
    def test_detect_local_directory(self, tmp_path):
        """Test detection of local directory."""
        mode = detect_input_mode(str(tmp_path))
        assert mode == "local"
    
    def test_detect_local_file(self, tmp_path):
        """Test detection of local file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        mode = detect_input_mode(str(test_file))
        assert mode == "local"


class TestEcosystemDetection:
    """Test ecosystem detection (Requirement 2.3)."""
    
    def test_detect_npm_ecosystem(self, tmp_path):
        """Test detection of npm ecosystem."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test", "version": "1.0.0"}')
        
        ecosystem = detect_ecosystem(str(tmp_path))
        assert ecosystem == "npm"
    
    def test_detect_python_ecosystem_requirements(self, tmp_path):
        """Test detection of Python ecosystem via requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\n")
        
        ecosystem = detect_ecosystem(str(tmp_path))
        assert ecosystem == "pypi"
    
    def test_detect_python_ecosystem_setup(self, tmp_path):
        """Test detection of Python ecosystem via setup.py."""
        # Create setup.py
        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\nsetup(name='test')")
        
        ecosystem = detect_ecosystem(str(tmp_path))
        assert ecosystem == "pypi"
    
    def test_detect_unknown_ecosystem(self, tmp_path):
        """Test detection when no manifest files present."""
        ecosystem = detect_ecosystem(str(tmp_path))
        assert ecosystem == "unknown"


class TestManifestFileFinding:
    """Test manifest file finding (Requirement 2.3)."""
    
    def test_find_npm_manifest(self, tmp_path):
        """Test finding npm manifest file."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')
        
        manifest = find_manifest_file(str(tmp_path), "npm")
        assert manifest is not None
        assert manifest.endswith("package.json")
    
    def test_find_python_manifest_requirements(self, tmp_path):
        """Test finding Python manifest via requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\n")
        
        manifest = find_manifest_file(str(tmp_path), "pypi")
        assert manifest is not None
        assert manifest.endswith("requirements.txt")
    
    def test_find_python_manifest_setup(self, tmp_path):
        """Test finding Python manifest via setup.py."""
        # Create setup.py
        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\nsetup(name='test')")
        
        manifest = find_manifest_file(str(tmp_path), "pypi")
        assert manifest is not None
        assert manifest.endswith("setup.py")
    
    def test_manifest_not_found(self, tmp_path):
        """Test when manifest file is not found."""
        manifest = find_manifest_file(str(tmp_path), "npm")
        assert manifest is None


class TestRuleBasedDetection:
    """Test rule-based detection engine (Requirements 2.1-2.5)."""
    
    def test_pattern_matching(self):
        """Test pattern matching for suspicious packages (Requirement 2.1)."""
        engine = RuleBasedDetectionEngine()
        
        packages = [
            {"name": "test-package", "version": "1.0.0", "ecosystem": "npm"},
            {"name": "suspicious-eval-pkg", "version": "1.0.0", "ecosystem": "npm"}
        ]
        
        findings = engine._pattern_matching(packages)
        
        # Should detect suspicious patterns
        assert isinstance(findings, list)
        # All findings should be rule-based
        for finding in findings:
            assert finding.detection_method == "rule_based"
    
    def test_typosquatting_detection(self):
        """Test typosquatting detection (Requirement 2.4)."""
        engine = RuleBasedDetectionEngine()
        
        packages = [
            {"name": "reqeusts", "version": "1.0.0", "ecosystem": "pypi"},  # Typo of "requests"
            {"name": "lodahs", "version": "1.0.0", "ecosystem": "npm"}  # Typo of "lodash"
        ]
        
        findings = engine._typosquatting_detection(packages)
        
        # Should detect typosquats
        assert len(findings) > 0
        
        # Check findings structure
        for finding in findings:
            assert finding.finding_type == "typosquat"
            assert finding.detection_method == "rule_based"
            assert finding.confidence > 0.7
            assert "target_package" in finding.evidence
    
    def test_detection_method_tagging(self):
        """Test that all findings are tagged with detection_method (Requirement 2.5)."""
        engine = RuleBasedDetectionEngine()
        
        packages = [
            {"name": "test-package", "version": "1.0.0", "ecosystem": "npm"}
        ]
        
        findings = engine.detect(packages)
        
        # All findings should have detection_method = "rule_based"
        for finding in findings:
            assert finding.detection_method == "rule_based"


class TestSimpleReportGeneration:
    """Test simple report generation without agents."""
    
    def test_generate_simple_report(self):
        """Test generating report without agent analysis."""
        findings = [
            Finding(
                package_name="test-pkg",
                package_version="1.0.0",
                finding_type="vulnerability",
                severity="high",
                description="Test vulnerability",
                detection_method="rule_based",
                confidence=0.9,
                evidence={"cve": "CVE-2023-1234"},
                remediation="Update to version 2.0.0"
            )
        ]
        
        dependency_graph = {
            "name": "root",
            "version": "1.0.0",
            "dependencies": {}
        }
        
        packages = [
            {"name": "test-pkg", "version": "1.0.0", "ecosystem": "npm"}
        ]
        
        report = _generate_simple_report(
            findings,
            dependency_graph,
            packages,
            "local",
            "/test/path",
            "npm"
        )
        
        # Validate report structure
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert "dependency_graph" in report
        assert "recommendations" in report
        
        # Validate metadata
        assert report["metadata"]["analysis_type"] == "local_rule_based"
        assert report["metadata"]["ecosystem"] == "npm"
        assert report["metadata"]["agent_analysis_enabled"] is False
        
        # Validate summary
        assert report["summary"]["total_packages"] == 1
        assert report["summary"]["total_findings"] == 1
        assert report["summary"]["high_findings"] == 1
        
        # Validate security findings
        assert len(report["security_findings"]["packages"]) == 1
        pkg = report["security_findings"]["packages"][0]
        assert pkg["name"] == "test-pkg"
        assert len(pkg["findings"]) == 1


class TestHybridAnalysisIntegration:
    """Test hybrid analysis integration (Requirements 14.1-14.5)."""
    
    def test_analyze_local_npm_project(self, tmp_path):
        """Test analyzing local npm project (Requirement 14.2)."""
        # Create minimal npm project
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "^4.17.21"
            }
        }))
        
        # Run analysis without agents (faster for testing)
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Load and validate report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Validate structure (Requirement 14.3)
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert "dependency_graph" in report
        
        # Validate backward compatibility (Requirement 14.4)
        assert output_path.endswith("demo_ui_comprehensive_report.json")
    
    def test_analyze_local_python_project(self, tmp_path):
        """Test analyzing local Python project (Requirement 14.2)."""
        # Create minimal Python project
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.28.0\n")
        
        # Run analysis without agents
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Load and validate report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Validate ecosystem detection
        assert report["metadata"]["ecosystem"] == "pypi"
    
    def test_performance_metrics_collection(self, tmp_path):
        """Test performance metrics collection (Requirement 14.5)."""
        # Create minimal project
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {}
        }))
        
        # Run analysis
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Load report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Validate performance metrics
        assert "performance_metrics" in report
        assert "total_analysis_time" in report["performance_metrics"]
        assert isinstance(report["performance_metrics"]["total_analysis_time"], (int, float))
        assert report["performance_metrics"]["total_analysis_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
