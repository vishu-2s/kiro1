"""Generate a comprehensive report for the preinstall script vulnerability"""
import json
import sys
from analyze_supply_chain import SupplyChainAnalyzer

# Initialize analyzer
analyzer = SupplyChainAnalyzer()

# Analyze the vulnerable folder
print("Analyzing vulnerable preinstall script folder...")
result = analyzer.analyze_local_directory(
    r'C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script'
)

# Convert to dict
result = result.__dict__ if hasattr(result, '__dict__') else result
if hasattr(result, 'metadata'):
    result = {
        'metadata': result.metadata.__dict__ if hasattr(result.metadata, '__dict__') else result.metadata,
        'summary': result.summary.__dict__ if hasattr(result.summary, '__dict__') else result.summary,
        'sbom_data': result.sbom_data,
        'security_findings': result.security_findings,
        'suspicious_activities': result.suspicious_activities,
        'recommendations': result.recommendations,
        'raw_data': result.raw_data
    }

# Save to the demo UI report file
output_path = 'outputs/demo_ui_comprehensive_report.json'
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n✅ Report generated: {output_path}")
print(f"Total findings: {result.get('summary', {}).get('total_findings', 0)}")
print(f"Critical: {result.get('summary', {}).get('critical_findings', 0)}")
print(f"High: {result.get('summary', {}).get('high_findings', 0)}")

# Show malicious script findings
if 'security_findings' in result and 'packages' in result['security_findings']:
    for pkg in result['security_findings']['packages']:
        if pkg.get('package_name') == 'vuln-preinstall':
            print(f"\n📦 Package: {pkg['package_name']}")
            if 'vulnerabilities' in pkg:
                print(f"   Vulnerabilities: {len(pkg.get('vulnerabilities', []))}")
            if 'malicious_scripts' in pkg:
                print(f"   Malicious scripts: {len(pkg.get('malicious_scripts', []))}")
                for script in pkg.get('malicious_scripts', []):
                    print(f"   - {script.get('severity', 'unknown').upper()}: {script.get('script_name', 'unknown')}")
