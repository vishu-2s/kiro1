"""
Property-based tests for external API integration layer.

**Feature: multi-agent-security, Property 19: External API Integration**
**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

**Feature: multi-agent-security, Property 20: API Response Processing**
**Validates: Requirements 8.5**
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any, Optional
import requests
import string

from tools.api_integration import (
    APIErrorType,
    APIError,
    RateLimitInfo,
    APIResponse,
    RateLimiter,
    BaseAPIClient,
    GitHubAPIClient,
    OSVAPIClient,
    OpenAIAPIClient,
    APIIntegrationManager,
    retry_on_failure,
    api_manager
)


# Strategies for property-based testing
api_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=10,
    max_size=100
)

http_status_strategy = st.integers(min_value=200, max_value=599)

json_data_strategy = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100)
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=20), children, max_size=5)
    ),
    max_leaves=10
)

error_message_strategy = st.text(min_size=1, max_size=200)

rate_limit_strategy = st.builds(
    RateLimitInfo,
    requests_remaining=st.integers(min_value=0, max_value=5000),
    requests_limit=st.integers(min_value=1, max_value=5000),
    reset_time=st.datetimes(min_value=datetime.now(), max_value=datetime.now() + timedelta(hours=1)),
    retry_after=st.one_of(st.none(), st.integers(min_value=1, max_value=3600))
)


class TestExternalAPIIntegration:
    """Property-based tests for external API integration."""

    @settings(deadline=1000)  # Allow up to 1 second for this test
    @given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=60))
    def test_rate_limiter_consistency(self, max_requests: int, time_window: int):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any API call to OSV, GitHub, or OpenAI, the system should handle
        authentication, rate limiting, and error conditions appropriately.
        """
        rate_limiter = RateLimiter(max_requests, time_window)
        
        # Property: Initially should allow requests
        assert rate_limiter.can_make_request(), "Rate limiter should initially allow requests"
        
        # Property: Should track requests correctly
        requests_made = 0
        while rate_limiter.can_make_request() and requests_made < max_requests:
            rate_limiter.record_request()
            requests_made += 1
        
        # Property: Should not exceed max requests
        assert requests_made <= max_requests, f"Should not exceed max requests: {requests_made} > {max_requests}"
        
        # Property: Should block requests when limit reached
        if requests_made == max_requests:
            assert not rate_limiter.can_make_request(), "Should block requests when limit reached"
        
        # Property: Wait time should be reasonable
        wait_time = rate_limiter.wait_time()
        assert 0 <= wait_time <= time_window, f"Wait time should be between 0 and {time_window}, got {wait_time}"

    @given(api_key_strategy)
    def test_github_client_initialization_consistency(self, api_key: str):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any GitHub API authentication, the client should initialize
        consistently with proper headers and configuration.
        """
        assume(api_key.strip() != "")
        
        client = GitHubAPIClient(token=api_key)
        
        # Property: Should store token correctly
        assert client.token == api_key, "Client should store provided token"
        
        # Property: Should have proper base URL
        assert client.base_url == "https://api.github.com", "Client should have correct GitHub API base URL"
        
        # Property: Should have rate limiter configured
        assert client.rate_limiter is not None, "Client should have rate limiter"
        assert client.rate_limiter.max_requests > 0, "Rate limiter should have positive max requests"
        
        # Property: Should have proper authentication headers
        headers = client._get_auth_headers()
        assert "Authorization" in headers, "Should include Authorization header"
        assert headers["Authorization"] == f"token {api_key}", "Authorization header should be correct"
        assert "Accept" in headers, "Should include Accept header"
        assert "User-Agent" in headers, "Should include User-Agent header"

    def test_github_client_no_token_initialization(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any GitHub API client without token, it should initialize
        with appropriate defaults and warnings.
        """
        with patch('tools.api_integration.config.GITHUB_TOKEN', None):
            client = GitHubAPIClient()
            
            # Property: Should handle missing token gracefully
            assert client.token is None, "Client should have no token when none provided"
            
            # Property: Should still have proper headers (without auth)
            headers = client._get_auth_headers()
            assert "Accept" in headers, "Should include Accept header even without token"
            assert "User-Agent" in headers, "Should include User-Agent header even without token"
            assert "Authorization" not in headers, "Should not include Authorization header without token"

    @given(api_key_strategy)
    def test_openai_client_initialization_consistency(self, api_key: str):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any OpenAI API authentication, the client should initialize
        consistently with proper configuration.
        """
        assume(api_key.strip() != "")
        
        client = OpenAIAPIClient(api_key=api_key)
        
        # Property: Should store API key correctly
        assert client.api_key == api_key, "Client should store provided API key"
        
        # Property: Should have proper base URL
        assert client.base_url == "https://api.openai.com", "Client should have correct OpenAI API base URL"
        
        # Property: Should have rate limiter configured
        assert client.rate_limiter is not None, "Client should have rate limiter"
        
        # Property: Should have proper authentication headers
        headers = client._get_auth_headers()
        assert "Authorization" in headers, "Should include Authorization header"
        assert headers["Authorization"] == f"Bearer {api_key}", "Authorization header should be correct"
        assert "Content-Type" in headers, "Should include Content-Type header"

    def test_openai_client_missing_key_error(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any OpenAI API client without API key, it should raise
        appropriate error.
        """
        with patch('tools.api_integration.config.OPENAI_API_KEY', ""):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIAPIClient()

    def test_osv_client_initialization_consistency(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any OSV API client, it should initialize consistently
        without requiring authentication.
        """
        client = OSVAPIClient()
        
        # Property: Should have proper base URL
        assert client.base_url.startswith("https://"), "OSV client should use HTTPS"
        
        # Property: Should have rate limiter configured
        assert client.rate_limiter is not None, "Client should have rate limiter"
        
        # Property: Should have proper headers (no auth required)
        headers = client._get_auth_headers()
        assert "Content-Type" in headers, "Should include Content-Type header"
        assert "User-Agent" in headers, "Should include User-Agent header"
        assert "Authorization" not in headers, "OSV API should not require Authorization header"

    @given(http_status_strategy, error_message_strategy)
    def test_api_error_handling_consistency(self, status_code: int, error_message: str):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any API error conditions, the system should handle them
        gracefully and categorize them appropriately.
        """
        assume(error_message.strip() != "")
        
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.headers = {}
        mock_response.content = b""
        mock_response.text = error_message
        
        # Test with GitHub client
        client = GitHubAPIClient(token="test-token")
        
        with patch.object(client.session, 'request', return_value=mock_response):
            response = client._make_request("GET", "test")
            
            # Property: Should return APIResponse object
            assert isinstance(response, APIResponse), "Should return APIResponse object"
            
            # Property: Success should match status code
            expected_success = status_code == 200  # Our implementation only considers 200 as success
            assert response.success == expected_success, f"Success should be {expected_success} for status {status_code}"
            
            # Property: Error should be present for non-success responses
            if not expected_success:
                assert response.error is not None, "Error should be present for non-success responses"
                assert isinstance(response.error, APIError), "Error should be APIError instance"
                
                # Property: Error type should be appropriate for status code
                if status_code == 401:
                    assert response.error.error_type == APIErrorType.AUTHENTICATION
                elif status_code == 403:
                    assert response.error.error_type in [APIErrorType.AUTHENTICATION, APIErrorType.RATE_LIMIT]
                elif status_code == 404:
                    assert response.error.error_type == APIErrorType.INVALID_REQUEST
                elif status_code == 429:
                    assert response.error.error_type == APIErrorType.RATE_LIMIT
                elif 500 <= status_code < 600:
                    assert response.error.error_type == APIErrorType.SERVER_ERROR

    @given(json_data_strategy)
    def test_api_response_processing_consistency(self, test_data: Any):
        """
        **Feature: multi-agent-security, Property 20: API Response Processing**
        
        For any API response, the system should parse and structure
        the data for agent consumption.
        """
        # Create successful mock response with JSON data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = json.dumps(test_data).encode() if test_data is not None else b""
        mock_response.json.return_value = test_data if test_data is not None else {}
        
        client = GitHubAPIClient(token="test-token")
        
        with patch.object(client.session, 'request', return_value=mock_response):
            response = client._make_request("GET", "test")
            
            # Property: Should successfully parse response
            assert response.success, "Should successfully parse valid JSON response"
            
            # Property: Data should match original
            if test_data is not None:
                assert response.data == test_data, "Parsed data should match original"
            else:
                assert response.data == {}, "Empty content should result in empty dict"
            
            # Property: Should be able to get data without exception
            try:
                retrieved_data = response.get_data()
                if test_data is not None:
                    assert retrieved_data == test_data, "Retrieved data should match original"
            except Exception as e:
                pytest.fail(f"get_data() should not raise exception for successful response: {e}")

    def test_api_response_processing_invalid_json(self):
        """
        **Feature: multi-agent-security, Property 20: API Response Processing**
        
        For any malformed JSON response, the system should handle
        it gracefully and provide fallback.
        """
        # Create mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b"invalid json content"
        mock_response.text = "invalid json content"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        client = GitHubAPIClient(token="test-token")
        
        with patch.object(client.session, 'request', return_value=mock_response):
            response = client._make_request("GET", "test")
            
            # Property: Should still be successful (fallback to text)
            assert response.success, "Should handle invalid JSON gracefully"
            
            # Property: Should fallback to text content
            assert response.data == "invalid json content", "Should fallback to text content for invalid JSON"

    @given(rate_limit_strategy)
    def test_rate_limit_parsing_consistency(self, rate_limit_info: RateLimitInfo):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any rate limit headers, the system should parse them
        consistently across different APIs.
        """
        # Test GitHub rate limit parsing
        github_client = GitHubAPIClient(token="test-token")
        
        # Create headers that match the rate limit info
        reset_timestamp = int(rate_limit_info.reset_time.timestamp())
        headers = {
            'X-RateLimit-Remaining': str(rate_limit_info.requests_remaining),
            'X-RateLimit-Limit': str(rate_limit_info.requests_limit),
            'X-RateLimit-Reset': str(reset_timestamp)
        }
        
        parsed_info = github_client._parse_rate_limit_headers(headers)
        
        # Property: Should parse rate limit info correctly
        assert parsed_info is not None, "Should parse valid rate limit headers"
        assert parsed_info.requests_remaining == rate_limit_info.requests_remaining
        assert parsed_info.requests_limit == rate_limit_info.requests_limit
        # Allow some tolerance for timestamp conversion
        time_diff = abs((parsed_info.reset_time - rate_limit_info.reset_time).total_seconds())
        assert time_diff < 2, "Reset time should be parsed correctly (within 2 seconds)"

    def test_rate_limit_parsing_invalid_headers(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any invalid or missing rate limit headers, the system
        should handle them gracefully.
        """
        github_client = GitHubAPIClient(token="test-token")
        
        # Test with missing headers
        parsed_info = github_client._parse_rate_limit_headers({})
        # GitHub client provides defaults for missing headers
        if parsed_info is not None:
            assert parsed_info.requests_remaining >= 0, "Should have non-negative remaining requests"
        # It's acceptable for the client to provide defaults or return None
        
        # Test with invalid values
        invalid_headers = {
            'X-RateLimit-Remaining': 'invalid',
            'X-RateLimit-Limit': 'also_invalid',
            'X-RateLimit-Reset': 'not_a_timestamp'
        }
        
        parsed_info = github_client._parse_rate_limit_headers(invalid_headers)
        assert parsed_info is None, "Should return None for invalid header values"

    def test_retry_mechanism_consistency(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any retryable API errors, the system should implement
        consistent retry logic with exponential backoff.
        """
        retry_count = 0
        
        @retry_on_failure(max_retries=3, backoff_factor=0.1)  # Fast backoff for testing
        def failing_function():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                return APIResponse(
                    success=False,
                    error=APIError(APIErrorType.NETWORK, "Network error")
                )
            return APIResponse(success=True, data={"success": True})
        
        start_time = time.time()
        result = failing_function()
        end_time = time.time()
        
        # Property: Should eventually succeed after retries
        assert result.success, "Should succeed after retries"
        assert result.data == {"success": True}, "Should return correct data"
        
        # Property: Should have made expected number of attempts
        assert retry_count == 3, f"Should have made 3 attempts, made {retry_count}"
        
        # Property: Should have taken time for backoff (at least some delay)
        elapsed_time = end_time - start_time
        assert elapsed_time > 0.1, "Should have taken time for backoff delays"

    def test_retry_mechanism_non_retryable_errors(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any non-retryable API errors, the system should not
        retry and return immediately.
        """
        call_count = 0
        
        @retry_on_failure(max_retries=3)
        def auth_failing_function():
            nonlocal call_count
            call_count += 1
            return APIResponse(
                success=False,
                error=APIError(APIErrorType.AUTHENTICATION, "Auth failed")
            )
        
        result = auth_failing_function()
        
        # Property: Should not retry authentication errors
        assert not result.success, "Should fail for auth errors"
        assert call_count == 1, "Should not retry authentication errors"
        assert result.error.error_type == APIErrorType.AUTHENTICATION

    def test_api_integration_manager_initialization(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any API integration manager, it should initialize all
        clients consistently and handle missing configurations.
        """
        manager = APIIntegrationManager()
        
        # Property: Should attempt to initialize all clients
        # Note: Some may be None if configuration is missing, which is acceptable
        assert hasattr(manager, 'github_client'), "Should have github_client attribute"
        assert hasattr(manager, 'osv_client'), "Should have osv_client attribute"
        assert hasattr(manager, 'openai_client'), "Should have openai_client attribute"
        
        # Property: OSV client should always be available (no auth required)
        assert manager.osv_client is not None, "OSV client should always be available"
        
        # Property: Should provide getter methods
        assert callable(manager.get_github_client), "Should have get_github_client method"
        assert callable(manager.get_osv_client), "Should have get_osv_client method"
        assert callable(manager.get_openai_client), "Should have get_openai_client method"

    def test_api_integration_manager_health_check(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any API integration manager, health check should return
        consistent status for all configured APIs.
        """
        manager = APIIntegrationManager()
        
        # Mock successful responses for health checks
        with patch.object(manager, 'github_client') as mock_github, \
             patch.object(manager, 'osv_client') as mock_osv, \
             patch.object(manager, 'openai_client') as mock_openai:
            
            # Configure mocks
            if mock_github:
                mock_github._make_request.return_value = APIResponse(success=True, data={})
            if mock_osv:
                mock_osv.query_vulnerabilities.return_value = APIResponse(success=True, data={})
            if mock_openai:
                mock_openai.create_chat_completion.return_value = APIResponse(success=True, data={})
            
            health_status = manager.health_check()
            
            # Property: Should return dictionary with status for each API
            assert isinstance(health_status, dict), "Health check should return dictionary"
            
            expected_apis = ["github", "osv", "openai"]
            for api in expected_apis:
                assert api in health_status, f"Health status should include {api}"
                assert isinstance(health_status[api], bool), f"Health status for {api} should be boolean"

    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=50))
    def test_osv_api_query_consistency(self, package_name: str, ecosystem: str):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any OSV API query, the system should format requests
        consistently and handle responses appropriately.
        """
        assume(package_name.strip() != "" and ecosystem.strip() != "")
        
        client = OSVAPIClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"vulns": []}
        
        with patch.object(client.session, 'request', return_value=mock_response) as mock_request:
            response = client.query_vulnerabilities(package_name, ecosystem)
            
            # Property: Should make POST request to correct endpoint
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.kwargs['method'] == 'POST', "Should make POST request"
            assert 'v1/query' in call_args.kwargs['url'], "Should call query endpoint"
            
            # Property: Should include package and ecosystem in payload
            json_payload = call_args.kwargs['json']
            assert 'package' in json_payload, "Should include package in payload"
            assert json_payload['package']['name'] == package_name, "Should include correct package name"
            assert json_payload['package']['ecosystem'] == ecosystem, "Should include correct ecosystem"
            
            # Property: Should return successful response
            assert response.success, "Should return successful response for valid query"

    def test_openai_api_chat_completion_consistency(self):
        """
        **Feature: multi-agent-security, Property 20: API Response Processing**
        
        For any OpenAI chat completion request, the system should
        format requests consistently and parse responses correctly.
        """
        client = OpenAIAPIClient(api_key="test-key")
        
        test_messages = [
            {"role": "user", "content": "Test message"}
        ]
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    }
                }
            ]
        }
        
        with patch.object(client.session, 'request', return_value=mock_response) as mock_request:
            response = client.create_chat_completion(test_messages)
            
            # Property: Should make POST request to correct endpoint
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.kwargs['method'] == 'POST', "Should make POST request"
            assert 'v1/chat/completions' in call_args.kwargs['url'], "Should call chat completions endpoint"
            
            # Property: Should include messages in payload
            json_payload = call_args.kwargs['json']
            assert 'messages' in json_payload, "Should include messages in payload"
            assert json_payload['messages'] == test_messages, "Should include correct messages"
            assert 'model' in json_payload, "Should include model in payload"
            
            # Property: Should return successful response
            assert response.success, "Should return successful response for valid request"
            assert response.data is not None, "Should return response data"

    @settings(max_examples=50, deadline=5000)  # Reduced examples for performance
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
    def test_api_error_resilience(self, error_messages: List[str]):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any sequence of API errors, the system should handle them
        gracefully without crashing or corrupting state.
        """
        assume(all(msg.strip() != "" for msg in error_messages))
        
        client = GitHubAPIClient(token="test-token")
        
        # Test various error conditions
        for i, error_msg in enumerate(error_messages):
            mock_response = Mock()
            mock_response.status_code = 500 + (i % 5)  # Various server errors
            mock_response.headers = {}
            mock_response.text = error_msg
            
            with patch.object(client.session, 'request', return_value=mock_response):
                response = client._make_request("GET", f"test/{i}")
                
                # Property: Should handle all errors gracefully
                assert isinstance(response, APIResponse), "Should return APIResponse for all errors"
                assert not response.success, "Should indicate failure for server errors"
                assert response.error is not None, "Should include error information"
                assert isinstance(response.error.message, str), "Error message should be string"
                assert len(response.error.message) > 0, "Error message should not be empty"

    def test_concurrent_api_requests_safety(self):
        """
        **Feature: multi-agent-security, Property 19: External API Integration**
        
        For any concurrent API requests, the rate limiter and clients
        should handle them safely without race conditions.
        """
        import threading
        import queue
        
        rate_limiter = RateLimiter(max_requests=5, time_window=1)
        results = queue.Queue()
        
        def make_request(request_id):
            try:
                can_make = rate_limiter.can_make_request()
                if can_make:
                    rate_limiter.record_request()
                results.put((request_id, can_make, None))
            except Exception as e:
                results.put((request_id, False, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        successful_requests = 0
        errors = []
        
        while not results.empty():
            request_id, success, error = results.get()
            if error:
                errors.append(error)
            elif success:
                successful_requests += 1
        
        # Property: Should not have any errors from concurrent access
        assert len(errors) == 0, f"Should not have errors from concurrent access: {errors}"
        
        # Property: Should respect rate limits even with concurrent access
        assert successful_requests <= 5, f"Should not exceed rate limit even with concurrent requests: {successful_requests}"