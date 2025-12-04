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
        
        prompt = f"""You are a senior security engineer analyzing a comprehensive software supply chain security report. 
Based on the complete analysis below, generate detailed, actionable, and specific recommendations.

{context}

Your task is to generate recommendations in 3 categories. Each recommendation should be 7-8 lines long, 
highly specific to the actual packages and findings in the report, and provide concrete actionable steps.

1. IMMEDIATE ACTIONS (2-3 recommendations):
   - Reference SPECIFIC package names from the report
   - Explain the EXACT risk based on the findings
   - Provide CONCRETE remediation steps with timelines
   - Mention specific CVEs or vulnerability types if relevant
   - Include impact assessment

2. PREVENTIVE MEASURES (4-5 recommendations):
   - Long-term security improvements based on the patterns observed
   - Specific tools and technologies to implement
   - Process improvements tailored to the findings
   - Best practices relevant to the ecosystem
   - Implementation guidance with examples

3. MONITORING (4-5 recommendations):
   - Ongoing security practices specific to the vulnerabilities found
   - Metrics to track based on the analysis
   - Alert configurations for similar issues
   - Audit schedules appropriate for the risk level
   - Continuous improvement strategies

IMPORTANT:
- Use emojis for visual clarity (🔴, ⚠️, 🛡️, 📦, 📅, 🔔, etc.)
- Reference actual package names from the report
- Make each recommendation 7-8 lines with complete context
- Be specific and actionable, not generic
- Consider the severity distribution and package count

Return ONLY valid JSON in this exact format:
{{
  "immediate_actions": [
    "🔴 First immediate action with 7-8 lines of detailed guidance...",
    "⚠️ Second immediate action with 7-8 lines of detailed guidance..."
  ],
  "preventive_measures": [
    "🛡️ First preventive measure with 7-8 lines...",
    "📦 Second preventive measure with 7-8 lines...",
    "🔒 Third preventive measure with 7-8 lines...",
    "📊 Fourth preventive measure with 7-8 lines...",
    "👥 Fifth preventive measure with 7-8 lines..."
  ],
  "monitoring": [
    "📅 First monitoring practice with 7-8 lines...",
    "🔔 Second monitoring practice with 7-8 lines...",
    "🔄 Third monitoring practice with 7-8 lines...",
    "📈 Fourth monitoring practice with 7-8 lines...",
    "🚨 Fifth monitoring practice with 7-8 lines..."
  ]
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

def generate_fallback_recommendations(context: str) -> Dict[str, List[str]]:
    """Generate basic recommendations if LLM fails."""
    return {
        "immediate_actions": [
            "Review the security findings in the report and prioritize critical and high-severity vulnerabilities",
            "Update vulnerable packages to patched versions as soon as possible"
        ],
        "preventive_measures": [
            "Implement automated dependency scanning in your CI/CD pipeline",
            "Use lock files to ensure reproducible builds",
            "Enable security policies for dependency management",
            "Maintain a Software Bill of Materials (SBOM)",
            "Establish a dependency approval process"
        ],
        "monitoring": [
            "Schedule regular dependency audits",
            "Subscribe to security advisories",
            "Establish update cadence for dependencies",
            "Track security metrics over time",
            "Set up real-time vulnerability alerts"
        ]
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
    print(f"  - Total findings: {report['summary']['total_findings']}")
    print(f"  - Critical: {report['summary']['critical_findings']}")
    print(f"  - High: {report['summary']['high_findings']}")
    print(f"  - Packages affected: {report['summary']['packages_with_findings']}")
    
    # Generate recommendations
    print("\n🤖 Generating LLM-based recommendations...")
    recommendations = generate_llm_recommendations(context)
    
    # Display recommendations
    print("\n" + "=" * 60)
    print("GENERATED RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n🚨 IMMEDIATE ACTIONS:")
    for i, action in enumerate(recommendations['immediate_actions'], 1):
        print(f"\n{i}. {action[:150]}...")
    
    print("\n\n🛡️ PREVENTIVE MEASURES:")
    for i, measure in enumerate(recommendations['preventive_measures'], 1):
        print(f"\n{i}. {measure[:150]}...")
    
    print("\n\n📊 MONITORING:")
    for i, practice in enumerate(recommendations['monitoring'], 1):
        print(f"\n{i}. {practice[:150]}...")
    
    # Update report
    print("\n" + "=" * 60)
    update_report_with_recommendations(report_path, recommendations)
    
    print("\n✅ Recommendations generated and saved successfully!")
    print("\nYou can now view the updated report in the web UI.")

if __name__ == '__main__':
    main()
