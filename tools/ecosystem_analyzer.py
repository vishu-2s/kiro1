"""
Ecosystem Analyzer Framework for Multi-Agent Security Analysis System.

This module provides a pluggable framework for analyzing different package ecosystems.
New ecosystems can be added by implementing the EcosystemAnalyzer base class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Security finding from ecosystem analysis."""
    package: str
    version: str
    finding_type: str
    severity: str  # "critical", "high", "medium", "low"
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    recommendations: List[str]
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "package": self.package,
            "version": self.version,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "source": self.source
        }


class EcosystemAnalyzer(ABC):
    """Abstract base class for ecosystem-specific security analyzers."""
    
    @property
    @abstractmethod
    def ecosystem_name(self) -> str:
        """
        Return the ecosystem name (e.g., 'npm', 'pypi', 'maven').
        
        Returns:
            Ecosystem identifier string
        """
        pass
    
    @abstractmethod
    def detect_manifest_files(self, directory: str) -> List[str]:
        """
        Detect ecosystem-specific manifest files in directory.
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            List of manifest file paths found
        """
        pass
    
    @abstractmethod
    def extract_dependencies(self, manifest_path: str) -> List[Dict[str, Any]]:
        """
        Extract dependencies from manifest file.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            List of dependency dictionaries with name, version, and metadata
        """
        pass
    
    @abstractmethod
    def analyze_install_scripts(self, directory: str) -> List[SecurityFinding]:
        """
        Analyze installation scripts for malicious patterns.
        
        Args:
            directory: Path to directory containing package
            
        Returns:
            List of security findings from script analysis
        """
        pass
    
    @abstractmethod
    def get_registry_url(self, package_name: str) -> str:
        """
        Return registry API URL for package metadata.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Full URL to package metadata endpoint
        """
        pass
    
    def get_malicious_patterns(self) -> Dict[str, List[str]]:
        """
        Return ecosystem-specific malicious patterns (optional override).
        
        Returns:
            Dictionary mapping severity levels to regex patterns
        """
        return {}
    
    def is_malicious_package(self, package_name: str, version: str = "*") -> Optional[Dict[str, Any]]:
        """
        Check if package is in known malicious package database.
        
        Args:
            package_name: Name of the package
            version: Version of the package (default: "*" for any)
            
        Returns:
            Malicious package info if found, None otherwise
        """
        from constants import KNOWN_MALICIOUS_PACKAGES
        
        ecosystem_packages = KNOWN_MALICIOUS_PACKAGES.get(self.ecosystem_name, [])
        
        for malicious_pkg in ecosystem_packages:
            if malicious_pkg["name"] == package_name:
                # Check version match
                if version == "*" or malicious_pkg["version"] == "*":
                    return malicious_pkg
                # Simple version matching (can be enhanced)
                if malicious_pkg["version"] == version:
                    return malicious_pkg
                if malicious_pkg["version"].startswith(">=") and version >= malicious_pkg["version"][2:]:
                    return malicious_pkg
        
        return None


class AnalyzerRegistry:
    """Central registry for ecosystem analyzers."""
    
    def __init__(self):
        """Initialize empty registry."""
        self._analyzers: Dict[str, EcosystemAnalyzer] = {}
        logger.info("Initialized AnalyzerRegistry")
    
    def register(self, analyzer: EcosystemAnalyzer):
        """
        Register an analyzer for an ecosystem.
        
        Args:
            analyzer: EcosystemAnalyzer instance to register
        """
        ecosystem = analyzer.ecosystem_name
        if ecosystem in self._analyzers:
            logger.warning(f"Overwriting existing analyzer for ecosystem: {ecosystem}")
        
        self._analyzers[ecosystem] = analyzer
        logger.info(f"Registered analyzer for ecosystem: {ecosystem}")
    
    def get_analyzer(self, ecosystem: str) -> Optional[EcosystemAnalyzer]:
        """
        Get analyzer for specific ecosystem.
        
        Args:
            ecosystem: Ecosystem name
            
        Returns:
            EcosystemAnalyzer instance or None if not found
        """
        return self._analyzers.get(ecosystem)
    
    def detect_ecosystem(self, directory: str) -> Optional[str]:
        """
        Auto-detect ecosystem from directory contents.
        
        Args:
            directory: Path to directory to analyze
            
        Returns:
            Detected ecosystem name or None if not detected
        """
        for name, analyzer in self._analyzers.items():
            manifest_files = analyzer.detect_manifest_files(directory)
            if manifest_files:
                logger.info(f"Detected ecosystem '{name}' in directory: {directory}")
                return name
        
        logger.warning(f"Could not detect ecosystem in directory: {directory}")
        return None
    
    def get_all_ecosystems(self) -> List[str]:
        """
        Get list of all registered ecosystems.
        
        Returns:
            List of ecosystem names
        """
        return list(self._analyzers.keys())
    
    def unregister(self, ecosystem: str) -> bool:
        """
        Unregister an analyzer.
        
        Args:
            ecosystem: Ecosystem name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if ecosystem in self._analyzers:
            del self._analyzers[ecosystem]
            logger.info(f"Unregistered analyzer for ecosystem: {ecosystem}")
            return True
        return False


# Global registry instance
_global_registry: Optional[AnalyzerRegistry] = None


def get_registry() -> AnalyzerRegistry:
    """
    Get the global analyzer registry instance.
    
    Returns:
        Global AnalyzerRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AnalyzerRegistry()
    return _global_registry


def register_analyzer(analyzer: EcosystemAnalyzer):
    """
    Register an analyzer with the global registry.
    
    Args:
        analyzer: EcosystemAnalyzer instance to register
    """
    registry = get_registry()
    registry.register(analyzer)


def get_analyzer(ecosystem: str) -> Optional[EcosystemAnalyzer]:
    """
    Get analyzer for specific ecosystem from global registry.
    
    Args:
        ecosystem: Ecosystem name
        
    Returns:
        EcosystemAnalyzer instance or None if not found
    """
    registry = get_registry()
    return registry.get_analyzer(ecosystem)


def detect_ecosystem(directory: str) -> Optional[str]:
    """
    Auto-detect ecosystem from directory contents using global registry.
    
    Args:
        directory: Path to directory to analyze
        
    Returns:
        Detected ecosystem name or None if not detected
    """
    registry = get_registry()
    return registry.detect_ecosystem(directory)
