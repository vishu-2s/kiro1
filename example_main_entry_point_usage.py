"""
Example usage of the hybrid architecture main entry point.

This demonstrates how to use the new analyze_project_hybrid function
to analyze projects with both rule-based detection and agent analysis.
"""

import os
import json
from analyze_supply_chain import analyze_project_hybrid


def example_local_npm_project():
    """Example: Analyze a local npm project."""
    print("=" * 80)
    print("Example 1: Analyzing Local npm Project")
    print("=" * 80)
    
    # Analyze the test nested deps project
    project_path = "test_nested_deps"
    
    if not os.path.exists(project_path):
        print(f"Project not found: {project_path}")
        return
    
    print(f"\nAnalyzing: {project_path}")
    print("Input mode: auto-detect (will detect 'local')")
    print("Using agents: No (faster for demo)")
    
    # Run analysis
    output_path = analyze_project_hybrid(
        target=project_path,
        input_mode="auto",
        use_agents=False  # Disable agents for faster demo
    )
    
    print(f"\n✓ Analysis complete!")
    print(f"Output: {output_path}")
    
    # Load and display summary
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    metadata = report.get("metadata", {})
    summary = report.get("summary", {})
    
    print(f"\nAnalysis Type: {metadata.get('analysis_type', 'unknown')}")
    print(f"Ecosystem: {metadata.get('ecosystem', 'unknown')}")
    print(f"Target: {metadata.get('target', 'unknown')}")
    
    print(f"\nPackages Analyzed: {summary.get('total_packages', 0)}")
    print(f"Total Findings: {summary.get('total_findings', 0)}")
    print(f"  - Critical: {summary.get('critical_findings', 0)}")
    print(f"  - High: {summary.get('high_findings', 0)}")
    print(f"  - Medium: {summary.get('medium_findings', 0)}")
    print(f"  - Low: {summary.get('low_findings', 0)}")
    
    # Performance metrics
    perf = report.get("performance_metrics", {})
    print(f"\nPerformance:")
    print(f"  Total Time: {perf.get('total_analysis_time', 0):.2f}s")
    
    print("\n")


def example_local_python_project():
    """Example: Analyze a local Python project."""
    print("=" * 80)
    print("Example 2: Analyzing Local Python Project")
    print("=" * 80)
    
    # Create a temporary Python project for demo
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix="python_demo_")
    
    try:
        # Create requirements.txt
        requirements_path = os.path.join(temp_dir, "requirements.txt")
        with open(requirements_path, 'w') as f:
            f.write("requests==2.28.0\n")
            f.write("flask==2.3.0\n")
        
        print(f"\nCreated demo project: {temp_dir}")
        print("Input mode: local")
        print("Using agents: No (faster for demo)")
        
        # Run analysis
        output_path = analyze_project_hybrid(
            target=temp_dir,
            input_mode="local",
            use_agents=False
        )
        
        print(f"\n✓ Analysis complete!")
        print(f"Output: {output_path}")
        
        # Load and display summary
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        
        metadata = report.get("metadata", {})
        summary = report.get("summary", {})
        
        print(f"\nAnalysis Type: {metadata.get('analysis_type', 'unknown')}")
        print(f"Ecosystem: {metadata.get('ecosystem', 'unknown')}")
        
        print(f"\nPackages Analyzed: {summary.get('total_packages', 0)}")
        print(f"Total Findings: {summary.get('total_findings', 0)}")
        
        # Performance metrics
        perf = report.get("performance_metrics", {})
        print(f"\nPerformance:")
        print(f"  Total Time: {perf.get('total_analysis_time', 0):.2f}s")
        
        print("\n")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_with_agents():
    """Example: Analyze with full agent analysis."""
    print("=" * 80)
    print("Example 3: Analyzing with Full Agent Analysis")
    print("=" * 80)
    
    # Create a temporary project for demo
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix="agent_demo_")
    
    try:
        # Create package.json
        package_json_path = os.path.join(temp_dir, "package.json")
        with open(package_json_path, 'w') as f:
            json.dump({
                "name": "demo-project",
                "version": "1.0.0",
                "dependencies": {
                    "lodash": "^4.17.21",
                    "express": "^4.18.0"
                }
            }, f, indent=2)
        
        print(f"\nCreated demo project: {temp_dir}")
        print("Input mode: auto-detect")
        print("Using agents: Yes (full analysis)")
        
        # Run analysis with agents
        output_path = analyze_project_hybrid(
            target=temp_dir,
            input_mode="auto",
            use_agents=True  # Enable full agent analysis
        )
        
        print(f"\n✓ Analysis complete!")
        print(f"Output: {output_path}")
        
        # Load and display summary
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        
        metadata = report.get("metadata", {})
        summary = report.get("summary", {})
        
        print(f"\nAnalysis Type: {metadata.get('analysis_type', 'unknown')}")
        print(f"Agent Analysis: {metadata.get('agent_analysis_enabled', False)}")
        
        print(f"\nPackages Analyzed: {summary.get('total_packages', 0)}")
        print(f"Total Findings: {summary.get('total_findings', 0)}")
        
        # Performance metrics
        perf = report.get("performance_metrics", {})
        print(f"\nPerformance:")
        print(f"  Total Time: {perf.get('total_analysis_time', 0):.2f}s")
        print(f"  Rule-Based Time: {perf.get('rule_based_time', 0):.2f}s")
        print(f"  Agent Time: {perf.get('agent_time', 0):.2f}s")
        
        # Agent insights
        if "agent_insights" in report:
            print("\nAgent Insights:")
            insights = report["agent_insights"]
            for key, value in insights.items():
                print(f"  {key}: {value}")
        
        print("\n")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "HYBRID ARCHITECTURE EXAMPLES" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    # Example 1: Local npm project
    example_local_npm_project()
    
    # Example 2: Local Python project
    example_local_python_project()
    
    # Example 3: With full agent analysis
    example_with_agents()
    
    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Input mode auto-detection (GitHub URL vs local path)")
    print("  ✓ Ecosystem detection (npm vs Python)")
    print("  ✓ Rule-based detection (fast, deterministic)")
    print("  ✓ Agent analysis (intelligent, adaptive)")
    print("  ✓ Performance metrics collection")
    print("  ✓ Backward compatibility (fixed output filename)")
    print("\n")


if __name__ == "__main__":
    main()
