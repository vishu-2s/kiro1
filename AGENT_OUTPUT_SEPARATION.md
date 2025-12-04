# Agent Output Separation - Design Document

## Problem Statement

Previously, supply chain and code analysis agent outputs were being mixed with rule-based findings in the `security_findings` section, causing confusion about which findings came from which source.

**Issue:** Users couldn't distinguish between:
- Rule-based findings (OSV API, malicious package databases)
- AI agent findings (supply chain analysis, code analysis)

## Solution: 5-Section JSON Structure

We now separate outputs into **5 distinct sections**:

### 1. `github_rule_based` - Rule-Based Security Analysis
**Source:** SBOM tools, OSV API, malicious package databases

**Contains:**
- OSV vulnerability checks
- Malicious package detection
- Typosquatting detection
- Pattern-based analysis

**Confidence:** 0.9 (highly reliable, deterministic)

```json
{
  "github_rule_based": {
    "description": "Automated rule-based security analysis using OSV API, malicious package databases, and pattern detection",
    "total_packages": 992,
    "packages_with_issues": 15,
    "total_issues": 39,
    "detection_methods": {
      "osv_api": "Checked all packages against OSV vulnerability database",
      "malicious_packages": "Scanned against known malicious package lists",
      "typosquatting": "Detected potential typosquatting attempts",
      "pattern_analysis": "Analyzed package patterns and behaviors"
    },
    "confidence": 0.9
  }
}
```

### 2. `dependency_graph` - Dependency Analysis
**Source:** npm/PyPI registry traversal

**Contains:**
- Circular dependencies
- Version conflicts
- Dependency depth analysis

```json
{
  "dependency_graph": {
    "applicable": true,
    "total_packages": 992,
    "circular_dependencies": {
      "count": 5,
      "details": [...]
    },
    "version_conflicts": {
      "count": 12,
      "details": [...]
    }
  }
}
```

### 3. `supply_chain_analysis` - AI-Powered Supply Chain Detection
**Source:** Supply Chain Agent (AI)

**Contains:**
- Maintainer history analysis
- Version timeline anomalies
- Publishing pattern detection
- Exfiltration pattern matching
- Known attack pattern correlation (Hulud, event-stream, etc.)

**Confidence:** 0.85 (AI-based, context-dependent)

```json
{
  "supply_chain_analysis": {
    "applicable": true,
    "description": "AI-powered supply chain attack detection analyzing maintainer changes, publishing patterns, and attack signatures",
    "total_packages_analyzed": 2,
    "attacks_detected": 1,
    "packages": [
      {
        "package_name": "suspicious-pkg",
        "attack_likelihood": "high",
        "supply_chain_indicators": [
          {
            "type": "maintainer_change",
            "severity": "high",
            "description": "Maintainer changed recently"
          }
        ],
        "attack_pattern_matches": [
          {
            "pattern_name": "Hulud-style Attack",
            "similarity": 0.75
          }
        ],
        "confidence": 0.85
      }
    ],
    "source": "supply_chain_agent",
    "note": "This is SEPARATE from rule-based findings - represents AI analysis of supply chain risks"
  }
}
```

### 4. `code_analysis` - AI-Powered Static Code Analysis
**Source:** Code Agent (AI)

**Contains:**
- Obfuscation detection
- Behavioral pattern analysis
- Suspicious code patterns
- Dynamic execution detection

**Confidence:** 0.85 (AI-based, pattern matching)

```json
{
  "code_analysis": {
    "applicable": true,
    "description": "AI-powered static code analysis detecting obfuscation, suspicious behaviors, and malicious patterns",
    "total_packages_analyzed": 1,
    "code_issues_found": 2,
    "packages": [
      {
        "package_name": "obfuscated-pkg",
        "code_analysis": {
          "obfuscation_detected": [
            {
              "technique": "base64_encoding",
              "severity": "high"
            }
          ],
          "behavioral_indicators": [
            {
              "behavior": "network_activity",
              "risk_level": "high"
            }
          ]
        }
      }
    ],
    "source": "code_agent",
    "note": "This is SEPARATE from rule-based findings - represents AI analysis of code patterns"
  }
}
```

