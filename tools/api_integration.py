"""
External API integration layer for Multi-Agent Security Analysis System.

This module provides comprehensive error handling, rate limiting, authentication,
and retry mechanisms for all external APIs (OSV, GitHub, OpenAI).
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from functools import wraps

from config import config

logger = logging.getLogger(__name__)


class APIErrorType(Enum):
    """Types of API errors."""
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


@dataclass
class APIError:
    """Represents an API error with context."""
    error_type: APIErrorType
    message: str
    status_code: Optional[int] = None
    retry_after: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    requests_remaining: int
    requests_limit: int
    reset_time: datetime
    retry_after: Optional[int] = None


class APIResponse:
    """Wrapper for API responses with error handling."""
    
    def __init__(self, success: bool, data: Optional[Any] = None, 
                 error: Optional[APIError] = None, rate_limit: Optional[RateLimitInfo] = None):
        self.success = success
        self.data = data
        self.error = error
        self.rate_limit = rate_limit
        self.timestamp = datetime.now()
    
    def is_success(self) -> bool:
        """Check if the API call was successful."""
        return self.success
    
    def get_data(self) -> Any:
        """Get response data, raising exception if error occurred."""
        if not self.success:
            raise Exception(f"API call failed: {self.error.message if self.error else 'Unknown error'}")
        return self.data


class RateLimiter:
    """Thread-safe rate limiter for API calls."""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits."""
        with self.lock:
            now = datetime.now()
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if (now - req_time).total_seconds() < self.time_window]
            
            return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record that a request was made."""
        with self.lock:
            self.requests.append(datetime.now())
    
    def wait_time(self) -> int:
        """Get the time to wait before next request can be made."""
        with self.lock:
            if len(self.requests) < self.max_requests:
                return 0
            
            oldest_request = min(self.requests)
            wait_time = self.time_window - (datetime.now() - oldest_request).total_seconds()
            return max(0, int(wait_time))


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0, 
                    retry_on_errors: List[APIErrorType] = None):
    """Decorator for retrying API calls on specific errors."""
    if retry_on_errors is None:
        retry_on_errors = [APIErrorType.NETWORK, APIErrorType.TIMEOUT, APIErrorType.SERVER_ERROR]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # If result is APIResponse and failed with retryable error
                    if isinstance(result, APIResponse) and not result.success:
                        if result.error and result.error.error_type in retry_on_errors:
                            last_error = result.error
                            if attempt < max_retries:
                                wait_time = backoff_factor * (2 ** attempt)
                                logger.info(f"Retrying API call in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                    
                    return result
                    
                except Exception as e:
                    last_error = APIError(APIErrorType.UNKNOWN, str(e))
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.info(f"Retrying API call in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    raise
            
            # If we get here, all retries failed
            if isinstance(last_error, APIError):
                return APIResponse(success=False, error=last_error)
            else:
                return APIResponse(success=False, error=APIError(APIErrorType.UNKNOWN, "Max retries exceeded"))
        
        return wrapper
    return decorator


class BaseAPIClient(ABC):
    """Base class for API clients with common functionality."""
    
    def __init__(self, base_url: str, timeout: int = 30, rate_limiter: Optional[RateLimiter] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limiter = rate_limiter
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy for network-level retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        pass
    
    @abstractmethod
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse rate limit information from response headers."""
        pass
    
    def _wait_for_rate_limit(self):
        """Wait if rate limiter indicates we should."""
        if self.rate_limiter:
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time} seconds")
                time.sleep(wait_time)
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> APIResponse:
        """
        Make an authenticated API request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON data for POST/PUT requests
            headers: Additional headers
        
        Returns:
            APIResponse object
        """
        # Check rate limiter
        self._wait_for_rate_limit()
        
        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        try:
            # Record request for rate limiting
            if self.rate_limiter:
                self.rate_limiter.record_request()
            
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout
            )
            
            # Parse rate limit info
            rate_limit = self._parse_rate_limit_headers(dict(response.headers))
            
            # Handle different status codes
            if response.status_code == 200:
                try:
                    data = response.json() if response.content else {}
                    return APIResponse(success=True, data=data, rate_limit=rate_limit)
                except json.JSONDecodeError:
                    return APIResponse(success=True, data=response.text, rate_limit=rate_limit)
            
            elif response.status_code == 401:
                error = APIError(
                    error_type=APIErrorType.AUTHENTICATION,
                    message="Authentication failed - check API credentials",
                    status_code=response.status_code
                )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
            
            elif response.status_code == 403:
                # Could be rate limit or permission issue
                if rate_limit and rate_limit.requests_remaining == 0:
                    error = APIError(
                        error_type=APIErrorType.RATE_LIMIT,
                        message=f"Rate limit exceeded. Reset at {rate_limit.reset_time}",
                        status_code=response.status_code,
                        retry_after=rate_limit.retry_after
                    )
                else:
                    error = APIError(
                        error_type=APIErrorType.AUTHENTICATION,
                        message="Access forbidden - insufficient permissions",
                        status_code=response.status_code
                    )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
            
            elif response.status_code == 404:
                error = APIError(
                    error_type=APIErrorType.INVALID_REQUEST,
                    message="Resource not found",
                    status_code=response.status_code
                )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
            
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                error = APIError(
                    error_type=APIErrorType.RATE_LIMIT,
                    message=f"Rate limit exceeded. Retry after {retry_after} seconds",
                    status_code=response.status_code,
                    retry_after=retry_after
                )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
            
            elif 500 <= response.status_code < 600:
                error = APIError(
                    error_type=APIErrorType.SERVER_ERROR,
                    message=f"Server error: {response.status_code}",
                    status_code=response.status_code
                )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
            
            else:
                error = APIError(
                    error_type=APIErrorType.UNKNOWN,
                    message=f"Unexpected status code: {response.status_code}",
                    status_code=response.status_code,
                    response_data=response.text
                )
                return APIResponse(success=False, error=error, rate_limit=rate_limit)
        
        except requests.exceptions.Timeout:
            error = APIError(
                error_type=APIErrorType.TIMEOUT,
                message=f"Request timed out after {self.timeout} seconds"
            )
            return APIResponse(success=False, error=error)
        
        except requests.exceptions.ConnectionError as e:
            error = APIError(
                error_type=APIErrorType.NETWORK,
                message=f"Network connection error: {str(e)}"
            )
            return APIResponse(success=False, error=error)
        
        except requests.exceptions.RequestException as e:
            error = APIError(
                error_type=APIErrorType.NETWORK,
                message=f"Request failed: {str(e)}"
            )
            return APIResponse(success=False, error=error)
        
        except Exception as e:
            error = APIError(
                error_type=APIErrorType.UNKNOWN,
                message=f"Unexpected error: {str(e)}"
            )
            return APIResponse(success=False, error=error)


