"""
Local directory analysis tools for Multi-Agent Security Analysis System.

This module provides functions for:
- Directory scanning and package file detection
- Support for multiple package file formats across ecosystems
- Local SBOM generation from discovered package files
- File system error handling and path validation
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from constants import ECOSYSTEM_FILES, get_ecosystem_from_file
from tools.sbom_tools import (
    SBOMPackage,
    SecurityFinding,
    detect_ecosystem,
    extract_packages_from_file,
    generate_sbom_from_packages,
    validate_sbom_structure,
    check_vulnerable_packages,
    _analyze_npm_scripts
)
from tools.dependency_analyzer import analyze_dependency_tree
from config import config

logger = logging.getLogger(__name__)

class LocalAnalysisError(Exception):
    """Custom exception for local analysis errors."""
    pass

class PathValidationError(LocalAnalysisError):
    """Exception raised for invalid or inaccessible paths."""
    pass

def validate_path(path: str) -> Path:
    """
    Validate and normalize a file system path.
    
    Args:
        path: Path to validate
    
    Returns:
        Validated Path object
    
    Raises:
        PathValidationError: If path is invalid or inaccessible
    """
    try:
        # Convert to Path object and resolve
        path_obj = Path(path).resolve()
        
        # Check if path exists
        if not path_obj.exists():
            raise PathValidationError(f"Path does not exist: {path}")
        
        # Check if it's a directory
        if not path_obj.is_dir():
            raise PathValidationError(f"Path is not a directory: {path}")
        
        # Check if we have read permissions
        if not os.access(path_obj, os.R_OK):
            raise PathValidationError(f"No read permission for path: {path}")
        
        return path_obj
    
    except OSError as e:
        raise PathValidationError(f"Invalid path {path}: {e}")

def scan_directory_for_package_files(directory_path: str, max_depth: int = 5) -> List[Dict[str, Any]]:
    """
    Scan directory recursively for package files across multiple ecosystems.
    
    Args:
        directory_path: Path to directory to scan
        max_depth: Maximum recursion depth to prevent infinite loops
    
    Returns:
        List of discovered package files with metadata
    
    Raises:
        PathValidationError: If directory path is invalid
        LocalAnalysisError: For other scanning errors
    """
    validated_path = validate_path(directory_path)
    
    logger.info(f"Scanning directory {validated_path} for package files (max depth: {max_depth})")
    
    package_files = []
    
    # Define package file patterns for each ecosystem
    package_file_patterns = {
        "npm": ["package.json", "package-lock.json", "yarn.lock", "npm-shrinkwrap.json"],
        "pypi": ["requirements.txt", "setup.py", "pyproject.toml", "pipfile", "pipfile.lock"],
        "maven": ["pom.xml", "build.gradle", "gradle.properties"],
        "rubygems": ["gemfile", "gemfile.lock"],
        "crates": ["cargo.toml", "cargo.lock"],
        "go": ["go.mod", "go.sum"]
    }
    
    # Flatten all patterns for easier matching
    all_patterns = []
    for ecosystem, patterns in package_file_patterns.items():
        all_patterns.extend(patterns)
    
    try:
        # Walk directory tree
        for root, dirs, files in os.walk(validated_path):
            current_path = Path(root)
            
            # Calculate current depth
            try:
                depth = len(current_path.relative_to(validated_path).parts)
            except ValueError:
                depth = 0
            
            # Skip if we've exceeded max depth
            if depth > max_depth:
                dirs.clear()  # Don't recurse further
                continue
            
            # Skip common directories that shouldn't contain package files
            dirs[:] = [d for d in dirs if not _should_skip_directory(d)]
            
            # Check each file in current directory
            for file in files:
                file_lower = file.lower()
                
                # Check if file matches any package file pattern
                for pattern in all_patterns:
                    if pattern.lower() == file_lower or file_lower.endswith(pattern.lower()):
                        file_path = current_path / file
                        
                        try:
                            # Get file metadata
                            stat = file_path.stat()
                            ecosystem = detect_ecosystem(str(file_path))
                            
                            # Read file content for ecosystem detection and validation
                            content = None
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except (UnicodeDecodeError, PermissionError) as e:
                                logger.warning(f"Could not read file {file_path}: {e}")
                                content = None
                            
                            package_file_info = {
                                "path": str(file_path),
                                "relative_path": str(file_path.relative_to(validated_path)),
                                "name": file,
                                "ecosystem": ecosystem,
                                "size": stat.st_size,
                                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "content": content,
                                "depth": depth
                            }
                            
                            package_files.append(package_file_info)
                            logger.debug(f"Found {ecosystem} package file: {file_path}")
                        
                        except (OSError, PermissionError) as e:
                            logger.warning(f"Error accessing file {file_path}: {e}")
                            continue
                        
                        break  # Found a match, no need to check other patterns
                
                # Also check for .gemspec files (Ruby)
                if file_lower.endswith('.gemspec'):
                    file_path = current_path / file
                    try:
                        stat = file_path.stat()
                        
                        package_file_info = {
                            "path": str(file_path),
                            "relative_path": str(file_path.relative_to(validated_path)),
                            "name": file,
                            "ecosystem": "rubygems",
                            "size": stat.st_size,
                            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "content": None,  # Don't read .gemspec content by default
                            "depth": depth
                        }
                        
                        package_files.append(package_file_info)
                        logger.debug(f"Found Ruby gemspec file: {file_path}")
                    
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Error accessing gemspec file {file_path}: {e}")
    
    except OSError as e:
        raise LocalAnalysisError(f"Error scanning directory {validated_path}: {e}")
    
    logger.info(f"Found {len(package_files)} package files in {validated_path}")
    return package_files

def _should_skip_directory(dir_name: str) -> bool:
    """
    Determine if a directory should be skipped during scanning.
    
    Args:
        dir_name: Directory name to check
    
    Returns:
        True if directory should be skipped
    """
    skip_patterns = [
        # Version control
        '.git', '.svn', '.hg', '.bzr',
        # Build/output directories
        'node_modules', 'dist', 'build', 'target', 'out', 'bin', 'obj',
        # Cache directories
        '.cache', '__pycache__', '.pytest_cache', '.mypy_cache',
        # IDE/Editor directories
        '.vscode', '.idea', '.vs', '.atom', '.sublime-text',
        # OS directories
        '.DS_Store', 'Thumbs.db',
        # Virtual environments
        'venv', 'env', '.env', 'virtualenv', '.virtualenv',
        # Temporary directories
        'tmp', 'temp', '.tmp', '.temp',
        # Log directories
        'logs', 'log', '.log',
        # Coverage/test output
        'coverage', '.coverage', '.nyc_output',
        # Documentation build
        '_build', 'site', '.docusaurus'
    ]
    
    dir_lower = dir_name.lower()
    return any(pattern.lower() in dir_lower for pattern in skip_patterns)

def generate_local_sbom(directory_path: str, include_dev_dependencies: bool = True) -> Dict[str, Any]:
    """
    Generate SBOM from local directory by scanning for package files.
    
    Args:
        directory_path: Path to directory to analyze
        include_dev_dependencies: Whether to include development dependencies
    
    Returns:
        Generated SBOM dictionary
    
    Raises:
        PathValidationError: If directory path is invalid
        LocalAnalysisError: For SBOM generation errors
    """
    validated_path = validate_path(directory_path)
    
    logger.info(f"Generating SBOM for local directory: {validated_path}")
    
    # Scan for package files
    package_files = scan_directory_for_package_files(str(validated_path))
    
    if not package_files:
        logger.warning(f"No package files found in {validated_path}")
        return generate_sbom_from_packages([], {
            "type": "local_directory",
            "path": str(validated_path),
            "scanned_at": datetime.now().isoformat(),
            "package_files_found": 0
        })
    
    all_packages = []
    all_script_findings = []
    processing_errors = []
    
    # Process each package file
    for file_info in package_files:
        try:
            file_path = file_info["path"]
            ecosystem = file_info["ecosystem"]
            
            if ecosystem == "unknown":
                logger.warning(f"Unknown ecosystem for file: {file_path}")
                continue
            
            # Extract packages and script findings from file
            packages, script_findings = extract_packages_from_file(file_path)
            
            # Collect script findings
            all_script_findings.extend(script_findings)
            
            # Filter development dependencies if requested
            if not include_dev_dependencies:
                packages = [pkg for pkg in packages 
                           if pkg.metadata.get("dependency_type") != "devDependencies"]
            
            # Add metadata about source file
            for package in packages:
                package.metadata.update({
                    "source_file": file_info["relative_path"],
                    "source_directory": str(validated_path),
                    "file_size": file_info["size"],
                    "file_modified": file_info["modified_time"],
                    "scan_depth": file_info["depth"]
                })
            
            all_packages.extend([pkg.to_dict() for pkg in packages])
            logger.debug(f"Extracted {len(packages)} packages and {len(script_findings)} script findings from {file_path}")
        
        except Exception as e:
            error_msg = f"Failed to process {file_info['path']}: {e}"
            logger.error(error_msg)
            processing_errors.append(error_msg)
    
    # Generate SBOM
    source_info = {
        "type": "local_directory",
        "path": str(validated_path),
        "scanned_at": datetime.now().isoformat(),
        "package_files_found": len(package_files),
        "packages_extracted": len(all_packages),
        "script_findings_detected": len(all_script_findings),
        "include_dev_dependencies": include_dev_dependencies,
        "processing_errors": processing_errors
    }
    
    sbom = generate_sbom_from_packages(all_packages, source_info)
    
    # Add script findings to SBOM
    sbom["script_findings"] = [finding.to_dict() for finding in all_script_findings]
    
    # Validate SBOM structure
    is_valid, errors = validate_sbom_structure(sbom)
    if not is_valid:
        logger.warning(f"Generated SBOM has validation errors: {errors}")
        sbom["validation_errors"] = errors
    
    logger.info(f"Generated SBOM with {len(all_packages)} packages and {len(all_script_findings)} script findings from {len(package_files)} files")
    return sbom

def analyze_local_directory(directory_path: str, output_dir: Optional[str] = None, 
                          use_osv: bool = True) -> Dict[str, Any]:
    """
    Perform comprehensive security analysis of a local directory.
    
    Args:
        directory_path: Path to directory to analyze
        output_dir: Optional output directory for results
        use_osv: Whether to query OSV API for vulnerabilities
    
    Returns:
        Analysis results dictionary
    
    Raises:
        PathValidationError: If directory path is invalid
        LocalAnalysisError: For analysis errors
    """
    validated_path = validate_path(directory_path)
    
    logger.info(f"Starting comprehensive analysis of {validated_path}")
    
    analysis_start_time = datetime.now()
    
    try:
        # Generate SBOM
        sbom_data = generate_local_sbom(str(validated_path))
        
        # Analyze root package.json scripts (npm)
        root_package_json = validated_path / "package.json"
        if root_package_json.exists():
            try:
                with open(root_package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                package_name = package_data.get('name', 'root-package')
                
                if scripts:
                    root_script_findings = _analyze_npm_scripts(scripts, package_name)
                    if root_script_findings:
                        logger.warning(f"Found {len(root_script_findings)} malicious scripts in root package.json")
                        # Add to sbom_data script_findings
                        if "script_findings" not in sbom_data:
                            sbom_data["script_findings"] = []
                        sbom_data["script_findings"].extend([f.to_dict() for f in root_script_findings])
            except Exception as e:
                logger.error(f"Error analyzing root package.json scripts: {e}")
        
        # Analyze dependency tree for deep script analysis (npm)
        dependency_analysis = analyze_dependency_tree(str(validated_path))
        logger.info(f"Dependency tree analysis: {dependency_analysis.get('total_dependencies', 0)} total dependencies, "
                   f"{len(dependency_analysis.get('packages_with_scripts', []))} with scripts")
        
        # Check for vulnerabilities
        security_findings = []
        if sbom_data.get("packages"):
            security_findings = check_vulnerable_packages(sbom_data, use_osv=use_osv)
        
        # Analyze scripts in all npm dependencies
        for pkg_info in dependency_analysis.get('packages_with_scripts', []):
            if pkg_info.get('scripts'):
                dep_findings = _analyze_npm_scripts(
                    pkg_info['scripts'],
                    f"{pkg_info['name']}@{pkg_info['version']} (depth: {pkg_info['depth']})"
                )
                security_findings.extend(dep_findings)
                if dep_findings:
                    logger.warning(f"Found {len(dep_findings)} malicious scripts in dependency {pkg_info['name']}")
        
        # Analyze Python dependencies if Python files are present
        try:
            from tools.ecosystem_analyzer import get_analyzer_registry
            registry = get_analyzer_registry()
            python_analyzer = registry.get_analyzer("pypi")
            
            if python_analyzer:
                # Check if this is a Python project
                python_manifests = python_analyzer.detect_manifest_files(str(validated_path))
                
                if python_manifests:
                    logger.info(f"Detected Python project with {len(python_manifests)} manifest files")
                    
                    # Analyze Python dependencies for malicious packages
                    python_findings = python_analyzer.analyze_dependencies_with_malicious_check(str(validated_path))
                    security_findings.extend(python_findings)
                    
                    if python_findings:
                        logger.warning(f"Found {len(python_findings)} malicious Python packages")
                    
                    # Analyze Python installation scripts (setup.py)
                    install_script_findings = python_analyzer.analyze_install_scripts(str(validated_path))
                    security_findings.extend(install_script_findings)
                    
                    if install_script_findings:
                        logger.warning(f"Found {len(install_script_findings)} suspicious patterns in Python installation scripts")
        
        except Exception as e:
            logger.error(f"Error during Python dependency analysis: {e}")
        
        # Add script findings from SBOM
        script_findings_data = sbom_data.get("script_findings", [])
        for finding_dict in script_findings_data:
            # Convert dict back to SecurityFinding object
            finding = SecurityFinding(
                package=finding_dict.get("package", "unknown"),
                version=finding_dict.get("version", "*"),
                finding_type=finding_dict.get("finding_type", "malicious_script"),
                severity=finding_dict.get("severity", "medium"),
                confidence=finding_dict.get("confidence", 0.5),
                evidence=finding_dict.get("evidence", []),
                recommendations=finding_dict.get("recommendations", []),
                source=finding_dict.get("source", "npm_script_analysis")
            )
            security_findings.append(finding)
        
        # Compile analysis results
        analysis_results = {
            "analysis_type": "local_directory",
            "target_path": str(validated_path),
            "analysis_start_time": analysis_start_time.isoformat(),
            "analysis_end_time": datetime.now().isoformat(),
            "sbom": sbom_data,
            "security_findings": [finding.to_dict() for finding in security_findings],
            "summary": {
                "total_packages": len(sbom_data.get("packages", [])),
                "total_findings": len(security_findings),
                "critical_findings": len([f for f in security_findings if f.severity == "critical"]),
                "high_findings": len([f for f in security_findings if f.severity == "high"]),
                "medium_findings": len([f for f in security_findings if f.severity == "medium"]),
                "low_findings": len([f for f in security_findings if f.severity == "low"]),
                "script_findings": len(script_findings_data),
                "ecosystems_found": list(set(pkg.get("ecosystem", "unknown") 
                                           for pkg in sbom_data.get("packages", []))),
                "package_files_scanned": sbom_data.get("source", {}).get("package_files_found", 0)
            }
        }
        
        # Save results if output directory specified
        if output_dir:
            output_path = save_local_analysis_results(analysis_results, output_dir)
            analysis_results["output_file"] = output_path
        
        logger.info(f"Analysis complete: {len(security_findings)} findings from {len(sbom_data.get('packages', []))} packages")
        return analysis_results
    
    except Exception as e:
        logger.error(f"Analysis failed for {validated_path}: {e}")
        raise LocalAnalysisError(f"Failed to analyze directory {validated_path}: {e}")

def save_local_analysis_results(analysis_results: Dict[str, Any], 
                               output_dir: str) -> str:
    """
    Save local analysis results to JSON file.
    
    Args:
        analysis_results: Analysis results to save
        output_dir: Output directory
    
    Returns:
        Path to saved file
    
    Raises:
        LocalAnalysisError: If saving fails
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename based on target path and timestamp
        target_path = Path(analysis_results["target_path"])
        safe_name = target_path.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        
        # Remove any control characters and other invalid filename characters
        import re
        safe_name = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', '_', safe_name)
        
        # Ensure the name is not empty and not too long
        if not safe_name or safe_name.isspace():
            safe_name = "unknown_path"
        safe_name = safe_name[:50]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"local_analysis_{safe_name}_{timestamp}.json"
        
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {file_path}")
        return str(file_path)
    
    except Exception as e:
        raise LocalAnalysisError(f"Failed to save analysis results: {e}")

