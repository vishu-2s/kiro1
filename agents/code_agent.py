"""
Code Analysis Agent for the multi-agent security analysis system.

This agent analyzes complex and obfuscated code using LLM-based analysis,
detects obfuscation techniques, identifies behavioral patterns, and calculates
code complexity.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

import os
import re
import time
import json
import hashlib
import base64
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

from agents.base_agent import SecurityAgent
from agents.types import SharedContext
from tools.cache_manager import get_cache_manager

# Load environment variables
load_dotenv()


class CodeAnalysisAgent(SecurityAgent):
    """
    Agent that analyzes complex and obfuscated code for security issues.
    
    This agent:
    - Analyzes complex or obfuscated code using LLM-based analysis
    - Detects obfuscation techniques (base64, eval, dynamic execution)
    - Explains security implications of suspicious patterns
    - Identifies behavioral indicators (network activity, file access, process spawning)
    - Calculates code complexity scores
    - Uses caching to optimize performance
    
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    """
    
    def __init__(self):
        """Initialize the Code Analysis Agent."""
        system_message = """You are a code security analysis expert. Your role is to:
1. Analyze complex or obfuscated code for security vulnerabilities
2. Detect obfuscation techniques (base64, eval, dynamic execution)
3. Explain security implications of suspicious patterns
4. Identify behavioral indicators (network activity, file access, process spawning)
5. Calculate code complexity and assess risk

