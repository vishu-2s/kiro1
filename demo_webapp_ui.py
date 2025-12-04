"""
Demo script to showcase the enhanced web UI features.
"""
import json
from pathlib import Path

def create_comprehensive_demo_report():
    """Create a comprehensive demo report showcasing all UI features."""
    
    demo_report = {
        "metadata": {
            "target": "multi-ecosystem-project",
            "analysis_type": "local",
            "start_time": "2025-12-02T10:00:00",
            "end_time": "2025-12-02T10:08:30",
            "total_packages": 45,
            "confidence_threshold": 0.7,
            "analysis_id": "demo-2025-12-02"
        },
        "summary": {
            "total_findings": 8,
            "critical_findings": 1,
            "high_findings": 3,
            "medium_findings": 3,
            "low_findings": 1,
            "total_packages": 45,
            "ecosystems_analyzed": ["npm", "pypi"],
            "finding_types": {
                "malicious_package": 1,
                "vulnerability": 3,
                "low_reputation": 4
            },
            "confidence_distribution": {
                "high": 4,
                "medium": 3,
                "low": 1
            }
        },
        "security_findings": [
            # Critical malicious package
            {
                "package": "evil-crypto-miner",
                "version": "1.2.3",
                "ecosystem": "npm",
                "finding_type": "malicious_package",
                "severity": "critical",
                "confidence": 0.98,
                "evidence": [
                    "Reason: Cryptocurrency mining malware detected",
                    "Pattern: Obfuscated code execution",
                    "Network: Connects to mining pool at evil-pool.com",
                    "Analysis: Package downloads and executes mining software"
                ],
                "recommendations": [
                    "Remove this package immediately",
                    "Scan systems for compromise",
                    "Review network logs for mining activity"
                ],
                "source": "npm_script_analysis_enhanced"
            },
            
            # High severity vulnerability
            {
                "package": "lodash",
                "version": "4.17.20",
                "ecosystem": "npm",
                "finding_type": "vulnerability",
                "severity": "high",
                "confidence": 0.95,
                "evidence": [
                    "Known vulnerability: CVE-2021-23337",
                    "Summary: Prototype pollution vulnerability in lodash",
                    "CVSS Score: 7.4 (High)",
                    "Affected versions: < 4.17.21"
                ],
                "recommendations": [
                    "Update to lodash version 4.17.21 or later",
                    "Review code for prototype pollution vulnerabilities"
                ]
            },
            
            # High reputation risk - npm
            {
                "package": "brand-new-framework",
                "version": "0.1.0",
                "ecosystem": "npm",
                "finding_type": "low_reputation",
                "severity": "high",
                "confidence": 0.88,
                "evidence": [
                    "Package reputation score: 0.18 (threshold: 0.3)",
                    "Risk factors: new_package, unknown_author, low_downloads, no_maintenance_history",
                    "Age: 5 days",
                    "Weekly downloads: 12",
                    "Author: unknown-dev-2025"
                ],
                "recommendations": [
                    "Avoid using this package in production",
                    "Wait for package to establish reputation",
                    "Consider well-established alternatives"
                ]
            },
            
            # High reputation risk - Python
            {
                "package": "suspicious-requests",
                "version": "0.0.1",
                "ecosystem": "pypi",
                "finding_type": "low_reputation",
                "severity": "high",
                "confidence": 0.92,
                "evidence": [
                    "Package reputation score: 0.12 (threshold: 0.3)",
                    "Risk factors: new_package, typosquat_candidate, unknown_author, low_downloads",
                    "Age: 2 days",
                    "Weekly downloads: 3",
                    "Similar to popular package: requests",
                    "Author: anonymous-dev"
                ],
                "recommendations": [
                    "Do not use - possible typosquatting attack",
                    "Use official 'requests' package instead",
                    "Report to PyPI security team"
                ]
            },
            
            # Medium vulnerability - Python
            {
                "package": "pillow",
                "version": "8.3.0",
                "ecosystem": "pypi",
                "finding_type": "vulnerability",
                "severity": "medium",
                "confidence": 0.90,
                "evidence": [
                    "Known vulnerability: CVE-2021-34552",
                    "Summary: Buffer overflow in Pillow image processing",
                    "CVSS Score: 5.5 (Medium)",
                    "Affected versions: < 8.3.2"
                ],
                "recommendations": [
                    "Update to Pillow version 8.3.2 or later",
                    "Review image processing code for security"
                ]
            },
            
            # Medium reputation risk - npm
            {
                "package": "experimental-lib",
                "version": "0.5.0",
                "ecosystem": "npm",
                "finding_type": "low_reputation",
                "severity": "medium",
                "confidence": 0.75,
                "evidence": [
                    "Package reputation score: 0.28 (threshold: 0.3)",
                    "Risk factors: new_package, low_downloads",
                    "Age: 45 days",
                    "Weekly downloads: 250",
                    "Author: established-dev (verified)"
                ],
                "recommendations": [
                    "Review package before production use",
                    "Monitor for updates and community adoption",
                    "Consider more established alternatives"
                ]
            },
            
            # Medium reputation risk - Python
            {
                "package": "beta-toolkit",
                "version": "0.3.1",
                "ecosystem": "pypi",
                "finding_type": "low_reputation",
                "severity": "medium",
                "confidence": 0.70,
                "evidence": [
                    "Package reputation score: 0.29 (threshold: 0.3)",
                    "Risk factors: new_package, limited_downloads",
                    "Age: 60 days",
                    "Weekly downloads: 180",
                    "Author: beta-dev-team"
                ],
                "recommendations": [
                    "Acceptable for development/testing",
                    "Monitor before production deployment",
                    "Check for security updates regularly"
                ]
            },
            
            # Low severity vulnerability
            {
                "package": "moment",
                "version": "2.29.1",
                "ecosystem": "npm",
                "finding_type": "vulnerability",
                "severity": "low",
                "confidence": 0.85,
                "evidence": [
                    "Known vulnerability: CVE-2022-31129",
                    "Summary: Regular expression denial of service",
                    "CVSS Score: 3.7 (Low)",
                    "Note: Package is in maintenance mode"
                ],
                "recommendations": [
                    "Consider migrating to modern alternatives (date-fns, dayjs)",
                    "Update to latest version if continuing to use",
                    "Review date parsing code"
                ]
            }
        ],
        "cache_statistics": {
            "backend": "sqlite",
            "total_entries": 42,
            "total_hits": 28,
            "size_mb": 3.8,
            "expired_entries": 2,
            "hit_rate": 0.667
        },
        "raw_data": {
            "cache_statistics": {
                "backend": "sqlite",
                "total_entries": 42,
                "total_hits": 28,
                "size_mb": 3.8,
                "expired_entries": 2
            }
        }
    }
    
    # Save demo report
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / "demo_ui_comprehensive_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(demo_report, f, indent=2)
    
    return report_path

