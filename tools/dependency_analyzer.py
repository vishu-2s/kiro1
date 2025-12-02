"""
Dependency graph analysis for Multi-Agent Security Analysis System.

This module analyzes the complete dependency tree to find malicious scripts
hidden in transitive dependencies.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    name: str
    version: str
    depth: int
    parent: Optional[str] = None
    scripts: Dict[str, str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.scripts is None:
            self.scripts = {}
        if self.dependencies is None:
            self.dependencies = []


class DependencyGraphAnalyzer:
    """Analyzes npm dependency graphs for security issues."""
    
    def __init__(self, max_depth: int = 10):
        """
        Initialize dependency graph analyzer.
        
        Args:
            max_depth: Maximum depth to traverse in dependency tree
        """
        self.max_depth = max_depth
        self.visited: Set[str] = set()
        self.dependency_graph: Dict[str, DependencyNode] = {}
    
    def analyze_package_lock(self, package_lock_path: str) -> Dict[str, Any]:
        """
        Analyze package-lock.json to build dependency graph.
        
        Args:
            package_lock_path: Path to package-lock.json
            
        Returns:
            Dictionary with dependency graph and statistics
        """
        try:
            with open(package_lock_path, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)
            
            # Handle both lockfileVersion 1 and 2/3
            if 'packages' in lock_data:
                # Lockfile v2/v3
                return self._analyze_v2_lock(lock_data)
            elif 'dependencies' in lock_data:
                # Lockfile v1
                return self._analyze_v1_lock(lock_data)
            else:
                logger.warning(f"Unknown package-lock.json format")
                return {"dependencies": [], "total_count": 0}
                
        except Exception as e:
            logger.error(f"Failed to analyze package-lock.json: {e}")
            return {"dependencies": [], "total_count": 0, "error": str(e)}
    
    def _analyze_v2_lock(self, lock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lockfile version 2/3 format."""
        packages = lock_data.get('packages', {})
        dependencies = []
        
        for package_path, package_info in packages.items():
            # Skip root package (empty string key)
            if not package_path:
                continue
            
            # Extract package name from path (node_modules/package-name)
            name = package_path.split('node_modules/')[-1]
            version = package_info.get('version', 'unknown')
            
            # Calculate depth based on path
            depth = package_path.count('node_modules')
            
            # Get scripts if present
            scripts = {}
            if 'scripts' in package_info:
                scripts = package_info['scripts']
            
            # Get dependencies
            deps = []
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                if dep_type in package_info:
                    deps.extend(package_info[dep_type].keys())
            
            node = DependencyNode(
                name=name,
                version=version,
                depth=depth,
                scripts=scripts,
                dependencies=deps
            )
            
            dependencies.append(node)
            self.dependency_graph[name] = node
        
        return {
            "dependencies": dependencies,
            "total_count": len(dependencies),
            "max_depth": max(d.depth for d in dependencies) if dependencies else 0
        }
    
    def _analyze_v1_lock(self, lock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lockfile version 1 format."""
        dependencies = []
        
        def traverse(deps: Dict[str, Any], depth: int = 1, parent: str = None):
            for name, info in deps.items():
                version = info.get('version', 'unknown')
                
                # Get scripts (not usually in lock file, but check anyway)
                scripts = info.get('scripts', {})
                
                # Get sub-dependencies
                sub_deps = []
                if 'dependencies' in info:
                    sub_deps = list(info['dependencies'].keys())
                
                node = DependencyNode(
                    name=name,
                    version=version,
                    depth=depth,
                    parent=parent,
                    scripts=scripts,
                    dependencies=sub_deps
                )
                
                dependencies.append(node)
                self.dependency_graph[name] = node
                
                # Recurse into sub-dependencies
                if 'dependencies' in info and depth < self.max_depth:
                    traverse(info['dependencies'], depth + 1, name)
        
        if 'dependencies' in lock_data:
            traverse(lock_data['dependencies'])
        
        return {
            "dependencies": dependencies,
            "total_count": len(dependencies),
            "max_depth": max(d.depth for d in dependencies) if dependencies else 0
        }
    
    def analyze_node_modules(self, node_modules_path: str) -> List[Dict[str, Any]]:
        """
        Scan node_modules directory for package.json files with scripts.
        
        Args:
            node_modules_path: Path to node_modules directory
            
        Returns:
            List of packages with their scripts
        """
        packages_with_scripts = []
        node_modules = Path(node_modules_path)
        
        if not node_modules.exists():
            logger.warning(f"node_modules not found at {node_modules_path}")
            return packages_with_scripts
        
        try:
            # Scan for package.json files
            for package_json in node_modules.rglob('package.json'):
                try:
                    # Skip if too deep or in nested node_modules
                    relative_path = package_json.relative_to(node_modules)
                    depth = len([p for p in relative_path.parts if p == 'node_modules'])
                    
                    if depth > self.max_depth:
                        continue
                    
                    with open(package_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    name = data.get('name', 'unknown')
                    version = data.get('version', 'unknown')
                    scripts = data.get('scripts', {})
                    
                    if scripts:
                        packages_with_scripts.append({
                            "name": name,
                            "version": version,
                            "depth": depth,
                            "scripts": scripts,
                            "path": str(package_json.parent)
                        })
                        
                except Exception as e:
                    logger.debug(f"Error reading {package_json}: {e}")
                    continue
            
            logger.info(f"Found {len(packages_with_scripts)} packages with scripts in node_modules")
            
        except Exception as e:
            logger.error(f"Error scanning node_modules: {e}")
        
        return packages_with_scripts
    
    def find_dependency_chain(self, package_name: str) -> List[str]:
        """
        Find the dependency chain from root to a specific package.
        
        Args:
            package_name: Name of the package to find chain for
            
        Returns:
            List of package names from root to target
        """
        if package_name not in self.dependency_graph:
            return [package_name]
        
        chain = [package_name]
        current = self.dependency_graph[package_name]
        
        while current.parent:
            chain.insert(0, current.parent)
            if current.parent in self.dependency_graph:
                current = self.dependency_graph[current.parent]
            else:
                break
        
        return chain


def analyze_dependency_tree(directory_path: str) -> Dict[str, Any]:
    """
    Analyze complete dependency tree for a project.
    
    Args:
        directory_path: Path to project directory
        
    Returns:
        Analysis results with dependency graph and script findings
    """
    analyzer = DependencyGraphAnalyzer()
    results = {
        "has_lock_file": False,
        "has_node_modules": False,
        "dependencies": [],
        "packages_with_scripts": [],
        "total_dependencies": 0
    }
    
    directory = Path(directory_path)
    
    # Check for package-lock.json
    package_lock = directory / "package-lock.json"
    if package_lock.exists():
        results["has_lock_file"] = True
        lock_analysis = analyzer.analyze_package_lock(str(package_lock))
        results.update(lock_analysis)
        logger.info(f"Analyzed package-lock.json: {lock_analysis.get('total_count', 0)} dependencies")
    
    # Check for node_modules
    node_modules = directory / "node_modules"
    if node_modules.exists():
        results["has_node_modules"] = True
        packages = analyzer.analyze_node_modules(str(node_modules))
        results["packages_with_scripts"] = packages
        logger.info(f"Scanned node_modules: {len(packages)} packages with scripts")
    
    return results
