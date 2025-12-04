# Multi-Agent Security Analysis System

An AI-powered security analysis platform that uses multiple specialized agents to detect malicious packages, vulnerabilities, and supply chain attacks in software projects.

## 🌟 New: Web Application Interface

**Now with a beautiful web UI!** Run security analysis through your browser with live logs and interactive reports.

```bash
python app.py
# Open http://localhost:5000
```

See [WEBAPP_QUICKSTART.md](WEBAPP_QUICKSTART.md) for details.

## Features

- **🌐 Web Interface**: Modern UI with live logs and interactive reports
- **🐍 Python Ecosystem Support**: Analyze setup.py scripts, requirements.txt, and pip dependencies
- **📦 npm Ecosystem Support**: Comprehensive npm package and script analysis
- **⚡ Intelligent Caching**: 10x performance boost with SQLite-based LLM response caching
- **🎯 Package Reputation Scoring**: Identify suspicious packages based on age, downloads, and author history
- **Multi-Agent Architecture**: Specialized AI agents for different security analysis tasks
- **Supply Chain Security**: Comprehensive SBOM analysis and vulnerability detection
- **Visual Security Analysis**: GPT-4 Vision integration for screenshot analysis
- **Automated Threat Intelligence**: Real-time updates from OSV database
- **Comprehensive Reporting**: Detailed incident reports with remediation guidance
- **Property-Based Testing**: Rigorous correctness verification using Hypothesis

## Project Structure

```
multi-agent-security/
├── agents/                 # AI agent implementations
├── tools/                  # Analysis tools and utilities
├── artifacts/              # Sample artifacts and test data
├── screenshots/            # Screenshots for visual analysis
├── outputs/                # Analysis results and reports
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── setup_venv.py         # Virtual environment setup
```

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository and navigate to the project directory
cd multi-agent-security

# Run the setup script to create virtual environment and install dependencies
python setup_venv.py

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Configuration

1. Copy the `.env` file and update with your API keys:
   ```bash
   cp .env .env.local
   ```

2. Edit `.env.local` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here  # Optional
   ```

### 3. Usage

#### Basic Analysis

```bash
# Analyze a GitHub repository
python main_github.py --repo https://github.com/owner/repo

# Analyze a local directory
python main_github.py --local /path/to/project

# Get help
python main_github.py --help
```

#### Web Interface

```bash
# Start the web application
python app.py

# Open your browser to http://localhost:5000
# Upload package.json, requirements.txt, or setup.py files for analysis
```

#### Python Project Analysis

The system automatically detects and analyzes Python projects:

```bash
# Analyze a Python project with setup.py
python main_github.py --local /path/to/python-project

# The analyzer will:
# - Parse setup.py for installation hooks and malicious patterns
# - Scan requirements.txt for known malicious packages
# - Recursively analyze pip dependencies
# - Check package reputation scores
# - Generate comprehensive security findings
```

**Supported Python Files:**
- `setup.py` - Installation scripts with arbitrary code execution
- `requirements.txt` - Dependency specifications
- `pyproject.toml` - Modern Python project configuration

**Python-Specific Detections:**
- Installation hooks (cmdclass, setup_requires, install_requires)
- Malicious patterns (os.system, subprocess, eval, exec)
- Remote code execution attempts
- Suspicious file access
- Known malicious packages from threat intelligence

#### npm Project Analysis

```bash
# Analyze an npm project
python main_github.py --local /path/to/npm-project

# The analyzer will:
# - Parse package.json for dependencies and scripts
# - Detect malicious install/postinstall scripts
# - Check for typosquatting attempts
# - Analyze package reputation
# - Scan for obfuscated code
```

## Python Ecosystem Support

The system provides comprehensive security analysis for Python projects:

### Supported Files

- **setup.py**: Installation scripts with arbitrary code execution capabilities
- **requirements.txt**: Dependency specifications
- **pyproject.toml**: Modern Python project configuration (PEP 518)

### Detection Capabilities

#### Installation Hook Analysis
Extracts and examines:
- `cmdclass` - Custom installation commands
- `setup_requires` - Build-time dependencies
- `install_requires` - Runtime dependencies
- Custom setup scripts

#### Malicious Pattern Detection
Identifies dangerous patterns:
- **Remote Code Execution**: `os.system()`, `subprocess.call()`, `eval()`, `exec()`
- **Network Activity**: `urllib.request.urlopen()`, `requests.get()`
- **File System Access**: Suspicious file operations
- **Obfuscation**: Base64 encoding, dynamic imports

#### Dependency Analysis
- Recursive pip dependency scanning
- Known malicious package detection
- Typosquatting identification
- Reputation scoring for all dependencies

### Example Analysis

```bash
# Analyze Python project
python main_github.py --local /path/to/python-project

