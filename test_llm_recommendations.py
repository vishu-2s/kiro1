"""
Test LLM-powered recommendations in synthesis agent.
"""

import os
import json
from dotenv import load_dotenv
from agents.synthesis_agent import SynthesisAgent
from agents.types import SharedContext, AgentResult, Finding

load_dotenv()

print("=" * 80)
print("TESTING LLM-POWERED RECOMMENDATIONS")
print("=" * 80)

# Create realistic test context with findings
test_packages = ["express", "lodash", "axios", "moment", "request"]
test_findings = [
    Finding(
        package_name="express",
        package_version="4.17.1",
        finding_type="vulnerability",
        severity="critical",
        description="Prototype pollution vulnerability",
        confidence=0.95,
        evidence=["CVE-2022-24999"],
        remediation="Update to express@4.18.2 or later"
    ),
    Finding(
        package_name="moment",
        package_version="2.29.1",
        finding_type="vulnerability",
        severity="high",
        description="Regular expression denial of service",
        confidence=0.85,
        evidence=["CVE-2022-31129"],
        remediation="Replace with date-fns or dayjs"
    ),
    Finding(
        package_name="request",
        package_version="2.88.2",
        finding_type="deprecated_package",
        severity="medium",
        description="Package is deprecated and no longer maintained",
        confidence=0.99,
        evidence=["Deprecated since 2020"],
        remediation="Replace with axios or node-fetch"
    )
]

context = SharedContext(
    initial_findings=test_findings,
    dependency_graph={
        "nodes": [
            {"name": "express", "version": "4.17.1"},
            {"name": "lodash", "version": "4.17.21"},
            {"name": "axios", "version": "0.27.2"},
            {"name": "moment", "version": "2.29.1"},
            {"name": "request", "version": "2.88.2"}
        ],
        "edges": [],
        "metadata": {"total_packages": 5}
    },
    packages=test_packages,
    input_mode="local",
    project_path="/test/project",
    ecosystem="npm"
)

# Add realistic agent results
context.add_agent_result(AgentResult(
    agent_name="VulnerabilityAnalysisAgent",
    success=True,
    data={
        "packages": [
            {
                "package_name": "express",
                "package_version": "4.17.1",
                "vulnerabilities": [
                    {
                        "id": "CVE-2022-24999",
                        "severity": "critical",
                        "description": "Prototype pollution in qs dependency"
                    }
                ],
                "vulnerability_count": 1
            },
            {
                "package_name": "moment",
                "package_version": "2.29.1",
                "vulnerabilities": [
                    {
                        "id": "CVE-2022-31129",
                        "severity": "high",
                        "description": "ReDoS vulnerability"
                    }
                ],
                "vulnerability_count": 1
            }
        ],
        "total_packages_analyzed": 5,
        "total_vulnerabilities_found": 2,
        "confidence": 0.9
    },
    duration_seconds=2.5,
    confidence=0.9
))

context.add_agent_result(AgentResult(
    agent_name="ReputationAnalysisAgent",
    success=True,
    data={
        "packages": [
            {
                "package_name": "express",
                "reputation_score": 0.95,
                "risk_level": "low",
                "downloads_per_week": 25000000
            },
            {
                "package_name": "request",
                "reputation_score": 0.45,
                "risk_level": "medium",
                "downloads_per_week": 5000000,
                "deprecated": True
            }
        ],
        "total_packages_analyzed": 5,
        "confidence": 0.85
    },
    duration_seconds=1.8,
    confidence=0.85
))

context.add_agent_result(AgentResult(
    agent_name="SupplyChainAttackAgent",
    success=True,
    data={
        "packages": [],
        "supply_chain_attacks_detected": 0,
        "total_packages_analyzed": 5,
        "confidence": 0.8
    },
    duration_seconds=3.2,
    confidence=0.8
))

print(f"\nTest Context:")
print(f"  Packages: {len(context.packages)}")
print(f"  Findings: {len(context.initial_findings)}")
print(f"  Agent Results: {len(context.agent_results)}")
print(f"  Critical Findings: 1")
print(f"  High Findings: 1")
print(f"  Medium Findings: 1")

print("\n" + "=" * 80)
print("RUNNING SYNTHESIS WITH LLM RECOMMENDATIONS")
print("=" * 80)

agent = SynthesisAgent()
result = agent.analyze(context, timeout=20)

print(f"\nSynthesis Result:")
print(f"  Synthesis Method: {result.get('metadata', {}).get('synthesis_method', 'unknown')}")
print(f"  Duration: {result.get('metadata', {}).get('synthesis_duration', 0):.2f}s")

# Check recommendations
recommendations = result.get("recommendations", {})
print(f"\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if isinstance(recommendations, dict):
    immediate = recommendations.get("immediate_actions", [])
    short_term = recommendations.get("short_term", [])
    long_term = recommendations.get("long_term", [])
    
    print(f"\nImmediate Actions ({len(immediate)}):")
    for i, action in enumerate(immediate, 1):
        print(f"  {i}. {action}")
    
    print(f"\nShort-Term Actions ({len(short_term)}):")
    for i, action in enumerate(short_term, 1):
        print(f"  {i}. {action}")
    
    print(f"\nLong-Term Actions ({len(long_term)}):")
    for i, action in enumerate(long_term, 1):
        print(f"  {i}. {action}")
else:
    print("\n⚠️  Recommendations are not in expected format")
    print(f"Type: {type(recommendations)}")

# Check LLM analysis
llm_analysis = result.get("agent_insights", {}).get("llm_analysis")
if llm_analysis:
    print(f"\n" + "=" * 80)
    print("LLM ANALYSIS")
    print("=" * 80)
    print(f"\n{llm_analysis}")

# Check risk assessment
risk_assessment = result.get("agent_insights", {}).get("risk_assessment", {})
print(f"\n" + "=" * 80)
print("RISK ASSESSMENT")
print("=" * 80)
print(f"  Overall Risk: {risk_assessment.get('overall_risk', 'unknown')}")
print(f"  Risk Score: {risk_assessment.get('risk_score', 0):.2f}")
print(f"  Reasoning: {risk_assessment.get('reasoning', 'N/A')}")
print(f"  Confidence: {risk_assessment.get('confidence', 0):.2f}")

# Save output for inspection
output_path = "outputs/test_llm_recommendations.json"
os.makedirs("outputs", exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n" + "=" * 80)
print(f"Full output saved to: {output_path}")
print("=" * 80)

# Determine success
synthesis_method = result.get('metadata', {}).get('synthesis_method', 'unknown')
if synthesis_method == 'llm_enhanced':
    print("\n✅ SUCCESS: LLM recommendations were generated!")
elif synthesis_method == 'rule_based':
    print("\n⚠️  WARNING: Fell back to rule-based recommendations")
else:
    print(f"\n❓ UNKNOWN: synthesis_method = {synthesis_method}")
