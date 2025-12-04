"""
Test script to demonstrate clean output formatting.

Shows how scattered data is consolidated into clean, organized structure.
"""

import json
from agents.output_formatter import format_clean_report
from agents.safe_types import SafeSharedContext, SafeAgentResult, SafeDict

print("=" * 80)
print("CLEAN OUTPUT FORMAT - DEMONSTRATION")
print("=" * 80)

# Create mock context with agent results
context = SafeSharedContext(
    packages=["express", "lodash", "word-wrap"],
    ecosystem="npm",
    input_mode="local",
    project_path="/path/to/project"
)

# Mock vulnerability agent result
vuln_result = SafeAgentResult(
    agent_name="vulnerability_analysis",
    success=True,
    data=SafeDict({
        "packages": [
            {
                "package_name": "express",
                "package_version": "4.17.0",
                "ecosystem": "npm",
                "vulnerabilities": [
                    {
                        "id": "GHSA-xxxx-yyyy-zzzz",
                        "summary": "Prototype Pollution in express",
                        "details": "Express is vulnerable to prototype pollution which could allow attackers to modify object prototypes.",
                        "severity": "high",
                        "cvss_score": 7.5,
                        "is_current_version_affected": True,
                        "fixed_versions": ["4.18.0"],
                        "affected_versions": [">=4.0.0", "<4.18.0"],
                        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2023-12345"],
                        "aliases": ["CVE-2023-12345"],
                        "published": "2023-06-15T10:00:00Z",
                        "modified": "2023-06-20T15:30:00Z"
                    },
                    {
                        "id": "GHSA-aaaa-bbbb-cccc",
                        "summary": "Path Traversal in express",
                        "details": "Express allows path traversal attacks in certain configurations.",
                        "severity": "medium",
                        "cvss_score": 5.3,
                        "is_current_version_affected": True,
                        "fixed_versions": ["4.18.0"],
                        "affected_versions": [">=4.0.0", "<4.18.0"],
                        "references": ["https://github.com/advisories/GHSA-aaaa-bbbb-cccc"],
                        "aliases": [],
                        "published": "2023-05-10T08:00:00Z",
                        "modified": "2023-05-15T12:00:00Z"
                    }
                ],
                "vulnerability_count": 2
            },
            {
                "package_name": "lodash",
                "package_version": "4.17.19",
                "ecosystem": "npm",
                "vulnerabilities": [],
                "vulnerability_count": 0
            },
            {
                "package_name": "word-wrap",
                "package_version": "1.2.3",
                "ecosystem": "npm",
                "vulnerabilities": [
                    {
                        "id": "GHSA-j8xg-fqg3-53r7",
                        "summary": "Regular Expression Denial of Service",
                        "details": "word-wrap is vulnerable to ReDoS due to insecure regex.",
                        "severity": "medium",
                        "cvss_score": 5.0,
                        "is_current_version_affected": True,
                        "fixed_versions": ["1.2.4"],
                        "affected_versions": [">=0", "<1.2.4"],
                        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2023-26115"],
                        "aliases": ["CVE-2023-26115"],
                        "published": "2023-06-22T06:30:18Z",
                        "modified": "2025-02-13T19:00:43Z"
                    }
                ],
                "vulnerability_count": 1
            }
        ]
    }),
    duration_seconds=8.5,
    confidence=0.95
)

# Mock reputation agent result
rep_result = SafeAgentResult(
    agent_name="reputation_analysis",
    success=True,
    data=SafeDict({
        "packages": [
            {
                "package_name": "express",
                "reputation_score": 0.85,
                "risk_level": "low",
                "risk_factors": [
                    {
                        "type": "high_downloads",
                        "severity": "low",
                        "description": "Package has high download counts",
                        "score": 0.9
                    }
                ]
            },
            {
                "package_name": "lodash",
                "reputation_score": 0.90,
                "risk_level": "low",
                "risk_factors": []
            },
            {
                "package_name": "word-wrap",
                "reputation_score": 0.69,
                "risk_level": "high",
                "risk_factors": [
                    {
                        "type": "abandoned",
                        "severity": "high",
                        "description": "Package appears to be abandoned",
                        "score": 0.2
                    }
                ]
            }
        ]
    }),
    duration_seconds=12.3,
    confidence=0.90
)

# Mock code analysis result (not available for local folder)
code_result = SafeAgentResult(
    agent_name="code_analysis",
    success=False,
    data=SafeDict({}),
    error="Local folder analysis - code analysis not available",
    duration_seconds=0.0,
    confidence=0.0,
    status="not_available"
)

# Add results to context
context.add_agent_result(vuln_result)
context.add_agent_result(rep_result)
context.add_agent_result(code_result)

