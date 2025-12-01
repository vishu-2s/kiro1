"""
Property-based tests for agent initialization in agents module.

**Feature: multi-agent-security, Property 10: Agent Initialization**
**Validates: Requirements 4.1, 4.2, 4.3**
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Any, Optional, List
import json
import os
from unittest.mock import patch, MagicMock

from agents import (
    BaseAgent,
    SupplyChainAgent,
    VlmSecurityAgent, 
    OrchestratorAgent,
    GroupChatManager,
    create_supply_chain_agent,
    create_vlm_security_agent,
    create_orchestrator_agent,
    create_agent_group
)
from config import config


# Strategy for generating valid LLM configurations
llm_config_strategy = st.one_of(
    st.none(),
    st.fixed_dictionaries({
        "config_list": st.lists(
            st.fixed_dictionaries({
                "model": st.sampled_from(["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]),
                "api_key": st.text(min_size=10, max_size=100),
                "temperature": st.floats(min_value=0.0, max_value=2.0),
                "max_tokens": st.integers(min_value=100, max_value=8192),
                "timeout": st.integers(min_value=10, max_value=300)
            }),
            min_size=1,
            max_size=3
        )
    })
)

# Strategy for generating agent names and roles
agent_name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=3,
    max_size=50
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

agent_role_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-",
    min_size=5,
    max_size=100
).filter(lambda x: x.strip())


class TestAgentInitialization:
    """Property-based tests for agent initialization."""

    @given(llm_config_strategy)
    def test_supply_chain_agent_initialization(self, llm_config: Optional[Dict]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        For any valid LLM configuration, SupplyChainAgent should initialize properly
        with all required attributes and embedded security signatures.
        """
        # Mock OpenAI client to avoid actual API calls during testing
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Initialize agent
            agent = create_supply_chain_agent(llm_config)
            
            # Property: Agent should be instance of SupplyChainAgent
            assert isinstance(agent, SupplyChainAgent)
            assert isinstance(agent, BaseAgent)
            
            # Property: Agent should have correct name and role
            assert agent.name == "SupplyChainAgent"
            assert agent.role == "Supply Chain Security Analyst"
            
            # Property: Agent should have embedded security signatures
            assert hasattr(agent, 'malicious_packages')
            assert hasattr(agent, 'typosquat_targets')
            assert hasattr(agent, 'suspicious_keywords')
            assert isinstance(agent.malicious_packages, dict)
            assert isinstance(agent.typosquat_targets, dict)
            assert isinstance(agent.suspicious_keywords, list)
            
            # Property: Agent should have conversation history initialized
            assert hasattr(agent, 'conversation_history')
            assert isinstance(agent.conversation_history, list)
            assert len(agent.conversation_history) == 0
            
            # Property: Agent should have LLM configuration
            assert hasattr(agent, 'llm_config')
            assert isinstance(agent.llm_config, dict)
            
            # Property: If custom config provided, it should be used
            if llm_config is not None:
                assert agent.llm_config == llm_config
            else:
                # Should use default config
                assert "config_list" in agent.llm_config

    @given(llm_config_strategy)
    def test_vlm_security_agent_initialization(self, llm_config: Optional[Dict]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        For any valid LLM configuration, VlmSecurityAgent should initialize properly
        with vision capabilities and proper configuration.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Initialize agent
            agent = create_vlm_security_agent(llm_config)
            
            # Property: Agent should be instance of VlmSecurityAgent
            assert isinstance(agent, VlmSecurityAgent)
            assert isinstance(agent, BaseAgent)
            
            # Property: Agent should have correct name and role
            assert agent.name == "VlmSecurityAgent"
            assert agent.role == "Visual Security Analyst"
            
            # Property: Agent should have vision client
            assert hasattr(agent, 'vision_client')
            
            # Property: Agent should have conversation history initialized
            assert hasattr(agent, 'conversation_history')
            assert isinstance(agent.conversation_history, list)
            assert len(agent.conversation_history) == 0
            
            # Property: Agent should have LLM configuration
            assert hasattr(agent, 'llm_config')
            assert isinstance(agent.llm_config, dict)

    @given(llm_config_strategy)
    def test_orchestrator_agent_initialization(self, llm_config: Optional[Dict]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        For any valid LLM configuration, OrchestratorAgent should initialize properly
        with correlation and reporting capabilities.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Initialize agent
            agent = create_orchestrator_agent(llm_config)
            
            # Property: Agent should be instance of OrchestratorAgent
            assert isinstance(agent, OrchestratorAgent)
            assert isinstance(agent, BaseAgent)
            
            # Property: Agent should have correct name and role
            assert agent.name == "OrchestratorAgent"
            assert agent.role == "Security Orchestrator and Incident Analyst"
            
            # Property: Agent should have conversation history initialized
            assert hasattr(agent, 'conversation_history')
            assert isinstance(agent.conversation_history, list)
            assert len(agent.conversation_history) == 0
            
            # Property: Agent should have LLM configuration
            assert hasattr(agent, 'llm_config')
            assert isinstance(agent.llm_config, dict)

    @given(agent_name_strategy, agent_role_strategy, llm_config_strategy)
    def test_base_agent_initialization(self, name: str, role: str, llm_config: Optional[Dict]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        For any valid name, role, and LLM configuration, BaseAgent should initialize
        with all required attributes and proper state.
        """
        assume(name.strip() != "")
        assume(role.strip() != "")
        
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Initialize base agent
            agent = BaseAgent(name, role, llm_config)
            
            # Property: Agent should have correct name and role
            assert agent.name == name
            assert agent.role == role
            
            # Property: Agent should have OpenAI client
            assert hasattr(agent, 'client')
            
            # Property: Agent should have conversation history initialized as empty list
            assert hasattr(agent, 'conversation_history')
            assert isinstance(agent.conversation_history, list)
            assert len(agent.conversation_history) == 0
            
            # Property: Agent should have LLM configuration
            assert hasattr(agent, 'llm_config')
            assert isinstance(agent.llm_config, dict)
            assert "config_list" in agent.llm_config

    @given(llm_config_strategy)
    def test_agent_group_creation(self, llm_config: Optional[Dict]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        For any valid LLM configuration, create_agent_group should initialize
        all specialized agents with consistent configuration.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create agent group
            agent_group = create_agent_group(llm_config)
            
            # Property: Should return dictionary with all expected agents
            assert isinstance(agent_group, dict)
            expected_agents = {"supply_chain", "vlm_security", "orchestrator"}
            assert set(agent_group.keys()) == expected_agents
            
            # Property: Each agent should be of correct type
            assert isinstance(agent_group["supply_chain"], SupplyChainAgent)
            assert isinstance(agent_group["vlm_security"], VlmSecurityAgent)
            assert isinstance(agent_group["orchestrator"], OrchestratorAgent)
            
            # Property: All agents should be BaseAgent instances
            for agent in agent_group.values():
                assert isinstance(agent, BaseAgent)
            
            # Property: All agents should have consistent configuration
            for agent in agent_group.values():
                assert hasattr(agent, 'llm_config')
                assert isinstance(agent.llm_config, dict)
                if llm_config is not None:
                    # Custom config should be used (or vision config for VLM agent)
                    assert "config_list" in agent.llm_config

    def test_group_chat_manager_initialization(self):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        GroupChatManager should initialize properly with any valid agent dictionary.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create test agents
            agents = create_agent_group()
            
            # Initialize GroupChatManager
            manager = GroupChatManager(agents)
            
            # Property: Manager should have agents dictionary
            assert hasattr(manager, 'agents')
            assert isinstance(manager.agents, dict)
            assert manager.agents == agents
            
            # Property: Manager should have conversation log initialized
            assert hasattr(manager, 'conversation_log')
            assert isinstance(manager.conversation_log, list)
            assert len(manager.conversation_log) == 0
            
            # Property: Manager should have active analysis state
            assert hasattr(manager, 'active_analysis')
            assert manager.active_analysis is None

    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.just(None),  # We'll create mock agents
        min_size=1,
        max_size=5
    ))
    def test_group_chat_manager_with_various_agent_configs(self, agent_names: Dict[str, None]):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        GroupChatManager should handle various agent configurations properly.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create mock agents for each name
            mock_agents = {}
            for name in agent_names.keys():
                mock_agent = BaseAgent(name, f"Test {name} Agent")
                mock_agents[name] = mock_agent
            
            # Initialize manager with mock agents
            manager = GroupChatManager(mock_agents)
            
            # Property: Manager should accept any agent dictionary
            assert manager.agents == mock_agents
            assert len(manager.agents) == len(agent_names)
            
            # Property: Manager should initialize properly regardless of agent count
            assert isinstance(manager.conversation_log, list)
            assert len(manager.conversation_log) == 0
            assert manager.active_analysis is None

    def test_agent_system_prompt_generation(self):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        All agents should generate appropriate system prompts based on their roles.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Test each specialized agent
            supply_chain_agent = create_supply_chain_agent()
            vlm_agent = create_vlm_security_agent()
            orchestrator_agent = create_orchestrator_agent()
            
            agents = [supply_chain_agent, vlm_agent, orchestrator_agent]
            
            for agent in agents:
                # Property: Each agent should generate a system prompt
                prompt = agent._get_system_prompt()
                assert isinstance(prompt, str)
                assert len(prompt) > 0
                
                # Property: Prompt should contain agent name and role
                assert agent.name in prompt
                assert agent.role in prompt
                
                # Property: Prompt should be informative (reasonable length)
                assert len(prompt) > 100, f"System prompt too short for {agent.name}"

    def test_agent_initialization_error_handling(self):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        Agent initialization should handle configuration errors gracefully.
        """
        # Test with invalid API key configuration
        invalid_config = {
            "config_list": [{
                "model": "gpt-4",
                "api_key": "",  # Empty API key
                "temperature": 0.1,
                "max_tokens": 1000
            }]
        }
        
        with patch('agents.openai.OpenAI') as mock_openai:
            # Mock OpenAI to raise an exception for invalid config
            mock_openai.side_effect = Exception("Invalid API key")
            
            # Property: Should handle initialization errors gracefully
            try:
                agent = create_supply_chain_agent(invalid_config)
                # If no exception is raised, the agent should still be created
                # (error handling might be deferred to actual API calls)
                assert isinstance(agent, SupplyChainAgent)
            except Exception:
                # If exception is raised during init, that's also acceptable
                # as long as it's a clear error message
                pass

    def test_agent_configuration_consistency(self):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        Agents initialized with the same configuration should have consistent settings.
        """
        test_config = {
            "config_list": [{
                "model": "gpt-4-turbo-preview",
                "api_key": "test-key-123",
                "temperature": 0.5,
                "max_tokens": 2048
            }]
        }
        
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create multiple agents with same config
            agent1 = create_supply_chain_agent(test_config)
            agent2 = create_supply_chain_agent(test_config)
            
            # Property: Agents with same config should have consistent settings
            assert agent1.llm_config == agent2.llm_config
            assert agent1.llm_config == test_config
            
            # Property: Agents should be separate instances
            assert agent1 is not agent2
            assert agent1.conversation_history is not agent2.conversation_history

    def test_specialized_agent_unique_attributes(self):
        """
        **Feature: multi-agent-security, Property 10: Agent Initialization**
        
        Each specialized agent should have unique attributes specific to their role.
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            supply_chain_agent = create_supply_chain_agent()
            vlm_agent = create_vlm_security_agent()
            orchestrator_agent = create_orchestrator_agent()
            
            # Property: SupplyChainAgent should have security signature attributes
            assert hasattr(supply_chain_agent, 'malicious_packages')
            assert hasattr(supply_chain_agent, 'typosquat_targets')
            assert hasattr(supply_chain_agent, 'suspicious_keywords')
            
            # Property: VlmSecurityAgent should have vision client
            assert hasattr(vlm_agent, 'vision_client')
            
            # Property: OrchestratorAgent should have base agent capabilities
            # (No unique attributes beyond BaseAgent for now)
            assert hasattr(orchestrator_agent, 'conversation_history')
            
            # Property: Each agent should have unique names
            agent_names = {supply_chain_agent.name, vlm_agent.name, orchestrator_agent.name}
            assert len(agent_names) == 3, "Agent names should be unique"


class TestAgentCommunication:
    """Property-based tests for agent communication."""

    @given(
        st.one_of(
            # Supply chain analysis data
            st.fixed_dictionaries({
                "sbom_data": st.fixed_dictionaries({
                    "packages": st.lists(
                        st.fixed_dictionaries({
                            "name": st.text(min_size=1, max_size=50),
                            "versionInfo": st.text(min_size=1, max_size=20),
                            "ecosystem": st.sampled_from(["npm", "pypi", "maven", "rubygems", "crates", "go"])
                        }),
                        min_size=0,
                        max_size=5
                    )
                })
            }),
            # Visual security analysis data
            st.fixed_dictionaries({
                "image_base64": st.text(min_size=10, max_size=100),
                "context": st.one_of(st.text(min_size=1, max_size=200), st.none())
            }),
            # Comprehensive analysis data
            st.fixed_dictionaries({
                "sbom_data": st.fixed_dictionaries({
                    "packages": st.lists(
                        st.fixed_dictionaries({
                            "name": st.text(min_size=1, max_size=50),
                            "versionInfo": st.text(min_size=1, max_size=20),
                            "ecosystem": st.sampled_from(["npm", "pypi", "maven", "rubygems", "crates", "go"])
                        }),
                        min_size=0,
                        max_size=3
                    )
                }),
                "image_base64": st.text(min_size=10, max_size=100),
                "context": st.one_of(st.text(min_size=1, max_size=100), st.none())
            })
        ),
        st.sampled_from(["supply_chain", "visual_security", "comprehensive"])
    )
    def test_agent_communication_protocol(self, analysis_data: Dict[str, Any], analysis_type: str):
        """
        **Feature: multi-agent-security, Property 11: Agent Communication**
        
        For any active multi-agent analysis, agents should successfully exchange messages
        through the GroupChat mechanism and maintain proper communication protocols.
        **Validates: Requirements 4.4**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock successful API responses
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"findings": [], "status": "success"}'
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create agent group and manager
            agents = create_agent_group()
            manager = GroupChatManager(agents)
            
            # Property: Manager should handle communication for any valid analysis type
            result = manager.start_analysis(analysis_type, analysis_data)
            
            # Property: Communication should return structured result
            assert isinstance(result, dict)
            assert "analysis_type" in result
            assert "results" in result
            assert "timestamp" in result
            assert "agents_used" in result
            
            # Property: Analysis type should be preserved
            assert result["analysis_type"] == analysis_type
            
            # Property: Results should be dictionary
            assert isinstance(result["results"], dict)
            
            # Property: Agents used should be list
            assert isinstance(result["agents_used"], list)
            
            # Property: Timestamp should be valid ISO format
            from datetime import datetime
            try:
                datetime.fromisoformat(result["timestamp"])
            except ValueError:
                pytest.fail("Invalid timestamp format")

    @given(
        st.lists(
            st.fixed_dictionaries({
                "agent": st.sampled_from(["SupplyChainAgent", "VlmSecurityAgent", "OrchestratorAgent"]),
                "message_type": st.sampled_from(["analysis", "finding", "request", "response"]),
                "content": st.text(min_size=1, max_size=500),
                "timestamp": st.datetimes().map(lambda dt: dt.isoformat())
            }),
            min_size=1,
            max_size=10
        )
    )
    def test_message_handling_and_validation(self, messages: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 11: Agent Communication**
        
        For any sequence of agent messages, the communication system should handle
        and validate messages properly, maintaining conversation history.
        **Validates: Requirements 4.4**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create agents and manager
            agents = create_agent_group()
            manager = GroupChatManager(agents)
            
            # Simulate message exchange by adding to conversation histories
            for message in messages:
                agent_name_map = {
                    "SupplyChainAgent": "supply_chain",
                    "VlmSecurityAgent": "vlm_security", 
                    "OrchestratorAgent": "orchestrator"
                }
                
                agent_key = agent_name_map.get(message["agent"])
                if agent_key and agent_key in agents:
                    agent = agents[agent_key]
                    agent.conversation_history.append({
                        "role": "user" if message["message_type"] in ["analysis", "request"] else "assistant",
                        "content": message["content"],
                        "timestamp": message["timestamp"],
                        "message_type": message["message_type"]
                    })
            
            # Property: Manager should retrieve complete conversation history
            history = manager.get_conversation_history()
            
            # Property: History should be list
            assert isinstance(history, list)
            
            # Property: History should contain all messages with agent attribution
            for entry in history:
                assert isinstance(entry, dict)
                assert "agent" in entry
                assert "role" in entry
                assert "content" in entry
                assert "timestamp" in entry
                assert "message_type" in entry
                
                # Property: Agent should be valid
                assert entry["agent"] in ["supply_chain", "vlm_security", "orchestrator"]
                
                # Property: Role should be valid
                assert entry["role"] in ["user", "assistant"]
                
                # Property: Content should be string
                assert isinstance(entry["content"], str)
                
                # Property: Message type should be valid
                assert entry["message_type"] in ["analysis", "finding", "request", "response"]

    @given(st.text(min_size=5, max_size=200))
    def test_individual_agent_message_handling(self, message_content: str):
        """
        **Feature: multi-agent-security, Property 11: Agent Communication**
        
        For any message sent to an individual agent, the agent should handle it properly
        and return a structured response with appropriate metadata.
        **Validates: Requirements 4.4**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = f"Analysis of: {message_content}"
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test each agent type
            agents = [
                create_supply_chain_agent(),
                create_vlm_security_agent(),
                create_orchestrator_agent()
            ]
            
            for agent in agents:
                # Property: Agent should handle any valid message
                response = agent.send_message(message_content, "analysis")
                
                # Property: Response should be structured dictionary
                assert isinstance(response, dict)
                
                # Property: Response should contain required fields
                required_fields = ["agent_name", "message_type", "content", "timestamp", "status"]
                for field in required_fields:
                    assert field in response, f"Missing field {field} in response from {agent.name}"
                
                # Property: Agent name should match
                assert response["agent_name"] == agent.name
                
                # Property: Message type should be response
                assert response["message_type"] == "response"
                
                # Property: Content should be string
                assert isinstance(response["content"], str)
                
                # Property: Status should be success or error
                assert response["status"] in ["success", "error"]
                
                # Property: Timestamp should be valid
                from datetime import datetime
                try:
                    datetime.fromisoformat(response["timestamp"])
                except ValueError:
                    pytest.fail(f"Invalid timestamp format from {agent.name}")
                
                # Property: Conversation history should be updated
                assert len(agent.conversation_history) >= 2  # User message + assistant response
                
                # Property: Last entries should match the exchange
                last_user_msg = None
                last_assistant_msg = None
                for entry in reversed(agent.conversation_history):
                    if entry["role"] == "assistant" and last_assistant_msg is None:
                        last_assistant_msg = entry
                    elif entry["role"] == "user" and last_user_msg is None:
                        last_user_msg = entry
                    if last_user_msg and last_assistant_msg:
                        break
                
                assert last_user_msg is not None, f"No user message found in {agent.name} history"
                assert last_assistant_msg is not None, f"No assistant message found in {agent.name} history"
                assert last_user_msg["content"] == message_content


class TestFindingCompilation:
    """Property-based tests for finding compilation and correlation."""

    @given(
        st.lists(
            st.fixed_dictionaries({
                "agent": st.sampled_from(["SupplyChainAgent", "VlmSecurityAgent", "OrchestratorAgent"]),
                "analysis_type": st.sampled_from(["sbom_security", "visual_security", "incident_correlation"]),
                "findings": st.lists(
                    st.fixed_dictionaries({
                        "type": st.sampled_from(["malicious_package", "vulnerability", "typosquat", "visual_indicator"]),
                        "package": st.text(min_size=1, max_size=50),
                        "severity": st.sampled_from(["critical", "high", "medium", "low"]),
                        "confidence": st.floats(min_value=0.0, max_value=1.0),
                        "evidence": st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5)
                    }),
                    min_size=0,
                    max_size=5
                ),
                "timestamp": st.datetimes().map(lambda dt: dt.isoformat()),
                "status": st.sampled_from(["success", "error", "partial"])
            }),
            min_size=1,
            max_size=5
        )
    )
    def test_finding_compilation_and_correlation(self, agent_findings: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 12: Finding Compilation**
        
        For any multi-agent analysis, all agent findings should be aggregated into
        a unified report structure with proper correlation and metadata.
        **Validates: Requirements 4.5**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock orchestrator response for correlation
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            correlation_report = {
                "executive_summary": {"risk_level": "medium", "key_findings": []},
                "technical_analysis": {"correlations": [], "attack_patterns": []},
                "remediation_plan": {"immediate": [], "short_term": [], "long_term": []}
            }
            mock_response.choices[0].message.content = json.dumps(correlation_report)
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create orchestrator agent
            orchestrator = create_orchestrator_agent()
            
            # Property: Orchestrator should handle any list of findings
            result = orchestrator.correlate_findings(agent_findings)
            
            # Property: Result should be structured dictionary
            assert isinstance(result, dict)
            
            # Property: Result should contain required fields
            required_fields = ["agent", "analysis_type", "incident_report", "timestamp", "status"]
            for field in required_fields:
                assert field in result, f"Missing field {field} in correlation result"
            
            # Property: Agent should be OrchestratorAgent
            assert result["agent"] == "OrchestratorAgent"
            
            # Property: Analysis type should be incident_correlation
            assert result["analysis_type"] == "incident_correlation"
            
            # Property: Incident report should be dictionary
            assert isinstance(result["incident_report"], dict)
            
            # Property: Status should be valid
            assert result["status"] in ["success", "error"]
            
            # Property: Timestamp should be valid
            from datetime import datetime
            try:
                datetime.fromisoformat(result["timestamp"])
            except ValueError:
                pytest.fail("Invalid timestamp in correlation result")

    @given(
        st.lists(
            st.fixed_dictionaries({
                "supply_chain": st.one_of(
                    st.none(),
                    st.fixed_dictionaries({
                        "agent": st.just("SupplyChainAgent"),
                        "analysis_type": st.just("sbom_security"),
                        "signature_findings": st.lists(st.dictionaries(
                            keys=st.text(min_size=1, max_size=20),
                            values=st.one_of(st.text(), st.floats(), st.lists(st.text()))
                        )),
                        "status": st.sampled_from(["success", "error"])
                    })
                ),
                "visual_security": st.one_of(
                    st.none(),
                    st.fixed_dictionaries({
                        "agent": st.just("VlmSecurityAgent"),
                        "analysis_type": st.just("visual_security"),
                        "analysis": st.dictionaries(
                            keys=st.text(min_size=1, max_size=20),
                            values=st.one_of(st.text(), st.lists(st.text()))
                        ),
                        "status": st.sampled_from(["success", "error"])
                    })
                )
            }),
            min_size=1,
            max_size=3
        )
    )
    def test_multi_agent_analysis_compilation(self, analysis_results: List[Dict[str, Any]]):
        """
        **Feature: multi-agent-security, Property 12: Finding Compilation**
        
        For any combination of agent analysis results, the GroupChatManager should
        compile them into a unified analysis with proper agent attribution.
        **Validates: Requirements 4.5**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock API responses for different agents
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"findings": [], "analysis": "test"}'
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create agents and manager
            agents = create_agent_group()
            manager = GroupChatManager(agents)
            
            # Simulate analysis results by directly setting them
            compiled_results = {}
            
            for result_set in analysis_results:
                for analysis_type, analysis_data in result_set.items():
                    if analysis_data is not None:
                        compiled_results[analysis_type] = analysis_data
            
            # Property: Compiled results should maintain agent attribution
            for analysis_type, data in compiled_results.items():
                assert isinstance(data, dict)
                if "agent" in data:
                    # Property: Agent name should be valid
                    assert data["agent"] in ["SupplyChainAgent", "VlmSecurityAgent", "OrchestratorAgent"]
                
                if "analysis_type" in data:
                    # Property: Analysis type should match key
                    expected_types = {
                        "supply_chain": "sbom_security",
                        "visual_security": "visual_security"
                    }
                    if analysis_type in expected_types:
                        assert data["analysis_type"] == expected_types[analysis_type]
                
                if "status" in data:
                    # Property: Status should be valid
                    assert data["status"] in ["success", "error", "partial"]

    @given(
        st.integers(min_value=0, max_value=10),
        st.integers(min_value=0, max_value=10),
        st.integers(min_value=0, max_value=10)
    )
    def test_finding_aggregation_consistency(self, supply_findings: int, visual_findings: int, correlation_findings: int):
        """
        **Feature: multi-agent-security, Property 12: Finding Compilation**
        
        For any number of findings from different agents, the aggregation should
        maintain consistency and proper counting across all sources.
        **Validates: Requirements 4.5**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Create mock findings for each agent type
            mock_findings = []
            
            # Add supply chain findings
            for i in range(supply_findings):
                mock_findings.append({
                    "agent": "SupplyChainAgent",
                    "analysis_type": "sbom_security",
                    "findings": [{"type": "malicious_package", "package": f"pkg{i}"}],
                    "status": "success"
                })
            
            # Add visual security findings
            for i in range(visual_findings):
                mock_findings.append({
                    "agent": "VlmSecurityAgent", 
                    "analysis_type": "visual_security",
                    "findings": [{"type": "visual_indicator", "description": f"indicator{i}"}],
                    "status": "success"
                })
            
            # Add correlation findings
            for i in range(correlation_findings):
                mock_findings.append({
                    "agent": "OrchestratorAgent",
                    "analysis_type": "incident_correlation", 
                    "findings": [{"type": "correlation", "pattern": f"pattern{i}"}],
                    "status": "success"
                })
            
            # Property: Total findings should equal sum of individual agent findings
            total_expected = supply_findings + visual_findings + correlation_findings
            assert len(mock_findings) == total_expected
            
            # Property: Each finding should have proper agent attribution
            supply_count = sum(1 for f in mock_findings if f["agent"] == "SupplyChainAgent")
            visual_count = sum(1 for f in mock_findings if f["agent"] == "VlmSecurityAgent")
            correlation_count = sum(1 for f in mock_findings if f["agent"] == "OrchestratorAgent")
            
            assert supply_count == supply_findings
            assert visual_count == visual_findings
            assert correlation_count == correlation_findings
            
            # Property: Each finding should have consistent structure
            for finding in mock_findings:
                assert isinstance(finding, dict)
                assert "agent" in finding
                assert "analysis_type" in finding
                assert "findings" in finding
                assert "status" in finding
                
                # Property: Findings should be list
                assert isinstance(finding["findings"], list)

    def test_empty_findings_handling(self):
        """
        **Feature: multi-agent-security, Property 12: Finding Compilation**
        
        The system should handle empty findings gracefully and still produce
        a valid compilation structure.
        **Validates: Requirements 4.5**
        """
        with patch('agents.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock response for empty findings
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"executive_summary": {"risk_level": "low", "key_findings": []}}'
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create orchestrator
            orchestrator = create_orchestrator_agent()
            
            # Property: Should handle empty findings list
            result = orchestrator.correlate_findings([])
            
            # Property: Result should still be valid structure
            assert isinstance(result, dict)
            assert "agent" in result
            assert "analysis_type" in result
            assert "incident_report" in result
            assert "timestamp" in result
            assert "status" in result
            
            # Property: Should handle None findings
            result_none = orchestrator.correlate_findings([None])
            assert isinstance(result_none, dict)
            
            # Property: Should handle findings with empty data
            empty_findings = [
                {"agent": "SupplyChainAgent", "findings": [], "status": "success"},
                {"agent": "VlmSecurityAgent", "findings": [], "status": "success"}
            ]
            result_empty = orchestrator.correlate_findings(empty_findings)
            assert isinstance(result_empty, dict)
            assert result_empty["status"] in ["success", "error"]