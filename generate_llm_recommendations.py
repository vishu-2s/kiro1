#!/usr/bin/env python3
"""
Generate LLM-based recommendations from existing analysis report.
Analyzes the complete demo_ui_comprehensive_report.json and generates
context-aware recommendations using LLM.
"""

import json
import os
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_report(report_path: str) -> Dict[str, Any]:
    """Load the analysis report."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_comprehensive_context(report: Dict[str, Any]) -> str:
    """Build comprehensive context from the entire report for LLM analysis."""
    
    summary = report.get('summary', {})
    security_findings = report.get('security_findings', {})
    dependency_graph = report.get('dependency_graph', {})
    packages = security_findings.get('packages', [])
    
    # Extract detailed information
    critical_packages = []
    high_packages = []
    medium_packages = []
    low_packages = []
    
    vulnerability_details = []
    
    for pkg in packages:
        pkg_name = pkg.get('name', 'unknown')
        findings = pkg.get('findings', [])
        
        for finding in findings:
            severity = finding.get('severity', 'unknown')
            finding_type = finding.get('type', 'unknown')
            description = finding.get('description', '')
            
            detail = {
                'package': pkg_name,
                'version': pkg.get('version', 'unknown'),
                'severity': severity,
                'type': finding_type,
                'description': description
            }
            
            vulnerability_details.append(detail)
            
            if severity == 'critical':
                critical_packages.append(pkg_name)
            elif severity == 'high':
                high_packages.append(pkg_name)
            elif severity == 'medium':
                medium_packages.append(pkg_name)
            elif severity == 'low':
                low_packages.append(pkg_name)
    
    # Build context
    context = f"""
SECURITY ANALYSIS REPORT SUMMARY:

Total Packages Analyzed: {summary.get('total_packages', 0)}
Packages with Security Issues: {summary.get('packages_with_findings', 0)}
Total Security Findings: {summary.get('total_findings', 0)}

SEVERITY BREAKDOWN:
- Critical: {summary.get('critical_findings', 0)} findings in {len(set(critical_packages))} packages
- High: {summary.get('high_findings', 0)} findings in {len(set(high_packages))} packages
- Medium: {summary.get('medium_findings', 0)} findings in {len(set(medium_packages))} packages
- Low: {summary.get('low_findings', 0)} findings in {len(set(low_packages))} packages

AFFECTED PACKAGES:
Critical Severity: {', '.join(list(set(critical_packages))[:10])}
High Severity: {', '.join(list(set(high_packages))[:10])}
Medium Severity: {', '.join(list(set(medium_packages))[:10])}

