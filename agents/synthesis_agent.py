"""
Synthesis Agent for the multi-agent security analysis system.

This agent aggregates findings from all other agents and produces the final
package-centric JSON output using OpenAI JSON mode for guaranteed valid JSON.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 11.1, 11.2, 11.3, 11.4, 11.5**
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from openai import OpenAI

from agents.base_agent import SecurityAgent
from agents.types import SharedContext, AgentResult

# Load environment variables
load_dotenv()


class SynthesisAgent(SecurityAgent):
    """
    Agent that synthesizes all agent findings into final package-centric JSON report.
    
    This agent:
    - Aggregates findings from all agents (Vulnerability, Reputation, Code, Supply Chain)
    - Generates common recommendations across packages using LLM
    - Provides project-level risk assessment with confidence scores
    - Produces final JSON output using OpenAI JSON mode (guaranteed valid JSON)
    - Implements fallback report generation when synthesis fails
    
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 11.1, 11.2, 11.3, 11.4, 11.5**
    """
    
    def __init__(self):
        """Initialize the Synthesis Agent."""
        system_message = """You are a Synthesis Agent responsible for producing the final package-centric JSON security report.

Your responsibilities:
1. Aggregate findings from all security agents (Vulnerability, Reputation, Code, Supply Chain)
2. Generate common recommendations across all packages
3. Provide project-level risk assessment with confidence scores
4. Produce final JSON output in the exact required format

CRITICAL: You MUST output valid JSON only. Your response must be a complete JSON object.

Required JSON structure:
{
  "metadata": { analysis metadata },
  "summary": { overall statistics },
  "sbom_data": { software bill of materials },
  "security_findings": [ array of findings ],
  "suspicious_activities": [ array of suspicious activities ],
  "recommendations": [ array of recommendations ],
  "agent_insights": { agent reasoning and confidence },
  "raw_data": { additional data }
}

