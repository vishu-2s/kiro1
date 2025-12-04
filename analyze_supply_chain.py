"""
Core analysis engine for Multi-Agent Security Analysis System.

This module provides the main analysis logic for processing SBOM data,
vulnerability detection, and suspicious activity analysis with finding
generation including confidence scores and evidence.

HYBRID ARCHITECTURE:
- Layer 1: Rule-based detection (fast, deterministic)
- Layer 2: Multi-agent analysis (intelligent, adaptive)
"""

import json
import logging
import os
import subprocess
import tempfile
import shutil
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
from tools.dependency_graph import DependencyGraphAnalyzer
from constants import (
    contains_suspicious_keywords,
    detect_suspicious_network_patterns,
    is_suspicious_package_name,
    calculate_typosquat_confidence
)
from config import config

# Import agent components
from agents.orchestrator import AgentOrchestrator
from agents.types import Finding
from agents.vulnerability_agent import VulnerabilityAnalysisAgent
from agents.reputation_agent import ReputationAnalysisAgent
from agents.code_agent import CodeAnalysisAgent
from agents.supply_chain_agent import SupplyChainAttackAgent
from agents.synthesis_agent import SynthesisAgent
from agents.proactive_validator import ProactiveValidator, validate_before_analysis

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
        # Disable reputation checks for performance (they're slow and sequential)
        findings = check_vulnerable_packages(sbom_data, use_osv=self.enable_osv, check_reputation=False)
        
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
        
        # Get cache statistics
        cache_stats = self._get_cache_statistics()
        
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
        
        # Add cache statistics to raw data
        if raw_data is None:
            raw_data = {}
        raw_data["cache_statistics"] = cache_stats
        
        return AnalysisResult(
            metadata=metadata,
            summary=summary,
            sbom_data=sbom_data,
            security_findings=findings_dicts,
            suspicious_activities=suspicious_activities,
            recommendations=recommendations,
            raw_data=raw_data
        )
    
    def _get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics for the current analysis.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            from tools.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            stats = cache_manager.get_statistics()
            
            # Calculate hit rate if possible
            if stats.get('total_hits', 0) > 0 and stats.get('total_entries', 0) > 0:
                # Approximate hit rate based on hits per entry
                avg_hits_per_entry = stats['total_hits'] / stats['total_entries']
                hit_rate = min(1.0, avg_hits_per_entry / 10.0)  # Normalize to 0-1
                stats['estimated_hit_rate'] = round(hit_rate * 100, 2)
            
            return stats
        except Exception as e:
            logger.warning(f"Failed to get cache statistics: {e}")
            return {"error": "Cache statistics unavailable"}
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], 
                                suspicious_activities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Generate LLM-based recommendations by analyzing the complete analysis context.
        
        Args:
            findings: Security findings with package details
            suspicious_activities: Suspicious activities
            
        Returns:
            Dict with immediate_actions, preventive_measures, and monitoring
        """
        try:
            from openai import OpenAI
            import os
            
            # Check if OpenAI API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not found, using fallback recommendations")
                return self._generate_fallback_recommendations(findings, suspicious_activities)
            
            # Build comprehensive context for LLM
            context = self._build_recommendation_context(findings, suspicious_activities)
            
            # Generate LLM-based recommendations
            client = OpenAI(api_key=api_key)
            
            prompt = f"""You are a security expert analyzing a software supply chain security report. 
Based on the following analysis results, generate detailed, actionable recommendations.

ANALYSIS CONTEXT:
{context}

Generate recommendations in 3 categories:

1. IMMEDIATE ACTIONS (2-3 items, 7-8 lines each):
   - List specific vulnerable packages by name
   - Explain the risk and impact
   - Provide concrete steps to remediate
   - Include timelines (24h, 48h, etc.)

2. PREVENTIVE MEASURES (4-5 items, 7-8 lines each):
   - Long-term security improvements
   - Specific tools and practices
   - Implementation guidance

3. MONITORING (4-5 items, 7-8 lines each):
   - Ongoing security practices
   - Metrics to track
   - Alert configurations

