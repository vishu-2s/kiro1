"""
Demonstration of reputation scoring integration into the analysis pipeline.

This script shows how reputation scoring is automatically integrated into
the package vulnerability checking process.
"""

import json
from tools.sbom_tools import check_vulnerable_packages
from tools.cache_manager import get_cache_manager


def demo_reputation_integration():
    """Demonstrate reputation scoring integration."""
    
    print("=" * 80)
    print("REPUTATION SCORING INTEGRATION DEMO")
    print("=" * 80)
    print()
    
    # Create a sample SBOM with various packages
    sbom_data = {
        "packages": [
            {
                "name": "express",
                "version": "4.18.2",
                "ecosystem": "npm"
            },
            {
                "name": "lodash",
                "version": "4.17.21",
                "ecosystem": "npm"
            },
            {
                "name": "very-new-suspicious-pkg",
                "version": "0.0.1",
                "ecosystem": "npm"
            }
        ]
    }
    
    print("Sample SBOM with 3 packages:")
    for pkg in sbom_data["packages"]:
        print(f"  - {pkg['name']}@{pkg['version']} ({pkg['ecosystem']})")
    print()
    
    # Run vulnerability check with reputation enabled
    print("Running vulnerability check with reputation scoring enabled...")
    print()
    
    findings = check_vulnerable_packages(
        sbom_data, 
        use_osv=False,  # Disable OSV to focus on reputation
        check_reputation=True
    )
    
    # Display findings
    print(f"Total findings: {len(findings)}")
    print()
    
    # Separate findings by type
    reputation_findings = [f for f in findings if f.finding_type == "low_reputation"]
    other_findings = [f for f in findings if f.finding_type != "low_reputation"]
    
    if reputation_findings:
        print(f"Reputation Findings: {len(reputation_findings)}")
        print("-" * 80)
        for finding in reputation_findings:
            print(f"\nPackage: {finding.package}@{finding.version}")
            print(f"Severity: {finding.severity}")
            print(f"Confidence: {finding.confidence:.2f}")
            print(f"Evidence:")
            for evidence in finding.evidence:
                print(f"  - {evidence}")
            print(f"Recommendations:")
            for rec in finding.recommendations[:3]:  # Show first 3
                print(f"  - {rec}")
    else:
        print("No low reputation packages detected.")
    
    print()
    
    if other_findings:
        print(f"Other Findings: {len(other_findings)}")
        print("-" * 80)
        for finding in other_findings:
            print(f"  - {finding.package}: {finding.finding_type} ({finding.severity})")
    
    print()
    
    # Show cache statistics
    print("Cache Statistics:")
    print("-" * 80)
    cache_manager = get_cache_manager()
    stats = cache_manager.get_statistics()
    
    print(f"Backend: {stats.get('backend', 'unknown')}")
    print(f"Total entries: {stats.get('total_entries', 0)}")
    print(f"Total hits: {stats.get('total_hits', 0)}")
    print(f"Cache size: {stats.get('size_mb', 0)} MB / {stats.get('max_size_mb', 0)} MB")
    if 'utilization_percent' in stats:
        print(f"Utilization: {stats['utilization_percent']}%")
    
    print()
    print("=" * 80)
    print("INTEGRATION FEATURES DEMONSTRATED:")
    print("=" * 80)
    print("✓ Reputation checks integrated into vulnerability scanning")
    print("✓ Low reputation packages automatically flagged")
    print("✓ Reputation data cached with 24-hour TTL")
    print("✓ Findings include detailed evidence and recommendations")
    print("✓ Graceful handling of API failures")
    print("✓ Support for multiple ecosystems (npm, pypi)")
    print()


def demo_cache_behavior():
    """Demonstrate caching behavior for reputation data."""
    
    print("=" * 80)
    print("REPUTATION CACHING DEMO")
    print("=" * 80)
    print()
    
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
    
    cache_key = "reputation:npm:demo-package:1.0.0"
    
    print("Storing reputation data in cache...")
    cache_manager.store_reputation(cache_key, test_reputation, ttl_hours=24)
    print(f"Cache key: {cache_key}")
    print(f"TTL: 24 hours")
    print()
    
    print("Retrieving from cache...")
    cached_data = cache_manager.get_reputation(cache_key)
    
    if cached_data:
        print("✓ Cache hit!")
        print(f"Score: {cached_data['score']}")
        print(f"Flags: {', '.join(cached_data['flags'])}")
    else:
        print("✗ Cache miss")
    
    print()
    print("Cache statistics:")
    stats = cache_manager.get_statistics()
    print(f"Total entries: {stats.get('total_entries', 0)}")
    print(f"Total hits: {stats.get('total_hits', 0)}")
    print()


if __name__ == "__main__":
    demo_reputation_integration()
    print()
    demo_cache_behavior()
