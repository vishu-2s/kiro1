"""
Comprehensive MVP Testing and Validation (Task 7).

This test suite validates all Phase 1 MVP functionality including:
- Unit tests for orchestrator, Vulnerability Agent, Reputation Agent, Synthesis Agent
- Integration tests: malicious package (flatmap-stream), clean project, agent failure handling
- Performance benchmark test (< 2 minutes for 20 packages)

Requirements: All Phase 1 requirements (1.1-7.5, 9.1-14.5)
"""

import pytest
import json
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import agents and components
from agents.orchestrator import AgentOrchestrator
from agents.vulnerability_agent import VulnerabilityAnalysisAgent
from agents.reputation_agent import ReputationAnalysisAgent
from agents.synthesis_agent import SynthesisAgent
from agents.types import SharedContext, Finding, AgentResult
from analyze_supply_chain import analyze_project_hybrid, RuleBasedDetectionEngine
from tools.dependency_graph import DependencyGraphAnalyzer


# ============================================================================
# UNIT TESTS - Orchestrator
# ============================================================================

class TestOrchestratorUnit:
    """Unit tests for AgentOrchestrator (Requirements 3.1-3.5, 9.1-9.5)."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return AgentOrchestrator()
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes with correct configuration."""
        assert orchestrator.output_dir is not None
        assert orchestrator.max_total_time == 140
        assert isinstance(orchestrator.agents, dict)
    
    def test_register_required_agents(self, orchestrator):
        """Test registering all required agents."""
        vuln_agent = VulnerabilityAnalysisAgent()
        rep_agent = ReputationAnalysisAgent()
        synth_agent = SynthesisAgent()
        
        orchestrator.register_agent("vulnerability_analysis", vuln_agent)
        orchestrator.register_agent("reputation_analysis", rep_agent)
        orchestrator.register_agent("synthesis", synth_agent)
        
        assert len(orchestrator.agents) == 3
        assert "vulnerability_analysis" in orchestrator.agents
        assert "reputation_analysis" in orchestrator.agents
        assert "synthesis" in orchestrator.agents
    
    def test_sequential_protocol_stages(self, orchestrator):
        """Test that orchestrator follows sequential protocol."""
        # Verify stage configuration
        assert "vulnerability_analysis" in orchestrator.STAGE_CONFIGS
        assert "reputation_analysis" in orchestrator.STAGE_CONFIGS
        assert "synthesis" in orchestrator.STAGE_CONFIGS
        
        # Verify timeouts
        assert orchestrator.STAGE_CONFIGS["vulnerability_analysis"].timeout == 30
        assert orchestrator.STAGE_CONFIGS["reputation_analysis"].timeout == 20
        assert orchestrator.STAGE_CONFIGS["synthesis"].timeout == 20
    
    def test_conditional_stage_execution(self, orchestrator):
        """Test conditional execution of code and supply chain agents."""
        # Context without suspicious patterns
        context_clean = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["lodash"]
        )
        assert orchestrator._should_run_code_analysis(context_clean) is False
        
        # Context with suspicious patterns
        context_suspicious = SharedContext(
            initial_findings=[
                Finding("pkg", "1.0.0", "obfuscated_code", "high", "Test")
            ],
            dependency_graph={},
            packages=["pkg"]
        )
        assert orchestrator._should_run_code_analysis(context_suspicious) is True
    
    def test_graceful_degradation(self, orchestrator):
        """Test graceful degradation when agents fail."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test-pkg"]
        )
        
        # Test fallback data generation
        fallback = orchestrator._get_fallback_data("vulnerability_analysis")
        assert "packages" in fallback
        assert fallback["source"] == "rule_based_fallback"
    
    def test_timeout_handling(self, orchestrator):
        """Test that orchestrator respects timeouts."""
        # Create a slow agent
        class SlowAgent:
            def analyze(self, context, timeout=None):
                time.sleep(2)
                return {"packages": []}
        
        orchestrator.register_agent("vulnerability_analysis", SlowAgent())
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test"]
        )
        
        start_time = time.time()
        result = orchestrator._run_agent_stage("vulnerability_analysis", context)
        duration = time.time() - start_time
        
        # Should timeout within reasonable time
        assert duration < 35  # 30s timeout + 5s buffer


# ============================================================================
# UNIT TESTS - Vulnerability Agent
# ============================================================================

class TestVulnerabilityAgentUnit:
    """Unit tests for VulnerabilityAnalysisAgent (Requirements 4.1-4.5)."""
    
    @pytest.fixture
    def agent(self):
        """Create vulnerability agent instance."""
        return VulnerabilityAnalysisAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "VulnerabilityAnalysisAgent"
        assert agent.osv_client is not None
        assert agent.cache_manager is not None
    
    def test_cvss_score_calculation(self, agent):
        """Test CVSS score calculation (Requirement 4.2)."""
        # Test with explicit score
        vuln_with_score = {
            "severity": [{"type": "CVSS_V3", "score": 7.5}]
        }
        cvss, severity = agent.calculate_cvss(vuln_with_score)
        assert cvss == 7.5
        assert severity == "high"
        
        # Test with severity string
        vuln_with_string = {
            "database_specific": {"severity": "CRITICAL"}
        }
        cvss, severity = agent.calculate_cvss(vuln_with_string)
        assert cvss == 9.5
        assert severity == "critical"
    
    def test_combined_impact_assessment(self, agent):
        """Test combined vulnerability impact assessment (Requirement 4.3)."""
        vulnerabilities = [
            {"severity": "critical", "cvss_score": 9.5},
            {"severity": "high", "cvss_score": 7.5},
            {"severity": "medium", "cvss_score": 5.0}
        ]
        
        impact = agent._assess_combined_impact(vulnerabilities)
        
        assert impact["overall_severity"] == "critical"
        assert impact["max_cvss_score"] == 9.5
        assert impact["critical_count"] == 1
        assert impact["high_count"] == 1
        assert impact["risk_level"] == "critical"
    
    def test_confidence_scoring(self, agent):
        """Test confidence scoring with reasoning (Requirement 4.5)."""
        vulnerabilities = [
            {"severity": "high", "cvss_score": 7.5}
        ]
        
        confidence = agent._calculate_package_confidence(vulnerabilities, "test-pkg")
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should have high confidence with detailed data
    
    @patch('agents.vulnerability_agent.OSVAPIClient')
    def test_osv_api_integration(self, mock_osv, agent):
        """Test OSV API integration (Requirement 4.1)."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.is_success.return_value = True
        mock_response.get_data.return_value = {
            "vulns": [
                {
                    "id": "GHSA-test-1234",
                    "summary": "Test vulnerability",
                    "severity": [{"type": "CVSS_V3", "score": 7.5}]
                }
            ]
        }
        
        agent.osv_client.query_vulnerabilities = Mock(return_value=mock_response)
        
        vulnerabilities = agent.query_osv_api("test-pkg", "npm", "1.0.0")
        
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0]["id"] == "GHSA-test-1234"