def get_directory_statistics(directory_path: str) -> Dict[str, Any]:
    """
    Get basic statistics about a directory.
    
    Args:
        directory_path: Path to directory
    
    Returns:
        Directory statistics dictionary
    
    Raises:
        PathValidationError: If directory path is invalid
    """
    validated_path = validate_path(directory_path)
    
    try:
        total_files = 0
        total_size = 0
        file_types = {}
        
        for root, dirs, files in os.walk(validated_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not _should_skip_directory(d)]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    total_files += 1
                    total_size += stat.st_size
                    
                    # Count file extensions
                    ext = file_path.suffix.lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                    else:
                        file_types["no_extension"] = file_types.get("no_extension", 0) + 1
                
                except (OSError, PermissionError):
                    continue
        
        return {
            "path": str(validated_path),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "analyzed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise LocalAnalysisError(f"Failed to get directory statistics: {e}")

def find_package_files_by_ecosystem(directory_path: str, 
                                   ecosystem: str) -> List[Dict[str, Any]]:
    """
    Find package files for a specific ecosystem in directory.
    
    Args:
        directory_path: Path to directory to search
        ecosystem: Ecosystem to search for (npm, pypi, maven, etc.)
    
    Returns:
        List of package files for the specified ecosystem
    
    Raises:
        PathValidationError: If directory path is invalid
        ValueError: If ecosystem is not supported
    """
    if ecosystem not in ECOSYSTEM_FILES:
        raise ValueError(f"Unsupported ecosystem: {ecosystem}")
    
    validated_path = validate_path(directory_path)
    
    # Get all package files
    all_package_files = scan_directory_for_package_files(str(validated_path))
    
    # Filter by ecosystem
    ecosystem_files = [f for f in all_package_files if f["ecosystem"] == ecosystem]
    
    logger.info(f"Found {len(ecosystem_files)} {ecosystem} package files in {validated_path}")
    return ecosystem_files

def detect_project_type(directory_path: str) -> Dict[str, Any]:
    """
    Detect the primary project type(s) based on package files found.
    
    Args:
        directory_path: Path to directory to analyze
    
    Returns:
        Project type detection results
    
    Raises:
        PathValidationError: If directory path is invalid
    """
    validated_path = validate_path(directory_path)
    
    # Scan for package files
    package_files = scan_directory_for_package_files(str(validated_path))
    
    # Count ecosystems
    ecosystem_counts = {}
    for file_info in package_files:
        ecosystem = file_info["ecosystem"]
        if ecosystem != "unknown":
            ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1
    
    # Determine primary ecosystem(s)
    if not ecosystem_counts:
        primary_ecosystem = "unknown"
        confidence = 0.0
    else:
        max_count = max(ecosystem_counts.values())
        primary_ecosystems = [eco for eco, count in ecosystem_counts.items() if count == max_count]
        primary_ecosystem = primary_ecosystems[0] if len(primary_ecosystems) == 1 else "mixed"
        confidence = max_count / len(package_files) if package_files else 0.0
    
    return {
        "path": str(validated_path),
        "primary_ecosystem": primary_ecosystem,
        "confidence": confidence,
        "ecosystem_counts": ecosystem_counts,
        "total_package_files": len(package_files),
        "detected_at": datetime.now().isoformat()
    }