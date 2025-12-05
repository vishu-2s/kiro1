"""
Cleanup specs directory - Archive outdated specs and remove duplicates.

This script:
1. Archives the superseded multi-agent-security spec
2. Deletes the duplicate npm-script-analysis copy directory
3. Creates a summary of actions taken
"""

import os
import shutil
from datetime import datetime

def cleanup_specs():
    """Clean up the specs directory."""
    
    print("=" * 80)
    print("SPECS DIRECTORY CLEANUP")
    print("=" * 80)
    
    actions = []
    
    # Create archive directory if it doesn't exist
    archive_dir = ".kiro/specs/_archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"\n✅ Created archive directory: {archive_dir}")
        actions.append(f"Created archive directory: {archive_dir}")
    
    # 1. Archive multi-agent-security (superseded by hybrid-agentic-architecture)
    old_spec = ".kiro/specs/multi-agent-security"
    archived_spec = f"{archive_dir}/multi-agent-security"
    
    if os.path.exists(old_spec):
        if os.path.exists(archived_spec):
            # Add timestamp to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_spec = f"{archive_dir}/multi-agent-security_{timestamp}"
        
        shutil.move(old_spec, archived_spec)
        print(f"\n📦 Archived: multi-agent-security")
        print(f"   From: {old_spec}")
        print(f"   To: {archived_spec}")
        actions.append(f"Archived multi-agent-security to {archived_spec}")
        
        # Create README in archived spec
        readme_path = os.path.join(archived_spec, "ARCHIVED_README.md")
        with open(readme_path, 'w') as f:
            f.write(f"""# Archived Spec: multi-agent-security

**Archived Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Reason**: Superseded by hybrid-agentic-architecture spec

## Why Archived?

This spec represented the first iteration of the multi-agent system. It was replaced by the more comprehensive `hybrid-agentic-architecture` spec which combines:
- Rule-based detection (fast, deterministic)
- Multi-agent analysis (intelligent, adaptive)

The hybrid approach is what's actually implemented in the current system.

## Historical Value

This spec is kept for historical reference and to understand the evolution of the system architecture.

## Current System

See: `.kiro/specs/hybrid-agentic-architecture/`
""")
        print(f"   ✅ Created ARCHIVED_README.md")
    else:
        print(f"\n⚠️  Spec not found: {old_spec}")
    
    # 2. Delete duplicate directory
    duplicate_dir = ".kiro/specs/npm-script-analysis copy"
    
    if os.path.exists(duplicate_dir):
        shutil.rmtree(duplicate_dir)
        print(f"\n❌ Deleted duplicate: npm-script-analysis copy")
        print(f"   Path: {duplicate_dir}")
        actions.append(f"Deleted duplicate directory: {duplicate_dir}")
    else:
        print(f"\n⚠️  Duplicate not found: {duplicate_dir}")
    
    # 3. Create summary document
    summary_path = ".kiro/specs/SPECS_DIRECTORY_STRUCTURE.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Specs Directory Structure

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

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

{chr(10).join(f"- {action}" for action in actions)}

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
""")
    
    print(f"\n📄 Created: {summary_path}")
    actions.append(f"Created directory structure document: {summary_path}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\nActions taken: {len(actions)}")
    for action in actions:
        print(f"  ✅ {action}")
    
    print("\n" + "=" * 80)
    print("ACTIVE SPECS (4):")
    print("  ✅ hybrid-agentic-architecture")
    print("  ✅ production-ready-enhancements")
    print("  ✅ ui-reputation-display")
    print("  ✅ npm-script-analysis")
    print("\nARCHIVED SPECS (1):")
    print("  📦 multi-agent-security")
    print("=" * 80)

if __name__ == "__main__":
    cleanup_specs()
