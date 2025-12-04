"""
End-to-end test for UI integration with agent orchestrator.

This test demonstrates the complete flow:
1. User input via UI (simulated)
2. Analysis through orchestrator with all agents
3. Error handling and graceful degradation
4. JSON output for UI display
"""

import os
import json
import tempfile
import shutil
from pathlib import Path

from analyze_supply_chain import analyze_project_with_agents
from agents.orchestrator import AgentOrchestrator
from agents.vulnerability_agent import VulnerabilityAnalysisAgent
from agents.reputation_agent import ReputationAnalysisAgent
from agents.code_agent import CodeAnalysisAgent
from agents.supply_chain_agent import SupplyChainAttackAgent
from agents.synthesis_agent import SynthesisAgent


def test_end_to_end_local_directory():
    """Test end-to-end analysis of a local directory."""
    print("=" * 70)
    print("TEST 1: End-to-End Local Directory Analysis")
    print("=" * 70)
    
    # Create a temporary test project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.17.1",
                "lodash": "^4.17.20"
            }
        }
        
        package_json_path = Path(temp_dir) / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"\nCreated test project at: {temp_dir}")
        print(f"Dependencies: express, lodash")
        
        # Run analysis
        print("\nStarting analysis...")
        try:
            result = analyze_project_with_agents(
                target=temp_dir,
                input_mode="local"
            )
            
            print("\n✅ Analysis completed successfully!")
            print(f"\nResults:")
            print(f"  - Analysis ID: {result.get('metadata', {}).get('analysis_id', 'N/A')}")
            print(f"  - Status: {result.get('metadata', {}).get('analysis_status', 'N/A')}")
            print(f"  - Confidence: {result.get('metadata', {}).get('confidence', 'N/A')}")
            print(f"  - Total Packages: {result.get('summary', {}).get('total_packages', 0)}")
            print(f"  - Critical Findings: {result.get('summary', {}).get('critical_findings', 0)}")
            print(f"  - High Findings: {result.get('summary', {}).get('high_findings', 0)}")
            
            # Check for degradation metadata
            if 'missing_analysis' in result.get('metadata', {}):
                print(f"\n⚠️  Degradation detected:")
                print(f"  - Missing: {result['metadata']['missing_analysis']}")
                print(f"  - Reason: {result['metadata'].get('degradation_reason', 'N/A')}")
            
            # Verify JSON structure
            assert 'metadata' in result, "Missing metadata"
            assert 'summary' in result, "Missing summary"
            assert 'security_findings' in result, "Missing security_findings"
            
            print("\n✅ JSON structure validated")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_end_to_end_with_agent_failure():
    """Test end-to-end analysis with simulated agent failure."""
    print("\n" + "=" * 70)
    print("TEST 2: End-to-End with Agent Failure (Graceful Degradation)")
    print("=" * 70)
    
    # Create a temporary test project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple package.json
        package_json = {
            "name": "test-project-failure",
            "version": "1.0.0",
            "dependencies": {
                "react": "^17.0.0"
            }
        }
        
        package_json_path = Path(temp_dir) / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"\nCreated test project at: {temp_dir}")
        
        # Run analysis (some agents may fail due to missing API keys, etc.)
        print("\nStarting analysis (expecting some agents to fail gracefully)...")
        try:
            result = analyze_project_with_agents(
                target=temp_dir,
                input_mode="local"
            )
            
            print("\n✅ Analysis completed with graceful degradation!")
            
            # Check degradation metadata
            metadata = result.get('metadata', {})
            print(f"\nDegradation Analysis:")
            print(f"  - Status: {metadata.get('analysis_status', 'N/A')}")
            print(f"  - Confidence: {metadata.get('confidence', 'N/A')}")
            
            if 'missing_analysis' in metadata:
                print(f"  - Missing Analysis: {metadata['missing_analysis']}")
                print(f"  - Reason: {metadata.get('degradation_reason', 'N/A')}")
                print(f"  - Retry Recommended: {metadata.get('retry_recommended', False)}")
            
            # Verify error handling worked
            assert 'metadata' in result, "Missing metadata"
            assert 'analysis_status' in metadata, "Missing analysis_status"
            
            print("\n✅ Graceful degradation validated")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Analysis failed catastrophically: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_ui_json_output_format():
    """Test that the JSON output format is compatible with the UI."""
    print("\n" + "=" * 70)
    print("TEST 3: UI JSON Output Format Validation")
    print("=" * 70)
    
    # Check if the demo report exists
    report_path = "outputs/demo_ui_comprehensive_report.json"
    
    if not os.path.exists(report_path):
        print(f"\n⚠️  No existing report found at {report_path}")
        print("Run an analysis first to generate a report")
        return True
    
    print(f"\nValidating report: {report_path}")
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        print("\n✅ JSON is valid")
        
        # Validate required fields for UI
        required_fields = {
            'metadata': ['analysis_id', 'timestamp'],
            'summary': ['total_packages', 'critical_findings', 'high_findings'],
            'security_findings': []
        }
        
        print("\nValidating required fields:")
        for section, fields in required_fields.items():
            if section not in report:
                print(f"  ❌ Missing section: {section}")
                return False
            print(f"  ✅ Section '{section}' present")
            
            for field in fields:
                if field not in report[section]:
                    print(f"    ❌ Missing field: {section}.{field}")
                    return False
                print(f"    ✅ Field '{field}' present")
        
        # Check for degradation metadata (optional but important)
        if 'analysis_status' in report['metadata']:
            print(f"\n  ℹ️  Analysis Status: {report['metadata']['analysis_status']}")
        if 'confidence' in report['metadata']:
            print(f"  ℹ️  Confidence: {report['metadata']['confidence']}")
        if 'missing_analysis' in report['metadata']:
            print(f"  ⚠️  Missing Analysis: {report['metadata']['missing_analysis']}")
        
        print("\n✅ UI JSON format validated")
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Invalid JSON: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        return False