class GitHubAPIClient(BaseAPIClient):
    """GitHub API client with comprehensive error handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or config.GITHUB_TOKEN
        # GitHub allows 5000 requests per hour for authenticated users
        rate_limiter = RateLimiter(max_requests=4500, time_window=3600)  # Conservative limit
        super().__init__(
            base_url="https://api.github.com",
            timeout=30,
            rate_limiter=rate_limiter
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get GitHub authentication headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Multi-Agent-Security-Analysis-System/1.0"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        return headers
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse GitHub rate limit headers."""
        try:
            remaining = int(headers.get('X-RateLimit-Remaining', 0))
            limit = int(headers.get('X-RateLimit-Limit', 60))
            reset_timestamp = int(headers.get('X-RateLimit-Reset', 0))
            reset_time = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else datetime.now()
            
            return RateLimitInfo(
                requests_remaining=remaining,
                requests_limit=limit,
                reset_time=reset_time
            )
        except (ValueError, TypeError):
            return None
    
    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def get_repository(self, owner: str, repo: str) -> APIResponse:
        """Get repository information."""
        return self._make_request("GET", f"repos/{owner}/{repo}")
    
    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> APIResponse:
        """Get repository contents."""
        return self._make_request("GET", f"repos/{owner}/{repo}/contents/{path}")
    
    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def get_dependabot_alerts(self, owner: str, repo: str) -> APIResponse:
        """Get Dependabot alerts for repository."""
        return self._make_request("GET", f"repos/{owner}/{repo}/dependabot/alerts")
    
    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def get_workflow_runs(self, owner: str, repo: str, params: Optional[Dict] = None) -> APIResponse:
        """Get workflow runs for repository."""
        return self._make_request("GET", f"repos/{owner}/{repo}/actions/runs", params=params)


