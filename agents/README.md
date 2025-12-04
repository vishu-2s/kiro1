# Agent Foundation - Implementation Guide

## Overview

This directory contains the core agent infrastructure for the hybrid intelligent agentic architecture. The implementation provides:

- **Base Agent Classes**: Reusable foundation for all specialized agents
- **Orchestrator**: Sequential protocol for coordinating multi-agent analysis
- **Type System**: Strongly-typed data structures for agent communication
- **Retry Logic**: Exponential backoff with graceful degradation
- **Timeout Handling**: Per-stage timeouts with validation checkpoints

## Architecture

### Core Components

```
agents/
├── types.py           # Data structures (AgentResult, Finding, SharedContext)
├── base_agent.py      # SecurityAgent base class and MockAgent
├── orchestrator.py    # AgentOrchestrator with sequential protocol
└── __init__.py        # Package exports
```

### Sequential Protocol

The orchestrator implements a 5-stage conversation protocol:

1. **Vulnerability Analysis** (required, 30s timeout)
   - Analyzes packages for known vulnerabilities
   - Queries OSV API and CVE databases
   - Calculates CVSS scores

2. **Reputation Analysis** (required, 20s timeout)
   - Assesses package trustworthiness
   - Analyzes age, downloads, author history
   - Identifies risk factors

3. **Code Analysis** (conditional, 40s timeout)
   - Triggered by suspicious patterns
   - Analyzes obfuscated code
   - Detects malicious behavior

4. **Supply Chain Analysis** (conditional, 30s timeout)
   - Triggered by high-risk packages
   - Detects sophisticated attacks (Hulud-style)
   - Analyzes maintainer changes

5. **Synthesis** (required, 20s timeout)
   - Aggregates all findings
   - Generates package-centric JSON
   - Produces recommendations

**Total Max Time**: 140 seconds (2.3 minutes)

## Usage

### Basic Usage

```python
from agents import AgentOrchestrator, MockAgent, Finding

# Create orchestrator
orchestrator = AgentOrchestrator()

# Register agents
orchestrator.register_agent("vulnerability_analysis", vuln_agent)
orchestrator.register_agent("reputation_analysis", rep_agent)
orchestrator.register_agent("synthesis", synth_agent)

# Run analysis
result = orchestrator.orchestrate(
    initial_findings=[...],
    dependency_graph={...},
    input_mode="local",
    ecosystem="npm"
)
```

### Creating Custom Agents

```python
from agents import SecurityAgent, SharedContext

class MyCustomAgent(SecurityAgent):
    def __init__(self):
        super().__init__(
            name="my_agent",
            system_message="You are a custom security agent...",
            tools=[tool1, tool2]
        )
    
    def analyze(self, context: SharedContext, timeout: int = None) -> dict:
        # Implement your analysis logic
        packages = context.packages
        
        # Perform analysis
        results = {"packages": [...]}
        
        return results
```

### Using Mock Agents for Testing

```python
from agents import MockAgent

# Create mock agent with predefined data
mock_agent = MockAgent(
    name="test_agent",
    mock_data={
        "packages": [
            {"name": "test", "version": "1.0.0"}
        ]
    }
)

# Use in tests
result = mock_agent.analyze(context)
```

## Data Structures

### AgentResult

Encapsulates the output from an agent execution:

```python
@dataclass
class AgentResult:
    agent_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0.0
    status: AgentStatus = AgentStatus.SUCCESS
    confidence: float = 1.0
```

### Finding

Represents a security finding:

```python
@dataclass
class Finding:
    package_name: str
    package_version: str
    finding_type: str
    severity: str
    description: str
    detection_method: str = "rule_based"
    confidence: float = 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None
```

### SharedContext

Shared state passed between agents:

```python
@dataclass
class SharedContext:
    initial_findings: List[Finding]
    dependency_graph: Dict[str, Any]
    packages: List[str]
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    input_mode: str = "local"
    project_path: str = ""
    ecosystem: str = "npm"
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Error Handling

### Retry Logic

Agents automatically retry on failure with exponential backoff:

- **Max Retries**: 2 (configurable per stage)
- **Initial Delay**: 1.0 seconds
- **Backoff Multiplier**: 2x
- **Retry Sequence**: 1s → 2s → 4s

```python
# Configuration
config = AgentConfig(
    name="vulnerability_analysis",
    timeout=30,
    required=True,
    max_retries=2,
    retry_delay=1.0
)
```

### Graceful Degradation

When agents fail, the orchestrator provides fallback behavior:

**Required Agents** (vulnerability, reputation, synthesis):
- Use fallback data (rule-based findings, default scores)
- Continue analysis with degraded capabilities
- Mark report as "partial"

**Optional Agents** (code, supply chain):
- Skip the stage
- Log the failure
- Continue with remaining stages

### Degradation Levels

| Level | Description | User Impact |
|-------|-------------|-------------|
| 100% | All agents succeed | Full analysis with high confidence |
| 70% | Required agents succeed, optional fail | Good analysis, missing advanced features |
| 40% | Some required agents fail | Partial analysis with fallback data |
| <40% | Multiple required agents fail | Minimal analysis, recommend retry |

## Configuration

All configuration is loaded from `.env` file:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=4096
AGENT_TIMEOUT_SECONDS=120

# AutoGen Configuration
AUTOGEN_CACHE_SEED=42
AUTOGEN_MAX_CONSECUTIVE_AUTO_REPLY=10

# Output Configuration
OUTPUT_DIRECTORY=outputs
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest test_agent_foundation.py -v

# Run specific test class
python -m pytest test_agent_foundation.py::TestAgentOrchestrator -v

# Run with coverage
python -m pytest test_agent_foundation.py --cov=agents
```

### Test Coverage

The test suite covers:

- ✅ AgentResult creation and validation
- ✅ Finding and SharedContext data structures
- ✅ SecurityAgent base class functionality
- ✅ MockAgent for testing
- ✅ AgentOrchestrator sequential protocol
- ✅ Retry logic with exponential backoff
- ✅ Timeout handling
- ✅ Graceful degradation
- ✅ Fallback data generation
- ✅ JSON schema validation

## Performance

### Expected Timings

| Stage | Timeout | Typical Duration |
|-------|---------|------------------|
| Vulnerability Analysis | 30s | 5-15s |
| Reputation Analysis | 20s | 3-8s |
| Code Analysis | 40s | 10-30s |
| Supply Chain Analysis | 30s | 8-20s |
| Synthesis | 20s | 5-10s |
| **Total** | **140s** | **30-80s** |

### Optimization Tips

1. **Enable Caching**: Cache LLM responses to avoid redundant API calls
2. **Conditional Execution**: Skip optional stages when not needed
3. **Parallel Tool Calls**: Use async for independent tool calls
4. **Batch Processing**: Process multiple packages in single LLM call

## Next Steps

After implementing the foundation, the next tasks are:

1. **Task 2**: Implement VulnerabilityAnalysisAgent with OSV integration
2. **Task 3**: Implement ReputationAnalysisAgent with registry integration
3. **Task 4**: Implement SynthesisAgent with OpenAI JSON mode
4. **Task 5**: Implement DependencyGraphAnalyzer
5. **Task 6**: Update main entry point (analyze_supply_chain.py)

## Troubleshooting

### Common Issues

**Issue**: Agent timeout
```
Solution: Increase timeout in AgentConfig or optimize agent logic
```

**Issue**: Retry exhaustion
```
Solution: Check agent implementation for bugs, verify API keys
```

**Issue**: Invalid JSON schema
```
Solution: Ensure synthesis agent returns required keys (metadata, summary, security_findings)
```

**Issue**: Missing agent registration
```
Solution: Register all required agents before calling orchestrate()
```

## References

- Design Document: `.kiro/specs/hybrid-agentic-architecture/design.md`
- Requirements: `.kiro/specs/hybrid-agentic-architecture/requirements.md`
- Tasks: `.kiro/specs/hybrid-agentic-architecture/tasks.md`
- Example Usage: `example_orchestrator_usage.py`
- Tests: `test_agent_foundation.py`
