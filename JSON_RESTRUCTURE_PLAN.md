# JSON Output Restructuring Plan

## Objective

Restructure the analysis output JSON into 3 clear, well-organized sections while maintaining UI compatibility.

## New JSON Structure

```json
{
  "metadata": {
    "analysis_id": "analysis_123",
    "timestamp": "2025-12-04T00:00:00",
    "input_mode": "github|local",
    "ecosystem": "npm",
    "analysis_version": "2.0"
  },
  
  "github_rule_based": {
    "description": "Automated rule-based security analysis",
    "total_packages": 992,
    "packages_analyzed": 992,
    "packages_with_issues": 15,
    "total_issues": 39,
    "severity_breakdown": {
      "critical": 4,
      "high": 21,
      "medium": 10,
      "low": 4
    },
    "finding_types": {
      "vulnerability": 35,
      "malicious_package": 2,
      "typosquat": 2
    },
    "detection_methods": {
      "osv_api": "Checked all packages against OSV vulnerability database",
      "malicious_packages": "Scanned against known malicious package lists",
      "typosquatting": "Detected potential typosquatting attempts",
      "pattern_analysis": "Analyzed package patterns and behaviors"
    },
    "confidence": 0.9,
    "agent_analysis_enabled": false
  },
  
  "dependency_graph": {
    "applicable": true|false,
    "reason": "Only for GitHub mode",
    "description": "Complete dependency graph analysis",
    "total_packages": 715,
    "circular_dependencies": {
      "count": 5,
      "details": [...],
      "severity": "medium",
      "impact": "Can cause installation issues"
    },
    "version_conflicts": {
      "count": 146,
      "details": [...],
      "severity": "medium",
      "impact": "Multiple versions increase bundle size"
    },
    "dependency_depth": {
      "max_depth": 10,
      "description": "Maximum depth of dependency tree"
    },
    "ecosystem": "npm"
  },
  
  "llm_assessment": {
    "description": "AI-powered risk assessment and recommendations",
    "overall_risk_level": "high",
    "risk_score": 7.5,
    "common_risks": [
      {
        "type": "Critical Vulnerabilities",
        "description": "4 critical security vulnerabilities require immediate attention",
        "severity": "critical",
        "impact": "Potential for severe security breaches"
      },
      {
        "type": "High-Severity Issues",
        "description": "21 high-severity security issues detected",
        "severity": "high",
        "impact": "Significant security risks"
      }
    ],
    "recommendations": {
      "immediate_actions": [
        "Review 4 critical findings",
        "Address 21 high-severity findings"
      ],
      "short_term": [
        "Implement dependency scanning in CI/CD",
        "Use lock files for reproducible builds"
      ],
      "long_term": [
        "Regularly update dependencies",
        "Monitor security advisories"
      ],
      "best_practices": [
        "Use semantic versioning",
        "Minimize dependency count"
      ]
    },
    "strategic_guidance": "URGENT: 4 critical vulnerabilities require immediate remediation...",
    "agent_analysis": {
      "enabled": false,
      "agents_run": 0,
      "agents_failed": 0,
      "confidence": 0.9
    }
  },
  
  // Keep original sections for UI compatibility
  "summary": {...},
  "security_findings": {...},
  "recommendations": {...},
  "performance_metrics": {...}
}
```

## Section 1: github_rule_based

### Purpose
Contains results from automated rule-based security analysis.

### Data Sources
- OSV API vulnerability checks
- Malicious package database
- Typosquatting detection
- Pattern-based analysis

### Key Fields
- `total_packages`: Total packages scanned
- `packages_analyzed`: Packages actually analyzed
- `packages_with_issues`: Packages with findings
- `total_issues`: Total security issues found
- `severity_breakdown`: Count by severity (critical, high, medium, low)
- `finding_types`: Count by type (vulnerability, malicious, typosquat)
- `detection_methods`: Description of methods used
- `confidence`: Confidence level (0.9 for rule-based)
- `agent_analysis_enabled`: Whether AI agents ran

### User Value
- Clear summary of what was found
- Understand detection methods
- See severity distribution
- Know confidence level

## Section 2: dependency_graph

### Purpose
Provides dependency graph analysis results.

### Conditional Logic
**GitHub Mode:**
- `applicable: true`
- Full dependency graph with circular deps and version conflicts

**Local Mode:**
- `applicable: false`
- `reason`: "Only available for GitHub repositories"
- `recommendation`: "Analyze a GitHub repository for full insights"

### Key Fields (GitHub Mode)
- `total_packages`: Total in dependency graph
- `circular_dependencies`: Count, details, severity, impact
- `version_conflicts`: Count, details, severity, impact
- `dependency_depth`: Maximum depth of tree
- `ecosystem`: Package ecosystem