# Expected output:
# ✓ Analyzing setup.py for installation hooks
# ✓ Scanning requirements.txt for dependencies
# ✓ Checking package reputation scores
# ✓ Running LLM analysis on complex patterns
# 
# Findings:
# 🔴 CRITICAL: Malicious pattern in setup.py
#     Pattern: os.system() call
#     Evidence: Downloads and executes remote script
# 🟡 MEDIUM: Low reputation package
#     Package: suspicious-pkg (reputation: 0.25)
```

### Python-Specific Configuration

```bash
# Enable Python analysis (default: true)
PYTHON_ANALYSIS_ENABLED=true

# Recursive dependency depth (default: 3)
PYTHON_DEPENDENCY_DEPTH=3

# Enable LLM analysis for complex patterns (default: true)
PYTHON_LLM_ANALYSIS=true
```

For detailed examples, see [EXAMPLES.md](EXAMPLES.md#python-project-analysis).

## Dependencies

The system requires the following main dependencies:

- **pyautogen**: Multi-agent framework
- **openai**: OpenAI API integration
- **requests**: HTTP client for API calls
- **pydantic**: Data validation
- **python-dotenv**: Environment configuration
- **hypothesis**: Property-based testing
- **requirements-parser**: Parse Python requirements files

See `requirements.txt` for the complete list.

## Configuration Options

The system can be configured through environment variables in the `.env` file:

### Core Configuration
- `OPENAI_API_KEY`: OpenAI API key (required)
- `GITHUB_TOKEN`: GitHub API token (optional)
- `OUTPUT_DIRECTORY`: Directory for analysis results

### Agent Configuration
- `AGENT_TEMPERATURE`: AI model temperature (default: 0.1)
- `AGENT_MAX_TOKENS`: Maximum tokens per response (default: 4096)
- `AGENT_TIMEOUT_SECONDS`: Agent timeout (default: 120)

### Analysis Configuration
- `CACHE_ENABLED`: Enable threat intelligence caching (default: true)
- `CACHE_DURATION_HOURS`: Cache duration (default: 24)
- `ENABLE_OSV_QUERIES`: Enable OSV API queries (default: true)

### Caching Configuration

The intelligent caching system dramatically improves performance by storing LLM analysis results and package reputation data.

#### Environment Variables

```bash
# Enable/disable caching (default: true)
CACHE_ENABLED=true

# Cache backend: "sqlite", "redis", or "memory" (default: sqlite)
CACHE_BACKEND=sqlite

# Cache database location (default: .cache/analysis_cache.db)
CACHE_DB_PATH=.cache/analysis_cache.db

# TTL for LLM analysis cache in hours (default: 168 = 1 week)
CACHE_LLM_TTL_HOURS=168

# TTL for reputation data cache in hours (default: 24)
CACHE_REPUTATION_TTL_HOURS=24

# Maximum cache size in MB (default: 500)
CACHE_MAX_SIZE_MB=500

# Enable cache statistics logging (default: false)
CACHE_STATS_ENABLED=false
```

#### Cache Backends

**SQLite (Default - Recommended)**
- Single file database, no server required
- Persistent across restarts
- Automatic cleanup of expired entries
- Best for single-machine deployments

```python
from tools.cache_manager import CacheManager

cache = CacheManager(backend="sqlite", ttl_hours=168)
```

**Redis (Optional - For Distributed Systems)**
- Requires Redis server
- Shared cache across multiple instances
- Automatic expiration with Redis TTL
- Best for multi-server deployments

```bash
# Install Redis support
pip install redis

# Configure Redis connection
CACHE_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Memory (Fallback)**
- In-memory dictionary
- Lost on restart
- No persistence
- Used automatically if SQLite/Redis fail

#### Cache Performance

With caching enabled:
- **First analysis**: Normal speed (LLM API calls)
- **Subsequent analyses**: 10x faster (cache hits)
- **API cost savings**: ~90% reduction for repeated analyses
- **Storage**: ~100MB for 1000 cached analyses

#### Cache Management

```python
from tools.cache_manager import CacheManager

cache = CacheManager()

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Total entries: {stats['total_entries']}")
print(f"Cache size: {stats['size_mb']:.1f} MB")

# Clear expired entries
cache.cleanup_expired()

# Clear all cache
cache.clear()

# Invalidate specific entry
cache.invalidate("sha256_hash_key")
```

See [tools/cache_manager_usage.md](tools/cache_manager_usage.md) for detailed usage examples.

### Reputation Scoring Configuration

Package reputation scoring helps identify suspicious packages even without malicious code.

#### Scoring Factors

The reputation score (0.0-1.0) is calculated from:

1. **Package Age** (30% weight)
   - < 30 days: 0.2 (new package risk)
   - 30-90 days: 0.5
   - 90-365 days: 0.7
   - 1-2 years: 0.9
   - 2+ years: 1.0 (established)

2. **Download Statistics** (30% weight)
   - < 100/week: 0.2 (very low adoption)
   - 100-1K/week: 0.5
   - 1K-10K/week: 0.7
   - 10K-100K/week: 0.9
   - 100K+/week: 1.0 (popular)

3. **Author History** (20% weight)
   - Unknown author: 0.3
   - New author (< 1 year): 0.5
   - Established author: 0.8
   - Verified organization: 1.0

4. **Maintenance** (20% weight)
   - Last update > 2 years: 0.2 (abandoned)
   - Last update 1-2 years: 0.5 (stale)
   - Last update 6-12 months: 0.7
   - Last update < 6 months: 1.0 (active)

#### Risk Thresholds

- **< 0.3**: High risk (flagged as security finding)
- **0.3-0.6**: Medium risk (warning)
- **0.6-0.8**: Low risk (informational)
- **> 0.8**: Trusted

#### Configuration

```bash
# Enable reputation scoring (default: true)
REPUTATION_ENABLED=true

# Reputation score threshold for flagging (default: 0.3)
REPUTATION_THRESHOLD=0.3

# Rate limit for registry API calls (requests/second, default: 10)
REPUTATION_RATE_LIMIT=10

# Timeout for registry API calls in seconds (default: 5)
REPUTATION_TIMEOUT=5
```

#### Usage Example

```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)

# Calculate reputation for any ecosystem
npm_rep = scorer.calculate_reputation("suspicious-pkg", "npm")
python_rep = scorer.calculate_reputation("malicious-setup", "pypi")

print(f"Score: {npm_rep['score']:.2f}")
print(f"Flags: {npm_rep['flags']}")
print(f"Age score: {npm_rep['factors']['age_score']:.2f}")
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest hypothesis

# Run all tests
pytest

# Run property-based tests
pytest -k "property"
```

### Project Status

This project is production-ready with the following components:

- [x] Core project structure
- [x] Python ecosystem support (setup.py, requirements.txt)
- [x] npm ecosystem support (package.json, scripts)
- [x] Intelligent caching system (SQLite/Redis)
- [x] Package reputation scoring
- [x] SBOM processing tools
- [x] GitHub integration
- [x] Local directory analysis
- [x] AI agent implementations
- [x] Multi-agent coordination
- [x] Visual security analysis
- [x] Comprehensive reporting
- [x] Web interface
- [x] Property-based testing
- [ ] CI/CD integration (planned)
- [ ] Additional ecosystems (Java, Go, Rust - planned)

## Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast reference for common tasks
- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive usage examples
- **[CONFIGURATION.md](CONFIGURATION.md)** - Complete configuration reference
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Detailed troubleshooting guide
- **[tools/cache_manager_usage.md](tools/cache_manager_usage.md)** - Cache system guide
- **[WEBAPP_QUICKSTART.md](WEBAPP_QUICKSTART.md)** - Web interface guide
- **[.kiro/TESTING_GUIDE.md](.kiro/TESTING_GUIDE.md)** - Testing documentation

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## Troubleshooting

### Common Issues

#### Cache Issues

**Problem**: Cache not working or slow performance
```bash
# Check cache statistics
python -c "from tools.cache_manager import CacheManager; print(CacheManager().get_stats())"

# Clear cache and rebuild
python -c "from tools.cache_manager import CacheManager; CacheManager().clear()"
```

**Problem**: "Database is locked" error
- SQLite cache is being accessed by multiple processes
- Solution: Use Redis backend for concurrent access or ensure single process

#### Python Analysis Issues

**Problem**: setup.py parsing fails
- The file may have syntax errors or use unsupported Python features
- Check the error log for details
- The analyzer uses AST parsing and won't execute the code

**Problem**: Missing dependencies not detected
- Ensure requirements.txt is in the project root
- Check that the file format is valid
- Use `pip install requirements-parser` if not installed

#### Reputation Scoring Issues

**Problem**: "Registry API timeout" errors
- Increase timeout: `REPUTATION_TIMEOUT=10`
- Check network connectivity
- Registry may be rate-limiting requests

**Problem**: All packages show low reputation
- Check if registry API is accessible
- Verify package names are correct
- Some packages may genuinely be new/unpopular

#### API Issues

**Problem**: OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and billing
- Reduce `AGENT_MAX_TOKENS` if hitting limits

**Problem**: Rate limiting errors
- Add delays between analyses
- Use caching to reduce API calls
- Consider upgrading API tier

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Support

For questions and support, please open an issue on the project repository.