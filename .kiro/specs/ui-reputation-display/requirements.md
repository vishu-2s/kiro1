# Requirements Document

## Introduction

The Multi-Agent Security Analysis System web UI currently displays vulnerability findings from the orchestrator's JSON output (`outputs/demo_ui_comprehensive_report.json`), but does not display reputation analysis findings. The orchestrator always writes its output to `demo_ui_comprehensive_report.json`, overwriting it with each new analysis. The orchestrator returns a package-centric JSON structure where each package can have both vulnerability data and reputation data. The UI needs to be enhanced to parse and display both types of findings from this file in a unified, user-friendly manner.

## Glossary

- **Web UI**: The Flask-based web interface for displaying security analysis reports
- **Orchestrator**: The component that coordinates multiple analysis agents and produces the final JSON report to `outputs/demo_ui_comprehensive_report.json`
- **Output File**: The file `outputs/demo_ui_comprehensive_report.json` that is overwritten by the orchestrator with each new analysis
- **Package-Centric Format**: JSON structure where findings are organized by package, with each package containing multiple types of analysis results
- **Vulnerability Finding**: Security vulnerability detected in a package (CVEs, known exploits)
- **Reputation Finding**: Risk assessment based on package metadata (age, downloads, author, maintenance)
- **Security Finding**: Generic term for any security-related issue (vulnerability or reputation concern)

## Requirements

### Requirement 1

**User Story:** As a security analyst, I want to see both vulnerability and reputation findings for each package in the web UI, so that I can make informed decisions about package security.

#### Acceptance Criteria

1. WHEN the UI receives a report with packages containing vulnerability data THEN the system SHALL display all vulnerabilities with their severity, CVSS scores, and descriptions
2. WHEN the UI receives a report with packages containing reputation data THEN the system SHALL display reputation scores, risk levels, and risk factors
3. WHEN a package has both vulnerability and reputation data THEN the system SHALL display both types of findings grouped under that package
4. WHEN displaying findings THEN the system SHALL show the package name and version prominently for each group of findings
5. WHEN multiple packages are analyzed THEN the system SHALL display findings for all packages in the report

### Requirement 2

**User Story:** As a security analyst, I want reputation findings to be visually distinct from vulnerability findings, so that I can quickly understand the type of risk each finding represents.

#### Acceptance Criteria

1. WHEN displaying a reputation finding THEN the system SHALL use a distinct visual indicator (icon, color, or label) to differentiate it from vulnerability findings
2. WHEN displaying reputation risk factors THEN the system SHALL show each factor with its severity level and description
3. WHEN displaying reputation scores THEN the system SHALL show the overall score and individual component scores (age, downloads, author, maintenance)
4. WHEN a package has low reputation THEN the system SHALL highlight the specific risk factors that contributed to the low score
5. WHEN displaying findings THEN the system SHALL maintain consistent styling with the existing UI design

### Requirement 3

**User Story:** As a security analyst, I want the summary statistics to accurately reflect all findings including reputation issues, so that I can quickly assess the overall security posture.

#### Acceptance Criteria

1. WHEN calculating total findings THEN the system SHALL count both vulnerability findings and reputation findings
2. WHEN calculating severity counts THEN the system SHALL map reputation risk levels to severity levels (critical/high/medium/low)
3. WHEN displaying the findings count THEN the system SHALL show the total across all finding types
4. WHEN a package has multiple findings of different types THEN the system SHALL count each finding separately in the totals
5. WHEN the report contains no findings THEN the system SHALL display an appropriate message indicating no security issues were detected

### Requirement 4

**User Story:** As a developer, I want the UI parsing logic to handle various JSON formats gracefully, so that the system remains robust as the orchestrator output evolves.

#### Acceptance Criteria

1. WHEN parsing package data THEN the system SHALL handle packages with only vulnerability data
2. WHEN parsing package data THEN the system SHALL handle packages with only reputation data
3. WHEN parsing package data THEN the system SHALL handle packages with both vulnerability and reputation data
4. WHEN parsing package data THEN the system SHALL handle missing or null fields without crashing
5. WHEN parsing fails for a specific package THEN the system SHALL log the error and continue processing other packages
