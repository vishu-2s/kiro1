"""
GitHub integration tools for Multi-Agent Security Analysis System.

This module provides functions for:
- GitHub API client and authentication
- Fetching repository data, package files, Dependabot alerts, and workflow runs
- SBOM generation from GitHub repository data
- Proper error handling and rate limiting for GitHub API
"""

import json
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import requests
from datetime import datetime, timedelta
import logging

from config import config
from tools.sbom_tools import (
    SBOMPackage, 
    SecurityFinding, 
    detect_ecosystem, 
    extract_packages_from_file,
    generate_sbom_from_packages,
    validate_sbom_structure
)
from tools.api_integration import GitHubAPIClient, APIResponse

logger = logging.getLogger(__name__)

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass

class RateLimitExceeded(GitHubAPIError):
    """Exception raised when GitHub API rate limit is exceeded."""
    pass

class GitHubClient:
    """GitHub API client with authentication and rate limiting."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or config.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        # Set up authentication headers
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Multi-Agent-Security-Analysis-System/1.0"
            })
        else:
            logger.warning("No GitHub token provided. API rate limits will be severely restricted.")
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Multi-Agent-Security-Analysis-System/1.0"
            })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API with rate limiting.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
        
        Returns:
            JSON response data
        
        Raises:
            GitHubAPIError: For API errors
            RateLimitExceeded: When rate limit is exceeded
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # Check rate limiting
            if response.status_code == 403:
                rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                if rate_limit_remaining == 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    raise RateLimitExceeded(
                        f"GitHub API rate limit exceeded. Resets at {reset_datetime}"
                    )
            
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"GitHub API request failed for {endpoint}: {e}")
            raise GitHubAPIError(f"Failed to fetch {endpoint}: {e}")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        try:
            return self._make_request("rate_limit")
        except GitHubAPIError:
            return {"resources": {"core": {"remaining": 0, "limit": 60}}}
    
    def wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset if necessary."""
        rate_limit = self.get_rate_limit_status()
        core_limit = rate_limit.get("resources", {}).get("core", {})
        remaining = core_limit.get("remaining", 0)
        
        if remaining < 10:  # Conservative threshold
            reset_time = core_limit.get("reset", 0)
            if reset_time:
                wait_time = max(0, reset_time - int(time.time()) + 60)  # Add 1 minute buffer
                if wait_time > 0:
                    logger.info(f"Rate limit low. Waiting {wait_time} seconds for reset.")
                    time.sleep(wait_time)

def parse_github_url(repo_url: str) -> Tuple[str, str]:
    """
    Parse GitHub repository URL to extract owner and repo name.
    
    Args:
        repo_url: GitHub repository URL
    
    Returns:
        Tuple of (owner, repo_name)
    
    Raises:
        ValueError: If URL is not a valid GitHub repository URL
    """
    try:
        parsed = urlparse(repo_url)
        
        # Handle different URL formats
        if parsed.netloc == "github.com":
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].replace(".git", "")
                return owner, repo
        
        # Try to extract from path if it looks like owner/repo format
        if "/" in repo_url and not repo_url.startswith("http"):
            parts = repo_url.strip("/").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    except Exception as e:
        raise ValueError(f"Failed to parse GitHub URL {repo_url}: {e}")

def fetch_repository_data(repo_url: str, client: Optional[GitHubAPIClient] = None) -> Dict[str, Any]:
    """
    Fetch comprehensive repository data including metadata, dependencies, and security alerts.
    
    Args:
        repo_url: GitHub repository URL
        client: Optional GitHubAPIClient instance
    
    Returns:
        Dictionary containing repository data
    
    Raises:
        GitHubAPIError: For API errors
        ValueError: For invalid repository URLs
    """
    if client is None:
        client = GitHubAPIClient()
    
    owner, repo = parse_github_url(repo_url)
    
    logger.info(f"Fetching repository data for {owner}/{repo}")
    
    # Fetch basic repository information
    repo_response = client.get_repository(owner, repo)
    if not repo_response.is_success():
        raise GitHubAPIError(f"Failed to fetch repository info: {repo_response.error.message}")
    
    repo_info = repo_response.get_data()
    
    # Fetch repository contents to find package files
    contents = fetch_repository_contents(owner, repo, client)
    
    # Fetch Dependabot alerts if available
    dependabot_alerts = fetch_dependabot_alerts(owner, repo, client)
    
    # Fetch workflow runs for CI/CD analysis
    workflow_runs = fetch_workflow_runs(owner, repo, client)
    
    # Generate SBOM from repository data
    sbom_data = generate_repository_sbom(owner, repo, contents, client)
    
    return {
        "repository": {
            "owner": owner,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "url": repo_url,
            "default_branch": repo_info.get("default_branch", "main"),
            "language": repo_info.get("language"),
            "languages": fetch_repository_languages(owner, repo, client),
            "created_at": repo_info.get("created_at"),
            "updated_at": repo_info.get("updated_at"),
            "size": repo_info.get("size"),
            "stargazers_count": repo_info.get("stargazers_count"),
            "forks_count": repo_info.get("forks_count")
        },
        "contents": contents,
        "dependabot_alerts": dependabot_alerts,
        "workflow_runs": workflow_runs,
        "sbom": sbom_data,
        "fetched_at": datetime.now().isoformat()
    }

