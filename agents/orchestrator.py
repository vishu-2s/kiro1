"""
Agent orchestrator for coordinating multi-agent security analysis.

This module implements the AgentOrchestrator class which coordinates the execution
of multiple specialized agents using an explicit sequential protocol with timeout
handling, retry logic, and graceful degradation.
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from agents.types import (
    AgentResult, 
    SharedContext, 
    Finding, 
    AgentConfig,
    AgentStatus
)
from agents.base_agent import SecurityAgent
from agents.error_handler import ErrorHandler, DegradationLevel
from agents.output_restructure import OutputRestructurer

# Load environment variables
load_dotenv()


class AgentOrchestrator:
    """
    Coordinates multi-agent analysis using explicit sequential protocol.
    
    The orchestrator manages a 5-stage conversation protocol:
    1. Vulnerability Analysis (required, 30s timeout)
    2. Reputation Analysis (required, 20s timeout)
    3. Code Analysis (conditional, 40s timeout)
    4. Supply Chain Analysis (conditional, 30s timeout)
    5. Synthesis (required, 20s timeout)
    
    Each stage has validation checkpoints and failure handling with graceful degradation.
    """
    
    # Stage configurations with timeouts (reduced for faster execution)
    STAGE_CONFIGS = {
        "vulnerability_analysis": AgentConfig(
            name="vulnerability_analysis",
            timeout=20,  # Reduced from 30
            required=True,
            max_retries=1,  # Reduced from 2
            retry_delay=0.5  # Reduced from 1.0
        ),
        "reputation_analysis": AgentConfig(
            name="reputation_analysis",
            timeout=15,  # Reduced from 20
            required=True,
            max_retries=1,  # Reduced from 2
            retry_delay=0.5  # Reduced from 1.0
        ),
        "code_analysis": AgentConfig(
            name="code_analysis",
            timeout=25,  # Reduced from 40
            required=False,
            max_retries=1,
            retry_delay=0.5  # Reduced from 1.0
        ),
        "supply_chain_analysis": AgentConfig(
            name="supply_chain_analysis",
            timeout=20,  # Reduced from 30
            required=False,
            max_retries=1,
            retry_delay=0.5  # Reduced from 1.0
        ),
        "synthesis": AgentConfig(
            name="synthesis",
            timeout=15,  # Reduced from 20
            required=True,
            max_retries=1,  # Reduced from 2
            retry_delay=0.5  # Reduced from 1.0
        )
    }
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        # Load configuration from .env
        self.output_dir = os.getenv("OUTPUT_DIRECTORY", "outputs")
        self.max_total_time = 90  # Reduced from 140 to 90 seconds (1.5 minutes)
        
        # Agents will be set by the caller
        self.agents: Dict[str, SecurityAgent] = {}
        
        # Execution state
        self.start_time: float = 0.0
        self.stage_results: Dict[str, AgentResult] = {}
        
        # Error handler for graceful degradation
        self.error_handler = ErrorHandler(max_retries=1, base_delay=0.5)  # Reduced retries and delay
        
    def register_agent(self, stage_name: str, agent: SecurityAgent) -> None:
        """
        Register an agent for a specific stage.
        
        Args:
            stage_name: Name of the stage (must match STAGE_CONFIGS keys)
            agent: Agent instance to register
        """
        if stage_name not in self.STAGE_CONFIGS:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        self.agents[stage_name] = agent
        self._log(f"Registered agent for stage: {stage_name}")
    
    def orchestrate(
        self, 
        initial_findings: List[Finding], 
        dependency_graph: Dict[str, Any],
        input_mode: str = "local",
        project_path: str = "",
        ecosystem: str = "npm"
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-agent analysis using explicit sequential protocol.
        
        Protocol stages:
        1. Vulnerability Agent (required, 20s timeout)
        2. Reputation Agent (required, 15s timeout)
        3. Code Agent (conditional, 25s timeout)
        4. Supply Chain Agent (conditional, 20s timeout)
        5. Synthesis Agent (required, 15s timeout)
        
        Args:
            initial_findings: Findings from rule-based detection
            dependency_graph: Complete dependency graph structure
            input_mode: Analysis mode ('github' or 'local')
            project_path: Path to the project being analyzed
            ecosystem: Primary ecosystem (npm, pypi, etc.)
        
        Returns:
            Package-centric JSON output
        """
        self.start_time = time.time()
        self._log("=" * 60)
        self._log("Starting multi-agent orchestration")
        self._log(f"Target: {project_path}")
        self._log(f"Ecosystem: {ecosystem}")
        self._log(f"Initial findings: {len(initial_findings)}")
        self._log("=" * 60)
        
        # Initialize shared context
        # Extract all packages from dependency graph, not just from findings
        all_packages = self._extract_all_packages(dependency_graph, initial_findings)
        
        self._log(f"Total packages to analyze: {len(all_packages)}")
        
        context = SharedContext(
            initial_findings=initial_findings,
            dependency_graph=dependency_graph,
            packages=all_packages,
            input_mode=input_mode,
            project_path=project_path,
            ecosystem=ecosystem
        )
        
        # Stage 1: Vulnerability Analysis (Required)
        self._log("=" * 60)
        self._log("Stage 1: Vulnerability Analysis")
        self._log("=" * 60)
        try:
            vuln_result = self._run_agent_stage(
                stage_name="vulnerability_analysis",
                context=context
            )
            context.add_agent_result(vuln_result)
            self._log(f"Stage 1 completed: success={vuln_result.success}")
            
            # Log detailed results
            if vuln_result.success and vuln_result.data:
                packages_analyzed = vuln_result.data.get("total_packages_analyzed", 0)
                vulns_found = vuln_result.data.get("total_vulnerabilities_found", 0)
                self._log(f"  > Packages analyzed: {packages_analyzed}")
                self._log(f"  > Vulnerabilities found: {vulns_found}")
                self._log(f"  > Confidence: {vuln_result.data.get('confidence', 0):.2f}")
                
                # Log per-package summary
                for pkg in vuln_result.data.get("packages", [])[:5]:  # First 5 packages
                    pkg_name = pkg.get("package_name", "unknown")
                    vuln_count = pkg.get("vulnerability_count", 0)
                    if vuln_count > 0:
                        self._log(f"  > {pkg_name}: {vuln_count} vulnerabilities")
            
        except Exception as e:
            self._log(f"Stage 1 failed with exception: {str(e)}", "ERROR")
            import traceback
            self._log(f"Traceback: {traceback.format_exc()}", "ERROR")
            raise
        
        # Stage 2: Reputation Analysis (Required)
        self._log("=" * 60)
        self._log("Stage 2: Reputation Analysis")
        self._log("=" * 60)
        rep_result = self._run_agent_stage(
            stage_name="reputation_analysis",
            context=context
        )
        context.add_agent_result(rep_result)
        
        # Log detailed results
        if rep_result.success and rep_result.data:
            packages_analyzed = rep_result.data.get("total_packages_analyzed", 0)
            self._log(f"  > Packages analyzed: {packages_analyzed}")
            self._log(f"  > Confidence: {rep_result.data.get('confidence', 0):.2f}")
            
            # Log reputation summary
            high_risk = 0
            medium_risk = 0
            low_risk = 0
            for pkg in rep_result.data.get("packages", []):
                risk_level = pkg.get("risk_level", "unknown")
                if risk_level == "high" or risk_level == "critical":
                    high_risk += 1
                elif risk_level == "medium":
                    medium_risk += 1
                else:
                    low_risk += 1
            
            self._log(f"  > High risk packages: {high_risk}")
            self._log(f"  > Medium risk packages: {medium_risk}")
            self._log(f"  > Low risk packages: {low_risk}")
            
            # Log specific high-risk packages
            for pkg in rep_result.data.get("packages", []):
                if pkg.get("risk_level") in ["high", "critical"]:
                    pkg_name = pkg.get("package_name", "unknown")
                    score = pkg.get("reputation_score", 0)
                    self._log(f"  > [!] {pkg_name}: reputation score {score:.2f}")
        
        # Stage 3: Code Analysis (Conditional - only if suspicious patterns found)
        self._log("=" * 60)
        if self._should_run_code_analysis(context):
            self._log("Stage 3: Code Analysis (triggered by suspicious patterns)")
            self._log("=" * 60)
            code_result = self._run_agent_stage(
                stage_name="code_analysis",
                context=context
            )
            context.add_agent_result(code_result)
            
            # Log detailed results
            if code_result.success and code_result.data:
                packages_analyzed = code_result.data.get("total_packages_analyzed", 0)
                issues_found = code_result.data.get("total_code_issues_found", 0)
                self._log(f"  > Packages analyzed: {packages_analyzed}")
                self._log(f"  > Code issues found: {issues_found}")
                self._log(f"  > Confidence: {code_result.data.get('confidence', 0):.2f}")
        else:
            self._log("Stage 3: Code Analysis (skipped - no suspicious patterns)")
            self._log("=" * 60)
        
        # Stage 4: Supply Chain Analysis (Conditional - only if high-risk packages)
        self._log("=" * 60)
        if self._should_run_supply_chain_analysis(context):
            self._log("Stage 4: Supply Chain Analysis (triggered by high-risk packages)")
            self._log("=" * 60)
            sc_result = self._run_agent_stage(
                stage_name="supply_chain_analysis",
                context=context
            )
            context.add_agent_result(sc_result)
            
            # Log detailed results
            if sc_result.success and sc_result.data:
                packages_analyzed = sc_result.data.get("total_packages_analyzed", 0)
                attacks_found = sc_result.data.get("total_attacks_detected", 0)
                self._log(f"  > Packages analyzed: {packages_analyzed}")
                self._log(f"  > Supply chain attacks detected: {attacks_found}")
                self._log(f"  > Confidence: {sc_result.data.get('confidence', 0):.2f}")
        else:
            self._log("Stage 4: Supply Chain Analysis (skipped - no high-risk packages)")
            self._log("=" * 60)
        
        # Stage 5: Synthesis (Required)
        self._log("=" * 60)
        self._log("Stage 5: Synthesis")
        self._log("=" * 60)
        self._log("Aggregating findings from all agents...")
        final_json = self._run_synthesis_stage(context)
        
        # Log synthesis results
        if final_json:
            summary = final_json.get("summary", {})
            self._log(f"  > Total packages: {summary.get('total_packages', 0)}")
            self._log(f"  > Total findings: {summary.get('total_findings', 0)}")
            self._log(f"  > Critical: {summary.get('critical_findings', 0)}")
            self._log(f"  > High: {summary.get('high_findings', 0)}")
            self._log(f"  > Medium: {summary.get('medium_findings', 0)}")
            self._log(f"  > Low: {summary.get('low_findings', 0)}")
        
        # Add performance metrics
        total_duration = time.time() - self.start_time
        final_json["performance_metrics"] = {
            "total_duration_seconds": total_duration,
            "agent_durations": {
                name: result.duration_seconds
                for name, result in context.agent_results.items()
            },
            "stages_completed": len(context.agent_results),
            "stages_failed": sum(
                1 for r in context.agent_results.values() if not r.success
            )
        }
        
        # Add degradation metadata
        degradation_metadata = self.error_handler.get_degradation_metadata(context)
        final_json["metadata"].update(degradation_metadata)
        
        # Restructure output into 3 clear sections
        self._log("Restructuring output into organized sections...")
        restructurer = OutputRestructurer()
        final_json = restructurer.restructure_output(
            final_json,
            input_mode=context.input_mode,
            ecosystem=context.ecosystem
        )
        self._log("Output restructured successfully")
        
        # Write to output file
        output_path = self._write_output(final_json)
        
        # Final summary
        self._log("=" * 60)
        self._log("ANALYSIS COMPLETE")
        self._log("=" * 60)
        self._log(f"Output: {output_path}")
        self._log(f"Total duration: {total_duration:.2f}s")
        self._log(f"Stages completed: {len(context.agent_results)}")
        
        # Log agent performance
        self._log("")
        self._log("Agent Performance:")
        for agent_name, result in context.agent_results.items():
            status = "[OK]" if result.success else "[FAIL]"
            self._log(f"  {agent_name}: {status} ({result.duration_seconds:.2f}s)")
        
        self._log("=" * 60)
        
        return final_json
    
    def _run_agent_stage(
        self,
        stage_name: str,
        context: SharedContext
    ) -> AgentResult:
        """
        Run a single agent stage with timeout, retry logic, and validation.
        
        Args:
            stage_name: Name of the stage to run
            context: Shared context
        
        Returns:
            AgentResult with success/failure and data
        """
        config = self.STAGE_CONFIGS[stage_name]
        agent = self.agents.get(stage_name)
        
        if agent is None:
            error = ValueError(f"No agent registered for stage: {stage_name}")
            self._log(str(error), "ERROR")
            return self.error_handler.handle_agent_failure(
                agent_name=stage_name,
                error=error,
                required=config.required
            )
        
        # Define retry function for error handler
        def retry_agent():
            start_time = time.time()
            result_data = agent.analyze(context, timeout=config.timeout)
            duration = time.time() - start_time
            
            if not self._validate_agent_result(result_data):
                raise ValueError(f"Agent {stage_name} returned invalid data")
            
            return AgentResult(
                agent_name=stage_name,
                success=True,
                data=result_data,
                duration_seconds=duration,
                status=AgentStatus.SUCCESS
            )
        
        # Try to run agent
        try:
            start_time = time.time()
            result_data = agent.analyze(context, timeout=config.timeout)
            duration = time.time() - start_time
            
            # Validate result
            if not self._validate_agent_result(result_data):
                raise ValueError(f"Agent {stage_name} returned invalid data")
            
            # Success
            self._log(f"Stage {stage_name} completed successfully in {duration:.2f}s")
            return AgentResult(
                agent_name=stage_name,
                success=True,
                data=result_data,
                duration_seconds=duration,
                status=AgentStatus.SUCCESS
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._log(f"Agent {stage_name} failed: {str(e)}", "ERROR")
            
            # Use error handler for retry and fallback
            return self.error_handler.handle_agent_failure(
                agent_name=stage_name,
                error=e,
                required=config.required,
                retry_func=retry_agent,
                duration=duration
            )
    
    def _run_synthesis_stage(self, context: SharedContext) -> Dict[str, Any]:
        """
        Run synthesis stage to produce final JSON output.
        
        Args:
            context: Shared context with all agent results
        
        Returns:
            Final package-centric JSON report
        """
        config = self.STAGE_CONFIGS["synthesis"]
        agent = self.agents.get("synthesis")
        
        if agent is None:
            error = ValueError("No synthesis agent registered")
            self._log(str(error), "WARNING")
            return self.error_handler.handle_synthesis_failure(context, error)
        
        try:
            start_time = time.time()
            
            # Run synthesis agent
            final_json = agent.analyze(context, timeout=config.timeout)
            
            duration = time.time() - start_time
            
            # Validate JSON schema
            if not self._validate_json_schema(final_json):
                raise ValueError("Synthesis agent returned invalid JSON schema")
            
            self._log(f"Synthesis completed successfully in {duration:.2f}s")
            return final_json
            
        except Exception as e:
            self._log(f"Synthesis failed: {str(e)}", "ERROR")
            return self.error_handler.handle_synthesis_failure(context, e)
    

    
    def _validate_agent_result(self, result_data: Dict[str, Any]) -> bool:
        """
        Validate that agent result has required structure.
        
        Args:
            result_data: Data returned by agent
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(result_data, dict):
            return False
        
        # Each agent must return a "packages" key
        if "packages" not in result_data:
            return False
        
        return True
    
    def _validate_json_schema(self, json_data: Dict[str, Any]) -> bool:
        """
        Validate final JSON against expected schema.
        
        Args:
            json_data: JSON data to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Check if it's a dictionary
        if not isinstance(json_data, dict):
            return False
        
        # Must have at least metadata and summary
        # security_findings is optional (can be empty)
        required_keys = ["metadata", "summary"]
        has_required = all(key in json_data for key in required_keys)
        
        if not has_required:
            return False
        
        # Validate metadata has basic fields
        metadata = json_data.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        
        # Validate summary has basic fields
        summary = json_data.get("summary", {})
        if not isinstance(summary, dict):
            return False
        
        return True
    

    
    def _extract_packages(self, findings: List[Finding]) -> List[str]:
        """
        Extract unique package names from findings.
        
        Args:
            findings: List of findings
        
        Returns:
            List of unique package names
        """
        return list(set(f.package_name for f in findings))
    
    def _extract_all_packages(self, dependency_graph: Dict[str, Any], findings: List[Finding]) -> List[str]:
        """
        Extract all unique package names from dependency graph and findings.
        
        Args:
            dependency_graph: Dependency graph structure
            findings: List of findings
        
        Returns:
            List of all unique package names
        """
        packages = set()
        
        # Extract from findings
        for finding in findings:
            packages.add(finding.package_name)
        
        # Extract from dependency graph metadata
        if "metadata" in dependency_graph:
            total_packages = dependency_graph["metadata"].get("total_packages", 0)
            self._log(f"Dependency graph contains {total_packages} packages")
        
        # Extract from dependency graph nodes
        if "nodes" in dependency_graph:
            for node in dependency_graph["nodes"]:
                if isinstance(node, dict) and "name" in node:
                    packages.add(node["name"])
        
        # Extract from packages list if available
        if "packages" in dependency_graph:
            for pkg in dependency_graph["packages"]:
                if isinstance(pkg, dict):
                    packages.add(pkg.get("name", ""))
                elif isinstance(pkg, str):
                    packages.add(pkg)
        
        # Remove empty strings
        packages.discard("")
        
        return list(packages)
    
    def _should_run_code_analysis(self, context: SharedContext) -> bool:
        """
        Determine if code analysis should run based on findings.
        
        Args:
            context: Shared context
        
        Returns:
            True if code analysis should run
        """
        # Check if any findings have suspicious code patterns
        for finding in context.initial_findings:
            if finding.finding_type in ["obfuscated_code", "suspicious_script", "malicious_code"]:
                return True
        
        return False
    
    def _should_run_supply_chain_analysis(self, context: SharedContext) -> bool:
        """
        Determine if supply chain analysis should run based on reputation.
        
        Args:
            context: Shared context
        
        Returns:
            True if supply chain analysis should run
        """
        # Check reputation results for high-risk packages
        rep_result = context.get_agent_result("reputation_analysis")
        if not rep_result or not rep_result.success:
            return False
        
        # Check for low reputation packages
        for pkg_data in rep_result.data.get("packages", []):
            reputation_score = pkg_data.get("reputation_score", 1.0)
            if reputation_score < 0.3:  # High risk threshold
                return True
        
        return False
    
    def _write_output(self, json_data: Dict[str, Any]) -> str:
        """
        Write final JSON to output file.
        
        Args:
            json_data: JSON data to write
        
        Returns:
            Path to output file
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Write to fixed filename for backward compatibility
        output_path = os.path.join(self.output_dir, "demo_ui_comprehensive_report.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message from the orchestrator.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{level}] Orchestrator: {message}")
