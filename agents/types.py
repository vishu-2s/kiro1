"""
Shared types and data structures for the multi-agent security analysis system.

This module defines the core data structures used for communication between agents
and the orchestrator, including agent results, findings, and shared context.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class AgentStatus(Enum):
    """Status of an agent execution"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """
    Result from an agent execution with validation and error handling.
    
    This dataclass encapsulates the output from any agent, including success status,
    data payload, error information, and performance metrics.
    
    Attributes:
        agent_name: Name of the agent that produced this result
        success: Whether the agent execution succeeded
        data: The actual data/findings from the agent
        error: Error message if execution failed (None if successful)
        duration_seconds: Time taken for agent execution
        status: Detailed status of the execution
        confidence: Overall confidence score for the agent's findings (0.0-1.0)
    """
    agent_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0.0
    status: AgentStatus = AgentStatus.SUCCESS
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate the agent result after initialization"""
        if not self.success and self.error is None:
            self.error = "Unknown error occurred"
        
        # Only auto-set status if it's still the default SUCCESS
        # This allows explicit status setting (like SKIPPED) to be preserved
        if self.status == AgentStatus.SUCCESS:
            if self.success:
                self.status = AgentStatus.SUCCESS
            elif "timeout" in str(self.error).lower():
                self.status = AgentStatus.TIMEOUT
            else:
                self.status = AgentStatus.FAILED
        
        # Ensure confidence is in valid range
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent result to dictionary for JSON serialization"""
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "confidence": self.confidence
        }


@dataclass
class Finding:
    """
    A security finding from rule-based detection or agent analysis.
    
    Attributes:
        package_name: Name of the package with the finding
        package_version: Version of the package
        finding_type: Type of finding (vulnerability, malicious_code, etc.)
        severity: Severity level (critical, high, medium, low)
        description: Human-readable description of the finding
        detection_method: How the finding was detected (rule_based, agent_analysis)
        confidence: Confidence score (0.0-1.0)
        evidence: Supporting evidence for the finding
        remediation: Suggested remediation steps
    """
    package_name: str
    package_version: str
    finding_type: str
    severity: str
    description: str
    detection_method: str = "rule_based"
    confidence: float = 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary for JSON serialization"""
        return {
            "package_name": self.package_name,
            "package_version": self.package_version,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "description": self.description,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "remediation": self.remediation
        }


@dataclass
class SharedContext:
    """
    Shared context passed between agents during orchestration.
    
    This context accumulates information as agents execute, allowing later agents
    to build on the work of earlier agents.
    
    Attributes:
        initial_findings: Findings from rule-based detection
        dependency_graph: Complete dependency graph structure
        packages: List of unique package names being analyzed
        agent_results: Results from completed agents
        input_mode: Analysis mode ('github' or 'local')
        project_path: Path to the project being analyzed
        ecosystem: Primary ecosystem (npm, pypi, etc.)
        metadata: Additional metadata about the analysis
    """
    initial_findings: List[Finding]
    dependency_graph: Dict[str, Any]
    packages: List[str]
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    input_mode: str = "local"
    project_path: str = ""
    ecosystem: str = "npm"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_agent_result(self, result: AgentResult) -> None:
        """Add an agent result to the shared context"""
        self.agent_results[result.agent_name] = result
    
    def get_agent_result(self, agent_name: str) -> Optional[AgentResult]:
        """Retrieve a specific agent's result"""
        return self.agent_results.get(agent_name)
    
    def has_successful_result(self, agent_name: str) -> bool:
        """Check if an agent completed successfully"""
        result = self.get_agent_result(agent_name)
        return result is not None and result.success
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shared context to dictionary"""
        return {
            "initial_findings": [f.to_dict() for f in self.initial_findings],
            "dependency_graph": self.dependency_graph,
            "packages": self.packages,
            "agent_results": {
                name: result.to_dict() 
                for name, result in self.agent_results.items()
            },
            "input_mode": self.input_mode,
            "project_path": self.project_path,
            "ecosystem": self.ecosystem,
            "metadata": self.metadata
        }


@dataclass
class AgentConfig:
    """
    Configuration for an agent.
    
    Attributes:
        name: Agent name
        timeout: Timeout in seconds
        required: Whether this agent is required for analysis
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
    """
    name: str
    timeout: int
    required: bool = True
    max_retries: int = 2
    retry_delay: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "name": self.name,
            "timeout": self.timeout,
            "required": self.required,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
