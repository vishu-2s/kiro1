#!/usr/bin/env python3
"""
Spyder - Main Orchestration System
AI-Powered Supply Chain Security Scanner

This module provides the command-line interface, configuration management,
analysis workflow coordination, and error handling for the security analysis system.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from config import config, Config
from analyze_supply_chain import (
    create_analyzer, 
    analyze_target, 
    analyze_target_with_screenshots,
    AnalysisError
)
from report_generator import create_security_report
from update_constants import MaliciousPackageUpdater

# Configure logging
def setup_logging(log_level: str = None, log_file: str = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    level = getattr(logging, (log_level or config.LOG_LEVEL).upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Spyder - AI-Powered Supply Chain Security Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze GitHub repository
  python main_github.py --github https://github.com/user/repo
  
  # Analyze local directory
  python main_github.py --local /path/to/project
  
  # Analyze SBOM file
  python main_github.py --sbom /path/to/sbom.json
  
  # Analyze with screenshots
  python main_github.py --github https://github.com/user/repo --screenshots screenshot1.png screenshot2.png
  
  # Skip database update and disable OSV queries
  python main_github.py --local /path/to/project --skip-db-update --no-osv
        """
    )
    
    # Analysis target options (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=False)
    target_group.add_argument(
        "--github", "-g",
        type=str,
        help="GitHub repository URL to analyze"
    )
    target_group.add_argument(
        "--local", "-l",
        type=str,
        help="Local directory path to analyze"
    )
    target_group.add_argument(
        "--sbom", "-s",
        type=str,
        help="SBOM file path to analyze"
    )
    
    # Visual analysis options
    parser.add_argument(
        "--screenshots",
        nargs="+",
        help="Screenshot file paths for visual security analysis"
    )
    
    # Configuration options
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=config.OUTPUT_DIRECTORY,
        help=f"Output directory for results (default: {config.OUTPUT_DIRECTORY})"
    )
    
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=config.CONFIDENCE_THRESHOLD,
        help=f"Minimum confidence threshold for findings (default: {config.CONFIDENCE_THRESHOLD})"
    )
    
    # Database and API options
    parser.add_argument(
        "--skip-db-update",
        action="store_true",
        help="Skip malicious package database update"
    )
    
    parser.add_argument(
        "--force-db-update",
        action="store_true",
        help="Force malicious package database update"
    )
    
    parser.add_argument(
        "--no-osv",
        action="store_true",
        help="Disable OSV API queries for vulnerability information"
    )
    
    parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Disable visual security analysis even if screenshots provided"
    )
    
    # Output format options
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Generate only JSON output (skip HTML report)"
    )
    
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Generate only HTML report (skip JSON output)"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=config.LOG_LEVEL,
        help=f"Logging level (default: {config.LOG_LEVEL})"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (default: console only)"
    )
    
    # Utility options
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Spyder v1.0.0 - AI-Powered Supply Chain Security Scanner"
    )
    
    return parser

def validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        True if arguments are valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check if any target is specified
    if not any([args.github, args.local, args.sbom]):
        logger.error("One of --github, --local, or --sbom must be specified")
        return False
    
    # Validate target paths/URLs
    if args.local:
        if not os.path.exists(args.local):
            logger.error(f"Local directory does not exist: {args.local}")
            return False
        if not os.path.isdir(args.local):
            logger.error(f"Local path is not a directory: {args.local}")
            return False
    
    if args.sbom:
        if not os.path.exists(args.sbom):
            logger.error(f"SBOM file does not exist: {args.sbom}")
            return False
        if not os.path.isfile(args.sbom):
            logger.error(f"SBOM path is not a file: {args.sbom}")
            return False
    
    # Validate screenshot paths
    if args.screenshots:
        for screenshot_path in args.screenshots:
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot file does not exist: {screenshot_path}")
                return False
            if not os.path.isfile(screenshot_path):
                logger.error(f"Screenshot path is not a file: {screenshot_path}")
                return False
    
    # Validate confidence threshold
    if not 0.0 <= args.confidence_threshold <= 1.0:
        logger.error(f"Confidence threshold must be between 0.0 and 1.0: {args.confidence_threshold}")
        return False
    
    # Validate mutually exclusive options
    if args.json_only and args.html_only:
        logger.error("Cannot specify both --json-only and --html-only")
        return False
    
    if args.skip_db_update and args.force_db_update:
        logger.error("Cannot specify both --skip-db-update and --force-db-update")
        return False
    
    return True

def setup_output_directory(output_dir: str) -> Path:
    """
    Set up and validate output directory.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        Path object for output directory
        
    Raises:
        OSError: If directory cannot be created
    """
    output_path = Path(output_dir)
    
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = output_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        
        return output_path
        
    except Exception as e:
        raise OSError(f"Cannot create or write to output directory {output_dir}: {e}")

def update_database_if_needed(skip_update: bool, force_update: bool) -> bool:
    """
    Update malicious package database if needed.
    
    Args:
        skip_update: Whether to skip the update
        force_update: Whether to force the update
        
    Returns:
        True if update was successful or skipped, False if failed
    """
    logger = logging.getLogger(__name__)
    
    if skip_update:
        logger.info("Skipping malicious package database update")
        return True
    
    try:
        logger.info("Checking malicious package database...")
        updater = MaliciousPackageUpdater()
        success = updater.update_database(force_update=force_update)
        
        if success:
            logger.info("Malicious package database is up to date")
        else:
            logger.warning("Failed to update malicious package database, continuing with existing data")
        
        return success
        
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        return False

