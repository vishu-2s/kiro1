# Agent Output Merge Fix

## Issue: Agent Outputs Not Properly Merged

### Problem
The fallback report was creating separate package entries for each agent's output instead of merging them by package name.

**Before Fix**:
```json
{
  "security_findings": {
    "packages": [
      {
        "package_name": "grunt",
        "vulnerabilities": [...]  // From vulnerability agent
      },
      {
        "package_name": "grunt",
        "reputation_score": 0.75  // From reputation agent (separate entry!)
      },
      {
        "package_name": "shelljs",
        "vulnerabilities": [...]
      },
      {
        "package_name": "shelljs",
        "reputation_score": 0.79
      }
    ]
  }
}
```

**Result**: 
- Duplicate package entries
- Vulnerability data separated from reputation data
- UI shows incomplete information per package
- Total package count inflated (10 instead of 5)

### Root Cause

The error handler was using `extend()` to add all agent packages to a flat list:

```python
for agent_name, result in context.agent_results.items():
    if result.success:
        agent_findings = result.data.get("packages", [])
        all_findings.extend(agent_findings)  # Just appends, no merging!
```

This created separate entries for each agent's view of the same package.

### Solution

Implemented proper package merging by package name:

```python
# Create dictionary keyed by package name
packages_dict = {}

for agent_name, result in context.agent_results.items():
    if result.success:
        agent_packages = result.data.get("packages", [])
        
        for pkg in agent_packages:
            pkg_name = pkg.get("package_name", "unknown")
            
            # Initialize package if not exists
            if pkg_name not in packages_dict:
                packages_dict[pkg_name] = {
                    "package_name": pkg_name,
                    "package_version": pkg.get("package_version"),
                    "ecosystem": pkg.get("ecosystem")
                }
            
            # Merge vulnerability data
            if "vulnerabilities" in pkg:
                packages_dict[pkg_name]["vulnerabilities"] = pkg["vulnerabilities"]
                packages_dict[pkg_name]["vulnerability_count"] = len(pkg["vulnerabilities"])
            
            # Merge reputation data
            if "reputation_score" in pkg:
                packages_dict[pkg_name]["reputation_score"] = pkg["reputation_score"]
                packages_dict[pkg_name]["risk_level"] = pkg["risk_level"]
                packages_dict[pkg_name]["risk_factors"] = pkg["risk_factors"]
            
            # Merge code analysis data
            if "code_issues" in pkg:
                packages_dict[pkg_name]["code_issues"] = pkg["code_issues"]
            
            # Merge supply chain data
            if "supply_chain_risks" in pkg:
                packages_dict[pkg_name]["supply_chain_risks"] = pkg["supply_chain_risks"]

# Convert to list
all_findings = list(packages_dict.values())
```

### After Fix

**Merged Output**:
```json
{
  "security_findings": {
    "packages": [
      {
        "package_name": "grunt",
        "package_version": "0.4.5",
        "ecosystem": "npm",
        "vulnerabilities": [
          {
            "id": "GHSA-j383-35pm-c5h4",
            "severity": "medium",
            "summary": "Path Traversal in Grunt"
          }
        ],
        "vulnerability_count": 3,
        "reputation_score": 0.75,
        "risk_level": "medium",
        "risk_factors": [...]
      },
      {
        "package_name": "shelljs",
        "package_version": "0.8.4",
        "ecosystem": "npm",
        "vulnerabilities": [...],
        "vulnerability_count": 5,
        "reputation_score": 0.79,
        "risk_level": "medium",
        "risk_factors": [...]
      }
    ]
  }
}
```

**Result**:
- ✅ Single entry per package
- ✅ All agent data merged together
- ✅ Complete information per package
- ✅ Correct package count (5 instead of 10)

### Summary Statistics Fix

Also updated the summary statistics calculation to count vulnerabilities correctly:

**Before**:
```python
# Counted packages by risk_level (reputation data)
high_count = sum(1 for f in all_findings if f.get("risk_level") == "high")
```

**After**:
```python
# Count vulnerabilities by severity
for pkg in all_findings:
    vulns = pkg.get("vulnerabilities", [])
    for vuln in vulns:
        severity = vuln.get("severity", "").lower()
        if severity == "critical":
            critical_count += 1
        elif severity == "high":
            high_count += 1
        # ... etc
```

### Benefits

1. **Accurate Data**: Each package shows complete information from all agents
2. **Correct Counts**: Package count reflects actual unique packages
3. **Better UI**: UI displays all data for each package in one place
4. **Proper Aggregation**: Vulnerabilities, reputation, code issues all merged
5. **Extensible**: Easy to add more agent data types

### Testing

**Before Fix**:
```bash
python -c "import json; data = json.load(open('outputs/demo_ui_comprehensive_report.json')); packages = data['security_findings']['packages']; print('Total packages:', len(packages)); print('First package has reputation:', 'reputation_score' in packages[0])"

# Output:
# Total packages: 10
# First package has reputation: False
```

**After Fix**:
```bash
python -c "import json; data = json.load(open('outputs/demo_ui_comprehensive_report.json')); packages = data['security_findings']['packages']; print('Total packages:', len(packages)); print('First package has reputation:', 'reputation_score' in packages[0])"

# Output:
# Total packages: 5
# First package has reputation: True
```

### Impact on UI

**Before**: 
- Package list showed duplicates
- Some packages only showed vulnerabilities
- Other entries only showed reputation
- Confusing for users

**After**:
- Each package appears once
- Shows all available data (vulnerabilities + reputation + more)
- Clear, complete information
- Professional presentation

## Conclusion

The orchestrator now properly merges agent outputs by package name, providing complete and accurate information in the final report. Each package entry contains all data from all agents that analyzed it.
