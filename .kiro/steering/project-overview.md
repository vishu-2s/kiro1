---
inclusion: always
---

# Multi-Agent Security Analysis System - Project Overview

## Purpose
This is an AI-powered security analysis platform that detects malicious packages, vulnerabilities, and supply chain attacks in software projects. It uses multiple specialized agents to analyze npm and Python ecosystems.

## Key Architecture Principles

### 1. Plugin-Based Ecosystem Analyzers
- **Base Class**: `EcosystemAnalyzer` in `tools/ecosystem_analyzer.py`
- **Current Implementations**: npm (`tools/npm_analyzer.py`), Python (`tools/python_analyzer.py`)
- **Registry Pattern**: All analyzers register with `AnalyzerRegistry` for auto-detection
- **Extensibility**: Add new languages by implementing one class (~100 lines)

### 2. Core Components
- **Caching Layer** (`tools/cache_manager.py`): SQLite-based LLM response caching
- **Reputation Service** (`tools/reputation_service.py`): Ecosystem-agnostic package scoring
- **Analysis Engine** (`analyze_supply_chain.py`): Main orchestration logic
- **Web UI** (`app.py`): Flask-based interface for analysis

### 3. Testing Strategy
- **Unit Tests**: Core functionality validation
- **Property-Based Tests**: Hypothesis for correctness properties
- **Integration Tests**: End-to-end workflow validation
- **Coverage Target**: 80%+ overall, 90%+ for security-critical code

## Current Development Focus
Working on production-ready enhancements (see `.kiro/specs/production-ready-enhancements/`):
1. Intelligent caching system (10x performance boost)
2. Package reputation scoring
3. Python ecosystem support
4. Comprehensive test suite
5. CI/CD integration

## Code Style Guidelines
- Use type hints for all function signatures
- Document security-critical functions with detailed docstrings
- Keep analyzers self-contained and testable
- Follow the plugin pattern for new ecosystem support
- Prefer composition over inheritance

## Security Considerations
- Never execute untrusted code directly (use AST parsing for Python)
- Validate all external inputs (package names, file paths)
- Rate limit API calls to registries
- Cache sensitive data with encryption
- Log security events for audit trails