def print_demo_info():
    """Print information about the demo."""
    
    print("=" * 80)
    print("🎨 Web UI Enhancement Demo")
    print("=" * 80)
    print()
    print("This demo showcases all the new web UI features:")
    print()
    print("✨ Features Demonstrated:")
    print("  1. Python Ecosystem Support")
    print("     - PyPI package analysis")
    print("     - Ecosystem badges (npm/PyPI)")
    print("     - Multi-ecosystem projects")
    print()
    print("  2. Reputation Score Display")
    print("     - Color-coded badges (High/Medium/Low risk)")
    print("     - Score values (0.0 - 1.0)")
    print("     - Risk factor details")
    print()
    print("  3. Cache Statistics")
    print("     - Total cached entries: 42")
    print("     - Cache hits: 28")
    print("     - Hit rate: 66.7%")
    print("     - Cache size: 3.8 MB")
    print()
    print("  4. Enhanced Finding Display")
    print("     - Ecosystem identification")
    print("     - Reputation information")
    print("     - AI-enhanced analysis indicators")
    print()
    print("📊 Demo Report Contents:")
    print("  - 8 total findings across npm and PyPI")
    print("  - 1 critical malicious package (npm)")
    print("  - 3 high severity issues (2 vulnerabilities, 2 low reputation)")
    print("  - 3 medium severity issues (1 vulnerability, 2 low reputation)")
    print("  - 1 low severity vulnerability")
    print()
    print("🚀 To View the Demo:")
    print("  1. Run: python app.py")
    print("  2. Open: http://localhost:5000")
    print("  3. Click the 'Report' tab")
    print("  4. The demo report will be displayed automatically")
    print()
    print("💡 What to Look For:")
    print("  - Red/Orange/Green reputation badges on low reputation findings")
    print("  - npm (red) and PyPI (blue) ecosystem badges on packages")
    print("  - Cache performance section showing 66.7% hit rate")
    print("  - Multi-ecosystem summary (npm + PyPI)")
    print("  - AI Enhanced badge on malicious package finding")
    print()
    print("=" * 80)

if __name__ == "__main__":
    print()
    report_path = create_comprehensive_demo_report()
    print(f"✅ Demo report created: {report_path}")
    print()
    print_demo_info()
