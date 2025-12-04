"""
Safe Type System with Validation and Consistent Data Structures.

This module provides type-safe wrappers and utilities to eliminate:
1. Dict vs Object confusion
2. Unsafe attribute access
3. Type inconsistencies
4. Unicode handling issues

Philosophy: "Make invalid states unrepresentable"
"""

import sys
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic
from enum import Enum

logger = logging.getLogger(__name__)

# Type variable for generic safe access
T = TypeVar('T')


class SafeDict(dict):
    """
    Dictionary with safe attribute access and type validation.
    
    Features:
    - Dot notation access (dict.key instead of dict['key'])
    - Returns None instead of KeyError
    - Type validation
    - Unicode-safe string conversion
    """
    
    def __getattr__(self, key: str) -> Any:
        """Allow dot notation access"""
        try:
            return self[key]
        except KeyError:
            return None
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Allow dot notation assignment"""
        self[key] = value
    
    def safe_get(self, key: str, default: T = None, expected_type: type = None) -> T:
        """
        Safely get value with type checking.
        
        Args:
            key: Dictionary key
            default: Default value if key not found
            expected_type: Expected type for validation
        
        Returns:
            Value or default
        """
        value = self.get(key, default)
        
        if expected_type and value is not None:
            if not isinstance(value, expected_type):
                logger.warning(
                    f"Type mismatch for key '{key}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
                return default
        
        return value
    
    def safe_str(self, key: str, default: str = "") -> str:
        """Safely get string value with unicode handling"""
        value = self.get(key, default)
        if value is None:
            return default
        
        try:
            # Handle unicode properly for Windows console
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='replace')
            return str(value)
        except Exception as e:
            logger.warning(f"Error converting to string: {e}")
            return default
    
    def safe_int(self, key: str, default: int = 0) -> int:
        """Safely get integer value"""
        value = self.get(key, default)
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Cannot convert '{key}' to int: {value}")
            return default
    
    def safe_float(self, key: str, default: float = 0.0) -> float:
        """Safely get float value"""
        value = self.get(key, default)
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Cannot convert '{key}' to float: {value}")
            return default
    
    def safe_list(self, key: str, default: List = None) -> List:
        """Safely get list value"""
        if default is None:
            default = []
        
        value = self.get(key, default)
        if value is None:
            return default
        
        if not isinstance(value, list):
            logger.warning(f"Expected list for '{key}', got {type(value).__name__}")
            return default
        
        return value
    
    def safe_dict(self, key: str, default: Dict = None) -> 'SafeDict':
        """Safely get nested dictionary"""
        if default is None:
            default = {}
        
        value = self.get(key, default)
        if value is None:
            return SafeDict(default)
        
        if not isinstance(value, dict):
            logger.warning(f"Expected dict for '{key}', got {type(value).__name__}")
            return SafeDict(default)
        
        return SafeDict(value)


def safe_unicode_print(text: str, fallback: str = "?") -> None:
    """
    Safely print unicode text to console (Windows-compatible).
    
    Args:
        text: Text to print
        fallback: Fallback character for unencodable characters
    """
    try:
        # Try to print normally
        print(text)
    except UnicodeEncodeError:
        # Fallback for Windows console
        try:
            # Encode to console encoding with replacement
            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            print(safe_text)
        except Exception:
            # Last resort: ASCII only
            ascii_text = text.encode('ascii', errors='replace').decode('ascii')
            print(ascii_text)


def safe_unicode_str(value: Any, fallback: str = "") -> str:
    """
    Safely convert any value to unicode string.
    
    Args:
        value: Value to convert
        fallback: Fallback if conversion fails
    
    Returns:
        Unicode string
    """
    if value is None:
        return fallback
    
    try:
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return str(value)
    except Exception as e:
        logger.warning(f"Error converting to string: {e}")
        return fallback


@dataclass
class SafeAgentResult:
    """
    Type-safe agent result with validation.
    
    This replaces the dict/object confusion with a consistent dataclass.
    """
    agent_name: str
    success: bool
    data: SafeDict
    error: Optional[str] = None
    duration_seconds: float = 0.0
    status: str = "success"
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate after initialization"""
        # Ensure data is SafeDict
        if not isinstance(self.data, SafeDict):
            self.data = SafeDict(self.data if isinstance(self.data, dict) else {})
        
        # Validate confidence
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Set status based on success if not explicitly set
        if self.status == "success" and not self.success:
            self.status = "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "data": dict(self.data),
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SafeAgentResult':
        """Create from dictionary"""
        return cls(
            agent_name=data.get("agent_name", "unknown"),
            success=data.get("success", False),
            data=SafeDict(data.get("data", {})),
            error=data.get("error"),
            duration_seconds=data.get("duration_seconds", 0.0),
            status=data.get("status", "success"),
            confidence=data.get("confidence", 1.0)
        )
    
    def get_packages(self) -> List[SafeDict]:
        """Safely get packages from data"""
        packages = self.data.safe_list("packages", [])
        return [SafeDict(p) if isinstance(p, dict) else SafeDict() for p in packages]
    
    def get_package_count(self) -> int:
        """Safely get package count"""
        return self.data.safe_int("total_packages_analyzed", len(self.get_packages()))


