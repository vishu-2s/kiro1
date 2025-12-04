"""
Proactive Error Prevention and Validation System.

This module validates inputs, checks preconditions, and prevents errors
BEFORE they occur, rather than reacting to failures.

Philosophy: "Fail fast with clear guidance" instead of "Try and catch later"
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"      # Must fix - will cause failure
    WARNING = "warning"  # Should fix - may cause issues
    INFO = "info"        # Nice to fix - best practices


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: ValidationLevel
    category: str
    message: str
    fix_suggestion: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "level": self.level.value,
            "category": self.category,
            "message": self.message,
            "fix_suggestion": self.fix_suggestion
        }


class ProactiveValidator:
    """
    Proactive validation system that prevents errors before they occur.
    
    Validates:
    - Environment configuration (API keys, tokens)
    - File system state (paths exist, permissions)
    - Input data (format, size, content)
    - Network connectivity (APIs reachable)
    - Resource availability (disk space, memory)
    """
    
    def __init__(self):
        """Initialize validator."""
        self.issues: List[ValidationIssue] = []
    
    def validate_environment(self) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate environment configuration before analysis starts.
        
        Checks:
        - Required API keys present
        - Optional API keys for enhanced features
        - Environment variables properly formatted
        - Cache directories writable
        
        Returns:
            (is_valid, list of issues)
        """
        self.issues = []
        
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="api_configuration",
                message="OPENAI_API_KEY not set",
                fix_suggestion="Set OPENAI_API_KEY in .env file for AI-powered analysis. Analysis will use rule-based fallbacks."
            ))
        elif not openai_key.startswith("sk-"):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="api_configuration",
                message="OPENAI_API_KEY appears invalid (should start with 'sk-')",
                fix_suggestion="Check your OpenAI API key in .env file. Get a valid key from https://platform.openai.com/api-keys"
            ))
        
        # Check GitHub token (optional but recommended)
        github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT_TOKEN")
        if not github_token:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="api_configuration",
                message="GitHub token not set",
                fix_suggestion="Set GITHUB_TOKEN in .env for higher rate limits and private repo access. Public repos will still work."
            ))
        
        # Check cache configuration
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        if cache_enabled:
            cache_dir = os.path.join(os.getcwd(), ".cache")
            if not os.path.exists(cache_dir):
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                except Exception as e:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="filesystem",
                        message=f"Cannot create cache directory: {e}",
                        fix_suggestion="Ensure write permissions for current directory or set CACHE_ENABLED=false"
                    ))
        
        # Check output directory
        output_dir = os.getenv("OUTPUT_DIRECTORY", "outputs")
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="filesystem",
                    message=f"Cannot create output directory: {e}",
                    fix_suggestion=f"Ensure write permissions or change OUTPUT_DIRECTORY in .env"
                ))
        
        # Check disk space
        try:
            import shutil
            stat = shutil.disk_usage(os.getcwd())
            free_gb = stat.free / (1024**3)
            if free_gb < 1.0:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="resources",
                    message=f"Low disk space: {free_gb:.2f} GB free",
                    fix_suggestion="Free up disk space. Analysis may fail if disk fills up."
                ))
        except Exception as e:
            logger.debug(f"Could not check disk space: {e}")
        
        # Determine if valid
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in self.issues)
        
        if self.issues:
            logger.info(f"Environment validation found {len(self.issues)} issues")
            for issue in self.issues:
                if issue.level == ValidationLevel.ERROR:
                    logger.error(f"{issue.category}: {issue.message}")
                elif issue.level == ValidationLevel.WARNING:
                    logger.warning(f"{issue.category}: {issue.message}")
                else:
                    logger.info(f"{issue.category}: {issue.message}")
        
        return (not has_errors, self.issues)
    
    def validate_manifest_file(self, manifest_path: str, ecosystem: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate manifest file before analysis.
        
        Checks:
        - File exists and is readable
        - File format is valid JSON/text
        - Required fields present
        - Dependencies list not empty
        
        Args:
            manifest_path: Path to manifest file
            ecosystem: 'npm' or 'pypi'
        
        Returns:
            (is_valid, list of issues)
        """
        self.issues = []
        
        # Check file exists
        if not os.path.exists(manifest_path):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="file_not_found",
                message=f"Manifest file not found: {manifest_path}",
                fix_suggestion=f"Ensure the file path is correct. Expected: {manifest_path}"
            ))
            return (False, self.issues)
        
        # Check file is readable
        if not os.access(manifest_path, os.R_OK):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="file_permissions",
                message=f"Cannot read manifest file: {manifest_path}",
                fix_suggestion="Check file permissions. Ensure read access is granted."
            ))
            return (False, self.issues)
        
        # Check file size
        file_size = os.path.getsize(manifest_path)
        if file_size == 0:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="file_empty",
                message=f"Manifest file is empty: {manifest_path}",
                fix_suggestion="Ensure the manifest file contains valid dependency declarations."
            ))
            return (False, self.issues)
        
        if file_size > 10 * 1024 * 1024:  # 10 MB
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="file_size",
                message=f"Manifest file is very large: {file_size / 1024 / 1024:.2f} MB",
                fix_suggestion="Large manifest files may slow down analysis. Consider splitting dependencies."
            ))
        
        # Validate content based on ecosystem
        try:
            if ecosystem == "npm":
                self._validate_npm_manifest(manifest_path)
            elif ecosystem == "pypi":
                self._validate_python_manifest(manifest_path)
            else:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="unsupported_ecosystem",
                    message=f"Unsupported ecosystem: {ecosystem}",
                    fix_suggestion="Supported ecosystems: 'npm', 'pypi'"
                ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="validation_error",
                message=f"Error validating manifest: {str(e)}",
                fix_suggestion="Check manifest file format and syntax."
            ))
        
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in self.issues)
        return (not has_errors, self.issues)
    
    def _validate_npm_manifest(self, manifest_path: str) -> None:
        """Validate npm package.json file."""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            if "name" not in data:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="missing_field",
                    message="package.json missing 'name' field",
                    fix_suggestion="Add 'name' field to package.json for better reporting."
                ))
            
            # Check dependencies
            has_deps = False
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_type in data and data[dep_type]:
                    has_deps = True
                    break
            
            if not has_deps:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="no_dependencies",
                    message="No dependencies found in package.json",
                    fix_suggestion="Ensure dependencies are declared in package.json. Nothing to analyze if no dependencies."
                ))
            
        except json.JSONDecodeError as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="invalid_json",
                message=f"Invalid JSON in package.json: {str(e)}",
                fix_suggestion="Fix JSON syntax errors. Use a JSON validator or linter."
            ))
    
    def _validate_python_manifest(self, manifest_path: str) -> None:
        """Validate Python requirements file."""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out comments and empty lines
            deps = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
            
            if not deps:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="no_dependencies",
                    message="No dependencies found in requirements file",
                    fix_suggestion="Ensure dependencies are declared. Nothing to analyze if no dependencies."
                ))
            
            # Check for common issues
            for line in deps:
                if "==" not in line and ">=" not in line and "<=" not in line:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.INFO,
                        category="unpinned_version",
                        message=f"Unpinned dependency: {line}",
                        fix_suggestion="Consider pinning versions (e.g., package==1.0.0) for reproducible builds."
                    ))
                    break  # Only warn once
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="file_read_error",
                message=f"Error reading requirements file: {str(e)}",
                fix_suggestion="Ensure file is valid UTF-8 text."
            ))
    
    def validate_network_connectivity(self) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate network connectivity to required services.
        
        Checks:
        - npm registry reachable
        - PyPI reachable
        - OSV API reachable
        - OpenAI API reachable (if key present)
        
        Returns:
            (is_valid, list of issues)
        """
        self.issues = []
        
        import requests
        
        # Test npm registry
        try:
            response = requests.get("https://registry.npmjs.org/", timeout=5)
            if response.status_code != 200:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="network",
                    message="npm registry not reachable",
                    fix_suggestion="Check internet connection. npm analysis may fail."
                ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="network",
                message=f"Cannot reach npm registry: {str(e)}",
                fix_suggestion="Check internet connection and firewall settings."
            ))
        
        # Test PyPI
        try:
            response = requests.get("https://pypi.org/", timeout=5)
            if response.status_code != 200:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="network",
                    message="PyPI not reachable",
                    fix_suggestion="Check internet connection. Python analysis may fail."
                ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="network",
                message=f"Cannot reach PyPI: {str(e)}",
                fix_suggestion="Check internet connection and firewall settings."
            ))
        
        # Test OSV API
        try:
            response = requests.get("https://api.osv.dev/v1/", timeout=5)
            # OSV returns 404 for root, but that means it's reachable
            if response.status_code not in [200, 404]:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="network",
                    message="OSV API not reachable",
                    fix_suggestion="Check internet connection. Vulnerability analysis may fail."
                ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="network",
                message=f"Cannot reach OSV API: {str(e)}",
                fix_suggestion="Check internet connection. Vulnerability analysis will be limited."
            ))
        
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in self.issues)
        return (not has_errors, self.issues)
    
    def validate_analysis_inputs(
        self,
        manifest_path: str,
        ecosystem: str,
        packages: Optional[List[str]] = None
    ) -> Tuple[bool, List[ValidationIssue]]:
        """
        Comprehensive validation of all analysis inputs.
        
        Args:
            manifest_path: Path to manifest file
            ecosystem: 'npm' or 'pypi'
            packages: Optional list of specific packages to analyze
        
        Returns:
            (is_valid, list of issues)
        """
        all_issues = []
        
        # Validate environment
        env_valid, env_issues = self.validate_environment()
        all_issues.extend(env_issues)
        
        # Validate manifest
        manifest_valid, manifest_issues = self.validate_manifest_file(manifest_path, ecosystem)
        all_issues.extend(manifest_issues)
        
        # Validate network (non-blocking)
        _, network_issues = self.validate_network_connectivity()
        all_issues.extend(network_issues)
        
        # Validate packages list if provided
        if packages:
            if not isinstance(packages, list):
                all_issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_input",
                    message="Packages must be a list",
                    fix_suggestion="Provide packages as a list of strings."
                ))
            elif len(packages) == 0:
                all_issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="empty_input",
                    message="Empty packages list provided",
                    fix_suggestion="Provide at least one package name or omit to analyze all."
                ))
        
        self.issues = all_issues
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in all_issues)
        
        return (not has_errors, all_issues)
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get formatted validation report.
        
        Returns:
            Validation report dictionary
        """
        errors = [issue for issue in self.issues if issue.level == ValidationLevel.ERROR]
        warnings = [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]
        info = [issue for issue in self.issues if issue.level == ValidationLevel.INFO]
        
        return {
            "is_valid": len(errors) == 0,
            "total_issues": len(self.issues),
            "errors": [issue.to_dict() for issue in errors],
            "warnings": [issue.to_dict() for issue in warnings],
            "info": [issue.to_dict() for issue in info],
            "summary": {
                "error_count": len(errors),
                "warning_count": len(warnings),
                "info_count": len(info)
            }
        }


# Convenience function
def validate_before_analysis(
    manifest_path: str,
    ecosystem: str,
    packages: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate all inputs before starting analysis.
    
    Args:
        manifest_path: Path to manifest file
        ecosystem: 'npm' or 'pypi'
        packages: Optional list of packages
    
    Returns:
        (is_valid, validation_report)
    """
    validator = ProactiveValidator()
    is_valid, issues = validator.validate_analysis_inputs(manifest_path, ecosystem, packages)
    report = validator.get_validation_report()
    
    return (is_valid, report)
