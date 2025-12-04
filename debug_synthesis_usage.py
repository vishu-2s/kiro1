"""
Debug script to check if synthesis agent is using LLM or fallback.
"""

import os
from dotenv import load_dotenv
from agents.synthesis_agent import SynthesisAgent
from agents.types import SharedContext, AgentResult, Finding

load_dotenv()

print("=" * 80)
print("DEBUGGING SYNTHESIS AGENT LLM USAGE")
print("=" * 80)

# Create a small test context (< 50 packages to trigger LLM)
test_packages = ["express", "lodash", "axios"]
test_findings = [
    Finding(
        package_name="express",
        package_version="4.18.0",
        finding_type="vulnerability",
        severity="high",
        description="Test vulnerability",
        confidence=0.9,
        evidence=["Test evidence"],
        remediation="Update to latest version"
    )
]

context = SharedContext(
    initial_findings=test_findings,
    dependency_graph={"nodes": [], "edges": []},
    packages=test_packages,
    input_mode="local",
    project_path="/test",
    ecosystem="npm"
)

# Add mock agent results
context.add_agent_result(AgentResult(
    agent_name="VulnerabilityAnalysisAgent",
    success=True,
    data={
        "packages": [
            {
                "package_name": "express",
                "package_version": "4.18.0",
                "vulnerabilities": [
                    {
                        "id": "CVE-2024-TEST",
                        "severity": "high",
                        "description": "Test vulnerability"
                    }
                ]
            }
        ],
        "total_packages_analyzed": 1,
        "total_vulnerabilities_found": 1
    },
    duration_seconds=1.0,
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
                "risk_level": "low"
            }
        ],
        "total_packages_analyzed": 1
    },
    duration_seconds=1.0,
    confidence=0.9
))

print(f"\nTest Context:")
print(f"  Packages: {len(context.packages)}")
print(f"  Findings: {len(context.initial_findings)}")
print(f"  Agent Results: {len(context.agent_results)}")

print("\n" + "=" * 80)
print("RUNNING SYNTHESIS AGENT")
print("=" * 80)

agent = SynthesisAgent()
result = agent.analyze(context, timeout=10)

print(f"\nResult:")
print(f"  Success: {result.get('success')}")
print(f"  Synthesis Method: {result.get('synthesis_method')}")
print(f"  Duration: {result.get('duration_seconds', 0):.2f}s")

if result.get('synthesis_method') == 'llm':
    print("\n✅ LLM SYNTHESIS WAS USED!")
elif result.get('synthesis_method') == 'fallback':
    print("\n⚠️  FALLBACK WAS USED (LLM failed or timed out)")
    if 'error' in result:
        print(f"  Error: {result['error']}")
elif result.get('synthesis_method') == 'fast_fallback':
    print("\n⚠️  FAST FALLBACK WAS USED (too many packages)")

print("\n" + "=" * 80)
print("TESTING WITH LARGE DATASET (>50 packages)")
print("=" * 80)

# Create context with >50 packages
large_packages = [f"package-{i}" for i in range(60)]
large_context = SharedContext(
    initial_findings=[],
    dependency_graph={"nodes": [], "edges": []},
    packages=large_packages,
    input_mode="local",
    project_path="/test",
    ecosystem="npm"
)

print(f"\nLarge Context:")
print(f"  Packages: {len(large_context.packages)}")

result2 = agent.analyze(large_context, timeout=10)

print(f"\nResult:")
print(f"  Success: {result2.get('success')}")
print(f"  Synthesis Method: {result2.get('synthesis_method')}")
print(f"  Duration: {result2.get('duration_seconds', 0):.2f}s")

if result2.get('synthesis_method') == 'fast_fallback':
    print("\n✅ CORRECTLY SKIPPED LLM FOR LARGE DATASET")
else:
    print("\n⚠️  UNEXPECTED: LLM was attempted for large dataset")

print("\n" + "=" * 80)
