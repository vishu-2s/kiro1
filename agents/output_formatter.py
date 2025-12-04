"""
Clean Output Formatter for Orchestrator Results.

This module consolidates scattered data from rule-based detection and all agents
into a clean, organized vulnerability report.

Philosophy: "One vulnerability, one entry, all details in one place"
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from agents.safe_types import SafeDict, SafeSharedContext, safe_unicode_str

logger = logging.getLogger(__name__)


@dataclass
class ConsolidatedVulnerability:
    """
    Single consolidated vulnerability with all details.
    
    All information about one vulnerability in one place.
    """
    # Identity
    vulnerability_id: str
    package_name: str
    package_version: str
    ecosystem: str
    
    # Description
    title: str
    description: str
    severity: str  # critical, high, medium, low
    cvss_score: Optional[float] = None
    
    # Status
    status: str = "active"  # active, fixed, not_applicable, not_available
    is_current_version_affected: bool = True
    
    # Fix Information
    fixed_versions: List[str] = field(default_factory=list)
    recommendation: str = ""
    
    # Additional Details
    affected_versions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    modified_date: Optional[str] = None
    
    # Analysis Context
    detection_method: str = "osv_api"  # osv_api, rule_based, agent_analysis
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "vulnerability_id": self.vulnerability_id,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "ecosystem": self.ecosystem,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "status": self.status,
            "is_current_version_affected": self.is_current_version_affected,
            "fixed_versions": self.fixed_versions,
            "recommendation": self.recommendation,
            "affected_versions": self.affected_versions,
            "references": self.references,
            "aliases": self.aliases,
            "published_date": self.published_date,
            "modified_date": self.modified_date,
            "detection_method": self.detection_method,
            "confidence": self.confidence
        }


@dataclass
class PackageSummary:
    """
    Summary of a package with all its issues.
    """
    package_name: str
    package_version: str
    ecosystem: str
    
    # Vulnerability Summary
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Reputation
    reputation_score: Optional[float] = None
    risk_level: str = "unknown"  # critical, high, medium, low, unknown
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Code Analysis
    code_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Supply Chain
    supply_chain_risks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Overall Assessment
    overall_risk: str = "unknown"  # critical, high, medium, low, safe
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "package_name": self.package_name,
            "package_version": self.package_version,
            "ecosystem": self.ecosystem,
            "total_vulnerabilities": self.total_vulnerabilities,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "reputation_score": self.reputation_score,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "code_issues": self.code_issues,
            "supply_chain_risks": self.supply_chain_risks,
            "overall_risk": self.overall_risk,
            "recommendation": self.recommendation
        }


class CleanOutputFormatter:
    """
    Formats orchestrator output into clean, consolidated structure.
    
    Takes scattered data from multiple agents and creates:
    1. Consolidated vulnerability list (one entry per vulnerability)
    2. Package summaries (one entry per package)
    3. Overall analysis summary
    """
    
    def format_analysis_results(
        self,
        context: SafeSharedContext,
        rule_based_findings: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format complete analysis results into clean structure.
        
        Args:
            context: Shared context with all agent results
            rule_based_findings: Optional rule-based findings
        
        Returns:
            Clean, consolidated report
        """
        logger.info("Formatting analysis results into clean structure...")
        
        # Consolidate vulnerabilities
        vulnerabilities = self._consolidate_vulnerabilities(context, rule_based_findings)
        
        # Create package summaries
        packages = self._create_package_summaries(context, vulnerabilities)
        
        # Calculate overall summary
        summary = self._calculate_summary(vulnerabilities, packages)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities, packages)
        
        # Create metadata
        metadata = self._create_metadata(context)
        
        # Create base report
        report = {
            "metadata": metadata,
            "summary": summary,
            "vulnerabilities": [v.to_dict() for v in vulnerabilities],
            "packages": [p.to_dict() for p in packages],
            "recommendations": recommendations,
            "analysis_details": self._create_analysis_details(context)
        }
        
        # Add agentic insights
        from agents.agentic_insights_formatter import add_agentic_insights_to_report
        report = add_agentic_insights_to_report(report, context)
        
        return report
    
    def _consolidate_vulnerabilities(
        self,
        context: SafeSharedContext,
        rule_based_findings: List[Dict[str, Any]] = None
    ) -> List[ConsolidatedVulnerability]:
        """
        Consolidate vulnerabilities from all sources into single list.
        
        Args:
            context: Shared context
            rule_based_findings: Rule-based findings
        
        Returns:
            List of consolidated vulnerabilities
        """
        vulnerabilities = []
        seen_ids = set()
        
        # Get vulnerability agent results
        vuln_result = context.get_agent_result("vulnerability_analysis")
        if vuln_result and vuln_result.success:
            packages = vuln_result.get_packages()
            
            for pkg in packages:
                pkg_name = pkg.safe_str("package_name", "unknown")
                pkg_version = pkg.safe_str("package_version", "unknown")
                ecosystem = pkg.safe_str("ecosystem", context.ecosystem)
                
                vulns = pkg.safe_list("vulnerabilities", [])
                for vuln_data in vulns:
                    vuln = SafeDict(vuln_data)
                    vuln_id = vuln.safe_str("id", "unknown")
                    
                    # Skip duplicates
                    if vuln_id in seen_ids:
                        continue
                    seen_ids.add(vuln_id)
                    
                    # Get LLM analysis if available
                    llm_analysis = pkg.safe_dict("llm_assessment")
                    
                    # Enhance description with LLM insights
                    description = vuln.safe_str("details", "No description")
                    if llm_analysis and llm_analysis.get("assessment"):
                        description += f"\n\n🤖 AI Analysis: {llm_analysis.get('assessment')}"
                    
                    # Enhance recommendation with LLM insights
                    recommendation = self._generate_vuln_recommendation(vuln, pkg_name)
                    if llm_analysis:
                        if llm_analysis.get("recommended_action"):
                            recommendation = llm_analysis.get("recommended_action")
                        if llm_analysis.get("exploitation_likelihood"):
                            recommendation += f" (Exploitation likelihood: {llm_analysis.get('exploitation_likelihood')})"
                    
                    # Create consolidated vulnerability
                    consolidated = ConsolidatedVulnerability(
                        vulnerability_id=vuln_id,
                        package_name=pkg_name,
                        package_version=pkg_version,
                        ecosystem=ecosystem,
                        title=vuln.safe_str("summary", "No title"),
                        description=description,
                        severity=vuln.safe_str("severity", "unknown").lower(),
                        cvss_score=vuln.safe_float("cvss_score"),
                        status=self._determine_status(vuln),
                        is_current_version_affected=vuln.get("is_current_version_affected", True),
                        fixed_versions=vuln.safe_list("fixed_versions", []),
                        recommendation=recommendation,
                        affected_versions=vuln.safe_list("affected_versions", []),
                        references=vuln.safe_list("references", []),
                        aliases=vuln.safe_list("aliases", []),
                        published_date=vuln.safe_str("published"),
                        modified_date=vuln.safe_str("modified"),
                        detection_method="osv_api_with_ai" if llm_analysis else "osv_api",
                        confidence=1.0
                    )
                    
                    vulnerabilities.append(consolidated)
        
        # Add rule-based findings
        if rule_based_findings:
            for finding in rule_based_findings:
                finding_dict = SafeDict(finding)
                vuln_id = f"rule_{finding_dict.safe_str('finding_type', 'unknown')}_{finding_dict.safe_str('package_name', 'unknown')}"
                
                if vuln_id not in seen_ids:
                    seen_ids.add(vuln_id)
                    
                    consolidated = ConsolidatedVulnerability(
                        vulnerability_id=vuln_id,
                        package_name=finding_dict.safe_str("package_name", "unknown"),
                        package_version=finding_dict.safe_str("package_version", "unknown"),
                        ecosystem=context.ecosystem,
                        title=finding_dict.safe_str("finding_type", "Unknown Issue"),
                        description=finding_dict.safe_str("description", "No description"),
                        severity=finding_dict.safe_str("severity", "medium").lower(),
                        status="active",
                        recommendation=finding_dict.safe_str("remediation", "Review and assess"),
                        detection_method="rule_based",
                        confidence=finding_dict.safe_float("confidence", 0.8)
                    )
                    
                    vulnerabilities.append(consolidated)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
        vulnerabilities.sort(key=lambda v: (severity_order.get(v.severity, 4), v.package_name))
        
        logger.info(f"Consolidated {len(vulnerabilities)} vulnerabilities")
        return vulnerabilities
    
    def _create_package_summaries(
        self,
        context: SafeSharedContext,
        vulnerabilities: List[ConsolidatedVulnerability]
    ) -> List[PackageSummary]:
        """
        Create package summaries with all information.
        
        Args:
            context: Shared context
            vulnerabilities: Consolidated vulnerabilities
        
        Returns:
            List of package summaries
        """
        packages_dict = {}
        
        # Initialize from context packages
        for pkg_name in context.packages:
            packages_dict[pkg_name] = PackageSummary(
                package_name=pkg_name,
                package_version="unknown",
                ecosystem=context.ecosystem
            )
        
        # Add vulnerability counts
        for vuln in vulnerabilities:
            pkg_name = vuln.package_name
            if pkg_name not in packages_dict:
                packages_dict[pkg_name] = PackageSummary(
                    package_name=pkg_name,
                    package_version=vuln.package_version,
                    ecosystem=vuln.ecosystem
                )
            
            summary = packages_dict[pkg_name]
            summary.total_vulnerabilities += 1
            
            if vuln.severity == "critical":
                summary.critical_count += 1
            elif vuln.severity == "high":
                summary.high_count += 1
            elif vuln.severity == "medium":
                summary.medium_count += 1
            elif vuln.severity == "low":
                summary.low_count += 1
        
        # Add reputation data with LLM analysis
        rep_result = context.get_agent_result("reputation_analysis")
        if rep_result and rep_result.success:
            for pkg in rep_result.get_packages():
                pkg_name = pkg.safe_str("package_name", "unknown")
                if pkg_name in packages_dict:
                    summary = packages_dict[pkg_name]
                    summary.reputation_score = pkg.safe_float("reputation_score")
                    summary.risk_level = pkg.safe_str("risk_level", "unknown")
                    summary.risk_factors = pkg.safe_list("risk_factors", [])
                    
                    # Add LLM reputation analysis if available
                    llm_rep = pkg.safe_dict("llm_reputation_analysis")
                    if llm_rep and llm_rep.get("trust_assessment"):
                        # Add AI insights to risk factors
                        summary.risk_factors.append({
                            "type": "ai_analysis",
                            "severity": "info",
                            "description": f"🤖 AI Assessment: {llm_rep.get('trust_assessment')}",
                            "score": llm_rep.get("trust_score", 0) / 10.0
                        })
        
        # Add code analysis data
        code_result = context.get_agent_result("code_analysis")
        if code_result and code_result.success:
            for pkg in code_result.get_packages():
                pkg_name = pkg.safe_str("package_name", "unknown")
                if pkg_name in packages_dict:
                    summary = packages_dict[pkg_name]
                    summary.code_issues = pkg.safe_list("code_issues", [])
        
        # Add supply chain data
        sc_result = context.get_agent_result("supply_chain_analysis")
        if sc_result and sc_result.success:
            for pkg in sc_result.get_packages():
                pkg_name = pkg.safe_str("package_name", "unknown")
                if pkg_name in packages_dict:
                    summary = packages_dict[pkg_name]
                    summary.supply_chain_risks = pkg.safe_list("supply_chain_risks", [])
        
        # Calculate overall risk and recommendations
        for summary in packages_dict.values():
            summary.overall_risk = self._calculate_overall_risk(summary)
            summary.recommendation = self._generate_package_recommendation(summary)
        
        # Sort by risk
        risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4, "unknown": 5}
        packages_list = sorted(
            packages_dict.values(),
            key=lambda p: (risk_order.get(p.overall_risk, 5), -p.total_vulnerabilities)
        )
        
        logger.info(f"Created summaries for {len(packages_list)} packages")
        return packages_list
    
    def _calculate_summary(
        self,
        vulnerabilities: List[ConsolidatedVulnerability],
        packages: List[PackageSummary]
    ) -> Dict[str, Any]:
        """Calculate overall summary statistics"""
        critical = sum(1 for v in vulnerabilities if v.severity == "critical")
        high = sum(1 for v in vulnerabilities if v.severity == "high")
        medium = sum(1 for v in vulnerabilities if v.severity == "medium")
        low = sum(1 for v in vulnerabilities if v.severity == "low")
        
        return {
            "total_packages": len(packages),
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": critical,
            "high_vulnerabilities": high,
            "medium_vulnerabilities": medium,
            "low_vulnerabilities": low,
            "packages_with_issues": sum(1 for p in packages if p.total_vulnerabilities > 0),
            "packages_safe": sum(1 for p in packages if p.total_vulnerabilities == 0),
            "overall_risk": self._determine_overall_risk(critical, high, medium, low)
        }
    
    def _generate_recommendations(
        self,
        vulnerabilities: List[ConsolidatedVulnerability],
        packages: List[PackageSummary]
    ) -> List[Dict[str, str]]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.severity == "critical"]
        if critical_vulns:
            recommendations.append({
                "priority": "critical",
                "action": f"Fix {len(critical_vulns)} critical vulnerabilities immediately",
                "details": f"Affected packages: {', '.join(set(v.package_name for v in critical_vulns[:5]))}",
                "impact": "Critical security risk - immediate action required"
            })
        
        # High vulnerabilities
        high_vulns = [v for v in vulnerabilities if v.severity == "high"]
        if high_vulns:
            recommendations.append({
                "priority": "high",
                "action": f"Address {len(high_vulns)} high-severity vulnerabilities",
                "details": f"Affected packages: {', '.join(set(v.package_name for v in high_vulns[:5]))}",
                "impact": "High security risk - address within 24-48 hours"
            })
        
        # Packages with fixes available
        fixable = [v for v in vulnerabilities if v.fixed_versions and v.is_current_version_affected]
        if fixable:
            recommendations.append({
                "priority": "medium",
                "action": f"Update {len(fixable)} packages with available fixes",
                "details": f"Packages: {', '.join(set(v.package_name for v in fixable[:5]))}",
                "impact": "Security fixes available - update recommended"
            })
        
        # Low reputation packages
        low_rep = [p for p in packages if p.reputation_score and p.reputation_score < 0.5]
        if low_rep:
            recommendations.append({
                "priority": "medium",
                "action": f"Review {len(low_rep)} packages with low reputation",
                "details": f"Packages: {', '.join(p.package_name for p in low_rep[:5])}",
                "impact": "Supply chain risk - verify package legitimacy"
            })
        
        return recommendations
    
    def _create_metadata(self, context: SafeSharedContext) -> Dict[str, Any]:
        """Create analysis metadata"""
        return {
            "analysis_id": f"analysis_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ecosystem": context.ecosystem,
            "input_mode": context.input_mode,
            "project_path": context.project_path if context.project_path else "not_available",
            "agents_executed": list(context.agent_results.keys()),
            "agents_successful": [
                name for name, result in context.agent_results.items()
                if result.success
            ]
        }
    
    def _create_analysis_details(self, context: SafeSharedContext) -> Dict[str, Any]:
        """Create detailed analysis information"""
        details = {}
        
        for agent_name, result in context.agent_results.items():
            details[agent_name] = {
                "success": result.success,
                "duration_seconds": result.duration_seconds,
                "confidence": result.confidence,
                "status": result.status,
                "error": result.error if not result.success else None
            }
        
        return details
    
    def _determine_status(self, vuln: SafeDict) -> str:
        """Determine vulnerability status"""
        if vuln.safe_list("fixed_versions"):
            if vuln.get("is_current_version_affected", True):
                return "active"
            else:
                return "fixed"
        return "active"
    
    def _generate_vuln_recommendation(self, vuln: SafeDict, pkg_name: str) -> str:
        """Generate recommendation for vulnerability"""
        fixed_versions = vuln.safe_list("fixed_versions", [])
        
        if fixed_versions:
            return f"Update {pkg_name} to version {fixed_versions[0]} or higher"
        else:
            return f"Review {pkg_name} for security issues - no fix available yet"
    
    def _calculate_overall_risk(self, summary: PackageSummary) -> str:
        """Calculate overall risk for package"""
        if summary.critical_count > 0:
            return "critical"
        elif summary.high_count > 0:
            return "high"
        elif summary.medium_count > 0:
            return "medium"
        elif summary.low_count > 0:
            return "low"
        elif summary.total_vulnerabilities == 0:
            return "safe"
        else:
            return "unknown"
    
    def _generate_package_recommendation(self, summary: PackageSummary) -> str:
        """Generate recommendation for package"""
        if summary.critical_count > 0:
            return f"CRITICAL: Update immediately - {summary.critical_count} critical vulnerabilities"
        elif summary.high_count > 0:
            return f"HIGH PRIORITY: Update within 24-48 hours - {summary.high_count} high-severity vulnerabilities"
        elif summary.medium_count > 0:
            return f"MEDIUM: Review and update - {summary.medium_count} medium-severity vulnerabilities"
        elif summary.low_count > 0:
            return f"LOW: Consider updating - {summary.low_count} low-severity vulnerabilities"
        elif summary.reputation_score and summary.reputation_score < 0.5:
            return "Review package reputation and consider alternatives"
        else:
            return "No immediate action required"
    
    def _determine_overall_risk(self, critical: int, high: int, medium: int, low: int) -> str:
        """Determine overall project risk"""
        if critical > 0:
            return "critical"
        elif high > 0:
            return "high"
        elif medium > 0:
            return "medium"
        elif low > 0:
            return "low"
        else:
            return "safe"


# Convenience function
def format_clean_report(
    context: SafeSharedContext,
    rule_based_findings: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format analysis results into clean report.
    
    Args:
        context: Shared context with agent results
        rule_based_findings: Optional rule-based findings
    
    Returns:
        Clean, consolidated report
    """
    formatter = CleanOutputFormatter()
    return formatter.format_analysis_results(context, rule_based_findings)
