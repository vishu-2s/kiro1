"""
SBOM (Software Bill of Materials) processing tools for Multi-Agent Security Analysis System.

This module provides functions for:
- Reading and parsing SBOM files in various formats
- Detecting vulnerable packages using malicious package database
- OSV API integration for vulnerability detection
- Ecosystem detection for different package managers
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from datetime import datetime
import logging

from constants import (
    KNOWN_MALICIOUS_PACKAGES, 
    TYPOSQUAT_TARGETS,
    SUSPICIOUS_KEYWORDS,
    ECOSYSTEM_FILES,
    get_ecosystem_from_file,
    is_suspicious_package_name,
    contains_suspicious_keywords,
    calculate_typosquat_confidence,
    is_legitimate_package_pattern,
    detect_suspicious_network_patterns
)
from config import config
from tools.api_integration import OSVAPIClient

logger = logging.getLogger(__name__)

class SBOMPackage:
    """Represents a package in an SBOM."""
    
    def __init__(self, name: str, version: str, purl: str = "", ecosystem: str = "", 
                 dependencies: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.version = version
        self.purl = purl  # Package URL
        self.ecosystem = ecosystem
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert package to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "purl": self.purl,
            "ecosystem": self.ecosystem,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }

class SecurityFinding:
    """Represents a security finding for a package."""
    
    def __init__(self, package: str, version: str, finding_type: str, 
                 severity: str, confidence: float, evidence: List[str], 
                 recommendations: List[str], source: str = "sbom_tools"):
        self.package = package
        self.version = version
        self.finding_type = finding_type
        self.severity = severity
        self.confidence = confidence
        self.evidence = evidence
        self.recommendations = recommendations
        self.source = source
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "package": self.package,
            "version": self.version,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "source": self.source,
            "timestamp": self.timestamp
        }

def detect_ecosystem(file_path: str, content: Optional[str] = None) -> str:
    """
    Detect the ecosystem type from file path or content.
    
    Args:
        file_path: Path to the package file
        content: Optional file content for additional detection
    
    Returns:
        Detected ecosystem type (npm, pypi, maven, rubygems, crates, go, unknown)
    """
    filename = Path(file_path).name.lower()
    
    # Direct file name matching
    ecosystem_mapping = {
        "package.json": "npm",
        "package-lock.json": "npm", 
        "yarn.lock": "npm",
        "npm-shrinkwrap.json": "npm",
        "requirements.txt": "pypi",
        "setup.py": "pypi",
        "pyproject.toml": "pypi",
        "pipfile": "pypi",
        "pipfile.lock": "pypi",
        "pom.xml": "maven",
        "build.gradle": "maven",
        "gradle.properties": "maven",
        "gemfile": "rubygems",
        "gemfile.lock": "rubygems",
        "cargo.toml": "crates",
        "cargo.lock": "crates",
        "go.mod": "go",
        "go.sum": "go"
    }
    
    if filename in ecosystem_mapping:
        return ecosystem_mapping[filename]
    
    # Extension-based detection
    if filename.endswith(".gemspec"):
        return "rubygems"
    
    # Content-based detection if available
    if content:
        content_lower = content.lower()
        if '"dependencies"' in content_lower and '"name"' in content_lower:
            return "npm"
        elif 'install_requires' in content_lower or 'setup(' in content_lower:
            return "pypi"
        elif '<groupId>' in content_lower and '<artifactId>' in content_lower:
            return "maven"
        elif '[dependencies]' in content_lower and 'version =' in content_lower:
            return "crates"
        elif 'module ' in content_lower and 'require ' in content_lower:
            return "go"
    
    return "unknown"

def read_sbom(file_path: str) -> Dict[str, Any]:
    """
    Read and parse SBOM file in various formats (JSON, XML, YAML).
    
    Args:
        file_path: Path to the SBOM file
    
    Returns:
        Parsed SBOM data as dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SBOM file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detect file format and parse accordingly
        if path.suffix.lower() == '.json' or content.strip().startswith('{'):
            return _parse_json_sbom(content, str(path))
        elif path.suffix.lower() in ['.xml', '.spdx'] or content.strip().startswith('<'):
            return _parse_xml_sbom(content, str(path))
        elif path.suffix.lower() in ['.yaml', '.yml']:
            import yaml
            return _parse_yaml_sbom(content, str(path))
        else:
            # Try to detect format from content
            content_stripped = content.strip()
            if content_stripped.startswith('{'):
                return _parse_json_sbom(content, str(path))
            elif content_stripped.startswith('<'):
                return _parse_xml_sbom(content, str(path))
            else:
                raise ValueError(f"Unsupported SBOM format: {file_path}")
    
    except Exception as e:
        logger.error(f"Error reading SBOM file {file_path}: {e}")
        raise ValueError(f"Failed to parse SBOM file {file_path}: {e}")

