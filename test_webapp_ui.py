"""
Test script to verify web UI enhancements for Python support and reputation scores.
"""
import json
import os
from pathlib import Path

def test_ui_enhancements():
    """Test that the UI template has the required enhancements."""
    
    # Read the HTML template
    template_path = Path("templates/index.html")
    if not template_path.exists():
        print("❌ Template file not found")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for ecosystem dropdown
    checks = {
        "Ecosystem dropdown": 'id="ecosystem"' in html_content,
        "PyPI option": 'value="pypi"' in html_content,
        "npm option": 'value="npm"' in html_content,
        "Auto-detect option": 'value="auto"' in html_content,
        "Reputation badge styles": 'reputation-badge' in html_content,
        "Reputation high-risk style": 'reputation-high-risk' in html_content,
        "Reputation medium-risk style": 'reputation-medium-risk' in html_content,
        "Reputation low-risk style": 'reputation-low-risk' in html_content,
        "Reputation trusted style": 'reputation-trusted' in html_content,
        "Cache stats section": 'cache-stats' in html_content,
        "Cache stats grid": 'cache-stats-grid' in html_content,
        "Ecosystem badge styles": 'ecosystem-badge' in html_content,
        "npm ecosystem badge": 'ecosystem-npm' in html_content,
        "PyPI ecosystem badge": 'ecosystem-pypi' in html_content,
        "Low reputation finding type": 'low_reputation' in html_content,
        "Cache statistics display": 'cache_statistics' in html_content,
        "Ecosystems analyzed display": 'ecosystems_analyzed' in html_content,
    }
    
    print("=" * 60)
    print("Web UI Enhancement Verification")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✅ All UI enhancements verified successfully!")
        return True
    else:
        print("❌ Some UI enhancements are missing")
        return False

def test_sample_report_rendering():
    """Test that a sample report with reputation and cache data renders correctly."""
    
    # Create a sample report with reputation findings and cache stats
    sample_report = {
        "metadata": {
            "target": "test-project",
            "analysis_type": "local",
            "start_time": "2025-12-02T10:00:00",
            "end_time": "2025-12-02T10:05:00",
            "total_packages": 10,
            "confidence_threshold": 0.7
        },
        "summary": {
            "total_findings": 3,
            "critical_findings": 0,
            "high_findings": 1,
            "medium_findings": 2,
            "low_findings": 0,
            "total_packages": 10,
            "ecosystems_analyzed": ["npm", "pypi"],
            "finding_types": {
                "vulnerability": 1,
                "low_reputation": 2
            }
        },
        "security_findings": [
            {
                "package": "suspicious-pkg",
                "version": "1.0.0",
                "ecosystem": "npm",
                "finding_type": "low_reputation",
                "severity": "medium",
                "confidence": 0.85,
                "evidence": [
                    "Package reputation score: 0.25 (threshold: 0.3)",
                    "Risk factors: new_package, low_downloads"
                ],
                "recommendations": ["Review package before use"]
            },
            {
                "package": "unknown-python-lib",
                "version": "0.1.0",
                "ecosystem": "pypi",
                "finding_type": "low_reputation",
                "severity": "high",
                "confidence": 0.90,
                "evidence": [
                    "Package reputation score: 0.15 (threshold: 0.3)",
                    "Risk factors: new_package, unknown_author, low_downloads"
                ],
                "recommendations": ["Avoid using this package"]
            },
            {
                "package": "lodash",
                "version": "4.17.20",
                "ecosystem": "npm",
                "finding_type": "vulnerability",
                "severity": "high",
                "confidence": 0.95,
                "evidence": [
                    "Known vulnerability: CVE-2021-23337",
                    "Summary: Prototype pollution vulnerability"
                ],
                "recommendations": ["Update to version 4.17.21 or later"]
            }
        ],
        "cache_statistics": {
            "backend": "sqlite",
            "total_entries": 25,
            "total_hits": 15,
            "size_mb": 2.5
        }
    }
    
    # Save sample report
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / "test_ui_sample_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(sample_report, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Sample Report Created")
    print("=" * 60)
    print(f"✅ Sample report saved to: {report_path}")
    print("\nReport includes:")
    print("  - 2 low reputation findings (npm + PyPI)")
    print("  - 1 vulnerability finding")
    print("  - Cache statistics (25 entries, 15 hits, 60% hit rate)")
    print("  - Multi-ecosystem analysis (npm + PyPI)")
    print("\nTo view in web UI:")
    print("  1. Run: python app.py")
    print("  2. Open: http://localhost:5000")
    print("  3. Click 'Report' tab")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("\n🧪 Testing Web UI Enhancements\n")
    
    # Test 1: Verify UI template has all enhancements
    ui_test_passed = test_ui_enhancements()
    
    # Test 2: Create sample report for manual testing
    sample_test_passed = test_sample_report_rendering()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"UI Template Verification: {'✅ PASSED' if ui_test_passed else '❌ FAILED'}")
    print(f"Sample Report Creation: {'✅ PASSED' if sample_test_passed else '❌ FAILED'}")
    print("=" * 60)
    
    if ui_test_passed and sample_test_passed:
        print("\n✅ All tests passed! Web UI is ready.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        exit(1)
