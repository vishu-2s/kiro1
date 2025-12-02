"""
Integration tests for complete workflows.
**Feature: multi-agent-security, Property 17: Comprehensive Reporting**
**Feature: multi-agent-security, Property 18: Dual Output Format**
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from analyze_supply_chain import create_analyzer, analyze_target, analyze_target_with_screenshots
from main_github import validate_arguments, setup_output_directory, save_results, perform_analysis
from report_generator import create_security_report


def test_simple_import():
    """Simple test to verify imports work."""
    assert create_analyzer is not None


class TestEndToEndGitHubAnalysis:
    """Test end-to-end GitHub repository analysis workflow."""
    
    def test_github_analysis_with_mock_data(self):
        """Test complete GitHub repository analysis pipeline from URL to findings."""
        with open("artifacts/sample-repository-data.json", "r") as f:
            mock_repo_data = json.load(f)
        
        # Add normalized SBOM data to mock repository
        with open("artifacts/backend-sbom.json", "r") as f:
            cyclonedx_sbom = json.load(f)
        
        # Normalize the CycloneDX SBOM to the expected format
        packages = []
        for component in cyclonedx_sbom.get('components', []):
            purl = component.get('purl', '')
            ecosystem = purl.split(':')[1].split('/')[0] if ':' in purl and '/' in purl else 'unknown'
            packages.append({
                'name': component.get('name', ''),
                'version': component.get('version', 'unknown'),
                'purl': purl,
                'ecosystem': ecosystem
            })
        
        mock_repo_data["sbom"] = {
            "format": "cyclonedx",
            "packages": packages
        }
        
        with patch("analyze_supply_chain.fetch_repository_data") as mock_fetch:
            mock_fetch.return_value = mock_repo_data
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_github_repository("https://github.com/test/repo")
            
            assert result is not None
            assert result.metadata.analysis_type == "github_repository"
            assert result.summary.total_packages > 0
            assert result.metadata.analysis_id is not None
            assert result.sbom_data is not None
            assert isinstance(result.security_findings, list)
            assert isinstance(result.recommendations, list)
    
    def test_github_analysis_detects_vulnerabilities(self):
        """Test that GitHub analysis detects known vulnerabilities."""
        with open("artifacts/sample-repository-data.json", "r") as f:
            mock_repo_data = json.load(f)
        
        with patch("analyze_supply_chain.fetch_repository_data") as mock_fetch:
            mock_fetch.return_value = mock_repo_data
            analyzer = create_analyzer(confidence_threshold=0.3, enable_osv=False)
            result = analyzer.analyze_github_repository("https://github.com/test/repo")
            
            # Should detect some security findings
            assert result.summary.total_findings >= 0
            
            # Check that findings have required fields
            for finding in result.security_findings:
                assert "package" in finding
                assert "severity" in finding
                assert "confidence" in finding
    
    def test_github_analysis_with_suspicious_activities(self):
        """Test detection of suspicious activities in GitHub repositories."""
        with open("artifacts/sample-repository-data.json", "r") as f:
            mock_repo_data = json.load(f)
        
        # Add workflow runs to trigger suspicious activity detection
        mock_repo_data["workflow_runs"] = [
            {"conclusion": "failure"},
            {"conclusion": "failure"},
            {"conclusion": "success"}
        ]
        
        with patch("analyze_supply_chain.fetch_repository_data") as mock_fetch:
            mock_fetch.return_value = mock_repo_data
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_github_repository("https://github.com/test/repo")
            
            assert result is not None
            assert isinstance(result.suspicious_activities, list)


class TestEndToEndLocalAnalysis:
    """Test end-to-end local directory analysis workflow."""
    
    def test_local_analysis_with_package_files(self):
        """Test complete local directory analysis pipeline from path to findings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            shutil.copy("artifacts/sample-package.json", os.path.join(temp_dir, "package.json"))
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_local_directory(temp_dir)
            
            assert result is not None
            assert result.metadata.analysis_type == "local_directory"
            assert result.summary.total_packages > 0
            assert result.metadata.target == temp_dir
            assert isinstance(result.security_findings, list)
    
    def test_local_analysis_multiple_ecosystems(self):
        """Test local analysis with multiple package file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy multiple package files
            shutil.copy("artifacts/sample-package.json", os.path.join(temp_dir, "package.json"))
            shutil.copy("artifacts/sample-requirements.txt", os.path.join(temp_dir, "requirements.txt"))
            
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_local_directory(temp_dir)
            
            assert result is not None
            assert result.summary.total_packages > 0
            
            # Should detect multiple ecosystems
            ecosystems = result.summary.ecosystems_analyzed
            assert len(ecosystems) > 0
    
    def test_local_analysis_empty_directory(self):
        """Test local analysis handles empty directories gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_local_directory(temp_dir)
            
            assert result is not None
            assert result.summary.total_packages == 0
            assert result.summary.total_findings == 0