Always provide actionable, prioritized recommendations with clear reasoning."""
        
        super().__init__(
            name="SynthesisAgent",
            system_message=system_message,
            tools=[
                self.aggregate_findings,
                self.generate_common_recommendations,
                self.assess_project_risk,
                self.format_package_centric_report
            ]
        )
        
        # Initialize OpenAI client with reduced timeout and no retries
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._log("WARNING: OPENAI_API_KEY not found in environment. LLM synthesis will fail.", "WARNING")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(
                api_key=api_key,
                timeout=10.0,  # 10 second timeout
                max_retries=0  # Disable automatic retries
            )
            self._log(f"OpenAI client initialized with key: {api_key[:10]}...", "INFO")
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Synthesize final JSON report from all agent results with LLM-powered recommendations.
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
        
        Strategy:
        1. Generate base report from all agent findings
        2. Use LLM to analyze complete findings and generate intelligent recommendations
        3. Combine base report with LLM insights
        
        Args:
            context: Shared context with all agent results
            timeout: Optional timeout override
        
        Returns:
            Complete package-centric JSON report with LLM recommendations
        """
        start_time = time.time()
        
        self._log("Starting synthesis with LLM-powered recommendations", "INFO")
        
        # Step 1: Generate base report from all agent findings
        base_report = self._generate_fallback_report(context)
        
        # Step 2: Try to enhance with LLM recommendations
        try:
            self._log("Generating LLM recommendations from complete analysis...", "INFO")
            
            llm_recommendations = self._generate_llm_recommendations(
                context=context,
                base_report=base_report,
                timeout=timeout or 15
            )
            
            # Replace recommendations with LLM-generated content
            if llm_recommendations:
                base_report["recommendations"] = llm_recommendations
                self._log("LLM recommendations generated successfully", "INFO")
                synthesis_method = "llm_enhanced"
            else:
                self._log("LLM returned empty recommendations, using rule-based", "WARNING")
                synthesis_method = "rule_based"
            
        except Exception as e:
            self._log(f"LLM recommendation generation failed: {str(e)}, using rule-based recommendations", "WARNING")
            synthesis_method = "rule_based"
        
        duration = time.time() - start_time
        base_report["metadata"]["synthesis_method"] = synthesis_method
        base_report["metadata"]["synthesis_duration"] = duration
        
        return base_report
    
    def synthesize_json_fast(
        self,
        context: SharedContext,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Fast synthesis with aggressive timeout and minimal token usage.
        
        Args:
            context: Shared context
            timeout: Timeout in seconds
        
        Returns:
            Synthesized JSON report
        """
        # Check if OpenAI client is available
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY in .env file.")
        
        # Create minimal prompt (reduce tokens)
        prompt = self._create_minimal_synthesis_prompt(context)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Faster than gpt-4
                messages=[
                    {"role": "system", "content": "You are a security report synthesizer. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000,  # Reduced from 4096
                timeout=timeout
            )
            
            json_output = json.loads(response.choices[0].message.content)
            return json_output
            
        except Exception as e:
            self._log(f"Fast synthesis failed: {str(e)}", "WARNING")
            raise
    
    def _create_minimal_synthesis_prompt(self, context: SharedContext) -> str:
        """
        Create minimal prompt to reduce tokens and speed up synthesis.
        
        Args:
            context: Shared context
        
        Returns:
            Minimal synthesis prompt
        """
        # Extract key data only
        package_count = len(context.packages) if hasattr(context, 'packages') else 0
        
        # Count findings by severity
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        
        for agent_name, result in context.agent_results.items():
            if result.success:
                packages = result.data.get("packages", [])
                for pkg in packages:
                    vulns = pkg.get("vulnerabilities", [])
                    for vuln in vulns:
                        severity = vuln.get("severity", "").lower()
                        if severity == "critical":
                            critical_count += 1
                        elif severity == "high":
                            high_count += 1
                        elif severity == "medium":
                            medium_count += 1
                        elif severity == "low":
                            low_count += 1
        
        # Minimal prompt
        prompt = f"""Synthesize security analysis for {package_count} packages.

Findings:
- Critical: {critical_count}
- High: {high_count}
- Medium: {medium_count}
- Low: {low_count}

Generate JSON with:
1. summary: {{total_packages, critical_findings, high_findings, medium_findings, low_findings}}
2. recommendations: [top 3 actions]
3. agent_insights: {{synthesis_note: "brief summary"}}

Keep response under 500 tokens. Output valid JSON only."""
        
        return prompt
    
    def synthesize_json(
        self,
        context: SharedContext,
        timeout: int,
        use_json_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesize final JSON report using OpenAI JSON mode.
        
        **Validates: Requirement 7.1 (aggregation), 7.5 (synthesis)**
        
        OpenAI JSON mode guarantees valid JSON output, eliminating parsing issues.
        
        Args:
            context: Shared context with all agent results
            timeout: Timeout in seconds
            use_json_mode: Whether to use OpenAI JSON mode (default: True)
        
        Returns:
            Complete JSON report
        """
        # Prepare synthesis prompt
        prompt = self._create_synthesis_prompt(context)
        
        # Check if OpenAI client is available
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY in .env file.")
        
        # Use OpenAI JSON mode for guaranteed valid JSON
        if use_json_mode:
            try:
                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": self.system_message},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},  # Forces JSON output
                    temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
                    max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
                    timeout=timeout
                )
                
                # Parse JSON (guaranteed to be valid by OpenAI)
                json_output = json.loads(response.choices[0].message.content)
                
                return json_output
                
            except Exception as e:
                self._log(f"OpenAI JSON mode failed: {str(e)}, using fallback", "WARNING")
                # Fall through to fallback method
        
        # Fallback: Try to extract JSON from regular completion
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
                timeout=timeout
            )
            
            content = response.choices[0].message.content
            json_output = self._extract_json_from_text(content)
            
            return json_output
            
        except Exception as e:
            self._log(f"Fallback synthesis failed: {str(e)}", "ERROR")
            raise
    
    def _create_synthesis_prompt(self, context: SharedContext) -> str:
        """
        Create synthesis prompt with all agent results.
        
        Args:
            context: Shared context
        
        Returns:
            Prompt string for LLM
        """
        agent_results = context.agent_results
        packages = context.packages
        initial_findings = context.initial_findings
        
        prompt = f"""Synthesize a complete security analysis report from the following agent results.

PROJECT INFORMATION:
- Input Mode: {context.input_mode}
- Ecosystem: {context.ecosystem}
- Total Packages: {len(packages)}
- Initial Findings: {len(initial_findings)}

AGENT ANALYSIS RESULTS:
"""
        
        # Add each agent's results
        for agent_name, result in agent_results.items():
            if result.success:
                prompt += f"\n{agent_name.upper()} (SUCCESS - {result.duration_seconds:.2f}s, confidence: {result.confidence:.2f}):\n"
                prompt += f"{json.dumps(result.data, indent=2)}\n"
            else:
                prompt += f"\n{agent_name.upper()} (FAILED): {result.error}\n"
        
        # Add dependency graph info
        if context.dependency_graph:
            prompt += f"\nDEPENDENCY GRAPH:\n{json.dumps(context.dependency_graph, indent=2)}\n"
        
        prompt += """

REQUIRED OUTPUT:
Generate a complete JSON report with this exact structure:

{
  "metadata": {
    "analysis_id": "analysis_YYYYMMDD_HHMMSS_hash",
    "analysis_type": "local_directory" or "github",
    "target": "path or URL",
    "start_time": "ISO timestamp",
    "end_time": "ISO timestamp",
    "total_packages": number,
    "total_findings": number,
    "confidence_threshold": 0.7,
    "analysis_method": "hybrid"
  },
  "summary": {
    "total_packages": number,
    "total_findings": number,
    "critical_findings": number,
    "high_findings": number,
    "medium_findings": number,
    "low_findings": number,
    "ecosystems_analyzed": ["npm", "pypi"],
    "finding_types": {}
  },
  "sbom_data": {
    "format": "multi-agent-security-sbom",
    "version": "1.0",
    "packages": []
  },
  "security_findings": [
    {
      "package": "package-name",
      "version": "1.0.0",
      "finding_type": "vulnerability|malicious_package|supply_chain_attack",
      "severity": "critical|high|medium|low",
      "confidence": 0.0-1.0,
      "evidence": ["array of evidence strings"],
      "recommendations": ["array of recommendations"],
      "source": "hybrid_analysis",
      "detection_method": "rule_based + agent_analysis",
      "agent_insights": {
        "analyzed_by": ["agent names"],
        "reasoning": "explanation",
        "confidence_explanation": "why this confidence score"
      }
    }
  ],
  "suspicious_activities": [],
  "recommendations": [
    "array of overall recommendations"
  ],
  "agent_insights": {
    "synthesis": "overall analysis summary",
    "risk_assessment": {
      "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",
      "risk_score": 0.0-1.0,
      "reasoning": "explanation",
      "confidence": 0.0-1.0
    },
    "prioritization": [
      {
        "priority": 1,
        "package": "package-name",
        "version": "1.0.0",
        "action": "what to do",
        "reason": "why",
        "impact": "critical|high|medium|low",
        "urgency": "immediate|high|medium|low"
      }
    ],
    "confidence_breakdown": {
      "vulnerability_analysis": 0.0-1.0,
      "reputation_analysis": 0.0-1.0,
      "overall_synthesis": 0.0-1.0
    },
    "agent_contributions": {
      "agent_name": "what this agent analyzed"
    }
  },
  "raw_data": {
    "cache_statistics": {},
    "performance_metrics": {}
  }
}

IMPORTANT:
1. Aggregate all findings by package (package-centric structure)
2. Generate common recommendations across all packages
3. Provide clear risk assessment with reasoning
4. Include confidence scores and explanations
5. Prioritize findings by severity and impact
6. Output ONLY valid JSON, no markdown or explanations
"""
        
        return prompt
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Fallback: Extract JSON from text response.
        
        Args:
            text: Text response from LLM
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError: If no valid JSON found
        """
        import re
        
        # Try to find JSON in markdown code block
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                raise ValueError("No JSON found in response")
        
        return json.loads(json_str)
    
    def _validate_json_schema(self, json_data: Dict[str, Any]) -> bool:
        """
        Validate final JSON against expected schema.
        
        **Validates: Requirement 7.3 (schema validation)**
        
        Args:
            json_data: JSON data to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            "metadata",
            "summary",
            "security_findings",
            "recommendations"
        ]
        
        # Check required top-level keys
        for key in required_keys:
            if key not in json_data:
                self._log(f"Missing required key: {key}", "ERROR")
                return False
        
        # Validate metadata structure
        if not isinstance(json_data["metadata"], dict):
            self._log("metadata must be a dictionary", "ERROR")
            return False
        
        # Validate summary structure
        if not isinstance(json_data["summary"], dict):
            self._log("summary must be a dictionary", "ERROR")
            return False
        
        # Validate security_findings is array
        if not isinstance(json_data["security_findings"], list):
            self._log("security_findings must be an array", "ERROR")
            return False
        
        # Validate recommendations is array
        if not isinstance(json_data["recommendations"], list):
            self._log("recommendations must be an array", "ERROR")
            return False
        
        return True
    
    def _generate_fallback_report(self, context: SharedContext) -> Dict[str, Any]:
        """
        Generate fallback report when synthesis fails.
        
        **Validates: Requirement 7.3 (fallback generation)**
        
        Args:
            context: Shared context
        
        Returns:
            Fallback JSON report
        """
        self._log("Generating fallback report from available data", "WARNING")
        
        # Aggregate findings manually
        packages_data = self.aggregate_findings(context)
        
        # Generate simple text recommendations based on findings
        recommendations = self._generate_simple_text_recommendations(context, packages_data)
        
        # Assess risk
        risk_assessment = self.assess_project_risk(packages_data)
        
        # Build security_findings from rule-based findings only (keep agents separate)
        security_findings = self._build_security_findings_from_rule_based(context)
        
        # Extract agent-specific data (keep separate from rule-based)
        supply_chain_data = self._extract_supply_chain_data(context)
        code_analysis_data = self._extract_code_analysis_data(context)
        
        # Create fallback report
        return {
            "metadata": {
                "analysis_id": f"analysis_{int(time.time())}",
                "analysis_type": context.input_mode,
                "target": context.project_path,
                "start_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_packages": len(context.packages),
                "total_findings": len(context.initial_findings),
                "confidence_threshold": 0.7,
                "analysis_method": "hybrid",
                "synthesis_status": "fallback"
            },
            "summary": self._calculate_severity_summary(context),
            "sbom_data": {
                "format": "multi-agent-security-sbom",
                "version": "1.0",
                "packages": []
            },
            "security_findings": security_findings,
            "supply_chain_analysis": self._get_supply_chain_detector_data(context),
            "code_analysis": code_analysis_data,
            "suspicious_activities": [],
            "recommendations": recommendations,
            "agent_insights": {
                "synthesis": "Synthesis agent failed, using fallback report generation",
                "risk_assessment": risk_assessment,
                "confidence_breakdown": self._get_confidence_breakdown(context),
                "agent_contributions": self._get_agent_contributions(context),
                "supply_chain_detector": self._get_supply_chain_detector_summary(context)
            },
            "raw_data": {
                "cache_statistics": {},
                "performance_metrics": {}
            }
        }
    
    def _calculate_severity_summary(self, context: SharedContext) -> Dict[str, Any]:
        """
        Calculate severity counts from initial findings.
        
        Args:
            context: Shared context with initial findings
        
        Returns:
            Summary dict with severity counts
        """
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in context.initial_findings:
            severity = finding.severity.lower() if hasattr(finding, 'severity') else "low"
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "total_packages": len(context.packages),
            "total_findings": len(context.initial_findings),
            "critical_findings": severity_counts["critical"],
            "high_findings": severity_counts["high"],
            "medium_findings": severity_counts["medium"],
            "low_findings": severity_counts["low"],
            "ecosystems_analyzed": [context.ecosystem]
        }
    
    def aggregate_findings(self, context: SharedContext) -> Dict[str, Any]:
        """
        Aggregate findings from all agents into package-centric structure.
        
        **Tool function for agent**
        **Validates: Requirement 7.1 (aggregation)**
        
        Args:
            context: Shared context with agent results
        
        Returns:
            Dictionary of packages with aggregated findings
        """
        packages = {}
        
        # Initialize packages from context
        for package_name in context.packages:
            packages[package_name] = {
                "name": package_name,
                "version": "unknown",
                "ecosystem": context.ecosystem,
                "vulnerabilities": [],
                "reputation_analysis": {},
                "code_analysis": {},
                "supply_chain_analysis": {},
                "recommendations": []
            }
        
        # Add vulnerability analysis results
        vuln_result = context.get_agent_result("VulnerabilityAnalysisAgent")
        if vuln_result and vuln_result.success:
            for pkg_data in vuln_result.data.get("packages", []):
                pkg_name = pkg_data.get("package_name")
                if pkg_name in packages:
                    packages[pkg_name]["vulnerabilities"] = pkg_data.get("vulnerabilities", [])
                    packages[pkg_name]["version"] = pkg_data.get("package_version", "unknown")
        
        # Add reputation analysis results
        rep_result = context.get_agent_result("ReputationAnalysisAgent")
        if rep_result and rep_result.success:
            for pkg_data in rep_result.data.get("packages", []):
                pkg_name = pkg_data.get("package_name")
                if pkg_name in packages:
                    packages[pkg_name]["reputation_analysis"] = pkg_data
        
        # Add code analysis results (if available)
        code_result = context.get_agent_result("CodeAnalysisAgent")
        if code_result and code_result.success:
            for pkg_data in code_result.data.get("packages", []):
                pkg_name = pkg_data.get("package_name")
                if pkg_name in packages:
                    packages[pkg_name]["code_analysis"] = pkg_data
        
        # Add supply chain analysis results (if available)
        sc_result = context.get_agent_result("SupplyChainAttackAgent")
        if sc_result and sc_result.success:
            for pkg_data in sc_result.data.get("packages", []):
                pkg_name = pkg_data.get("package_name")
                if pkg_name in packages:
                    packages[pkg_name]["supply_chain_analysis"] = pkg_data
        
        return packages
    
    def generate_common_recommendations(self, packages: Dict[str, Any]) -> List[str]:
        """
        Generate common recommendations across all packages.
        
        **Tool function for agent**
        **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
        
        Args:
            packages: Dictionary of packages with findings
        
        Returns:
            List of common recommendations
        """
        recommendations = []
        
        # Count severity levels
        critical_count = 0
        high_count = 0
        medium_count = 0
        malicious_count = 0
        
        for pkg in packages.values():
            for vuln in pkg.get("vulnerabilities", []):
                severity = vuln.get("severity", "").lower()
                if severity == "critical":
                    critical_count += 1
                elif severity == "high":
                    high_count += 1
                elif severity == "medium":
                    medium_count += 1
            
            # Check for malicious packages
            if pkg.get("supply_chain_analysis", {}).get("is_malicious"):
                malicious_count += 1
        
        # Generate recommendations based on findings
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical security finding{'s' if critical_count > 1 else ''}. "
                "These may indicate active security threats."
            )
        
        if malicious_count > 0:
            recommendations.append(
                f"Remove {malicious_count} identified malicious package{'s' if malicious_count > 1 else ''} immediately. "
                "Scan systems for signs of compromise and review all dependencies."
            )
        
        if high_count > 0:
            recommendations.append(
                f"Update {high_count} package{'s' if high_count > 1 else ''} with known vulnerabilities to patched versions. "
                "Prioritize based on severity and exploitability."
            )
        
        # General recommendations
        recommendations.extend([
            "Implement dependency scanning in your CI/CD pipeline to catch issues early.",
            "Use Software Bill of Materials (SBOM) to maintain visibility into your dependencies.",
            "Regularly update dependencies and monitor security advisories.",
            "Consider using dependency pinning and lock files to ensure reproducible builds.",
            "Implement security policies for dependency management and approval processes."
        ])
        
        return recommendations
    
    def assess_project_risk(self, packages: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall project risk level.
        
        **Tool function for agent**
        **Validates: Requirement 7.4 (risk assessment)**
        
        Args:
            packages: Dictionary of packages with findings
        
        Returns:
            Risk assessment dictionary
        """
        critical_count = 0
        high_count = 0
        medium_count = 0
        malicious_count = 0
        
        for pkg in packages.values():
            # Count vulnerabilities by severity
            for vuln in pkg.get("vulnerabilities", []):
                severity = vuln.get("severity", "").lower()
                if severity == "critical":
                    critical_count += 1
                elif severity == "high":
                    high_count += 1
                elif severity == "medium":
                    medium_count += 1
            
            # Check for malicious packages
            if pkg.get("supply_chain_analysis", {}).get("is_malicious"):
                malicious_count += 1
        
        # Determine overall risk
        if malicious_count > 0 or critical_count > 0:
            risk_level = "CRITICAL"
            risk_score = min(0.9 + (critical_count * 0.01) + (malicious_count * 0.05), 1.0)
            reasoning = f"Found {malicious_count} malicious package(s) and {critical_count} critical vulnerabilities"
        elif high_count > 2:
            risk_level = "HIGH"
            risk_score = 0.7 + (high_count * 0.02)
            reasoning = f"Found {high_count} high severity vulnerabilities"
        elif high_count > 0 or medium_count > 3:
            risk_level = "MEDIUM"
            risk_score = 0.5 + (high_count * 0.05) + (medium_count * 0.01)
            reasoning = f"Found {high_count} high and {medium_count} medium severity issues"
        else:
            risk_level = "LOW"
            risk_score = 0.3
            reasoning = "No critical or high severity issues found"
        
        return {
            "overall_risk": risk_level,
            "risk_score": min(risk_score, 1.0),
            "reasoning": reasoning,
            "confidence": 0.9
        }
    
    def format_package_centric_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format data into final package-centric JSON structure.
        
        **Tool function for agent**
        **Validates: Requirement 7.2 (package-centric structure)**
        
        Args:
            data: Raw data to format
        
        Returns:
            Formatted JSON report
        """
        return {
            "metadata": data.get("metadata", {}),
            "summary": data.get("summary", {}),
            "sbom_data": data.get("sbom_data", {}),
            "security_findings": data.get("security_findings", []),
            "suspicious_activities": data.get("suspicious_activities", []),
            "recommendations": data.get("recommendations", []),
            "agent_insights": data.get("agent_insights", {}),
            "raw_data": data.get("raw_data", {})
        }
    
    def _generate_basic_recommendations(self, packages: Dict[str, Any]) -> List[str]:
        """Generate basic recommendations from package data."""
        return self.generate_common_recommendations(packages)
    
    def _generate_llm_recommendations(
        self,
        context: SharedContext,
        base_report: Dict[str, Any],
        timeout: int
    ) -> Optional[str]:
        """
        Generate intelligent recommendations using LLM analysis of complete findings.
        
        This method sends ALL agent findings to the LLM for comprehensive analysis
        and returns a detailed recommendation text.
        
        Args:
            context: Shared context with all agent results
            base_report: Base report with aggregated findings
            timeout: Timeout in seconds
        
        Returns:
            String with LLM-generated recommendations
        """
        # Check if OpenAI client is available
        if not self.openai_client:
            self._log("OpenAI client not available, skipping LLM recommendations", "WARNING")
            return None
        
        # Create comprehensive prompt with ALL findings
        prompt = self._create_llm_recommendation_prompt(context, base_report)
        
        try:
            self._log(f"Sending {len(prompt)} chars to LLM for analysis...", "INFO")
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a senior security engineer writing recommendations for a development team.

Write clear, professional recommendations that:
- Prioritize by risk and impact (not by listing every package)
- Group similar issues together intelligently
- Provide specific actions for critical issues
- Include preventive measures and best practices
- Are engaging and easy to read

Write in flowing paragraphs, not bullet points. Be concise but thorough."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                timeout=timeout
            )
            
            recommendations_text = response.choices[0].message.content.strip()
            self._log("LLM recommendations generated successfully", "INFO")
            return recommendations_text
            
        except Exception as e:
            self._log(f"LLM recommendation generation failed: {str(e)}", "ERROR")
            return None
    
    def _create_llm_recommendation_prompt(
        self,
        context: SharedContext,
        base_report: Dict[str, Any]
    ) -> str:
        """
        Create intelligent prompt for LLM to generate smart, engaging recommendations.
        
        Args:
            context: Shared context
            base_report: Base report with findings
        
        Returns:
            Prompt string for LLM
        """
        # Extract key statistics
        summary = base_report.get("summary", {})
        security_findings = base_report.get("security_findings", {})
        
        # Get top critical/high severity packages (not all packages)
        critical_packages = []
        high_packages = []
        
        for finding in context.initial_findings:
            if finding.severity.lower() == "critical":
                critical_packages.append(f"{finding.package_name}@{finding.package_version}: {finding.description}")
            elif finding.severity.lower() == "high":
                high_packages.append(f"{finding.package_name}@{finding.package_version}: {finding.description}")
        
        # Limit to top 5 of each
        critical_packages = critical_packages[:5]
        high_packages = high_packages[:5]
        
        prompt = f"""You are a security expert reviewing a dependency analysis report. Generate intelligent, engaging recommendations.

PROJECT OVERVIEW:
- Total Packages Analyzed: {summary.get('total_packages', 0)}
- Security Issues Found: {summary.get('total_findings', 0)}
- Severity Breakdown: {summary.get('critical_findings', 0)} Critical, {summary.get('high_findings', 0)} High, {summary.get('medium_findings', 0)} Medium, {summary.get('low_findings', 0)} Low

TOP CRITICAL ISSUES:
{chr(10).join(f"• {pkg}" for pkg in critical_packages) if critical_packages else "None"}

TOP HIGH-SEVERITY ISSUES:
{chr(10).join(f"• {pkg}" for pkg in high_packages[:3]) if high_packages else "None"}

AGENT ANALYSIS SUMMARY:
"""
        
        # Add concise agent summaries
        for agent_name, result in context.agent_results.items():
            if result.success:
                data = result.data
                if "total_vulnerabilities_found" in data and data["total_vulnerabilities_found"] > 0:
                    prompt += f"• Vulnerability Analysis: Found {data['total_vulnerabilities_found']} vulnerabilities across {data.get('total_packages_analyzed', 0)} packages\n"
                if "supply_chain_attacks_detected" in data and data["supply_chain_attacks_detected"] > 0:
                    prompt += f"• Supply Chain: Detected {data['supply_chain_attacks_detected']} potential supply chain attacks\n"
        
        prompt += """

TASK: Generate clear, actionable security recommendations in plain text format.

GUIDELINES:
1. Be INTELLIGENT - Don't list every package. Group similar issues and prioritize by impact.
2. Be SPECIFIC - Mention the most critical packages by name, but summarize patterns.
3. Be ENGAGING - Write in clear, professional language that developers will actually read.
4. Be PRACTICAL - Focus on what they should do NOW vs. later.

FORMAT: Write 2-4 paragraphs covering:
- Critical/Immediate Actions (if any critical issues exist)
- Important Security Improvements (address high/medium issues)
- Best Practices & Prevention (long-term security posture)

Keep it concise but comprehensive. NO bullet points, NO JSON structure - just clear, flowing text."""
        
        return prompt
    
    def _generate_simple_text_recommendations(
        self,
        context: SharedContext,
        packages_data: Dict[str, Any]
    ) -> str:
        """
        Generate simple text recommendations when LLM is not available.
        
        Args:
            context: Shared context
            packages_data: Aggregated package data
        
        Returns:
            Simple recommendation text
        """
        recommendations = []
        
        # Count findings
        critical_count = 0
        high_count = 0
        
        for finding in context.initial_findings:
            if finding.severity.lower() == "critical":
                critical_count += 1
            elif finding.severity.lower() == "high":
                high_count += 1
        
        if critical_count > 0:
            recommendations.append(f"URGENT: Address {critical_count} critical security findings immediately.")
        
        if high_count > 0:
            recommendations.append(f"Update {high_count} packages with high-severity vulnerabilities.")
        
        if not recommendations:
            recommendations.append("No critical issues detected. Continue monitoring for new vulnerabilities.")
        
        recommendations.extend([
            "Implement dependency scanning in CI/CD pipeline.",
            "Regularly update dependencies and monitor security advisories."
        ])
        
        return "\n".join(f"• {rec}" for rec in recommendations)
    
    def _generate_specific_recommendations(
        self, 
        context: SharedContext,
        packages_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SPECIFIC, actionable recommendations based on actual findings.
        
        This analyzes all agent results and creates 7-8 lines of concrete recommendations
        instead of generic advice.
        
        Args:
            context: Shared context with all agent results
            packages_data: Aggregated package data
        
        Returns:
            Dictionary with categorized recommendations
        """
        immediate = []
        short_term = []
        long_term = []
        
        # Analyze vulnerabilities
        vuln_result = context.get_agent_result("VulnerabilityAnalysisAgent")
        if vuln_result and vuln_result.success:
            vuln_data = vuln_result.data
            critical_count = 0
            high_count = 0
            critical_packages = []
            high_packages = []
            
            for pkg in vuln_data.get("packages", []):
                pkg_name = pkg.get("package_name")
                for vuln in pkg.get("vulnerabilities", []):
                    severity = vuln.get("severity", "").lower()
                    if severity == "critical":
                        critical_count += 1
                        if pkg_name not in critical_packages:
                            critical_packages.append(pkg_name)
                    elif severity == "high":
                        high_count += 1
                        if pkg_name not in high_packages:
                            high_packages.append(pkg_name)
            
            if critical_count > 0:
                pkg_list = ", ".join(critical_packages[:3])
                more = f" and {len(critical_packages) - 3} more" if len(critical_packages) > 3 else ""
                immediate.append(
                    f"🔴 CRITICAL: Update {len(critical_packages)} packages with {critical_count} critical vulnerabilities ({pkg_list}{more})"
                )
            
            if high_count > 0:
                pkg_list = ", ".join(high_packages[:3])
                more = f" and {len(high_packages) - 3} more" if len(high_packages) > 3 else ""
                short_term.append(
                    f"⚠️  Update {len(high_packages)} packages with {high_count} high-severity vulnerabilities ({pkg_list}{more})"
                )
        
        # Analyze supply chain risks
        sc_result = context.get_agent_result("SupplyChainAttackAgent")
        if sc_result and sc_result.success:
            sc_data = sc_result.data
            attacks = sc_data.get("supply_chain_attacks_detected", 0)
            
            if attacks > 0:
                risky_packages = []
                for pkg in sc_data.get("packages", []):
                    if pkg.get("attack_likelihood") in ["critical", "high"]:
                        risky_packages.append(pkg.get("package_name"))
                
                if risky_packages:
                    pkg_list = ", ".join(risky_packages[:2])
                    immediate.append(
                        f"🚨 URGENT: Remove {len(risky_packages)} packages with supply chain attack indicators ({pkg_list}) and scan for compromise"
                    )
        
        # Analyze code issues
        code_result = context.get_agent_result("CodeAnalysisAgent")
        if code_result and code_result.success:
            code_data = code_result.data
            obfuscated_packages = []
            suspicious_packages = []
            
            for pkg in code_data.get("packages", []):
                pkg_name = pkg.get("package_name")
                code_analysis = pkg.get("code_analysis", {})
                
                if code_analysis.get("obfuscation_detected"):
                    obfuscated_packages.append(pkg_name)
                
                behavioral = code_analysis.get("behavioral_indicators", [])
                high_risk = [b for b in behavioral if b.get("risk_level") in ["high", "critical"]]
                if high_risk:
                    suspicious_packages.append(pkg_name)
            
            if obfuscated_packages:
                pkg_list = ", ".join(obfuscated_packages[:2])
                short_term.append(
                    f"🔍 Review {len(obfuscated_packages)} packages with obfuscated code ({pkg_list}) - verify legitimacy or replace"
                )
            
            if suspicious_packages:
                pkg_list = ", ".join(suspicious_packages[:2])
                short_term.append(
                    f"⚡ Audit {len(suspicious_packages)} packages with suspicious behaviors ({pkg_list}) - check network/file access"
                )
        
        # Analyze reputation
        rep_result = context.get_agent_result("ReputationAnalysisAgent")
        if rep_result and rep_result.success:
            rep_data = rep_result.data
            low_rep_packages = []
            
            for pkg in rep_data.get("packages", []):
                if pkg.get("reputation_score", 1.0) < 0.3:
                    low_rep_packages.append(pkg.get("package_name"))
            
            if low_rep_packages:
                pkg_list = ", ".join(low_rep_packages[:2])
                more = f" and {len(low_rep_packages) - 2} more" if len(low_rep_packages) > 2 else ""
                short_term.append(
                    f"📊 Replace {len(low_rep_packages)} low-reputation packages ({pkg_list}{more}) with trusted alternatives"
                )
        
        # Analyze dependency graph
        dep_graph = context.dependency_graph
        if dep_graph:
            metadata = dep_graph.get("metadata", {})
            circular = metadata.get("circular_dependencies_count", 0)
            conflicts = metadata.get("version_conflicts_count", 0)
            
            if circular > 0:
                long_term.append(
                    f"🔄 Resolve {circular} circular dependencies to improve build stability and reduce complexity"
                )
            
            if conflicts > 5:
                long_term.append(
                    f"📦 Fix {conflicts} version conflicts to reduce bundle size and prevent compatibility issues"
                )
        
        # Add general best practices if we have findings
        if immediate or short_term:
            long_term.append(
                "🛡️  Implement automated dependency scanning in CI/CD to catch vulnerabilities before deployment"
            )
            long_term.append(
                "📋 Generate and maintain SBOM (Software Bill of Materials) for supply chain visibility"
            )
        
        # Ensure we have at least some recommendations
        if not immediate:
            immediate.append("✅ No critical issues detected - continue monitoring for new vulnerabilities")
        
        if not short_term:
            short_term.append("✅ No high-priority issues - maintain current security practices")
        
        if not long_term:
            long_term.append("📈 Regularly update dependencies and review security advisories")
        
        return {
            "immediate_actions": immediate[:3],  # Top 3 most urgent
            "short_term": short_term[:3],        # Top 3 short-term
            "long_term": long_term[:2]           # Top 2 long-term
        }
    
    def _convert_findings_to_json(self, findings: List) -> List[Dict[str, Any]]:
        """Convert Finding objects to JSON dictionaries."""
        json_findings = []
        
        for finding in findings:
            if hasattr(finding, 'to_dict'):
                json_findings.append(finding.to_dict())
            elif isinstance(finding, dict):
                json_findings.append(finding)
        
        return json_findings
    
    def _get_confidence_breakdown(self, context: SharedContext) -> Dict[str, float]:
        """Get confidence scores from all agents."""
        breakdown = {}
        
        for agent_name, result in context.agent_results.items():
            breakdown[agent_name.lower().replace("agent", "")] = result.confidence
        
        # Calculate overall synthesis confidence
        if breakdown:
            breakdown["overall_synthesis"] = sum(breakdown.values()) / len(breakdown)
        else:
            breakdown["overall_synthesis"] = 0.5
        
        return breakdown
    
    def _get_agent_contributions(self, context: SharedContext) -> Dict[str, str]:
        """Get summary of what each agent analyzed."""
        contributions = {}
        
        for agent_name, result in context.agent_results.items():
            if result.success:
                data = result.data
                if "packages" in data:
                    pkg_count = len(data["packages"])
                    contributions[agent_name] = f"Analyzed {pkg_count} packages"
                else:
                    contributions[agent_name] = "Analysis completed"
            else:
                contributions[agent_name] = f"Failed: {result.error}"
        
        return contributions
    
    def _build_security_findings_from_rule_based(
        self, 
        context: SharedContext
    ) -> Dict[str, Any]:
        """
        Build security_findings structure with CONSOLIDATED findings per package.
        
        Creates a user-friendly summary per package with:
        - Rule-based findings (OSV vulnerabilities)
        - Agent-based findings (supply chain detector) - consolidated into single entry
        
        Args:
            context: Shared context with initial findings
        
        Returns:
            Security findings dictionary with packages array (consolidated view)
        """
        packages_dict = {}
        
        # Group initial findings by package (rule-based)
        for finding in context.initial_findings:
            pkg_name = finding.package_name
            if pkg_name not in packages_dict:
                packages_dict[pkg_name] = {
                    "name": pkg_name,
                    "version": finding.package_version if hasattr(finding, 'package_version') else "unknown",
                    "ecosystem": context.ecosystem,
                    "findings": [],
                    "agent_analysis": None,  # Will hold consolidated agent findings
                    "risk_score": 0.0,
                    "risk_level": "low"
                }
            
            # Add rule-based finding
            packages_dict[pkg_name]["findings"].append({
                "type": finding.finding_type,
                "severity": finding.severity,
                "description": finding.description,
                "confidence": finding.confidence,
                "evidence": finding.evidence,
                "remediation": finding.remediation
            })
        
        # Merge supply chain detector findings - CONSOLIDATED per package
        sc_result = context.get_agent_result("supply_chain_detector")
        if sc_result and sc_result.success:
            threats = sc_result.data.get("threats_detected", [])
            
            # Group threats by package
            threats_by_pkg = {}
            for threat in threats:
                pkg_name = threat.get("package_name", "unknown")
                if pkg_name not in threats_by_pkg:
                    threats_by_pkg[pkg_name] = []
                threats_by_pkg[pkg_name].append(threat)
            
            # Create consolidated agent analysis per package
            for pkg_name, pkg_threats in threats_by_pkg.items():
                # Create package entry if not exists
                if pkg_name not in packages_dict:
                    packages_dict[pkg_name] = {
                        "name": pkg_name,
                        "version": pkg_threats[0].get("package_version", "*") if pkg_threats else "*",
                        "ecosystem": pkg_threats[0].get("ecosystem", context.ecosystem) if pkg_threats else context.ecosystem,
                        "findings": [],
                        "agent_analysis": None,
                        "risk_score": 0.0,
                        "risk_level": "low"
                    }
                
                # Consolidate all threats into a single agent analysis entry
                consolidated = self._consolidate_agent_findings(pkg_name, pkg_threats)
                packages_dict[pkg_name]["agent_analysis"] = consolidated
                
                # Also add as a single finding for UI compatibility
                packages_dict[pkg_name]["findings"].append({
                    "type": "agent_security_analysis",
                    "severity": consolidated["highest_severity"],
                    "description": consolidated["summary"],
                    "confidence": consolidated["confidence"],
                    "evidence": {
                        "source": "supply_chain_agent",
                        "details": consolidated["key_findings"]
                    },
                    "remediation": "; ".join(consolidated["recommendations"][:3])
                })
        
        # Calculate risk scores for all packages
        packages_list = []
        for pkg_name, package_entry in packages_dict.items():
            risk_score = 0.0
            for finding in package_entry["findings"]:
                severity_weight = {
                    "critical": 1.0,
                    "high": 0.7,
                    "medium": 0.4,
                    "low": 0.2
                }
                weight = severity_weight.get(finding["severity"].lower(), 0.2)
                confidence = finding.get("confidence", 0.8)
                risk_score += weight * confidence
            
            package_entry["risk_score"] = min(1.0, risk_score)
            
            # Determine risk level
            if package_entry["risk_score"] >= 0.8:
                package_entry["risk_level"] = "critical"
            elif package_entry["risk_score"] >= 0.6:
                package_entry["risk_level"] = "high"
            elif package_entry["risk_score"] >= 0.3:
                package_entry["risk_level"] = "medium"
            else:
                package_entry["risk_level"] = "low"
            
            packages_list.append(package_entry)
        
        return {
            "packages": packages_list
        }
    
    def _consolidate_agent_findings(
        self, 
        pkg_name: str, 
        threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Consolidate multiple agent findings into a single user-friendly summary.
        
        Args:
            pkg_name: Package name
            threats: List of threat dictionaries from supply chain detector
        
        Returns:
            Consolidated analysis dictionary
        """
        if not threats:
            return {
                "summary": "No security issues detected by agent analysis",
                "highest_severity": "low",
                "confidence": 1.0,
                "key_findings": [],
                "sources_checked": [],
                "recommendations": [],
                "references": []
            }
        
        # Determine highest severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        highest_severity = "low"
        for threat in threats:
            threat_sev = threat.get("severity", "low").lower()
            if severity_order.get(threat_sev, 0) > severity_order.get(highest_severity, 0):
                highest_severity = threat_sev
        
        # Collect unique sources
        sources = set()
        for threat in threats:
            sources.add(threat.get("source", "Unknown"))
        
        # Collect unique CVEs and advisory IDs
        cves = set()
        advisories = set()
        references = []
        for threat in threats:
            evidence = threat.get("evidence", {})
            if isinstance(evidence, dict):
                if evidence.get("cve_id"):
                    cves.add(evidence["cve_id"])
                if evidence.get("ghsa_id"):
                    advisories.add(evidence["ghsa_id"])
                if evidence.get("url"):
                    references.append(evidence["url"])
        
        # Build key findings (unique, important ones)
        key_findings = []
        seen_descriptions = set()
        
        # Prioritize security advisories and vulnerabilities
        for threat in sorted(threats, key=lambda t: severity_order.get(t.get("severity", "low"), 0), reverse=True):
            desc = threat.get("description", "")
            threat_type = threat.get("threat_type", "")
            
            # Skip duplicates and generic web intelligence
            if desc in seen_descriptions:
                continue
            if threat_type == "web_intelligence" and len(key_findings) >= 3:
                continue  # Limit web intelligence entries
            
            seen_descriptions.add(desc)
            
            if threat_type == "security_advisory":
                key_findings.append(f"⚠️ {desc}")
            elif threat_type == "vulnerability":
                key_findings.append(f"🔴 {desc}")
            else:
                key_findings.append(f"ℹ️ {desc}")
            
            if len(key_findings) >= 5:
                break
        
        # Build recommendations (unique)
        recommendations = []
        seen_recs = set()
        for threat in threats:
            for rec in threat.get("recommendations", []):
                if rec not in seen_recs and len(recommendations) < 3:
                    seen_recs.add(rec)
                    recommendations.append(rec)
        
        # Calculate average confidence
        avg_confidence = sum(t.get("confidence", 0.8) for t in threats) / len(threats)
        
        # Build summary
        advisory_count = len([t for t in threats if t.get("threat_type") == "security_advisory"])
        vuln_count = len([t for t in threats if t.get("threat_type") == "vulnerability"])
        
        summary_parts = []
        if advisory_count > 0:
            summary_parts.append(f"{advisory_count} security advisor{'y' if advisory_count == 1 else 'ies'}")
        if vuln_count > 0:
            summary_parts.append(f"{vuln_count} vulnerabilit{'y' if vuln_count == 1 else 'ies'}")
        if cves:
            summary_parts.append(f"{len(cves)} CVE{'s' if len(cves) > 1 else ''}")
        
        if summary_parts:
            summary = f"Found {', '.join(summary_parts)} affecting {pkg_name}"
        else:
            summary = f"Security analysis completed for {pkg_name}"
        
        return {
            "summary": summary,
            "highest_severity": highest_severity,
            "confidence": round(avg_confidence, 2),
            "total_issues": len(threats),
            "advisory_count": advisory_count,
            "vulnerability_count": vuln_count,
            "cve_count": len(cves),
            "cves": list(cves)[:5],  # Top 5 CVEs
            "key_findings": key_findings,
            "sources_checked": list(sources),
            "recommendations": recommendations,
            "references": list(set(references))[:5]  # Top 5 unique references
        }
    
    def _extract_supply_chain_data(self, context: SharedContext) -> Dict[str, Any]:
        """
        Extract supply chain analysis data from agent results.
        
        Args:
            context: Shared context
        
        Returns:
            Supply chain analysis data (empty dict if not available)
        """
        sc_result = context.get_agent_result("SupplyChainAttackAgent")
        if sc_result and sc_result.success:
            return sc_result.data
        return {}
    
    def _extract_code_analysis_data(self, context: SharedContext) -> Dict[str, Any]:
        """
        Extract code analysis data from agent results.
        
        Args:
            context: Shared context
        
        Returns:
            Code analysis data (empty dict if not available)
        """
        code_result = context.get_agent_result("CodeAnalysisAgent")
        if code_result and code_result.success:
            return code_result.data
        return {}

    def _get_supply_chain_detector_data(self, context: SharedContext) -> Dict[str, Any]:
        """
        Extract supply chain detector results for the report.
        
        Args:
            context: Shared context with agent results
        
        Returns:
            Supply chain detector data for JSON report
        """
        sc_result = context.get_agent_result("supply_chain_detector")
        
        if not sc_result or not sc_result.success:
            return {}
        
        data = sc_result.data
        threats = data.get("threats_detected", [])
        
        # Format threats for UI display
        formatted_threats = []
        for threat in threats:
            formatted_threats.append({
                "package_name": threat.get("package_name"),
                "package_version": threat.get("package_version", "*"),
                "ecosystem": threat.get("ecosystem"),
                "threat_type": threat.get("threat_type"),
                "severity": threat.get("severity"),
                "confidence": threat.get("confidence"),
                "source": threat.get("source"),
                "description": threat.get("description"),
                "evidence": threat.get("evidence", {}),
                "recommendations": threat.get("recommendations", [])
            })
        
        return {
            "risk_level": data.get("risk_level", "unknown"),
            "total_packages_checked": data.get("total_packages_checked", 0),
            "total_threats_found": data.get("total_threats_found", 0),
            "malicious_packages_found": data.get("malicious_packages_found", 0),
            "vulnerabilities_found": data.get("vulnerabilities_found", 0),
            "web_intelligence_found": data.get("web_intelligence_found", 0),
            "critical_severity_count": data.get("critical_severity_count", 0),
            "high_severity_count": data.get("high_severity_count", 0),
            "confidence": data.get("confidence", 0),
            "duration_seconds": data.get("duration_seconds", 0),
            "threats": formatted_threats
        }
    
    def _get_supply_chain_detector_summary(self, context: SharedContext) -> Dict[str, Any]:
        """
        Get summary of supply chain detector for agent_insights.
        
        Args:
            context: Shared context
        
        Returns:
            Summary dict for agent_insights
        """
        sc_result = context.get_agent_result("supply_chain_detector")
        
        if not sc_result or not sc_result.success:
            return {"status": "not_run", "reason": "Agent not executed"}
        
        data = sc_result.data
        return {
            "status": "completed",
            "risk_level": data.get("risk_level", "unknown"),
            "total_threats": data.get("total_threats_found", 0),
            "malicious_packages": data.get("malicious_packages_found", 0),
            "web_intelligence": data.get("web_intelligence_found", 0),
            "sources_checked": ["GitHub Advisories", "Snyk", "NVD", "CVE Details"]
        }