def _parse_json_sbom(content: str, file_path: str) -> Dict[str, Any]:
    """Parse JSON format SBOM."""
    try:
        data = json.loads(content)
        
        # Handle different JSON SBOM formats
        if 'components' in data:
            # CycloneDX format
            return _normalize_cyclonedx_sbom(data, file_path)
        elif 'packages' in data:
            # SPDX JSON format
            return _normalize_spdx_json_sbom(data, file_path)
        elif 'dependencies' in data and 'name' in data:
            # npm package.json format
            return _normalize_npm_package_json(data, file_path)
        else:
            # Generic format - try to extract packages
            return _normalize_generic_json_sbom(data, file_path)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in SBOM file {file_path}: {e}")

def _parse_xml_sbom(content: str, file_path: str) -> Dict[str, Any]:
    """Parse XML format SBOM (SPDX)."""
    try:
        root = ET.fromstring(content)
        
        # Handle SPDX XML format
        packages = []
        namespace = {'spdx': 'http://spdx.org/spdxdocs/spdx-v2.2'}
        
        for package_elem in root.findall('.//spdx:Package', namespace):
            name_elem = package_elem.find('spdx:name', namespace)
            version_elem = package_elem.find('spdx:versionInfo', namespace)
            
            if name_elem is not None:
                package = SBOMPackage(
                    name=name_elem.text or "",
                    version=version_elem.text if version_elem is not None else "unknown",
                    ecosystem=detect_ecosystem(file_path)
                )
                packages.append(package.to_dict())
        
        return {
            "format": "spdx-xml",
            "source_file": file_path,
            "packages": packages,
            "metadata": {
                "parsed_at": datetime.now().isoformat(),
                "total_packages": len(packages)
            }
        }
    
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in SBOM file {file_path}: {e}")

def _parse_yaml_sbom(content: str, file_path: str) -> Dict[str, Any]:
    """Parse YAML format SBOM."""
    try:
        import yaml
        data = yaml.safe_load(content)
        
        # Handle different YAML SBOM formats
        if 'components' in data:
            return _normalize_cyclonedx_sbom(data, file_path)
        else:
            return _normalize_generic_json_sbom(data, file_path)
    
    except Exception as e:
        raise ValueError(f"Invalid YAML in SBOM file {file_path}: {e}")

def _normalize_cyclonedx_sbom(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Normalize CycloneDX format SBOM."""
    packages = []
    
    for component in data.get('components', []):
        package = SBOMPackage(
            name=component.get('name', ''),
            version=component.get('version', 'unknown'),
            purl=component.get('purl', ''),
            ecosystem=_extract_ecosystem_from_purl(component.get('purl', ''))
        )
        packages.append(package.to_dict())
    
    return {
        "format": "cyclonedx",
        "source_file": file_path,
        "packages": packages,
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_packages": len(packages),
            "cyclonedx_version": data.get('specVersion', 'unknown')
        }
    }

def _normalize_spdx_json_sbom(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Normalize SPDX JSON format SBOM."""
    packages = []
    
    for package_data in data.get('packages', []):
        package = SBOMPackage(
            name=package_data.get('name', ''),
            version=package_data.get('versionInfo', 'unknown'),
            ecosystem=detect_ecosystem(file_path)
        )
        packages.append(package.to_dict())
    
    return {
        "format": "spdx-json",
        "source_file": file_path,
        "packages": packages,
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_packages": len(packages),
            "spdx_version": data.get('spdxVersion', 'unknown')
        }
    }

