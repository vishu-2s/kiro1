"""
Unit tests for the Reputation Analysis Agent.

Tests the reputation agent's ability to:
- Fetch metadata from npm and PyPI registries
- Calculate reputation scores
- Identify risk factors
- Analyze author history
- Provide confidence scores and reasoning
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from agents.reputation_agent import ReputationAnalysisAgent
from agents.types import SharedContext, Finding


class TestReputationAnalysisAgent:
    """Test suite for ReputationAnalysisAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a reputation agent instance for testing"""
        return ReputationAnalysisAgent()
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock shared context"""
        return SharedContext(
            initial_findings=[],
            dependency_graph={"packages": []},
            packages=["express", "lodash"],
            ecosystem="npm"
        )
    
    @pytest.fixture
    def mock_npm_metadata(self):
        """Create mock npm metadata"""
        created_date = (datetime.now() - timedelta(days=365)).isoformat()
        modified_date = datetime.now().isoformat()
        
        return {
            "name": "express",
            "version": "4.18.2",
            "description": "Fast, unopinionated, minimalist web framework",
            "author": {
                "name": "TJ Holowaychuk"
            },
            "maintainers": [
                {"name": "dougwilson"},
                {"name": "wesleytodd"}
            ],
            "time": {
                "created": created_date,
                "modified": modified_date
            },
            "dist-tags": {
                "latest": "4.18.2"
            },
            "license": "MIT"
        }
    
    @pytest.fixture
    def mock_pypi_metadata(self):
        """Create mock PyPI metadata"""
        return {
            "info": {
                "name": "requests",
                "version": "2.31.0",
                "summary": "Python HTTP for Humans.",
                "author": "Kenneth Reitz",
                "author_email": "me@kennethreitz.org",
                "license": "Apache 2.0"
            },
            "releases": {
                "2.31.0": [
                    {
                        "upload_time": (datetime.now() - timedelta(days=30)).isoformat()
                    }
                ],
                "2.30.0": [
                    {
                        "upload_time": (datetime.now() - timedelta(days=180)).isoformat()
                    }
                ]
            }
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent.name == "ReputationAnalysisAgent"
        assert agent.reputation_scorer is not None
        assert agent.cache_manager is not None
        assert len(agent.tools) == 3
    
    def test_fetch_npm_metadata_success(self, agent, mock_npm_metadata):
        """Test fetching npm metadata successfully"""
        with patch.object(agent.reputation_scorer, '_fetch_metadata', return_value=mock_npm_metadata):
            metadata = agent.fetch_npm_metadata("express")
            
            assert metadata["name"] == "express"
            assert metadata["version"] == "4.18.2"
            assert "author" in metadata
    
    def test_fetch_pypi_metadata_success(self, agent, mock_pypi_metadata):
        """Test fetching PyPI metadata successfully"""
        with patch.object(agent.reputation_scorer, '_fetch_metadata', return_value=mock_pypi_metadata):
            metadata = agent.fetch_pypi_metadata("requests")
            
            assert metadata["info"]["name"] == "requests"
            assert metadata["info"]["version"] == "2.31.0"
    
    def test_fetch_npm_metadata_failure(self, agent):
        """Test handling of npm metadata fetch failure"""
        with patch.object(agent.reputation_scorer, '_fetch_metadata', side_effect=RuntimeError("Network error")):
            with pytest.raises(RuntimeError):
                agent.fetch_npm_metadata("nonexistent-package")
    
    def test_calculate_reputation_score(self, agent, mock_npm_metadata):
        """Test reputation score calculation"""
        reputation_data = agent.calculate_reputation_score(mock_npm_metadata, "npm")
        
        assert "score" in reputation_data
        assert "factors" in reputation_data
        assert 0.0 <= reputation_data["score"] <= 1.0
        
        # Check all factor scores are present
        factors = reputation_data["factors"]
        assert "age_score" in factors
        assert "downloads_score" in factors
        assert "author_score" in factors
        assert "maintenance_score" in factors
    
    def test_identify_risk_factors_new_package(self, agent):
        """Test risk factor identification for new packages"""
        reputation_data = {
            "score": 0.3,
            "factors": {
                "age_score": 0.2,  # Very new
                "downloads_score": 0.5,
                "author_score": 0.5,
                "maintenance_score": 0.5
            },
            "flags": ["new_package"]
        }
        
        risk_factors = agent._identify_risk_factors(reputation_data, {}, "npm")
        
        # Should identify new package risk
        assert any(rf["type"] == "new_package" for rf in risk_factors)
        assert any(rf["severity"] == "high" for rf in risk_factors)
    
    def test_identify_risk_factors_low_downloads(self, agent):
        """Test risk factor identification for low downloads"""
        reputation_data = {
            "score": 0.4,
            "factors": {
                "age_score": 0.7,
                "downloads_score": 0.2,  # Very low
                "author_score": 0.5,
                "maintenance_score": 0.5
            },
            "flags": ["low_downloads"]
        }
        
        risk_factors = agent._identify_risk_factors(reputation_data, {}, "npm")
        
        # Should identify low downloads risk
        assert any(rf["type"] == "low_downloads" for rf in risk_factors)
    
    def test_identify_risk_factors_unknown_author(self, agent):
        """Test risk factor identification for unknown authors"""
        reputation_data = {
            "score": 0.4,
            "factors": {
                "age_score": 0.7,
                "downloads_score": 0.7,
                "author_score": 0.3,  # Unknown author
                "maintenance_score": 0.5
            },
            "flags": ["unknown_author"]
        }
        
        risk_factors = agent._identify_risk_factors(reputation_data, {}, "npm")
        
        # Should identify unknown author risk
        assert any(rf["type"] == "unknown_author" for rf in risk_factors)
    
    def test_identify_risk_factors_abandoned_package(self, agent):
        """Test risk factor identification for abandoned packages"""
        reputation_data = {
            "score": 0.4,
            "factors": {
                "age_score": 0.9,
                "downloads_score": 0.7,
                "author_score": 0.7,
                "maintenance_score": 0.2  # Abandoned
            },
            "flags": ["unmaintained"]
        }
        
        risk_factors = agent._identify_risk_factors(reputation_data, {}, "npm")
        
        # Should identify abandoned package risk
        assert any(rf["type"] == "abandoned" for rf in risk_factors)
    
    def test_analyze_author_history_npm(self, agent, mock_npm_metadata):
        """Test author history analysis for npm packages"""
        author_analysis = agent._analyze_author_history(mock_npm_metadata, "npm")
        
        assert author_analysis["author_name"] == "TJ Holowaychuk"
        assert author_analysis["maintainer_count"] == 2
        assert author_analysis["is_organization"] is True
    
    def test_analyze_author_history_pypi(self, agent, mock_pypi_metadata):
        """Test author history analysis for PyPI packages"""
        author_analysis = agent._analyze_author_history(mock_pypi_metadata, "pypi")
        
        assert author_analysis["author_name"] == "Kenneth Reitz"
        assert "author_name" in author_analysis
    
    def test_analyze_author_history_no_author(self, agent):
        """Test author history analysis with missing author"""
        metadata = {"name": "test-package"}
        author_analysis = agent._analyze_author_history(metadata, "npm")
        
        assert author_analysis["author_name"] is None
        assert "no_author_information" in author_analysis["suspicious_patterns"]
    
    def test_determine_risk_level_high(self, agent):
        """Test risk level determination for high-risk packages"""
        risk_factors = [
            {"type": "new_package", "severity": "high"},
            {"type": "unknown_author", "severity": "high"}
        ]
        
        risk_level = agent._determine_risk_level(0.3, risk_factors)
        assert risk_level == "high"
    
    def test_determine_risk_level_medium(self, agent):
        """Test risk level determination for medium-risk packages"""
        risk_factors = [
            {"type": "recent_package", "severity": "medium"}
        ]
        
        risk_level = agent._determine_risk_level(0.5, risk_factors)
        assert risk_level == "medium"
    
    def test_determine_risk_level_low(self, agent):
        """Test risk level determination for low-risk packages"""
        risk_factors = []
        
        risk_level = agent._determine_risk_level(0.8, risk_factors)
        assert risk_level == "low"
    
    def test_calculate_confidence_high(self, agent):
        """Test confidence calculation with complete data"""
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
        assert confidence >= 0.9
    
    def test_calculate_confidence_low(self, agent):
        """Test confidence calculation with incomplete data"""
        reputation_data = {
            "score": 0.5,
            "factors": {
                "age_score": 0.5,
                "downloads_score": 0.5,
                "author_score": 0.5,
                "maintenance_score": 0.5
            },
            "flags": ["error"]
        }
        metadata = {}
        
        confidence = agent._calculate_confidence(reputation_data, metadata)
        assert confidence < 0.8
    
    def test_generate_reasoning(self, agent):
        """Test reasoning generation"""
        reputation_data = {
            "score": 0.4,
            "factors": {
                "age_score": 0.3,
                "downloads_score": 0.3,
                "author_score": 0.5,
                "maintenance_score": 0.5
            }
        }
        risk_factors = [
            {"type": "new_package", "severity": "high", "description": "Package is very new"}
        ]
        author_analysis = {
            "author_name": "Test Author",
            "suspicious_patterns": []
        }
        
        reasoning = agent._generate_reasoning(
            reputation_data,
            risk_factors,
            author_analysis,
            "high"
        )
        
        assert "reputation score" in reasoning.lower()
        assert "risk level" in reasoning.lower()
    
    def test_analyze_package_reputation_success(self, agent, mock_context, mock_npm_metadata):
        """Test full package reputation analysis"""
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_npm_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent._analyze_package_reputation("express", "npm", mock_context)
                    
                    assert result["package_name"] == "express"
                    assert "reputation_score" in result
                    assert "risk_level" in result
                    assert "risk_factors" in result
                    assert "author_analysis" in result
                    assert "confidence" in result
                    assert "reasoning" in result
    
    def test_analyze_with_cache_hit(self, agent, mock_context):
        """Test analysis with cached data"""
        cached_result = {
            "package_name": "express",
            "reputation_score": 0.8,
            "risk_level": "low",
            "confidence": 0.95
        }
        
        with patch.object(agent.cache_manager, 'get_reputation', return_value=cached_result):
            result = agent._analyze_package_reputation("express", "npm", mock_context)
            
            assert result == cached_result
    
    def test_analyze_full_context(self, agent, mock_context, mock_npm_metadata):
        """Test analyzing full context with multiple packages"""
        with patch.object(agent, 'fetch_npm_metadata', return_value=mock_npm_metadata):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                with patch.object(agent.cache_manager, 'store_reputation'):
                    result = agent.analyze(mock_context, timeout=30)
                    
                    assert "packages" in result
                    assert "total_packages_analyzed" in result
                    assert "confidence" in result
                    assert result["total_packages_analyzed"] == 2
    
    def test_analyze_with_timeout(self, agent, mock_context):
        """Test analysis respects timeout"""
        # Mock slow metadata fetch
        def slow_fetch(*args, **kwargs):
            import time
            time.sleep(2)
            return {}
        
        with patch.object(agent, 'fetch_npm_metadata', side_effect=slow_fetch):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                result = agent.analyze(mock_context, timeout=1)
                
                # Should timeout and return partial results
                assert "packages" in result
                assert result["total_packages_analyzed"] < len(mock_context.packages)
    
    def test_analyze_with_error_handling(self, agent, mock_context):
        """Test error handling during analysis"""
        with patch.object(agent, 'fetch_npm_metadata', side_effect=RuntimeError("Network error")):
            with patch.object(agent.cache_manager, 'get_reputation', return_value=None):
                result = agent.analyze(mock_context, timeout=30)
                
                # Should handle errors gracefully
                assert "packages" in result
                assert result["total_packages_analyzed"] == 2
                
                # Check that error packages have error field
                for pkg in result["packages"]:
                    if "error" in pkg:
                        assert pkg["confidence"] == 0.0
    
    def test_extract_metadata_summary_npm(self, agent, mock_npm_metadata):
        """Test metadata summary extraction for npm"""
        summary = agent._extract_metadata_summary(mock_npm_metadata, "npm")
        
        assert summary["name"] == "express"
        assert summary["version"] == "4.18.2"
        assert "description" in summary
        assert "license" in summary
    
    def test_extract_metadata_summary_pypi(self, agent, mock_pypi_metadata):
        """Test metadata summary extraction for PyPI"""
        summary = agent._extract_metadata_summary(mock_pypi_metadata, "pypi")
        
        assert summary["name"] == "requests"
        assert summary["version"] == "2.31.0"
        assert "description" in summary
    
    def test_has_suspicious_patterns_normal(self, agent, mock_npm_metadata):
        """Test suspicious pattern detection for normal packages"""
        has_suspicious = agent._has_suspicious_patterns(mock_npm_metadata, "npm")
        assert has_suspicious is False
    
    def test_has_suspicious_patterns_suspicious_version(self, agent):
        """Test suspicious pattern detection for suspicious versions"""
        metadata = {
            "name": "test-package",
            "version": "1.0.0",
            "dist-tags": {
                "latest": "99.0.0"  # Suspicious version
            }
        }
        
        has_suspicious = agent._has_suspicious_patterns(metadata, "npm")
        assert has_suspicious is True
    
    def test_has_suspicious_patterns_missing_fields(self, agent):
        """Test suspicious pattern detection for missing fields"""
        metadata = {}  # Missing critical fields
        
        has_suspicious = agent._has_suspicious_patterns(metadata, "npm")
        assert has_suspicious is True
    
    def test_generate_cache_key(self, agent):
        """Test cache key generation"""
        cache_key = agent._generate_cache_key("express", "npm")
        assert cache_key == "reputation:npm:express"
    
    def test_validate_context_invalid(self, agent):
        """Test context validation with invalid context"""
        invalid_context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]  # Empty packages
        )
        
        is_valid = agent._validate_context(invalid_context)
        assert is_valid is False
    
    def test_validate_context_valid(self, agent, mock_context):
        """Test context validation with valid context"""
        is_valid = agent._validate_context(mock_context)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
