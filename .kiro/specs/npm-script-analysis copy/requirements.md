# Requirements Document

## Introduction

This feature adds detection and analysis of malicious npm lifecycle scripts in package.json files. npm lifecycle scripts (preinstall, postinstall, preuninstall, postuninstall, etc.) can execute arbitrary commands during package installation, making them a common vector for supply chain attacks. The system currently extracts dependencies from package.json but does not analyze the scripts field for suspicious or malicious commands.

## Glossary

- **npm**: Node Package Manager, the default package manager for Node.js
- **Lifecycle Script**: Automated scripts that run at specific points during package installation/uninstallation
- **package.json**: The manifest file for npm packages containing metadata and dependencies
- **System**: The Multi-Agent Security Analysis System
- **Malicious Script**: A script containing commands that could compromise security (e.g., downloading and executing remote code, exfiltrating data)
- **Suspicious Pattern**: Code patterns commonly associated with malicious behavior (e.g., curl piped to sh, base64 encoded commands)

## Requirements

### Requirement 1

**User Story:** As a security analyst, I want to detect malicious lifecycle scripts in package.json files, so that I can identify supply chain attacks before they execute.

#### Acceptance Criteria

1. WHEN the System analyzes a package.json file THEN the System SHALL extract and examine all lifecycle scripts
2. WHEN a lifecycle script contains suspicious network patterns THEN the System SHALL flag it as a security finding
3. WHEN a lifecycle script contains command execution patterns THEN the System SHALL flag it as a security finding
4. WHEN a lifecycle script contains obfuscation patterns THEN the System SHALL flag it as a security finding
5. WHEN multiple suspicious patterns are detected in a single script THEN the System SHALL increase the confidence score accordingly

### Requirement 2

**User Story:** As a developer, I want to understand why a script was flagged as malicious, so that I can assess the risk and take appropriate action.

#### Acceptance Criteria

1. WHEN a malicious script is detected THEN the System SHALL provide the script name and content as evidence
2. WHEN a malicious script is detected THEN the System SHALL list all suspicious patterns found
3. WHEN a malicious script is detected THEN the System SHALL assign a severity level based on the threat
4. WHEN a malicious script is detected THEN the System SHALL provide actionable recommendations
5. WHEN a malicious script is detected THEN the System SHALL calculate a confidence score based on pattern matches

### Requirement 3

**User Story:** As a security engineer, I want the system to recognize common attack patterns in npm scripts, so that I can catch both known and novel threats.

#### Acceptance Criteria

1. WHEN a script downloads and executes remote code THEN the System SHALL classify it as critical severity
2. WHEN a script contains base64 or hex encoded commands THEN the System SHALL classify it as high severity
3. WHEN a script modifies system files or environment variables THEN the System SHALL classify it as high severity
4. WHEN a script makes network requests to suspicious domains THEN the System SHALL classify it as medium to high severity
5. WHEN a script uses eval or similar dynamic execution THEN the System SHALL classify it as medium severity

### Requirement 4

**User Story:** As a system administrator, I want benign scripts to not trigger false positives, so that I can focus on real threats.

#### Acceptance Criteria

1. WHEN a script contains only standard build commands THEN the System SHALL not flag it as malicious
2. WHEN a script uses common development tools THEN the System SHALL not flag it as malicious
3. WHEN a script performs legitimate file operations THEN the System SHALL not flag it as malicious
4. WHEN calculating confidence scores THEN the System SHALL consider context and common patterns
5. WHEN a script matches both benign and suspicious patterns THEN the System SHALL adjust confidence accordingly

### Requirement 5

**User Story:** As a developer using the web interface, I want script analysis findings to appear in my reports, so that I can see all security issues in one place.

#### Acceptance Criteria

1. WHEN malicious scripts are detected THEN the System SHALL include them in the security findings list
2. WHEN displaying script findings THEN the System SHALL group them with the package they belong to
3. WHEN displaying script findings THEN the System SHALL show the finding type as "malicious_script"
4. WHEN displaying script findings THEN the System SHALL include the script name in the finding title
5. WHEN displaying script findings THEN the System SHALL format the evidence for readability
