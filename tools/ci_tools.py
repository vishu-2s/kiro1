"""
CI/CD log analysis and suspicious activity detection tools for Multi-Agent Security Analysis System.

This module provides functions for:
- CI/CD log analysis for suspicious activities
- Dependency change detection in build logs
- Suspicious install hooks and lifecycle scripts detection
- Build process anomaly identification
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from constants import SUSPICIOUS_KEYWORDS, contains_suspicious_keywords, detect_suspicious_network_patterns
from tools.sbom_tools import SecurityFinding
from config import config

logger = logging.getLogger(__name__)

class CILogEntry:
    """Represents a CI/CD log entry."""
    
    def __init__(self, timestamp: str, level: str, message: str, 
                 job_id: Optional[str] = None, step_name: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.timestamp = timestamp
        self.level = level.upper()
        self.message = message
        self.job_id = job_id
        self.step_name = step_name
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "job_id": self.job_id,
            "step_name": self.step_name,
            "metadata": self.metadata
        }

class SuspiciousActivity:
    """Represents a suspicious activity detected in CI/CD logs."""
    
    def __init__(self, activity_type: str, description: str, evidence: List[str],
                 confidence: float, severity: str, log_entries: List[CILogEntry],
                 metadata: Optional[Dict[str, Any]] = None):
        self.activity_type = activity_type
        self.description = description
        self.evidence = evidence
        self.confidence = confidence
        self.severity = severity
        self.log_entries = log_entries
        self.metadata = metadata or {}
        self.detected_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suspicious activity to dictionary representation."""
        return {
            "activity_type": self.activity_type,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "severity": self.severity,
            "log_entries": [entry.to_dict() for entry in self.log_entries],
            "metadata": self.metadata,
            "detected_at": self.detected_at
        }

def parse_ci_logs(log_content: str, log_format: str = "auto") -> List[CILogEntry]:
    """
    Parse CI/CD logs into structured log entries.
    
    Args:
        log_content: Raw log content
        log_format: Log format ("github_actions", "jenkins", "gitlab", "auto")
    
    Returns:
        List of CILogEntry objects
    """
    if log_format == "auto":
        log_format = _detect_log_format(log_content)
    
    if log_format == "github_actions":
        return _parse_github_actions_logs(log_content)
    elif log_format == "jenkins":
        return _parse_jenkins_logs(log_content)
    elif log_format == "gitlab":
        return _parse_gitlab_logs(log_content)
    else:
        return _parse_generic_logs(log_content)

def _detect_log_format(log_content: str) -> str:
    """Detect CI/CD log format from content."""
    content_lower = log_content.lower()
    
    if "##[" in log_content and "github.com" in content_lower:
        return "github_actions"
    elif "started by user" in content_lower or "jenkins" in content_lower:
        return "jenkins"
    elif "job succeeded" in content_lower or "gitlab" in content_lower:
        return "gitlab"
    else:
        return "generic"

def _parse_github_actions_logs(log_content: str) -> List[CILogEntry]:
    """Parse GitHub Actions logs."""
    entries = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # GitHub Actions format: timestamp ##[level]message
        match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+##\[(\w+)\](.+)$', line)
        if match:
            timestamp, level, message = match.groups()
            entry = CILogEntry(
                timestamp=timestamp,
                level=level,
                message=message.strip(),
                metadata={"format": "github_actions"}
            )
            entries.append(entry)
        else:
            # Fallback for lines without proper format
            entry = CILogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                message=line,
                metadata={"format": "github_actions", "unparsed": True}
            )
            entries.append(entry)
    
    return entries

def _parse_jenkins_logs(log_content: str) -> List[CILogEntry]:
    """Parse Jenkins logs."""
    entries = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Jenkins format varies, try common patterns
        # Pattern 1: [timestamp] level: message
        match = re.match(r'^\[([^\]]+)\]\s+(\w+):\s*(.+)$', line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                # Try to parse timestamp
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").isoformat()
            except ValueError:
                timestamp = datetime.now().isoformat()
            
            entry = CILogEntry(
                timestamp=timestamp,
                level=level,
                message=message.strip(),
                metadata={"format": "jenkins"}
            )
            entries.append(entry)
        else:
            # Fallback
            entry = CILogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                message=line,
                metadata={"format": "jenkins", "unparsed": True}
            )
            entries.append(entry)
    
    return entries

