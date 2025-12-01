"""
Security alert processing and correlation tools for Multi-Agent Security Analysis System.

This module provides functions for:
- Processing security alerts from various sources
- Correlating alerts with SBOM data
- Analyzing alert patterns and trends
- Generating consolidated security findings
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from tools.sbom_tools import SecurityFinding, SBOMPackage
from config import config

logger = logging.getLogger(__name__)

class SecurityAlert:
    """Represents a security alert from various sources."""
    
    def __init__(self, alert_id: str, source: str, package_name: str, 
                 severity: str, summary: str, created_at: str,
                 vulnerability_id: Optional[str] = None, 
                 affected_versions: Optional[List[str]] = None,
                 fixed_versions: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.alert_id = alert_id
        self.source = source  # "dependabot", "snyk", "osv", "manual"
        self.package_name = package_name
        self.severity = severity.lower()
        self.summary = summary
        self.vulnerability_id = vulnerability_id
        self.affected_versions = affected_versions or []
        self.fixed_versions = fixed_versions or []
        self.created_at = created_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary representation."""
        return {
            "alert_id": self.alert_id,
            "source": self.source,
            "package_name": self.package_name,
            "severity": self.severity,
            "summary": self.summary,
            "vulnerability_id": self.vulnerability_id,
            "affected_versions": self.affected_versions,
            "fixed_versions": self.fixed_versions,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

def parse_dependabot_alerts(alerts_data: List[Dict[str, Any]]) -> List[SecurityAlert]:
    """
    Parse Dependabot alerts into SecurityAlert objects.
    
    Args:
        alerts_data: Raw Dependabot alerts data from GitHub API
    
    Returns:
        List of SecurityAlert objects
    """
    parsed_alerts = []
    
    for alert in alerts_data:
        try:
            security_advisory = alert.get("security_advisory", {})
            security_vulnerability = alert.get("security_vulnerability", {})
            
            parsed_alert = SecurityAlert(
                alert_id=f"dependabot-{alert.get('number', 'unknown')}",
                source="dependabot",
                package_name=alert.get("dependency", {}).get("package", {}).get("name", "unknown"),
                severity=security_advisory.get("severity", "medium"),
                summary=security_advisory.get("summary", "No summary available"),
                vulnerability_id=security_advisory.get("ghsa_id") or security_advisory.get("cve_id"),
                affected_versions=[security_vulnerability.get("vulnerable_version_range", "*")],
                fixed_versions=[security_vulnerability.get("first_patched_version", {}).get("identifier")] if security_vulnerability.get("first_patched_version") else [],
                created_at=alert.get("created_at", datetime.now().isoformat()),
                metadata={
                    "state": alert.get("state"),
                    "updated_at": alert.get("updated_at"),
                    "cvss_score": security_advisory.get("cvss", {}).get("score"),
                    "ecosystem": alert.get("dependency", {}).get("package", {}).get("ecosystem")
                }
            )
            parsed_alerts.append(parsed_alert)
        
        except Exception as e:
            logger.warning(f"Failed to parse Dependabot alert: {e}")
            continue
    
    return parsed_alerts

def parse_osv_alerts(osv_data: List[Dict[str, Any]], package_name: str) -> List[SecurityAlert]:
    """
    Parse OSV API vulnerability data into SecurityAlert objects.
    
    Args:
        osv_data: Raw OSV vulnerability data
        package_name: Name of the package being analyzed
    
    Returns:
        List of SecurityAlert objects
    """
    parsed_alerts = []
    
    for vuln in osv_data:
        try:
            # Extract affected versions
            affected_versions = []
            for affected in vuln.get("affected", []):
                ranges = affected.get("ranges", [])
                for range_info in ranges:
                    events = range_info.get("events", [])
                    for event in events:
                        if "introduced" in event:
                            affected_versions.append(f">={event['introduced']}")
                        elif "fixed" in event:
                            affected_versions.append(f"<{event['fixed']}")
            
            # Extract fixed versions
            fixed_versions = []
            for affected in vuln.get("affected", []):
                ranges = affected.get("ranges", [])
                for range_info in ranges:
                    events = range_info.get("events", [])
                    for event in events:
                        if "fixed" in event:
                            fixed_versions.append(event["fixed"])
            
            # Determine severity
            severity = "medium"  # default
            for severity_info in vuln.get("severity", []):
                if severity_info.get("type") == "CVSS_V3":
                    score = severity_info.get("score", 0)
                    if score >= 9.0:
                        severity = "critical"
                    elif score >= 7.0:
                        severity = "high"
                    elif score >= 4.0:
                        severity = "medium"
                    else:
                        severity = "low"
                    break
            
            parsed_alert = SecurityAlert(
                alert_id=f"osv-{vuln.get('id', 'unknown')}",
                source="osv",
                package_name=package_name,
                severity=severity,
                summary=vuln.get("summary", "No summary available"),
                vulnerability_id=vuln.get("id"),
                affected_versions=affected_versions,
                fixed_versions=list(set(fixed_versions)),  # Remove duplicates
                created_at=vuln.get("published", datetime.now().isoformat()),
                metadata={
                    "modified": vuln.get("modified"),
                    "withdrawn": vuln.get("withdrawn"),
                    "aliases": vuln.get("aliases", []),
                    "references": [ref.get("url") for ref in vuln.get("references", [])],
                    "database_specific": vuln.get("database_specific", {})
                }
            )
            parsed_alerts.append(parsed_alert)
        
        except Exception as e:
            logger.warning(f"Failed to parse OSV vulnerability: {e}")
            continue
    
    return parsed_alerts

def correlate_alerts_with_sbom(alerts: List[SecurityAlert], 
                              sbom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Correlate security alerts with SBOM package data.
    
    Args:
        alerts: List of SecurityAlert objects
        sbom_data: SBOM data containing package information
    
    Returns:
        List of correlation results with matched packages and alerts
    """
    correlations = []
    packages = sbom_data.get("packages", [])
    
    for alert in alerts:
        matched_packages = []
        
        # Find packages that match the alert
        for package in packages:
            package_name = package.get("name", "")
            package_version = package.get("version", "")
            
            # Exact name match
            if package_name.lower() == alert.package_name.lower():
                # Check if package version is affected
                is_affected = _is_version_affected(package_version, alert.affected_versions)
                has_fix = _has_available_fix(package_version, alert.fixed_versions)
                
                matched_packages.append({
                    "package": package,
                    "is_affected": is_affected,
                    "has_fix": has_fix,
                    "recommended_version": _get_recommended_version(alert.fixed_versions) if has_fix else None
                })
        
        if matched_packages:
            correlation = {
                "alert": alert.to_dict(),
                "matched_packages": matched_packages,
                "correlation_confidence": 1.0,  # Exact name match
                "correlation_type": "exact_match"
            }
            correlations.append(correlation)
    
    return correlations

def _is_version_affected(package_version: str, affected_versions: List[str]) -> bool:
    """Check if a package version is affected by vulnerability."""
    if not affected_versions or package_version in ["*", "unknown"]:
        return True  # Assume affected if version is unknown
    
    # Simple version comparison - in production, use proper semver library
    for affected_range in affected_versions:
        if affected_range == "*":
            return True
        elif affected_range.startswith(">=") and package_version >= affected_range[2:]:
            return True
        elif affected_range.startswith("<=") and package_version <= affected_range[2:]:
            return True
        elif affected_range.startswith("<") and package_version < affected_range[1:]:
            return True
        elif affected_range.startswith(">") and package_version > affected_range[1:]:
            return True
        elif affected_range == package_version:
            return True
    
    return False

def _has_available_fix(package_version: str, fixed_versions: List[str]) -> bool:
    """Check if there are fixed versions available."""
    if not fixed_versions or package_version in ["*", "unknown"]:
        return bool(fixed_versions)
    
    # Check if any fixed version is newer than current version
    for fixed_version in fixed_versions:
        if fixed_version > package_version:  # Simple string comparison
            return True
    
    return False

def _get_recommended_version(fixed_versions: List[str]) -> Optional[str]:
    """Get the recommended version to upgrade to."""
    if not fixed_versions:
        return None
    
    # Return the latest fixed version (simple string comparison)
    return max(fixed_versions)

def analyze_alert_patterns(alerts: List[SecurityAlert]) -> Dict[str, Any]:
    """
    Analyze patterns in security alerts to identify trends and anomalies.
    
    Args:
        alerts: List of SecurityAlert objects
    
    Returns:
        Analysis results with patterns and insights
    """
    if not alerts:
        return {"total_alerts": 0, "patterns": {}}
    
    # Group alerts by various dimensions
    by_severity = {}
    by_source = {}
    by_package = {}
    by_date = {}
    
    for alert in alerts:
        # By severity
        by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
        
        # By source
        by_source[alert.source] = by_source.get(alert.source, 0) + 1
        
        # By package
        by_package[alert.package_name] = by_package.get(alert.package_name, 0) + 1
        
        # By date (group by day)
        try:
            alert_date = datetime.fromisoformat(alert.created_at.replace('Z', '+00:00')).date()
            date_str = alert_date.isoformat()
            by_date[date_str] = by_date.get(date_str, 0) + 1
        except (ValueError, AttributeError):
            pass
    
    # Identify patterns
    patterns = {
        "severity_distribution": by_severity,
        "source_distribution": by_source,
        "most_vulnerable_packages": sorted(by_package.items(), key=lambda x: x[1], reverse=True)[:10],
        "alert_timeline": by_date,
        "high_risk_packages": [pkg for pkg, count in by_package.items() if count >= 3],
        "recent_alerts": len([a for a in alerts if _is_recent_alert(a.created_at)]),
        "critical_alerts": len([a for a in alerts if a.severity == "critical"])
    }
    
    # Calculate risk score
    risk_score = _calculate_overall_risk_score(alerts)
    
    return {
        "total_alerts": len(alerts),
        "patterns": patterns,
        "risk_score": risk_score,
        "analysis_timestamp": datetime.now().isoformat()
    }

def _is_recent_alert(created_at: str, days: int = 30) -> bool:
    """Check if alert was created within the specified number of days."""
    try:
        alert_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        cutoff_date = datetime.now() - timedelta(days=days)
        return alert_date >= cutoff_date
    except (ValueError, AttributeError):
        return False

def _calculate_overall_risk_score(alerts: List[SecurityAlert]) -> float:
    """Calculate overall risk score based on alerts (0.0 to 10.0)."""
    if not alerts:
        return 0.0
    
    severity_weights = {
        "critical": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0
    }
    
    total_score = 0.0
    for alert in alerts:
        weight = severity_weights.get(alert.severity, 1.0)
        
        # Increase weight for recent alerts
        if _is_recent_alert(alert.created_at, days=7):
            weight *= 1.5
        elif _is_recent_alert(alert.created_at, days=30):
            weight *= 1.2
        
        total_score += weight
    
    # Normalize to 0-10 scale (cap at 10)
    normalized_score = min(total_score / len(alerts), 10.0)
    return round(normalized_score, 2)

def generate_security_findings_from_alerts(correlations: List[Dict[str, Any]]) -> List[SecurityFinding]:
    """
    Generate SecurityFinding objects from alert correlations.
    
    Args:
        correlations: Alert correlation results
    
    Returns:
        List of SecurityFinding objects
    """
    findings = []
    
    for correlation in correlations:
        alert_data = correlation["alert"]
        matched_packages = correlation["matched_packages"]
        
        for package_match in matched_packages:
            if package_match["is_affected"]:
                package = package_match["package"]
                
                evidence = [
                    f"Security alert: {alert_data['alert_id']}",
                    f"Vulnerability: {alert_data['vulnerability_id'] or 'Unknown'}",
                    f"Summary: {alert_data['summary']}"
                ]
                
                recommendations = []
                if package_match["has_fix"]:
                    recommended_version = package_match["recommended_version"]
                    recommendations.append(f"Update to version {recommended_version} or later")
                else:
                    recommendations.append("Monitor for security updates")
                
                recommendations.extend([
                    "Review vulnerability details and assess impact",
                    "Consider alternative packages if no fix is available"
                ])
                
                finding = SecurityFinding(
                    package=package["name"],
                    version=package["version"],
                    finding_type="security_alert",
                    severity=alert_data["severity"],
                    confidence=0.9,
                    evidence=evidence,
                    recommendations=recommendations,
                    source=f"sca_tools_{alert_data['source']}"
                )
                findings.append(finding)
    
    return findings

def save_alert_analysis(analysis_results: Dict[str, Any], output_dir: str) -> str:
    """
    Save alert analysis results to JSON file.
    
    Args:
        analysis_results: Analysis results to save
        output_dir: Output directory
    
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"security_alert_analysis_{timestamp}.json"
    
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"Alert analysis results saved to {file_path}")
    return str(file_path)

def load_alerts_from_file(file_path: str) -> List[SecurityAlert]:
    """
    Load security alerts from JSON file.
    
    Args:
        file_path: Path to JSON file containing alerts
    
    Returns:
        List of SecurityAlert objects
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        alerts = []
        for alert_data in data:
            alert = SecurityAlert(
                alert_id=alert_data["alert_id"],
                source=alert_data["source"],
                package_name=alert_data["package_name"],
                severity=alert_data["severity"],
                summary=alert_data["summary"],
                vulnerability_id=alert_data.get("vulnerability_id"),
                affected_versions=alert_data.get("affected_versions", []),
                fixed_versions=alert_data.get("fixed_versions", []),
                created_at=alert_data["created_at"],
                metadata=alert_data.get("metadata", {})
            )
            alerts.append(alert)
        
        return alerts
    
    except Exception as e:
        logger.error(f"Failed to load alerts from {file_path}: {e}")
        return []