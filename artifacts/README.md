# Test Artifacts and Sample Data

This directory contains sample artifacts and test data for the Multi-Agent Security Analysis System. These files are used for testing various components of the system including SBOM processing, vulnerability detection, and security analysis.

## SBOM Files

### backend-sbom.json
A comprehensive SBOM file in CycloneDX format containing known vulnerable packages across multiple ecosystems:
- **npm**: event-stream, flatmap-stream, http-fetch, crossenv, babelcli, cross-env.js
- **pypi**: python3-dateutil, urllib4, requessts, beautifulsoup, pip-tools, colorama, ctx, phpass, jeIlyfish
- **maven**: log4j-core (Log4Shell), spring-core (Spring4Shell), xstream
- **rubygems**: rest-client, strong_password, bootstrap-sass
- **crates**: rustdecimal, rand-core
- **go**: beego, unknwon/cae

## Package Files

### sample-package.json
Node.js package.json file with vulnerable dependencies including:
- Malicious packages: event-stream@3.3.6, flatmap-stream@0.1.1
- Typosquat packages: http-fetch, crossenv, babelcli, cross-env.js
- Legitimate packages: express, lodash, axios, moment

### sample-requirements.txt
Python requirements.txt file with vulnerable packages including:
- Typosquat packages: python3-dateutil, urllib4, requessts, beautifulsoup
- Malicious packages: pip-tools@6.6.0, colorama@0.4.6, ctx, phpass
- Character substitution typosquats: jeIlyfish (capital i as l)

### sample-pom.xml
Maven pom.xml file with vulnerable Java dependencies including:
- Log4j Core 2.14.1 (vulnerable to Log4Shell CVE-2021-44228)
- Spring Core 5.3.18 (vulnerable to Spring4Shell)
- XStream 1.4.15 (remote code execution vulnerability)

## Security Data

### sample-security-alerts.json
GitHub security alerts data including:
- Critical malicious package alerts (event-stream)
- Log4Shell vulnerability alerts
- Typosquat package alerts (urllib4)
- Various alert states: open, dismissed, fixed

### sample-dependabot-alerts.json
Dependabot security alerts with detailed vulnerability information:
- CVSS scores and severity ratings
- Vulnerable version ranges and patched versions
- Alert lifecycle states and dismissal reasons

### sample-osv-response.json
OSV (Open Source Vulnerabilities) API response data containing:
- Detailed vulnerability information
- GHSA and CVE identifiers
- Affected package versions and ecosystems
- References and remediation guidance

## CI/CD Data

### sample-ci-logs.txt
CI/CD pipeline logs showing suspicious activities:
- Malicious package installations
- Suspicious network requests to .tk, .ml, .cf domains
- Base64 encoded code execution
- Cryptocurrency mining attempts
- Data exfiltration to Discord webhooks
- Environment variable theft

### sample-workflow-runs.json
GitHub Actions workflow run data including:
- Failed security scans
- Successful remediation workflows
- Commit information and triggering events
- Pull request associations

## Repository Data

### sample-repository-data.json
GitHub repository metadata including:
- Repository information and statistics
- Security feature configurations
- Package file locations and metadata
- Vulnerability alert summaries

## Visual Test Data

### screenshot-descriptions.md
Detailed descriptions of test screenshots that should be created for VLM testing:
- Security warning dialogs
- Malware download prompts
- Phishing login pages
- Package manager warnings
- CI/CD pipeline failures

### screenshots/ directory
Text representations of visual security indicators:
- `security-warning-text.txt`: Browser security warnings
- `npm-warnings-text.txt`: npm install security warnings
- `github-alert-text.txt`: GitHub security alert interface
- `phishing-page-text.txt`: Fake login page content
- `malware-download-text.txt`: Suspicious download prompts

## Usage in Testing

These artifacts are used by:

1. **SBOM Tools Tests**: Parsing and validation of SBOM formats
2. **Vulnerability Detection Tests**: Cross-referencing against malicious package databases
3. **OSV API Integration Tests**: Mock responses for API testing
4. **GitHub Tools Tests**: Repository data processing and alert handling
5. **VLM Tools Tests**: Visual security indicator detection
6. **Agent Tests**: Multi-agent collaboration and finding correlation
7. **Property-Based Tests**: Generating test data for correctness properties
8. **Integration Tests**: End-to-end analysis workflows

## Data Characteristics

The test data includes:
- **Known vulnerabilities**: Real CVEs and security issues
- **Typosquat patterns**: Common character substitutions and misspellings
- **Malicious behaviors**: Network requests, code execution, data exfiltration
- **Multiple ecosystems**: npm, PyPI, Maven, RubyGems, Crates.io, Go modules
- **Various severity levels**: Critical, high, medium, low risk findings
- **Different alert states**: Open, dismissed, fixed security alerts

## Maintenance

When updating test data:
1. Keep vulnerability information current with real-world threats
2. Add new typosquat patterns as they emerge
3. Include diverse package ecosystems and file formats
4. Maintain realistic metadata and timestamps
5. Ensure data consistency across related files

This test data provides comprehensive coverage for validating the security analysis system's ability to detect various types of supply chain attacks and vulnerabilities.