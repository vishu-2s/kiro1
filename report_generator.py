"""
Comprehensive reporting system for Multi-Agent Security Analysis System.

This module provides functions for:
- HTML report generation with executive summaries
- Risk assessment and attack classification
- Remediation planning and timeline generation
- Stakeholder communication guidance
- Dual output format (JSON and HTML)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

from analyze_supply_chain import AnalysisResult, AnalysisMetadata, AnalysisSummary
from config import config

logger = logging.getLogger(__name__)

@dataclass
class RiskAssessment:
    """Risk assessment for security analysis."""
    overall_risk_level: str  # "critical", "high", "medium", "low", "none"
    risk_score: float  # 0.0 to 10.0
    attack_vectors: List[str]
    business_impact: str
    likelihood: str
    risk_factors: List[str]
    mitigation_priority: str

@dataclass
class AttackClassification:
    """Classification of detected attacks."""
    attack_types: List[str]
    attack_sophistication: str  # "low", "medium", "high", "advanced"
    attack_stage: str  # "reconnaissance", "initial_access", "execution", "persistence", "impact"
    indicators_of_compromise: List[str]
    attribution_confidence: str  # "low", "medium", "high"

@dataclass
class RemediationPlan:
    """Remediation plan for security findings."""
    immediate_actions: List[str]
    short_term_actions: List[str]  # 1-7 days
    medium_term_actions: List[str]  # 1-4 weeks
    long_term_actions: List[str]  # 1+ months
    containment_steps: List[str]
    recovery_steps: List[str]
    prevention_measures: List[str]

@dataclass
class Timeline:
    """Timeline for incident response and remediation."""
    incident_start: str
    detection_time: str
    analysis_completion: str
    estimated_containment: str
    estimated_recovery: str
    milestones: List[Dict[str, str]]

@dataclass
class StakeholderGuidance:
    """Guidance for stakeholder communication."""
    executive_summary: str
    technical_summary: str
    business_impact_statement: str
    communication_priority: str  # "immediate", "urgent", "normal", "low"
    recommended_recipients: List[str]
    key_messages: List[str]
    next_steps: List[str]

@dataclass
class ComprehensiveReport:
    """Complete comprehensive security report."""
    analysis_result: AnalysisResult
    risk_assessment: RiskAssessment
    attack_classification: AttackClassification
    remediation_plan: RemediationPlan
    timeline: Timeline
    stakeholder_guidance: StakeholderGuidance
    report_metadata: Dict[str, Any]

class SecurityReportGenerator:
    """Generator for comprehensive security reports."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.report_id = self._generate_report_id()
        logger.info(f"Initialized SecurityReportGenerator with ID: {self.report_id}")
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID."""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"report_{timestamp}_{unique_suffix}"
    
    def generate_comprehensive_report(self, analysis_result: AnalysisResult) -> ComprehensiveReport:
        """
        Generate comprehensive security report from analysis results.
        
        Args:
            analysis_result: Analysis results to generate report from
            
        Returns:
            Complete comprehensive report
        """
        logger.info(f"Generating comprehensive report for analysis {analysis_result.metadata.analysis_id}")
        
        # Generate risk assessment
        risk_assessment = self._assess_risk(analysis_result)
        
        # Classify attacks
        attack_classification = self._classify_attacks(analysis_result)
        
        # Create remediation plan
        remediation_plan = self._create_remediation_plan(analysis_result, risk_assessment)
        
        # Generate timeline
        timeline = self._generate_timeline(analysis_result, remediation_plan)
        
        # Create stakeholder guidance
        stakeholder_guidance = self._create_stakeholder_guidance(
            analysis_result, risk_assessment, attack_classification
        )
        
        # Create report metadata
        report_metadata = {
            "report_id": self.report_id,
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0.0",
            "analysis_id": analysis_result.metadata.analysis_id,
            "report_type": "comprehensive_security_analysis"
        }
        
        return ComprehensiveReport(
            analysis_result=analysis_result,
            risk_assessment=risk_assessment,
            attack_classification=attack_classification,
            remediation_plan=remediation_plan,
            timeline=timeline,
            stakeholder_guidance=stakeholder_guidance,
            report_metadata=report_metadata
        )
    
    def _assess_risk(self, analysis_result: AnalysisResult) -> RiskAssessment:
        """Assess overall risk level and factors."""
        summary = analysis_result.summary
        findings = analysis_result.security_findings
        
        # Calculate risk score based on findings
        risk_score = 0.0
        
        # Weight by severity
        risk_score += summary.critical_findings * 4.0
        risk_score += summary.high_findings * 2.5
        risk_score += summary.medium_findings * 1.5
        risk_score += summary.low_findings * 0.5
        
        # Cap at 10.0
        risk_score = min(risk_score, 10.0)
        
        # Determine overall risk level
        if risk_score >= 8.0 or summary.critical_findings > 0:
            overall_risk_level = "critical"
        elif risk_score >= 6.0 or summary.high_findings > 2:
            overall_risk_level = "high"
        elif risk_score >= 3.0 or summary.medium_findings > 5:
            overall_risk_level = "medium"
        elif risk_score > 0:
            overall_risk_level = "low"
        else:
            overall_risk_level = "none"
        
        # Identify attack vectors
        attack_vectors = []
        finding_types = summary.finding_types
        
        if finding_types.get("malicious_package", 0) > 0:
            attack_vectors.append("Supply Chain Compromise")
        if finding_types.get("vulnerability", 0) > 0:
            attack_vectors.append("Known Vulnerability Exploitation")
        if finding_types.get("typosquat", 0) > 0:
            attack_vectors.append("Typosquatting Attack")
        if finding_types.get("suspicious_activity", 0) > 0:
            attack_vectors.append("Suspicious Code Execution")
        
        # Assess business impact
        if overall_risk_level in ["critical", "high"]:
            business_impact = "High - Potential for significant business disruption, data breach, or financial loss"
        elif overall_risk_level == "medium":
            business_impact = "Medium - Moderate impact on operations or security posture"
        elif overall_risk_level == "low":
            business_impact = "Low - Minimal impact on business operations"
        else:
            business_impact = "None - No significant business impact identified"
        
        # Assess likelihood
        confidence_dist = summary.confidence_distribution
        high_confidence_findings = confidence_dist.get("high", 0)
        
        if high_confidence_findings > 0 and overall_risk_level in ["critical", "high"]:
            likelihood = "High - Active threats detected with high confidence"
        elif summary.total_findings > 0:
            likelihood = "Medium - Potential threats identified requiring investigation"
        else:
            likelihood = "Low - No significant threats detected"
        
        # Identify risk factors
        risk_factors = []
        if summary.total_packages > 100:
            risk_factors.append("Large dependency footprint increases attack surface")
        if len(summary.ecosystems_analyzed) > 3:
            risk_factors.append("Multiple ecosystems increase complexity and risk")
        if summary.critical_findings > 0:
            risk_factors.append("Critical vulnerabilities present immediate risk")
        if finding_types.get("malicious_package", 0) > 0:
            risk_factors.append("Malicious packages indicate active compromise")
        
        # Determine mitigation priority
        if overall_risk_level == "critical":
            mitigation_priority = "Immediate - Address within hours"
        elif overall_risk_level == "high":
            mitigation_priority = "Urgent - Address within 24-48 hours"
        elif overall_risk_level == "medium":
            mitigation_priority = "High - Address within 1 week"
        elif overall_risk_level == "low":
            mitigation_priority = "Medium - Address within 1 month"
        else:
            mitigation_priority = "Low - Monitor and maintain current security posture"
        
        return RiskAssessment(
            overall_risk_level=overall_risk_level,
            risk_score=risk_score,
            attack_vectors=attack_vectors,
            business_impact=business_impact,
            likelihood=likelihood,
            risk_factors=risk_factors,
            mitigation_priority=mitigation_priority
        )
    
    def _classify_attacks(self, analysis_result: AnalysisResult) -> AttackClassification:
        """Classify detected attacks and threats."""
        findings = analysis_result.security_findings
        finding_types = analysis_result.summary.finding_types
        
        # Identify attack types
        attack_types = []
        if finding_types.get("malicious_package", 0) > 0:
            attack_types.append("Supply Chain Attack")
        if finding_types.get("typosquat", 0) > 0:
            attack_types.append("Typosquatting")
        if finding_types.get("vulnerability", 0) > 0:
            attack_types.append("Vulnerability Exploitation")
        
        # Check for specific attack patterns in findings
        for finding in findings:
            evidence = finding.get("evidence", [])
            evidence_text = " ".join(evidence).lower()
            
            if any(keyword in evidence_text for keyword in ["backdoor", "trojan", "malware"]):
                if "Backdoor/Trojan" not in attack_types:
                    attack_types.append("Backdoor/Trojan")
            
            if any(keyword in evidence_text for keyword in ["cryptocurrency", "mining", "bitcoin"]):
                if "Cryptojacking" not in attack_types:
                    attack_types.append("Cryptojacking")
            
            if any(keyword in evidence_text for keyword in ["credential", "password", "token"]):
                if "Credential Theft" not in attack_types:
                    attack_types.append("Credential Theft")
        
        # Assess attack sophistication
        critical_count = analysis_result.summary.critical_findings
        high_confidence_count = analysis_result.summary.confidence_distribution.get("high", 0)
        
        if critical_count > 2 and high_confidence_count > 3:
            attack_sophistication = "advanced"
        elif critical_count > 0 or high_confidence_count > 2:
            attack_sophistication = "high"
        elif analysis_result.summary.high_findings > 0:
            attack_sophistication = "medium"
        else:
            attack_sophistication = "low"
        
        # Determine attack stage
        if finding_types.get("malicious_package", 0) > 0:
            attack_stage = "execution"  # Malicious code is already executing
        elif finding_types.get("vulnerability", 0) > 0:
            attack_stage = "initial_access"  # Vulnerabilities provide access
        elif finding_types.get("typosquat", 0) > 0:
            attack_stage = "reconnaissance"  # Typosquats are often reconnaissance
        else:
            attack_stage = "reconnaissance"
        
        # Collect indicators of compromise
        indicators_of_compromise = []
        for finding in findings:
            if finding.get("severity") in ["critical", "high"]:
                package = finding.get("package", "unknown")
                finding_type = finding.get("finding_type", "unknown")
                indicators_of_compromise.append(f"{finding_type}: {package}")
        
        # Assess attribution confidence
        if high_confidence_count > 2 and critical_count > 0:
            attribution_confidence = "high"
        elif analysis_result.summary.total_findings > 0:
            attribution_confidence = "medium"
        else:
            attribution_confidence = "low"
        
        return AttackClassification(
            attack_types=attack_types,
            attack_sophistication=attack_sophistication,
            attack_stage=attack_stage,
            indicators_of_compromise=indicators_of_compromise,
            attribution_confidence=attribution_confidence
        )
    
    def _create_remediation_plan(self, analysis_result: AnalysisResult, 
                               risk_assessment: RiskAssessment) -> RemediationPlan:
        """Create detailed remediation plan."""
        findings = analysis_result.security_findings
        summary = analysis_result.summary
        
        immediate_actions = []
        short_term_actions = []
        medium_term_actions = []
        long_term_actions = []
        containment_steps = []
        recovery_steps = []
        prevention_measures = []
        
        # Immediate actions based on risk level
        if risk_assessment.overall_risk_level == "critical":
            immediate_actions.extend([
                "Isolate affected systems from network if possible",
                "Notify security team and incident response personnel",
                "Begin forensic preservation of evidence",
                "Activate incident response procedures"
            ])
        
        # Actions based on finding types
        malicious_count = summary.finding_types.get("malicious_package", 0)
        if malicious_count > 0:
            immediate_actions.append(f"Remove {malicious_count} identified malicious packages immediately")
            containment_steps.extend([
                "Scan all systems for signs of compromise",
                "Review network logs for suspicious activity",
                "Check for persistence mechanisms"
            ])
        
        vuln_count = summary.finding_types.get("vulnerability", 0)
        if vuln_count > 0:
            short_term_actions.append(f"Update {vuln_count} packages with known vulnerabilities")
            medium_term_actions.append("Implement automated vulnerability scanning")
        
        typosquat_count = summary.finding_types.get("typosquat", 0)
        if typosquat_count > 0:
            immediate_actions.append(f"Review {typosquat_count} potential typosquat packages")
            prevention_measures.append("Implement package name verification processes")
        
        # General remediation actions
        if summary.total_findings > 0:
            short_term_actions.extend([
                "Conduct thorough security audit of all dependencies",
                "Review and update dependency management policies",
                "Implement additional monitoring for suspicious activities"
            ])
            
            medium_term_actions.extend([
                "Establish regular security scanning schedule",
                "Train development team on secure dependency management",
                "Implement Software Bill of Materials (SBOM) tracking"
            ])
            
            long_term_actions.extend([
                "Develop comprehensive supply chain security program",
                "Establish vendor security assessment processes",
                "Implement zero-trust architecture principles"
            ])
        
        # Recovery steps
        recovery_steps.extend([
            "Verify system integrity after remediation",
            "Restore from clean backups if necessary",
            "Conduct post-incident review and lessons learned",
            "Update security documentation and procedures"
        ])
        
        # Prevention measures
        prevention_measures.extend([
            "Implement dependency scanning in CI/CD pipeline",
            "Use package lock files to ensure reproducible builds",
            "Establish security policies for dependency approval",
            "Regular security training for development teams",
            "Implement network segmentation and monitoring"
        ])
        
        return RemediationPlan(
            immediate_actions=immediate_actions,
            short_term_actions=short_term_actions,
            medium_term_actions=medium_term_actions,
            long_term_actions=long_term_actions,
            containment_steps=containment_steps,
            recovery_steps=recovery_steps,
            prevention_measures=prevention_measures
        )
    
    def _generate_timeline(self, analysis_result: AnalysisResult, 
                         remediation_plan: RemediationPlan) -> Timeline:
        """Generate incident response and remediation timeline."""
        analysis_start = datetime.fromisoformat(analysis_result.metadata.start_time)
        analysis_end = datetime.fromisoformat(analysis_result.metadata.end_time)
        
        # Estimate timeline based on risk level and findings
        risk_level = self._assess_risk(analysis_result).overall_risk_level
        
        if risk_level == "critical":
            containment_hours = 4
            recovery_days = 3
        elif risk_level == "high":
            containment_hours = 24
            recovery_days = 7
        elif risk_level == "medium":
            containment_hours = 72
            recovery_days = 14
        else:
            containment_hours = 168  # 1 week
            recovery_days = 30
        
        estimated_containment = (analysis_end + timedelta(hours=containment_hours)).isoformat()
        estimated_recovery = (analysis_end + timedelta(days=recovery_days)).isoformat()
        
        # Generate milestones
        milestones = [
            {
                "milestone": "Analysis Started",
                "timestamp": analysis_start.isoformat(),
                "status": "completed"
            },
            {
                "milestone": "Analysis Completed",
                "timestamp": analysis_end.isoformat(),
                "status": "completed"
            },
            {
                "milestone": "Immediate Actions",
                "timestamp": (analysis_end + timedelta(hours=1)).isoformat(),
                "status": "pending"
            },
            {
                "milestone": "Containment Complete",
                "timestamp": estimated_containment,
                "status": "pending"
            },
            {
                "milestone": "Recovery Complete",
                "timestamp": estimated_recovery,
                "status": "pending"
            }
        ]
        
        return Timeline(
            incident_start=analysis_start.isoformat(),
            detection_time=analysis_start.isoformat(),
            analysis_completion=analysis_end.isoformat(),
            estimated_containment=estimated_containment,
            estimated_recovery=estimated_recovery,
            milestones=milestones
        )
    
    def _create_stakeholder_guidance(self, analysis_result: AnalysisResult,
                                   risk_assessment: RiskAssessment,
                                   attack_classification: AttackClassification) -> StakeholderGuidance:
        """Create stakeholder communication guidance."""
        summary = analysis_result.summary
        
        # Executive summary
        executive_summary = f"""
        Security analysis of {analysis_result.metadata.target} has been completed. 
        {summary.total_findings} security findings were identified across {summary.total_packages} packages.
        Overall risk level: {risk_assessment.overall_risk_level.upper()}.
        
        Key findings:
        - {summary.critical_findings} critical severity issues
        - {summary.high_findings} high severity issues  
        - {summary.medium_findings} medium severity issues
        
        Immediate action is {'required' if risk_assessment.overall_risk_level in ['critical', 'high'] else 'recommended'}.
        """.strip()
        
        # Technical summary
        technical_summary = f"""
        Analysis Details:
        - Target: {analysis_result.metadata.target}
        - Analysis Type: {analysis_result.metadata.analysis_type}
        - Packages Analyzed: {summary.total_packages}
        - Ecosystems: {', '.join(summary.ecosystems_analyzed)}
        - Attack Types: {', '.join(attack_classification.attack_types) if attack_classification.attack_types else 'None detected'}
        - Risk Score: {risk_assessment.risk_score:.1f}/10.0
        """.strip()
        
        # Business impact statement
        business_impact_statement = risk_assessment.business_impact
        
        # Communication priority
        if risk_assessment.overall_risk_level == "critical":
            communication_priority = "immediate"
        elif risk_assessment.overall_risk_level == "high":
            communication_priority = "urgent"
        elif risk_assessment.overall_risk_level == "medium":
            communication_priority = "normal"
        else:
            communication_priority = "low"
        
        # Recommended recipients
        recommended_recipients = ["Security Team", "Development Team"]
        if risk_assessment.overall_risk_level in ["critical", "high"]:
            recommended_recipients.extend(["Management", "IT Operations", "Legal/Compliance"])
        
        # Key messages
        key_messages = [
            f"Security analysis identified {summary.total_findings} findings requiring attention",
            f"Risk level assessed as {risk_assessment.overall_risk_level}",
            f"Remediation priority: {risk_assessment.mitigation_priority}"
        ]
        
        if attack_classification.attack_types:
            key_messages.append(f"Attack types detected: {', '.join(attack_classification.attack_types)}")
        
        # Next steps
        next_steps = [
            "Review detailed findings and remediation plan",
            "Assign responsible parties for remediation actions",
            "Establish timeline for addressing critical and high-priority issues"
        ]
        
        if risk_assessment.overall_risk_level in ["critical", "high"]:
            next_steps.insert(0, "Initiate incident response procedures")
        
        return StakeholderGuidance(
            executive_summary=executive_summary,
            technical_summary=technical_summary,
            business_impact_statement=business_impact_statement,
            communication_priority=communication_priority,
            recommended_recipients=recommended_recipients,
            key_messages=key_messages,
            next_steps=next_steps
        )
    
    def save_json_report(self, report: ComprehensiveReport, output_path: Optional[str] = None) -> str:
        """
        Save comprehensive report as JSON file.
        
        Args:
            report: Comprehensive report to save
            output_path: Optional output file path
            
        Returns:
            Path to saved JSON file
        """
        if output_path is None:
            output_dir = Path(config.OUTPUT_DIRECTORY)
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_report_{report.report_metadata['report_id']}_{timestamp}.json"
            output_path = output_dir / filename
        
        # Convert report to dictionary
        report_dict = asdict(report)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"JSON report saved to {output_path}")
        return str(output_path)
    
    def save_html_report(self, report: ComprehensiveReport, output_path: Optional[str] = None) -> str:
        """
        Save comprehensive report as HTML file.
        
        Args:
            report: Comprehensive report to save
            output_path: Optional output file path
            
        Returns:
            Path to saved HTML file
        """
        if output_path is None:
            output_dir = Path(config.OUTPUT_DIRECTORY)
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_report_{report.report_metadata['report_id']}_{timestamp}.html"
            output_path = output_dir / filename
        
        # Generate HTML content
        html_content = self._generate_html_report(report)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to {output_path}")
        return str(output_path)
    
    def _generate_html_report(self, report: ComprehensiveReport) -> str:
        """Generate HTML content for comprehensive report."""
        analysis = report.analysis_result
        risk = report.risk_assessment
        attack = report.attack_classification
        remediation = report.remediation_plan
        timeline = report.timeline
        stakeholder = report.stakeholder_guidance
        
        # Generate severity color mapping
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14", 
            "medium": "#ffc107",
            "low": "#28a745"
        }
        
        risk_color = severity_colors.get(risk.overall_risk_level, "#6c757d")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Analysis Report - {analysis.metadata.analysis_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #0a0a0f;
            color: #E5E5E5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #1a1520;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5), 0 0 30px rgba(57, 255, 20, 0.15);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
            border-bottom: 1px solid rgba(57, 255, 20, 0.2);
            padding-bottom: 30px;
            background: #15111a;
            padding: 20px;
            border-radius: 8px;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #FFFFFF;
            border-left: 4px solid #39FF14;
            padding-left: 15px;
            margin-bottom: 20px;
            text-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
        }}
        .section p, .section span, .section div {{
            color: #FFFFFF;
        }}
        .section strong {{
            color: #39FF14;
            font-weight: 700;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            background-color: {risk_color};
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #1a1520;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #39FF14;
            border: 1px solid rgba(57, 255, 20, 0.25);
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #FFFFFF;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }}
        .stat-label {{
            color: #CCCCCC;
            margin-top: 5px;
            font-weight: 600;
        }}
        .findings-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .findings-table th,
        .findings-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .findings-table th {{
            background-color: #0a0a0f;
            font-weight: 600;
            color: #39FF14;
        }}
        .severity-critical {{ color: #FF7518; font-weight: bold; text-shadow: 0 0 10px rgba(255, 117, 24, 0.5); }}
        .severity-high {{ color: #FFFFFF; font-weight: bold; }}
        .severity-medium {{ color: #ffc107; font-weight: bold; }}
        .severity-low {{ color: #39FF14; font-weight: bold; }}
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #667eea;
        }}
        .timeline-item {{
            position: relative;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: #15111a;
            border-radius: 8px;
            border: 1px solid rgba(255, 117, 24, 0.3);
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -25px;
            top: 20px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #667eea;
        }}
        .action-list {{
            list-style: none;
            padding: 0;
        }}
        .action-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .action-list li:last-child {{
            border-bottom: none;
        }}
        .priority-immediate {{ border-left: 4px solid #dc3545; padding-left: 15px; }}
        .priority-urgent {{ border-left: 4px solid #fd7e14; padding-left: 15px; }}
        .priority-normal {{ border-left: 4px solid #ffc107; padding-left: 15px; }}
        .priority-low {{ border-left: 4px solid #28a745; padding-left: 15px; }}
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .alert-danger {{
            background-color: rgba(255, 117, 24, 0.15);
            border-color: #FF7518;
            color: #FF7518;
        }}
        .alert-warning {{
            background-color: rgba(255, 193, 7, 0.15);
            border-color: #ffc107;
            color: #ffc107;
        }}
        .alert-info {{
            background-color: rgba(57, 255, 20, 0.15);
            border-color: #39FF14;
            color: #39FF14;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        @media print {{
            body {{ background: #1a1520; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Security Analysis Report</h1>
            <div class="subtitle">
                Analysis ID: {analysis.metadata.analysis_id}<br>
                Generated: {report.report_metadata['generated_at'][:19].replace('T', ' ')}
            </div>
        </div>
        
        <div class="content">
            <!-- Executive Summary -->
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="alert {'alert-danger' if risk.overall_risk_level == 'critical' else 'alert-warning' if risk.overall_risk_level == 'high' else 'alert-info'}">
                    <strong>Risk Level: <span class="risk-badge">{risk.overall_risk_level}</span></strong>
                    <p>{stakeholder.executive_summary}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{analysis.summary.total_findings}</div>
                        <div class="stat-label">Total Findings</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis.summary.total_packages}</div>
                        <div class="stat-label">Packages Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{risk.risk_score:.1f}/10</div>
                        <div class="stat-label">Risk Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(analysis.summary.ecosystems_analyzed)}</div>
                        <div class="stat-label">Ecosystems</div>
                    </div>
                </div>
            </div>
            
            <!-- Risk Assessment -->
            <div class="section">
                <h2>Risk Assessment</h2>
                <p><strong>Business Impact:</strong> {risk.business_impact}</p>
                <p><strong>Likelihood:</strong> {risk.likelihood}</p>
                <p><strong>Mitigation Priority:</strong> {risk.mitigation_priority}</p>
                
                <h3>Attack Vectors</h3>
                <ul>
                    {''.join(f'<li>{vector}</li>' for vector in risk.attack_vectors)}
                </ul>
                
                <h3>Risk Factors</h3>
                <ul>
                    {''.join(f'<li>{factor}</li>' for factor in risk.risk_factors)}
                </ul>
            </div>
            
            <!-- Attack Classification -->
            <div class="section">
                <h2>Attack Classification</h2>
                <p><strong>Attack Types:</strong> {', '.join(attack.attack_types) if attack.attack_types else 'None detected'}</p>
                <p><strong>Sophistication Level:</strong> {attack.attack_sophistication.title()}</p>
                <p><strong>Attack Stage:</strong> {attack.attack_stage.replace('_', ' ').title()}</p>
                <p><strong>Attribution Confidence:</strong> {attack.attribution_confidence.title()}</p>
                
                {f'''
                <h3>Indicators of Compromise</h3>
                <ul>
                    {''.join(f'<li>{ioc}</li>' for ioc in attack.indicators_of_compromise)}
                </ul>
                ''' if attack.indicators_of_compromise else ''}
            </div>
            
            <!-- Detailed Findings -->
            <div class="section">
                <h2>Detailed Findings</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number severity-critical">{analysis.summary.critical_findings}</div>
                        <div class="stat-label">Critical</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number severity-high">{analysis.summary.high_findings}</div>
                        <div class="stat-label">High</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number severity-medium">{analysis.summary.medium_findings}</div>
                        <div class="stat-label">Medium</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number severity-low">{analysis.summary.low_findings}</div>
                        <div class="stat-label">Low</div>
                    </div>
                </div>
                
                <table class="findings-table">
                    <thead>
                        <tr>
                            <th>Package</th>
                            <th>Version</th>
                            <th>Finding Type</th>
                            <th>Severity</th>
                            <th>Confidence</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(self._generate_finding_row(finding) for finding in analysis.security_findings[:20])}
                    </tbody>
                </table>
                {f'<p><em>Showing first 20 of {len(analysis.security_findings)} findings. See JSON report for complete details.</em></p>' if len(analysis.security_findings) > 20 else ''}
            </div>
            
            <!-- Remediation Plan -->
            <div class="section">
                <h2>Remediation Plan</h2>
                
                <h3>Immediate Actions</h3>
                <div class="priority-immediate">
                    <ul class="action-list">
                        {''.join(f'<li>{action}</li>' for action in remediation.immediate_actions)}
                    </ul>
                </div>
                
                <h3>Short-term Actions (1-7 days)</h3>
                <div class="priority-urgent">
                    <ul class="action-list">
                        {''.join(f'<li>{action}</li>' for action in remediation.short_term_actions)}
                    </ul>
                </div>
                
                <h3>Medium-term Actions (1-4 weeks)</h3>
                <div class="priority-normal">
                    <ul class="action-list">
                        {''.join(f'<li>{action}</li>' for action in remediation.medium_term_actions)}
                    </ul>
                </div>
                
                <h3>Long-term Actions (1+ months)</h3>
                <div class="priority-low">
                    <ul class="action-list">
                        {''.join(f'<li>{action}</li>' for action in remediation.long_term_actions)}
                    </ul>
                </div>
                
                <h3>Containment Steps</h3>
                <ul class="action-list">
                    {''.join(f'<li>{step}</li>' for step in remediation.containment_steps)}
                </ul>
                
                <h3>Prevention Measures</h3>
                <ul class="action-list">
                    {''.join(f'<li>{measure}</li>' for measure in remediation.prevention_measures)}
                </ul>
            </div>
            
            <!-- Timeline -->
            <div class="section">
                <h2>Timeline</h2>
                <div class="timeline">
                    {''.join(self._generate_timeline_item(milestone) for milestone in timeline.milestones)}
                </div>
            </div>
            
            <!-- Stakeholder Communication -->
            <div class="section">
                <h2>Stakeholder Communication</h2>
                <p><strong>Communication Priority:</strong> {stakeholder.communication_priority.title()}</p>
                <p><strong>Recommended Recipients:</strong> {', '.join(stakeholder.recommended_recipients)}</p>
                
                <h3>Key Messages</h3>
                <ul>
                    {''.join(f'<li>{message}</li>' for message in stakeholder.key_messages)}
                </ul>
                
                <h3>Next Steps</h3>
                <ul>
                    {''.join(f'<li>{step}</li>' for step in stakeholder.next_steps)}
                </ul>
                
                <h3>Technical Summary</h3>
                <div class="alert alert-info">
                    <pre>{stakeholder.technical_summary}</pre>
                </div>
            </div>
            
            <!-- Analysis Details -->
            <div class="section">
                <h2>Analysis Details</h2>
                <p><strong>Target:</strong> {analysis.metadata.target}</p>
                <p><strong>Analysis Type:</strong> {analysis.metadata.analysis_type.replace('_', ' ').title()}</p>
                <p><strong>Start Time:</strong> {analysis.metadata.start_time[:19].replace('T', ' ')}</p>
                <p><strong>End Time:</strong> {analysis.metadata.end_time[:19].replace('T', ' ')}</p>
                <p><strong>Duration:</strong> {self._calculate_duration(analysis.metadata.start_time, analysis.metadata.end_time)}</p>
                <p><strong>Ecosystems Analyzed:</strong> {', '.join(analysis.summary.ecosystems_analyzed)}</p>
                <p><strong>OSV API Enabled:</strong> {'Yes' if analysis.metadata.osv_enabled else 'No'}</p>
                <p><strong>Visual Analysis:</strong> {'Yes' if analysis.metadata.visual_analysis_enabled else 'No'}</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Multi-Agent Security Analysis System v1.0.0</p>
            <p>Report ID: {report.report_metadata['report_id']}</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return html_content
    
    def _generate_finding_row(self, finding: Dict[str, Any]) -> str:
        """Generate HTML table row for a finding."""
        severity = finding.get("severity", "unknown")
        severity_class = f"severity-{severity}"
        
        # Truncate evidence for display
        evidence = finding.get("evidence", [])
        evidence_text = "; ".join(evidence[:2])
        if len(evidence) > 2:
            evidence_text += f" (and {len(evidence) - 2} more)"
        
        return f"""
        <tr>
            <td>{finding.get('package', 'unknown')}</td>
            <td>{finding.get('version', 'unknown')}</td>
            <td>{finding.get('finding_type', 'unknown').replace('_', ' ').title()}</td>
            <td class="{severity_class}">{severity.title()}</td>
            <td>{finding.get('confidence', 0):.2f}</td>
            <td>{evidence_text}</td>
        </tr>
        """
    
    def _generate_timeline_item(self, milestone: Dict[str, str]) -> str:
        """Generate HTML timeline item."""
        status = milestone.get("status", "pending")
        status_icon = "✓" if status == "completed" else "○"
        
        return f"""
        <div class="timeline-item">
            <strong>{status_icon} {milestone.get('milestone', 'Unknown')}</strong><br>
            <small>{milestone.get('timestamp', '')[:19].replace('T', ' ')}</small>
        </div>
        """
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate and format duration between timestamps."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except Exception:
            return "Unknown"
    
    def generate_dual_format_report(self, analysis_result: AnalysisResult, 
                                  output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate both JSON and HTML reports.
        
        Args:
            analysis_result: Analysis results to generate reports from
            output_dir: Optional output directory
            
        Returns:
            Tuple of (json_path, html_path)
        """
        # Generate comprehensive report
        comprehensive_report = self.generate_comprehensive_report(analysis_result)
        
        # Set output directory
        if output_dir is None:
            output_dir = config.OUTPUT_DIRECTORY
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"security_report_{comprehensive_report.report_metadata['report_id']}_{timestamp}"
        
        # Save JSON report
        json_path = output_path / f"{base_filename}.json"
        json_file_path = self.save_json_report(comprehensive_report, str(json_path))
        
        # Save HTML report
        html_path = output_path / f"{base_filename}.html"
        html_file_path = self.save_html_report(comprehensive_report, str(html_path))
        
        logger.info(f"Dual format reports generated: JSON={json_file_path}, HTML={html_file_path}")
        
        return json_file_path, html_file_path

