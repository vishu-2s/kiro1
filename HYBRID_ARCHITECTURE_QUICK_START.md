# Hybrid Architecture Quick Start Guide

## Overview

The hybrid architecture combines fast rule-based detection with intelligent multi-agent analysis for comprehensive security scanning.

## Quick Start

### Basic Usage

```python
from analyze_supply_chain import analyze_project_hybrid

# Analyze a local project (auto-detect ecosystem)
output_path = analyze_project_hybrid("path/to/project")

# Analyze a GitHub repository
output_path = analyze_project_hybrid("https://github.com/user/repo")
```

### Advanced Usage

```python
# Specify input mode explicitly
output_path = analyze_project_hybrid(
    target="path/to/project",
    input_mode="local"  # or "github"
)

# Disable agent analysis (faster, rule-based only)
output_path = analyze_project_hybrid(
    target="path/to/project",
    use_agents=False
)

# Full agent analysis (slower, more comprehensive)
output_path = analyze_project_hybrid(
    target="path/to/project",
    use_agents=True
)
```

## Input Modes

### GitHub Mode
- **Input**: GitHub repository URL
- **Process**: Clones repo → Analyzes dependencies → Runs detection
- **Capabilities**: Full version history, maintainer analysis, code diffs
- **Example**: `https://github.com/expressjs/express`

### Local Mode
- **Input**: Local directory path
- **Process**: Scans directory → Analyzes dependencies → Runs detection
- **Capabilities**: Current code analysis, dependency graph, pattern detection
- **Example**: `/path/to/my-project` or `C:\Users\...\my-project`

## Supported Ecosystems

### npm (JavaScript/Node.js)
- **Manifest**: `package.json`
- **Detection**: Automatic
- **Features**: Full dependency graph, vulnerability scanning, reputation scoring

### Python
- **Manifests**: `requirements.txt`, `setup.py`, `pyproject.toml`
- **Detection**: Automatic
- **Features**: Full dependency graph, vulnerability scanning, reputation scoring

## Analysis Layers

### Layer 1: Rule-Based Detection (Fast)
- **Execution Time**: < 5 seconds
- **Methods**:
  - Pattern matching for malicious code
  - Vulnerability database queries (OSV API)
  - Reputation scoring
  - Typosquatting detection
- **Output**: Initial findings with high confidence

### Layer 2: Agent Analysis (Intelligent)
- **Execution Time**: 10-20 seconds
- **Agents**:
  - Vulnerability Analysis Agent
  - Reputation Analysis Agent
  - Code Analysis Agent (conditional)
  - Supply Chain Attack Agent (conditional)
  - Synthesis Agent
- **Output**: Deep analysis with context and recommendations

## Output Format

### JSON Structure
```json
{
  "metadata": {
    "analysis_id": "analysis_20231203_123456_abc123",
    "analysis_type": "local_rule_based",
    "target": "/path/to/project",
    "timestamp": "2023-12-03T12:34:56",
    "ecosystem": "npm",
    "agent_analysis_enabled": false
  },
  "summary": {
    "total_packages": 10,
    "packages_with_findings": 2,
    "total_findings": 5,
    "critical_findings": 0,
    "high_findings": 2,
    "medium_findings": 3,
    "low_findings": 0
  },
  "security_findings": {
    "packages": [
      {
        "name": "package-name",
        "version": "1.0.0",
        "ecosystem": "npm",
        "findings": [...],
        "risk_score": 0.75,
        "risk_level": "high"
      }
    ]
  },
  "dependency_graph": {...},
  "recommendations": {
    "immediate_actions": [...],
    "preventive_measures": [...],
    "monitoring": [...]
  },
  "performance_metrics": {
    "total_analysis_time": 2.5,
    "rule_based_time": 1.2,
    "agent_time": 1.3
  }
}
```

### Output Location
- **File**: `outputs/demo_ui_comprehensive_report.json`
- **Format**: JSON (pretty-printed)
- **Encoding**: UTF-8

## Performance Characteristics

