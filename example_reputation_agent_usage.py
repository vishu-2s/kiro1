"""
Example usage of the Reputation Analysis Agent.

This script demonstrates how to use the ReputationAnalysisAgent to analyze
package trustworthiness by fetching metadata from npm and PyPI registries.
"""

from agents.reputation_agent import ReputationAnalysisAgent
from agents.types import SharedContext, Finding
import json


def example_npm_analysis():
    """Example: Analyze npm packages"""
    print("=" * 80)
    print("Example 1: Analyzing npm packages")
    print("=" * 80)
    
    # Create agent
    agent = ReputationAnalysisAgent()
    
    # Create context with npm packages
    context = SharedContext(
        initial_findings=[],
        dependency_graph={"packages": []},
        packages=["express", "lodash", "react"],
        ecosystem="npm"
    )
    
    # Analyze packages
    print("\nAnalyzing npm packages: express, lodash, react")
    print("-" * 80)
    
    result = agent.analyze(context, timeout=60)
    
    # Display results
    print(f"\nTotal packages analyzed: {result['total_packages_analyzed']}")
    print(f"High-risk packages: {result['high_risk_packages']}")
    print(f"Medium-risk packages: {result['medium_risk_packages']}")
    print(f"Overall confidence: {result['confidence']:.2f}")
    print(f"Duration: {result['duration_seconds']:.2f} seconds")
    
    # Display individual package results
    print("\nPackage Details:")
    print("-" * 80)
    for pkg in result['packages']:
        print(f"\nPackage: {pkg['package_name']}")
        print(f"  Reputation Score: {pkg.get('reputation_score', 0.0):.2f}")
        print(f"  Risk Level: {pkg.get('risk_level', 'unknown')}")
        print(f"  Confidence: {pkg.get('confidence', 0.0):.2f}")
        
        if 'factors' in pkg:
            print(f"  Factor Scores:")
            for factor, score in pkg['factors'].items():
                print(f"    - {factor}: {score:.2f}")
        
        if 'risk_factors' in pkg and pkg['risk_factors']:
            print(f"  Risk Factors:")
            for rf in pkg['risk_factors']:
                print(f"    - {rf['type']} ({rf['severity']}): {rf['description']}")
        
        if 'author_analysis' in pkg:
            author = pkg['author_analysis']
            print(f"  Author: {author.get('author_name', 'Unknown')}")
            print(f"  Verified: {author.get('is_verified', False)}")
            if author.get('suspicious_patterns'):
                print(f"  Suspicious Patterns: {', '.join(author['suspicious_patterns'])}")
        
        if 'reasoning' in pkg:
            print(f"  Reasoning: {pkg['reasoning']}")


def example_pypi_analysis():
    """Example: Analyze PyPI packages"""
    print("\n\n" + "=" * 80)
    print("Example 2: Analyzing PyPI packages")
    print("=" * 80)
    
    # Create agent
    agent = ReputationAnalysisAgent()
    
    # Create context with PyPI packages
    context = SharedContext(
        initial_findings=[],
        dependency_graph={"packages": []},
        packages=["requests", "numpy", "flask"],
        ecosystem="pypi"
    )
    
    # Analyze packages
    print("\nAnalyzing PyPI packages: requests, numpy, flask")
    print("-" * 80)
    
    result = agent.analyze(context, timeout=60)
    
    # Display results
    print(f"\nTotal packages analyzed: {result['total_packages_analyzed']}")
    print(f"High-risk packages: {result['high_risk_packages']}")
    print(f"Medium-risk packages: {result['medium_risk_packages']}")
    print(f"Overall confidence: {result['confidence']:.2f}")
    print(f"Duration: {result['duration_seconds']:.2f} seconds")
    
    # Display individual package results
    print("\nPackage Details:")
    print("-" * 80)
    for pkg in result['packages']:
        print(f"\nPackage: {pkg['package_name']}")
        print(f"  Reputation Score: {pkg.get('reputation_score', 0.0):.2f}")
        print(f"  Risk Level: {pkg.get('risk_level', 'unknown')}")
        
        if 'metadata_summary' in pkg:
            summary = pkg['metadata_summary']
            if 'version' in summary:
                print(f"  Version: {summary['version']}")
            if 'description' in summary:
                print(f"  Description: {summary['description'][:60]}...")


