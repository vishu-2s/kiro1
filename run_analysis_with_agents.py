"""
Run analysis with agents enabled to update demo_ui_comprehensive_report.json
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_supply_chain import analyze_project_hybrid

print("=" * 80)
print("RUNNING ANALYSIS WITH AGENTS ENABLED")
print("=" * 80)

target = "test_vuln_project"
print(f"\nTarget: {target}")
print("Agents: ENABLED")
print("Output: outputs/demo_ui_comprehensive_report.json")

try:
    output_path = analyze_project_hybrid(
        target=target,
        use_agents=True
    )
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Output: {output_path}")
    
    # Verify the output
    import json
    with open(output_path) as f:
        data = json.load(f)
    
    # Check if agents were used
    agent_enabled = data.get("metadata", {}).get("agent_analysis_enabled", False)
    synthesis_method = data.get("metadata", {}).get("synthesis_method", "unknown")
    
    print(f"\nAgent Analysis Enabled: {agent_enabled}")
    print(f"Synthesis Method: {synthesis_method}")
    
    # Check recommendations
    recommendations = data.get("recommendations", {})
    if isinstance(recommendations, dict):
        immediate = recommendations.get("immediate_actions", [])
        print(f"\nRecommendations:")
        print(f"  - Immediate actions: {len(immediate)}")
        
        if synthesis_method == "llm_enhanced":
            print("\n✅ SUCCESS: LLM recommendations generated!")
        else:
            print(f"\n⚠️  WARNING: Using {synthesis_method} recommendations")
    else:
        print(f"\n⚠️  Recommendations format: {type(recommendations)}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