def fetch_repository_contents(owner: str, repo: str, client: GitHubAPIClient, 
                            path: str = "", max_depth: int = 3) -> List[Dict[str, Any]]:
    """
    Fetch repository contents recursively to find package files.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: GitHubAPIClient instance
        path: Current path (for recursion)
        max_depth: Maximum recursion depth
    
    Returns:
        List of file information dictionaries
    """
    if max_depth <= 0:
        return []
    
    try:
        contents_response = client.get_repository_contents(owner, repo, path)
        if not contents_response.is_success():
            logger.warning(f"Failed to fetch contents for {owner}/{repo}/{path}: {contents_response.error.message}")
            return []
        
        contents = contents_response.get_data()
        
        if not isinstance(contents, list):
            contents = [contents]
        
        files = []
        package_files = [
            "package.json", "package-lock.json", "yarn.lock", "npm-shrinkwrap.json",
            "requirements.txt", "setup.py", "pyproject.toml", "pipfile", "pipfile.lock",
            "pom.xml", "build.gradle", "gradle.properties",
            "gemfile", "gemfile.lock", ".gemspec",
            "cargo.toml", "cargo.lock",
            "go.mod", "go.sum"
        ]
        
        for item in contents:
            if item["type"] == "file":
                filename = item["name"].lower()
                if any(pkg_file in filename for pkg_file in package_files):
                    # Fetch file content for package files
                    file_content = fetch_file_content(owner, repo, item["path"], client)
                    item["content"] = file_content
                    item["ecosystem"] = detect_ecosystem(item["name"], file_content)
                
                files.append(item)
            
            elif item["type"] == "dir" and max_depth > 1:
                # Recursively fetch directory contents
                subdir_files = fetch_repository_contents(
                    owner, repo, client, item["path"], max_depth - 1
                )
                files.extend(subdir_files)
        
        return files
    
    except GitHubAPIError as e:
        logger.warning(f"Failed to fetch contents for {owner}/{repo}/{path}: {e}")
        return []

def fetch_file_content(owner: str, repo: str, file_path: str, client: GitHubAPIClient) -> Optional[str]:
    """
    Fetch content of a specific file from repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        file_path: Path to file in repository
        client: GitHubAPIClient instance
    
    Returns:
        File content as string, or None if failed
    """
    try:
        file_response = client.get_repository_contents(owner, repo, file_path)
        if not file_response.is_success():
            logger.warning(f"Failed to fetch file content for {file_path}: {file_response.error.message}")
            return None
        
        file_data = file_response.get_data()
        
        if file_data.get("encoding") == "base64":
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            return content
        
        return file_data.get("content")
    
    except Exception as e:
        logger.warning(f"Failed to fetch file content for {file_path}: {e}")
        return None