def _parse_gitlab_logs(log_content: str) -> List[CILogEntry]:
    """Parse GitLab CI logs."""
    entries = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # GitLab format: timestamp level message
        match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)$', line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").isoformat()
            except ValueError:
                timestamp = datetime.now().isoformat()
            
            entry = CILogEntry(
                timestamp=timestamp,
                level=level,
                message=message.strip(),
                metadata={"format": "gitlab"}
            )
            entries.append(entry)
        else:
            entry = CILogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                message=line,
                metadata={"format": "gitlab", "unparsed": True}
            )
            entries.append(entry)
    
    return entries

def _parse_generic_logs(log_content: str) -> List[CILogEntry]:
    """Parse generic log format."""
    entries = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        entry = CILogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            message=line,
            metadata={"format": "generic"}
        )
        entries.append(entry)
    
    return entries

def detect_suspicious_install_hooks(log_entries: List[CILogEntry]) -> List[SuspiciousActivity]:
    """
    Detect suspicious install hooks and lifecycle scripts in CI/CD logs.
    
    Args:
        log_entries: List of parsed log entries
    
    Returns:
        List of suspicious activities detected
    """
    suspicious_activities = []
    
    # Patterns for suspicious install hooks
    suspicious_patterns = [
        # npm lifecycle scripts
        r'npm\s+run\s+(?:preinstall|postinstall|preuninstall|postuninstall)',
        r'running\s+(?:preinstall|postinstall)\s+script',
        
        # Python setup.py hooks
        r'python\s+setup\.py\s+(?:install|develop)',
        r'running\s+(?:install|develop)\s+for',
        
        # Suspicious shell commands in install scripts
        r'(?:curl|wget|nc|netcat)\s+[^\s]+',
        r'(?:bash|sh|cmd|powershell)\s+-c\s+["\']',
        r'eval\s*\(["\']',
        r'base64\s+(?:-d|--decode)',
        
        # Network activity during install
        r'connecting\s+to\s+(?:\d{1,3}\.){3}\d{1,3}',
        r'downloading\s+from\s+(?:http|ftp)://[^\s]+',
        
        # File system modifications
        r'(?:rm|del|rmdir)\s+(?:-rf|/s)\s+[^\s]+',
        r'chmod\s+(?:\+x|\d{3,4})\s+[^\s]+',
        r'chown\s+[^\s]+\s+[^\s]+',
    ]
    
    for pattern in suspicious_patterns:
        matching_entries = []
        
        for entry in log_entries:
            if re.search(pattern, entry.message, re.IGNORECASE):
                matching_entries.append(entry)
        
        if matching_entries:
            activity = SuspiciousActivity(
                activity_type="suspicious_install_hook",
                description=f"Detected suspicious install hook pattern: {pattern}",
                evidence=[f"Pattern '{pattern}' found in {len(matching_entries)} log entries"],
                confidence=0.7,
                severity="medium",
                log_entries=matching_entries,
                metadata={"pattern": pattern}
            )
            suspicious_activities.append(activity)
    
    return suspicious_activities