def _normalize_npm_package_json(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Normalize npm package.json format."""
    packages = []
    
    # Add dependencies
    for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
        deps = data.get(dep_type, {})
        for name, version in deps.items():
            package = SBOMPackage(
                name=name,
                version=version,
                ecosystem="npm",
                metadata={"dependency_type": dep_type}
            )
            packages.append(package.to_dict())
    
    return {
        "format": "npm-package-json",
        "source_file": file_path,
        "packages": packages,
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_packages": len(packages),
            "package_name": data.get('name', 'unknown')
        }
    }

def _normalize_generic_json_sbom(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Normalize generic JSON format SBOM."""
    packages = []
    ecosystem = detect_ecosystem(file_path)
    
    # Try to find packages in various structures
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['packages', 'dependencies', 'components']:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'name' in item:
                            package = SBOMPackage(
                                name=item.get('name', ''),
                                version=item.get('version', 'unknown'),
                                ecosystem=ecosystem
                            )
                            packages.append(package.to_dict())
                elif isinstance(value, dict):
                    for name, version in value.items():
                        package = SBOMPackage(
                            name=name,
                            version=str(version),
                            ecosystem=ecosystem
                        )
                        packages.append(package.to_dict())
    
    return {
        "format": "generic-json",
        "source_file": file_path,
        "packages": packages,
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_packages": len(packages)
        }
    }

def _extract_ecosystem_from_purl(purl: str) -> str:
    """Extract ecosystem from Package URL (purl)."""
    if not purl:
        return "unknown"
    
    # purl format: pkg:type/namespace/name@version
    if purl.startswith('pkg:'):
        parts = purl.split('/')
        if len(parts) > 0:
            type_part = parts[0].replace('pkg:', '')
            ecosystem_mapping = {
                'npm': 'npm',
                'pypi': 'pypi',
                'maven': 'maven',
                'gem': 'rubygems',
                'cargo': 'crates',
                'golang': 'go'
            }
            return ecosystem_mapping.get(type_part, type_part)
    
    return "unknown"

def check_vulnerable_packages(sbom_data: Dict[str, Any], use_osv: bool = True) -> List[SecurityFinding]:
    """
    Check packages in SBOM against malicious package database and OSV API.
    
    Args:
        sbom_data: Parsed SBOM data
        use_osv: Whether to query OSV API for additional vulnerability information
    
    Returns:
        List of security findings
    """
    findings = []
    packages = sbom_data.get('packages', [])
    
    logger.info(f"Checking {len(packages)} packages for vulnerabilities")
    
    for package_data in packages:
        package_name = package_data.get('name', '')
        package_version = package_data.get('version', '')
        ecosystem = package_data.get('ecosystem', 'unknown')
        
        if not package_name:
            continue
        
        # Check against known malicious packages
        malicious_findings = _check_malicious_packages(package_name, package_version, ecosystem)
        findings.extend(malicious_findings)
        
        # Check for typosquatting
        typosquat_findings = _check_typosquatting(package_name, ecosystem)
        findings.extend(typosquat_findings)
        
        # Query OSV API if enabled
        if use_osv and config.ENABLE_OSV_QUERIES:
            osv_findings = _query_osv_api(package_name, package_version, ecosystem)
            findings.extend(osv_findings)
    
    logger.info(f"Found {len(findings)} security findings")
    return findings

def _check_malicious_packages(package_name: str, package_version: str, ecosystem: str) -> List[SecurityFinding]:
    """Check package against known malicious packages database."""
    findings = []
    
    if ecosystem not in KNOWN_MALICIOUS_PACKAGES:
        return findings
    
    malicious_packages = KNOWN_MALICIOUS_PACKAGES[ecosystem]
    
    for malicious_pkg in malicious_packages:
        if malicious_pkg['name'].lower() == package_name.lower():
            # Check version match
            malicious_version = malicious_pkg['version']
            if malicious_version == '*' or malicious_version == package_version:
                finding = SecurityFinding(
                    package=package_name,
                    version=package_version,
                    finding_type="malicious_package",
                    severity="critical",
                    confidence=0.95,
                    evidence=[
                        f"Package {package_name}@{package_version} matches known malicious package",
                        f"Reason: {malicious_pkg['reason']}"
                    ],
                    recommendations=[
                        "Remove this package immediately",
                        "Scan system for signs of compromise",
                        "Review all dependencies that might have pulled this package"
                    ]
                )
                findings.append(finding)
    
    return findings

