# Implementation Plan: Hybrid Intelligent Agentic Architecture

## Phase 1: Core Infrastructure & MVP (2 weeks)

- [x] 1. Agent Base Classes and Orchestrator Foundation





  - Implement core orchestrator with explicit sequential protocol and agent base classes
  - Create `agents/base_agent.py` - SecurityAgent base class with LLM config from .env
  - Create `agents/orchestrator.py` - AgentOrchestrator with sequential protocol
  - Create `agents/types.py` - AgentResult dataclass and shared types
  - Implement 5-stage conversation protocol with timeout handling (30s, 20s, 40s, 30s, 20s)
  - Add shared context management and retry logic (exponential backoff, max 2 retries)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 2. Vulnerability Analysis Agent with OSV Integration





  - Implement VulnerabilityAnalysisAgent that queries OSV API and analyzes vulnerabilities
  - Create `agents/vulnerability_agent.py` with OSV API integration and caching
  - Implement CVSS score calculation and vulnerability impact assessment
  - Add confidence scoring with reasoning
  - Create tool functions: query_osv_api, calculate_cvss, get_cached_vuln
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Reputation Analysis Agent with Registry Integration





  - Implement ReputationAnalysisAgent that assesses package trustworthiness
  - Create `agents/reputation_agent.py` with npm and PyPI registry integration
  - Implement reputation scoring algorithm (age, downloads, author, maintenance)
  - Add risk factor identification
  - Create tool functions: fetch_npm_metadata, fetch_pypi_metadata, calculate_reputation_score
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4. Synthesis Agent with OpenAI JSON Mode







  - Implement SynthesisAgent that produces final JSON output using OpenAI JSON mode
  - Create `agents/synthesis_agent.py` with JSON schema validation
  - Implement fallback report generation when synthesis fails
  - Add aggregation of all agent results into package-centric structure
  - Generate common recommendations using LLM
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 5. Dependency Graph Analyzer












  - Implement dependency graph analyzer that builds complete dependency trees
  - Create `tools/dependency_graph.py` - DependencyGraphAnalyzer class
  - Build npm and Python dependency tree builders
  - Add transitive dependency resolution and circular dependency detection
  - Implement version conflict detection and vulnerability path tracing
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 6. Main Entry Point Integration





  - Update analyze_supply_chain.py to use the new hybrid architecture
  - Add GitHub repo cloning and local directory support
  - Implement input mode auto-detection
  - Integrate rule-based detection + agent analysis
  - Add performance metrics collection
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 7. MVP Testing and Validation





  - Create comprehensive tests for MVP functionality
  - Write unit tests for orchestrator, Vulnerability Agent, Reputation Agent, Synthesis Agent
  - Create integration tests: malicious package (flatmap-stream), clean project, agent failure handling
  - Add performance benchmark test (< 2 minutes for 20 packages)
  - _Requirements: All Phase 1 requirements_

- [x] 8. Checkpoint - MVP Complete





  - Ensure all tests pass, ask the user if questions arise

## Phase 2: Advanced Agents & Production Features (2 weeks)

- [x] 9. Code Analysis Agent with Pattern Detection






  - Implement CodeAnalysisAgent that analyzes complex and obfuscated code
  - Create `agents/code_agent.py` with LLM-based code analysis
  - Add obfuscation detection (base64, eval, dynamic execution)
  - Implement behavioral analysis (network activity, file access, process spawning)
  - Add code complexity calculation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Supply Chain Attack Detection Agent












  - Implement SupplyChainAttackAgent that detects sophisticated attacks like Hulud
  - Create `agents/supply_chain_agent.py` with maintainer change detection
  - Add version diff analysis and exfiltration pattern detection
  - Implement time-delayed activation detection
  - Add attack pattern matching (Hulud, event-stream, etc.)
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 11. Comprehensive Error Handling and Graceful Degradation





  - Implement robust error handling with graceful degradation
  - Create `agents/error_handler.py` with retry logic and exponential backoff
  - Add fallback data generation for failed agents
  - Implement graceful degradation levels (100%, 70%, 40%, <40%)
  - Add user-friendly error messages in JSON output
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 12. Caching Optimization and Performance Tuning
  - Optimize caching to achieve 60%+ cache hit rate and reduce costs
  - Enhance cache manager with LLM response caching
  - Add cache key generation for agent responses and TTL configuration
  - Implement cache statistics and performance metrics collection
  - Add cost tracking (token usage, API calls)
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 13. Property-Based Tests for Correctness Properties
  - Implement property-based tests using Hypothesis for key correctness properties
  - Create property tests: JSON structure validity, confidence scores in range [0, 1]
  - Add property tests: dependency graph consistency, agent result validation
  - Test synthesis output schema compliance
  - _Requirements: All design correctness properties_

- [ ]* 14. Integration Tests for Production Scenarios
  - Create comprehensive integration tests for production scenarios
  - Test large projects (100 packages), multiple ecosystems (npm + Python)
  - Test all agents succeed, partial agent failures, complete agent failure
  - Test GitHub repository analysis and local directory analysis
  - _Requirements: All Phase 2 requirements_

- [ ] 15. Checkpoint - Production Features Complete
  - Ensure all tests pass, ask the user if questions arise

## Phase 3: Observability & Optional Features (1 week)

- [ ] 16. Observability and Debugging Tools
  - Implement comprehensive logging, tracing, and debugging tools
  - Create structured logging with JSON format
  - Add agent conversation tracing (optional, enabled via .env)
  - Implement debugging tools: dry-run mode, single-agent mode, verbose mode
  - Add performance monitoring dashboard and cost tracking
  - _Requirements: Design observability requirements_

- [ ]* 17. MCP Server Integration (Optional)
  - Implement optional MCP server integration for external tools
  - Create `agents/mcp_client.py` - MCP client wrapper
  - Add MCP tool discovery and fallback strategy
  - Configure in .env (MCP_ENABLED, MCP_CONFIG_PATH)
  - Add example MCP configuration for vulnerability-db and threat-intelligence
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ]* 18. Kiro Agent Hooks Integration (Optional)
  - Implement optional Kiro agent hooks for IDE integration
  - Create hook engine for automatic security scanning
  - Add manifest file save hook, git commit hook, code file save hook
  - Implement IDE notification system
  - Configure in .env (HOOKS_ENABLED, HOOKS_NOTIFY_*, HOOKS_BLOCK_COMMIT_ON_CRITICAL)
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 19. Documentation and Deployment Guide
  - Create comprehensive documentation for deployment and usage
  - Update README.md with hybrid architecture overview
  - Create DEPLOYMENT.md, API_REFERENCE.md, PERFORMANCE_TUNING.md
  - Update TROUBLESHOOTING.md with agent-specific issues
  - Create example .env file with all settings
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ]* 20. Final Integration Testing and Performance Validation
  - Perform final validation and performance testing
  - Execute end-to-end test suite
  - Validate performance (< 2.5 minutes for 20 packages)
  - Validate cost (< $0.15 per analysis with caching)
  - Validate cache hit rate (> 60%) and error handling
  - Confirm backward compatibility with existing UI
  - _Requirements: All requirements_

- [ ] 21. Final Checkpoint - Production Ready
  - Ensure all tests pass, ask the user if questions arise
