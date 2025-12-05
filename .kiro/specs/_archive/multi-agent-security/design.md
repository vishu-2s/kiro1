# Design Document

## Overview

The Multi-Agent Security Analysis System is designed as a modular, AI-powered security analysis platform that leverages multiple specialized agents to provide comprehensive supply chain security analysis. The system uses Microsoft's AutoGen framework to coordinate three specialized agents: SupplyChainAgent for dependency analysis, VlmSecurityAgent for visual security analysis, and OrchestratorAgent for findings correlation and incident reporting.

The architecture follows a layered approach with clear separation between the orchestration layer, agent layer, tool layer, and external service integrations. This design enables scalable analysis of both GitHub repositories and local projects while maintaining up-to-date threat intelligence through automated database updates.

## Architecture

The system follows a multi-layered architecture pattern:

### Orchestration Layer
- **Main Controller** (`main_github.py`): Primary entry point handling command-line interface, configuration management, and analysis workflow coordination
- **Analysis Engine** (`analyze_supply_chain.py`): Core analysis logic that processes SBOM data, security alerts, and CI/CD logs
- **Update Manager** (`update_constants.py`): Automated threat intelligence updates with 24-hour caching mechanism
- **Report Generator** (`report_generator.py`): HTML report generation with executive summaries and remediation guidance

### Agent Layer (AutoGen Framework)
- **SupplyChainAgent**: Specialized in dependency analysis, malicious package detection, and vulnerability assessment
- **VlmSecurityAgent**: Focused on visual security analysis using GPT-4 Vision for screenshot processing
- **OrchestratorAgent**: Responsible for correlating findings across agents and generating comprehensive incident reports
- **GroupChatManager**: AutoGen's coordination mechanism for multi-agent collaboration

### Tool Layer
- **SBOM Tools** (`sbom_tools.py`): Software Bill of Materials parsing, vulnerability detection, and OSV API integration
- **Security Alert Tools** (`sca_tools.py`): Processing of security alerts and correlation with SBOM data
- **CI/CD Tools** (`ci_tools.py`): Analysis of build logs for suspicious activities and dependency changes
- **GitHub Tools** (`github_tools.py`): GitHub API integration for repository data fetching and SBOM generation
- **Local Tools** (`local_tools.py`): Local directory scanning and multi-ecosystem package file analysis
- **VLM Tools** (`vlm_tools.py`): Vision Language Model integration for image analysis

### External Service Layer
- **OSV API**: Open Source Vulnerabilities database for CVE information and malicious package data
- **GitHub API**: Repository metadata, Dependabot alerts, and workflow information
- **OpenAI API**: GPT-4 for text analysis and GPT-4 Vision for image processing

## Components and Interfaces

### Agent Interfaces

```python
# Base agent creation interface
def create_agent(llm_config: Optional[dict] = None) -> AssistantAgent:
    """Creates specialized agent with embedded security signatures and detection logic"""
    pass

# Agent communication protocol
class AgentMessage:
    agent_name: str
    message_type: str  # "finding", "request", "response"
    content: Dict[str, Any]
    timestamp: datetime
```

### Tool Function Interfaces

```python
# SBOM processing interface
def read_sbom(path: str) -> Dict[str, Any]:
    """Parses SBOM files and returns structured package data"""
    pass

def check_vulnerable_packages(sbom_data: Dict, use_osv: bool = True) -> List[Dict]:
    """Cross-references packages against malicious databases and OSV API"""
    pass

# GitHub integration interface
def fetch_repository_data(repo_url: str) -> Dict:
    """Fetches comprehensive repository data including dependencies and alerts"""
    pass

# Local analysis interface
def analyze_local_path(path: str) -> Dict:
    """Scans local directories and generates SBOM from discovered package files"""
    pass
```

### Data Flow Interfaces

```python
# Analysis pipeline interface
class AnalysisResult:
    status: str  # "success", "error", "partial"
    findings: List[SecurityFinding]
    metadata: Dict[str, Any]
    timestamp: datetime

class SecurityFinding:
    package: str
    version: str
    indicator_type: str  # "malicious_package", "vulnerability", "typosquat"
    severity: str  # "critical", "high", "medium", "low"
    confidence_score: float
    evidence: List[str]
    recommended_actions: List[str]
```

## Data Models

### Core Data Structures

