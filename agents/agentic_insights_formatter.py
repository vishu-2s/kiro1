"""
Agentic Insights Formatter - Capture and Display AI-Powered Analysis.

This module ensures that all LLM-powered agentic reasoning, analysis, and insights
are prominently captured and displayed in the final report.

Philosophy: "Show the intelligence - make AI analysis visible and actionable"
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from agents.safe_types import SafeDict, SafeSharedContext

logger = logging.getLogger(__name__)


@dataclass
class AgenticInsight:
    """
    Single agentic insight from LLM analysis.
    
    Captures reasoning, analysis, and recommendations from AI agents.
    """
    agent_name: str
    package_name: str
    insight_type: str  # vulnerability_analysis, reputation_analysis, code_analysis
    
    # AI-Generated Content
    assessment: str = ""
    reasoning: str = ""
    risk_score: Optional[float] = None
    confidence: float = 0.0
    
    # Specific Insights
    exploitation_likelihood: Optional[str] = None
    business_impact: Optional[str] = None
    trust_assessment: Optional[str] = None
    supply_chain_risk: Optional[str] = None
    code_quality_assessment: Optional[str] = None
    
    # Recommendations
    recommended_action: Optional[str] = None
    key_concerns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_name": self.agent_name,
            "package_name": self.package_name,
            "insight_type": self.insight_type,
            "assessment": self.assessment,
            "reasoning": self.reasoning,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "exploitation_likelihood": self.exploitation_likelihood,
            "business_impact": self.business_impact,
            "trust_assessment": self.trust_assessment,
            "supply_chain_risk": self.supply_chain_risk,
            "code_quality_assessment": self.code_quality_assessment,
            "recommended_action": self.recommended_action,
            "key_concerns": self.key_concerns
        }


class AgenticInsightsFormatter:
    """
    Extracts and formats AI-powered agentic insights from agent results.
    
    Ensures that all LLM analysis is visible and actionable in the final report.
    """
    
    def extract_agentic_insights(self, context: SafeSharedContext) -> Dict[str, Any]:
        """
        Extract all agentic insights from agent results.
        
        Args:
            context: Shared context with agent results
        
        Returns:
            Dictionary with all agentic insights organized by type
        """
        logger.info("Extracting agentic insights from agent results...")
        
        insights = {
            "vulnerability_insights": self._extract_vulnerability_insights(context),
            "reputation_insights": self._extract_reputation_insights(context),
            "code_insights": self._extract_code_insights(context),
            "supply_chain_insights": self._extract_supply_chain_insights(context),
            "synthesis_insights": self._extract_synthesis_insights(context),
            "overall_assessment": self._generate_overall_assessment(context)
        }
        
        # Count insights
        total_insights = sum(len(v) for v in insights.values() if isinstance(v, list))
        logger.info(f"Extracted {total_insights} agentic insights")
        
        return insights
    
    def _extract_vulnerability_insights(self, context: SafeSharedContext) -> List[Dict[str, Any]]:
        """Extract LLM-powered vulnerability analysis insights"""
        insights = []
        
        vuln_result = context.get_agent_result("vulnerability_analysis")
        if not vuln_result or not vuln_result.success:
            return insights
        
        for pkg in vuln_result.get_packages():
            pkg_name = pkg.safe_str("package_name", "unknown")
            
            # Check for LLM assessment
            llm_assessment = pkg.safe_dict("llm_assessment")
            if llm_assessment and llm_assessment.get("assessment"):
                insight = AgenticInsight(
                    agent_name="vulnerability_analysis",
                    package_name=pkg_name,
                    insight_type="vulnerability_analysis",
                    assessment=llm_assessment.safe_str("assessment", ""),
                    risk_score=llm_assessment.safe_float("risk_score"),
                    exploitation_likelihood=llm_assessment.safe_str("exploitation_likelihood"),
                    business_impact=llm_assessment.safe_str("business_impact"),
                    recommended_action=llm_assessment.safe_str("recommended_action"),
                    key_concerns=llm_assessment.safe_list("key_concerns", []),
                    confidence=llm_assessment.safe_float("confidence", 0.8)
                )
                insights.append(insight.to_dict())
        
        return insights
    
    def _extract_reputation_insights(self, context: SafeSharedContext) -> List[Dict[str, Any]]:
        """Extract LLM-powered reputation analysis insights"""
        insights = []
        
        rep_result = context.get_agent_result("reputation_analysis")
        if not rep_result or not rep_result.success:
            return insights
        
        for pkg in rep_result.get_packages():
            pkg_name = pkg.safe_str("package_name", "unknown")
            
            # Check for LLM reputation analysis
            llm_rep = pkg.safe_dict("llm_reputation_analysis")
            if llm_rep and llm_rep.get("trust_assessment"):
                insight = AgenticInsight(
                    agent_name="reputation_analysis",
                    package_name=pkg_name,
                    insight_type="reputation_analysis",
                    assessment=llm_rep.safe_str("trust_assessment", ""),
                    reasoning=llm_rep.safe_str("reasoning", ""),
                    risk_score=llm_rep.safe_float("trust_score"),
                    trust_assessment=llm_rep.safe_str("trust_assessment"),
                    supply_chain_risk=llm_rep.safe_str("supply_chain_risk"),
                    recommended_action=llm_rep.safe_str("enterprise_recommendation"),
                    key_concerns=llm_rep.safe_list("key_concerns", []),
                    confidence=0.85
                )
                insights.append(insight.to_dict())
        
        return insights
    
    def _extract_code_insights(self, context: SafeSharedContext) -> List[Dict[str, Any]]:
        """Extract LLM-powered code analysis insights"""
        insights = []
        
        code_result = context.get_agent_result("code_analysis")
        if not code_result or not code_result.success:
            return insights
        
        for pkg in code_result.get_packages():
            pkg_name = pkg.safe_str("package_name", "unknown")
            
            # Check for LLM code analysis
            llm_analysis = pkg.safe_dict("llm_analysis")
            if llm_analysis and llm_analysis.get("overall_assessment"):
                insight = AgenticInsight(
                    agent_name="code_analysis",
                    package_name=pkg_name,
                    insight_type="code_analysis",
                    assessment=llm_analysis.safe_str("overall_assessment", ""),
                    risk_score=llm_analysis.safe_float("confidence"),
                    code_quality_assessment=llm_analysis.safe_str("overall_assessment"),
                    key_concerns=llm_analysis.safe_list("suspicious_patterns", []),
                    confidence=llm_analysis.safe_float("confidence", 0.8)
                )
                insights.append(insight.to_dict())
        
        return insights
    
    def _extract_supply_chain_insights(self, context: SafeSharedContext) -> List[Dict[str, Any]]:
        """Extract supply chain analysis insights"""
        insights = []
        
        sc_result = context.get_agent_result("supply_chain_analysis")
        if not sc_result or not sc_result.success:
            return insights
        
        # Supply chain agent may have overall insights
        data = sc_result.data
        if data.safe_str("overall_assessment"):
            insight = {
                "agent_name": "supply_chain_analysis",
                "insight_type": "supply_chain_analysis",
                "assessment": data.safe_str("overall_assessment"),
                "confidence": data.safe_float("confidence", 0.8)
            }
            insights.append(insight)
        
        return insights
    
    def _extract_synthesis_insights(self, context: SafeSharedContext) -> Dict[str, Any]:
        """Extract synthesis agent insights"""
        synthesis_result = context.get_agent_result("synthesis")
        if not synthesis_result or not synthesis_result.success:
            return {}
        
        data = synthesis_result.data
        return {
            "synthesis_method": data.safe_str("synthesis_method", "unknown"),
            "overall_assessment": data.safe_str("overall_assessment", ""),
            "confidence": data.safe_float("confidence", 0.0)
        }
    
    def _generate_overall_assessment(self, context: SafeSharedContext) -> Dict[str, Any]:
        """Generate overall AI-powered assessment"""
        
        # Count insights by type
        vuln_insights = len(self._extract_vulnerability_insights(context))
        rep_insights = len(self._extract_reputation_insights(context))
        code_insights = len(self._extract_code_insights(context))
        
        # Determine if AI analysis was used
        ai_analysis_used = vuln_insights > 0 or rep_insights > 0 or code_insights > 0
        
        assessment = {
            "ai_analysis_used": ai_analysis_used,
            "total_ai_insights": vuln_insights + rep_insights + code_insights,
            "vulnerability_ai_insights": vuln_insights,
            "reputation_ai_insights": rep_insights,
            "code_ai_insights": code_insights,
            "analysis_quality": "high" if ai_analysis_used else "basic"
        }
        
        if ai_analysis_used:
            assessment["note"] = "🤖 AI-powered analysis provided enhanced insights and recommendations"
        else:
            assessment["note"] = "Analysis based on rule-based detection and API data"
        
        return assessment


def add_agentic_insights_to_report(report: Dict[str, Any], context: SafeSharedContext) -> Dict[str, Any]:
    """
    Add agentic insights section to report.
    
    Args:
        report: Existing report dictionary
        context: Shared context with agent results
    
    Returns:
        Enhanced report with agentic insights
    """
    formatter = AgenticInsightsFormatter()
    agentic_insights = formatter.extract_agentic_insights(context)
    
    # Add to report
    report["agentic_insights"] = agentic_insights
    
    # Update metadata to indicate AI analysis
    if "metadata" in report:
        report["metadata"]["ai_analysis_used"] = agentic_insights["overall_assessment"]["ai_analysis_used"]
        report["metadata"]["total_ai_insights"] = agentic_insights["overall_assessment"]["total_ai_insights"]
    
    return report