### User Value
- Understand dependency complexity
- Identify circular dependencies
- See version conflicts
- Know when analysis is not applicable

## Section 3: llm_assessment

### Purpose
AI-powered risk assessment and strategic recommendations.

### Data Sources
- Multi-agent analysis (if enabled)
- Synthesis of all findings
- Risk scoring algorithms
- Strategic guidance generation

### Key Fields
- `overall_risk_level`: critical|high|medium|low
- `risk_score`: Numerical score (0-10)
- `common_risks`: Top 5 risks across all issues
- `recommendations`: Prioritized by timeframe
  - `immediate_actions`: Do now
  - `short_term`: Do this sprint
  - `long_term`: Ongoing monitoring
  - `best_practices`: General guidance
- `strategic_guidance`: Executive summary
- `agent_analysis`: Status of AI agents

### User Value
- Understand overall risk
- Get prioritized actions
- See strategic guidance
- Know what to do next

## Implementation

### New Module: `agents/output_restructure.py`

**Class:** `OutputRestructurer`

**Main Method:** `restructure_output(raw_output, input_mode, ecosystem)`

**Helper Methods:**
- `_build_rule_based_section()`: Build section 1
- `_build_dependency_graph_section()`: Build section 2
- `_build_llm_assessment_section()`: Build section 3
- `_extract_common_risks()`: Extract top risks
- `_build_prioritized_recommendations()`: Prioritize recommendations
- `_calculate_overall_risk()`: Calculate risk level
- `_calculate_risk_score()`: Calculate numerical score
- `_generate_strategic_guidance()`: Generate guidance text

### Integration Point: `agents/orchestrator.py`

**Location:** After synthesis, before writing output

```python
# Restructure output into 3 clear sections
restructurer = OutputRestructurer()
final_json = restructurer.restructure_output(
    final_json,
    input_mode=context.input_mode,
    ecosystem=context.ecosystem
)
```

## Backward Compatibility

### UI Compatibility
- Original sections (`summary`, `security_findings`, `recommendations`) are preserved
- UI continues to work without changes
- New sections are additive, not replacing

### Data Preservation
- All original data is retained
- New sections provide organized views
- No information is lost

## Benefits

### For Users
1. **Clear organization**: 3 distinct sections
2. **Easy to understand**: Each section has clear purpose
3. **Actionable**: Prioritized recommendations
4. **Context-aware**: Different for GitHub vs local

### For Developers
1. **Clean structure**: Well-organized JSON
2. **Extensible**: Easy to add new sections
3. **Maintainable**: Clear separation of concerns
4. **Testable**: Each section can be tested independently

## Risk Scoring Algorithm

### Formula
```python
score = (critical * 10) + (high * 5) + (medium * 2) + (low * 0.5)
normalized = min(10, (score / 100) * 10)
```

### Risk Levels
- **Critical (9-10)**: Immediate action required
- **High (7-8.9)**: Address promptly
- **Medium (4-6.9)**: Plan remediation
- **Low (0-3.9)**: Monitor and maintain

## Testing

### Test Case 1: GitHub Mode with Findings
```python
input_mode = "github"
summary = {
    "total_packages": 992,
    "critical_findings": 4,
    "high_findings": 21
}
dependency_graph = {
    "metadata": {"total_packages": 715},
    "circular_dependencies": [...]
}
```

**Expected:**
- Section 1: Full rule-based results
- Section 2: Full dependency graph (applicable: true)
- Section 3: High risk level, prioritized recommendations

### Test Case 2: Local Mode
```python
input_mode = "local"
summary = {"total_packages": 100}
```

**Expected:**
- Section 1: Full rule-based results
- Section 2: Not applicable message
- Section 3: Risk assessment based on findings

### Test Case 3: No Findings
```python
summary = {
    "total_packages": 50,
    "total_findings": 0
}
```

**Expected:**
- Section 1: Clean results, no issues
- Section 2: Depends on mode
- Section 3: Low risk, maintenance recommendations

## Future Enhancements

1. **Trend Analysis**: Compare with previous scans
2. **Compliance Mapping**: Map findings to compliance frameworks
3. **Cost Estimation**: Estimate remediation effort
4. **Priority Scoring**: ML-based priority scoring
5. **Integration Hooks**: Webhooks for CI/CD integration

## Status

✅ **Implemented**
- Created `OutputRestructurer` class
- Integrated with orchestrator
- Maintains backward compatibility
- Ready for testing

## Next Steps

1. Run analysis to generate new JSON structure
2. Verify UI still works with new structure
3. Review new sections for clarity
4. Gather user feedback
5. Iterate on improvements
