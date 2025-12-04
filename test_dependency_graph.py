"""
Unit tests for Dependency Graph Analyzer.

Tests the core functionality of building dependency graphs, detecting circular
dependencies, version conflicts, and tracing vulnerability paths.
"""

import pytest
import json
import tempfile
from pathlib import Path
from tools.dependency_graph import (
    DependencyGraphAnalyzer,
    DependencyNode,
    CircularDependency,
    VersionConflict,
    build_dependency_graph,
    trace_vulnerability
)


class TestDependencyNode:
    """Test DependencyNode dataclass."""
    
    def test_node_creation(self):
        """Test creating a dependency node."""
        node = DependencyNode(
            name="express",
            version="4.18.2",
            ecosystem="npm",
            depth=1
        )
        
        assert node.name == "express"
        assert node.version == "4.18.2"
        assert node.ecosystem == "npm"
        assert node.depth == 1
        assert len(node.dependencies) == 0
    
    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        node = DependencyNode(
            name="lodash",
            version="4.17.21",
            ecosystem="npm",
            depth=2
        )
        
        result = node.to_dict()
        
        assert result["name"] == "lodash"
        assert result["version"] == "4.17.21"
        assert result["ecosystem"] == "npm"
        assert result["depth"] == 2
        assert "dependencies" in result
    
    def test_node_with_dependencies(self):
        """Test node with nested dependencies."""
        child = DependencyNode(
            name="lodash",
            version="4.17.21",
            ecosystem="npm",
            depth=2
        )
        
        parent = DependencyNode(
            name="express",
            version="4.18.2",
            ecosystem="npm",
            depth=1
        )
        parent.dependencies["lodash"] = child
        
        assert len(parent.dependencies) == 1
        assert "lodash" in parent.dependencies
        assert parent.dependencies["lodash"].name == "lodash"


