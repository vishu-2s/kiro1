"""
Python Ecosystem Analyzer for Multi-Agent Security Analysis System.

This module provides Python/PyPI-specific analysis functionality using the
EcosystemAnalyzer framework.
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

from tools.ecosystem_analyzer import EcosystemAnalyzer, SecurityFinding, register_analyzer

logger = logging.getLogger(__name__)


class PythonAnalyzer(EcosystemAnalyzer):
    """Python/PyPI ecosystem analyzer."""
    
    @property
    def ecosystem_name(self) -> str:
        """Return ecosystem name."""
        return "pypi"
    
    def detect_manifest_files(self, directory: str) -> List[str]:
        """
        Detect Python manifest files (setup.py, requirements.txt, pyproject.toml).
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            List of manifest file paths found
        """
        manifest_files = []
        manifest_patterns = ["setup.py", "requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock"]
        
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.warning(f"Directory does not exist or is not a directory: {directory}")
                return []
            
            for pattern in manifest_patterns:
                file_path = dir_path / pattern
                if file_path.exists() and file_path.is_file():
                    manifest_files.append(str(file_path))
                    logger.debug(f"Found Python manifest file: {file_path}")
        
        except Exception as e:
            logger.error(f"Error detecting Python manifest files in {directory}: {e}")
        
        return manifest_files
    
    def extract_dependencies(self, manifest_path: str) -> List[Dict[str, Any]]:
        """
        Extract dependencies from Python manifest files.
        
        Args:
            manifest_path: Path to manifest file (requirements.txt, setup.py, etc.)
            
        Returns:
            List of dependency dictionaries
        """
        file_name = os.path.basename(manifest_path).lower()
        
        if "requirements" in file_name and file_name.endswith(".txt"):
            return self._extract_from_requirements_txt(manifest_path)
        elif file_name == "setup.py":
            return self._extract_from_setup_py(manifest_path)
        elif file_name == "pyproject.toml":
            return self._extract_from_pyproject_toml(manifest_path)
        elif file_name in ["pipfile", "pipfile.lock"]:
            return self._extract_from_pipfile(manifest_path)
        else:
            logger.warning(f"Unsupported Python manifest file: {manifest_path}")
            return []
    
    def _extract_from_requirements_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract dependencies from requirements.txt."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Skip -r/-e flags (recursive requirements, editable installs)
                if line.startswith('-r') or line.startswith('-e'):
                    continue
                
                # Parse requirement line (package==version, package>=version, etc.)
                match = re.match(r'^([a-zA-Z0-9_.-]+)([><=!~]+)(.+)$', line)
                if match:
                    name, operator, version = match.groups()
                    dependency = {
                        "name": name,
                        "version": version.strip(),
                        "ecosystem": "pypi",
                        "dependency_type": "requirements",
                        "version_operator": operator,
                        "source_file": file_path
                    }
                    dependencies.append(dependency)
                    logger.debug(f"Extracted Python dependency: {name}{operator}{version}")
                else:
                    # Simple package name without version
                    if re.match(r'^[a-zA-Z0-9_.-]+$', line):
                        dependency = {
                            "name": line,
                            "version": "*",
                            "ecosystem": "pypi",
                            "dependency_type": "requirements",
                            "source_file": file_path
                        }
                        dependencies.append(dependency)
                        logger.debug(f"Extracted Python dependency: {line}")
        
        except Exception as e:
            logger.error(f"Error extracting dependencies from {file_path}: {e}")
        
        return dependencies
    
    def _extract_from_setup_py(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract dependencies from setup.py using AST parsing."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse setup.py safely using AST
            tree = ast.parse(content, filename=file_path)
            
            # Find setup() call
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this is a setup() call
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        # Extract install_requires
                        for keyword in node.keywords:
                            if keyword.arg in ['install_requires', 'requires', 'setup_requires']:
                                dep_type = keyword.arg
                                
                                # Extract list of dependencies
                                if isinstance(keyword.value, ast.List):
                                    for elt in keyword.value.elts:
                                        if isinstance(elt, ast.Constant):
                                            dep_string = elt.value
                                            dep_info = self._parse_dependency_string(dep_string)
                                            if dep_info:
                                                dep_info.update({
                                                    "ecosystem": "pypi",
                                                    "dependency_type": dep_type,
                                                    "source_file": file_path
                                                })
                                                dependencies.append(dep_info)
                                                logger.debug(f"Extracted Python dependency from setup.py: {dep_info['name']}")
        
        except SyntaxError as e:
            logger.error(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error extracting dependencies from {file_path}: {e}")
        
        return dependencies
    
    def _extract_from_pyproject_toml(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract dependencies from pyproject.toml."""
        dependencies = []
        
        try:
            # Try to import toml library
            try:
                import toml
            except ImportError:
                logger.warning("toml library not available, skipping pyproject.toml parsing")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Extract dependencies from different sections
            # Poetry format
            if 'tool' in data and 'poetry' in data['tool']:
                poetry_deps = data['tool']['poetry'].get('dependencies', {})
                for name, version_spec in poetry_deps.items():
                    if name == 'python':  # Skip python version requirement
                        continue
                    
                    version = version_spec if isinstance(version_spec, str) else "*"
                    dependency = {
                        "name": name,
                        "version": version,
                        "ecosystem": "pypi",
                        "dependency_type": "poetry_dependencies",
                        "source_file": file_path
                    }
                    dependencies.append(dependency)
            
            # PEP 621 format
            if 'project' in data:
                project_deps = data['project'].get('dependencies', [])
                for dep_string in project_deps:
                    dep_info = self._parse_dependency_string(dep_string)
                    if dep_info:
                        dep_info.update({
                            "ecosystem": "pypi",
                            "dependency_type": "project_dependencies",
                            "source_file": file_path
                        })
                        dependencies.append(dep_info)
        
        except Exception as e:
            logger.error(f"Error extracting dependencies from {file_path}: {e}")
        
        return dependencies
    
    def _extract_from_pipfile(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract dependencies from Pipfile."""
        dependencies = []
        
        try:
            # Try to import toml library
            try:
                import toml
            except ImportError:
                logger.warning("toml library not available, skipping Pipfile parsing")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Extract from packages and dev-packages sections
            for section in ['packages', 'dev-packages']:
                packages = data.get(section, {})
                for name, version_spec in packages.items():
                    version = version_spec if isinstance(version_spec, str) else "*"
                    dependency = {
                        "name": name,
                        "version": version,
                        "ecosystem": "pypi",
                        "dependency_type": section,
                        "source_file": file_path
                    }
                    dependencies.append(dependency)
        
        except Exception as e:
            logger.error(f"Error extracting dependencies from {file_path}: {e}")
        
        return dependencies
    
    def _parse_dependency_string(self, dep_string: str) -> Optional[Dict[str, Any]]:
        """Parse a dependency string like 'requests>=2.0.0'."""
        match = re.match(r'^([a-zA-Z0-9_.-]+)([><=!~]+)(.+)$', dep_string.strip())
        if match:
            name, operator, version = match.groups()
            return {
                "name": name,
                "version": version.strip(),
                "version_operator": operator
            }
        else:
            # Simple package name without version
            if re.match(r'^[a-zA-Z0-9_.-]+$', dep_string.strip()):
                return {
                    "name": dep_string.strip(),
                    "version": "*"
                }
        return None
    
    def analyze_install_scripts(self, directory: str) -> List[SecurityFinding]:
        """
        Analyze setup.py for malicious installation hooks and patterns.
        Integrates pattern matching with LLM analysis for complex cases.
        
        Args:
            directory: Path to directory containing setup.py
            
        Returns:
            List of security findings from script analysis
        """
        findings = []
        
        try:
            setup_py_path = Path(directory) / "setup.py"
            if not setup_py_path.exists():
                logger.debug(f"No setup.py found in {directory}")
                return []
            
            with open(setup_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze using AST for installation hooks
            findings.extend(self._analyze_setup_py_ast(setup_py_path, content))
            
            # Analyze using pattern matching + LLM for malicious code
            # This method now includes complexity detection and LLM routing
            findings.extend(self._analyze_setup_py_patterns(setup_py_path, content))
        
        except Exception as e:
            logger.error(f"Error analyzing Python install scripts in {directory}: {e}")
        
        return findings
    
    def _analyze_setup_py_ast(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """Analyze setup.py using AST to detect installation hooks."""
        findings = []
        
        try:
            tree = ast.parse(content, filename=str(file_path))
            
            # Track suspicious installation hooks
            suspicious_hooks = []
            
            # Find setup() call and check for cmdclass
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        for keyword in node.keywords:
                            # Check for cmdclass (custom command classes)
                            if keyword.arg == 'cmdclass':
                                suspicious_hooks.append({
                                    "hook_type": "cmdclass",
                                    "line": keyword.lineno,
                                    "description": "Custom command class defined (cmdclass)"
                                })
                            
                            # Check for setup_requires (dependencies needed during setup)
                            elif keyword.arg == 'setup_requires':
                                suspicious_hooks.append({
                                    "hook_type": "setup_requires",
                                    "line": keyword.lineno,
                                    "description": "Setup-time dependencies (setup_requires)"
                                })
            
            # If suspicious hooks found, create findings
            if suspicious_hooks:
                evidence = [f"File: {file_path}"]
                evidence.extend([f"Line {hook['line']}: {hook['description']}" for hook in suspicious_hooks])
                
                finding = SecurityFinding(
                    package=file_path.parent.name,
                    version="*",
                    finding_type="installation_hooks",
                    severity="medium",
                    confidence=0.6,
                    evidence=evidence,
                    recommendations=[
                        "Review the installation hooks to ensure they don't execute malicious code",
                        "Check if cmdclass or setup_requires are necessary for legitimate functionality",
                        "Consider using pyproject.toml instead of setup.py for safer configuration"
                    ],
                    source="python_ast_analysis"
                )
                findings.append(finding)
                logger.info(f"Detected {len(suspicious_hooks)} installation hooks in {file_path}")
        
        except SyntaxError as e:
            logger.error(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error in AST analysis of {file_path}: {e}")
        
        return findings
    
    def _analyze_setup_py_patterns(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """Analyze setup.py using pattern matching for malicious code."""
        findings = []
        
        malicious_patterns = self.get_malicious_patterns()
        detected_patterns = []
        max_severity = "low"
        
        # Check for malicious patterns
        for severity, patterns in malicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected_patterns.append(pattern)
                    # Update max severity
                    severity_priority = {"critical": 3, "high": 2, "medium": 1, "low": 0}
                    if severity_priority.get(severity, 0) > severity_priority.get(max_severity, 0):
                        max_severity = severity
        
        # Check if script is complex enough to warrant LLM analysis
        complexity_score = self._calculate_complexity_score(content)
        is_complex = complexity_score >= 0.5  # Threshold for complexity
        
        # If malicious patterns found or script is complex, analyze further
        if detected_patterns or is_complex:
            # Try LLM analysis for complex patterns
            llm_result = None
            if is_complex or len(detected_patterns) >= 2:
                llm_result = self._analyze_script_with_llm(content, file_path.parent.name)
            
            # Combine pattern matching and LLM results
            if llm_result and llm_result.get("is_suspicious"):
                # LLM found something suspicious - use LLM results
                evidence = [
                    f"File: {file_path}",
                    f"LLM Analysis: {llm_result.get('reasoning', 'Suspicious behavior detected')}"
                ]
                
                if detected_patterns:
                    evidence.append(f"Pattern matching detected {len(detected_patterns)} suspicious patterns")
                    evidence.extend([f"Pattern: {p}" for p in detected_patterns[:3]])
                
                if llm_result.get('threats'):
                    evidence.append("Threats identified:")
                    evidence.extend([f"- {threat}" for threat in llm_result['threats'][:5]])
                
                # Use LLM severity if higher than pattern severity
                llm_severity = llm_result.get('severity', 'medium')
                severity_priority = {"critical": 3, "high": 2, "medium": 1, "low": 0}
                if severity_priority.get(llm_severity, 0) > severity_priority.get(max_severity, 0):
                    max_severity = llm_severity
                
                # Use LLM confidence
                confidence = llm_result.get('confidence', 0.7)
                
                finding = SecurityFinding(
                    package=file_path.parent.name,
                    version="*",
                    finding_type="malicious_python_script",
                    severity=max_severity,
                    confidence=confidence,
                    evidence=evidence,
                    recommendations=[
                        "URGENT: Review this setup.py file immediately for malicious code",
                        "Do not install this package until verified safe",
                        "Check the package source and author reputation",
                        "Consider reporting this package to PyPI security team"
                    ],
                    source="python_llm_analysis"
                )
                findings.append(finding)
                logger.warning(f"LLM detected malicious behavior in {file_path} (severity: {max_severity}, confidence: {confidence})")
            
            elif detected_patterns:
                # Only pattern matching found issues (no LLM or LLM said not suspicious)
                evidence = [
                    f"File: {file_path}",
                    f"Detected {len(detected_patterns)} malicious patterns"
                ]
                evidence.extend([f"Pattern: {p}" for p in detected_patterns[:5]])
                
                # If LLM analyzed but said not suspicious, lower confidence
                confidence = 0.6 if llm_result else 0.8
                
                finding = SecurityFinding(
                    package=file_path.parent.name,
                    version="*",
                    finding_type="malicious_python_script",
                    severity=max_severity,
                    confidence=confidence,
                    evidence=evidence,
                    recommendations=[
                        "URGENT: Review this setup.py file immediately for malicious code",
                        "Do not install this package until verified safe",
                        "Check the package source and author reputation",
                        "Consider reporting this package to PyPI security team"
                    ],
                    source="python_pattern_analysis"
                )
                findings.append(finding)
                logger.warning(f"Detected malicious patterns in {file_path} (severity: {max_severity})")
        
        return findings
    
    def get_registry_url(self, package_name: str) -> str:
        """
        Return PyPI registry API URL for package metadata.
        
        Args:
            package_name: Name of the Python package
            
        Returns:
            Full URL to package metadata endpoint
        """
        return f"https://pypi.org/pypi/{package_name}/json"
    
    def get_malicious_patterns(self) -> Dict[str, List[str]]:
        """
        Return Python-specific malicious patterns.
        
        Returns:
            Dictionary mapping severity levels to regex patterns
        """
        return {
            "critical": [
                r'os\.system\s*\(',
                r'subprocess\.(?:call|run|Popen)\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(\s*["\'](?:os|subprocess)',
                r'urllib\.request\.urlopen',
                r'requests\.get.*\|\s*(?:sh|bash)',
            ],
            "high": [
                r'open\s*\(\s*["\'](?:/etc/|/root/|~/.ssh)',
                r'compile\s*\(',
                r'globals\s*\(\s*\)',
                r'locals\s*\(\s*\)',
                r'base64\.b64decode',
                r'pickle\.loads',
            ],
            "medium": [
                r'socket\.socket',
                r'http\.client',
                r'ftplib',
                r'telnetlib',
                r'smtplib',
                r'os\.environ',
                r'sys\.path\.insert',
            ]
        }
    
    def _calculate_complexity_score(self, script_content: str) -> float:
        """
        Calculate complexity score for a Python script to determine if LLM analysis is needed.
        
        Args:
            script_content: Python script content
            
        Returns:
            Complexity score from 0.0 (simple) to 1.0 (very complex)
        """
        complexity_indicators = {
            # Obfuscation indicators (high weight)
            r'base64\.(?:b64decode|b64encode)': 0.3,
            r'hex\s*\(': 0.2,
            r'chr\s*\(': 0.2,
            r'ord\s*\(': 0.2,
            r'\\x[0-9a-fA-F]{2}': 0.2,  # Hex escape sequences
            r'\\u[0-9a-fA-F]{4}': 0.2,  # Unicode escape sequences
            
            # Dynamic code execution (high weight)
            r'eval\s*\(': 0.4,
            r'exec\s*\(': 0.4,
            r'compile\s*\(': 0.3,
            r'__import__\s*\(': 0.3,
            
            # String manipulation that could hide intent (medium weight)
            r'\.join\s*\(': 0.1,
            r'\.replace\s*\(': 0.1,
            r'\.decode\s*\(': 0.15,
            r'\.encode\s*\(': 0.1,
            
            # Network operations (medium weight)
            r'urllib\.request': 0.2,
            r'requests\.(?:get|post)': 0.2,
            r'socket\.socket': 0.25,
            r'http\.client': 0.2,
            
            # System operations (medium weight)
            r'os\.system': 0.3,
            r'subprocess\.': 0.3,
            r'os\.popen': 0.3,
            
            # File operations on sensitive paths (medium weight)
            r'/etc/': 0.2,
            r'/root/': 0.2,
            r'~/.ssh': 0.25,
            r'\.bashrc': 0.2,
            
            # Multiple layers of function calls (low weight)
            r'\(\s*\(': 0.1,  # Nested parentheses
        }
        
        score = 0.0
        matched_indicators = []
        
        for pattern, weight in complexity_indicators.items():
            matches = re.findall(pattern, script_content, re.IGNORECASE)
            if matches:
                # Add weight, but with diminishing returns for multiple matches
                contribution = weight * min(1.0, len(matches) / 3.0)
                score += contribution
                matched_indicators.append(pattern)
        
        # Additional complexity factors
        
        # Long lines can indicate obfuscation
        lines = script_content.split('\n')
        long_lines = [line for line in lines if len(line) > 200]
        if long_lines:
            score += min(0.2, len(long_lines) * 0.05)
        
        # Very long scripts might be complex
        if len(script_content) > 1000:
            score += 0.1
        if len(script_content) > 5000:
            score += 0.2
        
        # Multiple suspicious patterns together increase complexity
        if len(matched_indicators) > 5:
            score += 0.2
        
        # Cap at 1.0
        final_score = min(1.0, score)
        
        if final_score >= 0.5:
            logger.debug(f"High complexity score: {final_score:.2f} (matched {len(matched_indicators)} indicators)")
        
        return final_score
    
    def _analyze_script_with_llm(self, script_content: str, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze Python script for sophisticated/obfuscated malicious behavior.
        Uses intelligent caching to avoid redundant API calls.
        
        Args:
            script_content: The Python script content to analyze
            package_name: Name of the package
            
        Returns:
            Dictionary with LLM analysis results or None if LLM unavailable
        """
        from config import config
        from tools.cache_manager import get_cache_manager
        
        # Skip if OpenAI not configured
        if not config.OPENAI_API_KEY:
            logger.debug("OpenAI API key not configured, skipping LLM analysis")
            return None
        
        # Skip for very short/simple scripts to save API costs
        if len(script_content) < 50:
            logger.debug(f"Script too short ({len(script_content)} chars), skipping LLM analysis")
            return None
        
        try:
            # Initialize cache manager
            cache_manager = get_cache_manager()
            
            # Generate cache key from script content and package name
            cache_content = f"python:{package_name}:{script_content}"
            cache_key = cache_manager.generate_cache_key(cache_content, prefix="llm_python")
            
            # Check cache first (Property 6: Cache-First Lookup)
            cached_result = cache_manager.get_llm_analysis(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for LLM analysis of Python package '{package_name}'")
                return cached_result
            
            logger.info(f"Cache miss for LLM analysis of Python package '{package_name}', calling LLM API")
            
            # Cache miss - perform LLM analysis
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            
            prompt = f"""Analyze this Python setup.py script for malicious behavior:

Package: {package_name}
Script content (first 2000 chars):
{script_content[:2000]}

Look for:
1. Remote code execution (downloading and executing code)
2. Data exfiltration (sending files/data to external servers)
3. Obfuscation techniques (base64, hex encoding, eval, exec)
4. System modification (changing permissions, modifying system files)
5. Credential theft (accessing environment variables, config files, SSH keys)
6. Backdoors or persistence mechanisms
7. Suspicious network connections to unknown domains
8. File system manipulation outside the package directory

Consider that legitimate setup.py scripts may:
- Compile C extensions
- Check Python version requirements
- Install package dependencies
- Create necessary directories in site-packages
- Run build tools (setuptools, distutils)

Respond in JSON format:
{{
    "is_suspicious": true/false,
    "confidence": 0.0-1.0,
    "severity": "critical"/"high"/"medium"/"low",
    "threats": ["list of specific threats found"],
    "reasoning": "brief explanation of why this is or isn't suspicious"
}}"""

            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing Python setup.py scripts for supply chain attacks. Be precise and avoid false positives. Legitimate build scripts often use subprocess for compilation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            # Store result in cache for future use
            cache_manager.store_llm_analysis(cache_key, result)
            logger.info(f"LLM analysis for Python package '{package_name}': suspicious={result.get('is_suspicious')}, confidence={result.get('confidence')} (cached)")
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM analysis failed for Python package '{package_name}': {e}")
            # Graceful fallback - continue without caching
            return None
    
    def check_malicious_packages(self, dependencies: List[Dict[str, Any]]) -> List[SecurityFinding]:
        """
        Check dependencies against known malicious package database.
        
        Args:
            dependencies: List of dependency dictionaries
            
        Returns:
            List of security findings for malicious packages
        """
        findings = []
        
        try:
            from constants import KNOWN_MALICIOUS_PACKAGES
            
            # Get PyPI malicious packages
            malicious_packages = KNOWN_MALICIOUS_PACKAGES.get("pypi", [])
            
            for dep in dependencies:
                package_name = dep.get("name", "").lower()
                package_version = dep.get("version", "*")
                
                # Check against malicious package database
                for malicious_pkg in malicious_packages:
                    if malicious_pkg["name"].lower() == package_name:
                        # Found a match - create security finding
                        finding = SecurityFinding(
                            package=package_name,
                            version=package_version,
                            finding_type="malicious_package",
                            severity="critical",
                            confidence=0.95,
                            evidence=[
                                f"Package '{package_name}' found in malicious package database",
                                f"Reason: {malicious_pkg.get('reason', 'Known malicious package')}",
                                f"Version constraint: {malicious_pkg.get('version', '*')}",
                                f"Source file: {dep.get('source_file', 'unknown')}"
                            ],
                            recommendations=[
                                f"URGENT: Remove '{package_name}' immediately from your dependencies",
                                "Scan your system for signs of compromise",
                                "Review all code that may have been affected by this package",
                                "Check for any unauthorized network activity or file modifications",
                                "Report this incident to your security team"
                            ],
                            source="python_malicious_db_check"
                        )
                        findings.append(finding)
                        logger.warning(f"Detected malicious Python package: {package_name}")
                        break  # Only report once per package
        
        except Exception as e:
            logger.error(f"Error checking malicious packages: {e}")
        
        return findings
    
    def scan_recursive_dependencies(self, package_name: str, max_depth: int = 5, 
                                   visited: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """
        Recursively scan pip dependencies for a package.
        
        Args:
            package_name: Name of the package to scan
            max_depth: Maximum recursion depth
            visited: Set of already visited packages (to avoid cycles)
            
        Returns:
            List of all transitive dependencies
        """
        if visited is None:
            visited = set()
        
        # Avoid infinite recursion
        if package_name in visited or max_depth <= 0:
            return []
        
        visited.add(package_name)
        all_dependencies = []
        
        try:
            import subprocess
            import json
            
            # Use pip show to get package info
            result = subprocess.run(
                ['pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse pip show output
                lines = result.stdout.split('\n')
                requires_line = None
                version = "*"
                
                for line in lines:
                    if line.startswith('Version:'):
                        version = line.split(':', 1)[1].strip()
                    elif line.startswith('Requires:'):
                        requires_line = line.split(':', 1)[1].strip()
                
                if requires_line and requires_line != '':
                    # Parse dependencies
                    dep_names = [dep.strip() for dep in requires_line.split(',')]
                    
                    for dep_name in dep_names:
                        if dep_name:
                            # Add this dependency
                            dep_info = {
                                "name": dep_name,
                                "version": "*",  # pip show doesn't give version constraints
                                "ecosystem": "pypi",
                                "dependency_type": "transitive",
                                "parent": package_name,
                                "depth": 6 - max_depth  # Calculate depth
                            }
                            all_dependencies.append(dep_info)
                            
                            # Recursively scan this dependency
                            transitive_deps = self.scan_recursive_dependencies(
                                dep_name, 
                                max_depth - 1, 
                                visited
                            )
                            all_dependencies.extend(transitive_deps)
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout scanning dependencies for {package_name}")
        except FileNotFoundError:
            logger.warning("pip command not found - cannot scan recursive dependencies")
        except Exception as e:
            logger.error(f"Error scanning recursive dependencies for {package_name}: {e}")
        
        return all_dependencies
    
    def analyze_dependencies_with_malicious_check(self, directory: str) -> List[SecurityFinding]:
        """
        Analyze all Python dependencies in a directory and check for malicious packages.
        
        Args:
            directory: Path to directory containing Python project
            
        Returns:
            List of security findings from dependency analysis
        """
        findings = []
        all_dependencies = []
        
        try:
            # Detect manifest files
            manifest_files = self.detect_manifest_files(directory)
            
            # Extract dependencies from all manifest files
            for manifest_path in manifest_files:
                deps = self.extract_dependencies(manifest_path)
                all_dependencies.extend(deps)
                logger.info(f"Extracted {len(deps)} dependencies from {manifest_path}")
            
            # Check direct dependencies against malicious database
            malicious_findings = self.check_malicious_packages(all_dependencies)
            findings.extend(malicious_findings)
            
            # Optionally scan recursive dependencies for each direct dependency
            # Note: This can be slow, so we limit it to direct dependencies only
            logger.info(f"Checking {len(all_dependencies)} Python dependencies for malicious packages")
            
            # For each direct dependency, we could scan recursively, but that's expensive
            # Instead, we'll just check the direct dependencies we already extracted
            # The recursive scanning can be done on-demand or for specific packages
            
        except Exception as e:
            logger.error(f"Error analyzing Python dependencies: {e}")
        
        return findings


# Register the Python analyzer with the global registry
def _register_python_analyzer():
    """Register Python analyzer with global registry."""
    try:
        analyzer = PythonAnalyzer()
        register_analyzer(analyzer)
        logger.info("Python analyzer registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Python analyzer: {e}")


# Auto-register when module is imported
_register_python_analyzer()
