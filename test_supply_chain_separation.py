"""
Test that supply chain and code analysis outputs are kept separate from rule-based findings.
"""

import json
from agents.output_restructure import OutputRestructurer


def test_supply_chain_separation():
    """Test that supply chain analysis is in its own section, separate from rule-based."""
    
    # Mock raw output with both rule-based and agent findings
    raw_output = {
        "metadata": {
            "analysis_id": "test_123",
            "timestamp": "2025-12-04T00:00:00"
        },
        "summary": {
            "total_packages": 10,
            "total_findings": 5,
            "critical_findings": 1,
            "high_findings": 2,
            "medium_findings": 2,
            "low_findings": 0
        },
        "security_findings": {
            "packages": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "findings": [
                        {
                            "type": "vulnerability",
                            "severity": "high",
                            "description": "OSV vulnerability",
                            "source": "sbom_tools"
                        }
                    ]
                }
            ]
        },
        "supply_chain_analysis": {
            "total_packages_analyzed": 2,
            "supply_chain_attacks_detected": 1,
            "packages": [
                {
                    "package_name": "suspicious-pkg",
                    "attack_likelihood": "high",
                    "supply_chain_indicators": [
                        {
                            "type": "maintainer_change",
                            "severity": "high",
                            "description": "Maintainer changed recently"
                        }
                    ],
                    "confidence": 0.85
                }
            ]
        },
        "code_analysis": {
            "total_packages_analyzed": 1,
            "total_code_issues_found": 2,
            "packages": [
                {
                    "package_name": "obfuscated-pkg",
                    "code_analysis": {
                        "obfuscation_detected": [
                            {
                                "technique": "base64_encoding",
                                "severity": "high"
                            }
                        ]
                    }
                }
            ]
        },
        "dependency_graph": {},
        "recommendations": {},
        "agent_insights": {},
        "performance_metrics": {}
    }
    
    # Restructure output
    restructurer = OutputRestructurer()
    result = restructurer.restructure_output(raw_output, input_mode="github", ecosystem="npm")
    
    # Verify structure
    assert "github_rule_based" in result, "Missing rule-based section"
    assert "supply_chain_analysis" in result, "Missing supply chain section"
    assert "code_analysis" in result, "Missing code analysis section"
    assert "dependency_graph" in result, "Missing dependency graph section"
    assert "llm_assessment" in result, "Missing LLM assessment section"
    
    # Verify rule-based section contains ONLY rule-based findings
    rule_based = result["github_rule_based"]
    assert rule_based["description"].startswith("Automated rule-based"), "Wrong description"
    assert "OSV API" in rule_based["description"], "Should mention OSV API"
    
    # Verify supply chain section is SEPARATE
    supply_chain = result["supply_chain_analysis"]
    assert supply_chain["applicable"] == True, "Supply chain should be applicable"
    assert supply_chain["source"] == "supply_chain_agent", "Wrong source"
    assert "SEPARATE from rule-based" in supply_chain["note"], "Should note separation"
    assert supply_chain["attacks_detected"] == 1, "Wrong attack count"
    assert len(supply_chain["packages"]) == 1, "Wrong package count"
    
    # Verify code analysis section is SEPARATE
    code_analysis = result["code_analysis"]
    assert code_analysis["applicable"] == True, "Code analysis should be applicable"
    assert code_analysis["source"] == "code_agent", "Wrong source"
    assert "SEPARATE from rule-based" in code_analysis["note"], "Should note separation"
    assert code_analysis["code_issues_found"] == 2, "Wrong issue count"
    
    # Verify original security_findings is preserved (for UI compatibility)
    assert "security_findings" in result, "Original security_findings should be preserved"
    assert len(result["security_findings"]["packages"]) == 1, "Should have rule-based findings"
    
    print("✅ All tests passed!")
    print("\n📊 JSON Structure:")
    print(json.dumps({
        "sections": list(result.keys()),
        "rule_based": {
            "description": rule_based["description"][:80] + "...",
            "detection_methods": list(rule_based.get("detection_methods", {}).keys())
        },
        "supply_chain": {
            "applicable": supply_chain["applicable"],
            "source": supply_chain["source"],
            "attacks_detected": supply_chain["attacks_detected"]
        },
        "code_analysis": {
            "applicable": code_analysis["applicable"],
            "source": code_analysis["source"],
            "issues_found": code_analysis["code_issues_found"]
        }
    }, indent=2))


if __name__ == "__main__":
    test_supply_chain_separation()