def perform_analysis(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """
    Perform the security analysis based on arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Analysis results dictionary or None if failed
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Determine target and analysis type
        if args.github:
            target = args.github
            analysis_type = "github"
        elif args.local:
            target = args.local
            analysis_type = "local"
        elif args.sbom:
            target = args.sbom
            analysis_type = "sbom"
        else:
            raise ValueError("No valid analysis target specified")
        
        logger.info(f"Starting {analysis_type} analysis of: {target}")
        
        # Configure analysis options
        analyzer_kwargs = {
            "confidence_threshold": args.confidence_threshold,
            "enable_osv": not args.no_osv
        }
        
        # Perform analysis with or without screenshots
        if args.screenshots and not args.no_visual:
            logger.info(f"Including visual analysis of {len(args.screenshots)} screenshots")
            result = analyze_target_with_screenshots(
                target, 
                args.screenshots, 
                analysis_type, 
                **analyzer_kwargs
            )
        else:
            result = analyze_target(target, analysis_type, **analyzer_kwargs)
        
        logger.info(f"Analysis completed successfully")
        logger.info(f"Found {result.summary.total_findings} security findings")
        logger.info(f"Critical: {result.summary.critical_findings}, "
                   f"High: {result.summary.high_findings}, "
                   f"Medium: {result.summary.medium_findings}, "
                   f"Low: {result.summary.low_findings}")
        
        return result
        
    except AnalysisError as e:
        logger.error(f"Analysis failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        return None

def save_results(result: Dict[str, Any], output_dir: Path, 
                json_only: bool = False, html_only: bool = False) -> Dict[str, str]:
    """
    Save analysis results in requested formats.
    
    Args:
        result: Analysis results
        output_dir: Output directory
        json_only: Save only JSON format
        html_only: Save only HTML format
        
    Returns:
        Dictionary with saved file paths
    """
    logger = logging.getLogger(__name__)
    saved_files = {}
    
    # Generate base filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_id = result.metadata.analysis_id
    base_filename = f"security_analysis_{analysis_id}_{timestamp}"
    
    try:
        # Save JSON results
        if not html_only:
            json_path = output_dir / f"{base_filename}.json"
            
            # Convert result to dictionary if needed
            if hasattr(result, '__dict__'):
                result_dict = result.__dict__
                # Convert nested objects to dicts
                def convert_to_dict(obj):
                    if hasattr(obj, '__dict__'):
                        return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
                    elif isinstance(obj, list):
                        return [convert_to_dict(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {k: convert_to_dict(v) for k, v in obj.items()}
                    else:
                        return obj
                result_dict = convert_to_dict(result_dict)
            else:
                result_dict = result
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            saved_files['json'] = str(json_path)
            logger.info(f"JSON results saved to: {json_path}")
        
        # Save HTML report
        if not json_only:
            html_path = output_dir / f"{base_filename}.html"
            
            # Generate HTML report using create_security_report
            temp_result_paths = create_security_report(
                result, 
                output_format="html", 
                output_dir=str(output_dir)
            )
            
            # Move the generated HTML file to our desired location
            if 'html' in temp_result_paths:
                import shutil
                shutil.move(temp_result_paths['html'], html_path)
            
            saved_files['html'] = str(html_path)
            logger.info(f"HTML report saved to: {html_path}")
        
        return saved_files
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return {}

def main() -> int:
    """
    Main entry point for the Multi-Agent Security Analysis System.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Spyder - AI-Powered Security Scanner starting...")
        
        # Validate configuration if requested
        if args.validate_config:
            logger.info("Validating configuration...")
            if config.validate():
                logger.info("Configuration is valid")
                return 0
            else:
                logger.error("Configuration validation failed")
                return 1
        
        # Validate arguments (skip if just validating config)
        if not args.validate_config and not validate_arguments(args):
            logger.error("Invalid arguments provided")
            return 1
        
        # Validate configuration
        if not config.validate():
            logger.error("Configuration validation failed")
            return 1
        
        # Set up output directory
        try:
            output_dir = setup_output_directory(args.output_dir)
            logger.info(f"Output directory: {output_dir}")
        except OSError as e:
            logger.error(f"Output directory setup failed: {e}")
            return 1
        
        # Update malicious package database if needed
        db_success = update_database_if_needed(args.skip_db_update, args.force_db_update)
        if not db_success and not args.skip_db_update:
            logger.warning("Database update failed, but continuing with analysis")
        
        # Perform analysis
        result = perform_analysis(args)
        if result is None:
            logger.error("Analysis failed")
            return 1
        
        # Save results
        saved_files = save_results(
            result, 
            output_dir, 
            args.json_only, 
            args.html_only
        )
        
        if not saved_files:
            logger.error("Failed to save results")
            return 1
        
        # Print summary
        logger.info("Analysis completed successfully!")
        logger.info(f"Results saved to:")
        for format_type, file_path in saved_files.items():
            logger.info(f"  {format_type.upper()}: {file_path}")
        
        # Print key findings summary
        if result.summary.critical_findings > 0:
            logger.warning(f"CRITICAL: {result.summary.critical_findings} critical security findings detected!")
        if result.summary.high_findings > 0:
            logger.warning(f"HIGH: {result.summary.high_findings} high-severity findings detected!")
        
        logger.info(f"Total findings: {result.summary.total_findings}")
        logger.info(f"Packages analyzed: {result.summary.total_packages}")
        logger.info(f"Ecosystems: {', '.join(result.summary.ecosystems_analyzed)}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())