"""
Unit tests for the error handler module.

Tests comprehensive error handling, retry logic, graceful degradation,
and fallback data generation.
"""

import pytest
import time
from unittest.mock import Mock, patch

from agents.error_handler import (
    ErrorHandler,
    DegradationLevel,
    ErrorType
)
from agents.types import AgentResult, AgentStatus, SharedContext, Finding


class TestErrorHandler:
    """Test suite for ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler(max_retries=2, base_delay=0.1)
    
    def test_initialization(self):
        """Test error handler initialization."""
        assert self.error_handler.max_retries == 2
        assert self.error_handler.base_delay == 0.1
        assert len(self.error_handler.error_log) == 0
    
    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        error = Exception("Request timeout after 30 seconds")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.TIMEOUT
    
    def test_classify_rate_limit_error(self):
        """Test classification of rate limit errors."""
        error = Exception("Rate limit exceeded, please try again later")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.RATE_LIMIT
    
    def test_classify_connection_error(self):
        """Test classification of connection errors."""
        error = Exception("Connection refused")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.CONNECTION
    
    def test_classify_service_unavailable_error(self):
        """Test classification of service unavailable errors."""
        error = Exception("503 Service Unavailable")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.SERVICE_UNAVAILABLE
    
    def test_classify_authentication_error(self):
        """Test classification of authentication errors."""
        error = Exception("401 Unauthorized")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.AUTHENTICATION
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        error = Exception("Something went wrong")
        error_type = self.error_handler._classify_error(error)
        assert error_type == ErrorType.UNKNOWN
    
    def test_is_retryable_error_timeout(self):
        """Test that timeout errors are retryable."""
        error = Exception("Request timeout")
        assert self.error_handler._is_retryable_error(error) is True
    
    def test_is_retryable_error_rate_limit(self):
        """Test that rate limit errors are retryable."""
        error = Exception("Rate limit exceeded")
        assert self.error_handler._is_retryable_error(error) is True
    
    def test_is_retryable_error_connection(self):
        """Test that connection errors are retryable."""
        error = Exception("Connection error")
        assert self.error_handler._is_retryable_error(error) is True
    
    def test_is_not_retryable_error(self):
        """Test that some errors are not retryable."""
        error = Exception("Invalid API key")
        assert self.error_handler._is_retryable_error(error) is False
    
    def test_handle_required_agent_failure_without_retry(self):
        """Test handling required agent failure without retry function."""
        error = Exception("Agent failed")
        result = self.error_handler.handle_agent_failure(
            agent_name="vulnerability_analysis",
            error=error,
            required=True,
            retry_func=None
        )
        
        assert result.success is False
        assert result.agent_name == "vulnerability_analysis"
        assert result.status == AgentStatus.FAILED
        assert "packages" in result.data
        assert result.data["fallback"] is True
        assert "rule_based_fallback" in result.data["source"]
    
    def test_handle_optional_agent_failure(self):
        """Test handling optional agent failure."""
        error = Exception("Agent failed")
        result = self.error_handler.handle_agent_failure(
            agent_name="code_analysis",
            error=error,
            required=False,
            retry_func=None
        )
        
        assert result.success is False
        assert result.agent_name == "code_analysis"
        assert result.status == AgentStatus.SKIPPED
        assert result.data["skipped"] is True
    
    def test_handle_agent_failure_with_successful_retry(self):
        """Test handling agent failure with successful retry."""
        error = Exception("Timeout")
        
        # Mock retry function that succeeds
        retry_func = Mock(return_value=AgentResult(
            agent_name="reputation_analysis",
            success=True,
            data={"packages": []},
            duration_seconds=1.0,
            status=AgentStatus.SUCCESS
        ))
        
        result = self.error_handler.handle_agent_failure(
            agent_name="reputation_analysis",
            error=error,
            required=True,
            retry_func=retry_func
        )
        
        assert result.success is True
        assert retry_func.called
    
    def test_handle_agent_failure_with_failed_retry(self):
        """Test handling agent failure with failed retry."""
        error = Exception("Timeout")
        
        # Mock retry function that fails
        retry_func = Mock(side_effect=Exception("Still failing"))
        
        result = self.error_handler.handle_agent_failure(
            agent_name="reputation_analysis",
            error=error,
            required=True,
            retry_func=retry_func
        )
        
        assert result.success is False
        assert result.status == AgentStatus.FAILED
        assert retry_func.called
    
    def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        # Mock retry function that succeeds on second attempt
        call_count = [0]
        
        def retry_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Still failing")
            return AgentResult(
                agent_name="test_agent",
                success=True,
                data={},
                duration_seconds=1.0,
                status=AgentStatus.SUCCESS
            )
        
        start_time = time.time()
        result = self.error_handler._retry_with_backoff("test_agent", retry_func)
        duration = time.time() - start_time
        
        assert result is not None
        assert result.success is True
        assert call_count[0] == 2
        # Should have waited at least 0.1s (base delay)
        assert duration >= 0.1
    
    def test_retry_exhausted(self):
        """Test retry exhaustion."""
        # Mock retry function that always fails
        retry_func = Mock(side_effect=Exception("Always failing"))
        
        result = self.error_handler._retry_with_backoff("test_agent", retry_func)
        
        assert result is None
        assert retry_func.call_count == 2  # max_retries
    
    def test_get_fallback_data_vulnerability(self):
        """Test fallback data for vulnerability agent."""
        data = self.error_handler._get_fallback_data("vulnerability_analysis")
        
        assert "packages" in data
        assert data["source"] == "rule_based_fallback"
        assert data["fallback"] is True
    
    def test_get_fallback_data_reputation(self):
        """Test fallback data for reputation agent."""
        data = self.error_handler._get_fallback_data("reputation_analysis")
        
        assert "packages" in data
        assert data["source"] == "default_scores"
        assert data["fallback"] is True
    
    def test_get_fallback_data_code(self):
        """Test fallback data for code agent."""
        data = self.error_handler._get_fallback_data("code_analysis")
        
        assert "packages" in data
        assert data["source"] == "pattern_matching_only"
        assert data["fallback"] is True
    
    def test_get_fallback_data_supply_chain(self):
        """Test fallback data for supply chain agent."""
        data = self.error_handler._get_fallback_data("supply_chain_analysis")
        
        assert "packages" in data
        assert data["source"] == "basic_checks_only"
        assert data["fallback"] is True
    
    def test_format_user_friendly_error_timeout(self):
        """Test user-friendly error formatting for timeout."""
        error = Exception("Timeout")
        message = self.error_handler._format_user_friendly_error(
            "vulnerability_analysis",
            error,
            ErrorType.TIMEOUT
        )
        
        assert "timed out" in message.lower()
        assert "Vulnerability Analysis" in message
    
    def test_format_user_friendly_error_rate_limit(self):
        """Test user-friendly error formatting for rate limit."""
        error = Exception("Rate limit")
        message = self.error_handler._format_user_friendly_error(
            "reputation_analysis",
            error,
            ErrorType.RATE_LIMIT
        )
        
        assert "rate limit" in message.lower()
        assert "Reputation Analysis" in message
    
    def test_calculate_degradation_level_full(self):
        """Test degradation level calculation for full analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # All agents succeeded
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="code", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        
        level = self.error_handler.calculate_degradation_level(context)
        assert level == DegradationLevel.FULL
    
    def test_calculate_degradation_level_partial(self):
        """Test degradation level calculation for partial analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # 3 out of 4 agents succeeded (75%)
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="code", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="sc", success=False, data={}, status=AgentStatus.FAILED
        ))
        
        level = self.error_handler.calculate_degradation_level(context)
        assert level == DegradationLevel.PARTIAL
    
    def test_calculate_degradation_level_basic(self):
        """Test degradation level calculation for basic analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # 1 out of 2 agents succeeded (50%)
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=False, data={}, status=AgentStatus.FAILED
        ))
        
        level = self.error_handler.calculate_degradation_level(context)
        assert level == DegradationLevel.BASIC
    
    def test_calculate_degradation_level_minimal(self):
        """Test degradation level calculation for minimal analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # All agents failed
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=False, data={}, status=AgentStatus.FAILED
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=False, data={}, status=AgentStatus.FAILED
        ))
        
        level = self.error_handler.calculate_degradation_level(context)
        assert level == DegradationLevel.MINIMAL
    
    def test_calculate_confidence_full(self):
        """Test confidence calculation for full analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # All agents succeeded
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        
        confidence = self.error_handler._calculate_confidence(context)
        assert confidence == 0.95
    
    def test_calculate_confidence_partial(self):
        """Test confidence calculation for partial analysis."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        # 3 out of 4 agents succeeded (75% = PARTIAL)
        context.add_agent_result(AgentResult(
            agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="code", success=True, data={}, status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="sc", success=False, data={}, status=AgentStatus.FAILED
        ))
        
        confidence = self.error_handler._calculate_confidence(context)
        assert confidence == 0.75
    
    def test_get_degradation_metadata(self):
        """Test degradation metadata generation."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=[]
        )
        
        context.add_agent_result(AgentResult(
            agent_name="vulnerability_analysis",
            success=True,
            data={},
            status=AgentStatus.SUCCESS
        ))
        context.add_agent_result(AgentResult(
            agent_name="code_analysis",
            success=False,
            data={},
            status=AgentStatus.FAILED
        ))
        
        metadata = self.error_handler.get_degradation_metadata(context)
        
        assert "analysis_status" in metadata
        assert "confidence" in metadata
        assert "degradation_reason" in metadata
        assert "missing_analysis" in metadata
        assert "Code Analysis" in metadata["missing_analysis"]
        assert metadata["retry_recommended"] is True
    
    def test_handle_synthesis_failure(self):
        """Test synthesis failure handling."""
        context = SharedContext(
            initial_findings=[],
            dependency_graph={},
            packages=["package1", "package2"]
        )
        
        context.add_agent_result(AgentResult(
            agent_name="vulnerability_analysis",
            success=True,
            data={"packages": [{"name": "pkg1", "risk_level": "critical"}]},
            status=AgentStatus.SUCCESS
        ))
        
        error = Exception("Synthesis failed")
        report = self.error_handler.handle_synthesis_failure(context, error)
        
        assert "metadata" in report
        assert report["metadata"]["analysis_status"] == "degraded"
        assert "summary" in report
        assert report["summary"]["total_packages"] == 2
        assert "security_findings" in report
        assert "recommendations" in report
        assert "agent_insights" in report
    
    def test_error_log_tracking(self):
        """Test that errors are logged for reporting."""
        error = Exception("Test error")
        
        self.error_handler.handle_agent_failure(
            agent_name="test_agent",
            error=error,
            required=True
        )
        
        assert len(self.error_handler.error_log) == 1
        assert self.error_handler.error_log[0]["agent"] == "test_agent"
        assert "Test error" in self.error_handler.error_log[0]["error"]
    
    def test_clear_error_log(self):
        """Test clearing error log."""
        error = Exception("Test error")
        
        self.error_handler.handle_agent_failure(
            agent_name="test_agent",
            error=error,
            required=True
        )
        
        assert len(self.error_handler.error_log) == 1
        
        self.error_handler.clear_error_log()
        assert len(self.error_handler.error_log) == 0
    
    def test_get_error_summary(self):
        """Test error summary generation."""
        error1 = Exception("First error")
        error2 = Exception("Second error")
        
        self.error_handler.handle_agent_failure(
            agent_name="agent1",
            error=error1,
            required=True
        )
        self.error_handler.handle_agent_failure(
            agent_name="agent2",
            error=error2,
            required=False
        )
        
        summary = self.error_handler._get_error_summary()
        
        assert len(summary) == 2
        assert summary[0]["agent"] == "agent1"
        assert summary[1]["agent"] == "agent2"
        assert "First error" in summary[0]["error"]
        assert "Second error" in summary[1]["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