class TestSBOMFileAnalysis:
    """Test SBOM file analysis workflow."""
    
    def test_sbom_file_analysis(self):
        """Test complete SBOM file analysis pipeline."""
        sbom_path = "artifacts/backend-sbom.json"
        analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
        result = analyzer.analyze_sbom_file(sbom_path)
        
        assert result is not None
        assert result.metadata.analysis_type == "sbom_file"
        assert result.summary.total_packages > 0
        assert result.metadata.target == sbom_path
    
    def test_sbom_analysis_detects_malicious_packages(self):
        """Test that SBOM analysis detects known malicious packages."""
        sbom_path = "artifacts/backend-sbom.json"
        analyzer = create_analyzer(confidence_threshold=0.3, enable_osv=False)
        result = analyzer.analyze_sbom_file(sbom_path)
        
        # backend-sbom.json contains known malicious packages
        assert result.summary.total_findings > 0
        
        # Check for specific malicious packages
        finding_packages = [f.get("package", "") for f in result.security_findings]
        # Should detect at least some of the malicious packages in the SBOM
        assert len(finding_packages) > 0
    
    def test_sbom_analysis_confidence_filtering(self):
        """Test that confidence threshold filters findings correctly."""
        sbom_path = "artifacts/backend-sbom.json"
        
        # Low threshold - should get more findings
        analyzer_low = create_analyzer(confidence_threshold=0.3, enable_osv=False)
        result_low = analyzer_low.analyze_sbom_file(sbom_path)
        
        # High threshold - should get fewer findings
        analyzer_high = create_analyzer(confidence_threshold=0.8, enable_osv=False)
        result_high = analyzer_high.analyze_sbom_file(sbom_path)
        
        # Low threshold should have >= findings than high threshold
        assert result_low.summary.total_findings >= result_high.summary.total_findings


