"""
Example usage of the AgentOrchestrator with the hybrid architecture.

This example demonstrates how to:
1. Create specialized agents
2. Register them with the orchestrator
3. Run a complete multi-agent analysis
4. Handle the results

This is a minimal example using mock agents. In production, you would
use real agents that integrate with LLMs and external APIs.
"""

from agents import (
    AgentOrchestrator,
    MockAgent,
    Finding,
    SharedContext
)


def main():
    """Run a simple orchestration example."""
    
    print("=" * 60)
    print("Agent Orchestrator Example")
    print("=" * 60)
    print()
    
    # Step 1: Create the orchestrator
    print("Step 1: Creating orchestrator...")
    orchestrator = AgentOrchestrator()
    print(f"✓ Orchestrator created (max time: {orchestrator.max_total_time}s)")
    print()
    
    # Step 2: Create mock agents for each stage
    print("Step 2: Creating mock agents...")
    
    # Vulnerability analysis agent
    vuln_agent = MockAgent(
        name="vulnerability_analysis",
        mock_data={
            "packages": [
                {
                    "name": "lodash",
                    "version": "4.17.20",
                    "vulnerabilities": [
                        {
                            "id": "CVE-2021-23337",
                            "severity": "high",
                            "cvss_score": 7.5,
                            "description": "Prototype pollution vulnerability",
                            "confidence": 0.95
                        }
                    ]
                }
            ]
        }
    )
    
    # Reputation analysis agent
    rep_agent = MockAgent(
        name="reputation_analysis",
        mock_data={
            "packages": [
                {
                    "name": "lodash",
                    "version": "4.17.20",
                    "reputation_score": 0.9,
                    "age_days": 3650,
                    "downloads_per_week": 50000000,
                    "risk_factors": []
                }
            ]
        }
    )
    
    # Synthesis agent
    synth_agent = MockAgent(
        name="synthesis",
        mock_data={
            "metadata": {
                "analysis_id": "example_001",
                "timestamp": "2024-01-01T00:00:00",
                "analysis_type": "comprehensive"
            },
            "summary": {
                "total_packages": 1,
                "critical_findings": 0,
                "high_findings": 1,
                "medium_findings": 0,
                "low_findings": 0
            },
            "security_findings": {
                "packages": [
                    {
                        "name": "lodash",
                        "version": "4.17.20",
                        "risk_level": "high",
                        "vulnerabilities": [
                            {
                                "id": "CVE-2021-23337",
                                "severity": "high",
                                "description": "Prototype pollution vulnerability"
                            }
                        ],
                        "reputation": {
                            "score": 0.9,
                            "assessment": "Well-established package"
                        }
                    }
                ]
            },
            "recommendations": {
                "immediate_actions": [
                    "Update lodash to version 4.17.21 or later"
                ],
                "preventive_measures": [
                    "Enable automated dependency updates"
                ],
                "monitoring": [
                    "Monitor for new vulnerabilities in lodash"
                ]
            }
        }
    )
    
    print("✓ Created 3 mock agents")
    print()
    
    # Step 3: Register agents with orchestrator
    print("Step 3: Registering agents...")
    orchestrator.register_agent("vulnerability_analysis", vuln_agent)
    orchestrator.register_agent("reputation_analysis", rep_agent)
    orchestrator.register_agent("synthesis", synth_agent)
    print("✓ Registered all agents")
    print()
    
    # Step 4: Create initial findings (from rule-based detection)
    print("Step 4: Creating initial findings...")
    initial_findings = [
        Finding(
            package_name="lodash",
            package_version="4.17.20",
            finding_type="vulnerability",
            severity="high",
            description="Potential CVE-2021-23337",
            detection_method="rule_based",
            confidence=0.8
        )
    ]
    print(f"✓ Created {len(initial_findings)} initial findings")
    print()
    
    # Step 5: Create dependency graph
    print("Step 5: Creating dependency graph...")
    dependency_graph = {
        "root": {
            "name": "my-project",
            "version": "1.0.0",
            "dependencies": {
                "lodash": {
                    "name": "lodash",
                    "version": "4.17.20",
                    "depth": 1,
                    "dependencies": {}
                }
            }
        }
    }
    print("✓ Created dependency graph")
    print()
    
    # Step 6: Run orchestration
    print("Step 6: Running orchestration...")
    print("-" * 60)
    
    result = orchestrator.orchestrate(
        initial_findings=initial_findings,
        dependency_graph=dependency_graph,
        input_mode="local",
        project_path="/path/to/project",
        ecosystem="npm"
    )
    
    print("-" * 60)
    print()
    
    # Step 7: Display results
    print("Step 7: Analysis Results")
    print("=" * 60)
    print()
    
    print(f"Analysis ID: {result['metadata']['analysis_id']}")
    print(f"Total Packages: {result['summary']['total_packages']}")
    print(f"High Findings: {result['summary']['high_findings']}")
    print()
    
    print("Performance Metrics:")
    print(f"  Total Duration: {result['performance_metrics']['total_duration_seconds']:.2f}s")
    print(f"  Stages Completed: {result['performance_metrics']['stages_completed']}")
    print(f"  Stages Failed: {result['performance_metrics']['stages_failed']}")
    print()
    
    print("Agent Durations:")
    for agent_name, duration in result['performance_metrics']['agent_durations'].items():
        print(f"  {agent_name}: {duration:.2f}s")
    print()
    
    print("Recommendations:")
    for action in result['recommendations']['immediate_actions']:
        print(f"  • {action}")
    print()
    
    print("=" * 60)
    print("✓ Orchestration complete!")
    print()
    
    # Step 8: Show output file location
    print(f"Report saved to: {orchestrator.output_dir}/demo_ui_comprehensive_report.json")
    print()


if __name__ == "__main__":
    main()