def detect_dependency_changes(log_entries: List[CILogEntry]) -> List[SuspiciousActivity]:
    """
    Detect suspicious dependency changes in CI/CD logs.
    
    Args:
        log_entries: List of parsed log entries
    
    Returns:
        List of suspicious dependency change activities
    """
    suspicious_activities = []
    
    # Track dependency installations and changes
    dependency_patterns = [
        # npm
        r'npm\s+(?:install|i)\s+([^\s@]+)(?:@([^\s]+))?',
        r'added\s+(\d+)\s+packages?',
        r'updated\s+(\d+)\s+packages?',
        
        # pip
        r'pip\s+install\s+([^\s=]+)(?:==([^\s]+))?',
        r'Successfully\s+installed\s+([^\n]+)',
        
        # Maven/Gradle
        r'Downloading\s+from\s+[^\s]+:\s+([^\s]+)',
        r'Downloaded\s+from\s+[^\s]+:\s+([^\s]+)',
        
        # Ruby gems
        r'gem\s+install\s+([^\s]+)',
        r'Installing\s+([^\s]+)\s+\(([^)]+)\)',
        
        # Go modules
        r'go:\s+downloading\s+([^\s]+)\s+([^\s]+)',
        
        # Rust crates
        r'Downloading\s+([^\s]+)\s+v([^\s]+)',
    ]
    
    dependency_changes = []
    
    for entry in log_entries:
        for pattern in dependency_patterns:
            matches = re.findall(pattern, entry.message, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    package_name = match[0]
                    version = match[1] if len(match) > 1 else "unknown"
                else:
                    package_name = match
                    version = "unknown"
                
                dependency_changes.append({
                    "package": package_name,
                    "version": version,
                    "log_entry": entry,
                    "pattern": pattern
                })
    
    # Analyze for suspicious patterns
    if len(dependency_changes) > 50:  # Unusually high number of dependency changes
        activity = SuspiciousActivity(
            activity_type="excessive_dependency_changes",
            description=f"Detected unusually high number of dependency changes: {len(dependency_changes)}",
            evidence=[f"Found {len(dependency_changes)} dependency changes in build logs"],
            confidence=0.6,
            severity="medium",
            log_entries=[change["log_entry"] for change in dependency_changes[:10]],  # Limit to first 10
            metadata={"total_changes": len(dependency_changes)}
        )
        suspicious_activities.append(activity)
    
    # Check for dependencies from suspicious sources
    suspicious_sources = [".tk", ".ml", ".ga", ".cf", "pastebin", "raw.githubusercontent.com"]
    
    for change in dependency_changes:
        package_name = change["package"].lower()
        for suspicious_source in suspicious_sources:
            if suspicious_source in package_name:
                activity = SuspiciousActivity(
                    activity_type="suspicious_dependency_source",
                    description=f"Dependency from suspicious source: {change['package']}",
                    evidence=[f"Package '{change['package']}' contains suspicious domain '{suspicious_source}'"],
                    confidence=0.8,
                    severity="high",
                    log_entries=[change["log_entry"]],
                    metadata={"package": change["package"], "suspicious_source": suspicious_source}
                )
                suspicious_activities.append(activity)
                break
    
    return suspicious_activities

def detect_network_anomalies(log_entries: List[CILogEntry]) -> List[SuspiciousActivity]:
    """
    Detect network anomalies in CI/CD logs.
    
    Args:
        log_entries: List of parsed log entries
    
    Returns:
        List of network anomaly activities
    """
    suspicious_activities = []
    
    # Network patterns to detect
    network_patterns = [
        # Outbound connections to suspicious IPs/domains
        r'connecting\s+to\s+((?:\d{1,3}\.){3}\d{1,3})',
        r'(?:curl|wget|http)\s+[^\s]*(?:\.tk|\.ml|\.ga|\.cf|\.cc)',
        r'(?:http|https|ftp)://(?:\d{1,3}\.){3}\d{1,3}',
        
        # Data exfiltration patterns
        r'POST\s+[^\s]+\s+.*(?:password|token|key|secret)',
        r'uploading\s+.*\.(?:zip|tar|gz|7z)',
        
        # Reverse shells
        r'nc\s+-[lL]\s+\d+',
        r'bash\s+-i\s+>&\s+/dev/tcp/',
        r'/bin/sh\s+-i',
        
        # DNS queries to suspicious domains
        r'nslookup\s+[^\s]*(?:\.tk|\.ml|\.ga|\.cf)',
        r'dig\s+[^\s]*(?:\.tk|\.ml|\.ga|\.cf)',
    ]
    
    for pattern in network_patterns:
        matching_entries = []
        
        for entry in log_entries:
            matches = re.findall(pattern, entry.message, re.IGNORECASE)
            if matches:
                matching_entries.append(entry)
        
        if matching_entries:
            activity = SuspiciousActivity(
                activity_type="network_anomaly",
                description=f"Detected suspicious network activity: {pattern}",
                evidence=[f"Network pattern '{pattern}' found in {len(matching_entries)} log entries"],
                confidence=0.8,
                severity="high",
                log_entries=matching_entries,
                metadata={"pattern": pattern}
            )
            suspicious_activities.append(activity)
    
    return suspicious_activities

def detect_build_process_anomalies(log_entries: List[CILogEntry]) -> List[SuspiciousActivity]:
    """
    Detect anomalies in build processes.
    
    Args:
        log_entries: List of parsed log entries
    
    Returns:
        List of build process anomaly activities
    """
    suspicious_activities = []
    
    # Analyze build duration and patterns
    error_entries = [entry for entry in log_entries if entry.level in ["ERROR", "FATAL"]]
    warning_entries = [entry for entry in log_entries if entry.level == "WARNING"]
    
    # High error rate
    if len(error_entries) > len(log_entries) * 0.1:  # More than 10% errors
        activity = SuspiciousActivity(
            activity_type="high_error_rate",
            description=f"Unusually high error rate in build: {len(error_entries)}/{len(log_entries)} entries",
            evidence=[f"Found {len(error_entries)} error entries out of {len(log_entries)} total entries"],
            confidence=0.6,
            severity="medium",
            log_entries=error_entries[:5],  # Show first 5 errors
            metadata={"error_count": len(error_entries), "total_entries": len(log_entries)}
        )
        suspicious_activities.append(activity)
    
    # Detect suspicious commands in build scripts
    suspicious_build_commands = [
        r'rm\s+-rf\s+/',  # Dangerous file deletion
        r'chmod\s+777',   # Overly permissive permissions
        r'sudo\s+',       # Privilege escalation
        r'su\s+-',        # User switching
        r'eval\s+\$',     # Dynamic code execution
        r'exec\s+\$',     # Command execution
    ]
    
    for pattern in suspicious_build_commands:
        matching_entries = []
        
        for entry in log_entries:
            if re.search(pattern, entry.message, re.IGNORECASE):
                matching_entries.append(entry)
        
        if matching_entries:
            activity = SuspiciousActivity(
                activity_type="suspicious_build_command",
                description=f"Detected suspicious build command: {pattern}",
                evidence=[f"Suspicious command pattern '{pattern}' found in build logs"],
                confidence=0.7,
                severity="medium",
                log_entries=matching_entries,
                metadata={"pattern": pattern}
            )
            suspicious_activities.append(activity)
    
    return suspicious_activities

def analyze_ci_logs(log_content: str, log_format: str = "auto") -> Dict[str, Any]:
    """
    Perform comprehensive analysis of CI/CD logs.
    
    Args:
        log_content: Raw log content
        log_format: Log format ("github_actions", "jenkins", "gitlab", "auto")
    
    Returns:
        Analysis results with detected suspicious activities
    """
    # Parse logs
    log_entries = parse_ci_logs(log_content, log_format)
    
    # Detect various types of suspicious activities
    install_hook_activities = detect_suspicious_install_hooks(log_entries)
    dependency_activities = detect_dependency_changes(log_entries)
    network_activities = detect_network_anomalies(log_entries)
    build_activities = detect_build_process_anomalies(log_entries)
    
    # Combine all activities
    all_activities = (install_hook_activities + dependency_activities + 
                     network_activities + build_activities)
    
    # Analyze keywords in log content
    suspicious_keywords = contains_suspicious_keywords(log_content)
    network_patterns = detect_suspicious_network_patterns(log_content)
    
    # Calculate overall risk score
    risk_score = _calculate_ci_risk_score(all_activities, suspicious_keywords, network_patterns)
    
    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "log_format": log_format,
        "total_log_entries": len(log_entries),
        "suspicious_activities": [activity.to_dict() for activity in all_activities],
        "suspicious_keywords": suspicious_keywords,
        "network_patterns": [pattern for pattern in network_patterns],
        "risk_score": risk_score,
        "summary": {
            "total_activities": len(all_activities),
            "install_hook_activities": len(install_hook_activities),
            "dependency_activities": len(dependency_activities),
            "network_activities": len(network_activities),
            "build_activities": len(build_activities),
            "high_severity_activities": len([a for a in all_activities if a.severity == "high"]),
            "medium_severity_activities": len([a for a in all_activities if a.severity == "medium"]),
            "low_severity_activities": len([a for a in all_activities if a.severity == "low"])
        }
    }

