"""
Example demonstrating comprehensive error handling and graceful degradation.

This example shows how the error handler manages various failure scenarios
and provides graceful degradation with user-friendly error messages.
"""

from agents.error_handler import ErrorHandler, DegradationLevel, ErrorType
from agents.types import AgentResult, AgentStatus, SharedContext, Finding


def example_1_required_agent_failure():
    """Example 1: Required agent failure with fallback data."""
    print("=" * 70)
    print("Example 1: Required Agent Failure with Fallback Data")
    print("=" * 70)
    
    error_handler = ErrorHandler(max_retries=2, base_delay=0.1)
    
    # Simulate a required agent failure
    error = Exception("Vulnerability API timeout after 30 seconds")
    result = error_handler.handle_agent_failure(
        agent_name="vulnerability_analysis",
        error=error,
        required=True,
        retry_func=None
    )
    
    print(f"\nAgent: {result.agent_name}")
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")
    print(f"Fallback Data: {result.data}")
    print()


def example_2_optional_agent_failure():
    """Example 2: Optional agent failure (skipped)."""
    print("=" * 70)
    print("Example 2: Optional Agent Failure (Skipped)")
    print("=" * 70)
    
    error_handler = ErrorHandler(max_retries=2, base_delay=0.1)
    
    # Simulate an optional agent failure
    error = Exception("Code analysis agent unavailable")
    result = error_handler.handle_agent_failure(
        agent_name="code_analysis",
        error=error,
        required=False,
        retry_func=None
    )
    
    print(f"\nAgent: {result.agent_name}")
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")
    print(f"Skipped: {result.data.get('skipped', False)}")
    print()


def example_3_successful_retry():
    """Example 3: Successful retry after transient error."""
    print("=" * 70)
    print("Example 3: Successful Retry After Transient Error")
    print("=" * 70)
    
    error_handler = ErrorHandler(max_retries=2, base_delay=0.1)
    
    # Simulate a retry function that succeeds on second attempt
    attempt_count = [0]
    
    def retry_func():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception("Rate limit exceeded, please retry")
        return AgentResult(
            agent_name="reputation_analysis",
            success=True,
            data={"packages": [{"name": "test-pkg", "reputation_score": 0.8}]},
            duration_seconds=1.5,
            status=AgentStatus.SUCCESS
        )
    
    # Simulate a retryable error
    error = Exception("Rate limit exceeded, please retry")
    result = error_handler.handle_agent_failure(
        agent_name="reputation_analysis",
        error=error,
        required=True,
        retry_func=retry_func
    )
    
    print(f"\nAgent: {result.agent_name}")
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Attempts: {attempt_count[0]}")
    print(f"Data: {result.data}")
    print()


