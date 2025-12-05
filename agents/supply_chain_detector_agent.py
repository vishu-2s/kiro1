"""
Supply Chain Attack Detection Agent for Multi-Agent Security Analysis System.

This agent specializes in detecting supply chain attacks by:
1. Extracting packages from manifest files (requirements.txt, package.json)
2. Checking against known malicious package databases
3. Using web search APIs to find recent supply chain attacks
4. Querying vulnerability databases (OSV, Snyk)
5. Using LLM to analyze and assess threats

**Primary Focus: Supply Chain Attack Detection**
"""

import os
import re
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from agents.base_agent import SecurityAgent
from agents.types import SharedContext
from tools.cache_manager import get_cache_manager
from config import config

# Load environment variables
load_dotenv()


class SupplyChainDetectorAgent(SecurityAgent):
    """
    Agent specialized in detecting supply chain attacks and malicious packages.
    
    This agent uses LLM capabilities to:
    - Analyze packages for supply chain attack indicators
    - Assess threat severity and confidence
    - Generate actionable recommendations
    
    Tools available:
    - extract_packages: Extract dependencies from GitHub/local projects
    - check_malicious_db: Check against known malicious package database
    - check_vulnerabilities: Query OSV and Snyk databases
    - web_search_threats: Search for recent supply chain attacks
    - llm_analyze_threat: Use LLM to analyze and assess threats
    """
    
    def __init__(self):
        """Initialize the Supply Chain Detector Agent."""
        system_message = """You are a supply chain security expert specializing in detecting malicious packages and supply chain attacks.

Your capabilities:
1. Extract and analyze dependencies from package manifests
2. Check packages against known malicious databases
3. Query vulnerability databases (OSV, Snyk)
4. Use web search to find recent supply chain attacks
5. Assess threat severity and provide recommendations

When analyzing packages:
- Check for known malicious packages first (highest priority)
- Look for typosquatting attempts
- Check for recent vulnerabilities
- Search for recent supply chain attack reports
- Provide confidence scores and evidence for all findings

Always provide actionable recommendations with severity levels."""
        
        super().__init__(
            name="SupplyChainDetectorAgent",
            system_message=system_message,
            tools=[
                self.extract_packages,
                self.check_malicious_db,
                self.check_vulnerabilities,
                self.web_search_threats,
                self.llm_analyze_threat
            ]
        )
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(
                api_key=api_key,
                timeout=30.0,
                max_retries=2
            )
            self._log("OpenAI client initialized for LLM analysis")
        else:
            self.openai_client = None
            self._log("WARNING: OPENAI_API_KEY not found. LLM analysis disabled.", "WARNING")
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager(
            backend="sqlite",
            cache_dir=".cache",
            ttl_hours=int(os.getenv("CACHE_DURATION_HOURS", "24")),
            max_size_mb=100
        )
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze project for supply chain attacks using tools and LLM.
        
        Args:
            context: Shared context with project information
            timeout: Optional timeout override
        
        Returns:
            Dictionary with supply chain threat analysis results
        """
        start_time = time.time()
        
        self._log("=" * 60)
        self._log("Starting Supply Chain Attack Detection")
        self._log("=" * 60)
        
        # Step 1: Extract packages from source
        source_path = context.metadata.get("source_path") or context.project_path
        ecosystem = context.ecosystem  # Get ecosystem from context
        self._log(f"Source: {source_path}")
        self._log(f"Ecosystem: {ecosystem}")
        
        packages = self.extract_packages(source_path, ecosystem)
        
        if not packages:
            self._log("No packages found to analyze")
            return {
                "threats_detected": [],
                "total_packages_checked": 0,
                "malicious_packages_found": 0,
                "vulnerable_packages_found": 0,
                "confidence": 1.0,
                "duration_seconds": time.time() - start_time,
                "source": "supply_chain_detector",
                "note": "No packages found in project"
            }
        
        self._log(f"Found {len(packages)} packages to analyze")
        
        all_threats = []
        
        # Step 2: Check against malicious database (highest priority)
        self._log("\n[1/4] Checking against malicious package database...")
        malicious_threats = self.check_malicious_db(packages)
        all_threats.extend(malicious_threats)
        self._log(f"  Found {len(malicious_threats)} malicious packages")
        
        # Step 3: Check vulnerability databases
        self._log("\n[2/4] Checking vulnerability databases (OSV, Snyk)...")
        vuln_threats = self.check_vulnerabilities(packages)
        all_threats.extend(vuln_threats)
        self._log(f"  Found {len(vuln_threats)} vulnerable packages")
        
        # Step 4: Web search for recent supply chain attacks
        self._log("\n[3/4] Searching for recent supply chain attacks...")
        web_threats = self.web_search_threats(packages)
        all_threats.extend(web_threats)
        self._log(f"  Found {len(web_threats)} potential threats from web search")
        
        # Step 5: Use LLM to analyze and assess all threats
        self._log("\n[4/4] LLM threat analysis and assessment...")
        if all_threats and self.openai_client:
            all_threats = self.llm_analyze_threat(all_threats, packages)
            self._log("  LLM analysis complete")
        
        # Deduplicate threats
        unique_threats = self._deduplicate_threats(all_threats)
        
        duration = time.time() - start_time
        
        # Calculate statistics by threat type
        malicious_count = len([t for t in unique_threats if t.get("threat_type") == "malicious_package"])
        vulnerable_count = len([t for t in unique_threats if t.get("threat_type") == "vulnerability"])
        web_intel_count = len([t for t in unique_threats if t.get("threat_type") == "web_intelligence"])
        
        # Count by severity
        critical_count = len([t for t in unique_threats if t.get("severity") == "critical"])
        high_count = len([t for t in unique_threats if t.get("severity") == "high"])
        
        overall_confidence = self._calculate_overall_confidence(unique_threats)
        
        # Determine overall risk level
        if malicious_count > 0 or critical_count > 0:
            risk_level = "CRITICAL"
        elif high_count > 0:
            risk_level = "HIGH"
        elif len(unique_threats) > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        self._log("\n" + "=" * 60)
        self._log(f"ANALYSIS COMPLETE - Risk Level: {risk_level}")
        self._log(f"  Total Threats: {len(unique_threats)}")
        self._log(f"  - Malicious Packages: {malicious_count}")
        self._log(f"  - Vulnerabilities: {vulnerable_count}")
        self._log(f"  - Web Intelligence: {web_intel_count}")
        self._log(f"  Duration: {duration:.2f}s")
        self._log("=" * 60)
        
        return {
            "threats_detected": unique_threats,
            "total_packages_checked": len(packages),
            "total_threats_found": len(unique_threats),
            "malicious_packages_found": malicious_count,
            "vulnerabilities_found": vulnerable_count,
            "web_intelligence_found": web_intel_count,
            "critical_severity_count": critical_count,
            "high_severity_count": high_count,
            "risk_level": risk_level,
            "confidence": overall_confidence,
            "duration_seconds": duration,
            "source": "supply_chain_detector"
        }
    
    # ==================== TOOL FUNCTIONS ====================
    
    def extract_packages(self, source_path: str, ecosystem: str = None) -> List[Dict[str, Any]]:
        """
        Extract packages from GitHub repository or local project.
        
        **Tool function for agent**
        
        Args:
            source_path: GitHub URL or local directory path
            ecosystem: Target ecosystem (npm, pypi) - only search relevant manifest files
        
        Returns:
            List of package dictionaries with name, version, ecosystem
        """
        packages = []
        
        try:
            is_github = source_path.startswith("http") and "github.com" in source_path
            
            if is_github:
                self._log(f"  Extracting from GitHub: {source_path}")
                packages = self._extract_from_github(source_path, ecosystem)
            else:
                self._log(f"  Extracting from local: {source_path}")
                packages = self._extract_from_local(source_path or ".", ecosystem)
            
        except Exception as e:
            self._log(f"  Error extracting packages: {str(e)}", "ERROR")
        
        return packages
    
    def check_malicious_db(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check packages against known malicious package database.
        
        **Tool function for agent**
        
        Args:
            packages: List of package dictionaries
        
        Returns:
            List of threat dictionaries for malicious packages found
        """
        threats = []
        
        try:
            from constants import KNOWN_MALICIOUS_PACKAGES
            
            for pkg in packages:
                pkg_name = pkg.get("name", "").lower()
                pkg_version = pkg.get("version", "*")
                ecosystem = pkg.get("ecosystem", "npm")
                
                malicious_packages = KNOWN_MALICIOUS_PACKAGES.get(ecosystem, [])
                
                for malicious_pkg in malicious_packages:
                    if malicious_pkg["name"].lower() == pkg_name:
                        self._log(f"  🚨 MALICIOUS: {pkg_name} ({ecosystem})", "WARNING")
                        
                        threats.append({
                            "package_name": pkg_name,
                            "package_version": pkg_version,
                            "ecosystem": ecosystem,
                            "threat_type": "malicious_package",
                            "severity": "critical",
                            "confidence": 0.95,
                            "source": "known_malicious_database",
                            "description": malicious_pkg.get("reason", "Known malicious package"),
                            "evidence": {
                                "database_entry": malicious_pkg,
                                "version_constraint": malicious_pkg.get("version", "*")
                            },
                            "recommendations": [
                                f"URGENT: Remove '{pkg_name}' immediately",
                                "Scan system for signs of compromise",
                                "Review affected code and dependencies"
                            ]
                        })
                        break
        
        except Exception as e:
            self._log(f"  Error checking malicious database: {str(e)}", "ERROR")
        
        return threats
    
    def check_vulnerabilities(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check packages against authentic security sources (NOT OSV - that's done by VulnerabilityAgent).
        
        Sources checked:
        - GitHub Security Advisories API
        - npm Registry (deprecated packages)
        - PyPI Registry (yanked packages)
        - Snyk API (if token available)
        
        **Tool function for agent**
        
        Args:
            packages: List of package dictionaries
        
        Returns:
            List of threat dictionaries for vulnerable packages
        """
        threats = []
        
        for pkg in packages:
            pkg_name = pkg.get("name")
            ecosystem = pkg.get("ecosystem", "npm")
            
            # Check cache
            cache_key = f"supply_chain_vuln:{ecosystem}:{pkg_name}"
            cached = self.cache_manager.get_reputation(cache_key)
            if cached:
                threats.extend(cached.get("threats", []))
                continue
            
            pkg_threats = []
            
            # Check GitHub Security Advisories (different from OSV)
            github_threats = self._check_github_advisories(pkg_name, ecosystem)
            pkg_threats.extend(github_threats)
            
            # Check npm/PyPI registries for deprecated/yanked
            if ecosystem == "npm":
                npm_threats = self._check_npm_audit(pkg_name, ecosystem)
                pkg_threats.extend(npm_threats)
            elif ecosystem == "pypi":
                pypi_threats = self._check_pypi_advisory(pkg_name, ecosystem)
                pkg_threats.extend(pypi_threats)
            
            # Check Snyk (if token available)
            snyk_threats = self._check_snyk(pkg_name, ecosystem)
            pkg_threats.extend(snyk_threats)
            
            # Cache results
            self.cache_manager.store_reputation(cache_key, {"threats": pkg_threats}, ttl_hours=24)
            
            threats.extend(pkg_threats)
        
        return threats
    
    def web_search_threats(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Search authentic security websites for recent supply chain attacks.
        
        **Tool function for agent**
        
        Searches ONLY trusted security sites:
        - snyk.io (Snyk Vulnerability DB)
        - nvd.nist.gov (NIST NVD)
        - cve.mitre.org (MITRE CVE)
        - github.com/advisories (GitHub Security)
        - cvedetails.com (CVE Details)
        
        Args:
            packages: List of package dictionaries
        
        Returns:
            List of threat dictionaries from web search
        """
        threats = []
        
        # Check if Serper API key is available
        if not config.SERPER_API_KEY:
            self._log("  No SERPER_API_KEY configured, skipping web search", "WARNING")
            return threats
        
        self._log(f"  Searching trusted security sites for {len(packages)} packages...")
        
        # Search for each package
        for pkg in packages:
            pkg_name = pkg.get("name")
            ecosystem = pkg.get("ecosystem", "npm")
            
            # Check cache
            cache_key = f"websearch_v2:{ecosystem}:{pkg_name}"
            cached = self.cache_manager.get_reputation(cache_key)
            if cached:
                threats.extend(cached.get("threats", []))
                continue
            
            # Perform web search on trusted sites
            pkg_threats = self._search_trusted_sites(pkg_name, ecosystem)
            
            if pkg_threats:
                self._log(f"    Found {len(pkg_threats)} results for {pkg_name}")
            
            # Cache results
            self.cache_manager.store_reputation(cache_key, {"threats": pkg_threats}, ttl_hours=24)
            
            threats.extend(pkg_threats)
        
        return threats
    
    def llm_analyze_threat(
        self, 
        threats: List[Dict[str, Any]], 
        packages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to analyze threats and provide enhanced assessment.
        
        **Tool function for agent**
        
        Args:
            threats: List of detected threats
            packages: List of all packages
        
        Returns:
            Enhanced threat list with LLM analysis
        """
        if not self.openai_client or not threats:
            return threats
        
        try:
            # Create analysis prompt
            prompt = self._create_llm_analysis_prompt(threats, packages)
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse LLM response
            llm_analysis = json.loads(response.choices[0].message.content)
            
            # Enhance threats with LLM analysis
            for threat in threats:
                pkg_name = threat.get("package_name")
                if pkg_name in llm_analysis.get("package_assessments", {}):
                    assessment = llm_analysis["package_assessments"][pkg_name]
                    threat["llm_assessment"] = assessment.get("assessment")
                    threat["llm_risk_score"] = assessment.get("risk_score")
                    threat["llm_recommendations"] = assessment.get("recommendations", [])
            
            # Add overall assessment
            if threats:
                threats[0]["overall_llm_assessment"] = llm_analysis.get("overall_assessment")
            
        except Exception as e:
            self._log(f"  LLM analysis error: {str(e)}", "WARNING")
        
        return threats
    
    # ==================== HELPER METHODS ====================
    
    def _extract_from_github(self, repo_url: str, target_ecosystem: str = None) -> List[Dict[str, Any]]:
        """Extract packages from GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            target_ecosystem: If specified, only search for manifest files of this ecosystem
        """
        packages = []
        
        try:
            from tools.github_tools import parse_github_url, fetch_file_content
            from tools.api_integration import GitHubAPIClient
            
            owner, repo = parse_github_url(repo_url)
            client = GitHubAPIClient()
            
            manifest_files = {
                "npm": ["package.json"],
                "pypi": ["requirements.txt", "setup.py", "pyproject.toml"]
            }
            
            # Filter to target ecosystem if specified
            if target_ecosystem:
                ecosystems_to_check = {target_ecosystem: manifest_files.get(target_ecosystem, [])}
            else:
                ecosystems_to_check = manifest_files
            
            for ecosystem, files in ecosystems_to_check.items():
                for filename in files:
                    content = fetch_file_content(owner, repo, filename, client)
                    if content:
                        self._log(f"    Found {filename}")
                        extracted = self._parse_manifest(content, filename, ecosystem)
                        packages.extend(extracted)
        
        except Exception as e:
            self._log(f"    GitHub extraction error: {str(e)}", "WARNING")
        
        return packages
    
    def _extract_from_local(self, directory: str, target_ecosystem: str = None) -> List[Dict[str, Any]]:
        """Extract packages from local directory.
        
        Args:
            directory: Local directory path
            target_ecosystem: If specified, only search for manifest files of this ecosystem
        """
        packages = []
        
        try:
            dir_path = Path(directory)
            
            # npm - only if target is npm or not specified
            if not target_ecosystem or target_ecosystem == "npm":
                package_json = dir_path / "package.json"
                if package_json.exists():
                    with open(package_json, 'r', encoding='utf-8') as f:
                        packages.extend(self._parse_manifest(f.read(), "package.json", "npm"))
            
            # Python - only if target is pypi or not specified
            if not target_ecosystem or target_ecosystem == "pypi":
                requirements_txt = dir_path / "requirements.txt"
                if requirements_txt.exists():
                    with open(requirements_txt, 'r', encoding='utf-8') as f:
                        packages.extend(self._parse_manifest(f.read(), "requirements.txt", "pypi"))
        
        except Exception as e:
            self._log(f"    Local extraction error: {str(e)}", "WARNING")
        
        return packages
    
    def _parse_manifest(self, content: str, filename: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Parse manifest file content."""
        packages = []
        
        try:
            if ecosystem == "npm" and "package.json" in filename:
                data = json.loads(content)
                for dep_type in ["dependencies", "devDependencies"]:
                    for name, version in data.get(dep_type, {}).items():
                        packages.append({"name": name, "version": version, "ecosystem": "npm"})
            
            elif ecosystem == "pypi" and "requirements.txt" in filename:
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    match = re.match(r'^([a-zA-Z0-9_.-]+)([><=!~]+)?(.*)$', line)
                    if match:
                        name = match.group(1)
                        version = match.group(3).strip() if match.group(3) else "*"
                        packages.append({"name": name, "version": version, "ecosystem": "pypi"})
        
        except Exception as e:
            self._log(f"    Parse error for {filename}: {str(e)}", "WARNING")
        
        return packages
    
    def _check_snyk(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Check package against Snyk vulnerability database."""
        threats = []
        
        if not config.SNYK_TOKEN:
            return threats
        
        try:
            import requests
            
            # Map ecosystem to Snyk package type
            ecosystem_map = {
                "npm": "npm",
                "pypi": "pip", 
                "maven": "maven",
                "rubygems": "rubygems",
                "go": "golang"
            }
            
            snyk_ecosystem = ecosystem_map.get(ecosystem)
            if not snyk_ecosystem:
                return threats
            
            # Snyk API endpoint for package vulnerabilities
            url = f"https://api.snyk.io/v1/test/{snyk_ecosystem}/{package_name}"
            headers = {
                "Authorization": f"token {config.SNYK_TOKEN}",
                "Content-Type": "application/json"
            }
            
            self._log(f"    Checking Snyk for {package_name}...")
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if package is ok or has issues
                if data.get("ok") == False:
                    issues = data.get("issues", {}).get("vulnerabilities", [])
                    
                    for issue in issues[:3]:  # Limit to top 3
                        severity = issue.get("severity", "medium").lower()
                        
                        threats.append({
                            "package_name": package_name,
                            "package_version": "*",
                            "ecosystem": ecosystem,
                            "threat_type": "snyk_vulnerability",
                            "severity": severity,
                            "confidence": 0.92,
                            "source": "Snyk Vulnerability DB",
                            "description": issue.get("title", "Vulnerability found"),
                            "evidence": {
                                "snyk_id": issue.get("id"),
                                "cvss_score": issue.get("cvssScore"),
                                "cve": issue.get("identifiers", {}).get("CVE", []),
                                "url": issue.get("url", f"https://snyk.io/vuln/{issue.get('id', '')}")
                            },
                            "recommendations": [
                                f"Update {package_name} to version {issue.get('fixedIn', ['latest'])[0] if issue.get('fixedIn') else 'latest'}",
                                f"Review Snyk advisory: https://snyk.io/vuln/{issue.get('id', '')}"
                            ]
                        })
                        self._log(f"    [+] Snyk found: {package_name} - {issue.get('title', '')[:50]}")
                    
            elif response.status_code == 404:
                # Package not found in Snyk - not an error
                pass
            elif response.status_code == 403:
                # API access not available on free plan
                self._log(f"    Snyk API: Requires paid plan for API access", "DEBUG")
            else:
                self._log(f"    Snyk API error for {package_name}: {response.status_code}", "DEBUG")
        
        except Exception as e:
            self._log(f"    Snyk check error for {package_name}: {str(e)}", "DEBUG")
        
        return threats
    
    def _web_search_package(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """
        Search for supply chain attacks using ONLY authentic security sources.
        This is called by web_search_threats for each package.
        """
        # Just call _search_trusted_sites - the main method
        return self._search_trusted_sites(package_name, ecosystem)
    
    def _check_github_advisories(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Check GitHub Security Advisories database."""
        threats = []
        
        try:
            import requests
            
            # GitHub Advisory Database API (public, no auth needed for basic queries)
            # https://github.com/advisories
            ecosystem_map = {"npm": "npm", "pypi": "pip", "maven": "maven", "rubygems": "rubygems"}
            gh_ecosystem = ecosystem_map.get(ecosystem, ecosystem)
            
            url = f"https://api.github.com/advisories"
            params = {
                "affects": package_name,
                "ecosystem": gh_ecosystem,
                "per_page": 5
            }
            headers = {"Accept": "application/vnd.github+json"}
            
            # Add GitHub token if available for higher rate limits
            if config.GITHUB_TOKEN:
                headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                advisories = response.json()
                for advisory in advisories[:3]:
                    severity = advisory.get("severity", "medium").lower()
                    threats.append({
                        "package_name": package_name,
                        "package_version": "*",
                        "ecosystem": ecosystem,
                        "threat_type": "security_advisory",
                        "severity": "critical" if severity in ["critical", "high"] else severity,
                        "confidence": 0.95,
                        "source": "GitHub Security Advisories",
                        "description": advisory.get("summary", "Security advisory found"),
                        "evidence": {
                            "ghsa_id": advisory.get("ghsa_id"),
                            "cve_id": advisory.get("cve_id"),
                            "url": advisory.get("html_url"),
                            "published": advisory.get("published_at")
                        },
                        "recommendations": [
                            f"Review advisory: {advisory.get('html_url', '')}",
                            f"Update {package_name} to patched version"
                        ]
                    })
                    self._log(f"    Found GitHub advisory for {package_name}: {advisory.get('ghsa_id')}")
        
        except Exception as e:
            self._log(f"    GitHub advisories check error: {str(e)}", "DEBUG")
        
        return threats
    
    def _check_npm_audit(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Check npm registry for security advisories."""
        threats = []
        
        if ecosystem != "npm":
            return threats
        
        try:
            import requests
            
            # npm registry API - check package for security holds
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if package is deprecated or has security issues
                if data.get("deprecated"):
                    threats.append({
                        "package_name": package_name,
                        "package_version": "*",
                        "ecosystem": ecosystem,
                        "threat_type": "deprecated_package",
                        "severity": "medium",
                        "confidence": 0.85,
                        "source": "npm Registry",
                        "description": f"Package is deprecated: {data.get('deprecated', 'No reason given')}",
                        "evidence": {"deprecated_message": data.get("deprecated")},
                        "recommendations": [f"Find alternative to {package_name}"]
                    })
        
        except Exception as e:
            self._log(f"    npm audit check error: {str(e)}", "DEBUG")
        
        return threats
    
    def _check_pypi_advisory(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Check PyPI for package advisories."""
        threats = []
        
        if ecosystem != "pypi":
            return threats
        
        try:
            import requests
            
            # PyPI JSON API
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                info = data.get("info", {})
                
                # Check for yanked versions or project status
                if info.get("yanked"):
                    threats.append({
                        "package_name": package_name,
                        "package_version": "*",
                        "ecosystem": ecosystem,
                        "threat_type": "yanked_package",
                        "severity": "high",
                        "confidence": 0.9,
                        "source": "PyPI Registry",
                        "description": f"Package version was yanked (removed for security/critical bug)",
                        "evidence": {"yanked_reason": info.get("yanked_reason", "Unknown")},
                        "recommendations": [f"Update {package_name} to a non-yanked version"]
                    })
        
        except Exception as e:
            self._log(f"    PyPI advisory check error: {str(e)}", "DEBUG")
        
        return threats
    
    def _search_trusted_sites(self, package_name: str, ecosystem: str) -> List[Dict[str, Any]]:
        """
        Search ONLY trusted security sites using Serper API.
        
        Trusted sites:
        - snyk.io/vuln
        - nvd.nist.gov
        - cve.mitre.org
        - github.com/advisories
        - cvedetails.com
        """
        threats = []
        
        if not config.SERPER_API_KEY:
            return threats
        
        # Define trusted security domains
        trusted_domains = [
            "snyk.io",
            "nvd.nist.gov",
            "cve.mitre.org",
            "github.com",
            "cvedetails.com",
            "security.snyk.io",
            "securityfocus.com"
        ]
        
        try:
            import requests
            
            # Search query targeting security sites - simpler query
            query = f'"{package_name}" vulnerability OR CVE OR security'
            
            self._log(f"    Serper search: {package_name}")
            
            response = requests.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": 10},
                headers={
                    "X-API-KEY": config.SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=15
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("message", response.text[:100]) if response.text else "Unknown error"
                if "credits" in error_msg.lower():
                    self._log(f"    ⚠️ Serper API: Out of credits - get more at https://serper.dev", "WARNING")
                else:
                    self._log(f"    Serper API error: {response.status_code} - {error_msg}", "WARNING")
                return threats
            
            data = response.json()
            results = data.get("organic", [])
            
            self._log(f"    Serper returned {len(results)} results")
            
            for result in results:
                url = result.get("link", "").lower()
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                # Only accept results from trusted domains
                is_trusted = any(domain in url for domain in trusted_domains)
                
                if not is_trusted:
                    continue
                
                # Determine severity from content
                content = (title + " " + snippet).lower()
                if "critical" in content or "remote code execution" in content or "rce" in content:
                    severity = "critical"
                elif "high" in content or "injection" in content or "xss" in content:
                    severity = "high"
                else:
                    severity = "medium"
                
                threats.append({
                    "package_name": package_name,
                    "package_version": "*",
                    "ecosystem": ecosystem,
                    "threat_type": "web_intelligence",
                    "severity": severity,
                    "confidence": 0.85,
                    "source": self._get_source_name(result.get("link", "")),
                    "description": title[:100],
                    "evidence": {
                        "title": title,
                        "snippet": snippet[:200],
                        "url": result.get("link")
                    },
                    "recommendations": [
                        f"Review: {result.get('link')}",
                        f"Check if {package_name} version is affected"
                    ]
                })
                self._log(f"    [+] Web intel: {package_name} from {self._get_source_name(result.get('link', ''))}")
        
        except Exception as e:
            self._log(f"    Trusted sites search error: {str(e)}", "DEBUG")
        
        return threats
    
    def _get_source_name(self, url: str) -> str:
        """Get friendly source name from URL."""
        if "snyk.io" in url:
            return "Snyk Vulnerability DB"
        elif "nvd.nist.gov" in url:
            return "NIST NVD"
        elif "cve.mitre.org" in url:
            return "MITRE CVE"
        elif "github.com" in url:
            return "GitHub Advisories"
        elif "npmjs.com" in url:
            return "npm Security"
        elif "pypi.org" in url:
            return "PyPI Security"
        elif "cvedetails.com" in url:
            return "CVE Details"
        else:
            return "Security Advisory"
    
    def _create_llm_analysis_prompt(self, threats: List[Dict[str, Any]], packages: List[Dict[str, Any]]) -> str:
        """Create prompt for LLM threat analysis."""
        return f"""Analyze these supply chain security threats and provide assessment.

DETECTED THREATS:
{json.dumps(threats[:10], indent=2)}

ALL PACKAGES ({len(packages)} total):
{json.dumps([p['name'] for p in packages[:20]], indent=2)}

Provide JSON response with:
{{
    "overall_assessment": "Brief overall security assessment",
    "risk_level": "critical/high/medium/low",
    "package_assessments": {{
        "package_name": {{
            "assessment": "Specific assessment for this package",
            "risk_score": 0.0-1.0,
            "recommendations": ["List of specific recommendations"]
        }}
    }},
    "priority_actions": ["Top 3 priority actions to take"]
}}"""
    
    def _deduplicate_threats(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate threats."""
        seen = set()
        unique = []
        for threat in threats:
            key = f"{threat['package_name']}:{threat['threat_type']}:{threat.get('source', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(threat)
        return unique
    
    def _calculate_overall_confidence(self, threats: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score."""
        if not threats:
            return 1.0
        return sum(t.get("confidence", 0.5) for t in threats) / len(threats)
    
    def _map_severity(self, severity: str) -> str:
        """Map severity to standard levels."""
        s = str(severity).lower()
        if "critical" in s or "high" in s:
            return "critical"
        elif "medium" in s or "moderate" in s:
            return "high"
        return "medium"
