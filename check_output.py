import json

with open('outputs/demo_ui_comprehensive_report.json', encoding='utf-8') as f:
    data = json.load(f)

packages = data.get('security_findings', {}).get('packages', [])
print(f'Packages: {len(packages)}')

for pkg in packages:
    pkg_name = pkg.get('package_name', 'unknown')
    vulns = pkg.get('vulnerabilities', [])
    print(f'  - {pkg_name}: {len(vulns)} vulnerabilities')
    for vuln in vulns[:2]:  # Show first 2
        print(f'    • {vuln.get("id", "N/A")}: {vuln.get("severity", "unknown")}')
