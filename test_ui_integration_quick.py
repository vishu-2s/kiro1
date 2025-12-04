"""
Quick test to verify UI integration with orchestrator.
"""

import os
import json
import tempfile
from pathlib import Path

# Test the hybrid analysis function directly
from analyze_supply_chain import analyze_project_hybrid

def test_quick():
    """Quick test of hybrid analysis."""
    print("=" * 70)
    print("QUICK UI INTEGRATION TEST")
    print("=" * 70)
    
    # Create a temporary test project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.17.1"
            }
        }
        
        package_json_path = Path(temp_dir) / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"\nCreated test project at: {temp_dir}")
        print("Running hybrid analysis...")
        
        try:
            # Run analysis
            output_path = analyze_project_hybrid(
                target=temp_dir,
                input_mode="local",
                use_agents=True
            )
            
            print(f"\n✅ Analysis completed!")
            print(f"Output: {output_path}")
            
            # Load and check the output
            with open(output_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            print("\n📊 Result Structure:")
            print(f"  - Has metadata: {'metadata' in result}")
            print(f"  - Has summary: {'summary' in result}")
            print(f"  - Has security_findings: {'security_findings' in result}")
            
            # Check for orchestrator metadata
            metadata = result.get('metadata', {})
            print(f"\n🔍 Metadata Check:")
            print(f"  - analysis_status: {metadata.get('analysis_status', 'NOT FOUND')}")
            print(f"  - confidence: {metadata.get('confidence', 'NOT FOUND')}")
            
            # Check for performance metrics
            perf = result.get('performance_metrics', {})
            print(f"\n⚡ Performance Metrics:")
            print(f"  - total_duration_seconds: {perf.get('total_duration_seconds', 'NOT FOUND')}")
            print(f"  - agent_durations: {perf.get('agent_durations', 'NOT FOUND')}")
            
            # Check for agent insights
            if 'agent_insights' in result:
                print(f"\n🤖 Agent Insights Found!")
                print(f"  - Keys: {list(result['agent_insights'].keys())}")
            else:
                print(f"\n⚠️  No agent_insights found (might be using old format)")
            
            # Determine if this is orchestrator output
            is_orchestrator = (
                'analysis_status' in metadata or
                'agent_durations' in perf or
                'agent_insights' in result
            )
            
            if is_orchestrator:
                print(f"\n✅ OUTPUT IS FROM ORCHESTRATOR!")
            else:
                print(f"\n❌ OUTPUT IS FROM OLD SYSTEM!")
            
            return is_orchestrator
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = test_quick()
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED - Orchestrator is working!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("=" * 70)
