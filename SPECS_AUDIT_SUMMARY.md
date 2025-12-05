# Specs Directory Audit

## Current System Architecture

The system is now based on the **Hybrid Agentic Architecture** which combines:
1. Rule-based detection (fast, deterministic)
2. Multi-agent analysis (intelligent, adaptive)

## Specs Status

### ✅ RELEVANT - Keep These

#### 1. `.kiro/specs/hybrid-agentic-architecture/`
**Status**: CURRENT SYSTEM ✅
**Purpose**: Defines the hybrid architecture combining rule-based + agent-based analysis
**Files**:
- `requirements.md` - 15 requirements for hybrid system
- `design.md` - Complete architecture, agents, tools
- `tasks.md` - Implementation tasks
- `SPEC_SUMMARY.md` - Overview
- `SUPPLY_CHAIN_DETECTION.md` - Supply chain specifics

**Keep**: YES - This is the foundation of the current system

#### 2. `.kiro/specs/production-ready-enhancements/`
**Status**: ACTIVE ENHANCEMENTS ✅
**Purpose**: Production features like caching, reputation scoring, Python support
**Files**:
- `requirements.md` - Production features
- `design.md` - Implementation details
- `tasks.md` - Enhancement tasks

**Keep**: YES - These are implemented features

#### 3. `.kiro/specs/ui-reputation-display/`
**Status**: UI FEATURE ✅
**Purpose**: UI improvements for displaying reputation and analysis
**Keep**: YES - UI is actively used

---

### ❓ REVIEW - May Be Outdated

#### 4. `.kiro/specs/multi-agent-security/`
**Status**: SUPERSEDED BY HYBRID-AGENTIC-ARCHITECTURE ❓
**Purpose**: Original multi-agent spec (before hybrid approach)
**Issue**: This was the first iteration, replaced by hybrid-agentic-architecture

**Recommendation**: 
- **ARCHIVE** or **DELETE** - Superseded by hybrid-agentic-architecture
- The hybrid spec is more comprehensive and is what's actually implemented

#### 5. `.kiro/specs/npm-script-analysis/`
**Status**: IMPLEMENTED ✅
**Purpose**: NPM script detection for preinstall attacks
**Implementation**: Found in `analyze_supply_chain.py` and `tools/sbom_tools.py`
- Detects malicious lifecycle scripts (preinstall, postinstall, etc.)
- Pattern matching for suspicious commands
- Integrated into rule-based detection

**Recommendation**: **KEEP** - Feature is implemented and spec is valid reference

#### 6. `.kiro/specs/npm-script-analysis copy/`
**Status**: DUPLICATE ❌
**Purpose**: Appears to be a duplicate directory

**Recommendation**: **DELETE** - This is clearly a duplicate

---

## Recommended Actions

### Immediate Actions

1. **DELETE** `.kiro/specs/npm-script-analysis copy/` - It's a duplicate

2. **ARCHIVE** `.kiro/specs/multi-agent-security/` 
   - Move to `.kiro/specs/_archive/multi-agent-security/`
   - Reason: Superseded by hybrid-agentic-architecture
   - Keep for historical reference

3. **REVIEW** `.kiro/specs/npm-script-analysis/`
   - Check if npm script detection is implemented
   - If yes: Keep
   - If no: Decide if needed or archive

### Keep Active

These specs are relevant to the current system:
- ✅ `hybrid-agentic-architecture/` - Core system
- ✅ `production-ready-enhancements/` - Active features
- ✅ `ui-reputation-display/` - UI features

---

## Current System Components

Based on the codebase, here's what's actually implemented:

### Core Architecture (from hybrid-agentic-architecture)
- ✅ Rule-based detection engine
- ✅ Agent orchestrator
- ✅ 5 specialized agents:
  1. Vulnerability Analysis Agent
  2. Reputation Analysis Agent
  3. Code Analysis Agent
  4. Supply Chain Attack Agent
  5. Synthesis Agent

### Production Features (from production-ready-enhancements)
- ✅ SQLite caching system
- ✅ Reputation scoring service
- ✅ Python ecosystem support
- ✅ Parallel OSV queries

### UI Features (from ui-reputation-display)
- ✅ Web interface (Flask)
- ✅ Real-time analysis status
- ✅ Package-centric report display
- ✅ LLM recommendations display

### Additional Features
- ✅ Dependency graph analysis
- ✅ GitHub repository analysis
- ✅ Local directory analysis
- ✅ npm and PyPI ecosystem support
- ✅ Malicious package detection
- ✅ Typosquatting detection
- ✅ Preinstall script detection (npm)

---

## Verification Needed

To complete this audit, verify:

1. **NPM Script Analysis**: 
   - Check `analyze_supply_chain.py` for preinstall script detection
   - Check if `.kiro/specs/npm-script-analysis/` matches implementation

2. **Multi-Agent Security Spec**:
   - Confirm it's fully superseded by hybrid-agentic-architecture
   - No unique requirements that aren't in hybrid spec

---

## Conclusion

**Specs to Keep**: 4 ✅
- hybrid-agentic-architecture (core system)
- production-ready-enhancements (active features)
- ui-reputation-display (UI features)
- npm-script-analysis (implemented feature)

**Specs to Archive**: 1 📦
- multi-agent-security (superseded by hybrid-agentic-architecture)

**Specs to Delete**: 1 ❌
- npm-script-analysis copy (duplicate directory)

---

**Next Steps**:
1. Verify npm script detection implementation
2. Archive multi-agent-security spec
3. Delete duplicate directory
4. Update this document with final decisions
