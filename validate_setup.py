#!/usr/bin/env python3
"""
Validation script for Multi-Agent Security Analysis System setup.
Tests that all core components are properly configured and accessible.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import openai
        print("✓ OpenAI library imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import OpenAI: {e}")
        return False
    
    try:
        import requests
        print("✓ Requests library imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic library imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pydantic: {e}")
        return False
    
    try:
        import hypothesis
        print("✓ Hypothesis library imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import hypothesis: {e}")
        return False
    
    try:
        from config import config
        print("✓ Configuration module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    return True

def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = ["agents", "tools", "artifacts", "screenshots", "outputs"]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✓ Directory '{dir_name}' exists")
        else:
            print(f"✗ Directory '{dir_name}' missing")
            return False
    
    return True

def test_configuration():
    """Test configuration loading and validation."""
    print("\nTesting configuration...")
    
    try:
        from config import config
        
        # Test basic configuration values
        print(f"✓ Output directory: {config.OUTPUT_DIRECTORY}")
        print(f"✓ Cache enabled: {config.CACHE_ENABLED}")
        print(f"✓ Agent temperature: {config.AGENT_TEMPERATURE}")
        print(f"✓ Max tokens: {config.AGENT_MAX_TOKENS}")
        
        # Test that output directory is created
        output_path = Path(config.OUTPUT_DIRECTORY)
        if output_path.exists():
            print(f"✓ Output directory '{config.OUTPUT_DIRECTORY}' exists")
        else:
            print(f"✗ Output directory '{config.OUTPUT_DIRECTORY}' not found")
            return False
        
        # Check if OpenAI API key is set (warn if not)
        if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here":
            print("✓ OpenAI API key is configured")
        else:
            print("⚠ OpenAI API key not configured (update .env file)")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_package_structure():
    """Test that package structure is correct."""
    print("\nTesting package structure...")
    
    # Test agents package
    agents_init = Path("agents/__init__.py")
    if agents_init.exists():
        print("✓ Agents package initialized")
    else:
        print("✗ Agents package missing __init__.py")
        return False
    
    # Test tools package
    tools_init = Path("tools/__init__.py")
    if tools_init.exists():
        print("✓ Tools package initialized")
    else:
        print("✗ Tools package missing __init__.py")
        return False
    
    return True

def main():
    """Run all validation tests."""
    print("Multi-Agent Security Analysis System - Setup Validation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_directory_structure,
        test_configuration,
        test_package_structure
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✓ All validation tests passed!")
        print("\nSetup is complete. You can now proceed with implementing the remaining tasks.")
        print("\nNext steps:")
        print("1. Update .env file with your OpenAI API key")
        print("2. Optionally add GitHub token for repository analysis")
        print("3. Start implementing the security signature database (Task 2)")
        return True
    else:
        print("✗ Some validation tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)