### 5. `llm_assessment` - AI Risk Assessment & Recommendations
**Source:** Synthesis Agent (AI)

**Contains:**
- Overall risk assessment
- Common risks across all issues
- Prioritized recommendations
- Strategic guidance

```json
{
  "llm_assessment": {
    "description": "AI-powered risk assessment and strategic recommendations based on multi-agent analysis",
    "overall_risk_level": "high",
    "risk_score": 7.5,
    "common_risks": [
      {
        "type": "Critical Vulnerabilities",
        "description": "4 critical security vulnerabilities require immediate attention",
        "severity": "critical"
      }
    ],
    "recommendations": {
      "immediate_actions": [...],
      "short_term": [...],
      "long_term": [...]
    }
  }
}
```

## Key Benefits

### 1. Clear Source Attribution
Users can immediately see which findings came from:
- **Rule-based tools** (deterministic, high confidence)
- **AI agents** (contextual, medium-high confidence)

### 2. No Duplication
Each finding appears in exactly one section based on its source.

### 3. Confidence Transparency
- Rule-based: 0.9 (very reliable)
- AI agents: 0.85 (reliable but context-dependent)

### 4. Backward Compatibility
The original `security_findings` section is preserved for UI compatibility.

## Implementation Details

### Synthesis Agent Changes
```python
# OLD: Mixed everything together
security_findings = self._build_security_findings_from_agents(context, packages_data)

# NEW: Keep separate
security_findings = self._build_security_findings_from_rule_based(context)
supply_chain_data = self._extract_supply_chain_data(context)
code_analysis_data = self._extract_code_analysis_data(context)
```

### Output Restructurer Changes
```python
# NEW: 5 sections instead of 3
restructured = {
    "github_rule_based": self._build_rule_based_section(...),
    "dependency_graph": self._build_dependency_graph_section(...),
    "supply_chain_analysis": self._build_supply_chain_section(...),  # NEW
    "code_analysis": self._build_code_analysis_section(...),         # NEW
    "llm_assessment": self._build_llm_assessment_section(...)
}
```

## UI Integration

The UI can now display findings in separate tabs/sections:

1. **Security Findings** (Rule-Based) - OSV vulnerabilities, malicious packages
2. **Supply Chain Risks** (AI) - Maintainer changes, attack patterns
3. **Code Issues** (AI) - Obfuscation, suspicious behaviors
4. **Dependencies** - Circular deps, version conflicts
5. **Risk Assessment** (AI) - Overall risk and recommendations

## Testing

Run the test to verify separation:
```bash
python test_supply_chain_separation.py
```

Expected output:
```
✅ All tests passed!

📊 JSON Structure:
{
  "sections": [
    "metadata",
    "github_rule_based",      ← Rule-based findings
    "dependency_graph",       ← Dependency analysis
    "supply_chain_analysis",  ← AI supply chain detection
    "code_analysis",          ← AI code analysis
    "llm_assessment",         ← AI risk assessment
    "summary",
    "security_findings",      ← Preserved for compatibility
    "recommendations",
    "performance_metrics"
  ]
}
```

## Migration Notes

### For UI Developers
- **Old:** Read from `security_findings.packages[].findings[]`
- **New:** Read from appropriate section based on finding type:
  - Vulnerabilities → `github_rule_based`
  - Supply chain → `supply_chain_analysis`
  - Code issues → `code_analysis`

### For API Consumers
- All sections are available in the JSON output
- Original `security_findings` is preserved for backward compatibility
- New sections provide richer, source-attributed data

## Summary

✅ **Supply chain agent output is now SEPARATE from rule-based findings**
✅ **Code analysis agent output is now SEPARATE from rule-based findings**
✅ **Clear source attribution for all findings**
✅ **No duplication or confusion**
✅ **Backward compatible with existing UI**
