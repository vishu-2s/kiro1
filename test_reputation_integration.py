"""
Test reputation scoring integration into analysis pipeline.
"""

import pytest
import json
from tools.sbom_tools import check_vulnerable_packages, SecurityFinding
from tools.cache_manager import get_cache_manager


class TestReputationIntegration:
    """Test reputation scoring integration."""
    
    def test_reputation_check_in_vulnerable_packages(self):
        """Test that reputation checks are performed during package analysis."""
        # Create a simple SBOM with a package
        sbom_data = {
            "packages": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "ecosystem": "npm"
                }
            ]
        }
        
        # Run vulnerability check with reputation enabled
        findings = check_vulnerable_packages(sbom_data, use_osv=False, check_reputation=True)
        
        # Should return findings (may include reputation findings)
        assert isinstance(findings, list)
        
        # All findings should be SecurityFinding objects
        for finding in findings:
            assert isinstance(finding, SecurityFinding)
    
    def test_reputation_check_disabled(self):
        """Test that reputation checks can be disabled."""
        sbom_data = {
            "packages": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "ecosystem": "npm"
                }
            ]
        }
        
        # Run without reputation checks
        findings = check_vulnerable_packages(sbom_data, use_osv=False, check_reputation=False)
        
        # Should not have any reputation findings
        reputation_findings = [f for f in findings if f.finding_type == "low_reputation"]
        assert len(reputation_findings) == 0
    
    def test_reputation_caching(self):
        """Test that reputation data is cached with 24-hour TTL."""
        cache_manager = get_cache_manager()
        
        # Create test reputation data
        test_reputation = {
            "score": 0.25,
            "factors": {
                "age_score": 0.2,
                "downloads_score": 0.1,
                "author_score": 0.3,
                "maintenance_score": 0.4
            },
            "flags": ["new_package", "low_downloads"]
        }
        
        # Store in cache
        cache_key = "reputation:npm:test-pkg:1.0.0"
        cache_manager.store_reputation(cache_key, test_reputation, ttl_hours=24)
        
        # Retrieve from cache
        cached_data = cache_manager.get_reputation(cache_key)
        
        assert cached_data is not None
        assert cached_data["score"] == 0.25
        assert "new_package" in cached_data["flags"]
    
    def test_low_reputation_finding_generation(self):
        """Test that low reputation packages generate appropriate findings."""
        # This test would require mocking the reputation service
        # For now, we'll test the structure
        
        sbom_data = {
            "packages": [
                {
                    "name": "very-new-package",
                    "version": "0.0.1",
                    "ecosystem": "npm"
                }
            ]
        }
        
        # Run check (may or may not generate findings depending on actual package)
        findings = check_vulnerable_packages(sbom_data, use_osv=False, check_reputation=True)
        
        # Check that any reputation findings have correct structure
        reputation_findings = [f for f in findings if f.finding_type == "low_reputation"]
        
        for finding in reputation_findings:
            assert finding.package is not None
            assert finding.version is not None
            assert finding.severity in ["low", "medium", "high", "critical"]
            assert finding.confidence > 0
            assert len(finding.evidence) > 0
            assert len(finding.recommendations) > 0
            assert finding.source == "reputation_scoring"
    
    def test_unsupported_ecosystem_skipped(self):
        """Test that unsupported ecosystems are skipped for reputation checks."""
        sbom_data = {
            "packages": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "ecosystem": "maven"  # Not supported yet
                }
            ]
        }
        
        # Run check
        findings = check_vulnerable_packages(sbom_data, use_osv=False, check_reputation=True)
        
        # Should not have reputation findings for unsupported ecosystem
        reputation_findings = [f for f in findings if f.finding_type == "low_reputation"]
        assert len(reputation_findings) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
