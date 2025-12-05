# Specs Directory Structure

**Last Updated**: 2025-12-04 17:36:30

## Active Specs

These specs are relevant to the current system:

### 1. hybrid-agentic-architecture/
**Purpose**: Core system architecture
**Status**: ✅ ACTIVE - Current system implementation
**Description**: Defines the hybrid architecture combining rule-based detection with multi-agent analysis

**Key Files**:
- `requirements.md` - 15 requirements for hybrid system
- `design.md` - Complete architecture, agents, tools
- `tasks.md` - Implementation tasks
- `SPEC_SUMMARY.md` - Overview

### 2. production-ready-enhancements/
**Purpose**: Production features
**Status**: ✅ ACTIVE - Implemented features
**Description**: Caching, reputation scoring, Python support, parallel processing

**Key Files**:
- `requirements.md` - Production feature requirements
- `design.md` - Implementation details
- `tasks.md` - Enhancement tasks

### 3. ui-reputation-display/
**Purpose**: UI features
**Status**: ✅ ACTIVE - Current UI
**Description**: Web interface for displaying analysis results, reputation scores, and recommendations

### 4. npm-script-analysis/
**Purpose**: NPM script detection
**Status**: ✅ ACTIVE - Implemented feature
**Description**: Detection of malicious lifecycle scripts in package.json (preinstall, postinstall, etc.)

**Implementation**: `analyze_supply_chain.py`, `tools/sbom_tools.py`

---

## Archived Specs

### _archive/multi-agent-security/
**Purpose**: Original multi-agent spec
**Status**: 📦 ARCHIVED - Superseded by hybrid-agentic-architecture
**Reason**: First iteration, replaced by more comprehensive hybrid approach

---

## Directory Structure

```
.kiro/specs/
├── hybrid-agentic-architecture/     ✅ Core system
├── production-ready-enhancements/   ✅ Production features
├── ui-reputation-display/           ✅ UI features
├── npm-script-analysis/             ✅ NPM script detection
├── _archive/                        📦 Archived specs
│   └── multi-agent-security/        (superseded)
└── SPECS_DIRECTORY_STRUCTURE.md    📄 This file
```

---

## Cleanup History



---

## Guidelines

### When to Create a New Spec

Create a new spec when:
- Adding a major new feature
- Significant architectural change
- New agent or analysis capability
- Major UI redesign

### When to Archive a Spec

Archive a spec when:
- Superseded by a newer spec
- Feature removed from system
- No longer relevant to current architecture

### When to Delete a Spec

Delete only:
- Duplicate directories
- Accidental copies
- Never started/abandoned specs

---

## Current System Overview

**Architecture**: Hybrid (Rule-based + Multi-agent)

**Agents**:
1. Vulnerability Analysis Agent
2. Reputation Analysis Agent
3. Code Analysis Agent
4. Supply Chain Attack Agent
5. Synthesis Agent

**Ecosystems**: npm, PyPI

**Features**:
- GitHub repository analysis
- Local directory analysis
- Dependency graph visualization
- LLM-powered recommendations
- Real-time analysis status
- Caching system
- Reputation scoring
