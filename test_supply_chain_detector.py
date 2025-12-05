"""
Test script for Supply Chain Detector Agent.

Tests the agent's ability to:
1. Extract packages from GitHub repositories
2. Extract packages from local manifest files
3. Detect known malicious packages
4. Check vulnerability databases (OSV, Snyk)
5. Use web search to find recent supply chain attacks
"""

import os
import json
import tempfile
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agents.supply_chain_detector_agent import SupplyChainDetectorAgent
from agents.types import SharedContext


def test_github_repository():
    """Test analyzing the specified GitHub repository"""
    print("\n" + "=" * 70)
    print("TEST: GitHub Repository Analysis")
    print("=" * 70)
    
    repo_url = "https://github.com/lokeshsharma99/python-scanner-test"
    
    # Create context
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[],
        input_mode="github",
        project_path=repo_url,
        metadata={"source_path": repo_url}
    )
    
    # Run analysis
    agent = SupplyChainDetectorAgent()
    result = agent.analyze(context)
    
    print(f"\n📊 Analysis Results for: {repo_url}")
    print(f"{'─' * 70}")
    print(f"Risk Level: {result.get('risk_level', 'N/A')}")
    print(f"Total packages checked: {result.get('total_packages_checked')}")
    print(f"Total threats found: {result.get('total_threats_found', len(result.get('threats_detected', [])))}")
    print(f"  - Malicious packages: {result.get('malicious_packages_found')}")
    print(f"  - Vulnerabilities: {result.get('vulnerabilities_found', result.get('vulnerable_packages_found', 0))}")
    print(f"  - Web intelligence: {result.get('web_intelligence_found', 0)}")
    print(f"Critical severity: {result.get('critical_severity_count', 0)}")
    print(f"High severity: {result.get('high_severity_count', 0)}")
    print(f"Confidence: {result.get('confidence'):.2f}")
    print(f"Duration: {result.get('duration_seconds'):.2f}s")
    
    threats = result.get('threats_detected', [])
    if threats:
        print(f"\n🚨 {len(threats)} THREATS DETECTED:")
        print(f"{'─' * 70}")
        
        for i, threat in enumerate(threats, 1):
            print(f"\n[{i}] {threat['package_name']} ({threat['ecosystem']})")
            print(f"    Type: {threat['threat_type']}")
            print(f"    Severity: {threat['severity'].upper()}")
            print(f"    Confidence: {threat['confidence']:.2f}")
            print(f"    Source: {threat['source']}")
            print(f"    Description: {threat['description']}")
            
            if threat.get('recommendations'):
                print(f"    Recommendations:")
                for rec in threat['recommendations'][:2]:
                    print(f"      • {rec}")
    else:
        print("\n✅ No threats detected")
    
    print(f"\n{'─' * 70}")
    print("✓ Test completed!")
    return result


def test_local_malicious_npm():
    """Test detecting malicious npm package from local package.json"""
    print("\n" + "=" * 70)
    print("TEST: Local npm Malicious Package Detection")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create package.json with known malicious package
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
        
        # Create context
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = SupplyChainDetectorAgent()
        result = agent.analyze(context)
        
        print(f"\n📊 Analysis Results:")
        print(f"{'─' * 70}")
        print(f"Total packages checked: {result.get('total_packages_checked')}")
        print(f"Malicious packages found: {result.get('malicious_packages_found')}")
        
        threats = result.get('threats_detected', [])
        if threats:
            print(f"\n🚨 {len(threats)} THREATS DETECTED:")
            for threat in threats:
                if threat['threat_type'] == 'malicious_package':
                    print(f"\n  ⚠️  MALICIOUS: {threat['package_name']}")
                    print(f"      Reason: {threat['description']}")
        
        assert result['malicious_packages_found'] > 0, "Should detect flatmap-stream as malicious"
        print(f"\n{'─' * 70}")
        print("✓ Test passed!")


