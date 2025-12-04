"""
Dependency Graph Analyzer for Multi-Agent Security Analysis System.

This module builds and analyzes complete dependency graphs for vulnerability tracing,
circular dependency detection, and version conflict identification.

Supports npm and Python ecosystems with transitive dependency resolution.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    name: str
    version: str
    ecosystem: str
    depth: int = 0
    dependencies: Dict[str, 'DependencyNode'] = field(default_factory=dict)
    parent_paths: List[List[str]] = field(default_factory=list)
    
    def to_dict(self, visited: Optional[set] = None, max_depth: int = 10) -> Dict[str, Any]:
        """
        Convert node to dictionary representation.
        
        Args:
            visited: Set of visited package names to prevent circular expansion
            max_depth: Maximum depth to prevent infinite recursion
        
        Returns:
            Dictionary representation of the node
        """
        if visited is None:
            visited = set()
        
        # Create unique key for this node (name@version)
        node_key = f"{self.name}@{self.version}"
        
        # If we've seen this node before or exceeded max depth, return reference only
        if node_key in visited or self.depth >= max_depth:
            return {
                "name": self.name,
                "version": self.version,
                "ecosystem": self.ecosystem,
                "depth": self.depth,
                "dependencies": {},
                "circular_reference": node_key in visited
            }
        
        # Mark this node as visited
        visited.add(node_key)
        
        # Recursively convert dependencies
        result = {
            "name": self.name,
            "version": self.version,
            "ecosystem": self.ecosystem,
            "depth": self.depth,
            "dependencies": {
                name: dep.to_dict(visited.copy(), max_depth) 
                for name, dep in self.dependencies.items()
            }
        }
        
        return result


@dataclass
class CircularDependency:
    """Represents a circular dependency chain."""
    cycle: List[str]
    severity: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cycle": self.cycle,
            "severity": self.severity,
            "description": f"Circular dependency: {' -> '.join(self.cycle)}"
        }


@dataclass
class VersionConflict:
    """Represents a version conflict between dependencies."""
    package_name: str
    versions: List[str]
    paths: List[List[str]]
    severity: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "package": self.package_name,
            "conflicting_versions": self.versions,
            "dependency_paths": self.paths,
            "severity": self.severity,
            "description": f"Version conflict for '{self.package_name}': {', '.join(self.versions)}"
        }


class DependencyGraphAnalyzer:
    """
    Analyzes dependency graphs and traces vulnerabilities.
    
    Validates Requirements 10.1-10.5:
    - 10.1: Build complete dependency graphs
    - 10.2: Trace impact through dependency chains
    - 10.3: Identify paths from root to vulnerable packages
    - 10.4: Detect circular dependencies and version conflicts
    - 10.5: Visualize dependency relationships
    """
    
    def __init__(self):
        """Initialize dependency graph analyzer."""
        self.graph: Optional[DependencyNode] = None
        self.all_packages: Dict[str, List[DependencyNode]] = defaultdict(list)
        self.circular_dependencies: List[CircularDependency] = []
        self.version_conflicts: List[VersionConflict] = []
        logger.info("Initialized DependencyGraphAnalyzer")
    
    def build_graph(self, manifest_path: str, ecosystem: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        Build complete dependency graph from manifest file.
        
        Validates Requirement 10.1: Build complete dependency graphs
        
        Process:
        1. Parse manifest file (package.json, requirements.txt, etc.)
        2. Extract direct dependencies
        3. Recursively resolve transitive dependencies
        4. Build graph structure with parent-child relationships
        5. Detect circular dependencies
        6. Identify version conflicts
        
        Args:
            manifest_path: Path to manifest file
            ecosystem: Ecosystem type ('npm' or 'pypi')
            max_depth: Maximum depth for transitive resolution (default: 10)
        
        Returns:
            Complete dependency graph with all relationships
        """
        logger.info(f"Building dependency graph from {manifest_path} (ecosystem: {ecosystem})")
        
        try:
            if ecosystem == "npm":
                self.graph = self._build_npm_graph(manifest_path, max_depth)
            elif ecosystem == "pypi":
                self.graph = self._build_python_graph(manifest_path, max_depth)
            else:
                logger.error(f"Unsupported ecosystem: {ecosystem}")
                return self._create_empty_graph()
            
            # Detect issues
            self.circular_dependencies = self.detect_circular_dependencies(self.graph)
            self.version_conflicts = self.detect_version_conflicts(self.graph)
            
            # Convert to dictionary
            graph_dict = self.graph.to_dict() if self.graph else self._create_empty_graph()
            
            # Add metadata
            graph_dict["metadata"] = {
                "ecosystem": ecosystem,
                "manifest_path": manifest_path,
                "total_packages": len(self.all_packages),
                "circular_dependencies_count": len(self.circular_dependencies),
                "version_conflicts_count": len(self.version_conflicts)
            }
            
            # Add issues
            graph_dict["circular_dependencies"] = [cd.to_dict() for cd in self.circular_dependencies]
            graph_dict["version_conflicts"] = [vc.to_dict() for vc in self.version_conflicts]
            
            logger.info(f"Built dependency graph: {len(self.all_packages)} packages, "
                       f"{len(self.circular_dependencies)} circular deps, "
                       f"{len(self.version_conflicts)} version conflicts")
            
            return graph_dict
        
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}", exc_info=True)
            return self._create_empty_graph()
    
    def _build_npm_graph(self, manifest_path: str, max_depth: int) -> DependencyNode:
        """Build dependency graph for npm ecosystem."""
        from tools.npm_analyzer import NpmAnalyzer
        
        analyzer = NpmAnalyzer()
        
        # Extract package metadata
        metadata = analyzer.extract_package_metadata(manifest_path)
        root_name = metadata.get("name", "root")
        root_version = metadata.get("version", "1.0.0")
        
        # Create root node
        root = DependencyNode(
            name=root_name,
            version=root_version,
            ecosystem="npm",
            depth=0
        )
        
        # Extract direct dependencies
        dependencies = analyzer.extract_dependencies(manifest_path)
        
        # Build graph recursively
        visited = set()
        self._resolve_npm_dependencies(root, dependencies, visited, max_depth)
        
        return root
    
    def _resolve_npm_dependencies(
        self, 
        parent: DependencyNode, 
        dependencies: List[Dict[str, Any]], 
        visited: Set[str],
        max_depth: int
    ):
        """Recursively resolve npm dependencies using real registry data."""
        if parent.depth >= max_depth:
            logger.debug(f"Reached max depth {max_depth} at package {parent.name}")
            return
        
        # Import transitive resolver
        from tools.transitive_resolver import TransitiveDependencyResolver
        resolver = TransitiveDependencyResolver()
        
        for dep in dependencies:
            dep_name = dep["name"]
            dep_version = dep["version"]
            
            # Track all packages
            dep_key = f"{dep_name}@{dep_version}"
            
            # Check for circular dependency
            if dep_key in visited:
                logger.debug(f"Circular dependency detected: {dep_key}")
                continue
            
            # Mark as visited
            visited.add(dep_key)
            
            # Create dependency node
            dep_node = DependencyNode(
                name=dep_name,
                version=dep_version,
                ecosystem="npm",
                depth=parent.depth + 1
            )
            
            # Add to parent
            parent.dependencies[dep_name] = dep_node
            
            # Track in all_packages
            self.all_packages[dep_name].append(dep_node)
            
            # Fetch real transitive dependencies from npm registry
            try:
                metadata = resolver._fetch_package_metadata(dep_name, dep_version, "npm")
                if metadata and metadata.dependencies:
                    # Convert to expected format
                    transitive_deps = [
                        {"name": name, "version": version}
                        for name, version in metadata.dependencies.items()
                    ]
                    # Recursively resolve transitive dependencies
                    self._resolve_npm_dependencies(dep_node, transitive_deps, visited, max_depth)
            except Exception as e:
                logger.warning(f"Could not fetch transitive deps for {dep_key}: {e}")
            
            # Remove from visited after processing (for other branches)
            visited.discard(dep_key)
    
    def _build_python_graph(self, manifest_path: str, max_depth: int) -> DependencyNode:
        """Build dependency graph for Python ecosystem."""
        from tools.python_analyzer import PythonAnalyzer
        
        analyzer = PythonAnalyzer()
        
        # Create root node
        root = DependencyNode(
            name="root",
            version="1.0.0",
            ecosystem="pypi",
            depth=0
        )
        
        # Extract direct dependencies
        dependencies = analyzer.extract_dependencies(manifest_path)
        
        # Build graph recursively
        visited = set()
        self._resolve_python_dependencies(root, dependencies, visited, max_depth)
        
        return root
    
    def _resolve_python_dependencies(
        self, 
        parent: DependencyNode, 
        dependencies: List[Dict[str, Any]], 
        visited: Set[str],
        max_depth: int
    ):
        """Recursively resolve Python dependencies using real PyPI data."""
        if parent.depth >= max_depth:
            logger.debug(f"Reached max depth {max_depth} at package {parent.name}")
            return
        
        # Import transitive resolver
        from tools.transitive_resolver import TransitiveDependencyResolver
        resolver = TransitiveDependencyResolver()
        
        for dep in dependencies:
            dep_name = dep["name"]
            dep_version = dep.get("version", "*")
            
            # Resolve version spec to actual version
            if dep_version == "*" or not dep_version:
                dep_version = resolver._fetch_latest_version(dep_name, "pypi") or "latest"
            
            # Track all packages
            dep_key = f"{dep_name}@{dep_version}"
            
            # Check for circular dependency
            if dep_key in visited:
                logger.debug(f"Circular dependency detected: {dep_key}")
                continue
            
            # Mark as visited
            visited.add(dep_key)
            
            # Create dependency node
            dep_node = DependencyNode(
                name=dep_name,
                version=dep_version,
                ecosystem="pypi",
                depth=parent.depth + 1
            )
            
            # Add to parent
            parent.dependencies[dep_name] = dep_node
            
            # Track in all_packages
            self.all_packages[dep_name].append(dep_node)
            
            # Fetch real transitive dependencies from PyPI
            try:
                metadata = resolver._fetch_package_metadata(dep_name, dep_version, "pypi")
                if metadata and metadata.dependencies:
                    # Convert to expected format
                    transitive_deps = [
                        {"name": name, "version": version}
                        for name, version in metadata.dependencies.items()
                    ]
                    # Recursively resolve transitive dependencies
                    self._resolve_python_dependencies(dep_node, transitive_deps, visited, max_depth)
            except Exception as e:
                logger.warning(f"Could not fetch transitive deps for {dep_key}: {e}")
            
            # Remove from visited after processing (for other branches)
            visited.discard(dep_key)
    
    def trace_vulnerability_impact(
        self, 
        vulnerable_package: str, 
        graph: Optional[Dict[str, Any]] = None
    ) -> List[List[str]]:
        """
        Trace impact of vulnerable package through dependency chain.
        
        Validates Requirements 10.2 and 10.3:
        - 10.2: Trace impact through dependency chains
        - 10.3: Identify paths from root to vulnerable package
        
        Args:
            vulnerable_package: Name of the vulnerable package
            graph: Optional graph dict (uses self.graph if not provided)
        
        Returns:
            List of dependency paths from root to vulnerable package
            Example: [["root", "express", "body-parser", "lodash"]]
        """
        if graph is None and self.graph is None:
            logger.warning("No graph available for vulnerability tracing")
            return []
        
        paths = []
        current_path = []
        
        # Use provided graph or convert self.graph
        if graph is None:
            graph_node = self.graph
        else:
            # Convert dict to node if needed
            graph_node = self.graph
        
        # Find all paths to vulnerable package
        self._find_paths_to_package(graph_node, vulnerable_package, current_path, paths)
        
        logger.info(f"Found {len(paths)} paths to vulnerable package '{vulnerable_package}'")
        return paths
    
    def _find_paths_to_package(
        self, 
        node: Optional[DependencyNode], 
        target_package: str, 
        current_path: List[str], 
        all_paths: List[List[str]]
    ):
        """Recursively find all paths to target package."""
        if node is None:
            return
        
        # Add current node to path
        current_path.append(node.name)
        
        # Check if this is the target
        if node.name == target_package:
            all_paths.append(current_path.copy())
        
        # Recurse into dependencies
        for dep_name, dep_node in node.dependencies.items():
            self._find_paths_to_package(dep_node, target_package, current_path, all_paths)
        
        # Backtrack
        current_path.pop()
    
    def detect_circular_dependencies(
        self, 
        graph: Optional[DependencyNode] = None
    ) -> List[CircularDependency]:
        """
        Detect circular dependency chains.
        
        Validates Requirement 10.4: Detect circular dependencies
        
        Args:
            graph: Root node of dependency graph
        
        Returns:
            List of circular dependency chains
        """
        if graph is None:
            return []
        
        circular_deps = []
        visited = set()
        rec_stack = []
        
        self._detect_cycles_dfs(graph, visited, rec_stack, circular_deps)
        
        logger.info(f"Detected {len(circular_deps)} circular dependencies")
        return circular_deps
    
    def _detect_cycles_dfs(
        self, 
        node: DependencyNode, 
        visited: Set[str], 
        rec_stack: List[str], 
        circular_deps: List[CircularDependency]
    ):
        """DFS-based cycle detection."""
        node_key = f"{node.name}@{node.version}"
        
        # Add to recursion stack
        rec_stack.append(node.name)
        visited.add(node_key)
        
        # Check dependencies
        for dep_name, dep_node in node.dependencies.items():
            dep_key = f"{dep_node.name}@{dep_node.version}"
            
            # If dependency is in recursion stack, we found a cycle
            if dep_node.name in rec_stack:
                # Extract cycle
                cycle_start = rec_stack.index(dep_node.name)
                cycle = rec_stack[cycle_start:] + [dep_node.name]
                
                # Check if this cycle is already recorded
                if not any(set(cd.cycle) == set(cycle) for cd in circular_deps):
                    circular_deps.append(CircularDependency(cycle=cycle))
                    logger.debug(f"Found circular dependency: {' -> '.join(cycle)}")
            
            # Recurse if not visited
            elif dep_key not in visited:
                self._detect_cycles_dfs(dep_node, visited, rec_stack, circular_deps)
        
        # Remove from recursion stack
        rec_stack.pop()
    
    def detect_version_conflicts(
        self, 
        graph: Optional[DependencyNode] = None
    ) -> List[VersionConflict]:
        """
        Detect packages with conflicting version requirements.
        
        Validates Requirement 10.4: Detect version conflicts
        
        Args:
            graph: Root node of dependency graph
        
        Returns:
            List of version conflicts
        """
        if graph is None:
            return []
        
        # Collect all versions of each package
        package_versions: Dict[str, Dict[str, List[List[str]]]] = defaultdict(lambda: defaultdict(list))
        
        self._collect_package_versions(graph, [], package_versions)
        
        # Find conflicts
        conflicts = []
        for package_name, versions_dict in package_versions.items():
            if len(versions_dict) > 1:
                # Multiple versions found
                versions = list(versions_dict.keys())
                paths = []
                for version, version_paths in versions_dict.items():
                    paths.extend(version_paths)
                
                conflict = VersionConflict(
                    package_name=package_name,
                    versions=versions,
                    paths=paths
                )
                conflicts.append(conflict)
                logger.debug(f"Version conflict for '{package_name}': {versions}")
        
        logger.info(f"Detected {len(conflicts)} version conflicts")
        return conflicts
    
    def _collect_package_versions(
        self, 
        node: DependencyNode, 
        current_path: List[str], 
        package_versions: Dict[str, Dict[str, List[List[str]]]]
    ):
        """Recursively collect all package versions and their paths."""
        current_path.append(node.name)
        
        # Record this package version and path
        package_versions[node.name][node.version].append(current_path.copy())
        
        # Recurse into dependencies
        for dep_name, dep_node in node.dependencies.items():
            self._collect_package_versions(dep_node, current_path, package_versions)
        
        current_path.pop()
    
    def visualize_graph(
        self, 
        graph: Optional[Dict[str, Any]] = None, 
        max_depth: int = 3
    ) -> str:
        """
        Generate Mermaid diagram of dependency graph.
        
        Validates Requirement 10.5: Visualize dependency relationships
        
        Args:
            graph: Graph dictionary (uses self.graph if not provided)
            max_depth: Maximum depth to visualize (default: 3)
        
        Returns:
            Mermaid diagram string
        """
        if graph is None and self.graph is None:
            return "graph TD\n    A[No graph available]"
        
        mermaid_lines = ["graph TD"]
        node_counter = [0]  # Use list to allow modification in nested function
        node_ids = {}
        
        def get_node_id(name: str) -> str:
            """Get or create node ID."""
            if name not in node_ids:
                node_ids[name] = f"N{node_counter[0]}"
                node_counter[0] += 1
            return node_ids[name]
        
        def add_node(node: DependencyNode, depth: int = 0):
            """Recursively add nodes to diagram."""
            if depth > max_depth:
                return
            
            node_id = get_node_id(node.name)
            node_label = f"{node.name}@{node.version}"
            
            # Add node definition
            if depth == 0:
                mermaid_lines.append(f"    {node_id}[{node_label}]")
                mermaid_lines.append(f"    style {node_id} fill:#e1f5ff")
            
            # Add dependencies
            for dep_name, dep_node in node.dependencies.items():
                dep_id = get_node_id(dep_name)
                dep_label = f"{dep_node.name}@{dep_node.version}"
                
                # Add dependency node
                mermaid_lines.append(f"    {dep_id}[{dep_label}]")
                
                # Add edge
                mermaid_lines.append(f"    {node_id} --> {dep_id}")
                
                # Recurse
                add_node(dep_node, depth + 1)
        
        # Build diagram
        if self.graph:
            add_node(self.graph)
        
        # Add legend for circular dependencies
        if self.circular_dependencies:
            mermaid_lines.append("")
            mermaid_lines.append("    %% Circular Dependencies Detected")
            for i, cd in enumerate(self.circular_dependencies[:3]):  # Show first 3
                cycle_str = " -> ".join(cd.cycle)
                mermaid_lines.append(f"    %% Cycle {i+1}: {cycle_str}")
        
        # Add legend for version conflicts
        if self.version_conflicts:
            mermaid_lines.append("")
            mermaid_lines.append("    %% Version Conflicts Detected")
            for i, vc in enumerate(self.version_conflicts[:3]):  # Show first 3
                versions_str = ", ".join(vc.versions)
                mermaid_lines.append(f"    %% Conflict {i+1}: {vc.package_name} ({versions_str})")
        
        diagram = "\n".join(mermaid_lines)
        logger.debug(f"Generated Mermaid diagram with {len(node_ids)} nodes")
        return diagram
    
    def get_package_list(self) -> List[Dict[str, str]]:
        """
        Extract flat list of all packages from graph.
        
        Returns:
            List of package dictionaries with name, version, ecosystem
        """
        packages = []
        seen = set()
        
        for package_name, nodes in self.all_packages.items():
            for node in nodes:
                key = f"{node.name}@{node.version}"
                if key not in seen:
                    packages.append({
                        "name": node.name,
                        "version": node.version,
                        "ecosystem": node.ecosystem
                    })
                    seen.add(key)
        
        logger.debug(f"Extracted {len(packages)} unique packages from graph")
        return packages
    
    def _create_empty_graph(self) -> Dict[str, Any]:
        """Create empty graph structure."""
        return {
            "name": "root",
            "version": "1.0.0",
            "ecosystem": "unknown",
            "depth": 0,
            "dependencies": {},
            "metadata": {
                "total_packages": 0,
                "circular_dependencies_count": 0,
                "version_conflicts_count": 0
            },
            "circular_dependencies": [],
            "version_conflicts": []
        }


