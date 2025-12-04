"""
Example usage of Dependency Graph Analyzer.

This script demonstrates how to use the DependencyGraphAnalyzer to:
1. Build complete dependency graphs
2. Trace vulnerability impact through dependency chains
3. Detect circular dependencies
4. Detect version conflicts
5. Visualize dependency relationships
"""

import json
import tempfile
from pathlib import Path
from tools.dependency_graph import (
    DependencyGraphAnalyzer,
    build_dependency_graph,
    trace_vulnerability
)


def example_npm_analysis():
    """Example: Analyze npm project dependencies."""
    print("=" * 80)
    print("Example 1: npm Dependency Analysis")
    print("=" * 80)
    
    # Create a sample package.json
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "my-web-app",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.2",
                "lodash": "^4.17.21",
                "body-parser": "^1.20.1",
                "axios": "^1.3.0"
            },
            "devDependencies": {
                "webpack": "^5.75.0",
                "jest": "^29.4.0"
            }
        }))
        
        # Build dependency graph
        print(f"\n📦 Building dependency graph from: {package_json}")
        graph = build_dependency_graph(str(package_json), "npm", max_depth=2)
        
        # Display results
        print(f"\n✅ Graph built successfully!")
        print(f"   - Root package: {graph['name']}@{graph['version']}")
        print(f"   - Ecosystem: {graph['ecosystem']}")
        print(f"   - Total packages: {graph['metadata']['total_packages']}")
        print(f"   - Circular dependencies: {graph['metadata']['circular_dependencies_count']}")
        print(f"   - Version conflicts: {graph['metadata']['version_conflicts_count']}")
        
        # Display direct dependencies
        print(f"\n📋 Direct dependencies:")
        for dep_name, dep_info in graph.get('dependencies', {}).items():
            print(f"   - {dep_name}@{dep_info['version']}")
        
        return graph


def example_python_analysis():
    """Example: Analyze Python project dependencies."""
    print("\n" + "=" * 80)
    print("Example 2: Python Dependency Analysis")
    print("=" * 80)
    
    # Create a sample requirements.txt
    with tempfile.TemporaryDirectory() as tmpdir:
        requirements = Path(tmpdir) / "requirements.txt"
        requirements.write_text("""
flask==2.3.0
requests>=2.28.0
sqlalchemy==2.0.0
pytest>=7.2.0
black==23.1.0
""")
        
        # Build dependency graph
        print(f"\n📦 Building dependency graph from: {requirements}")
        graph = build_dependency_graph(str(requirements), "pypi", max_depth=2)
        
        # Display results
        print(f"\n✅ Graph built successfully!")
        print(f"   - Ecosystem: {graph['ecosystem']}")
        print(f"   - Total packages: {graph['metadata']['total_packages']}")
        
        # Display direct dependencies
        print(f"\n📋 Direct dependencies:")
        for dep_name, dep_info in graph.get('dependencies', {}).items():
            print(f"   - {dep_name}@{dep_info['version']}")
        
        return graph


def example_vulnerability_tracing():
    """Example: Trace vulnerability impact through dependency chain."""
    print("\n" + "=" * 80)
    print("Example 3: Vulnerability Impact Tracing")
    print("=" * 80)
    
    # Create analyzer
    analyzer = DependencyGraphAnalyzer()
    
    # Build a sample graph with known vulnerable package
    from tools.dependency_graph import DependencyNode
    
    # Simulate: root -> express -> body-parser -> lodash (vulnerable)
    #           root -> webpack -> lodash (vulnerable)
    lodash_v1 = DependencyNode("lodash", "4.17.20", "npm", depth=3)
    lodash_v2 = DependencyNode("lodash", "4.17.20", "npm", depth=2)
    
    body_parser = DependencyNode("body-parser", "1.20.1", "npm", depth=2)
    body_parser.dependencies["lodash"] = lodash_v1
    
    express = DependencyNode("express", "4.18.2", "npm", depth=1)
    express.dependencies["body-parser"] = body_parser
    
    webpack = DependencyNode("webpack", "5.75.0", "npm", depth=1)
    webpack.dependencies["lodash"] = lodash_v2
    
    root = DependencyNode("my-app", "1.0.0", "npm", depth=0)
    root.dependencies["express"] = express
    root.dependencies["webpack"] = webpack
    
    analyzer.graph = root
    
    # Trace vulnerability
    vulnerable_package = "lodash"
    print(f"\n🔍 Tracing vulnerability in package: {vulnerable_package}")
    
    paths = analyzer.trace_vulnerability_impact(vulnerable_package)
    
    print(f"\n⚠️  Found {len(paths)} dependency path(s) to vulnerable package:")
    for i, path in enumerate(paths, 1):
        path_str = " → ".join(path)
        print(f"   {i}. {path_str}")
    
    print(f"\n💡 Recommendation: Update or remove '{vulnerable_package}' to fix vulnerability")
    print(f"   This affects {len(paths)} dependency chain(s) in your project")