def create_security_report(analysis_result: AnalysisResult, 
                         output_format: str = "both",
                         output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Create security report in specified format(s).
    
    Args:
        analysis_result: Analysis results to generate report from
        output_format: "json", "html", or "both"
        output_dir: Optional output directory
        
    Returns:
        Dictionary with paths to generated reports
    """
    generator = SecurityReportGenerator()
    comprehensive_report = generator.generate_comprehensive_report(analysis_result)
    
    result_paths = {}
    
    if output_format in ["json", "both"]:
        json_path = generator.save_json_report(comprehensive_report, 
                                             None if output_dir is None else 
                                             str(Path(output_dir) / f"report_{generator.report_id}.json"))
        result_paths["json"] = json_path
    
    if output_format in ["html", "both"]:
        html_path = generator.save_html_report(comprehensive_report,
                                             None if output_dir is None else
                                             str(Path(output_dir) / f"report_{generator.report_id}.html"))
        result_paths["html"] = html_path
    
    return result_paths

def generate_executive_summary(analysis_result: AnalysisResult) -> str:
    """
    Generate executive summary for quick review.
    
    Args:
        analysis_result: Analysis results
        
    Returns:
        Executive summary text
    """
    generator = SecurityReportGenerator()
    risk_assessment = generator._assess_risk(analysis_result)
    attack_classification = generator._classify_attacks(analysis_result)
    stakeholder_guidance = generator._create_stakeholder_guidance(
        analysis_result, risk_assessment, attack_classification
    )
    
    return stakeholder_guidance.executive_summary