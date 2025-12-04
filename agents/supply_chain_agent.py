"""
Enhanced Supply Chain Attack Detection Agent with multiple detection strategies.

This agent uses multiple approaches beyond SBOM tools:
1. Static code analysis for malicious patterns
2. Behavioral analysis of package lifecycle
3. Maintainer and publishing anomaly detection
4. Network-based threat intelligence
5. Historical version comparison
6. Community and security advisory checking

**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5**
"""

import os
import re
import time
import hashlib
import requests
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

from agents.base_agent import SecurityAgent
from agents.types import SharedContext
from tools.cache_manager import get_cache_manager

load_dotenv()


class SupplyChainAttackAgent(SecurityAgent):
    """
    Enhanced agent for detecting supply chain attacks using multiple strategies.
    
    Detection Strategies:
    1. Code Pattern Analysis - Scans for malicious code patterns
    2. Behavioral Anomaly Detection - Identifies suspicious package behavior
    3. Maintainer Risk Assessment - Tracks maintainer changes and risks
    4. Publishing Pattern Analysis - Detects suspicious release patterns
    5. Dependency Risk Analysis - Identifies risky dependencies
    6. Threat Intelligence Integration - Checks against known malicious packages
    
    **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5**
    """
    
    def __init__(self):
        """Initialize the Enhanced Supply Chain Attack Detection Agent."""
        system_message = """You are an advanced supply chain attack detection expert using multiple detection strategies.
Your role is to identify supply chain attacks through:
1. Static code analysis for malicious patterns
2. Behavioral anomaly detection
3. Maintainer and publishing pattern analysis
4. Threat intelligence correlation
5. Historical comparison and anomaly detection

Provide detailed evidence and risk scores for all findings."""
        
        super().__init__(
            name="SupplyChainAttackAgent",
            system_message=system_message,
            tools=[
                self.analyze_code_patterns,
                self.detect_behavioral_anomalies,
                self.assess_maintainer_risk,
                self.analyze_publishing_patterns,
                self.check_threat_intelligence,
                self.analyze_dependency_risk
            ]
        )
        
        self.cache_manager = get_cache_manager(
            backend="sqlite",
            cache_dir=".cache",
            ttl_hours=int(os.getenv("CACHE_DURATION_HOURS", "24")),
            max_size_mb=100
        )
        
        # Enhanced malicious code patterns
        self.malicious_patterns = {
            "credential_theft": {
                "patterns": [
                    r'process\.env\[?["\'](?:NPM_TOKEN|GITHUB_TOKEN|AWS_[A-Z_]+|API_KEY|SECRET|PASSWORD|TOKEN|KEY)',
                    r'os\.environ(?:\[|\.get\()["\'](?:NPM_TOKEN|GITHUB_TOKEN|AWS_[A-Z_]+|API_KEY|SECRET|PASSWORD|TOKEN)',
                    r'\.npmrc|\.pypirc|\.aws/credentials|\.ssh/id_rsa|\.gitconfig|\.git-credentials',
                    r'Authorization:\s*Bearer|Basic\s+[A-Za-z0-9+/=]+',
                ],
                "severity": "critical",
                "weight": 1.0
            },
            "network_exfiltration": {
                "patterns": [
                    r'(?:fetch|axios|http\.request|urllib\.request)\([^)]*(?:process\.env|os\.environ)',
                    r'new\s+(?:WebSocket|EventSource)\([^)]*(?:process\.env|os\.environ)',
                    r'(?:https?://|wss?://)[^\s\'"]+(?:pastebin|discord|telegram|bit\.ly)',
                    r'\.(?:post|put|send)\([^)]*(?:btoa|atob|base64|Buffer)',
                ],
                "severity": "critical",
                "weight": 1.0
            },
            "obfuscation": {
                "patterns": [
                    r'eval\s*\([^\)]*(?:atob|Buffer\.from|unescape|fromCharCode)',
                    r'Function\s*\([^)]*["\']return',
                    r'\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}',
                    r'new\s+Function\s*\(',
                    r'\.replace\(/[^/]+/g[^)]*\)\.replace\(/[^/]+/g',  # Multiple replacements
                ],
                "severity": "high",
                "weight": 0.8
            },
            "delayed_execution": {
                "patterns": [
                    r'setTimeout\s*\([^)]*(?:eval|Function|require)',
                    r'setInterval\s*\([^)]*(?:eval|Function)',
                    r'(?:new\s+)?Date\s*\([^)]*\)\s*[<>=]+',
                    r'process\.(?:nextTick|on)\s*\(["\'](?:exit|SIGINT)',
                ],
                "severity": "high",
                "weight": 0.7
            },
            "file_system_access": {
                "patterns": [
                    r'(?:fs|path)\.(?:readFile|writeFile|unlink|rm)(?:Sync)?\([^)]*(?:home|~|\.\./)',
                    r'child_process\.(?:exec|spawn|fork)(?:Sync)?',
                    r'require\s*\(["\']child_process["\']',
                    r'os\.(?:homedir|tmpdir)\(\)',
                ],
                "severity": "medium",
                "weight": 0.6
            },
            "crypto_mining": {
                "patterns": [
                    r'(?:stratum|xmrig|cryptonight|monero|coinhive)',
                    r'(?:cpu|gpu)(?:Miner|Mining)',
                    r'(?:mining|miner).*(?:pool|worker)',
                ],
                "severity": "critical",
                "weight": 0.9
            }
        }
        
        # Known malicious package indicators
        self.known_indicators = {
            "typosquatting_patterns": [
                r'^py-',  # py-requests instead of requests
                r'-py$',
                r'.*(?:colour|colour|libary|libraray)',  # Common typos
            ],
            "suspicious_keywords": [
                "pwngrabber", "stealer", "token-grabber", "discord-token",
                "cookie-stealer", "password-stealer", "logger", "grabber"
            ]
        }
        
        # Threat intelligence sources
        self.threat_intel_sources = {
            "osv": "https://api.osv.dev/v1/query",
            "snyk": "https://security.snyk.io/vuln/",
        }
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform comprehensive supply chain attack analysis.
        
        Args:
            context: Shared context with package information
            timeout: Optional timeout override
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        start_time = time.time()
        
        if not self._validate_context(context):
            return self._format_error_result("Invalid context provided", 0.0)
        
        # Get all packages to analyze (not just high-risk)
        packages_to_analyze = self._get_packages_to_analyze(context)
        
        if not packages_to_analyze:
            self._log("No packages found for analysis")
            return {
                "packages": [],
                "total_packages_analyzed": 0,
                "supply_chain_attacks_detected": 0,
                "confidence": 1.0,
                "duration_seconds": time.time() - start_time,
                "source": "supply_chain_analysis"
            }
        
        self._log(f"Analyzing {len(packages_to_analyze)} packages for supply chain attacks")
        
        # Run multiple detection strategies in parallel
        results = []
        for pkg_info in packages_to_analyze:
            try:
                if timeout and (time.time() - start_time) > timeout:
                    self._log(f"Timeout reached at {len(results)}/{len(packages_to_analyze)}", "WARNING")
                    break
                
                result = self._multi_strategy_analysis(pkg_info, context)
                results.append(result)
                
            except Exception as e:
                self._log(f"Error analyzing {pkg_info.get('name')}: {str(e)}", "ERROR")
                results.append({
                    "package_name": pkg_info.get("name"),
                    "package_version": pkg_info.get("version", "unknown"),
                    "error": str(e),
                    "risk_score": 0.0,
                    "attack_likelihood": "unknown"
                })
        
        # Aggregate results
        attacks_detected = sum(1 for r in results if r.get("risk_score", 0) >= 0.7)
        avg_confidence = sum(r.get("confidence", 0.8) for r in results) / len(results) if results else 0.8
        
        return {
            "packages": results,
            "total_packages_analyzed": len(results),
            "supply_chain_attacks_detected": attacks_detected,
            "confidence": avg_confidence,
            "duration_seconds": time.time() - start_time,
            "source": "supply_chain_analysis",
            "detection_strategies_used": [
                "code_pattern_analysis",
                "behavioral_anomaly_detection",
                "maintainer_risk_assessment",
                "publishing_pattern_analysis",
                "threat_intelligence",
                "dependency_risk_analysis"
            ]
        }
    
    def _get_packages_to_analyze(self, context: SharedContext) -> List[Dict[str, Any]]:
        """
        Get all packages from context for analysis.
        
        Args:
            context: Shared context
        
        Returns:
            List of packages to analyze
        """
        packages = []
        seen = set()
        
        # Get from initial findings
        for finding in context.initial_findings:
            pkg_key = f"{finding.package_name}@{finding.package_version}"
            if pkg_key not in seen:
                seen.add(pkg_key)
                packages.append({
                    "name": finding.package_name,
                    "version": finding.package_version,
                    "source": "initial_findings"
                })
        
        # Get from package list if available
        if hasattr(context, 'package_list') and context.package_list:
            for pkg in context.package_list:
                pkg_key = f"{pkg.get('name')}@{pkg.get('version', 'unknown')}"
                if pkg_key not in seen:
                    seen.add(pkg_key)
                    packages.append({
                        "name": pkg.get("name"),
                        "version": pkg.get("version", "unknown"),
                        "source": "package_list"
                    })
        
        # Get from other agent results
        for agent_name, result in context.agent_results.items():
            if result.success and "packages" in result.data:
                for pkg_data in result.data["packages"]:
                    pkg_name = pkg_data.get("package_name")
                    pkg_version = pkg_data.get("package_version", "unknown")
                    pkg_key = f"{pkg_name}@{pkg_version}"
                    
                    if pkg_key not in seen:
                        seen.add(pkg_key)
                        packages.append({
                            "name": pkg_name,
                            "version": pkg_version,
                            "source": f"agent_{agent_name}"
                        })
        
        return packages
    
    def _multi_strategy_analysis(
        self,
        pkg_info: Dict[str, Any],
        context: SharedContext
    ) -> Dict[str, Any]:
        """
        Run multiple detection strategies on a package.
        
        Args:
            pkg_info: Package information
            context: Shared context
        
        Returns:
            Comprehensive analysis result
        """
        pkg_name = pkg_info.get("name")
        pkg_version = pkg_info.get("version", "unknown")
        
        # Check cache
        cache_key = f"supply_chain:{context.ecosystem}:{pkg_name}:{pkg_version}"
        cached = self.cache_manager.get_reputation(cache_key)
        if cached:
            return cached
        
        # Run all detection strategies
        findings = []
        
        # Strategy 1: Code Pattern Analysis
        code_findings = self.analyze_code_patterns(pkg_name, context)
        findings.extend(code_findings)
        
        # Strategy 2: Behavioral Anomaly Detection
        behavioral_findings = self.detect_behavioral_anomalies(pkg_name, context)
        findings.extend(behavioral_findings)
        
        # Strategy 3: Maintainer Risk Assessment
        maintainer_findings = self.assess_maintainer_risk(pkg_name, context.ecosystem)
        findings.extend(maintainer_findings)
        
        # Strategy 4: Publishing Pattern Analysis
        publishing_findings = self.analyze_publishing_patterns(pkg_name, context.ecosystem)
        findings.extend(publishing_findings)
        
        # Strategy 5: Threat Intelligence
        threat_findings = self.check_threat_intelligence(pkg_name, context.ecosystem)
        findings.extend(threat_findings)
        
        # Strategy 6: Dependency Risk Analysis
        dep_findings = self.analyze_dependency_risk(pkg_name, context)
        findings.extend(dep_findings)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(findings)
        attack_likelihood = self._get_attack_likelihood(risk_score)
        
        result = {
            "package_name": pkg_name,
            "package_version": pkg_version,
            "ecosystem": context.ecosystem,
            "risk_score": risk_score,
            "attack_likelihood": attack_likelihood,
            "findings": findings,
            "finding_count": len(findings),
            "critical_findings": sum(1 for f in findings if f.get("severity") == "critical"),
            "confidence": self._calculate_confidence(findings),
            "recommendations": self._generate_recommendations(risk_score, findings)
        }
        
        # Cache result
        self.cache_manager.store_reputation(cache_key, result, ttl_hours=6)
        
        return result
    
    def analyze_code_patterns(
        self,
        package_name: str,
        context: SharedContext
    ) -> List[Dict[str, Any]]:
        """
        Analyze code for malicious patterns.
        
        Strategy 1: Direct code analysis for known malicious patterns
        """
        findings = []
        
        # Get code from context if available
        code_content = self._get_package_code(package_name, context)
        
        if not code_content:
            return findings
        
        # Check each pattern category
        for category, config in self.malicious_patterns.items():
            for pattern in config["patterns"]:
                matches = re.findall(pattern, code_content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    findings.append({
                        "type": "malicious_code_pattern",
                        "category": category,
                        "severity": config["severity"],
                        "weight": config["weight"],
                        "description": f"Detected {category} pattern in code",
                        "pattern": pattern[:50],  # Truncate long patterns
                        "match_count": len(matches),
                        "evidence": matches[:2]  # Include sample matches
                    })
        
        # Check for typosquatting in package name
        for pattern in self.known_indicators["typosquatting_patterns"]:
            if re.match(pattern, package_name, re.IGNORECASE):
                findings.append({
                    "type": "typosquatting_indicator",
                    "category": "package_naming",
                    "severity": "high",
                    "weight": 0.8,
                    "description": f"Package name matches typosquatting pattern: {pattern}",
                    "package_name": package_name
                })
        
        # Check for suspicious keywords
        for keyword in self.known_indicators["suspicious_keywords"]:
            if keyword.lower() in package_name.lower():
                findings.append({
                    "type": "suspicious_keyword",
                    "category": "package_naming",
                    "severity": "high",
                    "weight": 0.9,
                    "description": f"Package name contains suspicious keyword: {keyword}",
                    "package_name": package_name
                })
        
        return findings
    
    def detect_behavioral_anomalies(
        self,
        package_name: str,
        context: SharedContext
    ) -> List[Dict[str, Any]]:
        """
        Detect behavioral anomalies from code analysis.
        
        Strategy 2: Behavioral pattern analysis
        """
        findings = []
        
        # Check code analysis results from context
        if "code" in context.agent_results:
            code_result = context.agent_results["code"]
            if code_result.success:
                for pkg_data in code_result.data.get("packages", []):
                    if pkg_data.get("package_name") != package_name:
                        continue
                    
                    behavioral = pkg_data.get("code_analysis", {}).get("behavioral_indicators", [])
                    
                    # Check for dangerous combinations
                    behaviors = {b.get("behavior") for b in behavioral}
                    
                    # Network + env access = potential exfiltration
                    if "network_activity" in behaviors and "env_variable_access" in behaviors:
                        findings.append({
                            "type": "behavioral_anomaly",
                            "category": "exfiltration_risk",
                            "severity": "critical",
                            "weight": 1.0,
                            "description": "Package combines network activity with environment variable access",
                            "behaviors": ["network_activity", "env_variable_access"]
                        })
                    
                    # File system + network = potential data theft
                    if "file_system_access" in behaviors and "network_activity" in behaviors:
                        findings.append({
                            "type": "behavioral_anomaly",
                            "category": "data_theft_risk",
                            "severity": "high",
                            "weight": 0.8,
                            "description": "Package combines file system access with network activity",
                            "behaviors": ["file_system_access", "network_activity"]
                        })
                    
                    # Process execution
                    if "process_execution" in behaviors:
                        findings.append({
                            "type": "behavioral_anomaly",
                            "category": "process_execution",
                            "severity": "high",
                            "weight": 0.7,
                            "description": "Package executes external processes",
                            "behaviors": ["process_execution"]
                        })
        
        return findings
    
    def assess_maintainer_risk(
        self,
        package_name: str,
        ecosystem: str
    ) -> List[Dict[str, Any]]:
        """
        Assess maintainer-related risks.
        
        Strategy 3: Maintainer history and account analysis
        """
        findings = []
        
        try:
            metadata = self._fetch_package_metadata(package_name, ecosystem)
            if not metadata:
                return findings
            
            if ecosystem.lower() == "npm":
                maintainers = metadata.get("maintainers", [])
                versions = metadata.get("versions", {})
                
                # Single maintainer risk
                if len(maintainers) == 1:
                    findings.append({
                        "type": "maintainer_risk",
                        "category": "single_maintainer",
                        "severity": "low",
                        "weight": 0.3,
                        "description": "Package maintained by single person",
                        "maintainer_count": 1
                    })
                
                # Check for maintainer changes in recent versions
                if len(versions) >= 2:
                    version_list = sorted(versions.keys(), reverse=True)[:5]
                    prev_maintainers = None
                    
                    for version in version_list:
                        curr_maintainers = set(
                            m.get("name") for m in versions[version].get("maintainers", [])
                        )
                        
                        if prev_maintainers and curr_maintainers != prev_maintainers:
                            findings.append({
                                "type": "maintainer_risk",
                                "category": "maintainer_change",
                                "severity": "medium",
                                "weight": 0.6,
                                "description": f"Maintainers changed in version {version}",
                                "version": version
                            })
                            break
                        
                        prev_maintainers = curr_maintainers
            
            elif ecosystem.lower() in ["pypi", "python"]:
                if "info" in metadata:
                    info = metadata["info"]
                    author = info.get("author", "").strip()
                    maintainer = info.get("maintainer", "").strip()
                    
                    # Check if maintainer differs from author
                    if maintainer and author and maintainer != author and maintainer != "":
                        findings.append({
                            "type": "maintainer_risk",
                            "category": "maintainer_change",
                            "severity": "medium",
                            "weight": 0.5,
                            "description": "Package maintainer differs from original author",
                            "author": author,
                            "maintainer": maintainer
                        })
        
        except Exception as e:
            self._log(f"Error assessing maintainer risk for {package_name}: {str(e)}", "WARNING")
        
        return findings
    
    def analyze_publishing_patterns(
        self,
        package_name: str,
        ecosystem: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze publishing patterns for anomalies.
        
        Strategy 4: Release pattern analysis
        """
        findings = []
        
        try:
            metadata = self._fetch_package_metadata(package_name, ecosystem)
            if not metadata or "time" not in metadata:
                return findings
            
            time_data = metadata["time"]
            versions = {k: v for k, v in time_data.items() if k not in ["created", "modified"]}
            
            if len(versions) < 2:
                return findings
            
            # Parse timestamps
            timestamps = []
            for version, ts_str in versions.items():
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    timestamps.append((version, ts))
                except:
                    continue
            
            timestamps.sort(key=lambda x: x[1])
            
            # Check for rapid releases (< 1 hour apart)
            for i in range(len(timestamps) - 1):
                v1, t1 = timestamps[i]
                v2, t2 = timestamps[i + 1]
                hours_diff = (t2 - t1).total_seconds() / 3600
                
                if hours_diff < 1:
                    findings.append({
                        "type": "publishing_anomaly",
                        "category": "rapid_release",
                        "severity": "high",
                        "weight": 0.7,
                        "description": f"Rapid release: {v1} and {v2} published {hours_diff:.1f} hours apart",
                        "hours_between": hours_diff
                    })
            
            # Check for unusual publishing times (2-5 AM UTC)
            recent_versions = timestamps[-5:]
            unusual_time_count = 0
            
            for version, ts in recent_versions:
                if 2 <= ts.hour <= 5:
                    unusual_time_count += 1
            
            if unusual_time_count >= 2:
                findings.append({
                    "type": "publishing_anomaly",
                    "category": "unusual_time",
                    "severity": "medium",
                    "weight": 0.4,
                    "description": f"{unusual_time_count} recent versions published between 2-5 AM UTC",
                    "count": unusual_time_count
                })
            
            # Check for long dormancy followed by activity
            if timestamps:
                created = timestamps[0][1]
                latest = timestamps[-1][1]
                now = datetime.now(created.tzinfo)
                
                days_since_created = (now - created).days
                days_since_latest = (now - latest).days
                
                if days_since_created > 365 and days_since_latest < 30:
                    findings.append({
                        "type": "publishing_anomaly",
                        "category": "dormant_package_reactivated",
                        "severity": "medium",
                        "weight": 0.6,
                        "description": "Package dormant for over a year, recently reactivated",
                        "days_dormant": days_since_created,
                        "days_since_update": days_since_latest
                    })
        
        except Exception as e:
            self._log(f"Error analyzing publishing patterns for {package_name}: {str(e)}", "WARNING")
        
        return findings
    
    def check_threat_intelligence(
        self,
        package_name: str,
        ecosystem: str
    ) -> List[Dict[str, Any]]:
        """
        Check package against threat intelligence sources.
        
        Strategy 5: External threat intelligence
        """
        findings = []
        
        try:
            # Check OSV database
            osv_vulns = self._check_osv(package_name, ecosystem)
            if osv_vulns:
                for vuln in osv_vulns:
                    findings.append({
                        "type": "threat_intelligence",
                        "category": "known_vulnerability",
                        "severity": self._map_osv_severity(vuln),
                        "weight": 0.9,
                        "description": f"Known vulnerability: {vuln.get('id')}",
                        "vuln_id": vuln.get("id"),
                        "summary": vuln.get("summary", "")[:100]
                    })
        
        except Exception as e:
            self._log(f"Error checking threat intelligence for {package_name}: {str(e)}", "WARNING")
        
        return findings
    
    def analyze_dependency_risk(
        self,
        package_name: str,
        context: SharedContext
    ) -> List[Dict[str, Any]]:
        """
        Analyze risks from package dependencies.
        
        Strategy 6: Dependency chain analysis
        """
        findings = []
        
        try:
            metadata = self._fetch_package_metadata(package_name, context.ecosystem)
            if not metadata:
                return findings
            
            # Get latest version dependencies
            dist_tags = metadata.get("dist-tags", {})
            latest = dist_tags.get("latest")
            
            if latest and "versions" in metadata:
                version_data = metadata["versions"].get(latest, {})
                dependencies = version_data.get("dependencies", {})
                
                # Check for excessive dependencies
                if len(dependencies) > 50:
                    findings.append({
                        "type": "dependency_risk",
                        "category": "excessive_dependencies",
                        "severity": "low",
                        "weight": 0.3,
                        "description": f"Package has {len(dependencies)} dependencies",
                        "dependency_count": len(dependencies)
                    })
                
                # Check for suspicious dependency names
                for dep_name in dependencies.keys():
                    for keyword in self.known_indicators["suspicious_keywords"]:
                        if keyword in dep_name.lower():
                            findings.append({
                                "type": "dependency_risk",
                                "category": "suspicious_dependency",
                                "severity": "high",
                                "weight": 0.8,
                                "description": f"Suspicious dependency: {dep_name}",
                                "dependency": dep_name
                            })
        
        except Exception as e:
            self._log(f"Error analyzing dependency risk for {package_name}: {str(e)}", "WARNING")
        
        return findings
    
    def _get_package_code(self, package_name: str, context: SharedContext) -> str:
        """Extract package code from context."""
        code_parts = []
        
        # Try to get from code analysis results
        if "code" in context.agent_results:
            code_result = context.agent_results["code"]
            if code_result.success:
                for pkg_data in code_result.data.get("packages", []):
                    if pkg_data.get("package_name") == package_name:
                        # Concatenate code samples
                        code_analysis = pkg_data.get("code_analysis", {})
                        
                        # Get from obfuscation samples
                        for obf in code_analysis.get("obfuscation_detected", []):
                            if "sample_code" in obf:
                                code_parts.append(obf["sample_code"])
                        
                        # Get from behavioral indicators
                        for behav in code_analysis.get("behavioral_indicators", []):
                            if "sample_code" in behav:
                                code_parts.append(behav["sample_code"])
        
        return "\n".join(code_parts)
    
    def _fetch_package_metadata(self, package_name: str, ecosystem: str) -> Optional[Dict]:
        """Fetch package metadata from registry."""
        try:
            if ecosystem.lower() == "npm":
                url = f"https://registry.npmjs.org/{package_name}"
            elif ecosystem.lower() in ["pypi", "python"]:
                url = f"https://pypi.org/pypi/{package_name}/json"
            else:
                return None
            
            response = requests.get(url, timeout=10)
            return response.json() if response.status_code == 200 else None
        
        except Exception as e:
            self._log(f"Error fetching metadata: {str(e)}", "WARNING")
            return None
    
    def _check_osv(self, package_name: str, ecosystem: str) -> List[Dict]:
        """Check package against OSV vulnerability database."""
        try:
            ecosystem_map = {"npm": "npm", "pypi": "PyPI", "python": "PyPI"}
            osv_ecosystem = ecosystem_map.get(ecosystem.lower(), ecosystem)
            
            payload = {
                "package": {
                    "name": package_name,
                    "ecosystem": osv_ecosystem
                }
            }
            
            response = requests.post(
                self.threat_intel_sources["osv"],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("vulns", [])
            
            return []
        
        except Exception as e:
            self._log(f"Error checking OSV: {str(e)}", "WARNING")
            return []
    
    def _map_osv_severity(self, vuln: Dict) -> str:
        """Map OSV vulnerability severity to internal severity levels."""
        # Check for CVSS score or severity field
        severity = vuln.get("severity", [])
        if severity:
            for sev in severity:
                score = sev.get("score")
                if score:
                    # Parse CVSS score
                    try:
                        cvss_score = float(score.split(":")[1].split("/")[0])
                        if cvss_score >= 9.0:
                            return "critical"
                        elif cvss_score >= 7.0:
                            return "high"
                        elif cvss_score >= 4.0:
                            return "medium"
                        else:
                            return "low"
                    except:
                        pass
        
        # Default to high for any reported vulnerability
        return "high"
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """
        Calculate overall risk score from findings.
        
        Args:
            findings: List of findings from all strategies
        
        Returns:
            Risk score between 0.0 and 1.0
        """
        if not findings:
            return 0.0
        
        # Calculate weighted score
        total_weight = 0.0
        max_possible_weight = 0.0
        
        severity_multipliers = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2
        }
        
        for finding in findings:
            weight = finding.get("weight", 0.5)
            severity = finding.get("severity", "medium")
            multiplier = severity_multipliers.get(severity, 0.5)
            
            total_weight += weight * multiplier
            max_possible_weight += weight
        
        # Normalize to 0-1 range
        if max_possible_weight > 0:
            risk_score = min(1.0, total_weight / max_possible_weight)
        else:
            risk_score = 0.0
        
        # Apply non-linear scaling to be more sensitive to multiple findings
        if len(findings) >= 5:
            risk_score = min(1.0, risk_score * 1.2)
        
        return round(risk_score, 3)
    
    def _get_attack_likelihood(self, risk_score: float) -> str:
        """
        Convert risk score to attack likelihood category.
        
        Args:
            risk_score: Risk score between 0.0 and 1.0
        
        Returns:
            Attack likelihood category
        """
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        elif risk_score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _calculate_confidence(self, findings: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence in the analysis.
        
        Args:
            findings: List of findings
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not findings:
            return 0.95  # High confidence in no findings
        
        # More findings from different categories = higher confidence
        categories = set(f.get("category") for f in findings)
        num_categories = len(categories)
        
        # Base confidence
        confidence = 0.75
        
        # Increase confidence with more diverse findings
        if num_categories >= 3:
            confidence += 0.15
        elif num_categories >= 2:
            confidence += 0.10
        
        # Increase confidence if we have critical findings
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        if critical_count >= 2:
            confidence += 0.10
        
        return min(1.0, confidence)
    
    def _generate_recommendations(
        self,
        risk_score: float,
        findings: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate actionable recommendations based on findings.
        
        Args:
            risk_score: Calculated risk score
            findings: List of findings
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if risk_score >= 0.8:
            recommendations.extend([
                "🚨 CRITICAL: Remove this package immediately from all projects",
                "Scan your systems for indicators of compromise",
                "Rotate all credentials and secrets that may have been exposed",
                "Review audit logs for suspicious activity",
                "Report this package to the registry security team"
            ])
        elif risk_score >= 0.6:
            recommendations.extend([
                "⚠️ HIGH RISK: Do not use this package in production",
                "Conduct thorough security review before any use",
                "Monitor for security advisories",
                "Consider alternative packages"
            ])
        elif risk_score >= 0.4:
            recommendations.extend([
                "⚡ MEDIUM RISK: Exercise caution with this package",
                "Review package source code before deployment",
                "Implement additional monitoring",
                "Keep package updated to latest version"
            ])
        elif risk_score >= 0.2:
            recommendations.extend([
                "ℹ️ LOW RISK: Monitor this package",
                "Follow security best practices",
                "Stay informed of updates"
            ])
        
        # Add specific recommendations based on finding types
        finding_types = set(f.get("type") for f in findings)
        
        if "malicious_code_pattern" in finding_types:
            recommendations.append("🔍 Review code for obfuscation and malicious patterns")
        
        if "behavioral_anomaly" in finding_types:
            categories = set(f.get("category") for f in findings if f.get("type") == "behavioral_anomaly")
            if "exfiltration_risk" in categories:
                recommendations.append("🔒 Check for unauthorized network connections")
            if "data_theft_risk" in categories:
                recommendations.append("📁 Audit file system access permissions")
        
        if "maintainer_risk" in finding_types:
            recommendations.append("👤 Verify package maintainer identity and reputation")
        
        if "threat_intelligence" in finding_types:
            recommendations.append("📋 Review CVE details and apply patches if available")
        
        if "typosquatting_indicator" in finding_types or "suspicious_keyword" in finding_types:
            recommendations.append("🏷️ Verify you're using the correct package name")
        
        return recommendations
    
    def _validate_context(self, context: SharedContext) -> bool:
        """
        Validate that context has required information.
        
        Args:
            context: Shared context to validate
        
        Returns:
            True if context is valid
        """
        if not context:
            self._log("Context is None", "ERROR")
            return False
        
        if not hasattr(context, 'ecosystem'):
            self._log("Context missing ecosystem", "ERROR")
            return False
        
        # We need at least one source of packages
        has_packages = (
            (hasattr(context, 'initial_findings') and context.initial_findings) or
            (hasattr(context, 'package_list') and context.package_list) or
            (hasattr(context, 'agent_results') and context.agent_results)
        )
        
        if not has_packages:
            self._log("Context has no package information", "WARNING")
            return True  # Still valid, just no work to do
        
        return True
    
    def _format_error_result(self, error_msg: str, confidence: float) -> Dict[str, Any]:
        """
        Format an error result.
        
        Args:
            error_msg: Error message
            confidence: Confidence score
        
        Returns:
            Formatted error result
        """
        return {
            "packages": [],
            "total_packages_analyzed": 0,
            "supply_chain_attacks_detected": 0,
            "confidence": confidence,
            "error": error_msg,
            "source": "supply_chain_analysis"
        }
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message (delegated to base class if available).
        
        Args:
            message: Message to log
            level: Log level
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] SupplyChainAttackAgent: {message}")
    
    def _generate_cache_key(
        self,
        package_name: str,
        ecosystem: str,
        version: str
    ) -> str:
        """
        Generate cache key for supply chain analysis.
        
        Args:
            package_name: Package name
            ecosystem: Package ecosystem
            version: Package version
        
        Returns:
            Cache key string
        """
        key_str = f"supply_chain_v2:{ecosystem}:{package_name}:{version}"
        return hashlib.md5(key_str.encode()).hexdigest()