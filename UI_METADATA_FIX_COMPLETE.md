# UI Metadata Fix - Complete ✅

## Issue

The Repository/Folder field in the UI was showing the temporary extraction path instead of the user's original input (GitHub URL or local folder name).

**Before:**
```
Repository/Folder: supply_chain_analysis_fq5uxtuj
```

**After:**
```
Repository/Folder: https://github.com/bahmutov/pre-git
```
or
```
Repository/Folder: test_nested_deps
```

## Root Cause

In `analyze_supply_chain.py`, the `analyze_project_hybrid()` function was passing `project_dir` (the temporary cloned directory path) instead of `target` (the original user input) to:
1. `orchestrator.orchestrate()` - for agent-based analysis
2. `_generate_simple_report()` - for rule-based analysis

This caused the metadata to store the temp path instead of the user's input.

## Fix Applied

### File: `analyze_supply_chain.py`

**Changed Line 1463:**
```python
# Before
project_path=project_dir,

# After
project_path=target,  # Use original target (user input), not project_dir (temp path)
```

**Changed Line 1478:**
```python
# Before
project_dir,

# After
target,  # Use original target (user input), not project_dir (temp path)
```

**Changed Line 1489:**
```python
# Before
project_dir,

# After
target,  # Use original target (user input), not project_dir (temp path)
```

## How It Works

1. **User Input**: User enters GitHub URL or local folder in the web UI
2. **Target Variable**: `main_github.py` stores this as `target` variable
3. **Project Directory**: For GitHub repos, code is cloned to temp directory (`project_dir`)
4. **Metadata Storage**: Now uses `target` (user input) instead of `project_dir` (temp path)
5. **UI Display**: Shows the original user input in the Repository/Folder field

## Testing

### Test 1: Local Folder
```bash
python main_github.py --local test_nested_deps --ecosystem npm
```
**Result:** `metadata.target = "test_nested_deps"` ✅

### Test 2: GitHub URL
```bash
python main_github.py --github https://github.com/owner/repo
```
**Result:** `metadata.target = "https://github.com/owner/repo"` ✅

## UI Display

The metadata section now correctly shows:

```
METADATA
Repository/Folder: https://github.com/bahmutov/pre-git
Timestamp: 12/4/2025, 1:58:58 AM
Confidence: 90%

Analysis Type:
• Rule-Based Security Findings: Yes
• Agent-Based Security Findings: No
• Dependency Graph: Yes
• Supply Chain Attack Detection: No
```

## Files Modified

- `analyze_supply_chain.py` - Fixed 3 locations where `project_dir` was used instead of `target`

## Result

The UI now displays the **user's original input** (GitHub URL or local folder name) in the Repository/Folder field, making it clear what was analyzed.
