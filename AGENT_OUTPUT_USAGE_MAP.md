# Agent Output Usage Map

## Current Agent Output Flow

### 1. Vulnerability Agent
**Output:**
```json
{
  "packages": [
    {
      "package_name": "lodash",
      "vulnerabilities": [...],
      "vulnerability_count": 2
    }
  ],
  "total_packages_analyzed": 992,
  "total_vulnerabilities_found": 39
}
```

**Used In:**
- ✅ Merged into `security_findings.packages[].vulnerabilities`
- ✅ Displayed in Security Findings section
- ✅ Counted in severity breakdown
- ✅ Used for recommendations

**UI Display:** ✅ Prominent (main findings section)

---

### 2. Reputation Agent
**Output:**
```json
{
  "packages": [
    {
      "package_name": "unknown-pkg",
      "reputation_score": 0.2,
      "risk_level": "high",
      "risk_factors": [...]
    }
  ]
}
```

**Used In:**
- ✅ Merged into `security_findings.packages[].reputation_score`
- ✅ Used to calculate risk_level
- ⚠️ NOT prominently displayed in UI

**UI Display:** ⚠️ Hidden (only in package metadata)

---

### 3. Code Agent
**Output:**
```json
{
  "packages": [
    {
      "package_name": "suspicious-pkg",
      "code_issues": [...],
      "suspicious_patterns": [...]
    }
  ]
}
```

**Used In:**
- ✅ Merged into `security_findings.packages[].code_analysis`
- ⚠️ NOT displayed in UI

**UI Display:** ❌ Not shown

---

### 4. Supply Chain Agent
**Output:**
```json
{
  "packages": [
    {
      "package_name": "compromised-pkg",
      "is_malicious": true,
      "attack_indicators": [...],
      "attack_likelihood": "high"
    }
  ],
  "supply_chain_attacks_detected": 2
}
```

**Used In:**
- ✅ Merged into `security_findings.packages[].supply_chain_analysis`
- ✅ Used to count malicious packages
- ✅ Used in recommendations
- ⚠️ NOT prominently displayed in UI

**UI Display:** ❌ Not shown

---

### 5. Synthesis Agent
**Output:**
```json
{
  "metadata": {...},
  "summary": {...},
  "security_findings": {...},
  "recommendations": {...}
}
```

**Used In:**
- ✅ Final JSON output
- ✅ All sections displayed

**UI Display:** ✅ Fully displayed

---

## The Problem

**Supply Chain Agent output is buried:**
- Merged into package metadata
- Not shown in UI
- Users don't see supply chain attack detection results
- Valuable analysis is hidden

**Same for Code Agent:**
- Code analysis results are merged but not displayed
- Suspicious patterns not shown
- Users miss important insights

## Recommendation

### Option 1: Add to Security Findings
Show supply chain and code findings as separate finding types:

```
lodash v4.17.15
  1. Vulnerability (OSV API)
  2. Supply Chain Risk (Suspicious maintainer change)
  3. Code Issue (Obfuscated code detected)
```

### Option 2: Separate Section
Create dedicated sections:

```
Security Findings (39)
  - Vulnerabilities from OSV
  
Supply Chain Risks (2)
  - Compromised maintainer detected
  - Suspicious publishing pattern
  
Code Analysis (5)
  - Obfuscated code
  - Suspicious patterns
```

### Option 3: Enhanced Package Cards
Show all agent results in package cards:

```
lodash v4.17.15
  
  Vulnerabilities (2)
    - CVE-2021-1234
    - CVE-2021-5678
  
  Reputation Analysis
    - Score: 0.85 (Good)
    - Age: 5 years
  
  Supply Chain Analysis
    - No suspicious activity
  
  Code Analysis
    - No issues detected
```

## Current Usage in Synthesis

### Supply Chain Agent
```python
# Line 645-651 in synthesis_agent.py
sc_result = context.get_agent_result("SupplyChainAttackAgent")
if sc_result and sc_result.success:
    for pkg_data in sc_result.data.get("packages", []):
        pkg_name = pkg_data.get("package_name")
        if pkg_name in packages:
            packages[pkg_name]["supply_chain_analysis"] = pkg_data
```

**Result:** Data is merged but not surfaced

### Code Agent
```python
# Similar pattern - merged but not displayed
code_result = context.get_agent_result("CodeAnalysisAgent")
if code_result and code_result.success:
    for pkg_data in code_result.data.get("packages", []):
        packages[pkg_name]["code_analysis"] = pkg_data
```

**Result:** Data is merged but not surfaced

## Proposed Fix

### 1. Update Synthesis to Surface Agent Findings
Convert agent analysis into findings:

```python
# In synthesis_agent.py
def _convert_supply_chain_to_findings(pkg_data):
    """Convert supply chain analysis to findings."""
    findings = []
    
    if pkg_data.get("is_malicious"):
        findings.append({
            "type": "supply_chain_attack",
            "severity": "critical",
            "description": "Supply chain attack detected",
            "confidence": pkg_data.get("confidence", 0.8),
            "evidence": pkg_data.get("attack_indicators", []),
            "remediation": "Remove package immediately; Scan for compromise"
        })
    
    return findings
```

### 2. Update UI to Display All Finding Types
Already done - UI now supports any finding type

### 3. Update Output Restructurer
Add supply chain and code analysis to the 3 sections

## Status

**Current State:**
- ❌ Supply chain agent output is hidden
- ❌ Code agent output is hidden
- ✅ Vulnerability agent output is displayed
- ✅ Reputation agent output is partially displayed

**Needed:**
- Convert agent analysis to findings
- Surface in UI
- Include in restructured output

## Next Steps

1. Update synthesis to convert agent analysis to findings
2. Ensure findings include all agent results
3. Update restructured output to highlight agent findings
4. Test end-to-end to verify all agent outputs are visible

Would you like me to implement these changes to surface the supply chain and code agent outputs?
