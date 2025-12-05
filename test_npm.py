"""Test npm repository."""
from dotenv import load_dotenv
load_dotenv()

from agents.supply_chain_detector_agent import SupplyChainDetectorAgent
from agents.types import SharedContext

repo_url = "https://github.com/lokeshsharma99/nodejs-scanner-test"

print("=" * 70)
print(f"Testing: {repo_url}")
print("=" * 70)

context = SharedContext(
    initial_findings=[],
    dependency_graph={},
    packages=[],
    input_mode="github",
    project_path=repo_url,
    metadata={"source_path": repo_url}
)

agent = SupplyChainDetectorAgent()
result = agent.analyze(context)

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print(f"Risk Level: {result.get('risk_level')}")
print(f"Total Packages: {result.get('total_packages_checked')}")
print(f"Total Threats: {result.get('total_threats_found')}")
print(f"  - Malicious: {result.get('malicious_packages_found')}")
print(f"  - Vulnerabilities: {result.get('vulnerabilities_found')}")
print(f"  - Web Intelligence: {result.get('web_intelligence_found')}")

print("\nThreat Details:")
for t in result.get("threats_detected", []):
    severity = t.get('severity', 'unknown').upper()
    source = t.get('source', 'Unknown')
    pkg = t.get('package_name', 'Unknown')
    desc = t.get('description', '')[:60]
    print(f"  [{severity}] {pkg} - {source}")
    print(f"       {desc}...")