class TestDependencyGraphAnalyzer:
    """Test DependencyGraphAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = DependencyGraphAnalyzer()
        
        assert analyzer.graph is None
        assert len(analyzer.all_packages) == 0
        assert len(analyzer.circular_dependencies) == 0
        assert len(analyzer.version_conflicts) == 0
    
    def test_build_npm_graph_simple(self):
        """Test building simple npm dependency graph."""
        # Create temporary package.json
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.2",
                    "lodash": "^4.17.21"
                }
            }))
            
            analyzer = DependencyGraphAnalyzer()
            graph = analyzer.build_graph(str(package_json), "npm", max_depth=1)
            
            assert graph is not None
            assert graph["name"] == "test-project"
            assert graph["version"] == "1.0.0"
            assert graph["ecosystem"] == "npm"
            assert "dependencies" in graph
            assert "metadata" in graph
    
    def test_build_python_graph_simple(self):
        """Test building simple Python dependency graph."""
        # Create temporary requirements.txt
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements = Path(tmpdir) / "requirements.txt"
            requirements.write_text("requests==2.28.0\nflask>=2.0.0\n")
            
            analyzer = DependencyGraphAnalyzer()
            graph = analyzer.build_graph(str(requirements), "pypi", max_depth=1)
            
            assert graph is not None
            assert graph["name"] == "root"
            assert graph["ecosystem"] == "pypi"
            assert "dependencies" in graph
            assert "metadata" in graph
    
    def test_trace_vulnerability_impact(self):
        """Test tracing vulnerability through dependency chain."""
        # Create a simple graph manually
        analyzer = DependencyGraphAnalyzer()
        
        # Build graph: root -> express -> body-parser -> lodash
        lodash = DependencyNode("lodash", "4.17.20", "npm", depth=3)
        body_parser = DependencyNode("body-parser", "1.20.1", "npm", depth=2)
        body_parser.dependencies["lodash"] = lodash
        
        express = DependencyNode("express", "4.18.2", "npm", depth=1)
        express.dependencies["body-parser"] = body_parser
        
        root = DependencyNode("root", "1.0.0", "npm", depth=0)
        root.dependencies["express"] = express
        
        analyzer.graph = root
        
        # Trace vulnerability in lodash
        paths = analyzer.trace_vulnerability_impact("lodash")
        
        assert len(paths) > 0
        assert paths[0] == ["root", "express", "body-parser", "lodash"]
    
    def test_trace_vulnerability_multiple_paths(self):
        """Test tracing vulnerability with multiple dependency paths."""
        analyzer = DependencyGraphAnalyzer()
        
        # Build graph with multiple paths to lodash:
        # root -> express -> lodash
        # root -> webpack -> lodash
        lodash1 = DependencyNode("lodash", "4.17.20", "npm", depth=2)
        lodash2 = DependencyNode("lodash", "4.17.21", "npm", depth=2)
        
        express = DependencyNode("express", "4.18.2", "npm", depth=1)
        express.dependencies["lodash"] = lodash1
        
        webpack = DependencyNode("webpack", "5.0.0", "npm", depth=1)
        webpack.dependencies["lodash"] = lodash2
        
        root = DependencyNode("root", "1.0.0", "npm", depth=0)
        root.dependencies["express"] = express
        root.dependencies["webpack"] = webpack
        
        analyzer.graph = root
        
        # Trace vulnerability in lodash
        paths = analyzer.trace_vulnerability_impact("lodash")
        
        assert len(paths) == 2
        assert ["root", "express", "lodash"] in paths
        assert ["root", "webpack", "lodash"] in paths
    
    def test_detect_circular_dependencies(self):
        """Test detecting circular dependency chains."""
        analyzer = DependencyGraphAnalyzer()
        
        # Create circular dependency: A -> B -> C -> A
        node_a = DependencyNode("package-a", "1.0.0", "npm", depth=0)
        node_b = DependencyNode("package-b", "1.0.0", "npm", depth=1)
        node_c = DependencyNode("package-c", "1.0.0", "npm", depth=2)
        
        node_a.dependencies["package-b"] = node_b
        node_b.dependencies["package-c"] = node_c
        node_c.dependencies["package-a"] = node_a  # Creates cycle
        
        circular_deps = analyzer.detect_circular_dependencies(node_a)
        
        assert len(circular_deps) > 0
        # Check that cycle contains the expected packages
        cycle_packages = set(circular_deps[0].cycle)
        assert "package-a" in cycle_packages or "package-b" in cycle_packages
    
    def test_detect_version_conflicts(self):
        """Test detecting version conflicts."""
        analyzer = DependencyGraphAnalyzer()
        
        # Create version conflict:
        # root -> express -> lodash@4.17.20
        # root -> webpack -> lodash@4.17.21
        lodash_old = DependencyNode("lodash", "4.17.20", "npm", depth=2)
        lodash_new = DependencyNode("lodash", "4.17.21", "npm", depth=2)
        
        express = DependencyNode("express", "4.18.2", "npm", depth=1)
        express.dependencies["lodash"] = lodash_old
        
        webpack = DependencyNode("webpack", "5.0.0", "npm", depth=1)
        webpack.dependencies["lodash"] = lodash_new
        
        root = DependencyNode("root", "1.0.0", "npm", depth=0)
        root.dependencies["express"] = express
        root.dependencies["webpack"] = webpack
        
        conflicts = analyzer.detect_version_conflicts(root)
        
        assert len(conflicts) > 0
        # Find lodash conflict
        lodash_conflict = next((c for c in conflicts if c.package_name == "lodash"), None)
        assert lodash_conflict is not None
        assert "4.17.20" in lodash_conflict.versions
        assert "4.17.21" in lodash_conflict.versions
    
    def test_visualize_graph(self):
        """Test generating Mermaid diagram."""
        analyzer = DependencyGraphAnalyzer()
        
        # Create simple graph
        lodash = DependencyNode("lodash", "4.17.21", "npm", depth=2)
        express = DependencyNode("express", "4.18.2", "npm", depth=1)
        express.dependencies["lodash"] = lodash
        
        root = DependencyNode("root", "1.0.0", "npm", depth=0)
        root.dependencies["express"] = express
        
        analyzer.graph = root
        
        diagram = analyzer.visualize_graph(max_depth=3)
        
        assert "graph TD" in diagram
        assert "root" in diagram
        assert "express" in diagram
        assert "lodash" in diagram
        assert "-->" in diagram
    
    def test_get_package_list(self):
        """Test extracting flat package list."""
        analyzer = DependencyGraphAnalyzer()
        
        # Create graph
        lodash = DependencyNode("lodash", "4.17.21", "npm", depth=2)
        express = DependencyNode("express", "4.18.2", "npm", depth=1)
        express.dependencies["lodash"] = lodash
        
        root = DependencyNode("root", "1.0.0", "npm", depth=0)
        root.dependencies["express"] = express
        
        # Manually populate all_packages
        analyzer.all_packages["express"].append(express)
        analyzer.all_packages["lodash"].append(lodash)
        
        packages = analyzer.get_package_list()
        
        assert len(packages) >= 2
        package_names = [p["name"] for p in packages]
        assert "express" in package_names
        assert "lodash" in package_names
    
    def test_empty_graph_handling(self):
        """Test handling of empty/missing graphs."""
        analyzer = DependencyGraphAnalyzer()
        
        # Test with no graph
        paths = analyzer.trace_vulnerability_impact("lodash")
        assert len(paths) == 0
        
        circular = analyzer.detect_circular_dependencies(None)
        assert len(circular) == 0
        
        conflicts = analyzer.detect_version_conflicts(None)
        assert len(conflicts) == 0
        
        diagram = analyzer.visualize_graph(None)
        assert "No graph available" in diagram


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_build_dependency_graph_npm(self):
        """Test build_dependency_graph convenience function for npm."""
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-app",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.2"
                }
            }))
            
            graph = build_dependency_graph(str(package_json), "npm", max_depth=1)
            
            assert graph is not None
            assert graph["name"] == "test-app"
            assert "metadata" in graph
    
    def test_build_dependency_graph_python(self):
        """Test build_dependency_graph convenience function for Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements = Path(tmpdir) / "requirements.txt"
            requirements.write_text("flask==2.0.0\n")
            
            graph = build_dependency_graph(str(requirements), "pypi", max_depth=1)
            
            assert graph is not None
            assert graph["ecosystem"] == "pypi"
            assert "metadata" in graph


