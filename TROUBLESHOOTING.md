# Troubleshooting Guide

This guide provides detailed solutions for common issues with the Multi-Agent Security Analysis System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Cache Issues](#cache-issues)
- [Python Analysis Issues](#python-analysis-issues)
- [npm Analysis Issues](#npm-analysis-issues)
- [Reputation Scoring Issues](#reputation-scoring-issues)
- [API and Network Issues](#api-and-network-issues)
- [Performance Issues](#performance-issues)
- [Web Interface Issues](#web-interface-issues)
- [Testing Issues](#testing-issues)

---

## Installation Issues

### Problem: `pip install` fails with dependency conflicts

**Symptoms:**
```
ERROR: Cannot install -r requirements.txt because these package versions have conflicts
```

**Solutions:**

1. **Use a fresh virtual environment:**
```bash
# Remove old environment
rm -rf venv

# Create new environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Update pip and setuptools:**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

3. **Install dependencies one by one:**
```bash
# Install core dependencies first
pip install openai requests pydantic python-dotenv

# Then install analysis tools
pip install hypothesis pytest

# Finally install optional dependencies
pip install redis  # If using Redis cache
```

### Problem: Python version incompatibility

**Symptoms:**
```
ERROR: This package requires Python >=3.8
```

**Solution:**
```bash
# Check Python version
python --version

# If < 3.8, install Python 3.8+ and create new venv
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration Issues

### Problem: "OPENAI_API_KEY not found" error

**Symptoms:**
```
Error: OPENAI_API_KEY environment variable not set
```

**Solutions:**

1. **Check .env file exists:**
```bash
ls -la .env
```

2. **Verify .env file format:**
```bash
# .env should contain:
OPENAI_API_KEY=sk-...your-key-here...
```

3. **Load environment manually:**
```python
from dotenv import load_dotenv
load_dotenv()
import os
print(os.getenv('OPENAI_API_KEY'))  # Should print your key
```

4. **Set environment variable directly:**
```bash
# Linux/Mac
export OPENAI_API_KEY=sk-...your-key...

# Windows CMD
set OPENAI_API_KEY=sk-...your-key...

# Windows PowerShell
$env:OPENAI_API_KEY="sk-...your-key..."
```

### Problem: Configuration changes not taking effect

**Solution:**
```bash
# Restart the application
# Clear cache if configuration affects caching
python -c "from tools.cache_manager import CacheManager; CacheManager().clear()"

# Verify configuration is loaded
python -c "from config import Config; print(Config.CACHE_ENABLED)"
```

---

## Cache Issues

### Problem: "Database is locked" error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes trying to access SQLite cache simultaneously.

**Solutions:**

1. **Use Redis for concurrent access:**
```bash
# Install Redis
pip install redis

# Start Redis server
redis-server

# Configure in .env
CACHE_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

2. **Ensure single process access:**
```bash
# Check for running processes
ps aux | grep python

# Kill duplicate processes
kill <process_id>
```

3. **Use file locking:**
```python
from tools.cache_manager import CacheManager

# Increase timeout for lock acquisition
cache = CacheManager(backend="sqlite", lock_timeout=30)
```

### Problem: Cache not improving performance

**Symptoms:**
- Analysis takes same time on repeated runs
- Cache hit rate is 0%

**Diagnosis:**
```python
from tools.cache_manager import CacheManager

cache = CacheManager()
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Total entries: {stats['total_entries']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

**Solutions:**

1. **Verify cache is enabled:**
```bash
# Check .env
grep CACHE_ENABLED .env
# Should show: CACHE_ENABLED=true
```

2. **Check cache file exists:**
```bash
ls -la .cache/analysis_cache.db
```

3. **Verify content hashing:**
```python
from tools.cache_manager import CacheManager

cache = CacheManager()
script = "console.log('test');"
key1 = cache._generate_cache_key(script, "test-pkg")
key2 = cache._generate_cache_key(script, "test-pkg")
print(f"Keys match: {key1 == key2}")  # Should be True
```

4. **Clear corrupted cache:**
```bash
rm -rf .cache/analysis_cache.db
# Cache will be rebuilt on next run
```

### Problem: Cache growing too large

**Symptoms:**
- Cache database file > 500MB
- Disk space warnings

**Solutions:**

1. **Set cache size limit:**
```bash
# In .env
CACHE_MAX_SIZE_MB=200
```

2. **Manual cleanup:**
```python
from tools.cache_manager import CacheManager

cache = CacheManager()

# Remove expired entries
cache.cleanup_expired()

# Check size
stats = cache.get_stats()
print(f"Cache size: {stats['size_mb']:.1f} MB")

# Clear all if needed
cache.clear()
```

3. **Reduce TTL:**
```bash
# In .env
CACHE_LLM_TTL_HOURS=24  # Instead of 168 (1 week)
```

### Problem: Cache returning stale data

**Symptoms:**
- Analysis results don't reflect recent changes
- Package reputation scores outdated

**Solutions:**

1. **Invalidate specific entries:**
```python
from tools.cache_manager import CacheManager

cache = CacheManager()
# Invalidate by package name
cache.invalidate_pattern("package-name")
```

2. **Reduce TTL for reputation data:**
```bash
# In .env
CACHE_REPUTATION_TTL_HOURS=6  # Instead of 24
```

3. **Force refresh:**
```bash
# Clear cache before analysis
python -c "from tools.cache_manager import CacheManager; CacheManager().clear()"
python main_github.py --local /path/to/project
```

---

## Python Analysis Issues

### Problem: setup.py parsing fails

**Symptoms:**
```
Error: Failed to parse setup.py: invalid syntax
```

**Causes:**
- Syntax errors in setup.py
- Python 2 syntax in Python 3 environment
- Dynamic imports or complex metaprogramming

**Solutions:**

1. **Check Python version compatibility:**
```bash
# Try parsing with Python AST
python -c "import ast; ast.parse(open('setup.py').read())"
```

2. **View detailed error:**
```python
from tools.python_analyzer import PythonAnalyzer

analyzer = PythonAnalyzer()
try:
    findings = analyzer.analyze_install_scripts('/path/to/project')
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

3. **Skip problematic files:**
```python
# The analyzer will log warnings but continue
# Check logs for details
```

### Problem: False positives in malicious pattern detection

**Symptoms:**
- Legitimate code flagged as malicious
- Test files triggering security warnings

**Solutions:**

1. **Review context:**
```python
# Check if code is in test files
# Pattern detection considers file paths
```

2. **Adjust pattern sensitivity:**
```python
from tools.python_analyzer import PythonAnalyzer

analyzer = PythonAnalyzer()
# Patterns are in get_malicious_patterns()
# Can be customized for your use case
```

3. **Use LLM analysis for context:**
```python
# Complex patterns automatically route to LLM
# LLM provides context-aware analysis
```

### Problem: Missing dependencies not detected

**Symptoms:**
- requirements.txt exists but dependencies not analyzed
- Transitive dependencies not found

**Solutions:**

1. **Verify requirements.txt format:**
```bash
# Valid format:
requests>=2.28.0
numpy==1.24.0
pandas~=1.5.0

# Invalid format (will be skipped):
# This is a comment only file
```

2. **Check requirements-parser installation:**
```bash
pip install requirements-parser
```

3. **Test dependency extraction:**
```python
from tools.python_analyzer import PythonAnalyzer

analyzer = PythonAnalyzer()
deps = analyzer.extract_dependencies('/path/to/requirements.txt')
print(f"Found {len(deps)} dependencies")
for dep in deps:
    print(f"  - {dep['name']} {dep.get('version', 'any')}")
```

4. **Enable recursive scanning:**
```python
# Recursive dependency scanning is automatic
# Check logs for pip resolution errors
```

---

## npm Analysis Issues

### Problem: package.json parsing fails

**Symptoms:**
```
Error: Failed to parse package.json: invalid JSON
```

**Solutions:**

1. **Validate JSON syntax:**
```bash
# Use jq or Python to validate
python -c "import json; json.load(open('package.json'))"
```

2. **Check for comments:**
```json
// Comments are not valid in JSON
{
  "name": "my-package"  // Remove this comment
}
```

3. **Fix trailing commas:**
```json
{
  "dependencies": {
    "express": "^4.18.0",  // Remove this comma
  }
}
```

### Problem: Scripts not being analyzed

**Symptoms:**
- Malicious install scripts not detected
- No findings for suspicious npm scripts

**Solutions:**

1. **Verify script detection:**
```python
from tools.npm_analyzer import NpmAnalyzer

analyzer = NpmAnalyzer()
findings = analyzer.analyze_install_scripts('/path/to/project')
print(f"Found {len(findings)} findings")
```

2. **Check script types:**
```json
// These scripts are analyzed:
{
  "scripts": {
    "preinstall": "...",
    "install": "...",
    "postinstall": "...",
    "preuninstall": "...",
    "uninstall": "...",
    "postuninstall": "..."
  }
}
```

---

## Reputation Scoring Issues

### Problem: "Registry API timeout" errors

**Symptoms:**
```
Error: Timeout fetching metadata from registry
```

**Solutions:**

1. **Increase timeout:**
```bash
# In .env
REPUTATION_TIMEOUT=10  # Increase from default 5 seconds
```

2. **Check network connectivity:**
```bash
# Test npm registry
curl https://registry.npmjs.org/express

# Test PyPI
curl https://pypi.org/pypi/requests/json
```

3. **Use cached data:**
```python
# Reputation service automatically uses cache
# Increase cache TTL to reduce API calls
CACHE_REPUTATION_TTL_HOURS=48
```

4. **Implement retry logic:**
```python
from tools.reputation_service import ReputationScorer

# Retry is built-in with exponential backoff
# Check logs for retry attempts
```

### Problem: All packages show low reputation scores

**Symptoms:**
- Every package flagged as suspicious
- Reputation scores consistently < 0.3

**Causes:**
- Registry API returning incomplete data
- Packages genuinely new/unpopular
- Scoring thresholds too strict

**Solutions:**

1. **Verify API responses:**
```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)
rep = scorer.calculate_reputation("express", "npm")
print(f"Metadata: {rep['metadata']}")
print(f"Factors: {rep['factors']}")
```

2. **Adjust threshold:**
```bash
# In .env
REPUTATION_THRESHOLD=0.2  # Lower threshold
```

3. **Check specific factors:**
```python
# If age_score is low, packages may be genuinely new
# If downloads_score is low, packages may be unpopular
# Review flags for specific issues
print(f"Flags: {rep['flags']}")
```

### Problem: Rate limiting from package registries

**Symptoms:**
```
Error: 429 Too Many Requests
```

**Solutions:**

1. **Reduce rate limit:**
```bash
# In .env
REPUTATION_RATE_LIMIT=5  # Reduce from default 10 req/sec
```

2. **Add delays:**
```python
import time
# Built-in rate limiting handles this
# Increase cache TTL to reduce requests
```

3. **Use authentication (npm):**
```bash
# In .env
NPM_TOKEN=your_npm_token
# Authenticated requests have higher limits
```

---

## API and Network Issues

### Problem: OpenAI API rate limiting

**Symptoms:**
```
Error: Rate limit exceeded
```

**Solutions:**

1. **Enable caching:**
```bash
# In .env
CACHE_ENABLED=true
CACHE_LLM_TTL_HOURS=168
```

2. **Reduce concurrent requests:**
```python
# Analyze projects sequentially
# Use batch analysis with delays
```

3. **Upgrade API tier:**
```
# Visit OpenAI dashboard to upgrade
# Higher tiers have higher rate limits
```

4. **Reduce token usage:**
```bash
# In .env
AGENT_MAX_TOKENS=2048  # Reduce from 4096
```

### Problem: Network timeouts

**Symptoms:**
```
Error: Connection timeout
```

**Solutions:**

1. **Increase timeouts:**
```bash
# In .env
AGENT_TIMEOUT_SECONDS=180  # Increase from 120
REPUTATION_TIMEOUT=10
```

2. **Check proxy settings:**
```bash
# If behind corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

3. **Verify connectivity:**
```bash
# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test package registries
curl https://registry.npmjs.org/express
curl https://pypi.org/pypi/requests/json
```

---

## Performance Issues

### Problem: Analysis is very slow

**Symptoms:**
- Analysis takes > 5 minutes for small projects
- High CPU/memory usage

**Solutions:**

1. **Enable caching:**
```bash
# In .env
CACHE_ENABLED=true
```

2. **Reduce LLM calls:**
```python
# Use pattern matching for simple cases
# Only route complex patterns to LLM
```

3. **Limit dependency depth:**
```python
# For Python projects with many dependencies
# Consider analyzing only direct dependencies first
```

4. **Use faster cache backend:**
```bash
# Redis is faster than SQLite for large caches
CACHE_BACKEND=redis
```

5. **Profile performance:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run analysis
# ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Problem: High memory usage

**Symptoms:**
- Python process using > 1GB RAM
- Out of memory errors

**Solutions:**

1. **Process files in batches:**
```python
# Analyze large projects in chunks
# Clear cache between batches
```

2. **Limit cache size:**
```bash
# In .env
CACHE_MAX_SIZE_MB=200
```

3. **Use memory backend for cache:**
```bash
# If SQLite causing issues
CACHE_BACKEND=memory
```

4. **Monitor memory:**
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

---

## Web Interface Issues

### Problem: Web app won't start

**Symptoms:**
```
Error: Address already in use
```

**Solutions:**

1. **Change port:**
```bash
# In app.py or via environment
export FLASK_PORT=5001
python app.py
```

2. **Kill existing process:**
```bash
# Find process using port 5000
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Kill process
kill <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### Problem: File upload fails

**Symptoms:**
- Upload button doesn't work
- "File too large" error

**Solutions:**

1. **Check file size limit:**
```python
# In app.py
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

2. **Verify file type:**
```python
# Supported files:
# - package.json
# - requirements.txt
# - setup.py
# - pyproject.toml
```

3. **Check browser console:**
```
# Open browser DevTools (F12)
# Check Console tab for JavaScript errors
```

---

## Testing Issues

### Problem: Property-based tests failing

**Symptoms:**
```
Falsifying example: test_property_X(...)
```

**Solutions:**

1. **Review counterexample:**
```python
# Hypothesis provides minimal failing example
# Analyze why the property doesn't hold
```

2. **Adjust test constraints:**
```python
from hypothesis import given, strategies as st

# Add constraints to generators
@given(st.text(min_size=1, max_size=100))  # Limit size
def test_property(text):
    # Exclude invalid inputs
    assume(len(text.strip()) > 0)
    # ...
```

3. **Fix implementation:**
```python
# If counterexample reveals a bug
# Fix the implementation, not the test
```

4. **Update specification:**
```python
# If property is incorrect
# Discuss with team and update design doc
```

### Problem: Tests timing out

**Symptoms:**
```
Error: Test exceeded timeout
```

**Solutions:**

1. **Increase timeout:**
```bash
# In pytest.ini or command line
pytest --timeout=300  # 5 minutes
```

2. **Mock external APIs:**
```python
from unittest.mock import patch

@patch('tools.reputation_service.requests.get')
def test_reputation(mock_get):
    mock_get.return_value.json.return_value = {...}
    # Test with mocked data
```

3. **Use smaller test data:**
```python
# Reduce Hypothesis example count
from hypothesis import settings

@settings(max_examples=50)  # Instead of 100
@given(...)
def test_property(...):
    pass
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main_github.py --local /path/to/project
```

2. **Run diagnostics:**
```bash
python .kiro/diagnose.py
```

3. **Collect system info:**
```bash
python --version
pip list
uname -a  # Linux/Mac
systeminfo  # Windows
```

4. **Create minimal reproduction:**
```python
# Simplify to smallest failing case
# Share code and error message
```

5. **Open an issue:**
- Include error messages
- Provide system information
- Share minimal reproduction
- Describe expected vs actual behavior

---

## Additional Resources

- [README.md](README.md) - Main documentation
- [tools/cache_manager_usage.md](tools/cache_manager_usage.md) - Cache usage guide
- [WEBAPP_QUICKSTART.md](WEBAPP_QUICKSTART.md) - Web interface guide
- [.kiro/TESTING_GUIDE.md](.kiro/TESTING_GUIDE.md) - Testing documentation