# Mock rule-based findings
rule_based_findings = [
    {
        "package_name": "express",
        "package_version": "4.17.0",
        "finding_type": "suspicious_pattern",
        "severity": "low",
        "description": "Package contains eval() usage",
        "confidence": 0.7,
        "remediation": "Review code for potential security issues"
    }
]

print("\n" + "=" * 80)
print("FORMATTING CLEAN REPORT...")
print("=" * 80)

# Format clean report
clean_report = format_clean_report(context, rule_based_findings)

print("\n✅ Clean report generated!")

# Display summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
summary = clean_report["summary"]
print(f"\nTotal Packages: {summary['total_packages']}")
print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
print(f"  - Critical: {summary['critical_vulnerabilities']}")
print(f"  - High: {summary['high_vulnerabilities']}")
print(f"  - Medium: {summary['medium_vulnerabilities']}")
print(f"  - Low: {summary['low_vulnerabilities']}")
print(f"\nPackages with Issues: {summary['packages_with_issues']}")
print(f"Packages Safe: {summary['packages_safe']}")
print(f"Overall Risk: {summary['overall_risk'].upper()}")

# Display vulnerabilities
print("\n" + "=" * 80)
print("VULNERABILITIES (Consolidated)")
print("=" * 80)

for i, vuln in enumerate(clean_report["vulnerabilities"], 1):
    print(f"\n{i}. [{vuln['severity'].upper()}] {vuln['title']}")
    print(f"   ID: {vuln['vulnerability_id']}")
    print(f"   Package: {vuln['package_name']}@{vuln['package_version']}")
    print(f"   Status: {vuln['status']}")
    print(f"   CVSS: {vuln['cvss_score']}")
    print(f"   Recommendation: {vuln['recommendation']}")
    if vuln['fixed_versions']:
        print(f"   Fixed in: {', '.join(vuln['fixed_versions'])}")

# Display packages
print("\n" + "=" * 80)
print("PACKAGES (Summary)")
print("=" * 80)

for pkg in clean_report["packages"]:
    print(f"\n📦 {pkg['package_name']}@{pkg['package_version']}")
    print(f"   Vulnerabilities: {pkg['total_vulnerabilities']} "
          f"(Critical: {pkg['critical_count']}, High: {pkg['high_count']}, "
          f"Medium: {pkg['medium_count']}, Low: {pkg['low_count']})")
    print(f"   Reputation: {pkg['reputation_score']:.2f}" if pkg['reputation_score'] else "   Reputation: N/A")
    print(f"   Risk Level: {pkg['risk_level']}")
    print(f"   Overall Risk: {pkg['overall_risk'].upper()}")
    print(f"   Recommendation: {pkg['recommendation']}")

# Display recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS (Prioritized)")
print("=" * 80)

for i, rec in enumerate(clean_report["recommendations"], 1):
    priority_icon = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📋",
        "low": "ℹ️"
    }.get(rec['priority'], "•")
    
    print(f"\n{i}. {priority_icon} [{rec['priority'].upper()}] {rec['action']}")
    print(f"   Details: {rec['details']}")
    print(f"   Impact: {rec['impact']}")

# Display analysis details
print("\n" + "=" * 80)
print("ANALYSIS DETAILS")
print("=" * 80)

for agent_name, details in clean_report["analysis_details"].items():
    status_icon = "✅" if details['success'] else "❌"
    print(f"\n{status_icon} {agent_name}")
    print(f"   Status: {details['status']}")
    print(f"   Duration: {details['duration_seconds']:.2f}s")
    print(f"   Confidence: {details['confidence']:.2f}")
    if details['error']:
        print(f"   Error: {details['error']}")

# Save to file
print("\n" + "=" * 80)
print("SAVING REPORT...")
print("=" * 80)

output_file = "outputs/clean_report_demo.json"
with open(output_file, "w") as f:
    json.dump(clean_report, f, indent=2)

print(f"\n✅ Clean report saved to: {output_file}")

# Show file size comparison
import os
file_size = os.path.getsize(output_file)
print(f"   File size: {file_size:,} bytes")

print("\n" + "=" * 80)
print("KEY IMPROVEMENTS")
print("=" * 80)

print("\n✅ CLEAN STRUCTURE:")
print("   • One vulnerability = one entry (all details in one place)")
print("   • One package = one summary (consolidated information)")
print("   • Clear status field (active, fixed, not_available)")
print("   • Prioritized recommendations")

print("\n✅ EASY TO USE:")
print("   • Simple to display in UI")
print("   • Easy to filter/sort")
print("   • Clear hierarchy")
print("   • Intuitive structure")

print("\n✅ COMPLETE:")
print("   • All vulnerability details")
print("   • All package information")
print("   • Overall summary")
print("   • Analysis metadata")

print("\n🚀 SYSTEM STATUS: CLEAN, ORGANIZED & USER-FRIENDLY")
print("=" * 80)
