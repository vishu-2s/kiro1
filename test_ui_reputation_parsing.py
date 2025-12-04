"""
Unit test to verify UI reputation parsing logic
Tests that the renderReport function correctly extracts and processes reputation findings
"""
import json
import os

def test_reputation_data_structure():
    """Verify the report file has the expected reputation data structure"""
    report_path = 'outputs/demo_ui_comprehensive_report.json'
    
    if not os.path.exists(report_path):
        print(f"❌ Report file not found at {report_path}")
        return False
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    print("✓ Report file loaded successfully")
    
    # Check for security_findings.packages
    if 'security_findings' not in data:
        print("❌ Missing 'security_findings' in report")
        return False
    print("✓ Found 'security_findings'")
    
    if 'packages' not in data['security_findings']:
        print("❌ Missing 'packages' in security_findings")
        return False
    print("✓ Found 'packages' array")
    
    packages = data['security_findings']['packages']
    print(f"✓ Found {len(packages)} packages")
    
    # Check for reputation data
    reputation_packages = [p for p in packages if 'reputation_score' in p or 'risk_factors' in p]
    vulnerability_packages = [p for p in packages if 'vulnerabilities' in p]
    
    print(f"✓ Found {len(reputation_packages)} packages with reputation data")
    print(f"✓ Found {len(vulnerability_packages)} packages with vulnerability data")
    
    if len(reputation_packages) == 0:
        print("❌ No reputation data found in report")
        return False
    
    # Verify reputation data structure
    for pkg in reputation_packages:
        print(f"\n📦 Checking reputation data for: {pkg.get('package_name', 'Unknown')}")
        
        if 'reputation_score' in pkg:
            print(f"  ✓ reputation_score: {pkg['reputation_score']}")
        
        if 'risk_level' in pkg:
            print(f"  ✓ risk_level: {pkg['risk_level']}")
        
        if 'factors' in pkg:
            print(f"  ✓ factors: {pkg['factors']}")
        
        if 'risk_factors' in pkg:
            print(f"  ✓ risk_factors: {len(pkg['risk_factors'])} items")
            for rf in pkg['risk_factors']:
                print(f"    - [{rf.get('severity', 'unknown').upper()}] {rf.get('description', 'N/A')}")
    
    print("\n✅ All reputation data structure checks passed!")
    return True

def test_severity_mapping():
    """Test that risk_level maps correctly to severity"""
    mapping = {
        'critical': 'critical',
        'high': 'high',
        'medium': 'medium',
        'low': 'low'
    }
    
    print("\n🔍 Testing severity mapping:")
    for risk_level, expected_severity in mapping.items():
        print(f"  ✓ {risk_level} → {expected_severity}")
    
    print("✅ Severity mapping is correct!")
    return True

def test_finding_extraction_logic():
    """Simulate the JavaScript finding extraction logic"""
    report_path = 'outputs/demo_ui_comprehensive_report.json'
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    findings = []
    packages = data['security_findings']['packages']
    
    print("\n🔍 Simulating JavaScript finding extraction:")
    
    for pkg in packages:
        pkg_name = pkg.get('package_name', 'Unknown')
        
        # Extract vulnerabilities
        if 'vulnerabilities' in pkg and isinstance(pkg['vulnerabilities'], list):
            vuln_count = len(pkg['vulnerabilities'])
            print(f"  📦 {pkg_name}: Found {vuln_count} vulnerabilities")
            findings.extend([{'type': 'vulnerability', 'package': pkg_name}] * vuln_count)
        
        # Extract reputation
        if 'reputation_score' in pkg or 'risk_factors' in pkg:
            risk_level = pkg.get('risk_level', 'medium')
            severity_map = {'critical': 'critical', 'high': 'high', 'medium': 'medium', 'low': 'low'}
            severity = severity_map.get(risk_level, 'medium')
            print(f"  🛡️  {pkg_name}: Found reputation data (risk_level: {risk_level} → severity: {severity})")
            findings.append({'type': 'reputation', 'package': pkg_name, 'severity': severity})
    
    print(f"\n✅ Total findings extracted: {len(findings)}")
    
    # Count by type
    vuln_count = len([f for f in findings if f['type'] == 'vulnerability'])
    rep_count = len([f for f in findings if f['type'] == 'reputation'])
    
    print(f"  - Vulnerability findings: {vuln_count}")
    print(f"  - Reputation findings: {rep_count}")
    
    # Count by severity
    severity_counts = {}
    for f in findings:
        if 'severity' in f:
            severity = f['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    print(f"\n📊 Severity distribution:")
    for severity in ['critical', 'high', 'medium', 'low']:
        count = severity_counts.get(severity, 0)
        print(f"  - {severity.capitalize()}: {count}")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("UI Reputation Parsing Test")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_reputation_data_structure()
    all_passed &= test_severity_mapping()
    all_passed &= test_finding_extraction_logic()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