def example_circular_dependency_detection():
    """Example: Detect circular dependencies."""
    print("\n" + "=" * 80)
    print("Example 4: Circular Dependency Detection")
    print("=" * 80)
    
    # Create analyzer
    analyzer = DependencyGraphAnalyzer()
    
    # Build a graph with circular dependency
    from tools.dependency_graph import DependencyNode
    
    # Create circular dependency: A -> B -> C -> A
    node_a = DependencyNode("package-a", "1.0.0", "npm", depth=0)
    node_b = DependencyNode("package-b", "1.0.0", "npm", depth=1)
    node_c = DependencyNode("package-c", "1.0.0", "npm", depth=2)
    
    node_a.dependencies["package-b"] = node_b
    node_b.dependencies["package-c"] = node_c
    node_c.dependencies["package-a"] = node_a  # Creates cycle!
    
    print("\n🔄 Detecting circular dependencies...")
    circular_deps = analyzer.detect_circular_dependencies(node_a)
    
    if circular_deps:
        print(f"\n⚠️  Found {len(circular_deps)} circular dependency chain(s):")
        for i, cd in enumerate(circular_deps, 1):
            cycle_str = " → ".join(cd.cycle)
            print(f"   {i}. {cycle_str}")
            print(f"      Severity: {cd.severity}")
    else:
        print("\n✅ No circular dependencies detected")


def example_version_conflict_detection():
    """Example: Detect version conflicts."""
    print("\n" + "=" * 80)
    print("Example 5: Version Conflict Detection")
    print("=" * 80)
    
    # Create analyzer
    analyzer = DependencyGraphAnalyzer()
    
    # Build a graph with version conflicts
    from tools.dependency_graph import DependencyNode
    
    # Create version conflict:
    # root -> express -> lodash@4.17.20
    # root -> webpack -> lodash@4.17.21
    lodash_old = DependencyNode("lodash", "4.17.20", "npm", depth=2)
    lodash_new = DependencyNode("lodash", "4.17.21", "npm", depth=2)
    
    express = DependencyNode("express", "4.18.2", "npm", depth=1)
    express.dependencies["lodash"] = lodash_old
    
    webpack = DependencyNode("webpack", "5.75.0", "npm", depth=1)
    webpack.dependencies["lodash"] = lodash_new
    
    root = DependencyNode("my-app", "1.0.0", "npm", depth=0)
    root.dependencies["express"] = express
    root.dependencies["webpack"] = webpack
    
    print("\n🔍 Detecting version conflicts...")
    conflicts = analyzer.detect_version_conflicts(root)
    
    if conflicts:
        print(f"\n⚠️  Found {len(conflicts)} version conflict(s):")
        for i, vc in enumerate(conflicts, 1):
            print(f"\n   {i}. Package: {vc.package_name}")
            print(f"      Conflicting versions: {', '.join(vc.versions)}")
            print(f"      Severity: {vc.severity}")
            print(f"      Affected paths:")
            for path in vc.paths[:3]:  # Show first 3 paths
                path_str = " → ".join(path)
                print(f"         - {path_str}")
    else:
        print("\n✅ No version conflicts detected")


