"""
Tests for the agent foundation: base classes, orchestrator, and types.

This test file validates the core agent infrastructure including:
- AgentResult and SharedContext data structures
- SecurityAgent base class functionality
- AgentOrchestrator sequential protocol
- Timeout handling and retry logic
- Graceful degradation
"""

import pytest
import time
from agents.types import (
    AgentResult,
    AgentStatus,
    Finding,
    SharedContext,
    AgentConfig
)
from agents.base_agent import SecurityAgent, MockAgent
from agents.orchestrator import AgentOrchestrator


class TestAgentTypes:
    """Test the agent type definitions and data structures."""
    
    def test_agent_result_creation(self):
        """Test creating an AgentResult with success status."""
        result = AgentResult(
            agent_name="test_agent",
            success=True,
            data={"packages": []},
            duration_seconds=1.5
        )
        
        assert result.agent_name == "test_agent"
        assert result.success is True
        assert result.status == AgentStatus.SUCCESS
        assert result.duration_seconds == 1.5
        assert result.error is None
    
    def test_agent_result_failure(self):
        """Test creating an AgentResult with failure status."""
        result = AgentResult(
            agent_name="test_agent",
            success=False,
            data={},
            error="Test error"
        )
        
        assert result.success is False
        assert result.status == AgentStatus.FAILED
        assert result.error == "Test error"
    
    def test_agent_result_timeout(self):
        """Test AgentResult correctly identifies timeout errors."""
        result = AgentResult(
            agent_name="test_agent",
            success=False,
            data={},
            error="Operation timeout after 30 seconds"
        )
        
        assert result.status == AgentStatus.TIMEOUT
    
    def test_agent_result_confidence_bounds(self):
        """Test that confidence scores are bounded to [0.0, 1.0]."""
        result1 = AgentResult(
            agent_name="test",
            success=True,
            data={},
            confidence=1.5  # Should be clamped to 1.0
        )
        assert result1.confidence == 1.0
        
        result2 = AgentResult(
            agent_name="test",
            success=True,
            data={},
            confidence=-0.5  # Should be clamped to 0.0
        )
        assert result2.confidence == 0.0
    
    def test_finding_creation(self):
        """Test creating a Finding object."""
        finding = Finding(
            package_name="lodash",
            package_version="4.17.20",
            finding_type="vulnerability",
            severity="high",
            description="Prototype pollution vulnerability",
            detection_method="rule_based",
            confidence=0.95
        )
        
        assert finding.package_name == "lodash"
        assert finding.severity == "high"
        assert finding.confidence == 0.95
    
    def test_finding_to_dict(self):
        """Test converting Finding to dictionary."""
        finding = Finding(
            package_name="express",
            package_version="4.18.2",
            finding_type="vulnerability",
            severity="medium",
            description="Test vulnerability"
        )
        
        finding_dict = finding.to_dict()
        assert isinstance(finding_dict, dict)
        assert finding_dict["package_name"] == "express"
        assert finding_dict["severity"] == "medium"
    
    def test_shared_context_creation(self):
        """Test creating a SharedContext object."""
        findings = [
            Finding(
                package_name="test-pkg",
                package_version="1.0.0",
                finding_type="vulnerability",
                severity="high",
                description="Test"
            )
        ]
        
        context = SharedContext(
            initial_findings=findings,
            dependency_graph={"root": {}},
            packages=["test-pkg"],
            input_mode="local",
            ecosystem="npm"
        )
        
        assert len(context.initial_findings) == 1
        assert context.packages == ["test-pkg"]
        assert context.input_mode == "local"
    
    def test_shared_context_agent_results(self):
        """Test adding and retrieving agent results from context."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        result = AgentResult(
            agent_name="test_agent",
            success=True,
            data={"packages": []}
        )
        
        context.add_agent_result(result)
        
        assert context.has_successful_result("test_agent")
        retrieved = context.get_agent_result("test_agent")
        assert retrieved is not None
        assert retrieved.agent_name == "test_agent"
    
    def test_agent_config_creation(self):
        """Test creating an AgentConfig object."""
        config = AgentConfig(
            name="vulnerability_analysis",
            timeout=30,
            required=True,
            max_retries=2
        )
        
        assert config.name == "vulnerability_analysis"
        assert config.timeout == 30
        assert config.required is True
        assert config.max_retries == 2


class TestSecurityAgent:
    """Test the SecurityAgent base class."""
    
    def test_agent_initialization(self):
        """Test initializing a SecurityAgent."""
        agent = MockAgent("test_agent")
        
        assert agent.name == "test_agent"
        assert agent.llm_config is not None
        assert "model" in agent.llm_config
        assert "api_key" in agent.llm_config
    
    def test_agent_llm_config_from_env(self):
        """Test that LLM config is loaded from environment."""
        agent = MockAgent("test_agent")
        
        # Should have default values if env vars not set
        assert agent.llm_config["model"] in ["gpt-4o-mini", "gpt-4"]
        assert agent.llm_config["temperature"] >= 0.0
        assert agent.llm_config["max_tokens"] > 0
    
    def test_mock_agent_analyze(self):
        """Test MockAgent returns predefined data."""
        mock_data = {"packages": [{"name": "test", "version": "1.0.0"}]}
        agent = MockAgent("test_agent", mock_data=mock_data)
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test"]
        )
        
        result = agent.analyze(context)
        assert result == mock_data
    
    def test_agent_create_result(self):
        """Test agent can create AgentResult objects."""
        agent = MockAgent("test_agent")
        
        result = agent._create_agent_result(
            success=True,
            data={"packages": []},
            duration=1.0,
            confidence=0.9
        )
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.confidence == 0.9
    
    def test_agent_validate_context(self):
        """Test agent context validation."""
        agent = MockAgent("test_agent")
        
        valid_context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test"]
        )
        assert agent._validate_context(valid_context) is True
        
        invalid_context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]  # Empty packages list
        )
        assert agent._validate_context(invalid_context) is False


class TestAgentOrchestrator:
    """Test the AgentOrchestrator sequential protocol."""
    
    def test_orchestrator_initialization(self):
        """Test initializing the orchestrator."""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.output_dir is not None
        assert orchestrator.max_total_time == 140
        assert len(orchestrator.agents) == 0
    
    def test_register_agent(self):
        """Test registering agents with the orchestrator."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test_agent")
        
        orchestrator.register_agent("vulnerability_analysis", agent)
        
        assert "vulnerability_analysis" in orchestrator.agents
        assert orchestrator.agents["vulnerability_analysis"] == agent
    
    def test_register_invalid_stage(self):
        """Test that registering an invalid stage raises error."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test_agent")
        
        with pytest.raises(ValueError, match="Unknown stage"):
            orchestrator.register_agent("invalid_stage", agent)
    
    def test_extract_packages(self):
        """Test extracting unique packages from findings."""
        orchestrator = AgentOrchestrator()
        
        findings = [
            Finding("pkg1", "1.0.0", "vuln", "high", "Test"),
            Finding("pkg2", "2.0.0", "vuln", "medium", "Test"),
            Finding("pkg1", "1.0.0", "vuln", "low", "Test")  # Duplicate
        ]
        
        packages = orchestrator._extract_packages(findings)
        
        assert len(packages) == 2
        assert "pkg1" in packages
        assert "pkg2" in packages
    
    def test_should_run_code_analysis(self):
        """Test conditional code analysis trigger."""
        orchestrator = AgentOrchestrator()
        
        # Context with suspicious patterns
        context_with_suspicious = SharedContext(
            initial_findings=[
                Finding("pkg1", "1.0.0", "obfuscated_code", "high", "Test")
            ],
            dependency_graph={},
            packages=["pkg1"]
        )
        assert orchestrator._should_run_code_analysis(context_with_suspicious) is True
        
        # Context without suspicious patterns
        context_without_suspicious = SharedContext(
            initial_findings=[
                Finding("pkg1", "1.0.0", "vulnerability", "high", "Test")
            ],
            dependency_graph={},
            packages=["pkg1"]
        )
        assert orchestrator._should_run_code_analysis(context_without_suspicious) is False
    
    def test_should_run_supply_chain_analysis(self):
        """Test conditional supply chain analysis trigger."""
        orchestrator = AgentOrchestrator()
        
        # Context with low reputation package
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["pkg1"]
        )
        
        # Add reputation result with low score
        rep_result = AgentResult(
            agent_name="reputation_analysis",
            success=True,
            data={
                "packages": [
                    {"name": "pkg1", "reputation_score": 0.2}  # Low reputation
                ]
            }
        )
        context.add_agent_result(rep_result)
        
        assert orchestrator._should_run_supply_chain_analysis(context) is True
    
    def test_validate_agent_result(self):
        """Test agent result validation."""
        orchestrator = AgentOrchestrator()
        
        # Valid result
        valid_result = {"packages": []}
        assert orchestrator._validate_agent_result(valid_result) is True
        
        # Invalid result (missing packages key)
        invalid_result = {"data": []}
        assert orchestrator._validate_agent_result(invalid_result) is False
        
        # Invalid result (not a dict)
        assert orchestrator._validate_agent_result("not a dict") is False
    
    def test_validate_json_schema(self):
        """Test final JSON schema validation."""
        orchestrator = AgentOrchestrator()
        
        # Valid JSON
        valid_json = {
            "metadata": {},
            "summary": {},
            "security_findings": {}
        }
        assert orchestrator._validate_json_schema(valid_json) is True
        
        # Invalid JSON (missing required keys)
        invalid_json = {
            "metadata": {}
        }
        assert orchestrator._validate_json_schema(invalid_json) is False
    
    def test_get_fallback_data(self):
        """Test fallback data generation (now in error handler)."""
        orchestrator = AgentOrchestrator()
        
        # Test that error handler is initialized
        assert orchestrator.error_handler is not None
        
        # Test fallback data through error handler
        vuln_fallback = orchestrator.error_handler._get_fallback_data("vulnerability_analysis")
        assert "packages" in vuln_fallback
        assert vuln_fallback["source"] == "rule_based_fallback"
        
        rep_fallback = orchestrator.error_handler._get_fallback_data("reputation_analysis")
        assert "packages" in rep_fallback
        assert rep_fallback["source"] == "default_scores"
    
    def test_generate_fallback_report(self):
        """Test fallback report generation (now in error handler)."""
        orchestrator = AgentOrchestrator()
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["pkg1", "pkg2"]
        )
        
        # Test through error handler
        error = Exception("Synthesis failed")
        report = orchestrator.error_handler.handle_synthesis_failure(context, error)
        
        assert "metadata" in report
        assert "summary" in report
        assert "security_findings" in report
        assert report["metadata"]["analysis_status"] == "degraded"
        assert report["summary"]["total_packages"] == 2
    
    def test_orchestrate_with_mock_agents(self):
        """Test full orchestration with mock agents."""
        orchestrator = AgentOrchestrator()
        
        # Register mock agents for required stages
        vuln_agent = MockAgent("vuln", {"packages": [{"name": "test", "vulnerabilities": []}]})
        rep_agent = MockAgent("rep", {"packages": [{"name": "test", "reputation_score": 0.8}]})
        synth_agent = MockAgent("synth", {
            "metadata": {"analysis_id": "test"},
            "summary": {"total_packages": 1},
            "security_findings": {"packages": []}
        })
        
        orchestrator.register_agent("vulnerability_analysis", vuln_agent)
        orchestrator.register_agent("reputation_analysis", rep_agent)
        orchestrator.register_agent("synthesis", synth_agent)
        
        # Run orchestration
        findings = [Finding("test", "1.0.0", "vulnerability", "high", "Test")]
        result = orchestrator.orchestrate(
            initial_findings=findings,
            dependency_graph={"root": {}},
            input_mode="local",
            ecosystem="npm"
        )
        
        assert "metadata" in result
        assert "performance_metrics" in result
        assert result["performance_metrics"]["stages_completed"] >= 2


class TestRetryLogic:
    """Test retry logic and exponential backoff."""
    
    def test_retry_with_eventual_success(self):
        """Test that retry logic works when agent eventually succeeds."""
        orchestrator = AgentOrchestrator()
        
        # Create an agent that fails first time, succeeds second time
        class FlakeyAgent(SecurityAgent):
            def __init__(self):
                super().__init__("flakey", "Test agent", [])
                self.attempt_count = 0
            
            def analyze(self, context, timeout=None):
                self.attempt_count += 1
                if self.attempt_count == 1:
                    raise Exception("First attempt fails")
                return {"packages": []}
        
        agent = FlakeyAgent()
        orchestrator.register_agent("vulnerability_analysis", agent)
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test"]
        )
        
        result = orchestrator._run_agent_stage("vulnerability_analysis", context)
        
        # Should succeed on second attempt
        assert result.success is True
        assert agent.attempt_count == 2
    
    def test_retry_exhaustion(self):
        """Test that retry logic gives up after max retries."""
        orchestrator = AgentOrchestrator()
        
        # Create an agent that always fails
        class FailingAgent(SecurityAgent):
            def __init__(self):
                super().__init__("failing", "Test agent", [])
                self.attempt_count = 0
            
            def analyze(self, context, timeout=None):
                self.attempt_count += 1
                raise Exception("Always fails")
        
        agent = FailingAgent()
        orchestrator.register_agent("vulnerability_analysis", agent)
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["test"]
        )
        
        result = orchestrator._run_agent_stage("vulnerability_analysis", context)
        
        # Should fail after max retries (3 attempts total: 1 initial + 2 retries)
        assert result.success is False
        assert agent.attempt_count == 3
        assert "fallback" in result.data.get("source", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