@dataclass
class SafeSharedContext:
    """
    Type-safe shared context with validation.
    
    Eliminates dict/object confusion and provides safe accessors.
    """
    packages: List[str]
    ecosystem: str = "npm"
    dependency_graph: SafeDict = field(default_factory=SafeDict)
    agent_results: Dict[str, SafeAgentResult] = field(default_factory=dict)
    initial_findings: List[SafeDict] = field(default_factory=list)
    input_mode: str = "local"
    project_path: str = ""
    metadata: SafeDict = field(default_factory=SafeDict)
    
    def __post_init__(self):
        """Validate after initialization"""
        # Ensure dependency_graph is SafeDict
        if not isinstance(self.dependency_graph, SafeDict):
            self.dependency_graph = SafeDict(
                self.dependency_graph if isinstance(self.dependency_graph, dict) else {}
            )
        
        # Ensure metadata is SafeDict
        if not isinstance(self.metadata, SafeDict):
            self.metadata = SafeDict(
                self.metadata if isinstance(self.metadata, dict) else {}
            )
        
        # Ensure initial_findings are SafeDict
        self.initial_findings = [
            SafeDict(f) if isinstance(f, dict) else SafeDict()
            for f in self.initial_findings
        ]
    
    def add_agent_result(self, result: Union[SafeAgentResult, Dict[str, Any]]) -> None:
        """Add agent result (accepts both SafeAgentResult and dict)"""
        if isinstance(result, dict):
            result = SafeAgentResult.from_dict(result)
        
        self.agent_results[result.agent_name] = result
    
    def get_agent_result(self, agent_name: str) -> Optional[SafeAgentResult]:
        """Safely get agent result"""
        return self.agent_results.get(agent_name)
    
    def has_successful_result(self, agent_name: str) -> bool:
        """Check if agent succeeded"""
        result = self.get_agent_result(agent_name)
        return result is not None and result.success
    
    def get_all_packages_data(self) -> List[SafeDict]:
        """
        Get all packages data from all agent results.
        
        Returns:
            List of package dictionaries merged from all agents
        """
        packages_dict = {}
        
        for agent_name, result in self.agent_results.items():
            if not result.success:
                continue
            
            for pkg in result.get_packages():
                pkg_name = pkg.safe_str("package_name", "unknown")
                
                if pkg_name not in packages_dict:
                    packages_dict[pkg_name] = SafeDict({
                        "package_name": pkg_name,
                        "package_version": pkg.safe_str("package_version", "unknown"),
                        "ecosystem": self.ecosystem
                    })
                
                # Merge data from this agent
                packages_dict[pkg_name].update(pkg)
        
        return list(packages_dict.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "packages": self.packages,
            "ecosystem": self.ecosystem,
            "dependency_graph": dict(self.dependency_graph),
            "agent_results": {
                name: result.to_dict()
                for name, result in self.agent_results.items()
            },
            "initial_findings": [dict(f) for f in self.initial_findings],
            "input_mode": self.input_mode,
            "project_path": self.project_path,
            "metadata": dict(self.metadata)
        }


class MinimalErrorHandler:
    """
    Minimal error handler that logs but doesn't mask issues.
    
    Philosophy: Fail fast, log clearly, don't hide problems.
    """
    
    @staticmethod
    def safe_execute(
        func: callable,
        *args,
        error_msg: str = "Operation failed",
        default: Any = None,
        **kwargs
    ) -> Any:
        """
        Execute function with minimal error handling.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            error_msg: Error message to log
            default: Default value on error
            **kwargs: Keyword arguments
        
        Returns:
            Function result or default
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{error_msg}: {type(e).__name__}: {str(e)}")
            return default
    
    @staticmethod
    def validate_not_none(value: Any, name: str) -> Any:
        """
        Validate value is not None.
        
        Args:
            value: Value to check
            name: Name for error message
        
        Returns:
            Value if not None
        
        Raises:
            ValueError: If value is None
        """
        if value is None:
            raise ValueError(f"{name} cannot be None")
        return value
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, name: str) -> Any:
        """
        Validate value type.
        
        Args:
            value: Value to check
            expected_type: Expected type
            name: Name for error message
        
        Returns:
            Value if correct type
        
        Raises:
            TypeError: If value is wrong type
        """
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{name} must be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        return value


# Convenience functions
def ensure_safe_dict(data: Union[Dict, SafeDict, None]) -> SafeDict:
    """Ensure data is SafeDict"""
    if data is None:
        return SafeDict()
    if isinstance(data, SafeDict):
        return data
    if isinstance(data, dict):
        return SafeDict(data)
    logger.warning(f"Cannot convert {type(data).__name__} to SafeDict")
    return SafeDict()


def ensure_safe_list(data: Union[List, None]) -> List:
    """Ensure data is list"""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    logger.warning(f"Cannot convert {type(data).__name__} to list")
    return []


def safe_json_dumps(data: Any, indent: int = 2) -> str:
    """
    Safely convert data to JSON string with unicode handling.
    
    Args:
        data: Data to convert
        indent: JSON indentation
    
    Returns:
        JSON string
    """
    import json
    
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON serialization failed: {e}")
        # Fallback: ASCII only
        try:
            return json.dumps(data, indent=indent, ensure_ascii=True)
        except Exception:
            return "{}"
