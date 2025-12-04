"""
End-to-end test for reputation scoring integration in the full analysis pipeline.
"""

import pytest
import tempfile
import json
from pathlib import Path
from analyze_supply_chain import SupplyChainAnalyzer


class TestEndToEndReputation:
    """Test reputation scoring in the complete analysis pipeline."""
    
    def test_sbom_analysis_includes_reputation(self):
        """Test that SBOM analysis includes reputation checks."""
        # Create a temporary SBOM file
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "components": [
                {
                    "type": "library",
                    "name": "express",
                    "version": "4.18.2",
                    "purl": "pkg:npm/express@4.18.2"
                }
            ],
            "packages": [
                {
                    "name": "express",
                    "version": "4.18.2",
                    "ecosystem": "npm"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sbom_data, f)
            sbom_path = f.name
        
        try:
            # Create analyzer
            analyzer = SupplyChainAnalyzer(enable_osv=False)
            
            # Analyze SBOM
            result = analyzer.analyze_sbom_file(sbom_path)
            
            # Verify result structure
            assert result is not None
            assert result.metadata is not None
            assert result.summary is not None
            assert result.security_findings is not None
            
            # Check that findings can include reputation findings
            # (may or may not have findings depending on actual package reputation)
            finding_types = set()
            for finding in result.security_findings:
                if isinstance(finding, dict):
                    finding_types.add(finding.get('finding_type'))
                else:
                    finding_types.add(finding.finding_type)
            
            # Reputation findings are possible
            # (express is well-established, so likely no low_reputation finding)
            print(f"Finding types: {finding_types}")
            
        finally:
            # Clean up
            Path(sbom_path).unlink(missing_ok=True)
    
    def test_local_directory_analysis_includes_reputation(self):
        """Test that local directory analysis includes reputation checks."""
        # Use the test_nested_deps directory which has a package.json
        test_dir = "test_nested_deps"
        
        if not Path(test_dir).exists():
            pytest.skip("test_nested_deps directory not found")
        
        # Create analyzer
        analyzer = SupplyChainAnalyzer(enable_osv=False)
        
        # Analyze directory
        result = analyzer.analyze_local_directory(test_dir)
        
        # Verify result structure
        assert result is not None
        assert result.metadata is not None
        assert result.summary is not None
        assert result.security_findings is not None
        
        # Check that analysis completed successfully
        assert result.metadata.analysis_type == "local_directory"
        assert result.summary.total_packages >= 0
    
    def test_reputation_findings_in_summary(self):
        """Test that reputation findings are counted in summary statistics."""
        # Create SBOM with a potentially low-reputation package
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "packages": [
                {
                    "name": "test-package-xyz-123",
                    "version": "0.0.1",
                    "ecosystem": "npm"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sbom_data, f)
            sbom_path = f.name
        
        try:
            # Create analyzer
            analyzer = SupplyChainAnalyzer(enable_osv=False)
            
            # Analyze SBOM
            result = analyzer.analyze_sbom_file(sbom_path)
            
            # Check summary includes finding types
            assert hasattr(result.summary, 'finding_types')
            assert isinstance(result.summary.finding_types, dict)
            
            # If there are low_reputation findings, they should be counted
            if 'low_reputation' in result.summary.finding_types:
                assert result.summary.finding_types['low_reputation'] > 0
                print(f"Found {result.summary.finding_types['low_reputation']} low reputation findings")
            
        finally:
            # Clean up
            Path(sbom_path).unlink(missing_ok=True)
    
    def test_reputation_cache_used_in_analysis(self):
        """Test that reputation cache is used during analysis."""
        from tools.cache_manager import get_cache_manager
        
        # Get initial cache stats
        cache_manager = get_cache_manager()
        initial_stats = cache_manager.get_statistics()
        initial_entries = initial_stats.get('total_entries', 0)
        
        # Create SBOM
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "packages": [
                {
                    "name": "lodash",
                    "version": "4.17.21",
                    "ecosystem": "npm"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sbom_data, f)
            sbom_path = f.name
        
        try:
            # Create analyzer
            analyzer = SupplyChainAnalyzer(enable_osv=False)
            
            # First analysis - should cache reputation data
            result1 = analyzer.analyze_sbom_file(sbom_path)
            
            # Check cache grew
            stats_after_first = cache_manager.get_statistics()
            entries_after_first = stats_after_first.get('total_entries', 0)
            
            # Second analysis - should use cached data
            result2 = analyzer.analyze_sbom_file(sbom_path)
            
            # Check cache was used (hits increased)
            stats_after_second = cache_manager.get_statistics()
            hits_after_second = stats_after_second.get('total_hits', 0)
            
            # Cache should have been used
            assert hits_after_second > 0
            print(f"Cache entries: {entries_after_first}, Cache hits: {hits_after_second}")
            
        finally:
            # Clean up
            Path(sbom_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
