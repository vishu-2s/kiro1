# Test Screenshot Descriptions for VLM Analysis

This document describes the test screenshots that should be created for VLM (Vision Language Model) testing. These screenshots should contain various security indicators and UI anomalies for the visual security analysis system to detect.

## Required Test Screenshots

### 1. security-warning-dialog.png
**Description**: A browser security warning dialog
**Content**:
- Browser security warning: "This site may be harmful"
- Red warning icon
- "Proceed anyway" and "Go back" buttons
- URL showing suspicious domain: "malicious-site.tk"
- Certificate error indicators

### 2. malware-download-prompt.png  
**Description**: A suspicious download prompt
**Content**:
- File download dialog for "update.exe" 
- Warning text: "This file may harm your computer"
- Download source: "unknown-publisher.ml"
- File size: 2.3 MB
- "Keep" and "Discard" buttons

### 3. phishing-login-page.png
**Description**: A fake login page mimicking a legitimate service
**Content**:
- Fake GitHub login page with slight URL misspelling: "githup.com"
- Username and password fields
- "Sign in" button
- Suspicious elements like poor styling or typos
- Browser address bar showing the fake URL

### 4. npm-install-warnings.png
**Description**: Terminal showing npm install with security warnings
**Content**:
- Terminal window with npm install command
- Multiple security warnings:
  - "npm WARN deprecated event-stream@3.3.6"
  - "found 5 vulnerabilities (3 high, 2 critical)"
  - "run npm audit fix to fix them"
- Package installation progress with suspicious package names

### 5. dependency-vulnerability-alert.png
**Description**: GitHub Dependabot security alert
**Content**:
- GitHub security alert interface
- "Critical vulnerability in log4j-core"
- CVE-2021-44228 (Log4Shell)
- Affected versions and fix recommendations
- "Create security update" button

### 6. suspicious-network-activity.png
**Description**: Network monitoring tool showing suspicious connections
**Content**:
- Network monitoring interface (like Wireshark or similar)
- Outbound connections to suspicious domains:
  - "data-collector.tk"
  - "mining-pool.cf" 
  - "evil-server.ml"
- High data transfer volumes
- Cryptocurrency mining pool connections

### 7. fake-antivirus-popup.png
**Description**: Fake antivirus warning popup
**Content**:
- Fake antivirus alert: "Your computer is infected!"
- Countdown timer: "Remove viruses now!"
- "Download AntiVirus Pro" button
- Suspicious branding and poor design quality
- Pop-up window styling

### 8. code-injection-attempt.png
**Description**: Code editor showing potential injection attempt
**Content**:
- Code editor (VS Code or similar) 
- JavaScript code with suspicious patterns:
  - `eval(atob('base64encodedcode'))`
  - `document.cookie` access
  - Network requests to suspicious domains
- Syntax highlighting showing the malicious code

### 9. package-manager-typosquat.png
**Description**: Package manager showing typosquat packages
**Content**:
- Package manager interface (npm, pip, etc.)
- Search results showing:
  - "requessts" (typosquat of "requests")
  - "urllib4" (typosquat of "urllib3") 
  - "python3-dateutil" (typosquat of "python-dateutil")
- Download counts and suspicious publisher names

### 10. ci-cd-pipeline-failure.png
**Description**: CI/CD pipeline failing due to security issues
**Content**:
- CI/CD interface (GitHub Actions, Jenkins, etc.)
- Failed build with security-related errors:
  - "Security scan failed: 8 critical vulnerabilities"
  - "Malicious package detected: event-stream@3.3.6"
  - "Deployment blocked due to security issues"
- Red failure indicators and error logs

## Screenshot Creation Instructions

To create these screenshots for testing:

1. **Use browser developer tools** to create realistic security warnings
2. **Set up test environments** with vulnerable packages to capture real warnings
3. **Use screenshot tools** like browser extensions or OS screenshot utilities
4. **Ensure high quality** - images should be clear and readable for VLM analysis
5. **Include realistic details** - URLs, package names, version numbers should match test data
6. **Vary the layouts** - different browsers, terminals, and tools for diversity

## File Naming Convention

Save screenshots in the `screenshots/` directory with descriptive names:
- `security-warning-dialog.png`
- `malware-download-prompt.png`
- `phishing-login-page.png`
- etc.

## Usage in Tests

These screenshots will be used by:
- VLM tools for visual security analysis
- Property-based tests for image processing
- Integration tests for multi-modal security analysis
- Agent testing for visual finding correlation