### Rule-Based Only (use_agents=False)
- **Time**: 2-5 seconds
- **Use Case**: Quick scans, CI/CD pipelines
- **Accuracy**: High for known patterns

### With Agents (use_agents=True)
- **Time**: 15-25 seconds
- **Use Case**: Comprehensive analysis, security audits
- **Accuracy**: Very high with context and reasoning

## Configuration

### Environment Variables
```bash
# OpenAI API (required for agents)
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini

# OSV API (optional)
ENABLE_OSV_QUERIES=true

# Output directory
OUTPUT_DIRECTORY=outputs

# Agent configuration
AGENT_TIMEOUT_SECONDS=120
AGENT_MAX_ROUNDS=12
```

### Configuration File
Location: `.env` in project root

## Error Handling

### Graceful Degradation
- If agents fail, falls back to rule-based results
- If synthesis fails, generates partial report
- If GitHub clone fails, suggests local mode

### Common Issues

#### Issue: "No manifest file found"
**Solution**: Ensure project has package.json (npm) or requirements.txt (Python)

#### Issue: "Git clone timed out"
**Solution**: Use local mode or increase timeout

#### Issue: "Synthesis agent failed"
**Solution**: Check OpenAI API key and quota

## Examples

### Example 1: Quick Scan
```python
# Fast scan without agents
output = analyze_project_hybrid(
    target="./my-project",
    use_agents=False
)
print(f"Report: {output}")
```

### Example 2: Comprehensive Analysis
```python
# Full analysis with agents
output = analyze_project_hybrid(
    target="https://github.com/user/repo",
    use_agents=True
)
print(f"Report: {output}")
```

### Example 3: Python Project
```python
# Analyze Python project
output = analyze_project_hybrid(
    target="./python-project",
    input_mode="local"
)
print(f"Report: {output}")
```

## Integration with Web UI

The output JSON is compatible with the existing Flask web UI:

```python
# In app.py
from analyze_supply_chain import analyze_project_hybrid

@app.route('/analyze', methods=['POST'])
def analyze():
    target = request.form['target']
    output_path = analyze_project_hybrid(target)
    
    # Load report
    with open(output_path) as f:
        report = json.load(f)
    
    return render_template('results.html', report=report)
```

## Best Practices

### 1. Use Rule-Based for CI/CD
- Fast execution
- Deterministic results
- No API dependencies

### 2. Use Agents for Security Audits
- Comprehensive analysis
- Context-aware findings
- Actionable recommendations

### 3. Cache Results
- Reuse dependency graphs
- Cache reputation scores
- Store vulnerability data

### 4. Monitor Performance
- Track analysis times
- Monitor API usage
- Optimize for your use case

## Troubleshooting

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

output = analyze_project_hybrid(target)
```

### Check Output
```python
import json

with open('outputs/demo_ui_comprehensive_report.json') as f:
    report = json.load(f)
    print(json.dumps(report, indent=2))
```

### Verify Dependencies
```bash
# Check if git is installed
git --version

# Check if Python packages are installed
pip list | grep requests
```

## Support

For issues or questions:
1. Check the logs in the output
2. Review the test suite: `test_main_entry_point.py`
3. Run examples: `python example_main_entry_point_usage.py`
4. Check the completion summary: `TASK_6_COMPLETION_SUMMARY.md`

## Next Steps

1. Run the examples: `python example_main_entry_point_usage.py`
2. Test with your project: `analyze_project_hybrid("path/to/your/project")`
3. Review the output: `outputs/demo_ui_comprehensive_report.json`
4. Integrate with your workflow

## Additional Resources

- **Design Document**: `.kiro/specs/hybrid-agentic-architecture/design.md`
- **Requirements**: `.kiro/specs/hybrid-agentic-architecture/requirements.md`
- **Task List**: `.kiro/specs/hybrid-agentic-architecture/tasks.md`
- **Test Suite**: `test_main_entry_point.py`
- **Examples**: `example_main_entry_point_usage.py`