def _calculate_ci_risk_score(activities: List[SuspiciousActivity], 
                           keywords: List[str], 
                           network_patterns: List[Dict[str, str]]) -> float:
    """Calculate overall CI/CD risk score (0.0 to 10.0)."""
    if not activities and not keywords and not network_patterns:
        return 0.0
    
    severity_weights = {
        "critical": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0
    }
    
    total_score = 0.0
    
    # Score from activities
    for activity in activities:
        weight = severity_weights.get(activity.severity, 1.0)
        confidence_multiplier = activity.confidence
        total_score += weight * confidence_multiplier
    
    # Score from keywords (lower weight)
    total_score += len(keywords) * 0.5
    
    # Score from network patterns
    for pattern in network_patterns:
        confidence = float(pattern.get("confidence", 0.5))
        total_score += confidence * 2.0
    
    # Normalize to 0-10 scale
    if activities:
        normalized_score = min(total_score / len(activities), 10.0)
    else:
        normalized_score = min(total_score, 10.0)
    
    return round(normalized_score, 2)

def generate_ci_security_findings(analysis_results: Dict[str, Any]) -> List[SecurityFinding]:
    """
    Generate SecurityFinding objects from CI/CD analysis results.
    
    Args:
        analysis_results: CI/CD analysis results
    
    Returns:
        List of SecurityFinding objects
    """
    findings = []
    
    for activity_data in analysis_results.get("suspicious_activities", []):
        evidence = activity_data["evidence"]
        
        # Add log entries as evidence
        log_entries = activity_data.get("log_entries", [])
        if log_entries:
            evidence.extend([f"Log entry: {entry['message'][:100]}..." for entry in log_entries[:3]])
        
        recommendations = _get_recommendations_for_activity_type(activity_data["activity_type"])
        
        finding = SecurityFinding(
            package="ci_cd_pipeline",
            version="*",
            finding_type=activity_data["activity_type"],
            severity=activity_data["severity"],
            confidence=activity_data["confidence"],
            evidence=evidence,
            recommendations=recommendations,
            source="ci_tools"
        )
        findings.append(finding)
    
    return findings

