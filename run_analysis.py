"""Run analysis and check output."""
from analyze_supply_chain import analyze_supply_chain
import json

print("Starting analysis...")
result = analyze_supply_chain("https://github.com/lokeshsharma99/python-scanner-test", use_agents=True)
print("Analysis complete")

# Check supply chain data
sc_data = result.get("supply_chain_analysis", {})
print(f"\nSupply Chain Analysis:")
print(f"  Keys: {list(sc_data.keys()) if sc_data else 'Empty'}")

if sc_data:
    print(f"  Risk Level: {sc_data.get('risk_level')}")
    print(f"  Total Threats: {sc_data.get('total_threats_found')}")
    print(f"  Malicious: {sc_data.get('malicious_packages_found')}")
    print(f"  Web Intel: {sc_data.get('web_intelligence_found')}")

# Check agent insights
insights = result.get("agent_insights", {})
sc_summary = insights.get("supply_chain_detector", {})
print(f"\nAgent Insights - Supply Chain Detector:")
print(f"  {sc_summary}")