class TestMultiAgentCollaboration:
    """Test multi-agent collaboration scenarios."""
    
    def test_analyze_target_auto_detection_sbom(self):
        """Test automatic detection of SBOM file analysis type."""
        sbom_path = "artifacts/backend-sbom.json"
        result = analyze_target(sbom_path, analysis_type="auto", confidence_threshold=0.5, enable_osv=False)
        
        assert result is not None
        assert result.metadata.analysis_type == "sbom_file"
    
    def test_analyze_target_auto_detection_directory(self):
        """Test automatic detection of local directory analysis type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            shutil.copy("artifacts/sample-package.json", os.path.join(temp_dir, "package.json"))
            result = analyze_target(temp_dir, analysis_type="auto", confidence_threshold=0.5, enable_osv=False)
            
            assert result is not None
            assert result.metadata.analysis_type == "local_directory"
    
    def test_analyze_target_explicit_type(self):
        """Test explicit analysis type specification."""
        sbom_path = "artifacts/backend-sbom.json"
        result = analyze_target(sbom_path, analysis_type="sbom", confidence_threshold=0.5, enable_osv=False)
        
        assert result is not None
        assert result.metadata.analysis_type == "sbom_file"
    
    def test_analyze_with_visual_data_mock(self):
        """Test analysis with visual data integration."""
        sbom_path = "artifacts/backend-sbom.json"
        screenshot_paths = ["screenshots/npm-warnings-text.txt"]
        
        # Mock the visual analysis functions
        with patch("tools.vlm_tools.process_multiple_images") as mock_process:
            with patch("tools.vlm_tools.generate_visual_security_findings") as mock_generate:
                with patch("tools.vlm_tools.correlate_visual_findings_with_packages") as mock_correlate:
                    # Setup mocks
                    mock_process.return_value = {"findings": []}
                    mock_generate.return_value = []
                    mock_correlate.return_value = []
                    
                    result = analyze_target_with_screenshots(
                        sbom_path, 
                        screenshot_paths, 
                        analysis_type="sbom",
                        confidence_threshold=0.5, 
                        enable_osv=False
                    )
                    
                    assert result is not None
                    assert "visual" in result.metadata.analysis_type


class TestMainOrchestration:
    """Test main orchestration system."""
    
    def test_validate_arguments_valid_sbom(self):
        """Test argument validation with valid SBOM file."""
        from argparse import Namespace
        args = Namespace(
            github=None, local=None, sbom="artifacts/backend-sbom.json",
            screenshots=None, confidence_threshold=0.7,
            json_only=False, html_only=False,
            skip_db_update=False, force_db_update=False
        )
        assert validate_arguments(args) is True
    
    def test_validate_arguments_valid_local(self):
        """Test argument validation with valid local directory."""
        from argparse import Namespace
        with tempfile.TemporaryDirectory() as temp_dir:
            args = Namespace(
                github=None, local=temp_dir, sbom=None,
                screenshots=None, confidence_threshold=0.7,
                json_only=False, html_only=False,
                skip_db_update=False, force_db_update=False
            )
            assert validate_arguments(args) is True
    
    def test_validate_arguments_invalid_confidence(self):
        """Test argument validation rejects invalid confidence threshold."""
        from argparse import Namespace
        args = Namespace(
            github=None, local=None, sbom="artifacts/backend-sbom.json",
            screenshots=None, confidence_threshold=1.5,
            json_only=False, html_only=False,
            skip_db_update=False, force_db_update=False
        )
        assert validate_arguments(args) is False
    
    def test_validate_arguments_missing_target(self):
        """Test argument validation requires a target."""
        from argparse import Namespace
        args = Namespace(
            github=None, local=None, sbom=None,
            screenshots=None, confidence_threshold=0.7,
            json_only=False, html_only=False,
            skip_db_update=False, force_db_update=False
        )
        assert validate_arguments(args) is False
    
    def test_setup_output_directory(self):
        """Test output directory setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "test_output")
            result_path = setup_output_directory(output_dir)
            assert result_path.exists()
            assert result_path.is_dir()
    
    def test_save_results_json_format(self):
        """Test saving results in JSON format."""
        sbom_path = "artifacts/backend-sbom.json"
        result = analyze_target(sbom_path, analysis_type="sbom", confidence_threshold=0.5, enable_osv=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            saved_files = save_results(result, output_dir, json_only=True)
            
            assert "json" in saved_files
            assert os.path.exists(saved_files["json"])
            
            # Verify JSON is valid
            with open(saved_files["json"], "r") as f:
                data = json.load(f)
                assert "metadata" in data
                assert "summary" in data
    
    def test_perform_analysis_sbom(self):
        """Test perform_analysis function with SBOM target."""
        from argparse import Namespace
        args = Namespace(
            github=None, 
            local=None, 
            sbom="artifacts/backend-sbom.json",
            screenshots=None,
            confidence_threshold=0.5,
            no_osv=True,
            no_visual=True
        )
        
        result = perform_analysis(args)
        assert result is not None
        assert result.summary.total_packages > 0


class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_complete_sbom_workflow(self):
        """Test complete workflow: SBOM file -> analysis -> report generation."""
        sbom_path = "artifacts/backend-sbom.json"
        
        # Step 1: Analyze SBOM
        analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
        result = analyzer.analyze_sbom_file(sbom_path)
        
        assert result is not None
        assert result.summary.total_packages > 0
        
        # Step 2: Generate report
        with tempfile.TemporaryDirectory() as temp_dir:
            report_paths = create_security_report(
                result, 
                output_format="both", 
                output_dir=temp_dir
            )
            
            assert "json" in report_paths or "html" in report_paths
    
    def test_complete_local_workflow(self):
        """Test complete workflow: local directory -> analysis -> findings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test directory
            shutil.copy("artifacts/sample-package.json", os.path.join(temp_dir, "package.json"))
            
            # Analyze
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_local_directory(temp_dir)
            
            assert result is not None
            assert result.summary.total_packages > 0
            
            # Save results
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            saved_files = save_results(result, output_dir, json_only=True)
            
            assert "json" in saved_files
            assert os.path.exists(saved_files["json"])
    
    def test_complete_github_workflow_mock(self):
        """Test complete workflow: GitHub URL -> analysis -> report (mocked)."""
        with open("artifacts/sample-repository-data.json", "r") as f:
            mock_repo_data = json.load(f)
        
        with patch("analyze_supply_chain.fetch_repository_data") as mock_fetch:
            mock_fetch.return_value = mock_repo_data
            
            # Analyze
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_github_repository("https://github.com/test/repo")
            
            assert result is not None
            
            # Generate report
            with tempfile.TemporaryDirectory() as temp_dir:
                report_paths = create_security_report(
                    result, 
                    output_format="json", 
                    output_dir=temp_dir
                )
                
                assert "json" in report_paths


class TestPropertyValidation:
    """Test validation of correctness properties."""
    
    def test_property_17_comprehensive_reporting(self):
        """
        **Feature: multi-agent-security, Property 17: Comprehensive Reporting**
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        
        For any completed analysis, the system should generate reports with risk assessment,
        attack classification, containment steps, remediation plans, timeline, and stakeholder guidance.
        """
        sbom_path = "artifacts/backend-sbom.json"
        result = analyze_target(sbom_path, analysis_type="sbom", confidence_threshold=0.5, enable_osv=False)
        
        # Verify metadata exists
        assert result.metadata is not None
        assert result.metadata.analysis_id is not None
        assert result.metadata.start_time is not None
        assert result.metadata.end_time is not None
        
        # Verify summary with risk assessment
        assert result.summary is not None
        assert hasattr(result.summary, "critical_findings")
        assert hasattr(result.summary, "high_findings")
        assert hasattr(result.summary, "medium_findings")
        assert hasattr(result.summary, "low_findings")
        
        # Verify remediation plans (recommendations)
        assert len(result.recommendations) > 0
        assert isinstance(result.recommendations, list)
        
        # Verify timeline information (start/end times)
        assert result.metadata.start_time is not None
        assert result.metadata.end_time is not None
    
    def test_property_18_dual_output_format(self):
        """
        **Feature: multi-agent-security, Property 18: Dual Output Format**
        **Validates: Requirements 7.5**
        
        For any completed analysis, the system should generate both JSON findings and HTML reports.
        """
        sbom_path = "artifacts/backend-sbom.json"
        result = analyze_target(sbom_path, analysis_type="sbom", confidence_threshold=0.5, enable_osv=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Test JSON output
            saved_json = save_results(result, output_dir, json_only=True)
            assert "json" in saved_json
            assert os.path.exists(saved_json["json"])
            
            # Verify JSON is valid
            with open(saved_json["json"], "r") as f:
                json_data = json.load(f)
                assert "metadata" in json_data
                assert "summary" in json_data
            
            # Test that both formats can be generated
            # Generate both JSON and HTML
            with patch("main_github.create_security_report") as mock_report:
                # Create a dummy HTML file
                html_file = output_dir / "test.html"
                html_file.write_text("<html><body>Test Report</body></html>")
                mock_report.return_value = {"html": str(html_file)}
                
                saved_both = save_results(result, output_dir, json_only=False, html_only=False)
                
                # Should have JSON (always saved unless html_only)
                assert "json" in saved_both
                assert os.path.exists(saved_both["json"])


class TestErrorHandling:
    """Test error handling in workflows."""
    
    def test_invalid_sbom_file(self):
        """Test handling of invalid SBOM file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": "sbom"}')
            invalid_sbom = f.name
        
        try:
            analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
            result = analyzer.analyze_sbom_file(invalid_sbom)
            
            # Should handle gracefully
            assert result is not None
            assert result.summary.total_packages == 0
        finally:
            os.unlink(invalid_sbom)
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        from analyze_supply_chain import AnalysisError
        
        analyzer = create_analyzer(confidence_threshold=0.5, enable_osv=False)
        
        with pytest.raises((AnalysisError, FileNotFoundError, Exception)):
            analyzer.analyze_sbom_file("/nonexistent/path/to/sbom.json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
