"""
Spyder - Core Analysis Engine
AI-Powered Supply Chain Security Scanner

This module provides the main analysis logic for processing SBOM data,
vulnerability detection, and suspicious activity analysis with finding
generation including confidence scores and evidence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from tools.sbom_tools import (
    SBOMPackage,
    SecurityFinding,
    check_vulnerable_packages,
    validate_sbom_structure,
    generate_sbom_from_packages
)
from tools.github_tools import fetch_repository_data, analyze_repository_for_supply_chain_risks
from tools.local_tools import analyze_local_directory
from constants import (
    contains_suspicious_keywords,
    detect_suspicious_network_patterns,
    is_suspicious_package_name,
    calculate_typosquat_confidence
)
from config import config

logger = logging.getLogger(__name__)

@dataclass
class AnalysisMetadata:
    """Metadata for analysis results."""
    analysis_id: str
    analysis_type: str  # "github_repository", "local_directory", "sbom_file"
    target: str
    start_time: str
    end_time: str
    total_packages: int
    total_findings: int
    confidence_threshold: float
    osv_enabled: bool
    visual_analysis_enabled: bool

@dataclass
class AnalysisSummary:
    """Summary statistics for analysis results."""
    total_packages: int
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    ecosystems_analyzed: List[str]
    finding_types: Dict[str, int]
    confidence_distribution: Dict[str, int]  # "high", "medium", "low"

@dataclass
class AnalysisResult:
    """Complete analysis result structure."""
    metadata: AnalysisMetadata
    summary: AnalysisSummary
    sbom_data: Dict[str, Any]
    security_findings: List[Dict[str, Any]]
    suspicious_activities: List[Dict[str, Any]]
    recommendations: List[str]
    raw_data: Optional[Dict[str, Any]] = None

class SupplyChainAnalyzer:
    """Main supply chain analysis engine."""
    
    def __init__(self, confidence_threshold: float = None, enable_osv: bool = None):
        """
        Initialize the analyzer.
        
        Args:
            confidence_threshold: Minimum confidence score for findings (0.0-1.0)
            enable_osv: Whether to query OSV API for vulnerabilities
        """
        self.confidence_threshold = confidence_threshold or config.CONFIDENCE_THRESHOLD
        self.enable_osv = enable_osv if enable_osv is not None else config.ENABLE_OSV_QUERIES
        self.analysis_id = self._generate_analysis_id()
        
        logger.info(f"Initialized SupplyChainAnalyzer with ID: {self.analysis_id}")
    
    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID."""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"analysis_{timestamp}_{unique_suffix}"
    
    def analyze_github_repository(self, repo_url: str) -> AnalysisResult:
        """
        Analyze a GitHub repository for supply chain vulnerabilities.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Complete analysis results
        """
        start_time = datetime.now()
        logger.info(f"Starting GitHub repository analysis: {repo_url}")
        
        try:
            # Fetch repository data
            repo_data = fetch_repository_data(repo_url)
            
            # Extract SBOM data
            sbom_data = repo_data.get("sbom", {})
            
            # Perform security analysis
            security_findings = self._analyze_sbom_security(sbom_data)
            
            # Analyze repository-specific risks
            repo_findings = analyze_repository_for_supply_chain_risks(repo_data)
            security_findings.extend(repo_findings)
            
            # Detect suspicious activities
            suspicious_activities = self._detect_suspicious_activities(repo_data)
            
            # Generate analysis result
            end_time = datetime.now()
            result = self._compile_analysis_result(
                analysis_type="github_repository",
                target=repo_url,
                start_time=start_time,
                end_time=end_time,
                sbom_data=sbom_data,
                security_findings=security_findings,
                suspicious_activities=suspicious_activities,
                raw_data=repo_data
            )
            
            logger.info(f"GitHub analysis complete: {len(security_findings)} findings")
            return result
            
        except Exception as e:
            logger.error(f"GitHub repository analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze GitHub repository {repo_url}: {e}")
    
    def analyze_local_directory(self, directory_path: str) -> AnalysisResult:
        """
        Analyze a local directory for supply chain vulnerabilities.
        
        Args:
            directory_path: Path to local directory
            
        Returns:
            Complete analysis results
        """
        start_time = datetime.now()
        logger.info(f"Starting local directory analysis: {directory_path}")
        
        try:
            # Perform local analysis
            local_data = analyze_local_directory(
                directory_path, 
                use_osv=self.enable_osv
            )
            
            # Extract SBOM and findings
            sbom_data = local_data.get("sbom", {})
            existing_findings = local_data.get("security_findings", [])
            
            # Convert existing findings to SecurityFinding objects if needed
            security_findings = []
            for finding_data in existing_findings:
                if isinstance(finding_data, dict):
                    finding = SecurityFinding(
                        package=finding_data.get("package", "unknown"),
                        version=finding_data.get("version", "unknown"),
                        finding_type=finding_data.get("finding_type", "unknown"),
                        severity=finding_data.get("severity", "medium"),
                        confidence=finding_data.get("confidence", 0.5),
                        evidence=finding_data.get("evidence", []),
                        recommendations=finding_data.get("recommendations", []),
                        source=finding_data.get("source", "local_analysis")
                    )
                    security_findings.append(finding)
                else:
                    security_findings.append(finding_data)
            
            # Detect additional suspicious activities
            suspicious_activities = self._detect_suspicious_activities(local_data)
            
            # Generate analysis result
            end_time = datetime.now()
            result = self._compile_analysis_result(
                analysis_type="local_directory",
                target=directory_path,
                start_time=start_time,
                end_time=end_time,
                sbom_data=sbom_data,
                security_findings=security_findings,
                suspicious_activities=suspicious_activities,
                raw_data=local_data
            )
            
            logger.info(f"Local directory analysis complete: {len(security_findings)} findings")
            return result
            
        except Exception as e:
            logger.error(f"Local directory analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze local directory {directory_path}: {e}")
    
    def analyze_sbom_file(self, sbom_file_path: str) -> AnalysisResult:
        """
        Analyze an SBOM file for supply chain vulnerabilities.
        
        Args:
            sbom_file_path: Path to SBOM file
            
        Returns:
            Complete analysis results
        """
        start_time = datetime.now()
        logger.info(f"Starting SBOM file analysis: {sbom_file_path}")
        
        try:
            from tools.sbom_tools import read_sbom
            
            # Read and validate SBOM
            sbom_data = read_sbom(sbom_file_path)
            is_valid, validation_errors = validate_sbom_structure(sbom_data)
            
            if not is_valid:
                logger.warning(f"SBOM validation errors: {validation_errors}")
            
            # Perform security analysis
            security_findings = self._analyze_sbom_security(sbom_data)
            
            # Detect suspicious activities in SBOM data
            suspicious_activities = self._detect_suspicious_activities({"sbom": sbom_data})
            
            # Generate analysis result
            end_time = datetime.now()
            result = self._compile_analysis_result(
                analysis_type="sbom_file",
                target=sbom_file_path,
                start_time=start_time,
                end_time=end_time,
                sbom_data=sbom_data,
                security_findings=security_findings,
                suspicious_activities=suspicious_activities,
                raw_data={"sbom": sbom_data, "validation_errors": validation_errors}
            )
            
            logger.info(f"SBOM file analysis complete: {len(security_findings)} findings")
            return result
            
        except Exception as e:
            logger.error(f"SBOM file analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze SBOM file {sbom_file_path}: {e}")
    
    def _analyze_sbom_security(self, sbom_data: Dict[str, Any]) -> List[SecurityFinding]:
        """
        Analyze SBOM data for security vulnerabilities.
        
        Args:
            sbom_data: SBOM data dictionary
            
        Returns:
            List of security findings
        """
        if not sbom_data or not sbom_data.get("packages"):
            logger.warning("No packages found in SBOM data")
            return []
        
        # Use existing vulnerability checking
        findings = check_vulnerable_packages(sbom_data, use_osv=self.enable_osv)
        
        # Filter by confidence threshold
        filtered_findings = [
            finding for finding in findings 
            if finding.confidence >= self.confidence_threshold
        ]
        
        logger.debug(f"Filtered {len(findings)} findings to {len(filtered_findings)} above threshold {self.confidence_threshold}")
        return filtered_findings
    
    def _detect_suspicious_activities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect suspicious activities in analysis data.
        
        Args:
            data: Analysis data (repository, local, or SBOM data)
            
        Returns:
            List of suspicious activity findings
        """
        suspicious_activities = []
        
        # Analyze SBOM packages for suspicious patterns
        sbom_data = data.get("sbom", {})
        packages = sbom_data.get("packages", [])
        
        for package_data in packages:
            package_name = package_data.get("name", "")
            ecosystem = package_data.get("ecosystem", "unknown")
            
            # Check for suspicious package names
            if is_suspicious_package_name(package_name, ecosystem):
                confidence = calculate_typosquat_confidence(package_name, "")
                suspicious_activities.append({
                    "type": "suspicious_package_name",
                    "package": package_name,
                    "ecosystem": ecosystem,
                    "confidence": confidence,
                    "evidence": [f"Package name '{package_name}' matches suspicious patterns"],
                    "severity": "medium" if confidence > 0.7 else "low"
                })
        
        # Analyze file contents for suspicious keywords (if available)
        if "contents" in data:
            for file_info in data["contents"]:
                if file_info.get("content"):
                    suspicious_keywords = contains_suspicious_keywords(file_info["content"])
                    if suspicious_keywords:
                        suspicious_activities.append({
                            "type": "suspicious_keywords",
                            "file": file_info.get("path", file_info.get("name", "unknown")),
                            "keywords": suspicious_keywords,
                            "confidence": min(0.8, len(suspicious_keywords) * 0.2),
                            "evidence": [f"Found suspicious keywords: {', '.join(suspicious_keywords[:5])}"],
                            "severity": "high" if len(suspicious_keywords) > 3 else "medium"
                        })
                    
                    # Check for suspicious network patterns
                    network_patterns = detect_suspicious_network_patterns(file_info["content"])
                    if network_patterns:
                        suspicious_activities.append({
                            "type": "suspicious_network_patterns",
                            "file": file_info.get("path", file_info.get("name", "unknown")),
                            "patterns": network_patterns,
                            "confidence": max(pattern.get("confidence", 0.5) for pattern in network_patterns),
                            "evidence": [f"Found {len(network_patterns)} suspicious network patterns"],
                            "severity": "high"
                        })
        
        # Analyze CI/CD workflow patterns (for GitHub repositories)
        if "workflow_runs" in data:
            workflow_runs = data["workflow_runs"]
            if workflow_runs:
                failed_runs = [run for run in workflow_runs if run.get("conclusion") == "failure"]
                failure_rate = len(failed_runs) / len(workflow_runs)
                
                if failure_rate > 0.5:  # More than 50% failure rate
                    suspicious_activities.append({
                        "type": "high_ci_failure_rate",
                        "failure_rate": failure_rate,
                        "total_runs": len(workflow_runs),
                        "failed_runs": len(failed_runs),
                        "confidence": min(0.8, failure_rate),
                        "evidence": [f"High CI/CD failure rate: {failure_rate:.1%}"],
                        "severity": "medium"
                    })
        
        return suspicious_activities
    
    def _compile_analysis_result(self, analysis_type: str, target: str, 
                               start_time: datetime, end_time: datetime,
                               sbom_data: Dict[str, Any], 
                               security_findings: List[SecurityFinding],
                               suspicious_activities: List[Dict[str, Any]],
                               raw_data: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Compile complete analysis results.
        
        Args:
            analysis_type: Type of analysis performed
            target: Analysis target (URL, path, etc.)
            start_time: Analysis start time
            end_time: Analysis end time
            sbom_data: SBOM data
            security_findings: Security findings
            suspicious_activities: Suspicious activities
            raw_data: Raw analysis data
            
        Returns:
            Complete analysis result
        """
        # Convert findings to dictionaries
        findings_dicts = []
        for finding in security_findings:
            if hasattr(finding, 'to_dict'):
                findings_dicts.append(finding.to_dict())
            elif isinstance(finding, dict):
                findings_dicts.append(finding)
            else:
                # Convert SecurityFinding object to dict manually
                findings_dicts.append({
                    "package": getattr(finding, 'package', 'unknown'),
                    "version": getattr(finding, 'version', 'unknown'),
                    "finding_type": getattr(finding, 'finding_type', 'unknown'),
                    "severity": getattr(finding, 'severity', 'medium'),
                    "confidence": getattr(finding, 'confidence', 0.5),
                    "evidence": getattr(finding, 'evidence', []),
                    "recommendations": getattr(finding, 'recommendations', []),
                    "source": getattr(finding, 'source', 'analysis_engine'),
                    "timestamp": getattr(finding, 'timestamp', datetime.now().isoformat())
                })
        
        # Calculate summary statistics
        packages = sbom_data.get("packages", [])
        ecosystems = list(set(pkg.get("ecosystem", "unknown") for pkg in packages))
        
        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        finding_types = {}
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for finding in findings_dicts:
            severity = finding.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            finding_type = finding.get("finding_type", "unknown")
            finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
            
            confidence = finding.get("confidence", 0.5)
            if confidence >= 0.8:
                confidence_distribution["high"] += 1
            elif confidence >= 0.5:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings_dicts, suspicious_activities)
        
        # Create metadata
        metadata = AnalysisMetadata(
            analysis_id=self.analysis_id,
            analysis_type=analysis_type,
            target=target,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_packages=len(packages),
            total_findings=len(findings_dicts),
            confidence_threshold=self.confidence_threshold,
            osv_enabled=self.enable_osv,
            visual_analysis_enabled=config.ENABLE_VISUAL_ANALYSIS
        )
        
        # Create summary
        summary = AnalysisSummary(
            total_packages=len(packages),
            total_findings=len(findings_dicts),
            critical_findings=severity_counts["critical"],
            high_findings=severity_counts["high"],
            medium_findings=severity_counts["medium"],
            low_findings=severity_counts["low"],
            ecosystems_analyzed=ecosystems,
            finding_types=finding_types,
            confidence_distribution=confidence_distribution
        )
        
        return AnalysisResult(
            metadata=metadata,
            summary=summary,
            sbom_data=sbom_data,
            security_findings=findings_dicts,
            suspicious_activities=suspicious_activities,
            recommendations=recommendations,
            raw_data=raw_data
        )
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], 
                                suspicious_activities: List[Dict[str, Any]]) -> List[str]:
        """
        Generate actionable recommendations based on findings.
        
        Args:
            findings: Security findings
            suspicious_activities: Suspicious activities
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Count findings by type and severity
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")
        malicious_count = sum(1 for f in findings if f.get("finding_type") == "malicious_package")
        vuln_count = sum(1 for f in findings if f.get("finding_type") == "vulnerability")
        typosquat_count = sum(1 for f in findings if f.get("finding_type") == "typosquat")
        
        # Critical findings recommendations
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical security findings immediately. "
                "These may indicate active security threats."
            )
        
        # Malicious package recommendations
        if malicious_count > 0:
            recommendations.append(
                f"Remove {malicious_count} identified malicious packages immediately. "
                "Scan systems for signs of compromise and review all dependencies."
            )
        
        # Vulnerability recommendations
        if vuln_count > 0:
            recommendations.append(
                f"Update {vuln_count} packages with known vulnerabilities to patched versions. "
                "Prioritize based on severity and exploitability."
            )
        
        # Typosquat recommendations
        if typosquat_count > 0:
            recommendations.append(
                f"Review {typosquat_count} potential typosquat packages. "
                "Verify package names and consider using package-lock files to prevent typos."
            )
        
        # High findings recommendations
        if high_count > 0:
            recommendations.append(
                f"Address {high_count} high-severity findings within 24-48 hours. "
                "These represent significant security risks."
            )
        
        # Suspicious activity recommendations
        if suspicious_activities:
            recommendations.append(
                f"Investigate {len(suspicious_activities)} suspicious activities detected. "
                "Review code changes and dependency updates for potential supply chain attacks."
            )
        
        # General recommendations
        if findings or suspicious_activities:
            recommendations.extend([
                "Implement dependency scanning in your CI/CD pipeline to catch issues early.",
                "Use Software Bill of Materials (SBOM) to maintain visibility into your dependencies.",
                "Regularly update dependencies and monitor security advisories.",
                "Consider using dependency pinning and lock files to ensure reproducible builds.",
                "Implement security policies for dependency management and approval processes."
            ])
        else:
            recommendations.append(
                "No significant security issues detected. Continue monitoring dependencies "
                "and maintain good security practices."
            )
        
        return recommendations
    
    def save_analysis_result(self, result: AnalysisResult, output_path: Optional[str] = None) -> str:
        """
        Save analysis result to JSON file.
        
        Args:
            result: Analysis result to save
            output_path: Optional output file path
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            output_dir = Path(config.OUTPUT_DIRECTORY)
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"supply_chain_analysis_{result.metadata.analysis_id}_{timestamp}.json"
            output_path = output_dir / filename
        
        # Convert result to dictionary
        result_dict = asdict(result)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        logger.info(f"Analysis result saved to {output_path}")
        return str(output_path)

    def analyze_with_visual_data(self, target: str, analysis_type: str = "auto", 
                               screenshot_paths: Optional[List[str]] = None) -> AnalysisResult:
        """
        Analyze a target with optional visual security analysis from screenshots.
        
        Args:
            target: Target to analyze (repository URL, directory path, or SBOM file)
            analysis_type: Type of analysis ("auto", "github", "local", "sbom")
            screenshot_paths: Optional list of screenshot file paths for visual analysis
            
        Returns:
            Analysis results including visual findings if screenshots provided
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            logger.info(f"Starting comprehensive analysis with visual data: {target}")
            start_time = datetime.now()
            
            # Perform standard analysis first
            if analysis_type == "auto":
                if target.startswith(("http://", "https://", "git@")):
                    base_result = self.analyze_github_repository(target)
                elif os.path.isdir(target):
                    base_result = self.analyze_local_directory(target)
                elif os.path.isfile(target):
                    base_result = self.analyze_sbom_file(target)
                else:
                    raise AnalysisError(f"Cannot determine analysis type for target: {target}")
            elif analysis_type == "github":
                base_result = self.analyze_github_repository(target)
            elif analysis_type == "local":
                base_result = self.analyze_local_directory(target)
            elif analysis_type == "sbom":
                base_result = self.analyze_sbom_file(target)
            else:
                raise AnalysisError(f"Unsupported analysis type: {analysis_type}")
            
            # If no screenshots provided, return base result
            if not screenshot_paths or not config.ENABLE_VISUAL_ANALYSIS:
                return base_result
            
            # Perform visual analysis
            logger.info(f"Performing visual analysis on {len(screenshot_paths)} screenshots...")
            
            from tools.vlm_tools import (
                process_multiple_images, 
                correlate_visual_findings_with_packages,
                generate_visual_security_findings,
                VisualSecurityFinding
            )
            
            # Process screenshots
            visual_analysis_results = process_multiple_images(screenshot_paths)
            
            # Convert visual analysis to SecurityFinding objects
            visual_security_findings = generate_visual_security_findings(visual_analysis_results)
            
            # Correlate visual findings with package data
            visual_findings_objects = []
            for finding_data in visual_analysis_results.get("findings", []):
                visual_finding = VisualSecurityFinding(
                    finding_type=finding_data.get("finding_type", "unknown"),
                    description=finding_data.get("description", ""),
                    confidence=finding_data.get("confidence", 0.5),
                    severity=finding_data.get("severity", "medium"),
                    evidence=finding_data.get("evidence", []),
                    metadata=finding_data.get("metadata", {})
                )
                visual_findings_objects.append(visual_finding)
            
            correlations = correlate_visual_findings_with_packages(
                visual_findings_objects, 
                base_result.sbom_data
            )
            
            # Combine findings
            combined_findings = base_result.security_findings.copy()
            
            # Add visual security findings
            for visual_finding in visual_security_findings:
                combined_findings.append({
                    "package": visual_finding.package,
                    "version": visual_finding.version,
                    "finding_type": visual_finding.finding_type,
                    "severity": visual_finding.severity,
                    "confidence": visual_finding.confidence,
                    "evidence": visual_finding.evidence,
                    "recommendations": visual_finding.recommendations,
                    "source": visual_finding.source,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Update raw data with visual analysis results
            updated_raw_data = base_result.raw_data.copy()
            updated_raw_data.update({
                "visual_analysis": visual_analysis_results,
                "visual_correlations": correlations,
                "screenshot_paths": screenshot_paths
            })
            
            # Create enhanced analysis result
            end_time = datetime.now()
            
            # Update summary with visual findings
            visual_finding_count = len(visual_security_findings)
            visual_critical = sum(1 for f in visual_security_findings if f.severity == "critical")
            visual_high = sum(1 for f in visual_security_findings if f.severity == "high")
            visual_medium = sum(1 for f in visual_security_findings if f.severity == "medium")
            visual_low = sum(1 for f in visual_security_findings if f.severity == "low")
            
            enhanced_summary = AnalysisSummary(
                total_packages=base_result.summary.total_packages,
                total_findings=base_result.summary.total_findings + visual_finding_count,
                critical_findings=base_result.summary.critical_findings + visual_critical,
                high_findings=base_result.summary.high_findings + visual_high,
                medium_findings=base_result.summary.medium_findings + visual_medium,
                low_findings=base_result.summary.low_findings + visual_low,
                ecosystems_analyzed=base_result.summary.ecosystems_analyzed,
                finding_types=base_result.summary.finding_types,
                confidence_distribution=base_result.summary.confidence_distribution
            )
            
            # Update metadata
            enhanced_metadata = AnalysisMetadata(
                analysis_id=base_result.metadata.analysis_id,
                analysis_type=f"{base_result.metadata.analysis_type}_with_visual",
                target=base_result.metadata.target,
                start_time=base_result.metadata.start_time,
                end_time=end_time.isoformat(),
                total_packages=base_result.metadata.total_packages,
                total_findings=base_result.metadata.total_findings + visual_finding_count,
                confidence_threshold=base_result.metadata.confidence_threshold,
                osv_enabled=base_result.metadata.osv_enabled,
                visual_analysis_enabled=True
            )
            
            logger.info(f"Visual analysis completed. Found {visual_finding_count} visual security findings")
            
            return AnalysisResult(
                metadata=enhanced_metadata,
                summary=enhanced_summary,
                sbom_data=base_result.sbom_data,
                security_findings=combined_findings,
                suspicious_activities=base_result.suspicious_activities,
                recommendations=base_result.recommendations,
                raw_data=updated_raw_data
            )
            
        except Exception as e:
            logger.error(f"Visual analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze {target} with visual data: {e}")

class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass

def create_analyzer(confidence_threshold: float = None, enable_osv: bool = None) -> SupplyChainAnalyzer:
    """
    Create a new supply chain analyzer instance.
    
    Args:
        confidence_threshold: Minimum confidence score for findings
        enable_osv: Whether to enable OSV API queries
        
    Returns:
        Configured analyzer instance
    """
    return SupplyChainAnalyzer(confidence_threshold, enable_osv)

def analyze_target(target: str, analysis_type: str = "auto", **kwargs) -> AnalysisResult:
    """
    Analyze a target (repository, directory, or SBOM file) automatically.
    
    Args:
        target: Target to analyze (URL, path, etc.)
        analysis_type: Type of analysis ("auto", "github", "local", "sbom")
        **kwargs: Additional arguments for analyzer
        
    Returns:
        Analysis results
    """
    analyzer = create_analyzer(**kwargs)
    
    if analysis_type == "auto":
        # Auto-detect analysis type
        if target.startswith(("http://", "https://")) and "github.com" in target:
            analysis_type = "github"
        elif Path(target).is_dir():
            analysis_type = "local"
        elif Path(target).is_file():
            analysis_type = "sbom"
        else:
            raise AnalysisError(f"Cannot auto-detect analysis type for target: {target}")
    
    if analysis_type == "github":
        return analyzer.analyze_github_repository(target)
    elif analysis_type == "local":
        return analyzer.analyze_local_directory(target)
    elif analysis_type == "sbom":
        return analyzer.analyze_sbom_file(target)
    else:
        raise AnalysisError(f"Unsupported analysis type: {analysis_type}")

def analyze_target_with_screenshots(target: str, screenshot_paths: List[str], 
                                  analysis_type: str = "auto", **kwargs) -> AnalysisResult:
    """
    Analyze a target with visual security analysis from screenshots.
    
    Args:
        target: Target to analyze (URL, path, etc.)
        screenshot_paths: List of screenshot file paths for visual analysis
        analysis_type: Type of analysis ("auto", "github", "local", "sbom")
        **kwargs: Additional arguments for analyzer
        
    Returns:
        Analysis results including visual findings
    """
    analyzer = create_analyzer(**kwargs)
    return analyzer.analyze_with_visual_data(target, analysis_type, screenshot_paths)