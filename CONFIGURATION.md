# Configuration Guide

Complete reference for configuring the Multi-Agent Security Analysis System.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Cache Configuration](#cache-configuration)
- [Reputation Scoring Configuration](#reputation-scoring-configuration)
- [Analysis Configuration](#analysis-configuration)
- [Agent Configuration](#agent-configuration)
- [Web Interface Configuration](#web-interface-configuration)
- [Advanced Configuration](#advanced-configuration)

---

## Environment Variables

All configuration is done through environment variables in the `.env` file.

### Creating Configuration File

```bash
# Copy example configuration
cp .env .env.local

# Edit with your settings
nano .env.local  # or use your preferred editor
```

### Required Variables

```bash
# OpenAI API Key (required for LLM analysis)
OPENAI_API_KEY=sk-...your-key-here...
```

### Optional Variables

```bash
# GitHub API Token (optional, for GitHub repository analysis)
GITHUB_TOKEN=ghp_...your-token...

# Output directory for analysis results
OUTPUT_DIRECTORY=./outputs

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## Cache Configuration

The caching system stores LLM analysis results and package reputation data to improve performance and reduce API costs.

### Basic Cache Settings

```bash
# Enable/disable caching (default: true)
CACHE_ENABLED=true

# Cache backend: sqlite, redis, or memory (default: sqlite)
CACHE_BACKEND=sqlite

# Cache database file location (for SQLite backend)
CACHE_DB_PATH=.cache/analysis_cache.db
```

### Cache TTL (Time-To-Live) Settings

```bash
# TTL for LLM analysis results in hours (default: 168 = 1 week)
CACHE_LLM_TTL_HOURS=168

# TTL for package reputation data in hours (default: 24)
CACHE_REPUTATION_TTL_HOURS=24

# TTL for general cache entries in hours (default: 72)
CACHE_DEFAULT_TTL_HOURS=72
```

### Cache Size Management

```bash
# Maximum cache size in MB (default: 500)
CACHE_MAX_SIZE_MB=500

# Enable automatic cleanup of expired entries (default: true)
CACHE_AUTO_CLEANUP=true

# Cleanup interval in hours (default: 24)
CACHE_CLEANUP_INTERVAL_HOURS=24
```

### Cache Statistics

```bash
# Enable cache statistics logging (default: false)
CACHE_STATS_ENABLED=false

# Log cache statistics interval in minutes (default: 60)
CACHE_STATS_INTERVAL_MINUTES=60
```

### SQLite Backend Configuration

```bash
# SQLite-specific settings
CACHE_BACKEND=sqlite
CACHE_DB_PATH=.cache/analysis_cache.db

# SQLite connection timeout in seconds (default: 30)
CACHE_SQLITE_TIMEOUT=30

# Enable WAL mode for better concurrency (default: true)
CACHE_SQLITE_WAL_MODE=true
```

### Redis Backend Configuration

```bash
# Redis-specific settings
CACHE_BACKEND=redis

# Redis connection settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password

# Redis connection pool settings
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Redis key prefix (default: "security_analysis:")
REDIS_KEY_PREFIX=security_analysis:
```

### Memory Backend Configuration

```bash
# Memory-specific settings (no persistence)
CACHE_BACKEND=memory

# Maximum entries in memory cache (default: 10000)
CACHE_MEMORY_MAX_ENTRIES=10000
```

### Cache Performance Tuning

**For Speed (Development):**
```bash
CACHE_BACKEND=memory
CACHE_LLM_TTL_HOURS=24
CACHE_REPUTATION_TTL_HOURS=6
```

**For Persistence (Production):**
```bash
CACHE_BACKEND=sqlite
CACHE_LLM_TTL_HOURS=168
CACHE_REPUTATION_TTL_HOURS=24
CACHE_MAX_SIZE_MB=1000
```

**For Distributed Systems:**
```bash
CACHE_BACKEND=redis
REDIS_HOST=cache-server.internal
CACHE_LLM_TTL_HOURS=72
CACHE_REPUTATION_TTL_HOURS=12
```

---

## Reputation Scoring Configuration

Package reputation scoring helps identify suspicious packages based on metadata.

### Basic Reputation Settings

```bash
# Enable/disable reputation scoring (default: true)
REPUTATION_ENABLED=true

# Reputation score threshold for flagging packages (default: 0.3)
# Packages with scores below this are flagged as security findings
REPUTATION_THRESHOLD=0.3

# Reputation score threshold for warnings (default: 0.6)
# Packages with scores below this generate warnings
REPUTATION_WARNING_THRESHOLD=0.6
```

### Reputation Factor Weights

```bash
# Weight for package age factor (default: 0.3)
REPUTATION_AGE_WEIGHT=0.3

# Weight for download statistics factor (default: 0.3)
REPUTATION_DOWNLOADS_WEIGHT=0.3

# Weight for author history factor (default: 0.2)
REPUTATION_AUTHOR_WEIGHT=0.2

# Weight for maintenance factor (default: 0.2)
REPUTATION_MAINTENANCE_WEIGHT=0.2
```

### Registry API Settings

```bash
# Rate limit for registry API calls (requests per second, default: 10)
REPUTATION_RATE_LIMIT=10

# Timeout for registry API calls in seconds (default: 5)
REPUTATION_TIMEOUT=5

# Maximum retries for failed API calls (default: 3)
REPUTATION_MAX_RETRIES=3

# Retry backoff multiplier (default: 2)
REPUTATION_RETRY_BACKOFF=2
```

### Registry-Specific Settings

```bash
# npm registry URL (default: https://registry.npmjs.org)
NPM_REGISTRY_URL=https://registry.npmjs.org

# PyPI registry URL (default: https://pypi.org/pypi)
PYPI_REGISTRY_URL=https://pypi.org/pypi

# npm authentication token (optional, for higher rate limits)
NPM_TOKEN=

# PyPI authentication token (optional)
PYPI_TOKEN=
```

### Reputation Scoring Thresholds

```bash
# Age thresholds (in days)
REPUTATION_AGE_NEW=30          # < 30 days = new package
REPUTATION_AGE_YOUNG=90        # < 90 days = young package
REPUTATION_AGE_ESTABLISHED=365 # < 365 days = established
REPUTATION_AGE_MATURE=730      # >= 730 days = mature

# Download thresholds (per week)
REPUTATION_DOWNLOADS_VERY_LOW=100
REPUTATION_DOWNLOADS_LOW=1000
REPUTATION_DOWNLOADS_MEDIUM=10000
REPUTATION_DOWNLOADS_HIGH=100000
```

---

## Analysis Configuration

### General Analysis Settings

```bash
# Enable/disable LLM analysis (default: true)
LLM_ANALYSIS_ENABLED=true

# Enable/disable pattern matching (default: true)
PATTERN_MATCHING_ENABLED=true

# Enable/disable OSV vulnerability queries (default: true)
ENABLE_OSV_QUERIES=true

# Enable/disable visual analysis (default: true)
VISUAL_ANALYSIS_ENABLED=true
```

### Python Analysis Settings

```bash
# Enable Python ecosystem analysis (default: true)
PYTHON_ANALYSIS_ENABLED=true

# Maximum depth for recursive dependency scanning (default: 3)
PYTHON_DEPENDENCY_DEPTH=3

# Enable LLM analysis for complex Python patterns (default: true)
PYTHON_LLM_ANALYSIS=true

# Timeout for pip dependency resolution in seconds (default: 60)
PYTHON_PIP_TIMEOUT=60
```

### npm Analysis Settings

```bash
# Enable npm ecosystem analysis (default: true)
NPM_ANALYSIS_ENABLED=true

# Maximum depth for recursive dependency scanning (default: 3)
NPM_DEPENDENCY_DEPTH=3

# Enable LLM analysis for complex npm patterns (default: true)
NPM_LLM_ANALYSIS=true

# Analyze devDependencies (default: true)
NPM_ANALYZE_DEV_DEPS=true
```

### Malicious Pattern Detection

```bash
# Sensitivity level: low, medium, high (default: medium)
PATTERN_SENSITIVITY=medium

# Enable obfuscation detection (default: true)
DETECT_OBFUSCATION=true

# Enable typosquatting detection (default: true)
DETECT_TYPOSQUATTING=true

# Levenshtein distance threshold for typosquatting (default: 2)
TYPOSQUATTING_DISTANCE_THRESHOLD=2
```

---

## Agent Configuration

### LLM Model Settings

```bash
# OpenAI model to use (default: gpt-4)
OPENAI_MODEL=gpt-4

# Model temperature (0.0-2.0, default: 0.1)
# Lower = more deterministic, Higher = more creative
AGENT_TEMPERATURE=0.1

# Maximum tokens per response (default: 4096)
AGENT_MAX_TOKENS=4096

# Top-p sampling (0.0-1.0, default: 1.0)
AGENT_TOP_P=1.0

# Frequency penalty (0.0-2.0, default: 0.0)
AGENT_FREQUENCY_PENALTY=0.0

# Presence penalty (0.0-2.0, default: 0.0)
AGENT_PRESENCE_PENALTY=0.0
```

### Agent Behavior Settings

```bash
# Agent timeout in seconds (default: 120)
AGENT_TIMEOUT_SECONDS=120

# Maximum retries for failed agent calls (default: 3)
AGENT_MAX_RETRIES=3

# Enable agent conversation history (default: true)
AGENT_ENABLE_HISTORY=true

# Maximum conversation history length (default: 10)
AGENT_MAX_HISTORY_LENGTH=10
```

### Multi-Agent Settings

```bash
# Enable multi-agent coordination (default: true)
MULTI_AGENT_ENABLED=true

# Maximum number of concurrent agents (default: 3)
MAX_CONCURRENT_AGENTS=3

# Agent coordination timeout in seconds (default: 300)
AGENT_COORDINATION_TIMEOUT=300
```

---

## Web Interface Configuration

### Flask Settings

```bash
# Flask host (default: 0.0.0.0)
FLASK_HOST=0.0.0.0

# Flask port (default: 5000)
FLASK_PORT=5000

# Flask debug mode (default: false)
FLASK_DEBUG=false

# Flask secret key (generate with: python -c "import secrets; print(secrets.token_hex())")
FLASK_SECRET_KEY=your-secret-key-here
```

### Upload Settings

```bash
# Maximum file upload size in MB (default: 16)
MAX_UPLOAD_SIZE_MB=16

# Allowed file extensions (comma-separated)
ALLOWED_EXTENSIONS=json,txt,py,toml

# Upload directory (default: ./uploads)
UPLOAD_DIRECTORY=./uploads
```

### Web Interface Features

```bash
# Enable live log streaming (default: true)
WEB_ENABLE_LIVE_LOGS=true

# Enable file upload (default: true)
WEB_ENABLE_UPLOAD=true

# Enable analysis history (default: true)
WEB_ENABLE_HISTORY=true

# Maximum history entries (default: 100)
WEB_MAX_HISTORY_ENTRIES=100
```

---

## Advanced Configuration

### Performance Tuning

```bash
# Enable parallel processing (default: true)
ENABLE_PARALLEL_PROCESSING=true

# Number of worker threads (default: 4)
WORKER_THREADS=4

# Enable async I/O (default: true)
ENABLE_ASYNC_IO=true

# I/O timeout in seconds (default: 30)
IO_TIMEOUT=30
```

### Security Settings

```bash
# Enable API key validation (default: true)
VALIDATE_API_KEYS=true

# Enable rate limiting (default: true)
ENABLE_RATE_LIMITING=true

# Rate limit: requests per minute (default: 60)
RATE_LIMIT_PER_MINUTE=60

# Enable request logging (default: true)
LOG_REQUESTS=true
```

### Debugging Settings

```bash
# Enable debug mode (default: false)
DEBUG_MODE=false

# Enable verbose logging (default: false)
VERBOSE_LOGGING=false

# Enable profiling (default: false)
ENABLE_PROFILING=false

# Save debug artifacts (default: false)
SAVE_DEBUG_ARTIFACTS=false

# Debug artifacts directory (default: ./debug)
DEBUG_ARTIFACTS_DIR=./debug
```

### Experimental Features

```bash
# Enable experimental features (default: false)
ENABLE_EXPERIMENTAL=false

# Enable machine learning-based detection (experimental)
ENABLE_ML_DETECTION=false

# Enable behavioral analysis (experimental)
ENABLE_BEHAVIORAL_ANALYSIS=false
```

---

## Configuration Examples

### Development Configuration

```bash
# .env.development
OPENAI_API_KEY=sk-...
LOG_LEVEL=DEBUG
CACHE_ENABLED=true
CACHE_BACKEND=memory
CACHE_LLM_TTL_HOURS=1
REPUTATION_ENABLED=true
FLASK_DEBUG=true
VERBOSE_LOGGING=true
```

### Production Configuration

```bash
# .env.production
OPENAI_API_KEY=sk-...
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_BACKEND=redis
REDIS_HOST=cache-server
CACHE_LLM_TTL_HOURS=168
CACHE_REPUTATION_TTL_HOURS=24
CACHE_MAX_SIZE_MB=1000
REPUTATION_ENABLED=true
REPUTATION_THRESHOLD=0.3
AGENT_TIMEOUT_SECONDS=180
FLASK_DEBUG=false
ENABLE_RATE_LIMITING=true
```

### High-Performance Configuration

```bash
# .env.performance
OPENAI_API_KEY=sk-...
CACHE_ENABLED=true
CACHE_BACKEND=redis
REDIS_HOST=localhost
CACHE_LLM_TTL_HOURS=168
ENABLE_PARALLEL_PROCESSING=true
WORKER_THREADS=8
ENABLE_ASYNC_IO=true
MAX_CONCURRENT_AGENTS=5
```

### Minimal Configuration

```bash
# .env.minimal
OPENAI_API_KEY=sk-...
CACHE_ENABLED=false
REPUTATION_ENABLED=false
LLM_ANALYSIS_ENABLED=true
PATTERN_MATCHING_ENABLED=true
```

---

## Configuration Validation

### Validate Configuration

```python
from config import Config

# Validate all settings
Config.validate()

# Check specific settings
print(f"Cache enabled: {Config.CACHE_ENABLED}")
print(f"Cache backend: {Config.CACHE_BACKEND}")
print(f"Reputation threshold: {Config.REPUTATION_THRESHOLD}")
```

### Configuration Diagnostics

```bash
# Run diagnostics script
python .kiro/diagnose.py

# Check configuration
python -c "from config import Config; Config.print_config()"
```

---

## Environment-Specific Configuration

### Using Multiple Environments

```bash
# Development
cp .env .env.development
# Edit .env.development

# Production
cp .env .env.production
# Edit .env.production

# Load specific environment
export ENV=production
python main_github.py --local /path/to/project
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.9

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV CACHE_BACKEND=redis
ENV REDIS_HOST=redis
ENV FLASK_HOST=0.0.0.0

# Run application
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CACHE_BACKEND=redis
      - REDIS_HOST=redis
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Troubleshooting Configuration

### Common Issues

**Problem: Configuration not loading**
```bash
# Check .env file exists
ls -la .env

# Verify format (no spaces around =)
cat .env

# Load manually
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ)"
```

**Problem: Invalid configuration values**
```bash
# Validate configuration
python -c "from config import Config; Config.validate()"
```

**Problem: Environment variables not set**
```bash
# Check environment
env | grep OPENAI
env | grep CACHE

# Set manually
export OPENAI_API_KEY=sk-...
```

---

For more information, see:
- [README.md](README.md) - Main documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