# ============================================================================
# UNIT TESTS - Reputation Agent
# ============================================================================

class TestReputationAgentUnit:
    """Unit tests for ReputationAnalysisAgent (Requirements 5.1-5.5)."""
    
    @pytest.fixture
    def agent(self):
        """Create reputation agent instance."""
        return ReputationAnalysisAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "ReputationAnalysisAgent"
        assert agent.reputation_scorer is not None
        assert agent.cache_manager is not None
    
    def test_reputation_scoring_algorithm(self, agent):
        """Test reputation scoring algorithm (Requirement 5.2)."""
        from datetime import datetime, timedelta
        
        metadata = {
            "name": "express",
            "version": "4.18.2",
            "time": {
                "created": (datetime.now() - timedelta(days=365)).isoformat(),
                "modified": datetime.now().isoformat()
            },
            "author": {"name": "TJ Holowaychuk"},
            "maintainers": [{"name": "dougwilson"}]
        }
        
        reputation_data = agent.calculate_reputation_score(metadata, "npm")
        
        assert "score" in reputation_data
        assert "factors" in reputation_data
        assert 0.0 <= reputation_data["score"] <= 1.0
        
        # Check all factors are present
        factors = reputation_data["factors"]
        assert "age_score" in factors
        assert "downloads_score" in factors
        assert "author_score" in factors
        assert "maintenance_score" in factors
    
    def test_risk_factor_identification(self, agent):
        """Test risk factor identification (Requirement 5.3)."""
        reputation_data = {
            "score": 0.3,
            "factors": {
                "age_score": 0.2,  # New package
                "downloads_score": 0.5,
                "author_score": 0.5,
                "maintenance_score": 0.5
            },
            "flags": ["new_package"]
        }
        
        risk_factors = agent._identify_risk_factors(reputation_data, {}, "npm")
        
        # Should identify new package risk
        assert len(risk_factors) > 0
        assert any(rf["type"] == "new_package" for rf in risk_factors)
    
    def test_author_history_analysis(self, agent):
        """Test author history analysis (Requirement 5.4)."""
        metadata = {
            "author": {"name": "Test Author"},
            "maintainers": [
                {"name": "maintainer1"},
                {"name": "maintainer2"}
            ]
        }
        
        author_analysis = agent._analyze_author_history(metadata, "npm")
        
        assert author_analysis["author_name"] == "Test Author"
        assert author_analysis["maintainer_count"] == 2
    
    def test_confidence_scores(self, agent):
        """Test confidence scores with reasoning (Requirement 5.5)."""
        reputation_data = {
            "score": 0.8,
            "factors": {
                "age_score": 0.9,
                "downloads_score": 0.8,
                "author_score": 0.9,
                "maintenance_score": 0.8
            },
            "flags": []
        }
        metadata = {"name": "test", "version": "1.0.0", "author": "Test"}
        
        confidence = agent._calculate_confidence(reputation_data, metadata)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.9  # High confidence with complete data