def _check_typosquatting(package_name: str, ecosystem: str) -> List[SecurityFinding]:
    """Check package for typosquatting patterns."""
    findings = []
    
    if ecosystem not in TYPOSQUAT_TARGETS:
        return findings
    
    targets = TYPOSQUAT_TARGETS[ecosystem]
    
    for target in targets:
        confidence = calculate_typosquat_confidence(package_name, target)
        
        if confidence > 0.5:  # Threshold for typosquat detection
            severity = "high" if confidence > 0.8 else "medium"
            
            finding = SecurityFinding(
                package=package_name,
                version="*",
                finding_type="typosquat",
                severity=severity,
                confidence=confidence,
                evidence=[
                    f"Package name '{package_name}' is similar to popular package '{target}'",
                    f"Typosquat confidence: {confidence:.2f}"
                ],
                recommendations=[
                    f"Verify if you intended to install '{target}' instead",
                    "Check package author and description for legitimacy",
                    "Consider using exact package names to avoid typos"
                ]
            )
            findings.append(finding)
    
    return findings

def _query_osv_api(package_name: str, package_version: str, ecosystem: str) -> List[SecurityFinding]:
    """Query OSV API for vulnerability information."""
    findings = []
    
    try:
        # Map ecosystem names to OSV format
        osv_ecosystem_mapping = {
            "npm": "npm",
            "pypi": "PyPI", 
            "maven": "Maven",
            "rubygems": "RubyGems",
            "crates": "crates.io",
            "go": "Go"
        }
        
        osv_ecosystem = osv_ecosystem_mapping.get(ecosystem)
        if not osv_ecosystem:
            return findings
        
        # Use the new OSV API client
        osv_client = OSVAPIClient()
        
        # Add version if available and not wildcard
        version = package_version if package_version and package_version not in ["*", "unknown"] else None
        
        response = osv_client.query_vulnerabilities(package_name, osv_ecosystem, version)
        
        if response.is_success():
            data = response.get_data()
            vulnerabilities = data.get('vulns', [])
            
            for vuln in vulnerabilities:
                finding = SecurityFinding(
                    package=package_name,
                    version=package_version,
                    finding_type="vulnerability",
                    severity=_determine_severity_from_osv(vuln),
                    confidence=0.9,
                    evidence=[
                        f"OSV vulnerability: {vuln.get('id', 'Unknown')}",
                        f"Summary: {vuln.get('summary', 'No summary available')}"
                    ],
                    recommendations=[
                        "Update to a patched version if available",
                        "Review vulnerability details and assess impact",
                        "Consider alternative packages if no fix is available"
                    ]
                )
                findings.append(finding)
        
        elif response.error and response.error.status_code != 404:  # 404 means no vulnerabilities found
            logger.warning(f"OSV API error for {package_name}: {response.error.message}")
    
    except Exception as e:
        logger.warning(f"Failed to query OSV API for {package_name}: {e}")
    
    return findings

def _determine_severity_from_osv(vuln_data: Dict[str, Any]) -> str:
    """Determine severity level from OSV vulnerability data."""
    # Check for CVSS score
    severity_info = vuln_data.get('severity', [])
    
    for severity in severity_info:
        if severity.get('type') == 'CVSS_V3':
            score = severity.get('score')
            if score:
                try:
                    score_float = float(score)
                    if score_float >= 9.0:
                        return "critical"
                    elif score_float >= 7.0:
                        return "high"
                    elif score_float >= 4.0:
                        return "medium"
                    else:
                        return "low"
                except (ValueError, TypeError):
                    # If score can't be converted to float, continue to next severity
                    continue
    
    # Fallback to database_specific severity
    db_specific = vuln_data.get('database_specific', {})
    severity = db_specific.get('severity', '').lower()
    
    if severity in ['critical', 'high', 'medium', 'low']:
        return severity
    
    # Default to medium if no severity information
    return "medium"

