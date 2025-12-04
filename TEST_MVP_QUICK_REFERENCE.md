# MVP Testing Quick Reference

## Running the Tests

### Run All MVP Tests
```bash
pytest test_mvp_comprehensive.py -v
```

### Run Specific Test Categories

#### Unit Tests Only
```bash
# Orchestrator tests
pytest test_mvp_comprehensive.py::TestOrchestratorUnit -v

# Vulnerability Agent tests
pytest test_mvp_comprehensive.py::TestVulnerabilityAgentUnit -v

# Reputation Agent tests
pytest test_mvp_comprehensive.py::TestReputationAgentUnit -v

# Synthesis Agent tests
pytest test_mvp_comprehensive.py::TestSynthesisAgentUnit -v
```

#### Integration Tests Only
```bash
# Malicious package detection
pytest test_mvp_comprehensive.py::TestMaliciousPackageIntegration -v

# Clean project analysis
pytest test_mvp_comprehensive.py::TestCleanProjectIntegration -v

# Agent failure handling
pytest test_mvp_comprehensive.py::TestAgentFailureHandling -v
```

#### Performance Tests Only
```bash
pytest test_mvp_comprehensive.py::TestPerformanceBenchmark -v
```

#### Backward Compatibility Tests Only
```bash
pytest test_mvp_comprehensive.py::TestBackwardCompatibility -v
```

### Run Specific Test
```bash
pytest test_mvp_comprehensive.py::TestOrchestratorUnit::test_orchestrator_initialization -v
```

## Test Output Options

### Verbose Output
```bash
pytest test_mvp_comprehensive.py -v
```

### Quiet Output (summary only)
```bash
pytest test_mvp_comprehensive.py -q
```

### Show Print Statements
```bash
pytest test_mvp_comprehensive.py -v -s
```

### Stop on First Failure
```bash
pytest test_mvp_comprehensive.py -x
```

### Show Test Duration
```bash
pytest test_mvp_comprehensive.py -v --durations=10
```

## Expected Results

### All Tests Pass
```
===================== 31 passed in ~68s ======================
```

### Test Breakdown
- **Unit Tests**: 21 tests
- **Integration Tests**: 7 tests
- **Performance Tests**: 2 tests
- **Backward Compatibility**: 2 tests

### Performance Targets
- Total execution time: < 120 seconds ✅
- 20 package analysis: < 120 seconds ✅
- Individual tests: < 10 seconds each ✅

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -r requirements.txt
```

### Tests Fail Due to Missing .env
Create `.env` file with:
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Performance Tests Timeout
Increase timeout in pytest.ini or run without performance tests:
```bash
pytest test_mvp_comprehensive.py -v -k "not Performance"
```

### Integration Tests Fail
Check that:
1. File system permissions allow temp directory creation
2. Network access for API calls (if not mocked)
3. Sufficient disk space for test artifacts

## Test Coverage Report

### Generate Coverage Report
```bash
pytest test_mvp_comprehensive.py --cov=agents --cov=analyze_supply_chain --cov-report=html
```

### View Coverage Report
Open `htmlcov/index.html` in browser

## Continuous Integration

### Run Tests in CI/CD
```yaml
# Example GitHub Actions
- name: Run MVP Tests
  run: pytest test_mvp_comprehensive.py -v --tb=short
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest test_mvp_comprehensive.py -q
```

## Test Maintenance

### Adding New Tests
1. Add test method to appropriate test class
2. Follow naming convention: `test_<what_is_tested>`
3. Add docstring explaining what is validated
4. Run tests to verify: `pytest test_mvp_comprehensive.py -v`

### Updating Tests
1. Modify test method
2. Ensure test still validates requirements
3. Run full test suite to check for regressions
4. Update documentation if behavior changes

## Related Test Files

### Other Test Files
- `test_agent_foundation.py` - Agent base classes and types
- `test_vulnerability_agent.py` - Vulnerability agent unit tests
- `test_reputation_agent.py` - Reputation agent unit tests
- `test_synthesis_agent.py` - Synthesis agent unit tests
- `test_main_entry_point.py` - Main entry point integration tests

### Run All Tests
```bash
pytest test_*.py -v
```

## Quick Validation

### Before Committing
```bash
# Run MVP tests
pytest test_mvp_comprehensive.py -q

# Expected output: 31 passed in ~68s
```

### Before Deploying
```bash
# Run all tests
pytest test_*.py -v --tb=short

# Check performance
pytest test_mvp_comprehensive.py::TestPerformanceBenchmark -v
```

## Support

For issues or questions:
1. Check test output for specific failure details
2. Review TASK_7_MVP_TESTING_SUMMARY.md for test descriptions
3. Check requirements in .kiro/specs/hybrid-agentic-architecture/requirements.md
4. Review design in .kiro/specs/hybrid-agentic-architecture/design.md