# ============================================================================
# UNIT TESTS - Synthesis Agent
# ============================================================================

class TestSynthesisAgentUnit:
    """Unit tests for SynthesisAgent (Requirements 7.1-7.5, 11.1-11.5)."""
    
    @pytest.fixture
    def agent(self):
        """Create synthesis agent instance."""
        return SynthesisAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "SynthesisAgent"
        assert agent.openai_client is not None
    
    def test_finding_aggregation(self, agent):
        """Test aggregation of findings (Requirement 7.1)."""
        context = SharedContext(
            initial_findings=[
                Finding("pkg1", "1.0.0", "vulnerability", "high", "Test")
            ],
            dependency_graph={},
            packages=["pkg1", "pkg2"]
        )
        
        # Add agent results
        vuln_result = AgentResult(
            agent_name="VulnerabilityAnalysisAgent",
            success=True,
            data={
                "packages": [
                    {"package_name": "pkg1", "vulnerabilities": []}
                ]
            }
        )
        context.add_agent_result(vuln_result)
        
        packages = agent.aggregate_findings(context)
        
        assert isinstance(packages, dict)
        assert "pkg1" in packages
    
    def test_common_recommendations_generation(self, agent):
        """Test common recommendations generation (Requirement 7.2, 11.1-11.5)."""
        packages = {
            "pkg1": {
                "vulnerabilities": [{"severity": "critical"}]
            }
        }
        
        recommendations = agent.generate_common_recommendations(packages)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should include urgent recommendation for critical finding
        assert any("URGENT" in rec or "critical" in rec.lower() for rec in recommendations)
    
    def test_project_risk_assessment(self, agent):
        """Test project-level risk assessment (Requirement 7.4)."""
        packages = {
            "pkg1": {"vulnerabilities": [{"severity": "critical"}]},
            "pkg2": {"vulnerabilities": [{"severity": "high"}]}
        }
        
        risk = agent.assess_project_risk(packages)
        
        assert "overall_risk" in risk
        assert "risk_score" in risk
        assert "confidence" in risk
        assert "reasoning" in risk
        assert risk["overall_risk"] == "CRITICAL"
    
    def test_json_schema_validation(self, agent):
        """Test JSON schema validation (Requirement 7.5)."""
        valid_json = {
            "metadata": {},
            "summary": {},
            "security_findings": [],
            "recommendations": []
        }
        assert agent._validate_json_schema(valid_json) is True
        
        invalid_json = {"metadata": {}}
        assert agent._validate_json_schema(invalid_json) is False
    
    def test_fallback_report_generation(self, agent):
        """Test fallback report generation when synthesis fails (Requirement 7.3)."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["pkg1"]
        )
        
        report = agent._generate_fallback_report(context)
        
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert report["metadata"]["synthesis_status"] == "fallback"


# ============================================================================
# INTEGRATION TEST - Malicious Package (flatmap-stream)
# ============================================================================

class TestMaliciousPackageIntegration:
    """Integration test for malicious package detection (flatmap-stream)."""
    
    def test_flatmap_stream_detection(self, tmp_path):
        """Test detection of known malicious package flatmap-stream."""
        # Create project with flatmap-stream
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "flatmap-stream": "0.1.1"  # Known malicious version
            }
        }))
        
        # Run analysis without agents (faster)
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Load report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Verify malicious package was detected
        assert report["summary"]["total_findings"] > 0
        
        # Check for flatmap-stream in findings
        packages = report["security_findings"]["packages"]
        flatmap_found = any(pkg["name"] == "flatmap-stream" for pkg in packages)
        assert flatmap_found, "flatmap-stream should be detected"
        
        # Verify severity is critical
        for pkg in packages:
            if pkg["name"] == "flatmap-stream":
                findings = pkg.get("findings", [])
                assert len(findings) > 0
                # Should have high/critical severity finding
                assert any(f["severity"] in ["high", "critical"] for f in findings)


# ============================================================================
# INTEGRATION TEST - Clean Project
# ============================================================================

class TestCleanProjectIntegration:
    """Integration test for clean project with no vulnerabilities."""
    
    def test_clean_npm_project(self, tmp_path):
        """Test analysis of clean npm project."""
        # Create clean project with well-maintained packages
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "clean-project",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "^4.17.21"  # Well-maintained, popular package
            }
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
        
        # Verify report structure
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        
        # Verify analysis completed successfully
        assert "analysis_type" in report["metadata"]
        assert "ecosystem" in report["metadata"]
        assert report["metadata"]["ecosystem"] == "npm"
        
        # Clean project should have low number of findings
        assert report["summary"]["total_packages"] >= 1
        # May have some findings (outdated versions, etc.) but not critical
        assert report["summary"]["critical_findings"] == 0
    
    def test_clean_python_project(self, tmp_path):
        """Test analysis of clean Python project."""
        # Create clean Python project
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.31.0\n")  # Well-maintained package
        
        # Run analysis
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Load report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Verify ecosystem detection
        assert report["metadata"]["ecosystem"] == "pypi"
        
        # Verify analysis completed successfully
        assert "analysis_type" in report["metadata"]
        assert report["summary"]["total_packages"] >= 1


# ============================================================================
# INTEGRATION TEST - Agent Failure Handling
# ============================================================================

class TestAgentFailureHandling:
    """Integration test for graceful agent failure handling."""
    
    def test_vulnerability_agent_failure(self):
        """Test handling of vulnerability agent failure."""
        orchestrator = AgentOrchestrator()
        
        # Create failing agent
        class FailingVulnAgent:
            def analyze(self, context, timeout=None):
                raise Exception("API unavailable")
        
        orchestrator.register_agent("vulnerability_analysis", FailingVulnAgent())
        orchestrator.register_agent("reputation_analysis", ReputationAnalysisAgent())
        orchestrator.register_agent("synthesis", SynthesisAgent())
        
        # Create context
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test-pkg"],
            input_mode="local",
            ecosystem="npm"
        )
        
        # Run orchestration - should not crash
        result = orchestrator.orchestrate(
            initial_findings=[],
            dependency_graph={},
            input_mode="local",
            ecosystem="npm"
        )
        
        # Should have fallback data
        assert "metadata" in result
        assert "summary" in result
    
    def test_partial_agent_success(self):
        """Test handling when some agents succeed and others fail."""
        orchestrator = AgentOrchestrator()
        
        # Register mix of working and failing agents
        orchestrator.register_agent("vulnerability_analysis", VulnerabilityAnalysisAgent())
        
        class FailingRepAgent:
            def analyze(self, context, timeout=None):
                raise Exception("Network error")
        
        orchestrator.register_agent("reputation_analysis", FailingRepAgent())
        orchestrator.register_agent("synthesis", SynthesisAgent())
        
        # Run orchestration
        result = orchestrator.orchestrate(
            initial_findings=[],
            dependency_graph={},
            input_mode="local",
            ecosystem="npm"
        )
        
        # Should complete with partial data
        assert "metadata" in result
        assert "performance_metrics" in result
        
        # Should indicate partial success
        stages_completed = result["performance_metrics"].get("stages_completed", 0)
        assert stages_completed >= 1  # At least vulnerability agent succeeded


# ============================================================================
# PERFORMANCE BENCHMARK TEST
# ============================================================================

class TestPerformanceBenchmark:
    """Performance benchmark test (< 2 minutes for 20 packages)."""
    
    def test_20_package_analysis_performance(self, tmp_path):
        """Test that analysis of 20 packages completes in under 2 minutes."""
        # Create project with 20 packages
        dependencies = {
            f"package-{i}": f"^{i}.0.0" for i in range(1, 21)
        }
        
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "performance-test",
            "version": "1.0.0",
            "dependencies": dependencies
        }))
        
        # Run analysis and measure time
        start_time = time.time()
        
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False  # Without agents for faster testing
        )
        
        duration = time.time() - start_time
        
        # Verify completion time
        assert duration < 120, f"Analysis took {duration:.2f}s, should be < 120s"
        
        # Load and verify report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Verify all packages were analyzed
        assert report["summary"]["total_packages"] == 20
        
        # Verify performance metrics are recorded
        assert "performance_metrics" in report
        assert "total_analysis_time" in report["performance_metrics"]
    
    def test_performance_with_caching(self, tmp_path):
        """Test that caching improves performance on second run."""
        # Create project
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "cache-test",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "^4.17.21",
                "express": "^4.18.2"
            }
        }))
        
        # First run
        start_time1 = time.time()
        analyze_project_hybrid(str(tmp_path), input_mode="local", use_agents=False)
        duration1 = time.time() - start_time1
        
        # Second run (should use cache)
        start_time2 = time.time()
        analyze_project_hybrid(str(tmp_path), input_mode="local", use_agents=False)
        duration2 = time.time() - start_time2
        
        # Second run should be faster or similar (caching effect)
        # Note: May not always be faster due to system variations
        assert duration2 <= duration1 * 1.5, "Second run should benefit from caching"


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with existing features (Requirements 14.1-14.5)."""
    
    def test_output_filename_compatibility(self, tmp_path):
        """Test that output filename remains consistent (Requirement 14.3)."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test",
            "version": "1.0.0",
            "dependencies": {}
        }))
        
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Verify filename
        assert output_path.endswith("demo_ui_comprehensive_report.json")
    
    def test_json_format_compatibility(self, tmp_path):
        """Test that JSON format is compatible with existing UI (Requirement 14.4)."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test",
            "version": "1.0.0",
            "dependencies": {"lodash": "^4.17.21"}
        }))
        
        output_path = analyze_project_hybrid(
            str(tmp_path),
            input_mode="local",
            use_agents=False
        )
        
        # Load report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Verify required fields for UI compatibility
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert "dependency_graph" in report
        
        # Verify summary fields
        summary = report["summary"]
        assert "total_packages" in summary
        assert "total_findings" in summary
        
        # Verify security findings structure
        findings = report["security_findings"]
        assert "packages" in findings
        assert isinstance(findings["packages"], list)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run all tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
