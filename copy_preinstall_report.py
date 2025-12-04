"""Copy preinstall test results to demo UI report"""
import json
from tools.local_tools import analyze_local_directory

# Analyze the vulnerable folder
print("Analyzing vulnerable preinstall script folder...")
result = analyze_local_directory(
    r'C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script',
    use_osv=False
)

# Convert security findings to the format expected by UI
# The UI expects findings as individual vulnerability-like objects in a vulnerabilities array
security_findings_packages = []

# Group findings by package
findings_by_package = {}
for finding in result['security_findings']:
    pkg_name = finding['package']
    if pkg_name not in findings_by_package:
        findings_by_package[pkg_name] = {
            'package_name': pkg_name,
            'package_version': finding.get('version', '*'),
            'ecosystem': 'npm',
            'vulnerabilities': [],
            'confidence': 0.9,
            'reasoning': 'Malicious scripts detected in package.json'
        }
    
    if finding['finding_type'] == 'malicious_script':
        # Convert to vulnerability format for UI compatibility
        findings_by_package[pkg_name]['vulnerabilities'].append({
            'id': f"MALICIOUS-SCRIPT-{len(findings_by_package[pkg_name]['vulnerabilities']) + 1}",
            'summary': f"Malicious {finding['evidence'][0].split(': ')[1]} script detected",
            'details': '\n'.join(finding['evidence']),
            'severity': finding['severity'],
            'cvss_score': 9.5 if finding['severity'] == 'critical' else 7.5,
            'confidence': finding['confidence'],
            'recommendations': finding['recommendations'],
            'source': finding['source']
        })

security_findings_packages = list(findings_by_package.values())

# Create the report structure
report = {
    'metadata': {
        'analysis_id': f"analysis_{int(__import__('time').time())}",
        'analysis_type': 'local',
        'analysis_status': 'complete',
        'timestamp': result['analysis_start_time'],
        'target': r'C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script',
        'confidence': 0.95
    },
    'summary': result['summary'],
    'security_findings': {
        'packages': security_findings_packages
    },
    'recommendations': {
        'immediate_actions': [
            '🚨 CRITICAL: Malicious preinstall script detected',
            'DO NOT install this package',
            'Remove this package from your dependencies immediately',
            'Review your package.json for other suspicious scripts'
        ],
        'preventive_measures': [
            'Always review package.json scripts before installing',
            'Use --ignore-scripts flag when installing untrusted packages',
            'Enable npm audit in your CI/CD pipeline',
            'Use package lock files to prevent supply chain attacks'
        ],
        'monitoring': [
            'Monitor for unexpected network activity during npm install',
            'Check system logs for suspicious process execution',
            'Review installed packages regularly'
        ]
    }
}

# Save to demo UI report file
output_path = 'outputs/demo_ui_comprehensive_report.json'
with open(output_path, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✅ Report generated: {output_path}")
print(f"Total findings: {report['summary']['total_findings']}")
print(f"Critical: {report['summary']['critical_findings']}")
print(f"High: {report['summary']['high_findings']}")
print(f"\nMalicious scripts detected:")
for pkg in security_findings_packages:
    print(f"  📦 {pkg['package_name']}: {len(pkg['vulnerabilities'])} malicious scripts")
    for vuln in pkg['vulnerabilities']:
        print(f"     - {vuln['severity'].upper()}: {vuln['summary']}")
