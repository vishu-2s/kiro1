"""
Comprehensive error handling and graceful degradation for multi-agent security analysis.

This module provides centralized error handling with retry logic, exponential backoff,
fallback data generation, and graceful degradation levels for the agent orchestrator.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from agents.types import AgentResult, AgentStatus, SharedContext, Finding


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Analysis degradation levels based on agent success rate."""
    FULL = "full"           # 100% - All agents succeeded
    PARTIAL = "partial"     # 70-99% - Some optional agents failed
    BASIC = "basic"         # 40-69% - Only required agents succeeded
    MINIMAL = "minimal"     # <40% - Only rule-based detection


class ErrorType(Enum):
    """Types of errors that can occur during analysis."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit_exceeded"
    CONNECTION = "connection_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_RESPONSE = "invalid_response"
    AUTHENTICATION = "authentication_error"
    UNKNOWN = "unknown"


class ErrorHandler:
    """
    Centralized error handling for agent orchestration.
    
    Provides:
    - Retry logic with exponential backoff
    - Fallback data generation for failed agents
    - Graceful degradation level calculation
    - User-friendly error messages
    """
    
    # Retryable error patterns
    RETRYABLE_PATTERNS = [
        "rate",
        "limit",
        "timeout",
        "connection",
        "service_unavailable",
        "503",
        "429",
        "502",
        "504"
    ]
    
    def __init__(self, max_retries: int = 2, base_delay: float = 1.0):
        """
        Initialize error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_log: List[Dict[str, Any]] = []
    
    def handle_agent_failure(
        self,
        agent_name: str,
        error: Exception,
        required: bool,
        retry_func: Optional[Callable] = None,
        duration: float = 0.0
    ) -> AgentResult:
        """
        Handle agent failure with appropriate fallback strategy.
        
        Strategy:
        1. Log error with full context
        2. Determine if failure is retryable
        3. Retry with exponential backoff if applicable
        4. If still failing, use fallback data
        5. Mark result as partial/degraded
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that occurred
            required: Whether this agent is required
            retry_func: Optional function to retry the agent
            duration: Time spent before failure
        
        Returns:
            AgentResult with fallback data or empty result
        """
        error_type = self._classify_error(error)
        error_msg = str(error)
        
        # Log error
        logger.error(
            f"Agent {agent_name} failed: {error_msg}",
            extra={
                "agent": agent_name,
                "error_type": error_type.value,
                "required": required,
                "duration": duration
            },
            exc_info=True
        )
        
        # Attempt retry if error is retryable and retry function provided
        if retry_func and self._is_retryable_error(error):
            logger.info(f"Attempting retry for {agent_name} (retryable error detected)")
            retry_result = self._retry_with_backoff(agent_name, retry_func)
            if retry_result is not None:
                return retry_result
        
        # Generate fallback result
        if required:
            logger.warning(f"Using fallback data for required agent: {agent_name}")
            fallback_data = self._get_fallback_data(agent_name)
            status = AgentStatus.FAILED
        else:
            logger.info(f"Skipping optional agent: {agent_name}")
            fallback_data = {"packages": [], "skipped": True}
            status = AgentStatus.SKIPPED
        
        # Record error for reporting (after determining if required)
        self.error_log.append({
            "agent": agent_name,
            "error": error_msg,
            "error_type": error_type.value,
            "required": required,
            "timestamp": time.time()
        })
        
        return AgentResult(
            agent_name=agent_name,
            success=False,
            data=fallback_data,
            error=self._format_user_friendly_error(agent_name, error, error_type),
            duration_seconds=duration,
            status=status
        )
    
    def handle_synthesis_failure(
        self,
        context: SharedContext,
        error: Exception
    ) -> Dict[str, Any]:
        """
        Handle synthesis failure by generating fallback report from raw data.
        
        Fallback strategy:
        1. Extract findings from agent results
        2. Generate basic summary statistics
        3. Create minimal recommendations
        4. Mark report as partial
        
        Args:
            context: Shared context with agent results
            error: Exception that occurred during synthesis
        
        Returns:
            Fallback report structure
        """
        logger.error(f"Synthesis failed: {str(error)}", exc_info=True)
        
        # Extract and merge findings from successful agents by package name
        packages_dict = {}
        successful_agents = []
        
        for agent_name, result in context.agent_results.items():
            if result.success:
                successful_agents.append(agent_name)
                # Extract findings from agent data
                agent_packages = result.data.get("packages", [])
                
                # Merge packages by name
                for pkg in agent_packages:
                    pkg_name = pkg.get("package_name", "unknown")
                    
                    if pkg_name not in packages_dict:
                        # Initialize package entry
                        packages_dict[pkg_name] = {
                            "package_name": pkg_name,
                            "package_version": pkg.get("package_version", "unknown"),
                            "ecosystem": pkg.get("ecosystem", context.ecosystem if hasattr(context, 'ecosystem') else "unknown")
                        }
                    
                    # Merge vulnerability data
                    if "vulnerabilities" in pkg:
                        packages_dict[pkg_name]["vulnerabilities"] = pkg["vulnerabilities"]
                        packages_dict[pkg_name]["vulnerability_count"] = pkg.get("vulnerability_count", len(pkg["vulnerabilities"]))
                    
                    # Merge reputation data
                    if "reputation_score" in pkg:
                        packages_dict[pkg_name]["reputation_score"] = pkg["reputation_score"]
                        packages_dict[pkg_name]["risk_level"] = pkg.get("risk_level", "unknown")
                        packages_dict[pkg_name]["risk_factors"] = pkg.get("risk_factors", [])
                    
                    # Merge code analysis data
                    if "code_issues" in pkg:
                        packages_dict[pkg_name]["code_issues"] = pkg["code_issues"]
                    
                    # Merge supply chain data
                    if "supply_chain_risks" in pkg:
                        packages_dict[pkg_name]["supply_chain_risks"] = pkg["supply_chain_risks"]
        
        # Convert dict to list
        all_findings = list(packages_dict.values())
        
        # Calculate summary statistics from vulnerabilities
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        
        for pkg in all_findings:
            if isinstance(pkg, dict):
                # Count vulnerabilities by severity
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
        
        # Generate fallback report
        return {
            "metadata": {
                "analysis_id": f"analysis_{int(time.time())}",
                "analysis_type": "partial",
                "analysis_status": "degraded",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": "Synthesis agent failed - using fallback report",
                "degradation_reason": str(error),
                "retry_recommended": True
            },
            "summary": {
                "total_packages": len(context.packages),
                "packages_analyzed": len(all_findings),
                "critical_findings": critical_count,
                "high_findings": high_count,
                "medium_findings": medium_count,
                "low_findings": low_count,
                "status": "partial",
                "confidence": self._calculate_confidence(context)
            },
            "security_findings": {
                "packages": all_findings
            },
            "recommendations": self._generate_smart_recommendations(all_findings, context),
            "agent_insights": {
                "error": "Synthesis failed - partial results only",
                "successful_agents": successful_agents,
                "failed_agents": [
                    name for name, result in context.agent_results.items()
                    if not result.success
                ],
                "degradation_level": self.calculate_degradation_level(context).value,
                "agent_details": {
                    agent_name: {
                        "success": result.success,
                        "duration_seconds": result.duration_seconds,
                        "confidence": result.confidence,
                        "packages_analyzed": result.data.get("total_packages_analyzed", 0) if result.success else 0,
                        "findings_count": len(result.data.get("packages", [])) if result.success else 0,
                        "error": result.error if not result.success else None
                    }
                    for agent_name, result in context.agent_results.items()
                }
            },
            "dependency_graph": context.dependency_graph if hasattr(context, 'dependency_graph') else {}
        }
    
    def calculate_degradation_level(self, context: SharedContext) -> DegradationLevel:
        """
        Calculate the degradation level based on agent success rate.
        
        Levels:
        - FULL (100%): All agents succeeded
        - PARTIAL (70-99%): Some optional agents failed
        - BASIC (40-69%): Only required agents succeeded
        - MINIMAL (<40%): Only rule-based detection
        
        Args:
            context: Shared context with agent results
        
        Returns:
            DegradationLevel enum value
        """
        if not context.agent_results:
            return DegradationLevel.MINIMAL
        
        total_agents = len(context.agent_results)
        successful_agents = sum(
            1 for result in context.agent_results.values()
            if result.success
        )
        
        success_rate = successful_agents / total_agents if total_agents > 0 else 0.0
        
        if success_rate >= 1.0:
            return DegradationLevel.FULL
        elif success_rate > 0.69:  # 70% threshold (exclusive)
            return DegradationLevel.PARTIAL
        elif success_rate >= 0.4:
            return DegradationLevel.BASIC
        else:
            return DegradationLevel.MINIMAL
    
    def _generate_smart_recommendations(
        self, 
        packages: List[Dict[str, Any]], 
        context: SharedContext
    ) -> Dict[str, List[str]]:
        """
        Generate intelligent recommendations based on actual findings.
        
        Args:
            packages: List of packages with merged agent data
            context: Shared context
        
        Returns:
            Dictionary with immediate_actions, preventive_measures, and monitoring
        """
        immediate_actions = []
        preventive_measures = []
        monitoring = []
        
        # Analyze vulnerabilities
        critical_vulns = []
        high_vulns = []
        outdated_packages = []
        
        for pkg in packages:
            pkg_name = pkg.get("package_name", "unknown")
            vulns = pkg.get("vulnerabilities", [])
            
            for vuln in vulns:
                severity = vuln.get("severity", "").lower()
                if severity == "critical":
                    critical_vulns.append((pkg_name, vuln))
                elif severity == "high":
                    high_vulns.append((pkg_name, vuln))
                
                # Check if fix is available
                if vuln.get("fixed_versions") and vuln.get("is_current_version_affected"):
                    outdated_packages.append((pkg_name, pkg.get("package_version"), vuln.get("fixed_versions")))
        
        # Analyze reputation
        high_risk_packages = []
        abandoned_packages = []
        unknown_authors = []
        
        for pkg in packages:
            pkg_name = pkg.get("package_name", "unknown")
            risk_level = pkg.get("risk_level", "").lower()
            risk_factors = pkg.get("risk_factors", [])
            
            if risk_level in ["high", "critical"]:
                high_risk_packages.append(pkg_name)
            
            for factor in risk_factors:
                if factor.get("type") == "abandoned":
                    abandoned_packages.append(pkg_name)
                elif factor.get("type") == "unknown_author":
                    unknown_authors.append(pkg_name)
        
        # Generate immediate actions
        if critical_vulns:
            immediate_actions.append(
                f"🚨 CRITICAL: {len(critical_vulns)} critical vulnerabilities found. "
                f"Affected packages: {', '.join(set(v[0] for v in critical_vulns[:3]))}{'...' if len(critical_vulns) > 3 else ''}. "
                "Update or remove these packages immediately."
            )
        
        if high_vulns:
            immediate_actions.append(
                f"⚠️ HIGH PRIORITY: {len(high_vulns)} high-severity vulnerabilities detected. "
                f"Review and patch within 24-48 hours."
            )
        
        if outdated_packages:
            unique_outdated = list(set(p[0] for p in outdated_packages))
            immediate_actions.append(
                f"📦 UPDATE REQUIRED: {len(unique_outdated)} packages have security fixes available. "
                f"Update: {', '.join(unique_outdated[:5])}{'...' if len(unique_outdated) > 5 else ''}"
            )
        
        if high_risk_packages:
            immediate_actions.append(
                f"🔍 REVIEW NEEDED: {len(high_risk_packages)} packages have low reputation scores. "
                f"Verify legitimacy: {', '.join(high_risk_packages[:3])}{'...' if len(high_risk_packages) > 3 else ''}"
            )
        
        if abandoned_packages:
            immediate_actions.append(
                f"⚠️ MAINTENANCE RISK: {len(abandoned_packages)} packages appear abandoned. "
                f"Consider alternatives for: {', '.join(abandoned_packages[:3])}{'...' if len(abandoned_packages) > 3 else ''}"
            )
        
        # If synthesis failed, add note
        if not immediate_actions:
            immediate_actions.append("✓ No critical issues detected in automated analysis")
        
        immediate_actions.insert(0, "⚠️ Note: Synthesis agent failed - recommendations based on available data")
        
        # Generate preventive measures
        preventive_measures.extend([
            "🔒 Implement automated dependency scanning in CI/CD pipeline",
            "📋 Use lock files (package-lock.json, requirements.txt) to ensure reproducible builds",
            "🔄 Set up automated security alerts for your dependencies",
            "📊 Regularly audit dependencies and remove unused packages",
            "🛡️ Use Software Bill of Materials (SBOM) for supply chain visibility"
        ])
        
        if unknown_authors:
            preventive_measures.append(
                "👤 Establish package vetting process for packages from unknown authors"
            )
        
        if len(packages) > 50:
            preventive_measures.append(
                "📉 Consider reducing dependency count to minimize attack surface"
            )
        
        # Generate monitoring recommendations
        monitoring.extend([
            "📡 Monitor security advisories for your dependencies (GitHub Security Advisories, OSV)",
            "🔔 Enable Dependabot or Renovate for automated dependency updates",
            "📈 Track dependency health metrics (age, maintenance, popularity)",
            "🔍 Regularly re-run security analysis (weekly or on each commit)"
        ])
        
        if critical_vulns or high_vulns:
            monitoring.append(
                "🚨 Set up real-time alerts for critical/high severity vulnerabilities"
            )
        
        if high_risk_packages:
            monitoring.append(
                "👁️ Monitor low-reputation packages for suspicious updates or behavior"
            )
        
        return {
            "immediate_actions": immediate_actions,
            "preventive_measures": preventive_measures,
            "monitoring": monitoring
        }
    
    def get_degradation_metadata(self, context: SharedContext) -> Dict[str, Any]:
        """
        Get metadata about analysis degradation for inclusion in report.
        
        Args:
            context: Shared context with agent results
        
        Returns:
            Dictionary with degradation metadata
        """
        degradation_level = self.calculate_degradation_level(context)
        confidence = self._calculate_confidence(context)
        
        failed_agents = [
            name for name, result in context.agent_results.items()
            if not result.success
        ]
        
        missing_analysis = []
        for agent_name, result in context.agent_results.items():
            if not result.success:
                if agent_name == "vulnerability_analysis":
                    missing_analysis.append("Vulnerability Analysis")
                elif agent_name == "reputation_analysis":
                    missing_analysis.append("Reputation Analysis")
                elif agent_name == "code_analysis":
                    missing_analysis.append("Code Analysis")
                elif agent_name == "supply_chain_analysis":
                    missing_analysis.append("Supply Chain Analysis")
        
        return {
            "analysis_status": degradation_level.value,
            "confidence": confidence,
            "degradation_reason": self._get_degradation_reason(failed_agents),
            "missing_analysis": missing_analysis,
            "retry_recommended": len(failed_agents) > 0,
            "error_summary": self._get_error_summary()
        }
    
    def _retry_with_backoff(
        self,
        agent_name: str,
        retry_func: Callable
    ) -> Optional[AgentResult]:
        """
        Retry agent execution with exponential backoff.
        
        Args:
            agent_name: Name of the agent to retry
            retry_func: Function to call for retry
        
        Returns:
            AgentResult if retry succeeds, None otherwise
        """
        for attempt in range(self.max_retries):
            delay = self.base_delay * (2 ** attempt)  # Exponential backoff
            logger.info(
                f"Retrying {agent_name} (attempt {attempt + 1}/{self.max_retries}) "
                f"after {delay}s delay"
            )
            time.sleep(delay)
            
            try:
                result = retry_func()
                if result and result.success:
                    logger.info(f"Retry successful for {agent_name}")
                    return result
            except Exception as retry_error:
                logger.warning(
                    f"Retry {attempt + 1} failed for {agent_name}: {str(retry_error)}"
                )
        
        logger.error(f"All retries exhausted for {agent_name}")
        return None
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error type for appropriate handling.
        
        Args:
            error: Exception to classify
        
        Returns:
            ErrorType enum value
        """
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return ErrorType.TIMEOUT
        elif "rate" in error_str and "limit" in error_str:
            return ErrorType.RATE_LIMIT
        elif "connection" in error_str or "network" in error_str:
            return ErrorType.CONNECTION
        elif "503" in error_str or "unavailable" in error_str:
            return ErrorType.SERVICE_UNAVAILABLE
        elif "invalid" in error_str or "malformed" in error_str:
            return ErrorType.INVALID_RESPONSE
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            return ErrorType.AUTHENTICATION
        else:
            return ErrorType.UNKNOWN
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if error is retryable.
        
        Args:
            error: Exception to check
        
        Returns:
            True if error is retryable, False otherwise
        """
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in self.RETRYABLE_PATTERNS)
    
    def _get_fallback_data(self, agent_name: str) -> Dict[str, Any]:
        """
        Get fallback data for a failed agent.
        
        Args:
            agent_name: Name of the failed agent
        
        Returns:
            Fallback data structure
        """
        if agent_name == "vulnerability_analysis":
            return {
                "packages": [],
                "source": "rule_based_fallback",
                "note": "Using rule-based vulnerability detection only",
                "fallback": True
            }
        elif agent_name == "reputation_analysis":
            return {
                "packages": [],
                "source": "default_scores",
                "note": "Using default reputation scores (0.5 neutral)",
                "fallback": True
            }
        elif agent_name == "code_analysis":
            return {
                "packages": [],
                "source": "pattern_matching_only",
                "note": "Using pattern matching only, no LLM analysis",
                "fallback": True
            }
        elif agent_name == "supply_chain_analysis":
            return {
                "packages": [],
                "source": "basic_checks_only",
                "note": "Using basic supply chain checks only",
                "fallback": True
            }
        else:
            return {
                "packages": [],
                "source": "fallback",
                "note": f"Agent {agent_name} failed, using fallback data",
                "fallback": True
            }
    
    def _format_user_friendly_error(
        self,
        agent_name: str,
        error: Exception,
        error_type: ErrorType
    ) -> str:
        """
        Format error message for user display.
        
        Args:
            agent_name: Name of the failed agent
            error: Original exception
            error_type: Classified error type
        
        Returns:
            User-friendly error message
        """
        agent_display_name = agent_name.replace("_", " ").title()
        
        if error_type == ErrorType.TIMEOUT:
            return f"{agent_display_name} timed out. Analysis may be incomplete."
        elif error_type == ErrorType.RATE_LIMIT:
            return f"{agent_display_name} hit rate limit. Please try again later."
        elif error_type == ErrorType.CONNECTION:
            return f"{agent_display_name} connection failed. Check network connectivity."
        elif error_type == ErrorType.SERVICE_UNAVAILABLE:
            return f"{agent_display_name} service unavailable. Please try again later."
        elif error_type == ErrorType.INVALID_RESPONSE:
            return f"{agent_display_name} received invalid response. Data may be incomplete."
        elif error_type == ErrorType.AUTHENTICATION:
            return f"{agent_display_name} authentication failed. Check API credentials."
        else:
            return f"{agent_display_name} encountered an error: {str(error)[:100]}"
    
    def _calculate_confidence(self, context: SharedContext) -> float:
        """
        Calculate overall confidence score based on agent success.
        
        Args:
            context: Shared context with agent results
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        degradation_level = self.calculate_degradation_level(context)
        
        # Base confidence on degradation level
        if degradation_level == DegradationLevel.FULL:
            return 0.95
        elif degradation_level == DegradationLevel.PARTIAL:
            return 0.75
        elif degradation_level == DegradationLevel.BASIC:
            return 0.55
        else:
            return 0.35
    
    def _get_degradation_reason(self, failed_agents: List[str]) -> str:
        """
        Get human-readable degradation reason.
        
        Args:
            failed_agents: List of failed agent names
        
        Returns:
            Degradation reason string
        """
        if not failed_agents:
            return "All agents completed successfully"
        
        agent_names = [name.replace("_", " ").title() for name in failed_agents]
        
        if len(agent_names) == 1:
            return f"{agent_names[0]} failed"
        elif len(agent_names) == 2:
            return f"{agent_names[0]} and {agent_names[1]} failed"
        else:
            return f"{', '.join(agent_names[:-1])}, and {agent_names[-1]} failed"
    
    def _get_error_summary(self) -> List[Dict[str, str]]:
        """
        Get summary of all errors encountered.
        
        Returns:
            List of error summaries
        """
        return [
            {
                "agent": error["agent"],
                "error": error["error"][:200],  # Truncate long errors
                "type": error["error_type"]
            }
            for error in self.error_log
        ]
    
    def clear_error_log(self) -> None:
        """Clear the error log."""
        self.error_log.clear()
