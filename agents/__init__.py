"""
Multi-Agent Security Analysis System - Agents Module

This module contains the specialized AI agents for security analysis:
- SupplyChainAgent: Dependency analysis and malicious package detection
- VlmSecurityAgent: Visual security analysis using GPT-4 Vision
- OrchestratorAgent: Findings correlation and incident reporting
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent Security Analysis System"

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import openai
from config import config
from constants import (
    KNOWN_MALICIOUS_PACKAGES, TYPOSQUAT_TARGETS, SUSPICIOUS_KEYWORDS,
    is_suspicious_package_name, contains_suspicious_keywords,
    calculate_typosquat_confidence, detect_suspicious_network_patterns
)

class BaseAgent:
    """Base class for all security analysis agents."""
    
    def __init__(self, name: str, role: str, llm_config: Optional[Dict] = None):
        self.name = name
        self.role = role
        self.llm_config = llm_config or config.get_llm_config()
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.conversation_history: List[Dict[str, str]] = []
        
    def send_message(self, message: str, message_type: str = "analysis") -> Dict[str, Any]:
        """Send a message and get response from the agent."""
        try:
            # Add message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "message_type": message_type
            })
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.llm_config["config_list"][0]["model"],
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": message}
                ],
                temperature=self.llm_config["config_list"][0]["temperature"],
                max_tokens=self.llm_config["config_list"][0]["max_tokens"]
            )
            
            response_content = response.choices[0].message.content
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "message_type": "response"
            })
            
            return {
                "agent_name": self.name,
                "message_type": "response",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            error_response = {
                "agent_name": self.name,
                "message_type": "error",
                "content": f"Error processing message: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            return error_response
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent. Override in subclasses."""
        return f"You are {self.name}, a {self.role}."

class SupplyChainAgent(BaseAgent):
    """Specialized agent for dependency analysis and malicious package detection."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__(
            name="SupplyChainAgent",
            role="Supply Chain Security Analyst",
            llm_config=llm_config
        )
        self.malicious_packages = KNOWN_MALICIOUS_PACKAGES
        self.typosquat_targets = TYPOSQUAT_TARGETS
        self.suspicious_keywords = SUSPICIOUS_KEYWORDS
    
    def _get_system_prompt(self) -> str:
        return f"""You are {self.name}, a specialized {self.role} focused on detecting supply chain attacks and malicious packages.

Your expertise includes:
- Analyzing Software Bill of Materials (SBOM) for security threats
- Detecting typosquatting attempts against popular packages
- Identifying suspicious package characteristics and behaviors
- Cross-referencing packages against known malicious package databases
- Analyzing package metadata for anomalies and red flags

You have access to:
- Known malicious packages database with {sum(len(packages) for packages in self.malicious_packages.values())} entries
- Typosquat target lists for major ecosystems (npm, PyPI, Maven, RubyGems, Crates, Go)
- {len(self.suspicious_keywords)} suspicious keywords and patterns for threat detection

When analyzing packages, provide:
1. Confidence scores (0.0-1.0) for each finding
2. Specific evidence supporting your assessment
3. Risk classification (Critical, High, Medium, Low)
4. Recommended actions for remediation

