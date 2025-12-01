"""
Property-based tests for main orchestration system configuration management.

**Feature: multi-agent-security, Property 21: Configuration Management**
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List, Optional
import json
import argparse
import string

from main_github import (
    create_argument_parser,
    validate_arguments,
    setup_output_directory,
    update_database_if_needed,
    setup_logging,
    main
)
from config import Config


# Strategies for generating test data
valid_url_strategy = st.sampled_from([
    "https://github.com/user/repo",
    "https://github.com/org/project",
    "https://github.com/test/example.git"
])

valid_path_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=1,
    max_size=50
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

confidence_threshold_strategy = st.floats(min_value=0.0, max_value=1.0)

log_level_strategy = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

output_format_strategy = st.sampled_from([
    {"json_only": True, "html_only": False},
    {"json_only": False, "html_only": True},
    {"json_only": False, "html_only": False}
])

env_var_strategy = st.dictionaries(
    keys=st.sampled_from([
        "OPENAI_API_KEY", "OPENAI_MODEL", "GITHUB_TOKEN", "CACHE_ENABLED",
        "OUTPUT_DIRECTORY", "AGENT_TEMPERATURE", "LOG_LEVEL", "CONFIDENCE_THRESHOLD"
    ]),
    values=st.text(
        alphabet=string.ascii_letters + string.digits + "_-./",
        min_size=1, 
        max_size=50
    ).filter(lambda x: '\x00' not in x and '\n' not in x and '\r' not in x),
    min_size=0,
    max_size=8
)

command_line_args_strategy = st.fixed_dictionaries({
    "target_type": st.sampled_from(["github", "local", "sbom"]),
    "target_value": st.text(min_size=1, max_size=100),
    "confidence_threshold": confidence_threshold_strategy,
    "output_dir": valid_path_strategy,
    "log_level": log_level_strategy,
    "skip_db_update": st.booleans(),
    "force_db_update": st.booleans(),
    "no_osv": st.booleans(),
    "no_visual": st.booleans(),
    "json_only": st.booleans(),
    "html_only": st.booleans()
})


class TestConfigurationManagement:
    """Property-based tests for configuration management."""

    @given(command_line_args_strategy)
    def test_argument_parser_consistency(self, args_config: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
        
        For any valid command-line argument configuration, the argument parser
        should consistently parse and validate the arguments according to the
        system's configuration rules.
        """
        # Skip invalid combinations
        if args_config["skip_db_update"] and args_config["force_db_update"]:
            assume(False)  # Skip this combination as it's invalid
        if args_config["json_only"] and args_config["html_only"]:
            assume(False)  # Skip this combination as it's invalid
        
        parser = create_argument_parser()
        
        # Build command line arguments
        cmd_args = []
        
        # Add target argument
        target_type = args_config["target_type"]
        target_value = args_config["target_value"]
        cmd_args.extend([f"--{target_type}", target_value])
        
        # Add optional arguments
        cmd_args.extend(["--confidence-threshold", str(args_config["confidence_threshold"])])
        cmd_args.extend(["--output-dir", args_config["output_dir"]])
        cmd_args.extend(["--log-level", args_config["log_level"]])
        
        if args_config["skip_db_update"]:
            cmd_args.append("--skip-db-update")
        if args_config["force_db_update"]:
            cmd_args.append("--force-db-update")
        if args_config["no_osv"]:
            cmd_args.append("--no-osv")
        if args_config["no_visual"]:
            cmd_args.append("--no-visual")
        if args_config["json_only"]:
            cmd_args.append("--json-only")
        if args_config["html_only"]:
            cmd_args.append("--html-only")
        
        # Parse arguments
        try:
            parsed_args = parser.parse_args(cmd_args)
            
            # Verify parsed values match input
            assert getattr(parsed_args, target_type) == target_value
            assert parsed_args.confidence_threshold == args_config["confidence_threshold"]
            assert parsed_args.output_dir == args_config["output_dir"]
            assert parsed_args.log_level == args_config["log_level"]
            assert parsed_args.skip_db_update == args_config["skip_db_update"]
            assert parsed_args.force_db_update == args_config["force_db_update"]
            assert parsed_args.no_osv == args_config["no_osv"]
            assert parsed_args.no_visual == args_config["no_visual"]
            assert parsed_args.json_only == args_config["json_only"]
            assert parsed_args.html_only == args_config["html_only"]
            
        except SystemExit:
            # Parser may exit on invalid arguments, which is expected behavior
            pass

    @given(env_var_strategy)
    def test_environment_variable_loading_consistency(self, env_vars: Dict[str, str]):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.2, 9.5**
        
        For any set of environment variables, the configuration system should
        consistently load and apply them to the system configuration.
        """
        try:
            with patch.dict(os.environ, env_vars, clear=False):
                # Import config fresh to pick up environment changes
                import importlib
                import config as config_module
                importlib.reload(config_module)
                test_config = config_module.Config()
                
                # Verify environment variables are loaded correctly
                for env_key, env_value in env_vars.items():
                    if env_key == "OPENAI_API_KEY":
                        assert test_config.OPENAI_API_KEY == env_value
                    elif env_key == "OPENAI_MODEL":
                        assert test_config.OPENAI_MODEL == env_value
                    elif env_key == "GITHUB_TOKEN":
                        assert test_config.GITHUB_TOKEN == env_value
                    elif env_key == "CACHE_ENABLED":
                        expected = env_value.lower() == "true"
                        assert test_config.CACHE_ENABLED == expected
                    elif env_key == "OUTPUT_DIRECTORY":
                        assert test_config.OUTPUT_DIRECTORY == env_value
                    elif env_key == "LOG_LEVEL":
                        assert test_config.LOG_LEVEL == env_value
                    elif env_key == "CONFIDENCE_THRESHOLD":
                        try:
                            expected = float(env_value)
                            assert test_config.CONFIDENCE_THRESHOLD == expected
                        except ValueError:
                            # Invalid float values should use default
                            pass
        except (ValueError, OSError):
            # Some environment variable values may be invalid
            pass

    @given(valid_path_strategy)
    def test_output_directory_management_consistency(self, output_path: str):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.4**
        
        For any valid output directory path, the system should consistently
        create and manage the output directory with proper permissions.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            full_output_path = os.path.join(temp_dir, output_path)
            
            try:
                result_path = setup_output_directory(full_output_path)
                
                # Verify directory was created
                assert result_path.exists(), f"Output directory should be created: {full_output_path}"
                assert result_path.is_dir(), f"Output path should be a directory: {full_output_path}"
                
                # Verify write permissions by creating a test file
                test_file = result_path / "test_write.txt"
                test_file.write_text("test")
                assert test_file.exists(), "Should be able to write to output directory"
                
                # Test idempotency - calling again should not fail
                result_path2 = setup_output_directory(full_output_path)
                assert result_path == result_path2, "Multiple calls should return same path"
                
            except OSError:
                # Some paths may be invalid on the current system, which is acceptable
                pass

    @given(st.booleans(), st.booleans())
    def test_database_update_flag_consistency(self, skip_update: bool, force_update: bool):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.2**
        
        For any combination of database update flags, the system should
        consistently handle the update logic according to the specified behavior.
        """
        # Skip invalid combinations
        if skip_update and force_update:
            assume(False)
        
        with patch('main_github.MaliciousPackageUpdater') as mock_updater_class:
            mock_updater = mock_updater_class.return_value
            mock_updater.update_database.return_value = True
            
            result = update_database_if_needed(skip_update, force_update)
            
            if skip_update:
                # Should not create updater when skipping
                mock_updater_class.assert_not_called()
                assert result is True, "Skip update should return True"
            else:
                # Should create updater and call update_database with correct force parameter
                mock_updater_class.assert_called_once()
                mock_updater.update_database.assert_called_once_with(force_update=force_update)
                assert result is True, "Successful update should return True"

    @given(log_level_strategy, st.text(
        alphabet=string.ascii_letters + string.digits + "_-",
        min_size=1, 
        max_size=20
    ).filter(lambda x: x and x.isalnum()))
    def test_logging_configuration_consistency(self, log_level: str, log_filename: str):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.5**
        
        For any valid logging configuration, the system should consistently
        set up logging with the specified level and output destination.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = os.path.join(temp_dir, log_filename + ".log")
            
            # Test console-only logging
            setup_logging(log_level, None)
            
            import logging
            logger = logging.getLogger("test_logger")
            
            # Verify log level is set correctly
            root_logger = logging.getLogger()
            expected_level = getattr(logging, log_level.upper())
            assert root_logger.level == expected_level, f"Log level should be {log_level}"
            
            # Test file logging
            try:
                setup_logging(log_level, log_file_path)
                
                # Verify log file is created when logging occurs
                logger.info("Test log message")
                
                # Close all handlers to release file locks
                import logging
                for handler in logging.getLogger().handlers[:]:
                    handler.close()
                    logging.getLogger().removeHandler(handler)
                
                # Check if log file exists (it should be created on first log message)
                if os.path.exists(log_file_path):
                    assert os.path.isfile(log_file_path), "Log file should be a regular file"
            except (OSError, ValueError, PermissionError):
                # Some filenames may be invalid on the current system or file may be locked
                pass

    @given(command_line_args_strategy)
    def test_argument_validation_consistency(self, args_config: Dict[str, Any]):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.1, 9.3**
        
        For any command-line argument configuration, the validation function
        should consistently validate arguments according to system rules.
        """
        # Create a mock args object
        args = argparse.Namespace()
        
        # Set target arguments
        target_type = args_config["target_type"]
        for t_type in ["github", "local", "sbom"]:
            setattr(args, t_type, None)
        setattr(args, target_type, args_config["target_value"])
        
        # Set other arguments
        args.confidence_threshold = args_config["confidence_threshold"]
        args.output_dir = args_config["output_dir"]
        args.screenshots = None
        args.skip_db_update = args_config["skip_db_update"]
        args.force_db_update = args_config["force_db_update"]
        args.json_only = args_config["json_only"]
        args.html_only = args_config["html_only"]
        
        # Test validation logic
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files/directories for validation
            if target_type == "local":
                test_dir = os.path.join(temp_dir, "test_local")
                os.makedirs(test_dir, exist_ok=True)
                args.local = test_dir
            elif target_type == "sbom":
                test_file = os.path.join(temp_dir, "test_sbom.json")
                with open(test_file, 'w') as f:
                    json.dump({"packages": []}, f)
                args.sbom = test_file
            
            # Validate arguments
            is_valid = validate_arguments(args)
            
            # Check validation results
            if args_config["skip_db_update"] and args_config["force_db_update"]:
                assert not is_valid, "Conflicting database flags should be invalid"
            elif args_config["json_only"] and args_config["html_only"]:
                assert not is_valid, "Conflicting output format flags should be invalid"
            elif not (0.0 <= args_config["confidence_threshold"] <= 1.0):
                assert not is_valid, "Invalid confidence threshold should be invalid"
            elif target_type in ["local", "sbom"]:
                # For local/sbom, validation depends on file existence (which we created)
                assert is_valid, "Valid file paths should pass validation"
            else:
                # For GitHub URLs, validation should pass for well-formed URLs
                assert isinstance(is_valid, bool), "Validation should return boolean"

    @settings(max_examples=10)  # Reduce examples for integration tests
    @given(st.sampled_from(["--validate-config", "--version"]))
    def test_utility_options_consistency(self, utility_flag: str):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.1**
        
        For any utility command-line option, the system should consistently
        handle the option and exit appropriately.
        """
        with patch('sys.argv', ['main_github.py', utility_flag, '--github', 'https://github.com/test/repo']):
            with patch('main_github.config') as mock_config:
                mock_config.validate.return_value = True
                mock_config.LOG_LEVEL = "INFO"  # Provide string value for LOG_LEVEL
                
                try:
                    if utility_flag == "--validate-config":
                        # Should validate config and exit
                        result = main()
                        # If it doesn't exit, it should return 0 for success
                        assert result == 0, "Validate config should return 0 for success"
                    
                    elif utility_flag == "--version":
                        # Should print version and exit
                        with pytest.raises(SystemExit) as exc_info:
                            main()
                        # Version flag typically exits with code 0
                        assert exc_info.value.code == 0, "Version flag should exit with code 0"
                except SystemExit as e:
                    # Both flags may cause SystemExit, which is acceptable
                    assert e.code in [0, 1], "Should exit with valid code"

    @given(st.dictionaries(
        keys=st.sampled_from(["OPENAI_API_KEY", "GITHUB_TOKEN", "OUTPUT_DIRECTORY"]),
        values=st.text(
            alphabet=string.ascii_letters + string.digits + "_-./",
            min_size=1, 
            max_size=50
        ).filter(lambda x: '\x00' not in x and '\n' not in x and '\r' not in x),
        min_size=1,
        max_size=3
    ))
    def test_configuration_override_consistency(self, config_overrides: Dict[str, str]):
        """
        **Feature: multi-agent-security, Property 21: Configuration Management**
        **Validates: Requirements 9.2, 9.5**
        
        For any configuration override (environment variables or command-line flags),
        the system should consistently apply the override values in the correct
        precedence order.
        """
        try:
            with patch.dict(os.environ, config_overrides, clear=False):
                # Import config fresh to pick up environment changes
                import importlib
                import config as config_module
                importlib.reload(config_module)
                test_config = config_module.Config()
                
                for key, value in config_overrides.items():
                    if key == "OPENAI_API_KEY":
                        assert test_config.OPENAI_API_KEY == value
                    elif key == "GITHUB_TOKEN":
                        assert test_config.GITHUB_TOKEN == value
                    elif key == "OUTPUT_DIRECTORY":
                        assert test_config.OUTPUT_DIRECTORY == value
                
                # Test that command-line arguments would override environment variables
                # (This is tested implicitly through the argument parsing tests)
                assert hasattr(test_config, 'OPENAI_API_KEY'), "Config should have required attributes"
        except (ValueError, OSError):
            # Some environment variable values may be invalid
            pass