def fetch_dependabot_alerts(owner: str, repo: str, client: GitHubAPIClient) -> List[Dict[str, Any]]:
    """
    Fetch Dependabot security alerts for repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: GitHubAPIClient instance
    
    Returns:
        List of Dependabot alerts
    """
    try:
        # Note: This endpoint requires specific permissions
        alerts_response = client.get_dependabot_alerts(owner, repo)
        if not alerts_response.is_success():
            logger.warning(f"Failed to fetch Dependabot alerts for {owner}/{repo}: {alerts_response.error.message}")
            return []
        
        alerts = alerts_response.get_data()
        
        processed_alerts = []
        for alert in alerts:
            processed_alert = {
                "number": alert.get("number"),
                "state": alert.get("state"),
                "dependency": alert.get("dependency", {}).get("package", {}).get("name"),
                "security_advisory": {
                    "ghsa_id": alert.get("security_advisory", {}).get("ghsa_id"),
                    "cve_id": alert.get("security_advisory", {}).get("cve_id"),
                    "summary": alert.get("security_advisory", {}).get("summary"),
                    "severity": alert.get("security_advisory", {}).get("severity"),
                    "cvss": alert.get("security_advisory", {}).get("cvss", {}).get("score")
                },
                "security_vulnerability": {
                    "package": alert.get("security_vulnerability", {}).get("package", {}).get("name"),
                    "severity": alert.get("security_vulnerability", {}).get("severity"),
                    "vulnerable_version_range": alert.get("security_vulnerability", {}).get("vulnerable_version_range"),
                    "first_patched_version": alert.get("security_vulnerability", {}).get("first_patched_version", {}).get("identifier")
                },
                "created_at": alert.get("created_at"),
                "updated_at": alert.get("updated_at")
            }
            processed_alerts.append(processed_alert)
        
        return processed_alerts
    
    except Exception as e:
        logger.warning(f"Failed to fetch Dependabot alerts for {owner}/{repo}: {e}")
        # This is expected for repositories without proper permissions
        return []