Always structure your responses as JSON with findings, evidence, and recommendations."""

    def analyze_sbom(self, sbom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SBOM data for security threats."""
        findings = []
        
        if "packages" in sbom_data:
            for package in sbom_data["packages"]:
                package_name = package.get("name", "")
                package_version = package.get("versionInfo", "")
                ecosystem = package.get("ecosystem", "unknown")
                
                # Check against known malicious packages
                malicious_finding = self._check_malicious_package(package_name, package_version, ecosystem)
                if malicious_finding:
                    findings.append(malicious_finding)
                
                # Check for typosquatting
                typosquat_finding = self._check_typosquatting(package_name, ecosystem)
                if typosquat_finding:
                    findings.append(typosquat_finding)
        
        analysis_request = f"""
        Analyze this SBOM data for supply chain security threats:
        
        SBOM Summary:
        - Total packages: {len(sbom_data.get('packages', []))}
        - Ecosystems detected: {list(set(pkg.get('ecosystem', 'unknown') for pkg in sbom_data.get('packages', [])))}
        
        Initial findings from signature matching:
        {json.dumps(findings, indent=2)}
        
        Please provide additional analysis focusing on:
        1. Package dependency relationships and potential attack vectors
        2. Unusual version patterns or suspicious package characteristics
        3. Overall risk assessment and prioritized recommendations
        
        Return your analysis as structured JSON.
        """
        
        response = self.send_message(analysis_request, "sbom_analysis")
        
        # Combine signature-based findings with LLM analysis
        try:
            llm_analysis = json.loads(response["content"])
            return {
                "agent": self.name,
                "analysis_type": "sbom_security",
                "signature_findings": findings,
                "llm_analysis": llm_analysis,
                "timestamp": datetime.now().isoformat(),
                "status": response["status"]
            }
        except json.JSONDecodeError:
            return {
                "agent": self.name,
                "analysis_type": "sbom_security", 
                "signature_findings": findings,
                "llm_analysis": {"raw_response": response["content"]},
                "timestamp": datetime.now().isoformat(),
                "status": response["status"]
            }
    
    def _check_malicious_package(self, package_name: str, version: str, ecosystem: str) -> Optional[Dict]:
        """Check if package matches known malicious packages."""
        if ecosystem in self.malicious_packages:
            for malicious_pkg in self.malicious_packages[ecosystem]:
                if (malicious_pkg["name"].lower() == package_name.lower() and
                    (malicious_pkg["version"] == "*" or malicious_pkg["version"] == version)):
                    return {
                        "type": "malicious_package",
                        "package": package_name,
                        "version": version,
                        "ecosystem": ecosystem,
                        "reason": malicious_pkg["reason"],
                        "confidence": 0.95,
                        "severity": "critical",
                        "evidence": [f"Matches known malicious package: {malicious_pkg['reason']}"]
                    }
        return None
    
    def _check_typosquatting(self, package_name: str, ecosystem: str) -> Optional[Dict]:
        """Check if package name is a potential typosquat."""
        if is_suspicious_package_name(package_name, ecosystem):
            # Find the most likely target
            best_match = None
            best_confidence = 0.0
            
            if ecosystem in self.typosquat_targets:
                for target in self.typosquat_targets[ecosystem]:
                    confidence = calculate_typosquat_confidence(package_name, target)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = target
            
            if best_match and best_confidence > 0.5:
                return {
                    "type": "typosquat",
                    "package": package_name,
                    "ecosystem": ecosystem,
                    "target": best_match,
                    "confidence": best_confidence,
                    "severity": "high" if best_confidence > 0.8 else "medium",
                    "evidence": [f"Potential typosquat of popular package '{best_match}' (confidence: {best_confidence:.2f})"]
                }
        return None

class VlmSecurityAgent(BaseAgent):
    """Specialized agent for visual security analysis using GPT-4 Vision."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__(
            name="VlmSecurityAgent", 
            role="Visual Security Analyst",
            llm_config=llm_config or config.get_vision_llm_config()
        )
        self.vision_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    def _get_system_prompt(self) -> str:
        return f"""You are {self.name}, a specialized {self.role} focused on analyzing visual security indicators in screenshots and UI elements.

Your expertise includes:
- Detecting security warnings and alerts in application interfaces
- Identifying suspicious UI elements that may indicate compromise
- Analyzing error messages and system notifications for security implications
- Correlating visual indicators with potential security threats
- Recognizing phishing attempts and social engineering tactics in UI

When analyzing images, look for:
1. Security warnings, error dialogs, or alert messages
2. Unusual or suspicious UI elements
3. Signs of system compromise or unauthorized access
4. Phishing indicators or social engineering attempts
5. Anomalous behavior in application interfaces

Always provide:
- Detailed description of visual findings
- Security implications of observed elements
- Confidence scores for each finding
- Recommendations for investigation or remediation