Always provide confidence scores and reasoning for your assessments.
Focus on security implications and potential malicious behavior."""
        
        super().__init__(
            name="CodeAnalysisAgent",
            system_message=system_message,
            tools=[
                self.analyze_code_with_llm,
                self.detect_obfuscation,
                self.analyze_behavior,
                self.calculate_complexity,
                self.get_cached_analysis
            ]
        )
        
        # OpenAI client will be initialized by base class via llm_config
        # No need to set api_key here - it's handled in base_agent.py
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager(
            backend="sqlite",
            cache_dir=".cache",
            ttl_hours=int(os.getenv("CACHE_DURATION_HOURS", "24")),
            max_size_mb=100
        )
        
        # Obfuscation patterns
        self.obfuscation_patterns = {
            "base64_decode": [
                r'atob\s*\(',
                r'Buffer\.from\s*\([^,]+,\s*["\']base64["\']',
                r'base64\.b64decode\s*\(',
                r'base64\.decode\s*\('
            ],
            "dynamic_execution": [
                r'child_process\.exec\s*\(',
                r'child_process\.spawn\s*\(',
                r'\w+\.exec\s*\(["\'].*(?:curl|wget|bash|sh|cmd|powershell)',  # Variable.exec with shell commands
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'subprocess\.Popen\s*\(',
                r'Runtime\.getRuntime\(\)\.exec\s*\('
            ],
            "eval_execution": [
                r'\beval\s*\(',
                r'Function\s*\(',
                r'\bexec\s*\(',
                r'\bexecfile\s*\(',
                r'\bcompile\s*\('
            ],
            "hex_encoding": [
                r'\\x[0-9a-fA-F]{2}',
                r'0x[0-9a-fA-F]+'
            ],
            "unicode_obfuscation": [
                r'\\u[0-9a-fA-F]{4}',
                r'\\U[0-9a-fA-F]{8}'
            ]
        }
        
        # Behavioral patterns
        self.behavioral_patterns = {
            "network_activity": [
                r'https?://[^\s\'"]+',
                r'fetch\s*\(',
                r'XMLHttpRequest',
                r'axios\.',
                r'requests\.',
                r'urllib\.request',
                r'http\.request',
                r'https\.request',
                r'net\.connect',
                r'require\s*\(\s*["\']https?["\']',
                r'\.request\s*\('
            ],
            "file_access": [
                r'fs\.readFile',
                r'fs\.writeFile',
                r'fs\.unlink',
                r'open\s*\(',
                r'os\.remove',
                r'os\.unlink',
                r'File\s*\(',
                r'FileWriter',
                r'FileReader'
            ],
            "process_spawning": [
                r'child_process\.',
                r'spawn\s*\(',
                r'fork\s*\(',
                r'exec\s*\(',
                r'subprocess\.',
                r'ProcessBuilder',
                r'Runtime\.getRuntime'
            ],
            "env_variable_access": [
                r'process\.env',
                r'os\.environ',
                r'System\.getenv',
                r'ENV\[',
                r'\$\{[A-Z_]+\}'
            ],
            "crypto_operations": [
                r'crypto\.',
                r'createCipher',
                r'createHash',
                r'hashlib\.',
                r'Cipher\.',
                r'MessageDigest'
            ]
        }
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze code for all packages with suspicious patterns.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        
        Args:
            context: Shared context with package information
            timeout: Optional timeout override
        
        Returns:
            Dictionary with code analysis results for each package
        """
        start_time = time.time()
        
        # Validate context
        if not self._validate_context(context):
            return self._format_error_result("Invalid context provided", 0.0)
        
        # Get packages with suspicious patterns from initial findings
        suspicious_packages = self._get_suspicious_packages(context)
        
        if not suspicious_packages:
            self._log("No suspicious packages found, skipping code analysis")
            return {
                "packages": [],
                "total_packages_analyzed": 0,
                "suspicious_patterns_found": 0,
                "confidence": 1.0,
                "duration_seconds": time.time() - start_time,
                "source": "code_analysis",
                "note": "No suspicious patterns detected in initial scan"
            }
        
        self._log(f"Analyzing {len(suspicious_packages)} packages with suspicious patterns")
        
        # Analyze each suspicious package
        package_results = []
        for package_info in suspicious_packages:
            try:
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    self._log(f"Timeout reached, analyzed {len(package_results)}/{len(suspicious_packages)} packages", "WARNING")
                    break
                
                # Analyze package
                package_result = self._analyze_package_code(package_info, context)
                package_results.append(package_result)
                
            except Exception as e:
                self._log(f"Error analyzing package {package_info.get('name', 'unknown')}: {str(e)}", "ERROR")
                # Continue with other packages
                package_results.append({
                    "package_name": package_info.get("name", "unknown"),
                    "package_version": package_info.get("version", "unknown"),
                    "code_analysis": {
                        "obfuscation_detected": [],
                        "behavioral_indicators": [],
                        "complexity_score": 0.0,
                        "llm_assessment": "Analysis failed",
                        "security_implications": [],
                        "risk_level": "unknown"
                    },
                    "error": str(e),
                    "confidence": 0.0,
                    "reasoning": f"Analysis failed: {str(e)}"
                })
        
        duration = time.time() - start_time
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(package_results)
        
        # Count total suspicious patterns
        total_patterns = sum(
            len(p.get("code_analysis", {}).get("obfuscation_detected", [])) +
            len(p.get("code_analysis", {}).get("behavioral_indicators", []))
            for p in package_results
        )
        
        return {
            "packages": package_results,
            "total_packages_analyzed": len(package_results),
            "suspicious_patterns_found": total_patterns,
            "confidence": overall_confidence,
            "duration_seconds": duration,
            "source": "code_analysis"
        }
    
    def _get_suspicious_packages(self, context: SharedContext) -> List[Dict[str, Any]]:
        """
        Get packages with suspicious patterns from initial findings.
        
        Args:
            context: Shared context
        
        Returns:
            List of suspicious package information
        """
        suspicious_packages = []
        
        # Check initial findings for suspicious patterns
        for finding in context.initial_findings:
            if finding.finding_type in ["obfuscated_code", "suspicious_script", "malicious_package"]:
                suspicious_packages.append({
                    "name": finding.package_name,
                    "version": finding.package_version,
                    "finding_type": finding.finding_type,
                    "evidence": finding.evidence
                })
        
        # Remove duplicates
        seen = set()
        unique_packages = []
        for pkg in suspicious_packages:
            pkg_key = f"{pkg['name']}@{pkg['version']}"
            if pkg_key not in seen:
                seen.add(pkg_key)
                unique_packages.append(pkg)
        
        return unique_packages
    
    def _analyze_package_code(
        self, 
        package_info: Dict[str, Any], 
        context: SharedContext
    ) -> Dict[str, Any]:
        """
        Analyze code for a single package.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        
        Args:
            package_info: Package information with suspicious patterns
            context: Shared context
        
        Returns:
            Dictionary with code analysis for the package
        """
        package_name = package_info.get("name", "unknown")
        package_version = package_info.get("version", "unknown")
        
        # Check cache first
        cached_result = self.get_cached_analysis(package_name, package_version)
        if cached_result:
            self._log(f"Using cached code analysis for {package_name}")
            return cached_result
        
        # Get code sample from evidence
        code_sample = self._extract_code_sample(package_info)
        
        if not code_sample:
            self._log(f"No code sample available for {package_name}", "WARNING")
            return {
                "package_name": package_name,
                "package_version": package_version,
                "code_analysis": {},
                "confidence": 0.5,
                "reasoning": "No code sample available for analysis"
            }
        
        # Detect obfuscation
        obfuscation_results = self.detect_obfuscation(code_sample)
        
        # Analyze behavior
        behavioral_results = self.analyze_behavior(code_sample)
        
        # Calculate complexity
        complexity_score = self.calculate_complexity(code_sample)
        
        # Perform LLM-based analysis if patterns detected
        llm_analysis = {}
        if obfuscation_results["detected"] or behavioral_results["detected"]:
            try:
                llm_analysis = self.analyze_code_with_llm(
                    code_sample, 
                    package_name,
                    obfuscation_results,
                    behavioral_results
                )
            except Exception as e:
                self._log(f"LLM analysis failed for {package_name}: {str(e)}", "WARNING")
                llm_analysis = {
                    "assessment": "LLM analysis unavailable",
                    "security_implications": [],
                    "confidence": 0.5,
                    "error": str(e)
                }
        
        # Calculate confidence
        confidence = self._calculate_package_confidence(
            obfuscation_results,
            behavioral_results,
            llm_analysis
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            obfuscation_results,
            behavioral_results,
            complexity_score,
            llm_analysis
        )
        
        result = {
            "package_name": package_name,
            "package_version": package_version,
            "code_analysis": {
                "obfuscation_detected": obfuscation_results.get("techniques", []),
                "behavioral_indicators": behavioral_results.get("indicators", []),
                "complexity_score": complexity_score,
                "llm_assessment": llm_analysis.get("assessment", ""),
                "security_implications": llm_analysis.get("security_implications", []),
                "risk_level": self._determine_risk_level(
                    obfuscation_results,
                    behavioral_results,
                    complexity_score
                )
            },
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        # Cache the result
        self._cache_analysis_result(package_name, package_version, result)
        
        return result
    
    def detect_obfuscation(self, code: str) -> Dict[str, Any]:
        """
        Detect code obfuscation techniques.
        
        **Tool function for agent**
        **Validates: Requirement 6.2**
        
        Args:
            code: Code to analyze
        
        Returns:
            Dictionary with obfuscation detection results
        """
        detected_techniques = []
        
        # Check each obfuscation pattern
        for technique, patterns in self.obfuscation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    detected_techniques.append({
                        "technique": technique,
                        "pattern": pattern,
                        "severity": self._get_obfuscation_severity(technique)
                    })
                    break  # Only add each technique once
        
        return {
            "detected": len(detected_techniques) > 0,
            "techniques": detected_techniques,
            "count": len(detected_techniques)
        }
    
    def analyze_behavior(self, code: str) -> Dict[str, Any]:
        """
        Analyze code behavior patterns.
        
        **Tool function for agent**
        **Validates: Requirement 6.4**
        
        Args:
            code: Code to analyze
        
        Returns:
            Dictionary with behavioral analysis results
        """
        detected_indicators = []
        
        # Check each behavioral pattern
        for behavior, patterns in self.behavioral_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, code, re.IGNORECASE)
                if found:
                    matches.extend(found[:3])  # Limit to 3 examples per pattern
            
            if matches:
                detected_indicators.append({
                    "behavior": behavior,
                    "examples": matches,
                    "count": len(matches),
                    "severity": self._get_behavior_severity(behavior)
                })
        
        return {
            "detected": len(detected_indicators) > 0,
            "indicators": detected_indicators,
            "count": len(detected_indicators)
        }
    
    def calculate_complexity(self, code: str) -> float:
        """
        Calculate code complexity score.
        
        **Tool function for agent**
        **Validates: Requirement 6.5**
        
        Args:
            code: Code to analyze
        
        Returns:
            Complexity score (0.0-1.0, higher = more complex)
        """
        complexity = 0.0
        
        # Count lines of code
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip()])
        
        # Normalize LOC (0-100 lines = 0.0-0.3)
        complexity += min(0.3, loc / 333.0)
        
        # Count nesting depth
        max_nesting = self._calculate_max_nesting(code)
        complexity += min(0.2, max_nesting / 25.0)
        
        # Count control flow statements
        control_flow = len(re.findall(r'\b(if|else|for|while|switch|case|try|catch)\b', code))
        complexity += min(0.2, control_flow / 50.0)
        
        # Count function calls
        function_calls = len(re.findall(r'\w+\s*\(', code))
        complexity += min(0.15, function_calls / 100.0)
        
        # Check for long lines (indicator of obfuscation)
        long_lines = len([line for line in lines if len(line) > 200])
        if long_lines > 0:
            complexity += min(0.3, long_lines * 0.2)
        
        return min(1.0, complexity)
    
    def analyze_code_with_llm(
        self,
        code: str,
        package_name: str,
        obfuscation_results: Dict[str, Any],
        behavioral_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform deep code analysis using LLM.
        
        **Tool function for agent**
        **Validates: Requirements 6.1, 6.3**
        
        Args:
            code: Code to analyze
            package_name: Package name
            obfuscation_results: Obfuscation detection results
            behavioral_results: Behavioral analysis results
        
        Returns:
            Dictionary with LLM analysis results
        """
        try:
            # Truncate code if too long (max 2000 chars for LLM)
            code_sample = code[:2000] if len(code) > 2000 else code
            
            # Build prompt
            prompt = self._build_llm_prompt(
                code_sample,
                package_name,
                obfuscation_results,
                behavioral_results
            )
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.llm_config["model"],
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config["temperature"],
                max_tokens=self.llm_config["max_tokens"],
                timeout=self.llm_config["timeout"]
            )
            
            # Extract response
            analysis_text = response.choices[0].message.content
            
            # Parse LLM response
            return self._parse_llm_response(analysis_text)
            
        except Exception as e:
            self._log(f"LLM analysis failed: {str(e)}", "ERROR")
            return {
                "assessment": "LLM analysis unavailable",
                "security_implications": [],
                "confidence": 0.5,
                "error": str(e)
            }
    
    def get_cached_analysis(
        self, 
        package: str, 
        version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached code analysis.
        
        **Tool function for agent**
        
        Args:
            package: Package name
            version: Package version
        
        Returns:
            Cached analysis data or None
        """
        # Generate cache key
        cache_key = self._generate_cache_key(package, version)
        
        # Try to get from cache
        cached_data = self.cache_manager.get_reputation(cache_key)
        
        return cached_data
    
    def _extract_code_sample(self, package_info: Dict[str, Any]) -> str:
        """
        Extract code sample from package evidence.
        
        Args:
            package_info: Package information
        
        Returns:
            Code sample string
        """
        evidence = package_info.get("evidence", {})
        
        # Try to get code from evidence
        if isinstance(evidence, dict):
            if "code" in evidence:
                return evidence["code"]
            if "script_content" in evidence:
                return evidence["script_content"]
            if "suspicious_code" in evidence:
                return evidence["suspicious_code"]
        
        # Return empty string if no code found
        return ""
    
    def _get_obfuscation_severity(self, technique: str) -> str:
        """
        Get severity level for obfuscation technique.
        
        Args:
            technique: Obfuscation technique name
        
        Returns:
            Severity level (critical, high, medium, low)
        """
        severity_mapping = {
            "base64_decode": "high",
            "eval_execution": "critical",
            "dynamic_execution": "critical",
            "hex_encoding": "medium",
            "unicode_obfuscation": "medium"
        }
        return severity_mapping.get(technique, "medium")
    
    def _get_behavior_severity(self, behavior: str) -> str:
        """
        Get severity level for behavioral indicator.
        
        Args:
            behavior: Behavior type
        
        Returns:
            Severity level (critical, high, medium, low)
        """
        severity_mapping = {
            "network_activity": "high",
            "file_access": "medium",
            "process_spawning": "critical",
            "env_variable_access": "high",
            "crypto_operations": "medium"
        }
        return severity_mapping.get(behavior, "medium")
    
    def _calculate_max_nesting(self, code: str) -> int:
        """
        Calculate maximum nesting depth in code.
        
        Args:
            code: Code to analyze
        
        Returns:
            Maximum nesting depth
        """
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char in '{[(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in '}])':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _determine_risk_level(
        self,
        obfuscation_results: Dict[str, Any],
        behavioral_results: Dict[str, Any],
        complexity_score: float
    ) -> str:
        """
        Determine overall risk level.
        
        Args:
            obfuscation_results: Obfuscation detection results
            behavioral_results: Behavioral analysis results
            complexity_score: Code complexity score
        
        Returns:
            Risk level (critical, high, medium, low)
        """
        # Check for critical patterns
        obfuscation_techniques = obfuscation_results.get("techniques", [])
        behavioral_indicators = behavioral_results.get("indicators", [])
        
        # Critical if eval/exec + network activity
        has_eval = any(t["technique"] in ["eval_execution", "dynamic_execution"] 
                      for t in obfuscation_techniques)
        has_network = any(b["behavior"] == "network_activity" 
                         for b in behavioral_indicators)
        
        if has_eval and has_network:
            return "critical"
        
        # Critical if process spawning
        has_process_spawn = any(b["behavior"] == "process_spawning" 
                               for b in behavioral_indicators)
        if has_process_spawn:
            return "critical"
        
        # High if multiple obfuscation techniques
        if len(obfuscation_techniques) >= 2:
            return "high"
        
        # High if obfuscation + behavioral indicators
        if obfuscation_techniques and behavioral_indicators:
            return "high"
        
        # Medium if high complexity + indicators
        if complexity_score > 0.7 and (obfuscation_techniques or behavioral_indicators):
            return "medium"
        
        # Low otherwise
        return "low"
    
    def _calculate_package_confidence(
        self,
        obfuscation_results: Dict[str, Any],
        behavioral_results: Dict[str, Any],
        llm_analysis: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for package code analysis.
        
        Args:
            obfuscation_results: Obfuscation detection results
            behavioral_results: Behavioral analysis results
            llm_analysis: LLM analysis results
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with high confidence for pattern detection
        confidence = 0.90
        
        # Increase confidence if LLM analysis succeeded
        if llm_analysis and "error" not in llm_analysis:
            confidence = 0.95
        
        # Reduce confidence if no patterns detected (might be incomplete)
        if not obfuscation_results.get("detected") and not behavioral_results.get("detected"):
            confidence = 0.85
        
        return confidence
    
    def _calculate_overall_confidence(self, package_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence across all packages.
        
        Args:
            package_results: List of package analysis results
        
        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not package_results:
            return 1.0  # High confidence when no suspicious packages
        
        # Average confidence across all packages
        total_confidence = sum(p.get("confidence", 0.0) for p in package_results)
        avg_confidence = total_confidence / len(package_results)
        
        return avg_confidence
    
    def _generate_reasoning(
        self,
        obfuscation_results: Dict[str, Any],
        behavioral_results: Dict[str, Any],
        complexity_score: float,
        llm_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate reasoning for the code analysis.
        
        Args:
            obfuscation_results: Obfuscation detection results
            behavioral_results: Behavioral analysis results
            complexity_score: Code complexity score
            llm_analysis: LLM analysis results
        
        Returns:
            Reasoning string
        """
        reasoning_parts = []
        
        # Obfuscation
        obfuscation_count = len(obfuscation_results.get("techniques", []))
        if obfuscation_count > 0:
            techniques = ", ".join(t["technique"] for t in obfuscation_results.get("techniques", []))
            reasoning_parts.append(f"Detected {obfuscation_count} obfuscation technique(s): {techniques}.")
        
        # Behavioral indicators
        behavior_count = len(behavioral_results.get("indicators", []))
        if behavior_count > 0:
            behaviors = ", ".join(b["behavior"] for b in behavioral_results.get("indicators", []))
            reasoning_parts.append(f"Found {behavior_count} behavioral indicator(s): {behaviors}.")
        
        # Complexity
        if complexity_score > 0.7:
            reasoning_parts.append(f"High code complexity (score: {complexity_score:.2f}) may indicate obfuscation.")
        
        # LLM assessment
        if llm_analysis and "assessment" in llm_analysis:
            assessment = llm_analysis["assessment"]
            if assessment and assessment != "LLM analysis unavailable":
                reasoning_parts.append(f"LLM assessment: {assessment}")
        
        if not reasoning_parts:
            return "No significant code security issues detected."
        
        return " ".join(reasoning_parts)
    
    def _build_llm_prompt(
        self,
        code: str,
        package_name: str,
        obfuscation_results: Dict[str, Any],
        behavioral_results: Dict[str, Any]
    ) -> str:
        """
        Build prompt for LLM analysis.
        
        Args:
            code: Code sample
            package_name: Package name
            obfuscation_results: Obfuscation detection results
            behavioral_results: Behavioral analysis results
        
        Returns:
            Prompt string
        """
        prompt = f"""Analyze this code from package '{package_name}' for security issues.

Code Sample:
```
{code}
```

Detected Patterns:
- Obfuscation techniques: {len(obfuscation_results.get('techniques', []))}
- Behavioral indicators: {len(behavioral_results.get('indicators', []))}

Please provide:
1. Security assessment (2-3 sentences)
2. Specific security implications (list)
3. Confidence level (0.0-1.0)

Focus on:
- Is this code malicious or just poorly written?
- What are the security risks?
- What could this code do if executed?

Respond in this format:
ASSESSMENT: [your assessment]
IMPLICATIONS: [implication 1], [implication 2], ...
CONFIDENCE: [0.0-1.0]
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured data.
        
        Args:
            response_text: Raw LLM response
        
        Returns:
            Parsed response dictionary
        """
        result = {
            "assessment": "",
            "security_implications": [],
            "confidence": 0.8
        }
        
        # Extract assessment
        assessment_match = re.search(r'ASSESSMENT:\s*(.+?)(?=IMPLICATIONS:|CONFIDENCE:|$)', 
                                    response_text, re.DOTALL | re.IGNORECASE)
        if assessment_match:
            result["assessment"] = assessment_match.group(1).strip()
        
        # Extract implications
        implications_match = re.search(r'IMPLICATIONS:\s*(.+?)(?=CONFIDENCE:|$)', 
                                      response_text, re.DOTALL | re.IGNORECASE)
        if implications_match:
            implications_text = implications_match.group(1).strip()
            result["security_implications"] = [
                imp.strip() for imp in implications_text.split(',')
                if imp.strip()
            ]
        
        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*(0?\.\d+|1\.0)', 
                                    response_text, re.IGNORECASE)
        if confidence_match:
            try:
                result["confidence"] = float(confidence_match.group(1))
            except ValueError:
                pass
        
        return result
    
    def _generate_cache_key(self, package: str, version: str) -> str:
        """
        Generate cache key for code analysis.
        
        Args:
            package: Package name
            version: Package version
        
        Returns:
            Cache key string
        """
        key_string = f"{package}:{version}"
        return f"code_analysis:{key_string}"
    
    def _cache_analysis_result(
        self,
        package: str,
        version: str,
        result: Dict[str, Any]
    ):
        """
        Cache code analysis result.
        
        Args:
            package: Package name
            version: Package version
            result: Analysis result to cache
        """
        cache_key = self._generate_cache_key(package, version)
        
        # Cache for 24 hours
        self.cache_manager.store_reputation(cache_key, result, ttl_hours=24)
