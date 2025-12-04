"""
Verify that synthesis agent LLM integration works end-to-end.
"""

import sys
import json
from pathlib import Path

print("=" * 80)
print("VERIFYING SYNTHESIS AGENT LLM INTEGRATION")
print("=" * 80)

# Check test output
test_output = Path("outputs/test_llm_recommendations.json")

if not test_output.exists():
    print("\n❌ Test output not found!")
    print(f"   Expected: {test_output}")
    sys.exit(1)

print(f"\n✅ Test output found: {test_output}")

# Load and verify
with open(test_output) as f:
    data = json.load(f)

# Check synthesis method
synthesis_method = data.get("metadata", {}).get("synthesis_method")
print(f"\nSynthesis Method: {synthesis_method}")

if synthesis_method == "llm_enhanced":
    print("✅ LLM synthesis is working!")
elif synthesis_method == "rule_based":
    print("⚠️  Using rule-based fallback (LLM failed)")
else:
    print(f"❓ Unknown synthesis method: {synthesis_method}")

# Check recommendations structure
recommendations = data.get("recommendations", {})
if isinstance(recommendations, dict):
    immediate = recommendations.get("immediate_actions", [])
    short_term = recommendations.get("short_term", [])
    long_term = recommendations.get("long_term", [])
    
    print(f"\n✅ Recommendations structure is correct:")
    print(f"   - Immediate actions: {len(immediate)}")
    print(f"   - Short-term actions: {len(short_term)}")
    print(f"   - Long-term actions: {len(long_term)}")
    
    if immediate and short_term and long_term:
        print("\n✅ All recommendation categories populated")
    else:
        print("\n⚠️  Some recommendation categories are empty")
else:
    print(f"\n❌ Recommendations are not in dict format: {type(recommendations)}")

# Check LLM analysis
llm_analysis = data.get("agent_insights", {}).get("llm_analysis")
if llm_analysis:
    print(f"\n✅ LLM analysis present:")
    print(f"   {llm_analysis[:100]}...")
else:
    print("\n⚠️  No LLM analysis found")

# Check risk assessment
risk_assessment = data.get("agent_insights", {}).get("risk_assessment", {})
overall_risk = risk_assessment.get("overall_risk")
risk_score = risk_assessment.get("risk_score", 0)
reasoning = risk_assessment.get("reasoning", "")

if overall_risk and reasoning:
    print(f"\n✅ Risk assessment present:")
    print(f"   - Overall Risk: {overall_risk}")
    print(f"   - Risk Score: {risk_score:.2f}")
    print(f"   - Reasoning: {reasoning[:100]}...")
else:
    print("\n⚠️  Risk assessment incomplete")

# Final verdict
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

checks = {
    "Synthesis method is llm_enhanced": synthesis_method == "llm_enhanced",
    "Recommendations are structured": isinstance(recommendations, dict),
    "All recommendation categories present": bool(immediate and short_term and long_term),
    "LLM analysis present": bool(llm_analysis),
    "Risk assessment complete": bool(overall_risk and reasoning)
}

passed = sum(checks.values())
total = len(checks)

for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check}")

print(f"\nPassed: {passed}/{total}")

if passed == total:
    print("\n🎉 ALL CHECKS PASSED - LLM INTEGRATION WORKING!")
    sys.exit(0)
elif passed >= 3:
    print("\n⚠️  MOSTLY WORKING - Some issues detected")
    sys.exit(0)
else:
    print("\n❌ FAILED - LLM integration not working properly")
    sys.exit(1)