class TestCircularDependency:
    """Test CircularDependency dataclass."""
    
    def test_circular_dependency_creation(self):
        """Test creating circular dependency."""
        cd = CircularDependency(
            cycle=["package-a", "package-b", "package-c", "package-a"]
        )
        
        assert len(cd.cycle) == 4
        assert cd.severity == "medium"
    
    def test_circular_dependency_to_dict(self):
        """Test converting to dictionary."""
        cd = CircularDependency(
            cycle=["A", "B", "C", "A"],
            severity="high"
        )
        
        result = cd.to_dict()
        
        assert result["cycle"] == ["A", "B", "C", "A"]
        assert result["severity"] == "high"
        assert "description" in result


class TestVersionConflict:
    """Test VersionConflict dataclass."""
    
    def test_version_conflict_creation(self):
        """Test creating version conflict."""
        vc = VersionConflict(
            package_name="lodash",
            versions=["4.17.20", "4.17.21"],
            paths=[["root", "express", "lodash"], ["root", "webpack", "lodash"]]
        )
        
        assert vc.package_name == "lodash"
        assert len(vc.versions) == 2
        assert len(vc.paths) == 2
    
    def test_version_conflict_to_dict(self):
        """Test converting to dictionary."""
        vc = VersionConflict(
            package_name="react",
            versions=["17.0.0", "18.0.0"],
            paths=[["root", "app", "react"]],
            severity="high"
        )
        
        result = vc.to_dict()
        
        assert result["package"] == "react"
        assert result["conflicting_versions"] == ["17.0.0", "18.0.0"]
        assert result["severity"] == "high"
        assert "description" in result


class TestGraphMetadata:
    """Test graph metadata generation."""
    
    def test_metadata_in_graph(self):
        """Test that metadata is included in graph output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test",
                "version": "1.0.0",
                "dependencies": {}
            }))
            
            analyzer = DependencyGraphAnalyzer()
            graph = analyzer.build_graph(str(package_json), "npm")
            
            assert "metadata" in graph
            metadata = graph["metadata"]
            assert "ecosystem" in metadata
            assert "manifest_path" in metadata
            assert "total_packages" in metadata
            assert metadata["ecosystem"] == "npm"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