Structure your responses as JSON with clear findings and evidence."""

    def analyze_screenshot(self, image_base64: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a screenshot for visual security indicators."""
        try:
            analysis_prompt = f"""
            Analyze this screenshot for security-related visual indicators.
            
            {f"Context: {context}" if context else ""}
            
            Look for:
            1. Security warnings, alerts, or error messages
            2. Suspicious UI elements or anomalies
            3. Signs of system compromise or unauthorized access
            4. Phishing indicators or social engineering attempts
            5. Any visual elements that suggest security concerns
            
            Provide your analysis as structured JSON with:
            - findings: List of security-related observations
            - confidence_scores: Confidence level for each finding (0.0-1.0)
            - severity_levels: Risk level for each finding
            - recommendations: Suggested actions based on findings
            """
            
            response = self.vision_client.chat.completions.create(
                model=self.llm_config["config_list"][0]["model"],
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                            }
                        ]
                    }
                ],
                temperature=self.llm_config["config_list"][0]["temperature"],
                max_tokens=self.llm_config["config_list"][0]["max_tokens"]
            )
            
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": "Screenshot analysis request",
                "timestamp": datetime.now().isoformat(),
                "message_type": "image_analysis"
            })
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "message_type": "analysis_response"
            })
            
            # Try to parse as JSON, fallback to raw response
            try:
                analysis_data = json.loads(response_content)
            except json.JSONDecodeError:
                analysis_data = {"raw_response": response_content}
            
            return {
                "agent": self.name,
                "analysis_type": "visual_security",
                "analysis": analysis_data,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "analysis_type": "visual_security",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }

class OrchestratorAgent(BaseAgent):
    """Specialized agent for findings correlation and incident reporting."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__(
            name="OrchestratorAgent",
            role="Security Orchestrator and Incident Analyst", 
            llm_config=llm_config
        )
    
    def _get_system_prompt(self) -> str:
        return f"""You are {self.name}, a specialized {self.role} responsible for correlating security findings and generating comprehensive incident reports.

Your expertise includes:
- Correlating findings from multiple security analysis sources
- Assessing overall risk levels and attack classifications
- Generating actionable incident reports with remediation guidance
- Prioritizing security findings based on severity and impact
- Creating executive summaries for stakeholder communication

When correlating findings, consider:
1. Relationships between different types of security indicators
2. Attack patterns and potential threat actor methodologies
3. Business impact and risk assessment
4. Timeline reconstruction of potential security incidents
5. Containment and remediation strategies

Your reports should include:
- Executive summary with key findings and risk assessment
- Detailed technical analysis with evidence correlation
- Attack classification and potential threat actor attribution
- Prioritized remediation steps with timelines
- Stakeholder communication recommendations

Always structure responses as comprehensive JSON reports with clear sections and actionable recommendations."""

    def correlate_findings(self, findings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlate findings from multiple agents and generate incident report."""
        correlation_request = f"""
        Correlate and analyze the following security findings from multiple analysis sources:
        
        {json.dumps(findings_data, indent=2)}
        
        Please provide a comprehensive incident report including:
        
        1. EXECUTIVE SUMMARY:
           - Overall risk assessment (Critical/High/Medium/Low)
           - Key security findings summary
           - Business impact assessment
           - Immediate actions required
        
        2. TECHNICAL ANALYSIS:
           - Correlation of findings across different sources
           - Attack pattern identification
           - Evidence timeline and relationships
           - Confidence assessment for each finding cluster
        
        3. THREAT CLASSIFICATION:
           - Attack type classification (supply chain, malware, etc.)
           - Potential threat actor indicators
           - Attack sophistication level
           - Likely attack objectives
        
        4. REMEDIATION PLAN:
           - Immediate containment steps (0-24 hours)
           - Short-term remediation (1-7 days)
           - Long-term security improvements (1-4 weeks)
           - Monitoring and detection enhancements
        
        5. STAKEHOLDER COMMUNICATION:
           - Key messages for different stakeholder groups
           - Communication timeline recommendations
           - Regulatory or compliance considerations
        
        Return the complete analysis as structured JSON.
        """
        
        response = self.send_message(correlation_request, "finding_correlation")
        
        try:
            incident_report = json.loads(response["content"])
            
            # Add metadata to the report
            incident_report["metadata"] = {
                "report_generated_by": self.name,
                "generation_timestamp": datetime.now().isoformat(),
                "source_findings_count": len(findings_data),
                "analysis_sources": list(set(finding.get("agent", "unknown") for finding in findings_data if finding is not None and isinstance(finding, dict)))
            }
            
            return {
                "agent": self.name,
                "analysis_type": "incident_correlation",
                "incident_report": incident_report,
                "timestamp": datetime.now().isoformat(),
                "status": response["status"]
            }
            
        except json.JSONDecodeError:
            return {
                "agent": self.name,
                "analysis_type": "incident_correlation",
                "incident_report": {"raw_response": response["content"]},
                "timestamp": datetime.now().isoformat(),
                "status": response["status"]
            }

