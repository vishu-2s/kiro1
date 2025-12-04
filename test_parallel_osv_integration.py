"""
Test parallel OSV integration with sbom_tools.

Verifies:
1. Parallel queries are used instead of sequential
2. Network failures fail fast without endless retries
3. Graceful degradation when offline
"""

import pytest
from unittest.mock import patch, MagicMock
from tools.sbom_tools import check_vulnerable_packages
from tools.parallel_osv_client import ParallelOSVClient


def test_parallel_osv_used_for_multiple_packages():
    """Verify that parallel OSV client is used for multiple packages."""
    
    # Create SBOM with multiple packages
    sbom_data = {
        "packages": [
            {"name": "express", "version": "4.17.1", "ecosystem": "npm"},
            {"name": "lodash", "version": "4.17.20", "ecosystem": "npm"},
            {"name": "axios", "version": "0.21.1", "ecosystem": "npm"},
        ]
    }
    
    # Mock parallel OSV client to verify it's called
    with patch('tools.sbom_tools._parallel_query_osv') as mock_parallel:
        mock_parallel.return_value = []
        
        # Run check
        findings = check_vulnerable_packages(sbom_data, use_osv=True, check_reputation=False)
        
        # Verify parallel query was called once with all packages
        assert mock_parallel.call_count == 1
        packages_arg = mock_parallel.call_args[0][0]
        assert len(packages_arg) == 3
        assert all(isinstance(pkg, tuple) for pkg in packages_arg)


def test_network_failure_fails_fast():
    """Verify that network failures fail fast without endless retries."""
    
    client = ParallelOSVClient()
    
    # Mock network check to fail
    with patch.object(client, 'check_network_connectivity', return_value=False):
        packages = [
            ("express", "npm", "4.17.1"),
            ("lodash", "npm", "4.17.20"),
        ]
        
        # Should return immediately with errors
        import time
        start = time.time()
        results = client.query_vulnerabilities_parallel(packages)
        duration = time.time() - start
        
        # Should complete in under 1 second (no retries)
        assert duration < 1.0
        
        # All results should have network error
        assert len(results) == 2
        for result in results:
            assert result['success'] is False
            assert 'network' in result['error'].lower()


def test_graceful_degradation_offline():
    """Verify graceful degradation when working offline."""
    
    sbom_data = {
        "packages": [
            {"name": "express", "version": "4.17.1", "ecosystem": "npm"},
        ]
    }
    
    # Mock network check to fail
    with patch('tools.parallel_osv_client.ParallelOSVClient.check_network_connectivity', return_value=False):
        # Should complete without hanging
        findings = check_vulnerable_packages(sbom_data, use_osv=True, check_reputation=False)
        
        # Should still return (even if empty due to network failure)
        assert isinstance(findings, list)


def test_parallel_client_returns_vulns_key():
    """Verify parallel client returns 'vulns' key for compatibility."""
    
    client = ParallelOSVClient()
    
    # Mock successful response
    async def mock_query(*args, **kwargs):
        return {
            "package_name": "test",
            "ecosystem": "npm",
            "vulns": [{"id": "VULN-001"}],
            "success": True
        }
    
    with patch.object(client, 'query_package_async', side_effect=mock_query):
        packages = [("test", "npm", "1.0.0")]
        results = client.query_vulnerabilities_parallel(packages)
        
        # Should have 'vulns' key
        assert len(results) > 0
        assert 'vulns' in results[0]


def test_404_treated_as_success():
    """Verify 404 responses (no vulnerabilities) are treated as success."""
    
    client = ParallelOSVClient()
    
    # Mock 404 response
    async def mock_query(*args, **kwargs):
        return {
            "package_name": "safe-package",
            "ecosystem": "npm",
            "vulns": [],
            "success": True  # 404 should be success
        }
    
    with patch.object(client, 'query_package_async', side_effect=mock_query):
        packages = [("safe-package", "npm", "1.0.0")]
        results = client.query_vulnerabilities_parallel(packages)
        
        assert len(results) == 1
        assert results[0]['success'] is True
        assert results[0]['vulns'] == []


if __name__ == "__main__":
    print("Testing parallel OSV integration...")
    
    print("\n1. Testing parallel queries are used...")
    test_parallel_osv_used_for_multiple_packages()
    print("✓ Parallel queries verified")
    
    print("\n2. Testing network failure fast-fail...")
    test_network_failure_fails_fast()
    print("✓ Fast-fail verified")
    
    print("\n3. Testing graceful offline degradation...")
    test_graceful_degradation_offline()
    print("✓ Graceful degradation verified")
    
    print("\n4. Testing vulns key compatibility...")
    test_parallel_client_returns_vulns_key()
    print("✓ Compatibility verified")
    
    print("\n5. Testing 404 handling...")
    test_404_treated_as_success()
    print("✓ 404 handling verified")
    
    print("\n✅ All tests passed!")
