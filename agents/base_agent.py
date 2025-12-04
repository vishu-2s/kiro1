"""
Base agent class for the multi-agent security analysis system.

This module provides the SecurityAgent base class that all specialized agents
inherit from. It handles LLM configuration, tool registration, and common
agent functionality.
"""

import os
from typing import Dict, List, Callable, Optional, Any
from dotenv import load_dotenv
from agents.types import AgentResult, SharedContext, AgentStatus

# Load environment variables
load_dotenv()


class SecurityAgent:
    """
    Base class for all security analysis agents.
    
    This class provides common functionality for agents including:
    - LLM configuration from .env file
    - Tool registration and management
    - Error handling and retry logic
    - Result formatting
    
    All specialized agents (Vulnerability, Reputation, Code, etc.) inherit from this class.
    """
    
    def __init__(self, name: str, system_message: str, tools: Optional[List[Callable]] = None):
        """
        Initialize a security agent.
        
        Args:
            name: Unique name for this agent
            system_message: System message defining the agent's role and capabilities
            tools: List of tool functions this agent can use
        """
        self.name = name
        self.system_message = system_message
        self.tools = tools or []
        
        # Load LLM configuration from .env
        self.llm_config = self._load_llm_config()
        
        # Agent state
        self.conversation_history: List[Dict[str, Any]] = []
        
    def _load_llm_config(self) -> Dict[str, Any]:
        """
        Load LLM configuration from environment variables.
        
        Returns:
            Dictionary with LLM configuration parameters
        """
        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.1")),
            "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "4096")),
            "timeout": int(os.getenv("AGENT_TIMEOUT_SECONDS", "120")),
            "cache_seed": int(os.getenv("AUTOGEN_CACHE_SEED", "42"))
        }
    
    def register_tools(self) -> None:
        """
        Register tools with the agent.
        
        This method should be called after initialization to make tools
        available to the agent during execution.
        """
        # Tool registration will be implemented when we integrate AutoGen
        # For now, this is a placeholder
        pass
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform analysis based on the shared context.
        
        This is the main entry point for agent execution. Subclasses must
        implement this method to provide their specific analysis logic.
        
        Args:
            context: Shared context with findings and data from previous agents
            timeout: Optional timeout override (uses config default if not provided)
        
        Returns:
            Dictionary with analysis results
        
        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError(f"Agent {self.name} must implement analyze() method")
    
    def _create_agent_result(
        self,
        success: bool,
        data: Dict[str, Any],
        error: Optional[str] = None,
        duration: float = 0.0,
        confidence: float = 1.0
    ) -> AgentResult:
        """
        Create an AgentResult object.
        
        Args:
            success: Whether the analysis succeeded
            data: Analysis results
            error: Error message if failed
            duration: Execution time in seconds
            confidence: Confidence score (0.0-1.0)
        
        Returns:
            AgentResult object
        """
        return AgentResult(
            agent_name=self.name,
            success=success,
            data=data,
            error=error,
            duration_seconds=duration,
            confidence=confidence
        )
    
    def _validate_context(self, context: SharedContext) -> bool:
        """
        Validate that the shared context has required data.
        
        Args:
            context: Shared context to validate
        
        Returns:
            True if context is valid, False otherwise
        """
        if not isinstance(context, SharedContext):
            return False
        
        if not context.packages:
            return False
        
        return True
    
    def _get_packages_to_analyze(self, context: SharedContext) -> List[str]:
        """
        Get list of packages to analyze from context.
        
        Args:
            context: Shared context
        
        Returns:
            List of package names
        """
        return context.packages
    
    def _format_error_result(self, error_msg: str, duration: float = 0.0) -> Dict[str, Any]:
        """
        Format an error result when analysis fails.
        
        Args:
            error_msg: Error message
            duration: Execution time before failure
        
        Returns:
            Dictionary with error information
        """
        return {
            "packages": [],
            "error": error_msg,
            "success": False,
            "duration_seconds": duration
        }
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message from this agent.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{level}] {self.name}: {message}")


class MockAgent(SecurityAgent):
    """
    Mock agent for testing purposes.
    
    This agent returns predefined results and is used for testing
    the orchestrator without requiring actual LLM calls.
    """
    
    def __init__(self, name: str, mock_data: Optional[Dict[str, Any]] = None):
        """
        Initialize mock agent.
        
        Args:
            name: Agent name
            mock_data: Predefined data to return
        """
        super().__init__(
            name=name,
            system_message="Mock agent for testing",
            tools=[]
        )
        self.mock_data = mock_data or {"packages": []}
    
    def analyze(self, context: SharedContext, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Return mock data.
        
        Args:
            context: Shared context (not used)
            timeout: Timeout (not used)
        
        Returns:
            Mock data
        """
        return self.mock_data
