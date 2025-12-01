#!/usr/bin/env python3
"""
Setup script for Multi-Agent Security Analysis System virtual environment.
This script creates a virtual environment and installs all required dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        return None

def main():
    """Main setup function."""
    print("Multi-Agent Security Analysis System - Environment Setup")
    print("=" * 60)
    
    # Check if Python is available
    python_cmd = "python" if sys.platform == "win32" else "python3"
    
    # Create virtual environment
    venv_path = Path("venv")
    if not venv_path.exists():
        result = run_command(f"{python_cmd} -m venv venv", "Creating virtual environment")
        if not result:
            print("Failed to create virtual environment. Please ensure Python is installed.")
            return False
    else:
        print("✓ Virtual environment already exists")
    
    # Determine activation script path
    if sys.platform == "win32":
        activate_script = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_script = "venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    if Path("requirements.txt").exists():
        result = run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")
        if not result:
            print("Failed to install dependencies.")
            return False
    else:
        print("✗ requirements.txt not found")
        return False
    
    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("\nTo activate the virtual environment:")
    if sys.platform == "win32":
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    
    print("\nTo run the system:")
    print("  python main_github.py --help")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)