def example_4_degradation_levels():
    """Example 4: Calculate degradation levels based on agent success."""
    print("=" * 70)
    print("Example 4: Degradation Levels")
    print("=" * 70)
    
    error_handler = ErrorHandler()
    
    # Scenario 1: Full analysis (100%)
    context1 = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[]
    )
    context1.add_agent_result(AgentResult(
        agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    context1.add_agent_result(AgentResult(
        agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    
    level1 = error_handler.calculate_degradation_level(context1)
    confidence1 = error_handler._calculate_confidence(context1)
    print(f"\nScenario 1: All agents succeeded")
    print(f"  Degradation Level: {level1.value}")
    print(f"  Confidence: {confidence1}")
    
    # Scenario 2: Partial analysis (75%)
    context2 = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[]
    )
    context2.add_agent_result(AgentResult(
        agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    context2.add_agent_result(AgentResult(
        agent_name="rep", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    context2.add_agent_result(AgentResult(
        agent_name="code", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    context2.add_agent_result(AgentResult(
        agent_name="sc", success=False, data={}, status=AgentStatus.FAILED
    ))
    
    level2 = error_handler.calculate_degradation_level(context2)
    confidence2 = error_handler._calculate_confidence(context2)
    print(f"\nScenario 2: 3 out of 4 agents succeeded")
    print(f"  Degradation Level: {level2.value}")
    print(f"  Confidence: {confidence2}")
    
    # Scenario 3: Basic analysis (50%)
    context3 = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[]
    )
    context3.add_agent_result(AgentResult(
        agent_name="vuln", success=True, data={}, status=AgentStatus.SUCCESS
    ))
    context3.add_agent_result(AgentResult(
        agent_name="rep", success=False, data={}, status=AgentStatus.FAILED
    ))
    
    level3 = error_handler.calculate_degradation_level(context3)
    confidence3 = error_handler._calculate_confidence(context3)
    print(f"\nScenario 3: 1 out of 2 agents succeeded")
    print(f"  Degradation Level: {level3.value}")
    print(f"  Confidence: {confidence3}")
    
    # Scenario 4: Minimal analysis (0%)
    context4 = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=[]
    )
    context4.add_agent_result(AgentResult(
        agent_name="vuln", success=False, data={}, status=AgentStatus.FAILED
    ))
    context4.add_agent_result(AgentResult(
        agent_name="rep", success=False, data={}, status=AgentStatus.FAILED
    ))
    
    level4 = error_handler.calculate_degradation_level(context4)
    confidence4 = error_handler._calculate_confidence(context4)
    print(f"\nScenario 4: All agents failed")
    print(f"  Degradation Level: {level4.value}")
    print(f"  Confidence: {confidence4}")
    print()


def example_5_synthesis_failure():
    """Example 5: Synthesis failure with fallback report."""
    print("=" * 70)
    print("Example 5: Synthesis Failure with Fallback Report")
    print("=" * 70)
    
    error_handler = ErrorHandler()
    
    # Create context with some successful agent results
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=["package1", "package2", "package3"]
    )
    
    context.add_agent_result(AgentResult(
        agent_name="vulnerability_analysis",
        success=True,
        data={
            "packages": [
                {"name": "pkg1", "risk_level": "critical"},
                {"name": "pkg2", "risk_level": "high"}
            ]
        },
        status=AgentStatus.SUCCESS
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="reputation_analysis",
        success=True,
        data={
            "packages": [
                {"name": "pkg1", "reputation_score": 0.2},
                {"name": "pkg2", "reputation_score": 0.5}
            ]
        },
        status=AgentStatus.SUCCESS
    ))
    
    # Simulate synthesis failure
    error = Exception("OpenAI API unavailable")
    report = error_handler.handle_synthesis_failure(context, error)
    
    print(f"\nFallback Report Generated:")
    print(f"  Analysis Status: {report['metadata']['analysis_status']}")
    print(f"  Total Packages: {report['summary']['total_packages']}")
    print(f"  Critical Findings: {report['summary']['critical_findings']}")
    print(f"  High Findings: {report['summary']['high_findings']}")
    print(f"  Confidence: {report['summary']['confidence']}")
    print(f"  Successful Agents: {report['agent_insights']['successful_agents']}")
    print(f"  Degradation Level: {report['agent_insights']['degradation_level']}")
    print()


def example_6_error_classification():
    """Example 6: Error classification and user-friendly messages."""
    print("=" * 70)
    print("Example 6: Error Classification and User-Friendly Messages")
    print("=" * 70)
    
    error_handler = ErrorHandler()
    
    errors = [
        ("Timeout", Exception("Request timeout after 30 seconds")),
        ("Rate Limit", Exception("429 Rate limit exceeded")),
        ("Connection", Exception("Connection refused by server")),
        ("Service Unavailable", Exception("503 Service temporarily unavailable")),
        ("Authentication", Exception("401 Unauthorized - invalid API key")),
        ("Unknown", Exception("Something unexpected happened"))
    ]
    
    for name, error in errors:
        error_type = error_handler._classify_error(error)
        is_retryable = error_handler._is_retryable_error(error)
        user_message = error_handler._format_user_friendly_error(
            "test_agent",
            error,
            error_type
        )
        
        print(f"\n{name}:")
        print(f"  Error Type: {error_type.value}")
        print(f"  Retryable: {is_retryable}")
        print(f"  User Message: {user_message}")
    print()


def example_7_degradation_metadata():
    """Example 7: Degradation metadata for report."""
    print("=" * 70)
    print("Example 7: Degradation Metadata for Report")
    print("=" * 70)
    
    error_handler = ErrorHandler()
    
    # Create context with mixed results
    context = SharedContext(
        initial_findings=[],
        dependency_graph={},
        packages=["pkg1", "pkg2"]
    )
    
    context.add_agent_result(AgentResult(
        agent_name="vulnerability_analysis",
        success=True,
        data={},
        status=AgentStatus.SUCCESS
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="reputation_analysis",
        success=False,
        data={},
        error="API timeout",
        status=AgentStatus.FAILED
    ))
    
    context.add_agent_result(AgentResult(
        agent_name="code_analysis",
        success=False,
        data={},
        error="Service unavailable",
        status=AgentStatus.SKIPPED
    ))
    
    # Get degradation metadata
    metadata = error_handler.get_degradation_metadata(context)
    
    print(f"\nDegradation Metadata:")
    print(f"  Analysis Status: {metadata['analysis_status']}")
    print(f"  Confidence: {metadata['confidence']}")
    print(f"  Degradation Reason: {metadata['degradation_reason']}")
    print(f"  Missing Analysis: {metadata['missing_analysis']}")
    print(f"  Retry Recommended: {metadata['retry_recommended']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ERROR HANDLING EXAMPLES")
    print("=" * 70 + "\n")
    
    example_1_required_agent_failure()
    example_2_optional_agent_failure()
    example_3_successful_retry()
    example_4_degradation_levels()
    example_5_synthesis_failure()
    example_6_error_classification()
    example_7_degradation_metadata()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