def example_graph_visualization():
    """Example: Visualize dependency graph."""
    print("\n" + "=" * 80)
    print("Example 6: Dependency Graph Visualization")
    print("=" * 80)
    
    # Create analyzer
    analyzer = DependencyGraphAnalyzer()
    
    # Build a sample graph
    from tools.dependency_graph import DependencyNode
    
    lodash = DependencyNode("lodash", "4.17.21", "npm", depth=3)
    
    body_parser = DependencyNode("body-parser", "1.20.1", "npm", depth=2)
    body_parser.dependencies["lodash"] = lodash
    
    express = DependencyNode("express", "4.18.2", "npm", depth=1)
    express.dependencies["body-parser"] = body_parser
    
    axios = DependencyNode("axios", "1.3.0", "npm", depth=1)
    
    root = DependencyNode("my-web-app", "1.0.0", "npm", depth=0)
    root.dependencies["express"] = express
    root.dependencies["axios"] = axios
    
    analyzer.graph = root
    
    print("\n📊 Generating Mermaid diagram...")
    diagram = analyzer.visualize_graph(max_depth=3)
    
    print("\n" + "=" * 80)
    print("Mermaid Diagram (copy to https://mermaid.live for visualization):")
    print("=" * 80)
    print(diagram)
    print("=" * 80)


def example_complete_workflow():
    """Example: Complete workflow with all features."""
    print("\n" + "=" * 80)
    print("Example 7: Complete Dependency Analysis Workflow")
    print("=" * 80)
    
    # Create a realistic project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "production-app",
            "version": "2.1.0",
            "dependencies": {
                "express": "^4.18.2",
                "lodash": "^4.17.20",  # Vulnerable version
                "axios": "^1.3.0",
                "body-parser": "^1.20.1"
            }
        }))
        
        print(f"\n📦 Analyzing project: production-app")
        print(f"   Manifest: {package_json}")
        
        # Step 1: Build graph
        print("\n[1/5] Building dependency graph...")
        analyzer = DependencyGraphAnalyzer()
        graph = analyzer.build_graph(str(package_json), "npm", max_depth=3)
        print(f"      ✓ Found {graph['metadata']['total_packages']} packages")
        
        # Step 2: Check for circular dependencies
        print("\n[2/5] Checking for circular dependencies...")
        if graph['metadata']['circular_dependencies_count'] > 0:
            print(f"      ⚠️  Found {graph['metadata']['circular_dependencies_count']} circular dependencies")
            for cd in graph['circular_dependencies'][:2]:
                print(f"         - {cd['description']}")
        else:
            print("      ✓ No circular dependencies")
        
        # Step 3: Check for version conflicts
        print("\n[3/5] Checking for version conflicts...")
        if graph['metadata']['version_conflicts_count'] > 0:
            print(f"      ⚠️  Found {graph['metadata']['version_conflicts_count']} version conflicts")
            for vc in graph['version_conflicts'][:2]:
                print(f"         - {vc['description']}")
        else:
            print("      ✓ No version conflicts")
        
        # Step 4: Trace vulnerability (simulate lodash vulnerability)
        print("\n[4/5] Tracing vulnerability impact...")
        paths = analyzer.trace_vulnerability_impact("lodash")
        if paths:
            print(f"      ⚠️  Vulnerable package 'lodash' found in {len(paths)} path(s):")
            for path in paths[:3]:
                path_str = " → ".join(path)
                print(f"         - {path_str}")
        else:
            print("      ✓ No vulnerable packages in dependency chain")
        
        # Step 5: Generate visualization
        print("\n[5/5] Generating dependency visualization...")
        diagram = analyzer.visualize_graph(max_depth=2)
        print(f"      ✓ Generated Mermaid diagram ({len(diagram)} characters)")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 Analysis Summary")
        print("=" * 80)
        print(f"Total packages analyzed: {graph['metadata']['total_packages']}")
        print(f"Circular dependencies: {graph['metadata']['circular_dependencies_count']}")
        print(f"Version conflicts: {graph['metadata']['version_conflicts_count']}")
        print(f"Vulnerable dependency paths: {len(paths)}")
        print("\n✅ Analysis complete!")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("🔍 Dependency Graph Analyzer - Example Usage")
    print("=" * 80)
    
    try:
        # Run examples
        example_npm_analysis()
        example_python_analysis()
        example_vulnerability_tracing()
        example_circular_dependency_detection()
        example_version_conflict_detection()
        example_graph_visualization()
        example_complete_workflow()
        
        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
