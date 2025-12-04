"""
npm Ecosystem Analyzer for Multi-Agent Security Analysis System.

This module provides npm-specific analysis functionality using the
EcosystemAnalyzer framework.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from tools.ecosystem_analyzer import EcosystemAnalyzer, SecurityFinding, register_analyzer

logger = logging.getLogger(__name__)


class NpmAnalyzer(EcosystemAnalyzer):
    """npm ecosystem analyzer."""
    
    @property
    def ecosystem_name(self) -> str:
        """Return ecosystem name."""
        return "npm"
    
    def detect_manifest_files(self, directory: str) -> List[str]:
        """
        Detect npm manifest files (package.json, package-lock.json, etc.).
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            List of manifest file paths found
        """
        manifest_files = []
        manifest_patterns = ["package.json", "package-lock.json", "yarn.lock", "npm-shrinkwrap.json"]
        
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.warning(f"Directory does not exist or is not a directory: {directory}")
                return []
            
            for pattern in manifest_patterns:
                file_path = dir_path / pattern
                if file_path.exists() and file_path.is_file():
                    manifest_files.append(str(file_path))
                    logger.debug(f"Found npm manifest file: {file_path}")
        
        except Exception as e:
            logger.error(f"Error detecting npm manifest files in {directory}: {e}")
        
        return manifest_files
    
    def extract_dependencies(self, manifest_path: str) -> List[Dict[str, Any]]:
        """
        Extract dependencies from package.json.
        
        Args:
            manifest_path: Path to package.json file
            
        Returns:
            List of dependency dictionaries
        """
        dependencies = []
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract different types of dependencies
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    dependency = {
                        "name": name,
                        "version": version,
                        "ecosystem": "npm",
                        "dependency_type": dep_type,
                        "source_file": manifest_path
                    }
                    dependencies.append(dependency)
                    logger.debug(f"Extracted npm dependency: {name}@{version} ({dep_type})")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {manifest_path}: {e}")
        except Exception as e:
            logger.error(f"Error extracting dependencies from {manifest_path}: {e}")
        
        return dependencies
    
    def analyze_install_scripts(self, directory: str) -> List[SecurityFinding]:
        """
        Analyze npm lifecycle scripts for malicious patterns.
        
        Args:
            directory: Path to directory containing package.json
            
        Returns:
            List of security findings from script analysis
        """
        findings = []
        
        try:
            package_json_path = Path(directory) / "package.json"
            if not package_json_path.exists():
                logger.debug(f"No package.json found in {directory}")
                return []
            
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scripts = data.get('scripts', {})
            package_name = data.get('name', 'unknown')
            
            if not scripts:
                logger.debug(f"No scripts found in package '{package_name}'")
                return []
            
            # Import the existing npm script analysis function
            from tools.sbom_tools import _analyze_npm_scripts
            
            # Use existing analysis logic
            findings = _analyze_npm_scripts(scripts, package_name)
            logger.info(f"Analyzed {len(scripts)} scripts in package '{package_name}', found {len(findings)} issues")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in package.json: {e}")
        except Exception as e:
            logger.error(f"Error analyzing npm install scripts in {directory}: {e}")
        
        return findings
    
    def get_registry_url(self, package_name: str) -> str:
        """
        Return npm registry API URL for package metadata.
        
        Args:
            package_name: Name of the npm package
            
        Returns:
            Full URL to package metadata endpoint
        """
        # Handle scoped packages (e.g., @babel/core)
        if package_name.startswith('@'):
            # URL encode the @ symbol
            package_name = package_name.replace('@', '%40')
        
        return f"https://registry.npmjs.org/{package_name}"
    
    def get_malicious_patterns(self) -> Dict[str, List[str]]:
        """
        Return npm-specific malicious patterns.
        
        Returns:
            Dictionary mapping severity levels to regex patterns
        """
        return {
            "critical": [
                r'curl\s+.*\|\s*(?:bash|sh)',
                r'wget\s+.*\|\s*(?:bash|sh)',
                r'eval\s*\(\s*(?:atob|Buffer\.from)',
                r'exec\s*\(\s*(?:atob|Buffer\.from)',
            ],
            "high": [
                r'rm\s+-rf\s+(?:/|~|\$HOME)',
                r'chmod\s+\+[sx]',
                r'sudo\s+',
                r'base64\s+-d',
                r'>/etc/',
            ],
            "medium": [
                r'curl\s+.*\.(?:tk|ml|ga|cf|cc)\b',
                r'wget\s+.*\.(?:tk|ml|ga|cf|cc)\b',
                r'discord\.com/api/webhooks',
                r'\beval\s*\(',
                r'child_process\.exec',
            ]
        }
    
    def extract_package_metadata(self, manifest_path: str) -> Dict[str, Any]:
        """
        Extract package metadata from package.json.
        
        Args:
            manifest_path: Path to package.json file
            
        Returns:
            Dictionary with package metadata
        """
        metadata = {}
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = {
                "name": data.get("name", "unknown"),
                "version": data.get("version", "unknown"),
                "description": data.get("description", ""),
                "author": data.get("author", ""),
                "license": data.get("license", ""),
                "repository": data.get("repository", {}),
                "homepage": data.get("homepage", ""),
                "keywords": data.get("keywords", []),
                "scripts": data.get("scripts", {}),
                "engines": data.get("engines", {}),
            }
        
        except Exception as e:
            logger.error(f"Error extracting package metadata from {manifest_path}: {e}")
        
        return metadata


# Register the npm analyzer with the global registry
def _register_npm_analyzer():
    """Register npm analyzer with global registry."""
    try:
        analyzer = NpmAnalyzer()
        register_analyzer(analyzer)
        logger.info("npm analyzer registered successfully")
    except Exception as e:
        logger.error(f"Failed to register npm analyzer: {e}")


# Auto-register when module is imported
_register_npm_analyzer()