# Agent factory functions
def create_supply_chain_agent(llm_config: Optional[Dict] = None) -> SupplyChainAgent:
    """Create and initialize a SupplyChainAgent."""
    return SupplyChainAgent(llm_config)

def create_vlm_security_agent(llm_config: Optional[Dict] = None) -> VlmSecurityAgent:
    """Create and initialize a VlmSecurityAgent.""" 
    return VlmSecurityAgent(llm_config)

def create_orchestrator_agent(llm_config: Optional[Dict] = None) -> OrchestratorAgent:
    """Create and initialize an OrchestratorAgent."""
    return OrchestratorAgent(llm_config)

def create_agent_group(llm_config: Optional[Dict] = None) -> Dict[str, BaseAgent]:
    """Create a group of all specialized agents for multi-agent analysis."""
    return {
        "supply_chain": create_supply_chain_agent(llm_config),
        "vlm_security": create_vlm_security_agent(llm_config), 
        "orchestrator": create_orchestrator_agent(llm_config)
    }

class AgentMessage:
    """Structured message for agent communication."""
    
    def __init__(self, sender: str, recipient: str, message_type: str, content: Any, metadata: Optional[Dict] = None):
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.message_id = f"{sender}_{recipient}_{datetime.now().timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def validate(self) -> bool:
        """Validate message structure and content."""
        required_fields = ["sender", "recipient", "message_type", "content"]
        for field in required_fields:
            if not hasattr(self, field) or getattr(self, field) is None:
                return False
        
        valid_message_types = ["analysis_request", "analysis_response", "finding", "correlation_request", "correlation_response", "error"]
        return self.message_type in valid_message_types

