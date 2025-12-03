# 🕷️ Spyder - Quick Reference Card

## What is Spyder?

**Spyder** is an AI-powered supply chain security scanner that crawls through your software dependencies to detect malicious packages, vulnerabilities, and supply chain attacks.

## Quick Start

### Web Interface (Recommended)
```bash
python app.py
# Open http://localhost:5000
```

### Command Line
```bash
# Analyze GitHub repository
python main_github.py --github https://github.com/owner/repo

# Analyze local directory
python main_github.py --local /path/to/project

# Analyze SBOM file
python main_github.py --sbom /path/to/sbom.json
```

## Key Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Multi-Agent AI** | Specialized agents for different security analysis tasks |
| 🌐 **Multi-Ecosystem** | npm, PyPI, Maven, RubyGems, Crates, Go |
| 🎯 **High Precision** | Confidence scoring for all findings |
| 📊 **Beautiful Reports** | Interactive web UI with live logs |
| ⚡ **Real-time** | Watch analysis progress in real-time |
| 🔍 **Comprehensive** | Malicious packages, vulnerabilities, typosquats |

## Analysis Modes

### 1. GitHub Repository
```bash
python main_github.py --github https://github.com/expressjs/express
```
- Fetches repository data
- Analyzes dependencies
- Checks Dependabot alerts
- Reviews workflow runs

### 2. Local Directory
```bash
python main_github.py --local C:\Projects\myapp
```
- Scans package files
- Detects multiple ecosystems
- Generates SBOM
- Analyzes dependencies

### 3. SBOM File
```bash
python main_github.py --sbom ./artifacts/backend-sbom.json
```
- Fast analysis
- Cross-references databases
- Queries OSV API
- Generates findings

## Configuration

### Required
```env
OPENAI_API_KEY=your_key_here
```

### Optional
```env
GITHUB_TOKEN=your_token_here
CONFIDENCE_THRESHOLD=0.7
ENABLE_OSV_QUERIES=true
```

## Output

Results saved to `outputs/` directory:
- `{timestamp}_findings.json` - JSON report
- `{timestamp}_report.html` - HTML report

## Severity Levels

| Level | Color | Action |
|-------|-------|--------|
| 🔴 **Critical** | Red | Immediate action required |
| 🟠 **High** | Orange | Address within 24-48 hours |
| 🟡 **Medium** | Yellow | Review and plan remediation |
| 🟢 **Low** | Green | Monitor and address when possible |

## Finding Types

- **Malicious Package** - Known malicious code
- **Vulnerability** - CVE/GHSA vulnerabilities
- **Typosquat** - Suspicious package names
- **Suspicious Keywords** - Dangerous code patterns
- **Network Patterns** - Suspicious network activity

## Common Commands

### Skip Database Update (Faster)
```bash
python main_github.py --github URL --skip-db-update
```

### Disable OSV Queries (Faster)
```bash
python main_github.py --local PATH --no-osv
```

### Custom Confidence Threshold
```bash
python main_github.py --github URL --confidence-threshold 0.8
```

### JSON Output Only
```bash
python main_github.py --github URL --json-only
```

## Web Interface Shortcuts

| Action | Shortcut |
|--------|----------|
| Start Analysis | Click "🚀 Start Analysis" |
| View Logs | Dashboard tab (auto-updates) |
| View Report | Report tab (after completion) |
| Switch Modes | Click mode buttons (GitHub/Local) |

## Troubleshooting

### Port Already in Use
Edit `app.py` line 165:
```python
app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
```

### No API Key
Create `.env` file:
```env
OPENAI_API_KEY=your_key_here
```

### Analysis Not Starting
1. Check console logs
2. Verify API keys
3. Check target path/URL
4. Review Dashboard logs

## Support Ecosystems

| Ecosystem | Package Files |
|-----------|---------------|
| **npm** | package.json, package-lock.json |
| **PyPI** | requirements.txt, setup.py, pyproject.toml |
| **Maven** | pom.xml, build.gradle |
| **RubyGems** | Gemfile, Gemfile.lock |
| **Crates** | Cargo.toml, Cargo.lock |
| **Go** | go.mod, go.sum |

## AI Agents

### SupplyChainAgent
- Dependency analysis
- Malicious package detection
- Typosquat identification

### VlmSecurityAgent
- Visual security analysis
- Screenshot processing
- UI anomaly detection

### OrchestratorAgent
- Finding correlation
- Incident reporting
- Risk assessment

## Performance Tips

1. **Use SBOM mode** for repeated analysis
2. **Skip database update** if recently updated
3. **Disable OSV** for faster local-only checks
4. **Increase confidence** to reduce false positives
5. **Use local mode** for private repositories

## Documentation

- `README.md` - Full documentation
- `START_HERE.md` - Quick start guide
- `WEBAPP_QUICKSTART.md` - Web interface guide
- `WEB_APP_README.md` - Detailed web app docs
- `SPYDER_REBRAND.md` - Branding information

## Version

**Spyder v1.0.0** - AI-Powered Supply Chain Security Scanner

## License

MIT License

---

🕷️ **Spyder** - Catching threats in the dependency web

For detailed documentation, see README.md
For web interface help, see WEBAPP_QUICKSTART.md
For branding info, see SPYDER_REBRAND.md
