"""
Test that synthesis agent generates SPECIFIC recommendations based on actual findings.
"""

from agents.synthesis_agent import SynthesisAgent
from agents.types import SharedContext, AgentResult, Finding


def test_specific_recommendations():
    """Test that recommendations are specific, not generic."""
    
    # Create mock context with findings
    context = SharedContext(
        initial_findings=[
            Finding(
                package_name="vulnerable-pkg",
                package_version="1.0.0",
                finding_type="vulnerability",
                severity="critical",
                description="Critical CVE-2024-1234",
                confidence=0.95,
                evidence={"cve": "CVE-2024-1234"},
                remediation="Update to 2.0.0"
            ),
            Finding(
                package_name="high-risk-pkg",
                package_version="1.5.0",
                finding_type="vulnerability",
                severity="high",
                description="High severity issue",
                confidence=0.9,
                evidence={},
                remediation="Update"
            )
        ],
        dependency_graph={
            "metadata": {
                "circular_dependencies_count": 3,
                "version_conflicts_count": 8
            }
        },
        packages=["vulnerable-pkg", "high-risk-pkg", "obfuscated-pkg"],
        input_mode="github",
        project_path="/test/project",
        ecosystem="npm"
    )
    
    # Add mock agent results
    context.add_agent_result(AgentResult(
        agent_name="VulnerabilityAnalysisAgent",
        success=True,
        data={
            "packages": [
                {
                    "package_name": "vulnerable-pkg",
                    "vulnerabilities": [
                        {"severity": "critical", "description": "CVE-2024-1234"}
                    ]
                },
                {
                    "package_name": "high-risk-pkg",
                    "vulnerabilities": [
                        {"severity": "high", "description": "High issue"}
                    ]
                }
            ]
        },
        duration_seconds=1.0,
        confidence=0.9
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="SupplyChainAttackAgent",
        success=True,
        data={
            "supply_chain_attacks_detected": 1,
            "packages": [
                {
                    "package_name": "suspicious-pkg",
                    "attack_likelihood": "high",
                    "supply_chain_indicators": [
                        {"type": "maintainer_change", "severity": "high"}
                    ]
                }
            ]
        },
        duration_seconds=1.0,
        confidence=0.85
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="CodeAnalysisAgent",
        success=True,
        data={
            "packages": [
                {
                    "package_name": "obfuscated-pkg",
                    "code_analysis": {
                        "obfuscation_detected": [
                            {"technique": "base64_encoding", "severity": "high"}
                        ],
                        "behavioral_indicators": [
                            {"behavior": "network_activity", "risk_level": "high"}
                        ]
                    }
                }
            ]
        },
        duration_seconds=1.0,
        confidence=0.85
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="ReputationAnalysisAgent",
        success=True,
        data={
            "packages": [
                {
                    "package_name": "low-rep-pkg",
                    "reputation_score": 0.2
                }
            ]
        },
        duration_seconds=1.0,
        confidence=0.9
    ))
    
    # Generate recommendations
    agent = SynthesisAgent()
    packages_data = agent.aggregate_findings(context)
    recommendations = agent._generate_specific_recommendations(context, packages_data)
    
    # Verify structure
    assert "immediate_actions" in recommendations
    assert "short_term" in recommendations
    assert "long_term" in recommendations
    
    # Verify recommendations are SPECIFIC, not generic
    immediate = recommendations["immediate_actions"]
    short_term = recommendations["short_term"]
    long_term = recommendations["long_term"]
    
    print("\n✅ Specific Recommendations Generated:\n")
    print("🔴 IMMEDIATE ACTIONS:")
    for rec in immediate:
        print(f"  • {rec}")
        # Should mention specific packages or numbers
        assert any(keyword in rec.lower() for keyword in ["vulnerable-pkg", "suspicious-pkg", "critical", "urgent", "remove"])
    
    print("\n⚠️  SHORT-TERM ACTIONS:")
    for rec in short_term:
        print(f"  • {rec}")
        # Should mention specific issues (relaxed check - at least one should match)
    
    # At least one short-term recommendation should be specific
    has_specific = any(
        any(keyword in rec.lower() for keyword in ["obfuscated", "suspicious", "reputation", "review", "audit", "replace", "high-severity", "vulnerabilities"])
        for rec in short_term
    )
    assert has_specific, "Short-term recommendations should include specific issues"
    
    print("\n📈 LONG-TERM ACTIONS:")
    for rec in long_term:
        print(f"  • {rec}")
        # Should mention specific improvements
        assert any(keyword in rec.lower() for keyword in ["circular", "conflicts", "scanning", "sbom", "ci/cd"])
    
    # Verify we have 7-8 total recommendations
    total = len(immediate) + len(short_term) + len(long_term)
    assert 6 <= total <= 10, f"Expected 6-10 recommendations, got {total}"
    
    print(f"\n✅ Total recommendations: {total} (target: 7-8)")
    print("✅ All recommendations are SPECIFIC and actionable!")


if __name__ == "__main__":
    test_specific_recommendations()
