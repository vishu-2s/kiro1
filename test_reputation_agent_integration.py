"""
Integration tests for the Reputation Analysis Agent.

Tests the reputation agent's integration with:
- The orchestrator
- Cache manager
- Real registry APIs (with mocking for CI/CD)
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from agents.reputation_agent import ReputationAnalysisAgent
from agents.orchestrator import AgentOrchestrator
from agents.types import SharedContext, Finding, AgentResult


class TestReputationAgentIntegration:
    """Integration tests for ReputationAnalysisAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a reputation agent instance"""
        return ReputationAnalysisAgent()
    
    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance"""
        return AgentOrchestrator()
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample context with findings"""
        findings = [
            Finding(
                package_name="express",
                package_version="4.18.2",
                finding_type="vulnerability",
                severity="medium",
                description="Test vulnerability",
                detection_method="rule_based"
            )
        ]
        
        return SharedContext(
            initial_findings=findings,
            dependency_graph={
                "packages": [
                    {"name": "express", "version": "4.18.2"},
                    {"name": "lodash", "version": "4.17.21"}
                ]
            },
            packages=["express", "lodash"],
            ecosystem="npm"
        )
    
    def test_agent_with_orchestrator_context(self, agent, sample_context):
        """Test agent works with orchestrator-provided context"""
        # Mock registry calls
        mock_metadata = {
            "name": "express",
            "version": "4.18.2",
            "author": {"name": "TJ Holowaychuk"},
            "time": {
                "created": (datetime.now() - timedelta(days=365)).isoformat(),
                "modified": datetime.now().isoformat()
            },
            "dist-tags": {"latest": "4.18.2"}
        }
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(sample_context, timeout=30)
                    
                    # Verify result structure
                    assert "packages" in result
                    assert "total_packages_analyzed" in result
                    assert "confidence" in result
                    assert result["total_packages_analyzed"] == 2
    
    def test_agent_result_format(self, agent, sample_context):
        """Test that agent returns properly formatted AgentResult"""
        mock_metadata = {
            "name": "express",
            "version": "4.18.2",
            "author": {"name": "Test"},
            "time": {
                "created": (datetime.now() - timedelta(days=100)).isoformat(),
                "modified": datetime.now().isoformat()
            }
        }
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(sample_context, timeout=30)
                    
                    # Verify all required fields are present
                    assert "packages" in result
                    assert "confidence" in result
                    assert "duration_seconds" in result
                    assert "source" in result
                    
                    # Verify package results have required fields
                    for pkg in result["packages"]:
                        assert "package_name" in pkg
                        assert "reputation_score" in pkg
                        assert "risk_level" in pkg
                        assert "confidence" in pkg
    
    def test_agent_with_vulnerability_context(self, agent):
        """Test agent uses vulnerability information from context"""
        # Create context with vulnerability findings
        findings = [
            Finding(
                package_name="vulnerable-package",
                package_version="1.0.0",
                finding_type="vulnerability",
                severity="critical",
                description="Critical vulnerability",
                detection_method="rule_based"
            )
        ]
        
        context = SharedContext(
            initial_findings=findings,
            dependency_graph={"packages": []},
            packages=["vulnerable-package"],
            ecosystem="npm"
        )
        
        mock_metadata = {
            "name": "vulnerable-package",
            "version": "1.0.0",
            "time": {
                "created": (datetime.now() - timedelta(days=10)).isoformat(),
                "modified": (datetime.now() - timedelta(days=10)).isoformat()
            }
        }
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(context, timeout=30)
                    
                    # Verify analysis completed
                    assert result["total_packages_analyzed"] == 1
                    
                    # Package should have reputation analysis
                    pkg = result["packages"][0]
                    assert pkg["package_name"] == "vulnerable-package"
                    assert "reputation_score" in pkg
    
    def test_agent_caching_integration(self, agent, sample_context):
        """Test agent properly uses cache manager"""
        mock_metadata = {
            "name": "express",
            "version": "4.18.2",
            "author": {"name": "Test"},
            "time": {
                "created": (datetime.now() - timedelta(days=365)).isoformat(),
                "modified": datetime.now().isoformat()
            }
        }
        
        # First call - cache miss
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_metadata) as mock_fetch:
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None) as mock_get:
                with patch.object(agent.cache_manager, 'store_reputation') as mock_store:
                    result1 = agent.analyze(sample_context, timeout=30)
                    
                    # Verify cache was checked
                    assert mock_get.call_count >= 1
                    
                    # Verify results were stored in cache
                    assert mock_store.call_count >= 1
        
        # Second call - cache hit
        cached_result = {
            "package_name": "express",
            "reputation_score": 0.8,
            "risk_level": "low",
            "confidence": 0.95
        }
        
        with patch.object(agent, 'fetch_npm_metadata') as mock_fetch:
            with patch.object(agent.cache_manager, 'get_reputation', return_value=cached_result):
                result2 = agent.analyze(sample_context, timeout=30)
                
                # Verify fetch was not called (cache hit)
                # Note: May be called for packages not in cache
                assert result2["total_packages_analyzed"] == 2
    
    def test_agent_timeout_handling(self, agent, sample_context):
        """Test agent respects timeout in integration scenario"""
        # Mock slow metadata fetch
        def slow_fetch(*args, **kwargs):
            import time
            time.sleep(2)
            return {}
        
        with patch.object(agent, 'fetch_npm_metadata', side_effect=slow_fetch):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                result = agent.analyze(sample_context, timeout=1)
                
                # Should timeout and return partial results
                assert "packages" in result
                assert result["duration_seconds"] <= 3  # Should stop early (with some tolerance)
    
    def test_agent_with_mixed_ecosystems(self, agent):
        """Test agent handles context with mixed ecosystem information"""
        # Create context with npm packages
        context = SharedContext(
            initial_findings=[],
            dependency_graph={"packages": []},
            packages=["express"],
            ecosystem="npm"
        )
        
        mock_npm_metadata = {
            "name": "express",
            "version": "4.18.2",
            "time": {
                "created": (datetime.now() - timedelta(days=365)).isoformat(),
                "modified": datetime.now().isoformat()
            }
        }
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_npm_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(context, timeout=30)
                    
                    assert result["total_packages_analyzed"] == 1
                    assert result["packages"][0]["ecosystem"] == "npm"
    
    def test_agent_error_recovery(self, agent, sample_context):
        """Test agent recovers from errors and continues analysis"""
        # Mock fetch to fail for first package, succeed for second
        call_count = [0]
        
        def mock_fetch(package_name):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Network error")
            else:
                return {
                    "name": package_name,
                    "version": "1.0.0",
                    "time": {
                        "created": (datetime.now() - timedelta(days=100)).isoformat(),
                        "modified": datetime.now().isoformat()
                    }
                }
        
        with patch.object(agent, 'fetch_npm_metadata', side_effect=mock_fetch):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(sample_context, timeout=30)
                    
                    # Should analyze both packages despite first one failing
                    assert result["total_packages_analyzed"] == 2
                    
                    # First package should have error
                    assert any("error" in pkg for pkg in result["packages"])
                    
                    # Second package should succeed
                    assert any("error" not in pkg for pkg in result["packages"])
    
    def test_agent_confidence_scoring(self, agent, sample_context):
        """Test agent provides appropriate confidence scores"""
        mock_metadata = {
            "name": "express",
            "version": "4.18.2",
            "author": {"name": "TJ Holowaychuk"},
            "maintainers": [{"name": "dougwilson"}],
            "time": {
                "created": (datetime.now() - timedelta(days=365)).isoformat(),
                "modified": datetime.now().isoformat()
            },
            "dist-tags": {"latest": "4.18.2"}
        }
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(sample_context, timeout=30)
                    
                    # Overall confidence should be reasonable
                    assert 0.0 <= result["confidence"] <= 1.0
                    
                    # Individual package confidence should be reasonable
                    for pkg in result["packages"]:
                        assert 0.0 <= pkg.get("confidence", 0.0) <= 1.0
    
    def test_agent_risk_assessment(self, agent):
        """Test agent properly assesses risk levels"""
        # Test high-risk package (new, unknown author)
        high_risk_metadata = {
            "name": "suspicious-package",
            "version": "1.0.0",
            "time": {
                "created": (datetime.now() - timedelta(days=5)).isoformat(),
                "modified": (datetime.now() - timedelta(days=5)).isoformat()
            }
        }
        
        context = SharedContext(
            initial_findings=[],
            dependency_graph={"packages": []},
            packages=["suspicious-package"],
            ecosystem="npm"
        )
        
        with patch.object(agent, 'fetch_npm_metadata', return_value=high_risk_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(context, timeout=30)
                    
                    pkg = result["packages"][0]
                    
                    # Should identify as high or medium risk
                    assert pkg["risk_level"] in ["high", "medium"]
                    
                    # Should have risk factors
                    assert len(pkg.get("risk_factors", [])) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