Format as JSON:
{{
  "immediate_actions": ["action1", "action2"],
  "preventive_measures": ["measure1", "measure2", ...],
  "monitoring": ["practice1", "practice2", ...]
}}

Make recommendations specific to the actual packages and findings in the report. Use emojis for visual clarity."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior security engineer specializing in software supply chain security."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more focused recommendations
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse LLM response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                recommendations = json.loads(json_match.group())
                logger.info("Successfully generated LLM-based recommendations")
                return recommendations
            else:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse LLM recommendations, using fallback")
                return self._generate_fallback_recommendations(findings, suspicious_activities)
                
        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}, using fallback")
            return self._generate_fallback_recommendations(findings, suspicious_activities)
    
    def _build_recommendation_context(self, findings: List[Dict[str, Any]], 
                                     suspicious_activities: List[Dict[str, Any]]) -> str:
        """Build comprehensive context for LLM recommendation generation."""
        
        # Analyze findings
        critical_packages = []
        high_packages = []
        medium_packages = []
        malicious_packages = []
        vuln_details = []
        
        for finding in findings:
            pkg_name = finding.get("package", "unknown")
            severity = finding.get("severity", "unknown")
            finding_type = finding.get("finding_type", "unknown")
            description = finding.get("description", "")
            
            if severity == "critical":
                critical_packages.append(pkg_name)
            elif severity == "high":
                high_packages.append(pkg_name)
            elif severity == "medium":
                medium_packages.append(pkg_name)
                
            if finding_type == "malicious_package":
                malicious_packages.append(pkg_name)
            
            # Collect vulnerability details
            if finding_type == "vulnerability":
                vuln_details.append({
                    "package": pkg_name,
                    "severity": severity,
                    "description": description[:100]
                })
        
        # Build context string
        context_parts = [
            f"Total Findings: {len(findings)}",
            f"Critical: {len(set(critical_packages))} packages - {', '.join(list(set(critical_packages))[:5])}",
            f"High: {len(set(high_packages))} packages - {', '.join(list(set(high_packages))[:5])}",
            f"Medium: {len(set(medium_packages))} packages - {', '.join(list(set(medium_packages))[:5])}",
        ]
        
        if malicious_packages:
            context_parts.append(f"Malicious Packages: {', '.join(set(malicious_packages))}")
        
        if suspicious_activities:
            context_parts.append(f"Suspicious Activities: {len(suspicious_activities)} detected")
        
        # Add sample vulnerability details
        if vuln_details[:3]:
            context_parts.append("\nSample Vulnerabilities:")
            for vuln in vuln_details[:3]:
                context_parts.append(f"  - {vuln['package']} ({vuln['severity']}): {vuln['description']}")
        
        return "\n".join(context_parts)
    
    def _generate_fallback_recommendations(self, findings: List[Dict[str, Any]], 
                                          suspicious_activities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate basic recommendations when LLM is unavailable."""
        
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")
        
        immediate = []
        if critical_count > 0:
            immediate.append(f"Review and fix {critical_count} critical vulnerabilities immediately")
        if high_count > 0:
            immediate.append(f"Address {high_count} high-severity vulnerabilities within 48 hours")
        if not immediate:
            immediate.append("No critical issues detected - continue monitoring")
        
        return {
            "immediate_actions": immediate,
            "preventive_measures": [
                "Implement dependency scanning in CI/CD pipeline",
                "Use lock files to ensure reproducible builds",
                "Enable automated security updates"
            ],
            "monitoring": [
                "Regularly update dependencies",
                "Monitor security advisories",
                "Track security metrics"
            ]
        }
    
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


# ============================================================================
# HYBRID ARCHITECTURE IMPLEMENTATION
# ============================================================================

def clone_github_repo(repo_url: str) -> str:
    """
    Clone a GitHub repository to a temporary directory.
    
    Args:
        repo_url: GitHub repository URL
    
    Returns:
        Path to cloned repository
    
    Raises:
        RuntimeError: If cloning fails
    """
    logger.info(f"Cloning GitHub repository: {repo_url}")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="supply_chain_analysis_")
    
    try:
        # Clone repository
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        logger.info(f"Repository cloned to: {temp_dir}")
        return temp_dir
    
    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("Git clone timed out after 60 seconds")
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e}")


def detect_input_mode(target: str) -> str:
    """
    Auto-detect input mode from target string.
    
    Args:
        target: Target string (URL or path)
    
    Returns:
        Input mode: 'github' or 'local'
    """
    if target.startswith(("http://", "https://", "git@")):
        return "github"
    elif os.path.isdir(target) or os.path.isfile(target):
        return "local"
    else:
        # Default to local
        logger.warning(f"Could not determine input mode for '{target}', defaulting to 'local'")
        return "local"


def detect_ecosystem(project_dir: str) -> str:
    """
    Detect primary ecosystem from project directory.
    
    Args:
        project_dir: Path to project directory
    
    Returns:
        Ecosystem name: 'npm', 'pypi', or 'unknown'
    """
    # Check for npm
    if os.path.exists(os.path.join(project_dir, "package.json")):
        return "npm"
    
    # Check for Python
    if os.path.exists(os.path.join(project_dir, "requirements.txt")) or \
       os.path.exists(os.path.join(project_dir, "setup.py")) or \
       os.path.exists(os.path.join(project_dir, "pyproject.toml")):
        return "pypi"
    
    logger.warning(f"Could not detect ecosystem in {project_dir}")
    return "unknown"


def find_manifest_file(project_dir: str, ecosystem: str) -> Optional[str]:
    """
    Find manifest file for the given ecosystem.
    
    Args:
        project_dir: Path to project directory
        ecosystem: Ecosystem name
    
    Returns:
        Path to manifest file, or None if not found
    """
    if ecosystem == "npm":
        manifest_path = os.path.join(project_dir, "package.json")
        if os.path.exists(manifest_path):
            return manifest_path
    
    elif ecosystem == "pypi":
        # Try requirements.txt first
        manifest_path = os.path.join(project_dir, "requirements.txt")
        if os.path.exists(manifest_path):
            return manifest_path
        
        # Try setup.py
        manifest_path = os.path.join(project_dir, "setup.py")
        if os.path.exists(manifest_path):
            return manifest_path
        
        # Try pyproject.toml
        manifest_path = os.path.join(project_dir, "pyproject.toml")
        if os.path.exists(manifest_path):
            return manifest_path
    
    logger.warning(f"No manifest file found for ecosystem '{ecosystem}' in {project_dir}")
    return None


class RuleBasedDetectionEngine:
    """
    Fast, deterministic detection layer for known patterns.
    
    Validates Requirements 2.1-2.5:
    - 2.1: Apply pattern matching for known malicious patterns
    - 2.2: Query vulnerability databases (OSV, CVE)
    - 2.3: Calculate reputation scores
    - 2.4: Use Levenshtein distance for typosquatting
    - 2.5: Tag findings with detection_method: "rule_based"
    """
    
    def __init__(self):
        """Initialize rule-based detection engine."""
        self.enable_osv = config.ENABLE_OSV_QUERIES
        logger.info("Initialized RuleBasedDetectionEngine")
    
    def detect(self, packages: List[Dict[str, Any]]) -> List[Finding]:
        """
        Run rule-based detection on packages.
        
        Args:
            packages: List of package dictionaries
        
        Returns:
            List of findings with detection_method='rule_based'
        """
        logger.info(f"Running rule-based detection on {len(packages)} packages")
        findings = []
        
        # Pattern matching
        findings.extend(self._pattern_matching(packages))
        
        # Vulnerability database lookup
        findings.extend(self._vulnerability_lookup(packages))
        
        # Reputation scoring
        findings.extend(self._reputation_scoring(packages))
        
        # Typosquatting detection
        findings.extend(self._typosquatting_detection(packages))
        
        logger.info(f"Rule-based detection found {len(findings)} findings")
        return findings
    
    def _pattern_matching(self, packages: List[Dict[str, Any]]) -> List[Finding]:
        """Pattern matching for known malicious patterns."""
        findings = []
        
        for pkg in packages:
            pkg_name = pkg.get("name", "")
            pkg_version = pkg.get("version", "")
            
            # Check for suspicious package names
            if is_suspicious_package_name(pkg_name, pkg.get("ecosystem", "npm")):
                findings.append(Finding(
                    package_name=pkg_name,
                    package_version=pkg_version,
                    finding_type="suspicious_package_name",
                    severity="medium",
                    description=f"Package name '{pkg_name}' matches suspicious patterns",
                    detection_method="rule_based",
                    confidence=0.7,
                    evidence={"pattern": "suspicious_name"},
                    remediation="Review package source and verify legitimacy"
                ))
        
        return findings
    
    def _vulnerability_lookup(self, packages: List[Dict[str, Any]]) -> List[Finding]:
        """Query vulnerability databases."""
        findings = []
        
        if not self.enable_osv:
            logger.debug("OSV queries disabled, skipping vulnerability lookup")
            return findings
        
        # Create SBOM structure for vulnerability checking
        sbom_data = {
            "packages": packages
        }
        
        # Use existing vulnerability checking
        # Disable reputation checks for performance (they're slow and sequential)
        vuln_findings = check_vulnerable_packages(sbom_data, use_osv=True, check_reputation=False)
        
        # Convert to Finding objects with proper deduplication
        seen_findings = set()
        for vuln_finding in vuln_findings:
            # Create unique key for deduplication
            finding_key = (
                vuln_finding.package,
                vuln_finding.version,
                vuln_finding.finding_type,
                vuln_finding.severity
            )
            
            # Skip if we've already seen this exact finding
            if finding_key in seen_findings:
                continue
            seen_findings.add(finding_key)
            
            # Build proper description from evidence
            if vuln_finding.evidence and len(vuln_finding.evidence) > 0:
                # Use first evidence item as description, or combine them
                description = vuln_finding.evidence[0] if isinstance(vuln_finding.evidence, list) else str(vuln_finding.evidence)
            else:
                description = f"{vuln_finding.finding_type.replace('_', ' ').title()} detected"
            
            findings.append(Finding(
                package_name=vuln_finding.package,
                package_version=vuln_finding.version,
                finding_type=vuln_finding.finding_type,
                severity=vuln_finding.severity,
                description=description,
                detection_method="rule_based",
                confidence=vuln_finding.confidence,
                evidence={"source": vuln_finding.source, "details": vuln_finding.evidence},
                remediation="; ".join(vuln_finding.recommendations) if vuln_finding.recommendations else None
            ))
        
        return findings
    
    def _reputation_scoring(self, packages: List[Dict[str, Any]]) -> List[Finding]:
        """Calculate reputation scores."""
        findings = []
        
        # Use reputation service for scoring
        from tools.reputation_service import ReputationScorer
        
        reputation_scorer = ReputationScorer()
        
        for pkg in packages:
            pkg_name = pkg.get("name", "")
            pkg_version = pkg.get("version", "")
            ecosystem = pkg.get("ecosystem", "npm")
            
            # Get reputation score
            try:
                reputation_data = reputation_scorer.calculate_reputation(
                    pkg_name, 
                    ecosystem
                )
                reputation_score = reputation_data.get("score", 0.5)
            except Exception as e:
                logger.debug(f"Failed to get reputation for {pkg_name}: {e}")
                reputation_score = 0.5  # Default score
            
            # Flag low reputation packages
            if reputation_score < 0.3:
                findings.append(Finding(
                    package_name=pkg_name,
                    package_version=pkg_version,
                    finding_type="low_reputation",
                    severity="medium",
                    description=f"Package has low reputation score: {reputation_score:.2f}",
                    detection_method="rule_based",
                    confidence=0.8,
                    evidence={"reputation_score": reputation_score},
                    remediation="Review package source and verify trustworthiness"
                ))
        
        return findings
    
    def _typosquatting_detection(self, packages: List[Dict[str, Any]]) -> List[Finding]:
        """Detect potential typosquatting."""
        findings = []
        
        # Popular packages to check against
        popular_packages = {
            "npm": ["react", "express", "lodash", "axios", "webpack", "babel"],
            "pypi": ["requests", "numpy", "pandas", "django", "flask", "pytest"]
        }
        
        for pkg in packages:
            pkg_name = pkg.get("name", "")
            pkg_version = pkg.get("version", "")
            ecosystem = pkg.get("ecosystem", "npm")
            
            # Check against popular packages
            for popular_pkg in popular_packages.get(ecosystem, []):
                confidence = calculate_typosquat_confidence(pkg_name, popular_pkg)
                
                if confidence > 0.7 and pkg_name != popular_pkg:
                    findings.append(Finding(
                        package_name=pkg_name,
                        package_version=pkg_version,
                        finding_type="typosquat",
                        severity="high",
                        description=f"Potential typosquat of '{popular_pkg}' (confidence: {confidence:.2f})",
                        detection_method="rule_based",
                        confidence=confidence,
                        evidence={"target_package": popular_pkg},
                        remediation=f"Verify package name - did you mean '{popular_pkg}'?"
                    ))
        
        return findings


def analyze_project_hybrid(
    target: str, 
    input_mode: str = "auto",
    use_agents: bool = True,
    force_ecosystem: str = None
) -> str:
    """
    Main entry point for hybrid security analysis.
    
    Validates Requirements 2.1-2.5, 14.1-14.5:
    - Combines rule-based detection with agent analysis
    - Supports GitHub URL and local directory input
    - Auto-detects input mode
    - Maintains backward compatibility
    - Generates package-centric JSON output
    
    Args:
        target: GitHub URL or local directory path
        input_mode: "github", "local", or "auto" (auto-detect)
        use_agents: Whether to use agent analysis (default: True)
        force_ecosystem: Force specific ecosystem ("npm" or "pypi"), None for auto-detect
    
    Returns:
        Path to generated JSON report
    """
    start_time = datetime.now()
    logger.info(f"Starting hybrid analysis: {target}")
    
    # Step 0: PROACTIVE VALIDATION - Prevent errors before they occur
    logger.info("Running proactive validation checks...")
    validator = ProactiveValidator()
    
    # Validate environment first
    env_valid, env_issues = validator.validate_environment()
    if not env_valid:
        error_msg = "Environment validation failed:\n"
        for issue in env_issues:
            if issue.level.value == "error":
                error_msg += f"  ❌ {issue.message}\n  💡 {issue.fix_suggestion}\n"
        logger.error(error_msg)
        raise AnalysisError(error_msg)
    
    # Log warnings and info
    for issue in env_issues:
        if issue.level.value == "warning":
            logger.warning(f"{issue.message} - {issue.fix_suggestion}")
        elif issue.level.value == "info":
            logger.info(f"{issue.message} - {issue.fix_suggestion}")
    
    # Validate network connectivity (non-blocking)
    net_valid, net_issues = validator.validate_network_connectivity()
    if not net_valid:
        logger.warning("Network connectivity issues detected - analysis may be limited")
        for issue in net_issues:
            logger.warning(f"{issue.message} - {issue.fix_suggestion}")
    
    # Step 1: Detect input mode
    if input_mode == "auto":
        input_mode = detect_input_mode(target)
        logger.info(f"Auto-detected input mode: {input_mode}")
    
    # Step 2: Get project files
    project_dir = None
    cleanup_temp = False
    
    try:
        if input_mode == "github":
            project_dir = clone_github_repo(target)
            cleanup_temp = True
        else:
            project_dir = target
        
        # Step 3: Detect ecosystem (or use forced ecosystem)
        if force_ecosystem:
            ecosystem = force_ecosystem
            logger.info(f"Using forced ecosystem: {ecosystem}")
        else:
            ecosystem = detect_ecosystem(project_dir)
            logger.info(f"Auto-detected ecosystem: {ecosystem}")
        
        if ecosystem == "unknown":
            logger.warning("Could not detect ecosystem, analysis may be limited")
        
        # Step 4: Find manifest file
        manifest_file = find_manifest_file(project_dir, ecosystem)
        
        if manifest_file is None:
            logger.error(f"No manifest file found for ecosystem '{ecosystem}'")
            raise AnalysisError(f"No manifest file found in {project_dir}")
        
        logger.info(f"Found manifest file: {manifest_file}")
        
        # Step 4.5: PROACTIVE VALIDATION - Validate manifest file
        logger.info("Validating manifest file...")
        manifest_valid, manifest_issues = validator.validate_manifest_file(manifest_file, ecosystem)
        
        if not manifest_valid:
            error_msg = f"Manifest validation failed for {manifest_file}:\n"
            for issue in manifest_issues:
                if issue.level.value == "error":
                    error_msg += f"  ❌ {issue.message}\n  💡 {issue.fix_suggestion}\n"
            logger.error(error_msg)
            raise AnalysisError(error_msg)
        
        # Log manifest warnings
        for issue in manifest_issues:
            if issue.level.value == "warning":
                logger.warning(f"{issue.message} - {issue.fix_suggestion}")
        
        # Step 5: Build dependency graph
        logger.info("Building dependency graph...")
        dep_analyzer = DependencyGraphAnalyzer()
        
        try:
            # Build graph with timeout protection
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Dependency graph building timed out")
            
            # Set timeout for dependency graph building (30 seconds)
            if hasattr(signal, 'SIGALRM'):  # Unix-like systems
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
            
            dependency_graph = dep_analyzer.build_graph(manifest_file, ecosystem)
            packages = dep_analyzer.get_package_list()
            
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
            
            logger.info(f"Dependency graph built: {len(packages)} packages")
            
            if len(packages) == 0:
                logger.warning("No packages found in dependency graph!")
                # Try to extract packages directly from manifest
                if ecosystem == "npm":
                    from tools.npm_analyzer import NpmAnalyzer
                    npm_analyzer = NpmAnalyzer()
                    deps = npm_analyzer.extract_dependencies(manifest_file)
                    packages = [{"name": d["name"], "version": d["version"]} for d in deps]
                    logger.info(f"Extracted {len(packages)} packages directly from manifest")
                elif ecosystem == "pypi":
                    from tools.python_analyzer import PythonAnalyzer
                    py_analyzer = PythonAnalyzer()
                    deps = py_analyzer.extract_dependencies(manifest_file)
                    packages = [{"name": d["name"], "version": d["version"]} for d in deps]
                    logger.info(f"Extracted {len(packages)} packages directly from manifest")
        
        except TimeoutError as e:
            logger.error(f"Dependency graph building timed out: {e}")
            # Fallback: extract packages directly from manifest
            packages = []
            if ecosystem == "npm":
                from tools.npm_analyzer import NpmAnalyzer
                npm_analyzer = NpmAnalyzer()
                deps = npm_analyzer.extract_dependencies(manifest_file)
                packages = [{"name": d["name"], "version": d["version"]} for d in deps]
            elif ecosystem == "pypi":
                from tools.python_analyzer import PythonAnalyzer
                py_analyzer = PythonAnalyzer()
                deps = py_analyzer.extract_dependencies(manifest_file)
                packages = [{"name": d["name"], "version": d["version"]} for d in deps]
            
            dependency_graph = {"nodes": [], "edges": [], "packages": packages}
            logger.info(f"Using fallback: extracted {len(packages)} packages directly")
        
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            # Fallback to empty graph
            dependency_graph = {"nodes": [], "edges": [], "packages": []}
            packages = []
        
        # Step 6: Run rule-based detection (Layer 1)
        logger.info("Running rule-based detection...")
        rule_engine = RuleBasedDetectionEngine()
        initial_findings = rule_engine.detect(packages)
        
        # Step 6.5: Analyze root package.json scripts for malicious patterns (npm only)
        if ecosystem == "npm":
            logger.info("Analyzing root package.json scripts...")
            try:
                import json
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                
                scripts = package_json.get('scripts', {})
                package_name = package_json.get('name', 'root-package')
                
                if scripts:
                    from tools.sbom_tools import _analyze_npm_scripts
                    script_findings = _analyze_npm_scripts(scripts, package_name)
                    
                    if script_findings:
                        logger.warning(f"Found {len(script_findings)} malicious scripts in root package.json")
                        # Convert SecurityFinding to Finding objects
                        for sf in script_findings:
                            initial_findings.append(Finding(
                                package_name=sf.package,
                                package_version="1.0.0",  # Root package
                                finding_type=sf.finding_type,
                                severity=sf.severity,
                                description=sf.evidence[0] if sf.evidence else "Malicious script detected",
                                detection_method="rule_based",
                                confidence=sf.confidence,
                                evidence={"source": sf.source, "details": sf.evidence},
                                remediation="; ".join(sf.recommendations) if sf.recommendations else None
                            ))
                    else:
                        logger.info("No malicious scripts detected in root package.json")
                else:
                    logger.info("No scripts found in root package.json")
            except Exception as e:
                logger.warning(f"Failed to analyze root package scripts: {e}")
        
        logger.info(f"Rule-based detection complete: {len(initial_findings)} findings")
        
        # Step 7: Run agent analysis (Layer 2) if enabled
        if use_agents:
            logger.info("Running multi-agent analysis...")
            
            try:
                # Initialize orchestrator
                orchestrator = AgentOrchestrator()
                
                # Register agents
                logger.info("Registering agents...")
                orchestrator.register_agent("vulnerability_analysis", VulnerabilityAnalysisAgent())
                orchestrator.register_agent("reputation_analysis", ReputationAnalysisAgent())
                orchestrator.register_agent("code_analysis", CodeAnalysisAgent())
                orchestrator.register_agent("supply_chain_analysis", SupplyChainAttackAgent())
                orchestrator.register_agent("synthesis", SynthesisAgent())
                logger.info("All agents registered successfully")
                
                # Run orchestration with timeout protection
                logger.info("Starting orchestration...")
                final_json = orchestrator.orchestrate(
                    initial_findings=initial_findings,
                    dependency_graph=dependency_graph,
                    input_mode=input_mode,
                    project_path=target,  # Use original target (user input), not project_dir (temp path)
                    ecosystem=ecosystem
                )
                
                logger.info("Multi-agent analysis complete")
                
            except Exception as e:
                logger.error(f"Agent analysis failed: {e}", exc_info=True)
                logger.warning("Falling back to simple report generation")
                # Generate simple report without agents
                final_json = _generate_simple_report(
                    initial_findings, 
                    dependency_graph, 
                    packages,
                    input_mode,
                    target,  # Use original target (user input), not project_dir (temp path)
                    ecosystem
                )
        else:
            # Generate simple report without agents
            logger.info("Agent analysis disabled, generating simple report")
            final_json = _generate_simple_report(
                initial_findings, 
                dependency_graph, 
                packages,
                input_mode,
                target,  # Use original target (user input), not project_dir (temp path)
                ecosystem
            )
        
        # Step 8: Add performance metrics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if "performance_metrics" not in final_json:
            final_json["performance_metrics"] = {}
        
        # Ensure duration is at least a small positive value for testing
        final_json["performance_metrics"]["total_analysis_time"] = max(duration, 0.001)
        final_json["performance_metrics"]["rule_based_time"] = final_json["performance_metrics"].get("rule_based_time", 0)
        final_json["performance_metrics"]["agent_time"] = final_json["performance_metrics"].get("total_duration_seconds", 0)
        
        # Step 9: Add dependency graph to final JSON
        if "dependency_graph" not in final_json:
            final_json["dependency_graph"] = dependency_graph
        
        # Step 10: Write output with backup
        output_dir = os.getenv("OUTPUT_DIRECTORY", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "demo_ui_comprehensive_report.json")
        
        # Create backup of existing file if it exists
        if os.path.exists(output_path):
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(output_dir, f"demo_ui_comprehensive_report_backup_{backup_timestamp}.json")
            try:
                import shutil
                shutil.copy2(output_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Write new report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis complete. Output written to: {output_path}")
        logger.info(f"Total duration: {duration:.2f}s")
        
        return output_path
    
    finally:
        # Cleanup temporary directory if needed
        if cleanup_temp and project_dir:
            logger.info(f"Cleaning up temporary directory: {project_dir}")
            shutil.rmtree(project_dir, ignore_errors=True)


def _generate_simple_report(
    findings: List[Finding],
    dependency_graph: Dict[str, Any],
    packages: List[Dict[str, str]],
    input_mode: str,
    project_path: str,
    ecosystem: str
) -> Dict[str, Any]:
    """
    Generate simple report without agent analysis.
    
    Args:
        findings: Rule-based findings
        dependency_graph: Dependency graph
        packages: List of packages
        input_mode: Input mode
        project_path: Project path
        ecosystem: Ecosystem
    
    Returns:
        Simple JSON report
    """
    # Count findings by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        severity = finding.severity.lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Group findings by package
    packages_dict = {}
    for finding in findings:
        pkg_name = finding.package_name
        if pkg_name not in packages_dict:
            packages_dict[pkg_name] = {
                "name": pkg_name,
                "version": finding.package_version,
                "ecosystem": ecosystem,
                "findings": [],
                "risk_score": 0.0,
                "risk_level": "low"
            }
        
        packages_dict[pkg_name]["findings"].append({
            "type": finding.finding_type,
            "severity": finding.severity,
            "description": finding.description,
            "confidence": finding.confidence,
            "evidence": finding.evidence,
            "remediation": finding.remediation
        })
    
    # Calculate risk scores
    for pkg_data in packages_dict.values():
        risk_score = 0.0
        for finding in pkg_data["findings"]:
            severity_weight = {
                "critical": 1.0,
                "high": 0.7,
                "medium": 0.4,
                "low": 0.2
            }
            weight = severity_weight.get(finding["severity"].lower(), 0.2)
            risk_score += weight * finding["confidence"]
        
        pkg_data["risk_score"] = min(1.0, risk_score)
        
        # Determine risk level
        if pkg_data["risk_score"] >= 0.8:
            pkg_data["risk_level"] = "critical"
        elif pkg_data["risk_score"] >= 0.6:
            pkg_data["risk_level"] = "high"
        elif pkg_data["risk_score"] >= 0.3:
            pkg_data["risk_level"] = "medium"
        else:
            pkg_data["risk_level"] = "low"
    
    return {
        "metadata": {
            "analysis_id": f"analysis_{int(datetime.now().timestamp())}",
            "analysis_type": f"{input_mode}_rule_based",
            "target": project_path,
            "timestamp": datetime.now().isoformat(),
            "ecosystem": ecosystem,
            "agent_analysis_enabled": False
        },
        "summary": {
            "total_packages": len(packages),
            "packages_with_findings": len(packages_dict),
            "total_findings": len(findings),
            "critical_findings": severity_counts["critical"],
            "high_findings": severity_counts["high"],
            "medium_findings": severity_counts["medium"],
            "low_findings": severity_counts["low"]
        },
        "security_findings": {
            "packages": list(packages_dict.values())
        },
        "dependency_graph": dependency_graph,
        "recommendations": {
            "immediate_actions": [
                f"Review {severity_counts['critical']} critical findings" if severity_counts['critical'] > 0 else None,
                f"Address {severity_counts['high']} high-severity findings" if severity_counts['high'] > 0 else None
            ],
            "preventive_measures": [
                "Implement dependency scanning in CI/CD pipeline",
                "Use lock files to ensure reproducible builds"
            ],
            "monitoring": [
                "Regularly update dependencies",
                "Monitor security advisories"
            ]
        }
    }