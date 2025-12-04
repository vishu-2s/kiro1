"""Test preinstall script detection in local folder"""
from tools.local_tools import analyze_local_directory

# Test the vulnerable folder
result = analyze_local_directory(
    r'C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script',
    use_osv=False
)

print(f"Total findings: {result['summary']['total_findings']}")
print(f"Script findings: {result['summary']['script_findings']}")

malicious_scripts = [f for f in result['security_findings'] if f['finding_type'] == 'malicious_script']
print(f"\nMalicious script findings: {len(malicious_scripts)}")

for finding in malicious_scripts:
    print(f"\n- Severity: {finding['severity']}")
    print(f"  Package: {finding['package']}")
    print(f"  Evidence:")
    for evidence in finding['evidence']:
        print(f"    {evidence}")
