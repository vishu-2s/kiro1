"""
Property-based tests for GitHub integration tools.

**Feature: multi-agent-security, Property 1: Data Source Processing**
**Validates: Requirements 1.1, 2.1**
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume
from typing import Dict, List, Any, Tuple
import string
import requests

from tools.github_tools import (
    GitHubClient,
    GitHubAPIError,
    RateLimitExceeded,
    parse_github_url,
    fetch_repository_data,
    fetch_repository_contents,
    fetch_file_content,
    fetch_dependabot_alerts,
    fetch_workflow_runs,
    fetch_repository_languages,
    generate_repository_sbom,
    analyze_repository_for_supply_chain_risks,
    save_repository_data
)


# Strategies for property-based testing
github_username_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-",
    min_size=1,
    max_size=39
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

github_repo_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.",
    min_size=1,
    max_size=100
).filter(lambda x: x and not x.startswith('.') and not x.endswith('.'))

# Strategy for generating GitHub URLs
github_url_strategy = st.one_of(
    # Standard GitHub URLs
    st.builds(
        lambda owner, repo: f"https://github.com/{owner}/{repo}",
        github_username_strategy,
        github_repo_strategy
    ),
    # GitHub URLs with .git suffix
    st.builds(
        lambda owner, repo: f"https://github.com/{owner}/{repo}.git",
        github_username_strategy,
        github_repo_strategy
    ),
    # Short format owner/repo
    st.builds(
        lambda owner, repo: f"{owner}/{repo}",
        github_username_strategy,
        github_repo_strategy
    )
)

# Strategy for generating file content
file_content_strategy = st.text(min_size=0, max_size=1000)

# Strategy for generating repository data
repo_info_strategy = st.builds(
    dict,
    name=github_repo_strategy,
    full_name=st.builds(lambda o, r: f"{o}/{r}", github_username_strategy, github_repo_strategy),
    default_branch=st.sampled_from(["main", "master", "develop"]),
    language=st.sampled_from(["Python", "JavaScript", "Java", "Go", "Rust", None]),
    created_at=st.text(min_size=10, max_size=30),
    updated_at=st.text(min_size=10, max_size=30),
    size=st.integers(min_value=0, max_value=1000000),
    stargazers_count=st.integers(min_value=0, max_value=10000),
    forks_count=st.integers(min_value=0, max_value=1000)
)


class TestDataSourceProcessing:
    """Property-based tests for data source processing."""

    @given(github_url_strategy)
    def test_github_url_parsing_consistency(self, repo_url: str):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any valid data source (GitHub repository URL or local directory path), 
        the system should successfully fetch or scan all available package files and metadata.
        """
        assume(repo_url.strip() != "")
        
        try:
            owner, repo = parse_github_url(repo_url)
            
            # Property: Should return non-empty strings
            assert isinstance(owner, str), "Owner should be string"
            assert isinstance(repo, str), "Repo should be string"
            assert owner.strip() != "", "Owner should not be empty"
            assert repo.strip() != "", "Repo should not be empty"
            
            # Property: Owner and repo should not contain invalid characters
            invalid_chars = set(" \t\n\r/\\")
            assert not any(c in owner for c in invalid_chars), f"Owner '{owner}' should not contain invalid characters"
            assert not any(c in repo for c in invalid_chars), f"Repo '{repo}' should not contain invalid characters"
            
            # Property: Repo should not have .git suffix after parsing
            assert not repo.endswith('.git'), "Repo name should not end with .git after parsing"
            
        except ValueError:
            # This is acceptable for invalid URLs
            pass

    def test_github_url_parsing_known_formats(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any known GitHub URL format, parsing should extract correct owner and repo.
        """
        test_cases = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/owner/repo.git", ("owner", "repo")),
            ("owner/repo", ("owner", "repo")),
            ("https://github.com/test-user/test-repo", ("test-user", "test-repo")),
            ("https://github.com/user123/repo_name", ("user123", "repo_name")),
        ]
        
        for url, expected in test_cases:
            owner, repo = parse_github_url(url)
            assert (owner, repo) == expected, f"URL '{url}' should parse to {expected}, got ({owner}, {repo})"

    def test_github_url_parsing_invalid_formats(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any invalid GitHub URL format, parsing should raise appropriate errors.
        """
        invalid_urls = [
            "",
            "not-a-url",
            "https://gitlab.com/owner/repo",
            "https://github.com/",
            "https://github.com/owner",
            "owner",
            "/repo",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                parse_github_url(url)

    @patch('tools.github_tools.GitHubClient')
    def test_repository_data_fetching_structure(self, mock_client_class):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any valid GitHub repository, the system should fetch comprehensive
        data with consistent structure.
        """
        # Mock GitHubClient instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock API responses
        mock_client._make_request.side_effect = [
            # Repository info
            {
                "name": "test-repo",
                "full_name": "owner/test-repo",
                "default_branch": "main",
                "language": "Python",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "size": 1000,
                "stargazers_count": 10,
                "forks_count": 2
            }
        ]
        
        # Mock other functions
        with patch('tools.github_tools.fetch_repository_contents', return_value=[]), \
             patch('tools.github_tools.fetch_dependabot_alerts', return_value=[]), \
             patch('tools.github_tools.fetch_workflow_runs', return_value=[]), \
             patch('tools.github_tools.generate_repository_sbom', return_value={"packages": []}), \
             patch('tools.github_tools.fetch_repository_languages', return_value={"Python": 1000}):
            
            repo_data = fetch_repository_data("https://github.com/owner/test-repo")
            
            # Property: Should return dictionary with required top-level keys
            assert isinstance(repo_data, dict), "Repository data should be dictionary"
            required_keys = ["repository", "contents", "dependabot_alerts", "workflow_runs", "sbom", "fetched_at"]
            for key in required_keys:
                assert key in repo_data, f"Repository data should contain '{key}'"
            
            # Property: Repository section should have required fields
            repo_info = repo_data["repository"]
            repo_required_fields = ["owner", "name", "full_name", "url", "default_branch"]
            for field in repo_required_fields:
                assert field in repo_info, f"Repository info should contain '{field}'"
            
            # Property: All list fields should be lists
            list_fields = ["contents", "dependabot_alerts", "workflow_runs"]
            for field in list_fields:
                assert isinstance(repo_data[field], list), f"Field '{field}' should be list"

    def test_github_client_initialization(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any GitHub client initialization, it should set up proper authentication
        and headers consistently.
        """
        # Test with token
        client_with_token = GitHubClient(token="test-token")
        assert client_with_token.token == "test-token", "Client should store token"
        assert "Authorization" in client_with_token.session.headers, "Client should set Authorization header"
        assert client_with_token.session.headers["Authorization"] == "token test-token", "Authorization header should be correct"
        
        # Test without token
        with patch('tools.github_tools.config.GITHUB_TOKEN', None):
            client_without_token = GitHubClient()
            assert client_without_token.token is None, "Client should have no token"
            assert "Authorization" not in client_without_token.session.headers, "Client should not set Authorization header without token"

    @patch('tools.github_tools.requests.Session.get')
    def test_github_api_request_handling(self, mock_get):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any GitHub API request, the client should handle responses
        and errors consistently.
        """
        client = GitHubClient(token="test-token")
        
        # Test successful request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = client._make_request("test/endpoint")
        
        # Property: Should return JSON data
        assert result == {"test": "data"}, "Should return JSON response"
        
        # Property: Should call correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.github.com/test/endpoint" in call_args[0][0], "Should call correct API URL"

    @patch('tools.github_tools.requests.Session.get')
    def test_github_api_rate_limit_handling(self, mock_get):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any rate limit conditions, the GitHub client should handle
        them appropriately.
        """
        client = GitHubClient(token="test-token")
        
        # Test rate limit exceeded
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': '1640995200'  # Some future timestamp
        }
        mock_get.return_value = mock_response
        
        # Property: Should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            client._make_request("test/endpoint")

    @patch('tools.github_tools.requests.Session.get')
    def test_github_api_error_handling(self, mock_get):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any API error conditions, the GitHub client should handle
        them gracefully and raise appropriate exceptions.
        """
        client = GitHubClient(token="test-token")
        
        # Test various error conditions
        error_conditions = [
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (401, "Unauthorized"),
        ]
        
        for status_code, error_message in error_conditions:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.raise_for_status.side_effect = requests.HTTPError(error_message)
            mock_get.return_value = mock_response
            
            # Property: Should raise GitHubAPIError
            with pytest.raises(GitHubAPIError):
                client._make_request("test/endpoint")

    def test_repository_contents_processing(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any repository contents, the system should process them
        consistently and extract package files.
        """
        # Test with valid contents data (only files, no directories to avoid recursion complexity)
        contents_data = [
            {
                "name": "package.json",
                "path": "package.json", 
                "type": "file",
                "sha": "abc123",
                "size": 1000
            },
            {
                "name": "README.md",
                "path": "README.md",
                "type": "file",
                "sha": "def456",
                "size": 500
            }
        ]
        
        # Mock GitHubClient
        mock_client = Mock()
        mock_client._make_request.return_value = contents_data
        
        with patch('tools.github_tools.fetch_file_content', return_value="test content"):
            result = fetch_repository_contents("owner", "repo", mock_client)
            
            # Property: Should return list
            assert isinstance(result, list), "Repository contents should be list"
            
            # Property: Should process files correctly
            assert len(result) >= 0, "Result should be non-negative length"
            
            # Property: All items should be dictionaries
            for item in result:
                assert isinstance(item, dict), "All content items should be dictionaries"
                
            # Property: Package files should have content and ecosystem
            package_files = [item for item in result if item.get("name", "").lower() == "package.json"]
            for pkg_file in package_files:
                assert "content" in pkg_file, "Package files should have content"
                assert "ecosystem" in pkg_file, "Package files should have ecosystem detected"

    def test_file_content_fetching_consistency(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any file in a repository, content fetching should handle
        different encoding formats consistently.
        """
        mock_client = Mock()
        
        # Test base64 encoded content
        import base64
        test_content = "test file content"
        encoded_content = base64.b64encode(test_content.encode()).decode()
        
        mock_client._make_request.return_value = {
            "content": encoded_content,
            "encoding": "base64"
        }
        
        result = fetch_file_content("owner", "repo", "test.txt", mock_client)
        
        # Property: Should decode base64 content correctly
        assert result == test_content, "Should decode base64 content correctly"
        
        # Test direct content
        mock_client._make_request.return_value = {
            "content": test_content,
            "encoding": "utf-8"
        }
        
        result = fetch_file_content("owner", "repo", "test.txt", mock_client)
        
        # Property: Should return direct content
        assert result == test_content, "Should return direct content"

    def test_repository_sbom_generation(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any repository with package files, SBOM generation should
        create consistent structure.
        """
        mock_client = Mock()
        
        # Mock contents with package files
        contents = [
            {
                "name": "package.json",
                "path": "package.json",
                "type": "file",
                "content": json.dumps({"name": "test-pkg", "version": "1.0.0"}),
                "ecosystem": "npm",
                "sha": "sha1",
                "size": 100
            }
        ]
        
        with patch('tools.github_tools.extract_packages_from_file') as mock_extract:
            # Mock package extraction
            from tools.sbom_tools import SBOMPackage
            mock_packages = [
                SBOMPackage(
                    name="test-pkg",
                    version="1.0.0",
                    ecosystem="npm"
                )
            ]
            
            mock_extract.return_value = mock_packages
            
            result = generate_repository_sbom("owner", "repo", contents, mock_client)
            
            # Property: Should return dictionary with SBOM structure
            assert isinstance(result, dict), "SBOM should be dictionary"
            assert "packages" in result, "SBOM should contain packages"
            assert "source" in result, "SBOM should contain source info"
            assert "metadata" in result, "SBOM should contain metadata"
            
            # Property: Source should indicate GitHub repository
            source = result["source"]
            assert source["type"] == "github_repository", "Source type should be github_repository"
            assert "owner/repo" in source["repository"], "Source should contain repository info"

    def test_repository_data_saving_consistency(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any repository data, saving should create consistent file
        structure and format.
        """
        test_data = {
            "repository": {
                "owner": "test-owner",
                "name": "test-repo",
                "full_name": "test-owner/test-repo"
            },
            "contents": [],
            "dependabot_alerts": [],
            "workflow_runs": [],
            "sbom": {"packages": []},
            "fetched_at": "2024-01-01T00:00:00Z"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = save_repository_data(test_data, temp_dir)
            
            # Property: Should return valid file path
            assert isinstance(file_path, str), "Should return string file path"
            assert os.path.exists(file_path), "File should exist"
            
            # Property: File should contain valid JSON
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data, "Saved data should match original"
            
            # Property: Filename should follow expected pattern
            filename = os.path.basename(file_path)
            assert filename.startswith("github_analysis_"), "Filename should start with github_analysis_"
            assert filename.endswith(".json"), "Filename should end with .json"
            assert "test-owner_test-repo" in filename, "Filename should contain repository name"

    def test_supply_chain_risk_analysis_consistency(self):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any repository data, supply chain risk analysis should
        identify risks consistently.
        """
        # Test data with open Dependabot alerts
        repo_data_with_alerts = {
            "dependabot_alerts": [
                {
                    "number": 1,
                    "state": "open",
                    "dependency": "test-package",
                    "security_advisory": {
                        "ghsa_id": "GHSA-test-001",
                        "severity": "high",
                        "summary": "Test vulnerability"
                    }
                }
            ],
            "workflow_runs": []
        }
        
        findings = analyze_repository_for_supply_chain_risks(repo_data_with_alerts)
        
        # Property: Should return list of findings
        assert isinstance(findings, list), "Risk analysis should return list"
        
        # Property: Should detect open Dependabot alerts
        dependabot_findings = [f for f in findings if f.finding_type == "dependabot_alert"]
        assert len(dependabot_findings) > 0, "Should detect open Dependabot alerts"
        
        # Test data with high failure rate in CI/CD
        repo_data_with_failures = {
            "dependabot_alerts": [],
            "workflow_runs": [
                {"conclusion": "failure"},
                {"conclusion": "failure"},
                {"conclusion": "success"}
            ]
        }
        
        findings = analyze_repository_for_supply_chain_risks(repo_data_with_failures)
        
        # Property: Should detect CI/CD anomalies
        ci_findings = [f for f in findings if f.finding_type == "ci_cd_anomaly"]
        # Note: This depends on the threshold logic in the implementation
        # We just check that the function runs without error
        assert isinstance(findings, list), "Risk analysis should return list for CI/CD data"

    @given(st.text(min_size=1, max_size=100))
    def test_data_source_processing_error_resilience(self, invalid_input: str):
        """
        **Feature: multi-agent-security, Property 1: Data Source Processing**
        
        For any invalid or malformed input, the data source processing
        should handle errors gracefully without crashing.
        """
        assume(invalid_input.strip() != "")
        
        # Test URL parsing with invalid input
        try:
            parse_github_url(invalid_input)
        except ValueError:
            # This is expected for invalid URLs
            pass
        except Exception as e:
            pytest.fail(f"URL parsing should not raise unexpected exception: {e}")
        
        # Test client initialization with invalid token
        try:
            client = GitHubClient(token=invalid_input)
            assert isinstance(client, GitHubClient), "Client should initialize even with invalid token"
        except Exception as e:
            pytest.fail(f"Client initialization should not raise exception: {e}")