def example_single_package_analysis():
    """Example: Analyze a single package in detail"""
    print("\n\n" + "=" * 80)
    print("Example 3: Detailed analysis of a single package")
    print("=" * 80)
    
    # Create agent
    agent = ReputationAnalysisAgent()
    
    # Create context with a single package
    context = SharedContext(
        initial_findings=[],
        dependency_graph={"packages": []},
        packages=["express"],
        ecosystem="npm"
    )
    
    # Analyze package
    print("\nAnalyzing express package in detail")
    print("-" * 80)
    
    result = agent.analyze(context, timeout=30)
    
    # Display detailed results
    if result['packages']:
        pkg = result['packages'][0]
        
        print(f"\nPackage: {pkg['package_name']}")
        print(f"Ecosystem: {pkg.get('ecosystem', 'unknown')}")
        print(f"Reputation Score: {pkg.get('reputation_score', 0.0):.2f}")
        print(f"Risk Level: {pkg.get('risk_level', 'unknown')}")
        print(f"Confidence: {pkg.get('confidence', 0.0):.2f}")
        
        print("\nFactor Scores:")
        if 'factors' in pkg:
            for factor, score in pkg['factors'].items():
                print(f"  {factor}: {score:.2f}")
        
        print("\nRisk Factors:")
        if 'risk_factors' in pkg and pkg['risk_factors']:
            for rf in pkg['risk_factors']:
                print(f"  - Type: {rf['type']}")
                print(f"    Severity: {rf['severity']}")
                print(f"    Description: {rf['description']}")
                print(f"    Score: {rf['score']:.2f}")
        else:
            print("  No significant risk factors identified")
        
        print("\nAuthor Analysis:")
        if 'author_analysis' in pkg:
            author = pkg['author_analysis']
            print(f"  Author Name: {author.get('author_name', 'Unknown')}")
            print(f"  Verified: {author.get('is_verified', False)}")
            print(f"  Organization: {author.get('is_organization', False)}")
            print(f"  Maintainer Count: {author.get('maintainer_count', 0)}")
            if author.get('suspicious_patterns'):
                print(f"  Suspicious Patterns: {', '.join(author['suspicious_patterns'])}")
            else:
                print(f"  Suspicious Patterns: None")
        
        print("\nMetadata Summary:")
        if 'metadata_summary' in pkg:
            summary = pkg['metadata_summary']
            for key, value in summary.items():
                if value:
                    print(f"  {key}: {value}")
        
        print("\nReasoning:")
        if 'reasoning' in pkg:
            print(f"  {pkg['reasoning']}")


def example_with_cache():
    """Example: Demonstrate caching behavior"""
    print("\n\n" + "=" * 80)
    print("Example 4: Demonstrating cache behavior")
    print("=" * 80)
    
    # Create agent
    agent = ReputationAnalysisAgent()
    
    # Create context
    context = SharedContext(
        initial_findings=[],
        dependency_graph={"packages": []},
        packages=["lodash"],
        ecosystem="npm"
    )
    
    # First analysis (cache miss)
    print("\nFirst analysis (cache miss):")
    print("-" * 80)
    result1 = agent.analyze(context, timeout=30)
    print(f"Duration: {result1['duration_seconds']:.2f} seconds")
    
    # Second analysis (cache hit)
    print("\nSecond analysis (cache hit):")
    print("-" * 80)
    result2 = agent.analyze(context, timeout=30)
    print(f"Duration: {result2['duration_seconds']:.2f} seconds")
    
    print(f"\nSpeedup from caching: {result1['duration_seconds'] / result2['duration_seconds']:.2f}x")


def example_error_handling():
    """Example: Error handling for non-existent packages"""
    print("\n\n" + "=" * 80)
    print("Example 5: Error handling")
    print("=" * 80)
    
    # Create agent
    agent = ReputationAnalysisAgent()
    
    # Create context with non-existent package
    context = SharedContext(
        initial_findings=[],
        dependency_graph={"packages": []},
        packages=["this-package-definitely-does-not-exist-12345"],
        ecosystem="npm"
    )
    
    # Analyze package
    print("\nAnalyzing non-existent package:")
    print("-" * 80)
    
    result = agent.analyze(context, timeout=30)
    
    # Display results
    if result['packages']:
        pkg = result['packages'][0]
        print(f"\nPackage: {pkg['package_name']}")
        print(f"Error: {pkg.get('error', 'No error')}")
        print(f"Confidence: {pkg.get('confidence', 0.0):.2f}")
        print(f"Reasoning: {pkg.get('reasoning', 'N/A')}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("REPUTATION ANALYSIS AGENT - USAGE EXAMPLES")
    print("=" * 80)
    
    try:
        # Run examples
        example_npm_analysis()
        example_pypi_analysis()
        example_single_package_analysis()
        example_with_cache()
        example_error_handling()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