def batch_query_osv(packages: List[Tuple[str, str, str]]) -> List[SecurityFinding]:
    """
    Batch query OSV API for multiple packages.
    
    Args:
        packages: List of (package_name, version, ecosystem) tuples
    
    Returns:
        List of security findings from all packages
    """
    all_findings = []
    
    try:
        osv_client = OSVAPIClient()
        
        # Prepare queries for batch request
        osv_ecosystem_mapping = {
            "npm": "npm",
            "pypi": "PyPI", 
            "maven": "Maven",
            "rubygems": "RubyGems",
            "crates": "crates.io",
            "go": "Go"
        }
        
        queries = []
        package_mapping = {}  # Map query index to original package info
        
        for i, (package_name, version, ecosystem) in enumerate(packages):
            osv_ecosystem = osv_ecosystem_mapping.get(ecosystem)
            if osv_ecosystem:
                query = {
                    "package": {
                        "name": package_name,
                        "ecosystem": osv_ecosystem
                    }
                }
                
                if version and version not in ["*", "unknown"]:
                    query["version"] = version
                
                queries.append(query)
                package_mapping[len(queries) - 1] = (package_name, version, ecosystem)
        
        if not queries:
            return all_findings
        
        # Use batch query if available, otherwise fall back to individual queries
        try:
            response = osv_client.batch_query_vulnerabilities(queries)
            
            if response.is_success():
                results = response.get_data()
                
                for i, result in enumerate(results):
                    if i in package_mapping:
                        package_name, version, ecosystem = package_mapping[i]
                        vulnerabilities = result.get('vulns', [])
                        
                        for vuln in vulnerabilities:
                            finding = SecurityFinding(
                                package=package_name,
                                version=version,
                                finding_type="vulnerability",
                                severity=_determine_severity_from_osv(vuln),
                                confidence=0.9,
                                evidence=[
                                    f"OSV vulnerability: {vuln.get('id', 'Unknown')}",
                                    f"Summary: {vuln.get('summary', 'No summary available')}"
                                ],
                                recommendations=[
                                    "Update to a patched version if available",
                                    "Review vulnerability details and assess impact",
                                    "Consider alternative packages if no fix is available"
                                ]
                            )
                            all_findings.append(finding)
            else:
                # Fall back to individual queries
                logger.info("Batch query failed, falling back to individual queries")
                for package_name, version, ecosystem in packages:
                    findings = _query_osv_api(package_name, version, ecosystem)
                    all_findings.extend(findings)
                    
                    # Small delay between requests to be respectful
                    import time
                    time.sleep(0.1)
        
        except Exception as e:
            logger.warning(f"Batch query failed: {e}, falling back to individual queries")
            # Fall back to individual queries
            for package_name, version, ecosystem in packages:
                findings = _query_osv_api(package_name, version, ecosystem)
                all_findings.extend(findings)
                
                # Small delay between requests to be respectful
                import time
                time.sleep(0.1)
    
    except Exception as e:
        logger.error(f"Failed to perform batch OSV query: {e}")
    
    return all_findings