class OSVAPIClient(BaseAPIClient):
    """OSV API client with comprehensive error handling."""
    
    def __init__(self):
        # OSV API doesn't have strict rate limits, but we'll be conservative
        rate_limiter = RateLimiter(max_requests=100, time_window=60)
        super().__init__(
            base_url=config.OSV_API_BASE_URL,
            timeout=config.OSV_API_TIMEOUT,
            rate_limiter=rate_limiter
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """OSV API doesn't require authentication."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "Multi-Agent-Security-Analysis-System/1.0"
        }
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """OSV API doesn't provide rate limit headers."""
        return None
    
    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def query_vulnerabilities(self, package: str, ecosystem: str, version: Optional[str] = None) -> APIResponse:
        """Query vulnerabilities for a specific package."""
        payload = {
            "package": {
                "name": package,
                "ecosystem": ecosystem
            }
        }
        
        if version:
            payload["version"] = version
        
        return self._make_request("POST", "v1/query", json_data=payload)
    
    @retry_on_failure(max_retries=3, backoff_factor=2.0)
    def batch_query_vulnerabilities(self, queries: List[Dict[str, Any]]) -> APIResponse:
        """Batch query vulnerabilities for multiple packages."""
        payload = {"queries": queries}
        return self._make_request("POST", "v1/querybatch", json_data=payload)


class OpenAIAPIClient(BaseAPIClient):
    """OpenAI API client with comprehensive error handling."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # OpenAI has different rate limits based on model and tier
        # Using conservative limits for GPT-4
        rate_limiter = RateLimiter(max_requests=500, time_window=60)
        super().__init__(
            base_url="https://api.openai.com",
            timeout=config.AGENT_TIMEOUT_SECONDS,
            rate_limiter=rate_limiter
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get OpenAI authentication headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse OpenAI rate limit headers."""
        try:
            remaining_requests = headers.get('x-ratelimit-remaining-requests')
            limit_requests = headers.get('x-ratelimit-limit-requests')
            reset_requests = headers.get('x-ratelimit-reset-requests')
            
            if remaining_requests and limit_requests:
                remaining = int(remaining_requests)
                limit = int(limit_requests)
                
                # Parse reset time (format: "1s", "2m", "1h")
                reset_time = datetime.now()
                if reset_requests:
                    try:
                        if reset_requests.endswith('s'):
                            seconds = int(reset_requests[:-1])
                            reset_time = datetime.now() + timedelta(seconds=seconds)
                        elif reset_requests.endswith('m'):
                            minutes = int(reset_requests[:-1])
                            reset_time = datetime.now() + timedelta(minutes=minutes)
                        elif reset_requests.endswith('h'):
                            hours = int(reset_requests[:-1])
                            reset_time = datetime.now() + timedelta(hours=hours)
                    except ValueError:
                        pass
                
                return RateLimitInfo(
                    requests_remaining=remaining,
                    requests_limit=limit,
                    reset_time=reset_time
                )
        except (ValueError, TypeError):
            pass
        
        return None
    
    @retry_on_failure(max_retries=3, backoff_factor=2.0)
    def create_chat_completion(self, messages: List[Dict[str, Any]], 
                             model: Optional[str] = None, **kwargs) -> APIResponse:
        """Create a chat completion."""
        payload = {
            "model": model or config.OPENAI_MODEL,
            "messages": messages,
            "temperature": kwargs.get("temperature", config.AGENT_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", config.AGENT_MAX_TOKENS),
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        }
        
        return self._make_request("POST", "v1/chat/completions", json_data=payload)
    
    @retry_on_failure(max_retries=3, backoff_factor=2.0)
    def create_vision_completion(self, messages: List[Dict[str, Any]], **kwargs) -> APIResponse:
        """Create a vision completion using GPT-4 Vision."""
        payload = {
            "model": config.OPENAI_VISION_MODEL,
            "messages": messages,
            "temperature": kwargs.get("temperature", config.AGENT_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", config.AGENT_MAX_TOKENS),
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        }
        
        return self._make_request("POST", "v1/chat/completions", json_data=payload)


class APIIntegrationManager:
    """Manager class for coordinating all API clients."""
    
    def __init__(self):
        self.github_client = None
        self.osv_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients with error handling."""
        try:
            self.github_client = GitHubAPIClient()
            logger.info("GitHub API client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize GitHub API client: {e}")
        
        try:
            self.osv_client = OSVAPIClient()
            logger.info("OSV API client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OSV API client: {e}")
        
        try:
            self.openai_client = OpenAIAPIClient()
            logger.info("OpenAI API client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI API client: {e}")
    
    def get_github_client(self) -> Optional[GitHubAPIClient]:
        """Get GitHub API client."""
        return self.github_client
    
    def get_osv_client(self) -> Optional[OSVAPIClient]:
        """Get OSV API client."""
        return self.osv_client
    
    def get_openai_client(self) -> Optional[OpenAIAPIClient]:
        """Get OpenAI API client."""
        return self.openai_client
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all API clients."""
        health_status = {}
        
        # Check GitHub API
        if self.github_client:
            try:
                response = self.github_client._make_request("GET", "rate_limit")
                health_status["github"] = response.is_success()
            except Exception:
                health_status["github"] = False
        else:
            health_status["github"] = False
        
        # Check OSV API
        if self.osv_client:
            try:
                # Simple test query
                response = self.osv_client.query_vulnerabilities("test", "npm")
                health_status["osv"] = True  # OSV returns 404 for non-existent packages, which is expected
            except Exception:
                health_status["osv"] = False
        else:
            health_status["osv"] = False
        
        # Check OpenAI API
        if self.openai_client:
            try:
                response = self.openai_client.create_chat_completion([
                    {"role": "user", "content": "Hello"}
                ])
                health_status["openai"] = response.is_success()
            except Exception:
                health_status["openai"] = False
        else:
            health_status["openai"] = False
        
        return health_status


# Global API manager instance
api_manager = APIIntegrationManager()