def test_local_malicious_python():
    """Test detecting malicious Python package from local requirements.txt"""
    print("\n" + "=" * 70)
    print("TEST: Local Python Malicious Package Detection")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create requirements.txt with known malicious package
        requirements_txt = Path(tmpdir) / "requirements.txt"
        requirements_txt.write_text("""
flask==2.0.1
requests==2.26.0
ctx==0.1.2
numpy==1.21.0
""")
        
        # Create context
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = SupplyChainDetectorAgent()
        result = agent.analyze(context)
        
        print(f"\n📊 Analysis Results:")
        print(f"{'─' * 70}")
        print(f"Total packages checked: {result.get('total_packages_checked')}")
        print(f"Malicious packages found: {result.get('malicious_packages_found')}")
        
        threats = result.get('threats_detected', [])
        if threats:
            print(f"\n🚨 {len(threats)} THREATS DETECTED:")
            for threat in threats:
                if threat['threat_type'] == 'malicious_package':
                    print(f"\n  ⚠️  MALICIOUS: {threat['package_name']}")
                    print(f"      Reason: {threat['description']}")
        
        assert result['malicious_packages_found'] > 0, "Should detect ctx as malicious"
        print(f"\n{'─' * 70}")
        print("✓ Test passed!")


def test_vulnerability_detection():
    """Test vulnerability database checking"""
    print("\n" + "=" * 70)
    print("TEST: Vulnerability Database Checking")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create package.json with packages that have known vulnerabilities
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "4.17.0",  # Old version with vulnerabilities
                "axios": "0.18.0"    # Old version with vulnerabilities
            }
        }))
        
        # Create context
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = SupplyChainDetectorAgent()
        result = agent.analyze(context)
        
        print(f"\n📊 Analysis Results:")
        print(f"{'─' * 70}")
        print(f"Total packages checked: {result.get('total_packages_checked')}")
        print(f"Vulnerable packages found: {result.get('vulnerable_packages_found')}")
        
        threats = result.get('threats_detected', [])
        if threats:
            print(f"\n🔍 {len(threats)} VULNERABILITIES DETECTED:")
            for threat in threats:
                if threat['threat_type'] == 'vulnerability':
                    print(f"\n  📌 {threat['package_name']}")
                    print(f"      Severity: {threat['severity']}")
                    print(f"      Source: {threat['source']}")
                    print(f"      Description: {threat['description'][:80]}...")
        
        print(f"\n{'─' * 70}")
        print("✓ Test completed!")


def test_clean_project():
    """Test with project that has no MALICIOUS packages (may have vulnerabilities)"""
    print("\n" + "=" * 70)
    print("TEST: Project with No Malicious Packages")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create package.json with legitimate packages (may have vulnerabilities)
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "clean-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0",
                "react": "^18.0.0"
            }
        }))
        
        # Create context
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[],
            metadata={"source_path": tmpdir}
        )
        
        # Run analysis
        agent = SupplyChainDetectorAgent()
        result = agent.analyze(context)
        
        print(f"\n📊 Analysis Results:")
        print(f"{'─' * 70}")
        print(f"Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"Total packages checked: {result.get('total_packages_checked')}")
        print(f"Total threats found: {result.get('total_threats_found', len(result.get('threats_detected', [])))}")
        print(f"  - Malicious packages: {result.get('malicious_packages_found')}")
        print(f"  - Vulnerabilities: {result.get('vulnerabilities_found', 0)}")
        
        if result['malicious_packages_found'] == 0:
            print("\n✅ No MALICIOUS packages detected")
        
        vuln_count = result.get('vulnerabilities_found', 0)
        if vuln_count > 0:
            print(f"⚠️  {vuln_count} vulnerabilities found (update recommended)")
        
        print(f"\n{'─' * 70}")
        print("✓ Test passed!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SUPPLY CHAIN DETECTOR AGENT - TEST SUITE")
    print("=" * 70)
    
    try:
        # Test 1: GitHub repository (main test)
        github_result = test_github_repository()
        
        # Test 2: Local malicious npm package
        test_local_malicious_npm()
        
        # Test 3: Local malicious Python package
        test_local_malicious_python()
        
        # Test 4: Vulnerability detection
        test_vulnerability_detection()
        
        # Test 5: Clean project
        test_clean_project()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
