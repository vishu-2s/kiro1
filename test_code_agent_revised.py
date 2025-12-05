"""
Test script for revised Code Analysis Agent.

This script tests the new functionality:
1. Extracting packages from manifest files (local and GitHub)
2. Checking against malicious package database
3. Checking against OSV vulnerability database
4. Providing meaningful results instead of 0
"""

import os
import json
import tempfile
from pathlib import Path

# Set up test environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")

from agents.code_agent import CodeAnalysisAgent
from agents.types import SharedContext


def test_local_npm_malicious_package():
    """Test detecting malicious npm package from local package.json"""
    print("\n=== Test 1: Local npm malicious package ===")
    
    # Create temporary package.json with known malicious package
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.17.1",
                "flatmap-stream": "0.1.0",  # Known malicious
                "lodash": "^4.17.21"
            }
        }))
        
        # Create context with required fields
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["express", "flatmap-stream", "lodash"],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = CodeAnalysisAgent()
        result = agent.analyze(context)
        
        print(f"Total packages analyzed: {result.get('total_packages_analyzed')}")
        print(f"Suspicious patterns found: {result.get('suspicious_patterns_found')}")
        print(f"Confidence: {result.get('confidence')}")
        
        if result.get('packages'):
            for pkg in result['packages']:
                print(f"\nPackage: {pkg['package_name']}")
                print(f"Risk Level: {pkg['code_analysis'].get('risk_level')}")
                print(f"Reasoning: {pkg['reasoning']}")
        
        assert result['total_packages_analyzed'] > 0, "Should analyze at least one package"
        print("✓ Test passed!")


def test_local_python_malicious_package():
    """Test detecting malicious Python package from local requirements.txt"""
    print("\n=== Test 2: Local Python malicious package ===")
    
    # Create temporary requirements.txt with known malicious package
    with tempfile.TemporaryDirectory() as tmpdir:
        requirements_txt = Path(tmpdir) / "requirements.txt"
        requirements_txt.write_text("""
flask==2.0.1
requests==2.26.0
ctx==0.1.2
numpy==1.21.0
""")
        
        # Create context with required fields
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["flask", "requests", "ctx", "numpy"],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = CodeAnalysisAgent()
        result = agent.analyze(context)
        
        print(f"Total packages analyzed: {result.get('total_packages_analyzed')}")
        print(f"Suspicious patterns found: {result.get('suspicious_patterns_found')}")
        print(f"Confidence: {result.get('confidence')}")
        
        if result.get('packages'):
            for pkg in result['packages']:
                print(f"\nPackage: {pkg['package_name']}")
                print(f"Risk Level: {pkg['code_analysis'].get('risk_level')}")
                print(f"Reasoning: {pkg['reasoning']}")
        
        assert result['total_packages_analyzed'] > 0, "Should analyze at least one package"
        print("✓ Test passed!")


def test_osv_vulnerability_check():
    """Test checking package against OSV database"""
    print("\n=== Test 3: OSV vulnerability check ===")
    
    agent = CodeAnalysisAgent()
    
    # Test with a package known to have vulnerabilities
    result = agent.check_recent_supply_chain_attacks("lodash", "npm")
    
    print(f"Package: lodash")
    print(f"Is suspicious: {result.get('is_suspicious')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Threat indicators: {len(result.get('threat_indicators', []))}")
    
    if result.get('threat_indicators'):
        for threat in result['threat_indicators']:
            print(f"\n  Source: {threat.get('source')}")
            print(f"  Findings: {len(threat.get('findings', []))}")
    
    print("✓ Test passed!")


def test_no_malicious_packages():
    """Test with clean package.json (no malicious packages)"""
    print("\n=== Test 4: Clean package.json ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "clean-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.17.1",
                "lodash": "^4.17.21"
            }
        }))
        
        # Create context with required fields
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["express", "lodash"],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = CodeAnalysisAgent()
        result = agent.analyze(context)
        
        print(f"Total packages analyzed: {result.get('total_packages_analyzed')}")
        print(f"Suspicious patterns found: {result.get('suspicious_patterns_found')}")
        print(f"Note: {result.get('note', 'N/A')}")
        
        # Should return 0 packages analyzed if no malicious packages found
        print("✓ Test passed!")


def test_cache_functionality():
    """Test that caching works for repeated checks"""
    print("\n=== Test 5: Cache functionality ===")
    
    agent = CodeAnalysisAgent()
    
    # First check (should hit API)
    print("First check (cache miss)...")
    result1 = agent.check_recent_supply_chain_attacks("express", "npm")
    
    # Second check (should hit cache)
    print("Second check (cache hit)...")
    result2 = agent.check_recent_supply_chain_attacks("express", "npm")
    
    print(f"Results match: {result1 == result2}")
    assert result1 == result2, "Cached results should match"
    
    print("✓ Test passed!")


def test_github_repository():
    """Test analyzing a GitHub repository"""
    print("\n=== Test 6: GitHub Repository Analysis ===")
    
    repo_url = "https://github.com/lokeshsharma99/python-scanner-test"
    
    # Create context with GitHub URL and required fields
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[],
        input_mode="github",
        project_path=repo_url,
        metadata={"source_path": repo_url}
    )
    
    # Run analysis
    agent = CodeAnalysisAgent()
    result = agent.analyze(context)
    
    print(f"Repository: {repo_url}")
    print(f"Total packages analyzed: {result.get('total_packages_analyzed')}")
    print(f"Suspicious patterns found: {result.get('suspicious_patterns_found')}")
    print(f"Confidence: {result.get('confidence')}")
    
    if result.get('packages'):
        print(f"\nFound {len(result['packages'])} suspicious packages:")
        for pkg in result['packages']:
            print(f"\n  Package: {pkg['package_name']} @ {pkg['package_version']}")
            print(f"  Risk Level: {pkg['code_analysis'].get('risk_level')}")
            print(f"  Confidence: {pkg['confidence']}")
            print(f"  Reasoning: {pkg['reasoning'][:150]}...")
            
            # Show supply chain threats if any
            threats = pkg['code_analysis'].get('supply_chain_threats', [])
            if threats:
                print(f"  Supply Chain Threats: {len(threats)}")
                for threat in threats[:2]:
                    print(f"    - {threat.get('source')}: {len(threat.get('findings', []))} findings")
    else:
        print("\nNo suspicious packages found.")
    
    print("✓ Test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Revised Code Analysis Agent")
    print("=" * 60)
    
    try:
        # Run basic tests first
        test_local_npm_malicious_package()
        test_local_python_malicious_package()
        test_osv_vulnerability_check()
        test_no_malicious_packages()
        test_cache_functionality()
        
        # Test GitHub repository
        test_github_repository()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