def fetch_workflow_runs(owner: str, repo: str, client: GitHubAPIClient, 
                       limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recent workflow runs for CI/CD analysis.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: GitHubAPIClient instance
        limit: Maximum number of workflow runs to fetch
    
    Returns:
        List of workflow run information
    """
    try:
        params = {"per_page": limit, "status": "completed"}
        workflow_response = client.get_workflow_runs(owner, repo, params)
        if not workflow_response.is_success():
            logger.warning(f"Failed to fetch workflow runs for {owner}/{repo}: {workflow_response.error.message}")
            return []
        
        workflow_runs = workflow_response.get_data()
        
        processed_runs = []
        for run in workflow_runs.get("workflow_runs", []):
            processed_run = {
                "id": run.get("id"),
                "name": run.get("name"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "workflow_id": run.get("workflow_id"),
                "head_branch": run.get("head_branch"),
                "head_sha": run.get("head_sha"),
                "run_number": run.get("run_number"),
                "event": run.get("event"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "run_started_at": run.get("run_started_at"),
                "jobs_url": run.get("jobs_url"),
                "logs_url": run.get("logs_url")
            }
            processed_runs.append(processed_run)
        
        return processed_runs
    
    except Exception as e:
        logger.warning(f"Failed to fetch workflow runs for {owner}/{repo}: {e}")
        return []

def fetch_repository_languages(owner: str, repo: str, client: GitHubAPIClient) -> Dict[str, int]:
    """
    Fetch programming languages used in repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: GitHubAPIClient instance
    
    Returns:
        Dictionary of languages and their byte counts
    """
    try:
        languages_response = client._make_request("GET", f"repos/{owner}/{repo}/languages")
        if not languages_response.is_success():
            logger.warning(f"Failed to fetch languages for {owner}/{repo}: {languages_response.error.message}")
            return {}
        return languages_response.get_data()
    except Exception as e:
        logger.warning(f"Failed to fetch languages for {owner}/{repo}: {e}")
        return {}

def generate_repository_sbom(owner: str, repo: str, contents: List[Dict[str, Any]], 
                           client: GitHubAPIClient) -> Dict[str, Any]:
    """
    Generate SBOM from repository contents.
    
    Args:
        owner: Repository owner
        repo: Repository name
        contents: Repository contents from fetch_repository_contents
        client: GitHubClient instance
    
    Returns:
        SBOM dictionary
    """
    all_packages = []
    
    # Process each package file found in the repository
    for file_info in contents:
        if file_info.get("content") and file_info.get("ecosystem", "unknown") != "unknown":
            try:
                # Create a temporary file to use existing extraction logic
                temp_file_path = f"/tmp/{file_info['name']}"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
                
                # Extract packages using existing logic
                packages = extract_packages_from_file(temp_file_path)
                
                # Add metadata about source file
                for package in packages:
                    package.metadata.update({
                        "source_file": file_info["path"],
                        "source_repository": f"{owner}/{repo}",
                        "file_sha": file_info.get("sha"),
                        "file_size": file_info.get("size")
                    })
                
                all_packages.extend([pkg.to_dict() for pkg in packages])
                
                # Clean up temp file
                Path(temp_file_path).unlink(missing_ok=True)
            
            except Exception as e:
                logger.warning(f"Failed to extract packages from {file_info['path']}: {e}")
    
    # Generate SBOM using existing function
    source_info = {
        "type": "github_repository",
        "repository": f"{owner}/{repo}",
        "url": f"https://github.com/{owner}/{repo}",
        "fetched_at": datetime.now().isoformat()
    }
    
    sbom = generate_sbom_from_packages(all_packages, source_info)
    
    # Validate SBOM structure
    is_valid, errors = validate_sbom_structure(sbom)
    if not is_valid:
        logger.warning(f"Generated SBOM has validation errors: {errors}")
        sbom["validation_errors"] = errors
    
    return sbom

def fetch_repository_security_advisories(owner: str, repo: str, client: GitHubAPIClient) -> List[Dict[str, Any]]:
    """
    Fetch security advisories published by the repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        client: GitHubAPIClient instance
    
    Returns:
        List of security advisories
    """
    try:
        advisories_response = client._make_request("GET", f"repos/{owner}/{repo}/security-advisories")
        if not advisories_response.is_success():
            logger.warning(f"Failed to fetch security advisories for {owner}/{repo}: {advisories_response.error.message}")
            return []
        return advisories_response.get_data()
    except Exception as e:
        logger.warning(f"Failed to fetch security advisories for {owner}/{repo}: {e}")
        return []

def analyze_repository_for_supply_chain_risks(repo_data: Dict[str, Any]) -> List[SecurityFinding]:
    """
    Analyze repository data for supply chain security risks.
    
    Args:
        repo_data: Repository data from fetch_repository_data
    
    Returns:
        List of security findings
    """
    findings = []
    
    # Analyze Dependabot alerts
    dependabot_alerts = repo_data.get("dependabot_alerts", [])
    for alert in dependabot_alerts:
        if alert.get("state") == "open":
            finding = SecurityFinding(
                package=alert.get("dependency", "unknown"),
                version="*",
                finding_type="dependabot_alert",
                severity=alert.get("security_advisory", {}).get("severity", "medium").lower(),
                confidence=0.9,
                evidence=[
                    f"Dependabot alert #{alert.get('number')}",
                    f"GHSA ID: {alert.get('security_advisory', {}).get('ghsa_id')}",
                    f"Summary: {alert.get('security_advisory', {}).get('summary')}"
                ],
                recommendations=[
                    "Update to a patched version",
                    "Review the security advisory for details",
                    "Consider alternative packages if no fix is available"
                ],
                source="github_dependabot"
            )
            findings.append(finding)
    
    # Analyze workflow runs for suspicious activity
    workflow_runs = repo_data.get("workflow_runs", [])
    failed_runs = [run for run in workflow_runs if run.get("conclusion") == "failure"]
    
    if len(failed_runs) > len(workflow_runs) * 0.5:  # More than 50% failure rate
        finding = SecurityFinding(
            package="ci_cd_pipeline",
            version="*",
            finding_type="ci_cd_anomaly",
            severity="medium",
            confidence=0.6,
            evidence=[
                f"High failure rate in CI/CD: {len(failed_runs)}/{len(workflow_runs)} runs failed",
                "This could indicate supply chain attacks or compromised dependencies"
            ],
            recommendations=[
                "Review failed workflow logs for suspicious activity",
                "Check for unexpected dependency changes",
                "Verify integrity of build processes"
            ],
            source="github_workflow_analysis"
        )
        findings.append(finding)
    
    return findings

def save_repository_data(repo_data: Dict[str, Any], output_dir: str = None) -> str:
    """
    Save repository data to JSON file.
    
    Args:
        repo_data: Repository data to save
        output_dir: Output directory (defaults to config.OUTPUT_DIRECTORY)
    
    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIRECTORY
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    repo_name = repo_data["repository"]["full_name"].replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"github_analysis_{repo_name}_{timestamp}.json"
    
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(repo_data, f, indent=2, default=str)
    
    logger.info(f"Repository data saved to {file_path}")
    return str(file_path)