DETAILED VULNERABILITY SAMPLES (Top 10):
"""
    
    # Add detailed vulnerability information
    for i, vuln in enumerate(vulnerability_details[:10], 1):
        context += f"\n{i}. {vuln['package']} v{vuln['version']}"
        context += f"\n   Severity: {vuln['severity']}"
        context += f"\n   Type: {vuln['type']}"
        context += f"\n   Description: {vuln['description'][:150]}"
        context += "\n"
    
    # Add dependency graph info if available
    if dependency_graph:
        dep_metadata = dependency_graph.get('metadata', {})
        context += f"\n\nDEPENDENCY GRAPH ANALYSIS:"
        context += f"\n- Total Dependencies: {dep_metadata.get('total_packages', 0)}"
        context += f"\n- Circular Dependencies: {dep_metadata.get('circular_dependencies_count', 0)}"
        context += f"\n- Version Conflicts: {dep_metadata.get('version_conflicts_count', 0)}"
    
    return context

def generate_llm_recommendations(context: str) -> Dict[str, List[str]]:
    """Generate recommendations using LLM based on complete report context."""
    
    try:
        from openai import OpenAI
        import os
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are a Senior Security Architect writing an executive summary of security recommendations.

ANALYSIS RESULTS:
{context}

Write exactly 3 concise recommendation paragraphs (7-8 lines each). DO NOT list individual packages - focus on overall strategy and actions.

REQUIREMENTS:
1. IMMEDIATE PRIORITY (1 paragraph): Summarize the critical/high severity issues found and the general remediation approach. Mention the count of issues, not individual package names.

2. SECURITY HARDENING (1 paragraph): Recommend 2-3 specific tools/practices to prevent future vulnerabilities. Be specific about implementation.

3. ONGOING MONITORING (1 paragraph): Describe a sustainable monitoring strategy with specific metrics and cadence.

STYLE:
- Professional, executive-level tone
- No emojis, no bullet points within paragraphs
- Each paragraph should be exactly 7-8 lines
- Focus on business impact and ROI
- Mention specific tools (Dependabot, Snyk, npm audit) but don't list packages
- Use concrete numbers and timelines

Return ONLY valid JSON:
{{
  "summary": "One sentence executive summary of the security posture.",
  "immediate_priority": "7-8 line paragraph about immediate actions needed...",
  "security_hardening": "7-8 line paragraph about preventive measures...",
  "ongoing_monitoring": "7-8 line paragraph about monitoring strategy..."
}}"""

        print("Generating LLM-based recommendations...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior security engineer specializing in software supply chain security."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        response_text = response.choices[0].message.content
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            recommendations = json.loads(json_match.group())
            return recommendations
        else:
            raise ValueError("Could not extract JSON from LLM response")
            
    except Exception as e:
        print(f"Error generating LLM recommendations: {e}")
        print("Falling back to basic recommendations...")
        return generate_fallback_recommendations(context)

def generate_fallback_recommendations(context: str) -> Dict[str, str]:
    """Generate professional recommendations if LLM fails."""
    return {
        "summary": "Security analysis identified vulnerabilities requiring immediate attention and long-term remediation strategy.",
        "immediate_priority": "The analysis has identified critical and high-severity vulnerabilities that require immediate remediation. These vulnerabilities expose the application to potential security breaches including remote code execution, denial of service, and data exposure. Development teams should prioritize updating affected dependencies to their latest patched versions within the next 48-72 hours. For packages without available patches, consider implementing temporary mitigations such as input validation, network segmentation, or replacing the dependency with a secure alternative. Document all remediation actions and verify fixes through re-scanning before deployment to production environments.",
        "security_hardening": "To prevent future vulnerabilities, implement a comprehensive dependency management strategy. First, enable automated dependency scanning in your CI/CD pipeline using tools like npm audit, Snyk, or GitHub Dependabot. Configure these tools to block deployments when critical vulnerabilities are detected. Second, enforce the use of lock files (package-lock.json, yarn.lock, or requirements.txt) and use deterministic installation commands (npm ci instead of npm install) to ensure reproducible builds. Third, establish a dependency review process where new packages are evaluated for security posture, maintenance status, and community trust before adoption. These measures significantly reduce your attack surface and catch vulnerabilities before they reach production.",
        "ongoing_monitoring": "Establish a continuous security monitoring program to maintain long-term security posture. Subscribe to security advisory feeds from GitHub, NVD, and ecosystem-specific sources for real-time vulnerability notifications. Schedule weekly automated security scans and monthly manual dependency audits to identify newly disclosed vulnerabilities. Track key metrics including total dependency count, percentage of dependencies with known vulnerabilities, average time-to-patch, and dependency age distribution. Set organizational targets such as zero critical vulnerabilities in production and patch high-severity issues within 7 days. Regular reporting to stakeholders ensures accountability and demonstrates security program maturity to auditors and customers."
    }

def update_report_with_recommendations(report_path: str, recommendations: Dict[str, List[str]]):
    """Update the report with new recommendations."""
    
    # Load report
    report = load_report(report_path)
    
    # Update recommendations
    report['recommendations'] = recommendations
    
    # Save updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated report saved to: {report_path}")

def main():
    """Main function."""
    
    report_path = 'outputs/demo_ui_comprehensive_report.json'
    
    if not os.path.exists(report_path):
        print(f"Error: Report not found at {report_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("LLM-Based Recommendation Generator")
    print("=" * 60)
    
    # Load report
    print(f"\n📄 Loading report: {report_path}")
    report = load_report(report_path)
    
    # Build context
    print("🔍 Analyzing complete report context...")
    context = build_comprehensive_context(report)
    
    print(f"\nContext built:")
    print(f"  - Total findings: {report['summary'].get('total_findings', 0)}")
    print(f"  - Critical: {report['summary'].get('critical_findings', 0)}")
    print(f"  - High: {report['summary'].get('high_findings', 0)}")
    print(f"  - Packages analyzed: {report['summary'].get('total_packages', 0)}")
    
    # Generate recommendations
    print("\n🤖 Generating LLM-based recommendations...")
    recommendations = generate_llm_recommendations(context)
    
    # Display recommendations
    print("\n" + "=" * 60)
    print("GENERATED RECOMMENDATIONS")
    print("=" * 60)
    
    if 'summary' in recommendations:
        print(f"\n📋 SUMMARY:\n{recommendations.get('summary', '')[:200]}...")
    if 'immediate_priority' in recommendations:
        print(f"\n🚨 IMMEDIATE PRIORITY:\n{recommendations.get('immediate_priority', '')[:200]}...")
    if 'security_hardening' in recommendations:
        print(f"\n🛡️ SECURITY HARDENING:\n{recommendations.get('security_hardening', '')[:200]}...")
    if 'ongoing_monitoring' in recommendations:
        print(f"\n📊 ONGOING MONITORING:\n{recommendations.get('ongoing_monitoring', '')[:200]}...")
    
    # Update report
    print("\n" + "=" * 60)
    update_report_with_recommendations(report_path, recommendations)
    
    print("\n✅ Recommendations generated and saved successfully!")
    print("\nYou can now view the updated report in the web UI.")

if __name__ == '__main__':
    main()