def _get_recommendations_for_activity_type(activity_type: str) -> List[str]:
    """Get recommendations based on activity type."""
    recommendations_map = {
        "suspicious_install_hook": [
            "Review package install scripts for malicious code",
            "Use package managers with better security controls",
            "Monitor network activity during package installations"
        ],
        "excessive_dependency_changes": [
            "Review dependency changes for legitimacy",
            "Implement dependency approval workflows",
            "Use dependency scanning tools"
        ],
        "suspicious_dependency_source": [
            "Verify the legitimacy of dependency sources",
            "Use trusted package repositories only",
            "Implement allow-lists for package sources"
        ],
        "network_anomaly": [
            "Investigate network connections during build",
            "Implement network monitoring and restrictions",
            "Review build scripts for unauthorized network activity"
        ],
        "high_error_rate": [
            "Investigate root cause of build errors",
            "Review build configuration and dependencies",
            "Monitor build health metrics"
        ],
        "suspicious_build_command": [
            "Review build scripts for dangerous commands",
            "Implement least-privilege build environments",
            "Use containerized builds with restricted permissions"
        ]
    }
    
    return recommendations_map.get(activity_type, [
        "Review CI/CD logs for suspicious activity",
        "Implement additional monitoring and alerting",
        "Follow security best practices for CI/CD pipelines"
    ])

def save_ci_analysis(analysis_results: Dict[str, Any], output_dir: str) -> str:
    """
    Save CI/CD analysis results to JSON file.
    
    Args:
        analysis_results: Analysis results to save
        output_dir: Output directory
    
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ci_analysis_{timestamp}.json"
    
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"CI/CD analysis results saved to {file_path}")
    return str(file_path)