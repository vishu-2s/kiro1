"""
Output JSON Restructuring Module

Restructures the analysis output into 5 clear sections:
1. Rule-Based Analysis (github_rule_based) - OSV, malicious packages, typosquatting
2. Dependency Graph Analysis - Circular deps, version conflicts
3. Supply Chain Analysis - Maintainer changes, exfiltration, attack patterns
4. Code Analysis - Obfuscation, behavioral indicators
5. LLM-Based Risk Assessment & Recommendations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class OutputRestructurer:
    """Restructures analysis output into clean, organized JSON."""
    
    def restructure_output(
        self,
        raw_output: Dict[str, Any],
        input_mode: str = "local",
        ecosystem: str = "npm"
    ) -> Dict[str, Any]:
        """
        Restructure raw analysis output into 5 main sections.
        
        Args:
            raw_output: Raw analysis output from synthesis
            input_mode: 'github' or 'local'
            ecosystem: Package ecosystem
        
        Returns:
            Restructured JSON with 5 clear sections
        """
        metadata = raw_output.get("metadata", {})
        summary = raw_output.get("summary", {})
        security_findings = raw_output.get("security_findings", {})
        dependency_graph = raw_output.get("dependency_graph", {})
        recommendations = raw_output.get("recommendations", {})
        agent_insights = raw_output.get("agent_insights", {})
        
        # Extract agent-specific data
        supply_chain_data = raw_output.get("supply_chain_analysis", {})
        code_analysis_data = raw_output.get("code_analysis", {})
        
        # Build restructured output
        restructured = {
            "metadata": {
                "analysis_id": metadata.get("analysis_id", "unknown"),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "input_mode": input_mode,
                "ecosystem": ecosystem,
                "analysis_version": "2.0"
            },
            
            # Section 1: Rule-Based Analysis (SBOM tools, OSV API)
            "github_rule_based": self._build_rule_based_section(
                summary, security_findings, metadata
            ),
            
            # Section 2: Dependency Graph
            "dependency_graph": self._build_dependency_graph_section(
                dependency_graph, input_mode
            ),
            
            # Section 3: Supply Chain Analysis (Agent output - SEPARATE)
            "supply_chain_analysis": self._build_supply_chain_section(
                supply_chain_data, agent_insights
            ),
            
            # Section 4: Code Analysis (Agent output - SEPARATE)
            "code_analysis": self._build_code_analysis_section(
                code_analysis_data, agent_insights
            ),
            
            # Section 5: LLM-Based Assessment
            "llm_assessment": self._build_llm_assessment_section(
                agent_insights, recommendations, summary
            ),
            
            # Keep original sections for UI compatibility
            "summary": summary,
            "security_findings": security_findings,
            "recommendations": recommendations,
            "performance_metrics": raw_output.get("performance_metrics", {})
        }
        
        return restructured
    
    def _build_rule_based_section(
        self,
        summary: Dict[str, Any],
        security_findings: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Section 1: Rule-Based Analysis Results.
        
        This section contains results from:
        - OSV API vulnerability checks
        - Malicious package detection
        - Typosquatting detection
        - Pattern-based analysis
        """
        packages = security_findings.get("packages", [])
        
        # Calculate severity breakdown
        severity_breakdown = {
            "critical": summary.get("critical_findings", 0),
            "high": summary.get("high_findings", 0),
            "medium": summary.get("medium_findings", 0),
            "low": summary.get("low_findings", 0)
        }
        
        # Extract finding types
        finding_types = {}
        for pkg in packages:
            for finding in pkg.get("findings", []):
                finding_type = finding.get("type", "unknown")
                finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
        
        return {
            "description": "Automated rule-based security analysis using OSV API, malicious package databases, and pattern detection",
            "total_packages": summary.get("total_packages", 0),
            "packages_analyzed": summary.get("total_packages", 0),
            "packages_with_issues": summary.get("packages_with_findings", 0),
            "total_issues": summary.get("total_findings", 0),
            "severity_breakdown": severity_breakdown,
            "finding_types": finding_types,
            "detection_methods": {
                "osv_api": "Checked all packages against OSV vulnerability database",
                "malicious_packages": "Scanned against known malicious package lists",
                "typosquatting": "Detected potential typosquatting attempts",
                "pattern_analysis": "Analyzed package patterns and behaviors"
            },
            "confidence": 0.9,  # Rule-based detection is highly reliable
            "agent_analysis_enabled": metadata.get("agent_analysis_enabled", False)
        }
    
    def _build_dependency_graph_section(
        self,
        dependency_graph: Dict[str, Any],
        input_mode: str
    ) -> Dict[str, Any]:
        """
        Build Section 2: Dependency Graph Analysis.
        
        For GitHub mode: Full dependency graph with circular deps and version conflicts
        For local mode: Indicate not applicable
        """
        if input_mode == "local":
            return {
                "applicable": False,
                "reason": "Dependency graph analysis is only available for GitHub repositories",
                "description": "Local folder analysis does not include full dependency graph traversal",
                "recommendation": "Analyze a GitHub repository to get complete dependency graph insights"
            }
        
        # GitHub mode - full dependency graph
        metadata = dependency_graph.get("metadata", {})
        
        return {
            "applicable": True,
            "description": "Complete dependency graph analysis including transitive dependencies, circular dependencies, and version conflicts",
            "total_packages": metadata.get("total_packages", 0),
            "circular_dependencies": {
                "count": metadata.get("circular_dependencies_count", 0),
                "details": dependency_graph.get("circular_dependencies", []),
                "severity": "medium",
                "impact": "Circular dependencies can cause installation issues and unexpected behavior"
            },
            "version_conflicts": {
                "count": metadata.get("version_conflicts_count", 0),
                "details": dependency_graph.get("version_conflicts", []),
                "severity": "medium",
                "impact": "Multiple versions increase bundle size and can cause compatibility issues"
            },
            "dependency_depth": {
                "max_depth": metadata.get("max_depth", 0),
                "description": "Maximum depth of dependency tree"
            },
            "ecosystem": metadata.get("ecosystem", "unknown")
        }
    
    def _build_llm_assessment_section(
        self,
        agent_insights: Dict[str, Any],
        recommendations: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Section 3: LLM-Based Risk Assessment & Recommendations.
        
        This section contains:
        - Overall risk assessment from AI agents
        - Common risks across all issues
        - Prioritized recommendations
        - Strategic guidance
        """
        # Extract agent analysis
        agent_details = agent_insights.get("agent_details", {})
        
        # Build common risks from findings
        common_risks = self._extract_common_risks(summary, agent_details)
        
        # Build prioritized recommendations
        prioritized_recommendations = self._build_prioritized_recommendations(
            recommendations, summary
        )
        
        # Overall risk level
        risk_level = self._calculate_overall_risk(summary)
        
        return {
            "description": "AI-powered risk assessment and strategic recommendations based on multi-agent analysis",
            "overall_risk_level": risk_level,
            "risk_score": self._calculate_risk_score(summary),
            "common_risks": common_risks,
            "recommendations": prioritized_recommendations,
            "strategic_guidance": self._generate_strategic_guidance(summary, risk_level),
            "agent_analysis": {
                "enabled": agent_insights.get("successful_agents", 0) > 0,
                "agents_run": agent_insights.get("successful_agents", 0),
                "agents_failed": agent_insights.get("failed_agents", 0),
                "confidence": agent_insights.get("overall_confidence", 0.9)
            }
        }
    
    def _extract_common_risks(
        self,
        summary: Dict[str, Any],
        agent_details: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract common risks across all issues."""
        risks = []
        
        # Critical/High severity findings
        if summary.get("critical_findings", 0) > 0:
            risks.append({
                "type": "Critical Vulnerabilities",
                "description": f"{summary['critical_findings']} critical security vulnerabilities require immediate attention",
                "severity": "critical",
                "impact": "Potential for severe security breaches, data loss, or system compromise"
            })
        
        if summary.get("high_findings", 0) > 0:
            risks.append({
                "type": "High-Severity Issues",
                "description": f"{summary['high_findings']} high-severity security issues detected",
                "severity": "high",
                "impact": "Significant security risks that should be addressed promptly"
            })
        
        # Outdated dependencies
        if summary.get("total_packages", 0) > 100:
            risks.append({
                "type": "Large Dependency Tree",
                "description": f"{summary['total_packages']} total dependencies increase attack surface",
                "severity": "medium",
                "impact": "More dependencies mean more potential vulnerabilities and maintenance burden"
            })
        
        # Add agent-specific risks if available
        for agent_name, details in agent_details.items():
            if details.get("key_findings"):
                for finding in details["key_findings"][:2]:  # Top 2 per agent
                    risks.append({
                        "type": f"{agent_name.replace('_', ' ').title()} Finding",
                        "description": finding,
                        "severity": "medium",
                        "impact": "Identified by AI analysis"
                    })
        
        return risks[:5]  # Top 5 risks
    
    def _build_prioritized_recommendations(
        self,
        recommendations: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Build prioritized recommendations.
        
        If recommendations are already specific (from synthesis agent), use them.
        Otherwise, generate basic recommendations from summary.
        """
        # Check if we have specific recommendations from synthesis agent
        if recommendations and isinstance(recommendations, dict):
            immediate = recommendations.get("immediate_actions", [])
            short_term = recommendations.get("short_term", [])
            long_term = recommendations.get("long_term", [])
            
            # If we have specific recommendations, use them
            if immediate or short_term or long_term:
                return {
                    "immediate_actions": immediate,
                    "short_term": short_term,
                    "long_term": long_term
                }
        
        # Fallback to generic recommendations if none provided
        critical = summary.get('critical_findings', 0)
        high = summary.get('high_findings', 0)
        
        immediate = []
        if critical > 0:
            immediate.append(f"🔴 CRITICAL: Review and fix {critical} critical vulnerabilities immediately")
        if high > 0:
            immediate.append(f"⚠️  Address {high} high-severity vulnerabilities within 48 hours")
        if not immediate:
            immediate.append("✅ No critical issues detected - continue monitoring")
        
        return {
            "immediate_actions": immediate,
            "short_term": [
                "Implement dependency scanning in CI/CD pipeline",
                "Use lock files to ensure reproducible builds",
                "Enable automated security updates"
            ],
            "long_term": [
                "Regularly update dependencies",
                "Monitor security advisories",
                "Conduct periodic security audits"
            ]
        }
    
    def _calculate_overall_risk(self, summary: Dict[str, Any]) -> str:
        """Calculate overall risk level."""
        critical = summary.get("critical_findings", 0)
        high = summary.get("high_findings", 0)
        medium = summary.get("medium_findings", 0)
        
        if critical > 0:
            return "critical"
        elif high > 5:
            return "high"
        elif high > 0 or medium > 10:
            return "medium"
        else:
            return "low"
    
    def _calculate_risk_score(self, summary: Dict[str, Any]) -> float:
        """Calculate numerical risk score (0-10)."""
        critical = summary.get("critical_findings", 0)
        high = summary.get("high_findings", 0)
        medium = summary.get("medium_findings", 0)
        low = summary.get("low_findings", 0)
        
        # Weighted score
        score = (critical * 10) + (high * 5) + (medium * 2) + (low * 0.5)
        
        # Normalize to 0-10 scale
        max_score = 100  # Arbitrary max
        normalized = min(10, (score / max_score) * 10)
        
        return round(normalized, 1)
    
    def _generate_strategic_guidance(
        self,
        summary: Dict[str, Any],
        risk_level: str
    ) -> str:
        """Generate strategic guidance based on risk level."""
        critical = summary.get("critical_findings", 0)
        high = summary.get("high_findings", 0)
        total = summary.get("total_findings", 0)
        
        if risk_level == "critical":
            return (
                f"URGENT: {critical} critical vulnerabilities require immediate remediation. "
                "Prioritize patching critical issues before deployment. "
                "Consider rolling back to previous versions if patches are not available."
            )
        elif risk_level == "high":
            return (
                f"HIGH PRIORITY: {high} high-severity issues should be addressed promptly. "
                "Schedule remediation within the next sprint. "
                "Review and update vulnerable dependencies."
            )
        elif risk_level == "medium":
            return (
                f"MODERATE RISK: {total} security issues detected. "
                "Plan remediation as part of regular maintenance. "
                "Update dependencies and review security practices."
            )
        else:
            return (
                "LOW RISK: No critical issues detected. "
                "Continue monitoring for new vulnerabilities. "
                "Maintain good security hygiene with regular updates."
            )

    def _build_supply_chain_section(
        self,
        supply_chain_data: Dict[str, Any],
        agent_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Section 3: Supply Chain Analysis (Agent Output - SEPARATE from rule-based).
        
        This section contains AI-powered supply chain attack detection:
        - Maintainer history analysis
        - Version timeline anomalies
        - Publishing pattern detection
        - Exfiltration pattern matching
        - Known attack pattern correlation
        """
        if not supply_chain_data or not supply_chain_data.get("packages"):
            return {
                "applicable": False,
                "reason": "No high-risk packages detected for supply chain analysis",
                "description": "Supply chain analysis runs only when packages have low reputation or suspicious patterns"
            }
        
        packages = supply_chain_data.get("packages", [])
        attacks_detected = supply_chain_data.get("supply_chain_attacks_detected", 0)
        
        # Extract attack patterns
        attack_patterns = []
        for pkg in packages:
            pattern_matches = pkg.get("attack_pattern_matches", [])
            for match in pattern_matches:
                attack_patterns.append({
                    "package": pkg.get("package_name"),
                    "pattern": match.get("pattern_name"),
                    "similarity": match.get("similarity"),
                    "severity": match.get("severity")
                })
        
        # Extract indicators by type
        indicator_summary = {}
        for pkg in packages:
            indicators = pkg.get("supply_chain_indicators", [])
            for ind in indicators:
                ind_type = ind.get("type", "unknown")
                indicator_summary[ind_type] = indicator_summary.get(ind_type, 0) + 1
        
        return {
            "applicable": True,
            "description": "AI-powered supply chain attack detection analyzing maintainer changes, publishing patterns, and attack signatures",
            "total_packages_analyzed": supply_chain_data.get("total_packages_analyzed", 0),
            "attacks_detected": attacks_detected,
            "packages_with_indicators": len(packages),
            "attack_patterns_matched": attack_patterns,
            "indicator_summary": indicator_summary,
            "packages": packages,
            "confidence": supply_chain_data.get("confidence", 0.85),
            "source": "supply_chain_agent",
            "note": "This is SEPARATE from rule-based findings - represents AI analysis of supply chain risks"
        }
    
    def _build_code_analysis_section(
        self,
        code_analysis_data: Dict[str, Any],
        agent_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Section 4: Code Analysis (Agent Output - SEPARATE from rule-based).
        
        This section contains AI-powered static code analysis:
        - Obfuscation detection
        - Behavioral pattern analysis
        - Suspicious code patterns
        - Dynamic execution detection
        """
        if not code_analysis_data or not code_analysis_data.get("packages"):
            return {
                "applicable": False,
                "reason": "No suspicious code patterns detected in initial scan",
                "description": "Code analysis runs only when obfuscation or suspicious scripts are detected"
            }
        
        packages = code_analysis_data.get("packages", [])
        issues_found = code_analysis_data.get("total_code_issues_found", 0)
        
        # Extract obfuscation techniques
        obfuscation_summary = {}
        behavioral_summary = {}
        
        for pkg in packages:
            code_analysis = pkg.get("code_analysis", {})
            
            # Obfuscation
            obfuscation = code_analysis.get("obfuscation_detected", [])
            for obf in obfuscation:
                technique = obf.get("technique", "unknown")
                obfuscation_summary[technique] = obfuscation_summary.get(technique, 0) + 1
            
            # Behavioral indicators
            behavioral = code_analysis.get("behavioral_indicators", [])
            for beh in behavioral:
                behavior = beh.get("behavior", "unknown")
                behavioral_summary[behavior] = behavioral_summary.get(behavior, 0) + 1
        
        return {
            "applicable": True,
            "description": "AI-powered static code analysis detecting obfuscation, suspicious behaviors, and malicious patterns",
            "total_packages_analyzed": code_analysis_data.get("total_packages_analyzed", 0),
            "code_issues_found": issues_found,
            "packages_with_issues": len(packages),
            "obfuscation_techniques": obfuscation_summary,
            "behavioral_indicators": behavioral_summary,
            "packages": packages,
            "confidence": code_analysis_data.get("confidence", 0.85),
            "source": "code_agent",
            "note": "This is SEPARATE from rule-based findings - represents AI analysis of code patterns"
        }