# Convenience functions for external use

def build_dependency_graph(
    manifest_path: str, 
    ecosystem: str, 
    max_depth: int = 10
) -> Dict[str, Any]:
    """
    Build dependency graph from manifest file.
    
    Args:
        manifest_path: Path to manifest file
        ecosystem: Ecosystem type ('npm' or 'pypi')
        max_depth: Maximum depth for transitive resolution
    
    Returns:
        Complete dependency graph dictionary
    """
    analyzer = DependencyGraphAnalyzer()
    return analyzer.build_graph(manifest_path, ecosystem, max_depth)


def trace_vulnerability(
    vulnerable_package: str, 
    graph: Dict[str, Any]
) -> List[List[str]]:
    """
    Trace vulnerability impact through dependency chain.
    
    Args:
        vulnerable_package: Name of vulnerable package
        graph: Dependency graph dictionary
    
    Returns:
        List of paths from root to vulnerable package
    """
    analyzer = DependencyGraphAnalyzer()
    analyzer.graph = _dict_to_node(graph)
    return analyzer.trace_vulnerability_impact(vulnerable_package)


def _dict_to_node(graph_dict: Dict[str, Any]) -> DependencyNode:
    """Convert graph dictionary to DependencyNode."""
    node = DependencyNode(
        name=graph_dict.get("name", "root"),
        version=graph_dict.get("version", "1.0.0"),
        ecosystem=graph_dict.get("ecosystem", "unknown"),
        depth=graph_dict.get("depth", 0)
    )
    
    # Recursively convert dependencies
    for dep_name, dep_dict in graph_dict.get("dependencies", {}).items():
        node.dependencies[dep_name] = _dict_to_node(dep_dict)
    
    return node
