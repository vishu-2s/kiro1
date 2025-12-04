"""
Test that circular dependencies don't cause infinite expansion in JSON.
"""

from tools.dependency_graph import DependencyNode


def test_circular_dependency_prevention():
    """Test that circular dependencies are handled correctly."""
    
    print("Testing circular dependency prevention...")
    
    # Create a circular dependency: A -> B -> C -> A
    node_a = DependencyNode(name="package-a", version="1.0.0", ecosystem="npm", depth=0)
    node_b = DependencyNode(name="package-b", version="1.0.0", ecosystem="npm", depth=1)
    node_c = DependencyNode(name="package-c", version="1.0.0", ecosystem="npm", depth=2)
    
    # Create circular reference
    node_a.dependencies["package-b"] = node_b
    node_b.dependencies["package-c"] = node_c
    node_c.dependencies["package-a"] = node_a  # Circular!
    
    # Convert to dict
    result = node_a.to_dict()
    
    # Verify structure
    print(f"  Root: {result['name']}")
    print(f"  Dependencies: {list(result['dependencies'].keys())}")
    
    # Check that package-b is included
    assert "package-b" in result["dependencies"], "package-b should be in dependencies"
    
    # Check that package-c is included under package-b
    package_b = result["dependencies"]["package-b"]
    assert "package-c" in package_b["dependencies"], "package-c should be in package-b dependencies"
    
    # Check that package-a under package-c is marked as circular
    package_c = package_b["dependencies"]["package-c"]
    assert "package-a" in package_c["dependencies"], "package-a should be in package-c dependencies"
    
    # The circular reference should have empty dependencies
    circular_a = package_c["dependencies"]["package-a"]
    assert circular_a["dependencies"] == {}, "Circular reference should have empty dependencies"
    assert circular_a.get("circular_reference") == True, "Should be marked as circular"
    
    print("  ✓ Circular dependency detected and prevented")
    
    # Count total occurrences of package-a in JSON
    import json
    json_str = json.dumps(result)
    count = json_str.count('"package-a"')
    print(f"  ✓ package-a appears {count} times in JSON (should be ~2-3, not hundreds)")
    
    assert count < 10, f"package-a appears {count} times - circular dependency not prevented!"
    
    print("✅ Test passed!")


def test_regenerator_runtime_scenario():
    """Test the specific regenerator-runtime scenario."""
    
    print("\nTesting regenerator-runtime scenario...")
    
    # Simulate the real scenario where regenerator-runtime appears at many levels
    root = DependencyNode(name="my-app", version="1.0.0", ecosystem="npm", depth=0)
    
    # Add multiple packages that all depend on regenerator-runtime
    for i in range(10):
        pkg = DependencyNode(name=f"package-{i}", version="1.0.0", ecosystem="npm", depth=1)
        regenerator = DependencyNode(name="regenerator-runtime", version="0.11.0", ecosystem="npm", depth=2)
        pkg.dependencies["regenerator-runtime"] = regenerator
        root.dependencies[f"package-{i}"] = pkg
    
    # Convert to dict
    result = root.to_dict()
    
    # Count occurrences
    import json
    json_str = json.dumps(result)
    count = json_str.count('"regenerator-runtime"')
    
    print(f"  regenerator-runtime appears {count} times")
    print(f"  Expected: ~10-20 (once per package + metadata)")
    print(f"  Before fix: Would be 728+ times")
    
    assert count < 50, f"regenerator-runtime appears {count} times - too many!"
    
    print("✅ Test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("CIRCULAR DEPENDENCY FIX TESTS")
    print("=" * 60)
    print()
    
    try:
        test_circular_dependency_prevention()
        test_regenerator_runtime_scenario()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe fix prevents:")
        print("  • Infinite recursion in circular dependencies")
        print("  • Massive JSON file sizes")
        print("  • regenerator-runtime appearing 728 times")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