def generate_sbom_from_packages(packages: List[Dict[str, Any]], source_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a standardized SBOM structure from package data.
    
    Args:
        packages: List of package dictionaries
        source_info: Information about the source (file path, repository, etc.)
    
    Returns:
        Standardized SBOM dictionary
    """
    sbom = {
        "format": "multi-agent-security-sbom",
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "source": source_info,
        "packages": packages,
        "metadata": {
            "total_packages": len(packages),
            "ecosystems": list(set(pkg.get('ecosystem', 'unknown') for pkg in packages)),
            "generator": "multi-agent-security-analysis-system"
        }
    }
    
    return sbom

def validate_sbom_structure(sbom_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate SBOM structure and return validation results.
    
    Args:
        sbom_data: SBOM data to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required top-level fields
    required_fields = ['packages']
    for field in required_fields:
        if field not in sbom_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate packages structure
    packages = sbom_data.get('packages', [])
    if not isinstance(packages, list):
        errors.append("'packages' field must be a list")
    else:
        for i, package in enumerate(packages):
            if not isinstance(package, dict):
                errors.append(f"Package at index {i} must be a dictionary")
                continue
            
            # Check required package fields
            if 'name' not in package:
                errors.append(f"Package at index {i} missing 'name' field")
            elif not package['name']:
                errors.append(f"Package at index {i} has empty 'name' field")
    
    return len(errors) == 0, errors

def extract_packages_from_file(file_path: str) -> List[SBOMPackage]:
    """
    Extract package information from various package manager files.
    
    Args:
        file_path: Path to package file
    
    Returns:
        List of SBOMPackage objects
    """
    packages = []
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Package file not found: {file_path}")
    
    ecosystem = detect_ecosystem(file_path)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if ecosystem == "npm" and path.name == "package.json":
            packages = _extract_npm_packages(content)
        elif ecosystem == "pypi" and path.name == "requirements.txt":
            packages = _extract_pip_packages(content)
        elif ecosystem == "maven" and path.name == "pom.xml":
            packages = _extract_maven_packages(content)
        elif ecosystem == "rubygems" and path.name.lower() == "gemfile":
            packages = _extract_gem_packages(content)
        elif ecosystem == "crates" and path.name == "Cargo.toml":
            packages = _extract_cargo_packages(content)
        elif ecosystem == "go" and path.name == "go.mod":
            packages = _extract_go_packages(content)
        
        # Set ecosystem for all packages
        for package in packages:
            package.ecosystem = ecosystem
    
    except Exception as e:
        logger.error(f"Error extracting packages from {file_path}: {e}")
        raise ValueError(f"Failed to extract packages from {file_path}: {e}")
    
    return packages

def _extract_npm_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from npm package.json."""
    packages = []
    
    try:
        data = json.loads(content)
        
        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
            deps = data.get(dep_type, {})
            for name, version in deps.items():
                package = SBOMPackage(
                    name=name,
                    version=version,
                    metadata={"dependency_type": dep_type}
                )
                packages.append(package)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in package.json: {e}")
    
    return packages

def _extract_pip_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from pip requirements.txt."""
    packages = []
    
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Parse requirement line (package==version, package>=version, etc.)
            import re
            match = re.match(r'^([a-zA-Z0-9_.-]+)([><=!]+)(.+)$', line)
            if match:
                name, operator, version = match.groups()
                package = SBOMPackage(
                    name=name,
                    version=version,
                    metadata={"version_operator": operator}
                )
                packages.append(package)
            else:
                # Simple package name without version
                if re.match(r'^[a-zA-Z0-9_.-]+$', line):
                    package = SBOMPackage(name=line, version="*")
                    packages.append(package)
    
    return packages

def _extract_maven_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from Maven pom.xml."""
    packages = []
    
    try:
        root = ET.fromstring(content)
        
        # Find dependencies
        for dependency in root.findall('.//dependency'):
            group_id = dependency.find('groupId')
            artifact_id = dependency.find('artifactId')
            version = dependency.find('version')
            
            if group_id is not None and artifact_id is not None:
                name = f"{group_id.text}:{artifact_id.text}"
                version_text = version.text if version is not None else "unknown"
                
                package = SBOMPackage(name=name, version=version_text)
                packages.append(package)
    
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in pom.xml: {e}")
    
    return packages

def _extract_gem_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from Ruby Gemfile."""
    packages = []
    
    import re
    
    for line in content.split('\n'):
        line = line.strip()
        # Match gem declarations: gem 'name', 'version'
        match = re.match(r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?", line)
        if match:
            name = match.group(1)
            version = match.group(2) if match.group(2) else "*"
            package = SBOMPackage(name=name, version=version)
            packages.append(package)
    
    return packages

def _extract_cargo_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from Rust Cargo.toml."""
    packages = []
    
    try:
        import toml
        data = toml.loads(content)
        
        dependencies = data.get('dependencies', {})
        for name, version_info in dependencies.items():
            if isinstance(version_info, str):
                version = version_info
            elif isinstance(version_info, dict):
                version = version_info.get('version', '*')
            else:
                version = '*'
            
            package = SBOMPackage(name=name, version=version)
            packages.append(package)
    
    except Exception as e:
        raise ValueError(f"Invalid TOML in Cargo.toml: {e}")
    
    return packages

def _extract_go_packages(content: str) -> List[SBOMPackage]:
    """Extract packages from Go go.mod."""
    packages = []
    
    import re
    
    for line in content.split('\n'):
        line = line.strip()
        # Match require statements: require module.name v1.2.3
        match = re.match(r'require\s+([^\s]+)\s+([^\s]+)', line)
        if match:
            name = match.group(1)
            version = match.group(2)
            package = SBOMPackage(name=name, version=version)
            packages.append(package)
    
    return packages