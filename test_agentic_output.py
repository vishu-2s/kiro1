"""
Test to verify agentic LLM analysis is captured in output.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("AGENTIC OUTPUT TEST - Verify LLM Analysis is Captured")
print("=" * 80)

# Check if OpenAI API key is available
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("\n❌ OPENAI_API_KEY not found in .env")
    print("   LLM analysis will not be available")
    print("   Set OPENAI_API_KEY to enable AI-powered analysis")
    exit(1)
else:
    print(f"\n✅ OPENAI_API_KEY found: {api_key[:10]}...")

# Test vulnerability agent with LLM analysis
print("\n" + "=" * 80)
print("TEST 1: Vulnerability Agent with LLM Analysis")
print("=" * 80)

from agents.vulnerability_agent import VulnerabilityAnalysisAgent
from agents.safe_types import SafeSharedContext

# Create context
context = SafeSharedContext(
    packages=["lodash"],
    ecosystem="npm"
)

# Create agent
agent = VulnerabilityAnalysisAgent()

print("\nAnalyzing lodash package...")
print("This will:")
print("  1. Query OSV API for vulnerabilities")
print("  2. Use LLM to analyze vulnerabilities")
print("  3. Store LLM analysis in result")

try:
    result = agent.analyze(context, timeout=60)
    
    print(f"\n✅ Analysis completed!")
    print(f"   Packages analyzed: {result.get('total_packages_analyzed', 0)}")
    print(f"   Vulnerabilities found: {result.get('total_vulnerabilities_found', 0)}")
    
    # Check for LLM analysis
    packages = result.get("packages", [])
    if packages:
        for pkg in packages:
            pkg_name = pkg.get("package_name", "unknown")
            vuln_count = pkg.get("vulnerability_count", 0)
            
            print(f"\n📦 {pkg_name}:")
            print(f"   Vulnerabilities: {vuln_count}")
            
            # Check for LLM assessment
            if "llm_assessment" in pkg:
                llm = pkg["llm_assessment"]
                print(f"\n   🤖 AI Analysis Found!")
                print(f"      Assessment: {llm.get('assessment', 'N/A')}")
                print(f"      Risk Score: {llm.get('risk_score', 'N/A')}/10")
                print(f"      Exploitation Likelihood: {llm.get('exploitation_likelihood', 'N/A')}")
                print(f"      Business Impact: {llm.get('business_impact', 'N/A')}")
                print(f"      Recommended Action: {llm.get('recommended_action', 'N/A')}")
                
                if llm.get('key_concerns'):
                    print(f"      Key Concerns:")
                    for concern in llm.get('key_concerns', []):
                        print(f"        - {concern}")
            else:
                print(f"   ⚠️ No LLM assessment found")
                if vuln_count > 0:
                    print(f"      (Vulnerabilities exist but LLM analysis missing)")
    
    # Save result to file
    output_file = "outputs/test_agentic_output.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Result saved to: {output_file}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test with output formatter
print("\n" + "=" * 80)
print("TEST 2: Output Formatter with Agentic Insights")
print("=" * 80)

from agents.output_formatter import format_clean_report
from agents.safe_types import SafeAgentResult, SafeDict

# Create context with agent result
context2 = SafeSharedContext(
    packages=["lodash", "express"],
    ecosystem="npm"
)

# Add mock result with LLM analysis
mock_result = SafeAgentResult(
    agent_name="vulnerability_analysis",
    success=True,
    data=SafeDict({
        "packages": [
            {
                "package_name": "lodash",
                "package_version": "4.17.19",
                "vulnerabilities": [
                    {
                        "id": "GHSA-test",
                        "summary": "Test vulnerability",
                        "severity": "high",
                        "cvss_score": 7.5
                    }
                ],
                "vulnerability_count": 1,
                "llm_assessment": {
                    "assessment": "High-risk vulnerability with active exploits",
                    "risk_score": 8.0,
                    "exploitation_likelihood": "high",
                    "business_impact": "Could lead to data compromise",
                    "recommended_action": "Update immediately",
                    "key_concerns": ["Active exploits", "Widely used"]
                }
            }
        ]
    })
)

context2.add_agent_result(mock_result)

print("\nFormatting clean report with agentic insights...")

try:
    clean_report = format_clean_report(context2)
    
    print("\n✅ Clean report generated!")
    
    # Check for agentic insights
    if "agentic_insights" in clean_report:
        insights = clean_report["agentic_insights"]
        print(f"\n🤖 Agentic Insights Section Found!")
        print(f"   AI Analysis Used: {insights.get('overall_assessment', {}).get('ai_analysis_used', False)}")
        print(f"   Total AI Insights: {insights.get('overall_assessment', {}).get('total_ai_insights', 0)}")
        
        vuln_insights = insights.get("vulnerability_insights", [])
        if vuln_insights:
            print(f"\n   Vulnerability Insights: {len(vuln_insights)}")
            for insight in vuln_insights:
                print(f"      - {insight.get('package_name')}: {insight.get('assessment', 'N/A')}")
    else:
        print("\n⚠️ No agentic_insights section found in report")
    
    # Check if vulnerabilities have AI analysis
    vulns = clean_report.get("vulnerabilities", [])
    if vulns:
        print(f"\n   Vulnerabilities: {len(vulns)}")
        for vuln in vulns:
            if "🤖" in vuln.get("description", ""):
                print(f"      ✅ {vuln.get('vulnerability_id')}: Has AI analysis in description")
            else:
                print(f"      ⚠️ {vuln.get('vulnerability_id')}: No AI analysis in description")
    
    # Save report
    output_file = "outputs/test_clean_report_with_ai.json"
    with open(output_file, "w") as f:
        json.dump(clean_report, f, indent=2)
    
    print(f"\n✅ Clean report saved to: {output_file}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("\n✅ Tests completed!")
print("\nTo verify agentic output:")
print("  1. Check outputs/test_agentic_output.json for LLM analysis")
print("  2. Check outputs/test_clean_report_with_ai.json for agentic_insights section")
print("  3. Look for 🤖 emoji in vulnerability descriptions")
print("  4. Verify 'ai_analysis_used' is true in metadata")

print("\n🚀 If LLM analysis is present, agentic flow is working!")
print("=" * 80)
