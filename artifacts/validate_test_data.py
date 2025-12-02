#!/usr/bin/env python3
"""
Validation script for test artifacts and sample data.

This script validates that all test data files are properly formatted
and contain the expected content for testing the Multi-Agent Security Analysis System.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

def validate_json_file(file_path: str, expected_keys: List[str] = None) -> bool:
    """Validate that a JSON file is properly formatted and contains expected keys."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if expected_keys:
            if isinstance(data, dict):
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    print(f"❌ {file_path}: Missing keys: {missing_keys}")
                    return False
            elif isinstance(data, list) and data:
                # Check first item for expected keys
                if isinstance(data[0], dict):
                    missing_keys = [key for key in expected_keys if key not in data[0]]
                    if missing_keys:
                        print(f"❌ {file_path}: Missing keys in first item: {missing_keys}")
                        return False
        
        print(f"✅ {file_path}: Valid JSON")
        return True
    
    except json.JSONDecodeError as e:
        print(f"❌ {file_path}: Invalid JSON - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {file_path}: File not found")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def validate_text_file(file_path: str, min_lines: int = 1) -> bool:
    """Validate that a text file exists and has minimum content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < min_lines:
            print(f"❌ {file_path}: Too few lines ({len(lines)} < {min_lines})")
            return False
        
        print(f"✅ {file_path}: Valid text file ({len(lines)} lines)")
        return True
    
    except FileNotFoundError:
        print(f"❌ {file_path}: File not found")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def validate_sbom_file(file_path: str) -> bool:
    """Validate SBOM file structure."""
    expected_keys = ["format", "components", "metadata"]
    if not validate_json_file(file_path, expected_keys):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sbom = json.load(f)
        
        components = sbom.get("components", [])
        if not components:
            print(f"❌ {file_path}: No components found")
            return False
        
        # Check for vulnerable packages
        vulnerable_packages = [
            "event-stream", "flatmap-stream", "python3-dateutil", "urllib4",
            "log4j-core", "spring-core", "rest-client", "rustdecimal", "beego"
        ]
        
        found_vulnerable = []
        for component in components:
            name = component.get("name", "")
            if any(vuln in name for vuln in vulnerable_packages):
                found_vulnerable.append(name)
        
        if not found_vulnerable:
            print(f"❌ {file_path}: No known vulnerable packages found")
            return False
        
        print(f"✅ {file_path}: Found {len(found_vulnerable)} vulnerable packages")
        return True
    
    except Exception as e:
        print(f"❌ {file_path}: SBOM validation error - {e}")
        return False

def validate_package_files() -> bool:
    """Validate package manager files."""
    results = []
    
    # Validate package.json
    package_json_path = "artifacts/sample-package.json"
    expected_keys = ["name", "version", "dependencies"]
    results.append(validate_json_file(package_json_path, expected_keys))
    
    # Validate requirements.txt
    requirements_path = "artifacts/sample-requirements.txt"
    results.append(validate_text_file(requirements_path, min_lines=10))
    
    # Validate pom.xml
    pom_path = "artifacts/sample-pom.xml"
    results.append(validate_text_file(pom_path, min_lines=20))
    
    return all(results)

def validate_security_data() -> bool:
    """Validate security-related data files."""
    results = []
    
    # Validate security alerts
    alerts_path = "artifacts/sample-security-alerts.json"
    expected_keys = ["alert_id", "state", "dependency", "security_advisory"]
    results.append(validate_json_file(alerts_path, expected_keys))
    
    # Validate Dependabot alerts
    dependabot_path = "artifacts/sample-dependabot-alerts.json"
    expected_keys = ["number", "state", "dependency", "security_advisory"]
    results.append(validate_json_file(dependabot_path, expected_keys))
    
    # Validate OSV response
    osv_path = "artifacts/sample-osv-response.json"
    expected_keys = ["vulns"]
    results.append(validate_json_file(osv_path, expected_keys))
    
    return all(results)

def validate_ci_cd_data() -> bool:
    """Validate CI/CD related data files."""
    results = []
    
    # Validate CI logs
    logs_path = "artifacts/sample-ci-logs.txt"
    results.append(validate_text_file(logs_path, min_lines=20))
    
    # Validate workflow runs
    workflow_path = "artifacts/sample-workflow-runs.json"
    expected_keys = ["id", "name", "status", "conclusion"]
    results.append(validate_json_file(workflow_path, expected_keys))
    
    # Validate repository data
    repo_path = "artifacts/sample-repository-data.json"
    expected_keys = ["id", "name", "full_name", "package_files"]
    results.append(validate_json_file(repo_path, expected_keys))
    
    return all(results)

def validate_visual_data() -> bool:
    """Validate visual test data files."""
    results = []
    
    # Check screenshot text files
    screenshot_files = [
        "screenshots/security-warning-text.txt",
        "screenshots/npm-warnings-text.txt", 
        "screenshots/github-alert-text.txt",
        "screenshots/phishing-page-text.txt",
        "screenshots/malware-download-text.txt"
    ]
    
    for file_path in screenshot_files:
        results.append(validate_text_file(file_path, min_lines=3))
    
    # Check screenshot descriptions
    desc_path = "artifacts/screenshot-descriptions.md"
    results.append(validate_text_file(desc_path, min_lines=50))
    
    return all(results)

def main():
    """Main validation function."""
    print("🔍 Validating Multi-Agent Security Analysis Test Data")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    validation_results = []
    
    print("\n📋 Validating SBOM Files...")
    validation_results.append(validate_sbom_file("artifacts/backend-sbom.json"))
    
    print("\n📦 Validating Package Files...")
    validation_results.append(validate_package_files())
    
    print("\n🔒 Validating Security Data...")
    validation_results.append(validate_security_data())
    
    print("\n🔄 Validating CI/CD Data...")
    validation_results.append(validate_ci_cd_data())
    
    print("\n👁️ Validating Visual Data...")
    validation_results.append(validate_visual_data())
    
    print("\n" + "=" * 60)
    
    if all(validation_results):
        print("✅ All test data validation passed!")
        return 0
    else:
        print("❌ Some test data validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())