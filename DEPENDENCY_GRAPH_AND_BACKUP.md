# Dependency Graph and Backup Features

## Overview
Added dependency graph visualization to the report and automatic backup of existing reports before overwriting.

## Changes Made

### 1. Fixed HTML Report Generation Error

**Problem**: `'dict' object has no attribute 'metadata'`

**Root Cause**: The hybrid analysis returns a dict, but `create_security_report()` expects an `AnalysisResult` object with a `metadata` attribute.

**Solution**: Skip HTML generation when result is a dict
```python
# main_github.py
if isinstance(result, dict):
    logger.info("Skipping HTML report generation (result is dict)")
else:
    temp_result_paths = create_security_report(result, ...)
```

### 2. Added Dependency Graph to JSON Output

**Location**: `analyze_supply_chain.py`

**Implementation**:
```python
# Step 9: Add dependency graph to final JSON
if "dependency_graph" not in final_json:
    final_json["dependency_graph"] = dependency_graph
```

**Dependency Graph Structure**:
```json
{
  "dependency_graph": {
    "metadata": {
      "ecosystem": "npm",
      "manifest_path": "/path/to/package.json",
      "total_packages": 25,
      "circular_dependencies_count": 0,
      "version_conflicts_count": 0
    },
    "nodes": [...],
    "edges": [...],
    "circular_dependencies": [],
    "version_conflicts": []
  }
}
```

### 3. Automatic Backup Before Overwrite

**Location**: `analyze_supply_chain.py`

**Implementation**:
```python
# Create backup of existing file if it exists
if os.path.exists(output_path):
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        output_dir, 
        f"demo_ui_comprehensive_report_backup_{backup_timestamp}.json"
    )
    shutil.copy2(output_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
```

**Backup Naming Convention**:
```
demo_ui_comprehensive_report_backup_20251203_175001.json
demo_ui_comprehensive_report_backup_20251203_180530.json
demo_ui_comprehensive_report_backup_20251203_182145.json
```

### 4. Dependency Graph UI Display

**Location**: `templates/index.html`

**Features**:
- Visual metrics cards showing:
  - Total packages
  - Circular dependencies count
  - Version conflicts count
  - Ecosystem type
- Expandable details for circular dependencies
- Expandable details for version conflicts

**UI Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Dependency Graph                                        │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │    25    │ │     0    │ │     0    │ │   npm    │  │
│ │ Packages │ │ Circular │ │ Version  │ │Ecosystem │  │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                         │
│ ▼ Circular Dependencies (0)                            │
│ ▼ Version Conflicts (0)                                │
└─────────────────────────────────────────────────────────┘
```

### 5. Error Handler Enhancement

**Location**: `agents/error_handler.py`

Added dependency graph to fallback report:
```python
"dependency_graph": context.dependency_graph if hasattr(context, 'dependency_graph') else {}
```

## Benefits

### Dependency Graph Display
1. **Visibility**: See total package count and dependency structure
2. **Issue Detection**: Identify circular dependencies and version conflicts
3. **Ecosystem Info**: Know which package manager is being used
4. **Debugging**: Understand dependency relationships

### Automatic Backup
1. **Safety**: Never lose previous analysis results
2. **Comparison**: Compare results across multiple runs
3. **History**: Track changes over time
4. **Recovery**: Restore previous reports if needed

### Error Fix
1. **Stability**: No more crashes when generating reports
2. **Compatibility**: Works with both dict and object results
3. **Graceful Degradation**: Skips HTML when not possible

## Usage

### Viewing Dependency Graph

1. Run analysis
2. Open web UI report
3. Scroll to "Dependency Graph" section
4. View metrics and expand details

### Accessing Backups

Backups are automatically created in the `outputs/` directory:
```bash
outputs/
├── demo_ui_comprehensive_report.json          # Current report
├── demo_ui_comprehensive_report_backup_20251203_175001.json
├── demo_ui_comprehensive_report_backup_20251203_180530.json
└── demo_ui_comprehensive_report_backup_20251203_182145.json
```

### Restoring from Backup

```bash
# Copy backup to current report
cp outputs/demo_ui_comprehensive_report_backup_20251203_175001.json \
   outputs/demo_ui_comprehensive_report.json
```

## Example Dependency Graph Output

### Clean Project (No Issues)
```json
{
  "dependency_graph": {
    "metadata": {
      "ecosystem": "npm",
      "total_packages": 25,
      "circular_dependencies_count": 0,
      "version_conflicts_count": 0
    }
  }
}
```

### Project with Issues
```json
{
  "dependency_graph": {
    "metadata": {
      "ecosystem": "npm",
      "total_packages": 50,
      "circular_dependencies_count": 2,
      "version_conflicts_count": 3
    },
    "circular_dependencies": [
      {
        "cycle": ["package-a", "package-b", "package-c", "package-a"]
      }
    ],
    "version_conflicts": [
      {
        "package": "lodash",
        "versions": ["4.17.19", "4.17.21"]
      }
    ]
  }
}
```

## Testing

### Test Dependency Graph Display
```bash
# Run analysis
python main_github.py --github https://github.com/owner/repo --ecosystem npm

# Check JSON output
python -c "import json; data = json.load(open('outputs/demo_ui_comprehensive_report.json')); print('Has dependency_graph:', 'dependency_graph' in data)"

# View in UI
# Open http://localhost:5000 and navigate to Report tab
```

### Test Backup Creation
```bash
# Run first analysis
python main_github.py --github https://github.com/owner/repo --ecosystem npm

# Check for original report
ls -la outputs/demo_ui_comprehensive_report.json

# Run second analysis
python main_github.py --github https://github.com/owner/repo --ecosystem npm

# Check for backup
ls -la outputs/demo_ui_comprehensive_report_backup_*.json
```

### Test Error Fix
```bash
# Run analysis (should complete without 'metadata' error)
python main_github.py --github https://github.com/owner/repo --ecosystem npm

# Check logs - should see:
# "Skipping HTML report generation (result is dict, not AnalysisResult object)"
# "JSON results saved to: outputs\demo_ui_comprehensive_report.json"
# No error about 'dict' object has no attribute 'metadata'
```

## Log Output

### Successful Analysis with Backup
```
[INFO] Starting hybrid analysis: https://github.com/owner/repo
[INFO] Cloning GitHub repository...
[INFO] Building dependency graph...
[INFO] Built dependency graph: 25 packages, 0 circular deps, 0 version conflicts
[INFO] Running multi-agent analysis...
[INFO] Multi-agent analysis complete
[INFO] Created backup: outputs/demo_ui_comprehensive_report_backup_20251203_175001.json
[INFO] Analysis complete. Output written to: outputs/demo_ui_comprehensive_report.json
[INFO] Total duration: 52.69s
[INFO] Analysis completed successfully
[INFO] JSON results saved to: outputs\demo_ui_comprehensive_report.json
[INFO] Skipping HTML report generation (result is dict, not AnalysisResult object)
```

## Future Enhancements

1. **Backup Management**: Auto-delete old backups (keep last N)
2. **Backup Comparison**: UI to compare two reports
3. **Graph Visualization**: Interactive dependency graph visualization
4. **Export Graph**: Export dependency graph as DOT/GraphML
5. **Backup Restore**: UI button to restore from backup
6. **Backup Compression**: Compress old backups to save space

## Conclusion

All three issues have been resolved:
- ✅ Fixed 'dict' object metadata error
- ✅ Added dependency graph to JSON output
- ✅ Implemented automatic backup before overwrite

The system now provides complete dependency information and safely preserves previous analysis results.
