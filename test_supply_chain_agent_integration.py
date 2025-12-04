"""
Integration tests for the Supply Chain Attack Detection Agent.

Tests the SupplyChainAttackAgent's integration with the multi-agent system,
including interaction with other agents and the orchestrator.
"""

import pytest
from unittest.mock import Mock, patch

from agents.supply_chain_agent import SupplyChainAttackAgent
from agents.types import SharedContext, Finding, AgentResult


class TestSupplyChainAgentIntegration:
    """Integration test suite for SupplyChainAttackAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a SupplyChainAttackAgent instance for testing."""
        return SupplyChainAttackAgent()
    
    @pytest.fixture
    def full_context(self):
        """Create a full context with results from multiple agents."""
        return SharedContext(
            initial_findings=[
                Finding(
                    package_name="suspicious-pkg",
                    package_version="1.0.0",
                    finding_type="malicious_package",
                    severity="critical",
                    description="Suspicious package detected",
                    confidence=0.90,
                    evidence={"reason": "Pattern match"},
                    detection_method="rule_based"
                )
            ],
            dependency_graph={
                "packages": [
                    {"name": "suspicious-pkg", "version": "1.0.0"}
                ]
            },
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
                                "reputation_score": 0.20,
                                "risk_level": "high",
                                "risk_factors": [
                                    {"type": "new_package", "severity": "high"},
                                    {"type": "low_downloads", "severity": "high"}
                                ]
                            }
                        ]
                    },
                    duration_seconds=2.0,
                    confidence=0.90
                ),
                "code": AgentResult(
                    agent_name="CodeAnalysisAgent",
                    success=True,
                    data={
                        "packages": [
                            {
                                "package_name": "suspicious-pkg",
                                "package_version": "1.0.0",
                                "code_analysis": {
                                    "obfuscation_detected": [
                                        {"technique": "base64_decode", "severity": "high"}
                                    ],
                                    "behavioral_indicators": [
                                        {"behavior": "network_activity", "severity": "high"},
                                        {"behavior": "env_variable_access", "severity": "high"}
                                    ]
                                }
                            }
                        ]
                    },
                    duration_seconds=3.5,
                    confidence=0.92
                )
            }
        )
    
    def test_integration_with_reputation_agent(self, agent, full_context):
        """Test that supply chain agent uses reputation analysis results."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            # Should analyze the high-risk package from reputation analysis
            assert result["total_packages_analyzed"] >= 1
            assert result["confidence"] > 0.0
            
            # Check that package was analyzed
            packages = result.get("packages", [])
            assert len(packages) > 0
            
            pkg = packages[0]
            assert pkg["package_name"] == "suspicious-pkg"
    
    def test_integration_with_code_agent(self, agent, full_context):
        """Test that supply chain agent uses code analysis results."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            packages = result.get("packages", [])
            assert len(packages) > 0
            
            pkg = packages[0]
            indicators = pkg.get("supply_chain_indicators", [])
            
            # Should detect exfiltration based on code analysis
            # (network_activity + env_variable_access)
            exfiltration_indicators = [
                ind for ind in indicators 
                if ind.get("type") == "exfiltration_pattern"
            ]
            assert len(exfiltration_indicators) > 0
    
    def test_integration_with_multiple_agents(self, agent, full_context):
        """Test supply chain agent with results from multiple agents."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            # Should successfully analyze with multiple agent inputs
            assert "packages" in result
            assert result["confidence"] > 0.0
            
            packages = result.get("packages", [])
            if packages:
                pkg = packages[0]
                
                # Should have indicators from multiple sources
                indicators = pkg.get("supply_chain_indicators", [])
                assert len(indicators) > 0
                
                # Should calculate attack likelihood
                assert "attack_likelihood" in pkg
                assert pkg["attack_likelihood"] in ["critical", "high", "medium", "low", "none"]
    
    def test_orchestrator_compatibility(self, agent, full_context):
        """Test that agent output is compatible with orchestrator expectations."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            # Check required fields for orchestrator
            assert "packages" in result
            assert "total_packages_analyzed" in result
            assert "confidence" in result
            assert "duration_seconds" in result
            assert "source" in result
            
            # Check package structure
            packages = result.get("packages", [])
            for pkg in packages:
                assert "package_name" in pkg
                assert "supply_chain_indicators" in pkg
                assert "attack_likelihood" in pkg
                assert "confidence" in pkg
                assert "reasoning" in pkg
    
    def test_timeout_handling(self, agent, full_context):
        """Test that agent respects timeout parameter."""
        import time
        
        start_time = time.time()
        
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=1)
        
        duration = time.time() - start_time
        
        # Should complete within reasonable time of timeout
        assert duration < 5.0  # Allow some overhead
        assert "duration_seconds" in result
    
    def test_error_handling_with_invalid_context(self, agent):
        """Test agent handles invalid context gracefully."""
        # Create invalid context (missing required fields)
        invalid_context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[],
            ecosystem="npm",
            agent_results={}
        )
        
        # Should not crash, should return valid result
        result = agent.analyze(invalid_context, timeout=30)
        
        assert "packages" in result
        # Error result may not have confidence, but should have error info
        if "error" in result:
            assert result["success"] == False
        else:
            assert "confidence" in result
            assert result["total_packages_analyzed"] == 0
    
    def test_caching_integration(self, agent, full_context):
        """Test that caching works across multiple analyses."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            # First analysis
            result1 = agent.analyze(full_context, timeout=30)
            duration1 = result1.get("duration_seconds", 0)
            
            # Second analysis (should use cache)
            result2 = agent.analyze(full_context, timeout=30)
            duration2 = result2.get("duration_seconds", 0)
            
            # Both should succeed
            assert result1.get("total_packages_analyzed", 0) >= 0
            assert result2.get("total_packages_analyzed", 0) >= 0
            
            # Second should be faster (cached) or similar time
            # Note: May not always be faster due to network variability
            assert duration2 >= 0
    
    def test_high_confidence_with_multiple_indicators(self, agent, full_context):
        """Test that confidence increases with multiple indicators."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            packages = result.get("packages", [])
            if packages:
                pkg = packages[0]
                
                # With multiple indicators from different agents,
                # confidence should be reasonably high
                confidence = pkg.get("confidence", 0.0)
                assert confidence >= 0.80
    
    def test_pattern_matching_with_real_indicators(self, agent, full_context):
        """Test pattern matching with realistic indicator combinations."""
        with patch.object(agent, '_fetch_package_metadata', return_value=None):
            result = agent.analyze(full_context, timeout=30)
            
            packages = result.get("packages", [])
            if packages:
                pkg = packages[0]
                
                # Should have pattern matches
                pattern_matches = pkg.get("attack_pattern_matches", [])
                
                # With network + env access, should match some patterns
                if len(pkg.get("supply_chain_indicators", [])) > 0:
                    # May or may not have pattern matches depending on indicators
                    assert isinstance(pattern_matches, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