class GroupChatManager:
    """Enhanced manager for coordinating multi-agent conversations and analysis."""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.conversation_log: List[Dict[str, Any]] = []
        self.message_queue: List[AgentMessage] = []
        self.active_analysis: Optional[str] = None
        self.analysis_session_id: Optional[str] = None
        self.findings_registry: Dict[str, List[Dict[str, Any]]] = {}
        self.communication_protocols = self._setup_communication_protocols()
    
    def _setup_communication_protocols(self) -> Dict[str, Any]:
        """Setup communication protocols for agent interactions."""
        return {
            "message_validation": True,
            "response_timeout": 120,  # seconds
            "max_retries": 3,
            "correlation_threshold": 0.7,
            "supported_message_types": [
                "analysis_request", "analysis_response", "finding", 
                "correlation_request", "correlation_response", "error"
            ],
            "agent_roles": {
                "supply_chain": ["sbom_analysis", "malicious_package_detection", "vulnerability_assessment"],
                "vlm_security": ["visual_analysis", "screenshot_processing", "ui_anomaly_detection"],
                "orchestrator": ["finding_correlation", "incident_reporting", "risk_assessment"]
            }
        }
    
    def start_analysis(self, analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a multi-agent analysis session with enhanced coordination."""
        self.active_analysis = analysis_type
        self.analysis_session_id = f"session_{datetime.now().timestamp()}"
        self.conversation_log = []
        self.message_queue = []
        self.findings_registry = {}
        
        # Log session start
        self._log_session_event("analysis_started", {
            "analysis_type": analysis_type,
            "session_id": self.analysis_session_id,
            "available_agents": list(self.agents.keys()),
            "data_keys": list(data.keys())
        })
        
        results = {}
        
        try:
            # Route analysis to appropriate agents based on type and capabilities
            if analysis_type == "supply_chain":
                results = self._execute_supply_chain_analysis(data)
            elif analysis_type == "visual_security":
                results = self._execute_visual_security_analysis(data)
            elif analysis_type == "comprehensive":
                results = self._execute_comprehensive_analysis(data)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            # Validate and compile findings
            compiled_findings = self._compile_and_validate_findings(results)
            
            # Correlate findings if multiple agents participated
            if len(results) > 1 and "orchestrator" in self.agents:
                correlation_result = self._coordinate_finding_correlation(list(results.values()))
                if correlation_result:
                    results["correlation"] = correlation_result
            
            # Log session completion
            self._log_session_event("analysis_completed", {
                "session_id": self.analysis_session_id,
                "agents_used": list(results.keys()),
                "findings_count": len(compiled_findings),
                "status": "success"
            })
            
            return {
                "session_id": self.analysis_session_id,
                "analysis_type": analysis_type,
                "results": results,
                "compiled_findings": compiled_findings,
                "message_count": len(self.message_queue),
                "timestamp": datetime.now().isoformat(),
                "agents_used": list(results.keys()),
                "status": "success"
            }
            
        except Exception as e:
            # Log session error
            self._log_session_event("analysis_error", {
                "session_id": self.analysis_session_id,
                "error": str(e),
                "status": "error"
            })
            
            return {
                "session_id": self.analysis_session_id,
                "analysis_type": analysis_type,
                "results": results,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def _execute_supply_chain_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute supply chain analysis with message coordination."""
        results = {}
        
        if "supply_chain" in self.agents and "sbom_data" in data:
            # Send analysis request message
            request_msg = AgentMessage(
                sender="GroupChatManager",
                recipient="supply_chain",
                message_type="analysis_request",
                content={"sbom_data": data["sbom_data"], "analysis_type": "supply_chain"}
            )
            
            if self._send_message(request_msg):
                # Execute analysis
                analysis_result = self.agents["supply_chain"].analyze_sbom(data["sbom_data"])
                
                # Validate response
                if self._validate_agent_response(analysis_result, "supply_chain"):
                    results["supply_chain"] = analysis_result
                    self._register_findings("supply_chain", analysis_result)
                    
                    # Send response confirmation
                    response_msg = AgentMessage(
                        sender="supply_chain",
                        recipient="GroupChatManager", 
                        message_type="analysis_response",
                        content=analysis_result
                    )
                    self._send_message(response_msg)
        
        return results
    
    def _execute_visual_security_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute visual security analysis with message coordination."""
        results = {}
        
        if "vlm_security" in self.agents and "image_base64" in data:
            # Send analysis request message
            request_msg = AgentMessage(
                sender="GroupChatManager",
                recipient="vlm_security",
                message_type="analysis_request",
                content={"image_base64": data["image_base64"], "context": data.get("context")}
            )
            
            if self._send_message(request_msg):
                # Execute analysis
                analysis_result = self.agents["vlm_security"].analyze_screenshot(
                    data["image_base64"], 
                    data.get("context")
                )
                
                # Validate response
                if self._validate_agent_response(analysis_result, "vlm_security"):
                    results["visual_security"] = analysis_result
                    self._register_findings("vlm_security", analysis_result)
                    
                    # Send response confirmation
                    response_msg = AgentMessage(
                        sender="vlm_security",
                        recipient="GroupChatManager",
                        message_type="analysis_response", 
                        content=analysis_result
                    )
                    self._send_message(response_msg)
        
        return results
    
    def _execute_comprehensive_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive analysis coordinating multiple agents."""
        results = {}
        
        # Execute supply chain analysis if data available
        if "sbom_data" in data:
            supply_chain_results = self._execute_supply_chain_analysis({"sbom_data": data["sbom_data"]})
            results.update(supply_chain_results)
        
        # Execute visual security analysis if data available
        if "image_base64" in data:
            visual_results = self._execute_visual_security_analysis({
                "image_base64": data["image_base64"],
                "context": data.get("context")
            })
            results.update(visual_results)
        
        return results
    
    def _coordinate_finding_correlation(self, findings_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Coordinate finding correlation through orchestrator agent."""
        if "orchestrator" not in self.agents:
            return None
        
        try:
            # Send correlation request
            correlation_msg = AgentMessage(
                sender="GroupChatManager",
                recipient="orchestrator",
                message_type="correlation_request",
                content={"findings": findings_list, "session_id": self.analysis_session_id}
            )
            
            if self._send_message(correlation_msg):
                # Execute correlation
                correlation_result = self.agents["orchestrator"].correlate_findings(findings_list)
                
                # Validate correlation response
                if self._validate_agent_response(correlation_result, "orchestrator"):
                    # Send correlation response
                    response_msg = AgentMessage(
                        sender="orchestrator",
                        recipient="GroupChatManager",
                        message_type="correlation_response",
                        content=correlation_result
                    )
                    self._send_message(response_msg)
                    
                    return correlation_result
            
        except Exception as e:
            self._log_session_event("correlation_error", {
                "error": str(e),
                "session_id": self.analysis_session_id
            })
        
        return None
    
    def _send_message(self, message: AgentMessage) -> bool:
        """Send message with validation and logging."""
        if not message.validate():
            self._log_session_event("message_validation_failed", {
                "message_id": message.message_id,
                "sender": message.sender,
                "recipient": message.recipient
            })
            return False
        
        # Add to message queue
        self.message_queue.append(message)
        
        # Log message
        self._log_session_event("message_sent", message.to_dict())
        
        return True
    
    def _validate_agent_response(self, response: Dict[str, Any], agent_name: str) -> bool:
        """Validate agent response structure and content."""
        if not isinstance(response, dict):
            return False
        
        # Check required fields based on agent type
        if agent_name == "supply_chain":
            required_fields = ["agent", "analysis_type", "timestamp", "status"]
        elif agent_name == "vlm_security":
            required_fields = ["agent", "analysis_type", "timestamp", "status"]
        elif agent_name == "orchestrator":
            required_fields = ["agent", "analysis_type", "timestamp", "status"]
        else:
            required_fields = ["agent", "timestamp", "status"]
        
        for field in required_fields:
            if field not in response:
                self._log_session_event("response_validation_failed", {
                    "agent": agent_name,
                    "missing_field": field,
                    "response_keys": list(response.keys())
                })
                return False
        
        return True
    
    def _register_findings(self, agent_name: str, analysis_result: Dict[str, Any]) -> None:
        """Register findings from agent analysis."""
        if agent_name not in self.findings_registry:
            self.findings_registry[agent_name] = []
        
        # Extract findings based on agent type
        findings = []
        if agent_name == "supply_chain" and "signature_findings" in analysis_result:
            findings.extend(analysis_result["signature_findings"])
        elif agent_name == "vlm_security" and "analysis" in analysis_result:
            if isinstance(analysis_result["analysis"], dict) and "findings" in analysis_result["analysis"]:
                findings.extend(analysis_result["analysis"]["findings"])
        elif agent_name == "orchestrator" and "incident_report" in analysis_result:
            findings.append(analysis_result["incident_report"])
        
        self.findings_registry[agent_name].extend(findings)
    
    def _compile_and_validate_findings(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compile and validate findings from all agents."""
        compiled_findings = []
        
        for agent_name, findings_list in self.findings_registry.items():
            for finding in findings_list:
                if isinstance(finding, dict):
                    # Add agent attribution and session metadata
                    compiled_finding = finding.copy()
                    compiled_finding["source_agent"] = agent_name
                    compiled_finding["session_id"] = self.analysis_session_id
                    compiled_finding["compilation_timestamp"] = datetime.now().isoformat()
                    
                    compiled_findings.append(compiled_finding)
        
        return compiled_findings
    
    def _log_session_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log session events for debugging and audit purposes."""
        log_entry = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.analysis_session_id
        }
        
        self.conversation_log.append(log_entry)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the complete conversation history from all agents and session events."""
        all_history = []
        
        # Add session events
        all_history.extend(self.conversation_log)
        
        # Add agent conversation history
        for agent_name, agent in self.agents.items():
            for message in agent.conversation_history:
                message_with_agent = message.copy()
                message_with_agent["agent"] = agent_name
                message_with_agent["session_id"] = self.analysis_session_id
                all_history.append(message_with_agent)
        
        # Add message queue
        for message in self.message_queue:
            message_dict = message.to_dict()
            message_dict["event_type"] = "agent_message"
            all_history.append(message_dict)
        
        # Sort by timestamp
        all_history.sort(key=lambda x: x.get("timestamp", ""))
        return all_history
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of the current analysis session."""
        return {
            "session_id": self.analysis_session_id,
            "analysis_type": self.active_analysis,
            "agents_participated": list(self.findings_registry.keys()),
            "total_findings": sum(len(findings) for findings in self.findings_registry.values()),
            "message_count": len(self.message_queue),
            "session_events": len(self.conversation_log),
            "findings_by_agent": {agent: len(findings) for agent, findings in self.findings_registry.items()},
            "communication_protocols": self.communication_protocols
        }
    
    def reset_session(self) -> None:
        """Reset the current analysis session."""
        self.active_analysis = None
        self.analysis_session_id = None
        self.conversation_log = []
        self.message_queue = []
        self.findings_registry = {}

# Export all public functions and classes
__all__ = [
    "BaseAgent",
    "SupplyChainAgent", 
    "VlmSecurityAgent",
    "OrchestratorAgent",
    "AgentMessage",
    "GroupChatManager",
    "create_supply_chain_agent",
    "create_vlm_security_agent", 
    "create_orchestrator_agent",
    "create_agent_group"
]