```python
# SBOM Data Model
class SBOMPackage:
    name: str
    version: str
    purl: str  # Package URL
    ecosystem: str  # "npm", "pypi", "maven", etc.
    dependencies: List[str]
    metadata: Dict[str, Any]

# Vulnerability Data Model
class Vulnerability:
    id: str  # CVE or GHSA identifier
    summary: str
    severity_score: float
    affected_versions: List[str]
    fixed_versions: List[str]
    references: List[str]

# Security Alert Data Model
class SecurityAlert:
    alert_id: str
    package_name: str
    vulnerability: Vulnerability
    state: str  # "open", "dismissed", "fixed"
    created_at: datetime
    updated_at: datetime

# Analysis Finding Data Model
class AnalysisFinding:
    finding_id: str
    package: str
    version: str
    finding_type: str
    severity: str
    confidence: float
    evidence: List[Evidence]
    recommendations: List[str]
    agent_source: str

class Evidence:
    type: str  # "signature_match", "api_response", "pattern_detection"
    description: str
    data: Dict[str, Any]
```

### Configuration Models

```python
# System Configuration
class SystemConfig:
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_vision_model: str = "gpt-4-vision-preview"
    github_token: Optional[str] = None
    cache_enabled: bool = True
    cache_duration_hours: int = 24
    output_directory: str = "outputs"

# Agent Configuration
class AgentConfig:
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_seconds: int = 120
    max_rounds: int = 12
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*
Base
d on the prework analysis, I can identify several properties that can be consolidated to eliminate redundancy:

**Property Reflection:**
- Properties 1.1, 2.1 can be combined into a general "data fetching" property
- Properties 1.2, 2.2 can be combined into a general "SBOM generation" property  
- Properties 1.3, 2.4 can be combined into a general "security database checking" property
- Properties 3.1, 3.5 can be combined into a general "cache validation" property
- Properties 4.1, 4.2, 4.3 can be combined into a general "agent initialization" property
- Properties 8.1, 8.2, 8.3 can be combined into a general "API integration" property

### Property 1: Data Source Processing
*For any* valid data source (GitHub repository URL or local directory path), the system should successfully fetch or scan all available package files and metadata
**Validates: Requirements 1.1, 2.1**

### Property 2: SBOM Generation Consistency  
*For any* set of discovered package files, the system should generate a valid SBOM structure with all required fields populated
**Validates: Requirements 1.2, 2.2**

### Property 3: Security Database Cross-Reference
*For any* package in an SBOM, the system should check it against the malicious package database and return consistent results regardless of analysis mode
**Validates: Requirements 1.3, 2.4**

### Property 4: OSV API Integration
*For any* detected malicious package, the system should query the OSV API and retrieve additional vulnerability information
**Validates: Requirements 1.4**

### Property 5: Structured Output Generation
*For any* completed analysis, the system should generate findings in valid JSON format with all required fields
**Validates: Requirements 1.5**

### Property 6: Ecosystem Detection Accuracy
*For any* package file from supported ecosystems, the system should correctly identify the ecosystem type
**Validates: Requirements 2.3**

### Property 7: Output Persistence
*For any* completed analysis, the system should save findings to the specified output directory with proper file structure
**Validates: Requirements 2.5**

### Property 8: Cache Validation Logic
*For any* system startup or force update request, the cache age validation should correctly determine whether to fetch fresh data
**Validates: Requirements 3.1, 3.5**

### Property 9: Database Update Consistency
*For any* successful OSV API query, the system should update both the constants file and cache file with consistent data
**Validates: Requirements 3.2, 3.3, 3.4**

### Property 10: Agent Initialization
*For any* analysis request, the system should initialize the appropriate agents based on the analysis type and available data
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 11: Agent Communication
*For any* active multi-agent analysis, agents should successfully exchange messages through the GroupChat mechanism
**Validates: Requirements 4.4**

### Property 12: Finding Compilation
*For any* multi-agent analysis, all agent findings should be aggregated into a unified report structure
**Validates: Requirements 4.5**

### Property 13: Threat Detection Accuracy
*For any* package analysis, the system should detect typosquatting, suspicious scripts, network patterns, and anomalous characteristics with appropriate confidence scores
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 14: Image Processing Pipeline
*For any* provided screenshot, the system should encode it to base64, process it with GPT-4 Vision, and extract structured findings
**Validates: Requirements 6.1, 6.2, 6.5**

### Property 15: Visual Security Detection
*For any* image containing security indicators, the system should detect warnings, alerts, and UI anomalies
**Validates: Requirements 6.3**

### Property 16: Visual-Package Correlation
*For any* visual findings, the system should correlate them with relevant package data when possible
**Validates: Requirements 6.4**

### Property 17: Comprehensive Reporting
*For any* completed analysis, the system should generate reports with risk assessment, attack classification, containment steps, remediation plans, timeline, and stakeholder guidance
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 18: Dual Output Format
*For any* completed analysis, the system should generate both JSON findings and HTML reports
**Validates: Requirements 7.5**

### Property 19: External API Integration
*For any* API call to OSV, GitHub, or OpenAI, the system should handle authentication, rate limiting, and error conditions appropriately
**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 20: API Response Processing
*For any* API response, the system should parse and structure the data for agent consumption
**Validates: Requirements 8.5**

### Property 21: Configuration Management
*For any* system startup, configuration should be loaded from environment variables and files, and command-line flags should override default behavior
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

## Error Handling

The system implements comprehensive error handling across all layers:

### API Error Handling
- **Rate Limiting**: Implement exponential backoff for API rate limits
- **Authentication Failures**: Graceful degradation when API keys are invalid or missing
- **Network Timeouts**: Configurable timeout values with retry mechanisms
- **Malformed Responses**: Validation and sanitization of all API responses

### File System Error Handling
- **Missing Files**: Clear error messages when SBOM or configuration files are not found
- **Permission Errors**: Proper handling of file system permission issues
- **Disk Space**: Validation of available disk space before writing large reports
- **Path Validation**: Sanitization of user-provided file paths

### Agent Error Handling
- **Agent Initialization Failures**: Fallback mechanisms when agents cannot be created
- **Communication Timeouts**: Timeout handling for agent-to-agent communication
- **Invalid Responses**: Validation of agent responses and handling of malformed outputs
- **Resource Exhaustion**: Memory and CPU usage monitoring with graceful degradation

### Data Validation Error Handling
- **SBOM Format Validation**: Support for multiple SBOM formats with validation
- **Package Name Sanitization**: Handling of malformed or suspicious package names
- **Version String Parsing**: Robust parsing of various version string formats
- **Ecosystem Detection Failures**: Fallback mechanisms when ecosystem cannot be determined

## Testing Strategy

The system employs a dual testing approach combining unit tests for specific functionality and property-based tests for universal correctness properties.

### Unit Testing Approach
Unit tests will focus on:
- **Specific API Integration Examples**: Testing known GitHub repositories and OSV responses
- **File Format Parsing**: Testing specific SBOM formats and package file structures  
- **Agent Response Validation**: Testing specific agent message formats and responses
- **Configuration Loading**: Testing specific environment variable and file combinations
- **Error Condition Handling**: Testing specific error scenarios and recovery mechanisms

### Property-Based Testing Approach
Property-based tests will use **Hypothesis** for Python to verify universal properties across randomized inputs. Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage.

**Property-Based Testing Library**: Hypothesis (Python)
**Test Configuration**: Minimum 100 iterations per property test
**Test Tagging**: Each property-based test must include a comment with the format: `**Feature: multi-agent-security, Property {number}: {property_text}**`

Property-based tests will generate:
- **Random Repository URLs**: Testing GitHub API integration with various valid repository formats
- **Random Package Files**: Testing SBOM generation with various package.json, requirements.txt, and other ecosystem files
- **Random Package Names**: Testing typosquatting detection with generated package names similar to popular packages
- **Random SBOM Structures**: Testing vulnerability detection across various SBOM formats and package combinations
- **Random Configuration Combinations**: Testing system behavior with various environment variable and flag combinations

### Integration Testing
- **End-to-End Analysis Workflows**: Testing complete analysis pipelines from input to report generation
- **Multi-Agent Collaboration**: Testing agent communication and finding correlation
- **External API Integration**: Testing real API calls with rate limiting and error handling
- **File System Operations**: Testing file reading, writing, and directory operations

### Test Data Management
- **Sample Repositories**: Curated set of test repositories with known vulnerabilities
- **Mock API Responses**: Cached responses for consistent testing without API dependencies
- **Test Artifacts**: Sample SBOM files, security alerts, and CI/CD logs for testing
- **Visual Test Data**: Sample screenshots with known security indicators for VLM testing

The testing strategy ensures both concrete functionality validation through unit tests and general correctness verification through property-based testing, providing comprehensive coverage of the system's security analysis capabilities.