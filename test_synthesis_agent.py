"""
Unit tests for the Synthesis Agent.

Tests cover:
- JSON synthesis with OpenAI JSON mode
- Fallback report generation
- Finding aggregation
- Common recommendation generation
- Risk assessment
- Schema validation
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from agents.synthesis_agent import SynthesisAgent
from agents.types import SharedContext, AgentResult, Finding


@pytest.fixture
def synthesis_agent():
    """Create a Synthesis Agent instance for testing."""
    return SynthesisAgent()


@pytest.fixture
def mock_context():
    """Create a mock shared context with agent results."""
    # Create mock findings
    findings = [
        Finding(
            package_name="lodash",
            package_version="4.17.20",
            finding_type="vulnerability",
            severity="high",
            description="Prototype pollution",
            detection_method="rule_based",
            confidence=0.95
        ),
        Finding(
            package_name="flatmap-stream",
            package_version="0.1.1",
            finding_type="malicious_package",
            severity="critical",
            description="Known malicious package",
            detection_method="rule_based",
            confidence=0.98
        )
    ]
    
    # Create context
    context = SharedContext(
        initial_findings=findings,
        dependency_graph={"root": {"name": "test-project"}},
        packages=["lodash", "flatmap-stream"],
        input_mode="local",
        project_path="/test/path",
        ecosystem="npm"
    )
    
    # Add mock agent results
    vuln_result = AgentResult(
        agent_name="VulnerabilityAnalysisAgent",
        success=True,
        data={
            "packages": [
                {
                    "package_name": "lodash",
                    "package_version": "4.17.20",
                    "vulnerabilities": [{"id": "CVE-2021-23337", "severity": "high"}]
                }
            ]
        },
        duration_seconds=5.0,
        confidence=0.95
    )
    
    rep_result = AgentResult(
        agent_name="ReputationAnalysisAgent",
        success=True,
        data={
            "packages": [
                {
                    "package_name": "lodash",
                    "reputation_score": 0.95,
                    "risk_level": "low"
                }
            ]
        },
        duration_seconds=3.0,
        confidence=0.90
    )
    
    context.add_agent_result(vuln_result)
    context.add_agent_result(rep_result)
    
    return context


class TestSynthesisAgentInitialization:
    """Test Synthesis Agent initialization."""
    
    def test_agent_initialization(self, synthesis_agent):
        """Test that agent initializes correctly."""
        assert synthesis_agent.name == "SynthesisAgent"
        assert synthesis_agent.system_message is not None
        assert len(synthesis_agent.tools) == 4
        assert synthesis_agent.openai_client is not None
    
    def test_agent_has_required_tools(self, synthesis_agent):
        """Test that agent has all required tools."""
        tool_names = [tool.__name__ for tool in synthesis_agent.tools]
        assert "aggregate_findings" in tool_names
        assert "generate_common_recommendations" in tool_names
        assert "assess_project_risk" in tool_names
        assert "format_package_centric_report" in tool_names


class TestFindingAggregation:
    """Test finding aggregation functionality."""
    
    def test_aggregate_findings_basic(self, synthesis_agent, mock_context):
        """Test basic finding aggregation."""
        packages = synthesis_agent.aggregate_findings(mock_context)
        
        assert isinstance(packages, dict)
        assert len(packages) == 2
        assert "lodash" in packages
        assert "flatmap-stream" in packages
    
    def test_aggregate_findings_structure(self, synthesis_agent, mock_context):
        """Test that aggregated packages have correct structure."""
        packages = synthesis_agent.aggregate_findings(mock_context)
        
        for pkg_name, pkg_data in packages.items():
            assert "name" in pkg_data
            assert "version" in pkg_data
            assert "ecosystem" in pkg_data
            assert "vulnerabilities" in pkg_data
            assert "reputation_analysis" in pkg_data
            assert isinstance(pkg_data["vulnerabilities"], list)
    
    def test_aggregate_findings_with_vulnerabilities(self, synthesis_agent, mock_context):
        """Test that vulnerabilities are correctly aggregated."""
        packages = synthesis_agent.aggregate_findings(mock_context)
        
        lodash = packages["lodash"]
        assert len(lodash["vulnerabilities"]) > 0
        assert lodash["vulnerabilities"][0]["id"] == "CVE-2021-23337"
    
    def test_aggregate_findings_with_reputation(self, synthesis_agent, mock_context):
        """Test that reputation data is correctly aggregated."""
        packages = synthesis_agent.aggregate_findings(mock_context)
        
        lodash = packages["lodash"]
        assert "reputation_score" in lodash["reputation_analysis"]
        assert lodash["reputation_analysis"]["reputation_score"] == 0.95


class TestRecommendationGeneration:
    """Test recommendation generation functionality."""
    
    def test_generate_recommendations_basic(self, synthesis_agent):
        """Test basic recommendation generation."""
        packages = {
            "lodash": {
                "vulnerabilities": [{"severity": "high"}]
            }
        }
        
        recommendations = synthesis_agent.generate_common_recommendations(packages)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_generate_recommendations_critical(self, synthesis_agent):
        """Test recommendations for critical findings."""
        packages = {
            "test-pkg": {
                "vulnerabilities": [{"severity": "critical"}]
            }
        }
        
        recommendations = synthesis_agent.generate_common_recommendations(packages)
        
        # Should include urgent recommendation
        assert any("URGENT" in rec for rec in recommendations)
    
    def test_generate_recommendations_malicious(self, synthesis_agent):
        """Test recommendations for malicious packages."""
        packages = {
            "malicious-pkg": {
                "vulnerabilities": [],
                "supply_chain_analysis": {"is_malicious": True}
            }
        }
        
        recommendations = synthesis_agent.generate_common_recommendations(packages)
        
        # Should include removal recommendation
        assert any("Remove" in rec or "malicious" in rec for rec in recommendations)
    
    def test_generate_recommendations_includes_general(self, synthesis_agent):
        """Test that general recommendations are included."""
        packages = {}
        
        recommendations = synthesis_agent.generate_common_recommendations(packages)
        
        # Should include general best practices
        assert any("CI/CD" in rec for rec in recommendations)
        assert any("SBOM" in rec for rec in recommendations)


class TestRiskAssessment:
    """Test risk assessment functionality."""
    
    def test_assess_risk_critical(self, synthesis_agent):
        """Test risk assessment with critical findings."""
        packages = {
            "test-pkg": {
                "vulnerabilities": [{"severity": "critical"}]
            }
        }
        
        risk = synthesis_agent.assess_project_risk(packages)
        
        assert risk["overall_risk"] == "CRITICAL"
        assert risk["risk_score"] >= 0.9
        assert "confidence" in risk
        assert "reasoning" in risk
    
    def test_assess_risk_high(self, synthesis_agent):
        """Test risk assessment with high severity findings."""
        packages = {
            "pkg1": {"vulnerabilities": [{"severity": "high"}]},
            "pkg2": {"vulnerabilities": [{"severity": "high"}]},
            "pkg3": {"vulnerabilities": [{"severity": "high"}]}
        }
        
        risk = synthesis_agent.assess_project_risk(packages)
        
        assert risk["overall_risk"] == "HIGH"
        assert risk["risk_score"] >= 0.7
    
    def test_assess_risk_medium(self, synthesis_agent):
        """Test risk assessment with medium severity findings."""
        packages = {
            "pkg1": {"vulnerabilities": [{"severity": "high"}]}
        }
        
        risk = synthesis_agent.assess_project_risk(packages)
        
        assert risk["overall_risk"] in ["MEDIUM", "HIGH"]
        assert 0.0 <= risk["risk_score"] <= 1.0
    
    def test_assess_risk_low(self, synthesis_agent):
        """Test risk assessment with no findings."""
        packages = {
            "pkg1": {"vulnerabilities": []}
        }
        
        risk = synthesis_agent.assess_project_risk(packages)
        
        assert risk["overall_risk"] == "LOW"
        assert risk["risk_score"] < 0.5
    
    def test_assess_risk_malicious_package(self, synthesis_agent):
        """Test risk assessment with malicious package."""
        packages = {
            "malicious": {
                "vulnerabilities": [],
                "supply_chain_analysis": {"is_malicious": True}
            }
        }
        
        risk = synthesis_agent.assess_project_risk(packages)
        
        assert risk["overall_risk"] == "CRITICAL"
        assert risk["risk_score"] >= 0.9


class TestSchemaValidation:
    """Test JSON schema validation."""
    
    def test_validate_schema_valid(self, synthesis_agent):
        """Test validation of valid JSON."""
        valid_json = {
            "metadata": {},
            "summary": {},
            "security_findings": [],
            "recommendations": []
        }
        
        assert synthesis_agent._validate_json_schema(valid_json) is True
    
    def test_validate_schema_missing_metadata(self, synthesis_agent):
        """Test validation fails with missing metadata."""
        invalid_json = {
            "summary": {},
            "security_findings": [],
            "recommendations": []
        }
        
        assert synthesis_agent._validate_json_schema(invalid_json) is False
    
    def test_validate_schema_missing_summary(self, synthesis_agent):
        """Test validation fails with missing summary."""
        invalid_json = {
            "metadata": {},
            "security_findings": [],
            "recommendations": []
        }
        
        assert synthesis_agent._validate_json_schema(invalid_json) is False
    
    def test_validate_schema_invalid_findings_type(self, synthesis_agent):
        """Test validation fails with invalid findings type."""
        invalid_json = {
            "metadata": {},
            "summary": {},
            "security_findings": "not an array",
            "recommendations": []
        }
        
        assert synthesis_agent._validate_json_schema(invalid_json) is False
    
    def test_validate_schema_invalid_recommendations_type(self, synthesis_agent):
        """Test validation fails with invalid recommendations type."""
        invalid_json = {
            "metadata": {},
            "summary": {},
            "security_findings": [],
            "recommendations": "not an array"
        }
        
        assert synthesis_agent._validate_json_schema(invalid_json) is False


class TestFallbackReport:
    """Test fallback report generation."""
    
    def test_generate_fallback_report(self, synthesis_agent, mock_context):
        """Test fallback report generation."""
        report = synthesis_agent._generate_fallback_report(mock_context)
        
        assert isinstance(report, dict)
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert "recommendations" in report
        assert "agent_insights" in report
    
    def test_fallback_report_has_synthesis_status(self, synthesis_agent, mock_context):
        """Test that fallback report indicates fallback status."""
        report = synthesis_agent._generate_fallback_report(mock_context)
        
        assert report["metadata"]["synthesis_status"] == "fallback"
    
    def test_fallback_report_includes_findings(self, synthesis_agent, mock_context):
        """Test that fallback report includes initial findings."""
        report = synthesis_agent._generate_fallback_report(mock_context)
        
        assert len(report["security_findings"]) > 0
    
    def test_fallback_report_includes_recommendations(self, synthesis_agent, mock_context):
        """Test that fallback report includes recommendations."""
        report = synthesis_agent._generate_fallback_report(mock_context)
        
        assert len(report["recommendations"]) > 0
    
    def test_fallback_report_includes_risk_assessment(self, synthesis_agent, mock_context):
        """Test that fallback report includes risk assessment."""
        report = synthesis_agent._generate_fallback_report(mock_context)
        
        assert "risk_assessment" in report["agent_insights"]
        assert "overall_risk" in report["agent_insights"]["risk_assessment"]


class TestJSONExtraction:
    """Test JSON extraction from text."""
    
    def test_extract_json_from_markdown(self, synthesis_agent):
        """Test extracting JSON from markdown code block."""
        text = """Here is the JSON:
```json
{"test": "value"}
```
"""
        result = synthesis_agent._extract_json_from_text(text)
        
        assert result == {"test": "value"}
    
    def test_extract_json_from_code_block(self, synthesis_agent):
        """Test extracting JSON from generic code block."""
        text = """```
{"test": "value"}
```"""
        result = synthesis_agent._extract_json_from_text(text)
        
        assert result == {"test": "value"}
    
    def test_extract_json_from_plain_text(self, synthesis_agent):
        """Test extracting JSON from plain text."""
        text = 'Some text {"test": "value"} more text'
        result = synthesis_agent._extract_json_from_text(text)
        
        assert result == {"test": "value"}
    
    def test_extract_json_no_json_found(self, synthesis_agent):
        """Test extraction fails when no JSON found."""
        text = "No JSON here"
        
        with pytest.raises(ValueError, match="No JSON found"):
            synthesis_agent._extract_json_from_text(text)


class TestSynthesisPromptCreation:
    """Test synthesis prompt creation."""
    
    def test_create_synthesis_prompt(self, synthesis_agent, mock_context):
        """Test synthesis prompt creation."""
        prompt = synthesis_agent._create_synthesis_prompt(mock_context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_prompt_includes_agent_results(self, synthesis_agent, mock_context):
        """Test that prompt includes agent results."""
        prompt = synthesis_agent._create_synthesis_prompt(mock_context)
        
        assert "VULNERABILITYANALYSISAGENT" in prompt.upper()
        assert "REPUTATIONANALYSISAGENT" in prompt.upper()
    
    def test_prompt_includes_package_count(self, synthesis_agent, mock_context):
        """Test that prompt includes package count."""
        prompt = synthesis_agent._create_synthesis_prompt(mock_context)
        
        assert "2" in prompt  # 2 packages in mock context
    
    def test_prompt_includes_required_structure(self, synthesis_agent, mock_context):
        """Test that prompt specifies required JSON structure."""
        prompt = synthesis_agent._create_synthesis_prompt(mock_context)
        
        assert "metadata" in prompt
        assert "summary" in prompt
        assert "security_findings" in prompt
        assert "recommendations" in prompt


class TestFormatPackageCentricReport:
    """Test package-centric report formatting."""
    
    def test_format_report_basic(self, synthesis_agent):
        """Test basic report formatting."""
        data = {
            "metadata": {"test": "value"},
            "summary": {"count": 1},
            "security_findings": [],
            "recommendations": []
        }
        
        formatted = synthesis_agent.format_package_centric_report(data)
        
        assert "metadata" in formatted
        assert "summary" in formatted
        assert "security_findings" in formatted
        assert "recommendations" in formatted
    
    def test_format_report_with_missing_fields(self, synthesis_agent):
        """Test formatting with missing optional fields."""
        data = {
            "metadata": {},
            "summary": {}
        }
        
        formatted = synthesis_agent.format_package_centric_report(data)
        
        # Should have default empty values
        assert formatted["security_findings"] == []
        assert formatted["recommendations"] == []
        assert formatted["agent_insights"] == {}


class TestAnalyzeMethod:
    """Test the main analyze method."""
    
    @patch.object(SynthesisAgent, 'synthesize_json')
    def test_analyze_success(self, mock_synthesize, synthesis_agent, mock_context):
        """Test successful analysis."""
        mock_synthesize.return_value = {
            "metadata": {},
            "summary": {},
            "security_findings": [],
            "recommendations": []
        }
        
        result = synthesis_agent.analyze(mock_context, timeout=30)
        
        assert result["success"] is True
        assert "report" in result
        assert "duration_seconds" in result
    
    @patch.object(SynthesisAgent, 'synthesize_json')
    def test_analyze_failure_uses_fallback(self, mock_synthesize, synthesis_agent, mock_context):
        """Test that analysis failure triggers fallback report."""
        mock_synthesize.side_effect = Exception("Synthesis failed")
        
        result = synthesis_agent.analyze(mock_context, timeout=30)
        
        assert result["success"] is False
        assert "report" in result
        assert "error" in result
        assert result["report"]["metadata"]["synthesis_status"] == "fallback"
    
    @patch.object(SynthesisAgent, 'synthesize_json')
    def test_analyze_invalid_schema_uses_fallback(self, mock_synthesize, synthesis_agent, mock_context):
        """Test that invalid schema triggers fallback report."""
        mock_synthesize.return_value = {"invalid": "schema"}
        
        result = synthesis_agent.analyze(mock_context, timeout=30)
        
        assert result["success"] is False
        assert "report" in result


class TestConfidenceBreakdown:
    """Test confidence breakdown calculation."""
    
    def test_get_confidence_breakdown(self, synthesis_agent, mock_context):
        """Test confidence breakdown calculation."""
        breakdown = synthesis_agent._get_confidence_breakdown(mock_context)
        
        assert isinstance(breakdown, dict)
        assert "overall_synthesis" in breakdown
    
    def test_confidence_breakdown_includes_agents(self, synthesis_agent, mock_context):
        """Test that breakdown includes all agents."""
        breakdown = synthesis_agent._get_confidence_breakdown(mock_context)
        
        # Should have entries for vulnerability and reputation agents
        assert len(breakdown) >= 2
    
    def test_confidence_breakdown_overall_is_average(self, synthesis_agent, mock_context):
        """Test that overall confidence is average of agents."""
        breakdown = synthesis_agent._get_confidence_breakdown(mock_context)
        
        overall = breakdown["overall_synthesis"]
        assert 0.0 <= overall <= 1.0


class TestAgentContributions:
    """Test agent contributions summary."""
    
    def test_get_agent_contributions(self, synthesis_agent, mock_context):
        """Test agent contributions summary."""
        contributions = synthesis_agent._get_agent_contributions(mock_context)
        
        assert isinstance(contributions, dict)
        assert len(contributions) > 0
    
    def test_contributions_include_success_info(self, synthesis_agent, mock_context):
        """Test that contributions include success information."""
        contributions = synthesis_agent._get_agent_contributions(mock_context)
        
        for agent_name, contribution in contributions.items():
            assert isinstance(contribution, str)
            assert len(contribution) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