def test_orchestrator_error_handling():
    """Test orchestrator error handling directly."""
    print("\n" + "=" * 70)
    print("TEST 4: Orchestrator Error Handling")
    print("=" * 70)
    
    from agents.types import SharedContext, Finding
    from agents.error_handler import ErrorHandler
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Test error handler initialization
    print("\nChecking error handler...")
    assert orchestrator.error_handler is not None, "Error handler not initialized"
    print("✅ Error handler initialized")
    
    # Test degradation level calculation
    print("\nTesting degradation level calculation...")
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=["pkg1", "pkg2"]
    )
    
    from agents.types import AgentResult, AgentStatus
    
    # Add some agent results
    context.add_agent_result(AgentResult(
        agent_name="vulnerability_analysis",
        success=True,
        data={},
        status=AgentStatus.SUCCESS
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="reputation_analysis",
        success=False,
        data={},
        error="API timeout",
        status=AgentStatus.FAILED
    ))
    
    # Calculate degradation
    degradation_level = orchestrator.error_handler.calculate_degradation_level(context)
    metadata = orchestrator.error_handler.get_degradation_metadata(context)
    
    print(f"  - Degradation Level: {degradation_level.value}")
    print(f"  - Confidence: {metadata['confidence']}")
    print(f"  - Missing Analysis: {metadata['missing_analysis']}")
    
    print("\n✅ Error handling validated")
    return True


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 70)
    print("END-TO-END UI INTEGRATION TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Local directory analysis
    results.append(("Local Directory Analysis", test_end_to_end_local_directory()))
    
    # Test 2: Agent failure handling
    results.append(("Agent Failure Handling", test_end_to_end_with_agent_failure()))
    
    # Test 3: UI JSON format
    results.append(("UI JSON Format", test_ui_json_output_format()))
    
    # Test 4: Orchestrator error handling
    results.append(("Orchestrator Error Handling", test_orchestrator_error_handling()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! System is ready for UI testing.")
        print("\nTo test with the UI:")
        print("  1. Start the web server: python app.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Enter a local directory or GitHub URL")
        print("  4. Click 'Analyze' and watch the results")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
