"""Quick test for Supply Chain Detector with authentic sources."""
from dotenv import load_dotenv
load_dotenv()

from agents.supply_chain_detector_agent import SupplyChainDetectorAgent
from agents.types import SharedContext

repo_url = "https://github.com/lokeshsharma99/nodejs-scanner-test"
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

print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(f"Risk Level: {result.get('risk_level')}")
print(f"Total Packages: {result.get('total_packages_checked')}")
print(f"Total Threats: {result.get('total_threats_found')}")
print(f"  - Malicious: {result.get('malicious_packages_found')}")
print(f"  - Vulnerabilities: {result.get('vulnerabilities_found')}")
print(f"  - Web Intelligence: {result.get('web_intelligence_found')}")

print("\nThreat Details:")
for t in result.get("threats_detected", []):
    print(f"  [{t['severity'].upper()}] {t['package_name']} - {t['source']}")
    print(f"       {t['description'][:70]}...")
