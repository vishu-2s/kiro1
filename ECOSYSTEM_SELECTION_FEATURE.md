# Ecosystem Selection Feature

## Overview
Added ecosystem selection (npm/Python) to both the web UI and command-line interface, allowing users to force a specific ecosystem instead of relying on auto-detection.

## Changes Made

### 1. Web UI (templates/index.html)

#### Added Ecosystem Radio Buttons
```html
<div class="form-group">
    <label>Ecosystem</label>
    <div class="mode-toggle">
        <button class="mode-btn active" onclick="setEcosystem('npm')" id="ecosystem-npm">
            npm (JavaScript)
        </button>
        <button class="mode-btn" onclick="setEcosystem('pypi')" id="ecosystem-pypi">
            Python (PyPI)
        </button>
    </div>
</div>
```

#### Added JavaScript Functions
- `currentEcosystem` variable (default: 'npm')
- `setEcosystem(ecosystem)` function to handle ecosystem selection
- Updated `startAnalysis()` to send ecosystem parameter to backend

### 2. Flask Backend (app.py)

#### Updated API Endpoint
- `/api/analyze` now accepts `ecosystem` parameter
- Default value: 'auto' (auto-detect)
- Passes ecosystem to analysis command

#### Updated run_analysis Function
```python
def run_analysis(mode, target, skip_update, skip_osv, ecosystem='auto'):
    # ...
    if ecosystem and ecosystem != 'auto':
        cmd.extend(['--ecosystem', ecosystem])
```

### 3. Command-Line Interface (main_github.py)

#### Added Ecosystem Argument
```python
parser.add_argument(
    "--ecosystem",
    type=str,
    choices=["auto", "npm", "pypi"],
    default="auto",
    help="Force specific ecosystem (auto-detect if not specified)"
)
```

#### Updated Analysis Call
```python
output_path = analyze_project_hybrid(
    target=target,
    input_mode=analysis_type,
    force_ecosystem=args.ecosystem if args.ecosystem != "auto" else None
)
```

### 4. Analysis Engine (analyze_supply_chain.py)

#### Updated analyze_project_hybrid Function
```python
def analyze_project_hybrid(
    target: str, 
    input_mode: str = "auto",
    use_agents: bool = True,
    force_ecosystem: str = None  # NEW PARAMETER
) -> str:
```

#### Ecosystem Detection Logic
```python
if force_ecosystem:
    ecosystem = force_ecosystem
    logger.info(f"Using forced ecosystem: {ecosystem}")
else:
    ecosystem = detect_ecosystem(project_dir)
    logger.info(f"Auto-detected ecosystem: {ecosystem}")
```

## Usage

### Web UI
1. Open the web interface at `http://localhost:5000`
2. Select analysis mode (GitHub or Local)
3. **Select ecosystem** (npm or Python)
4. Enter target (URL or path)
5. Click "Start Analysis"

### Command Line

#### Auto-detect ecosystem (default)
```bash
python main_github.py --github https://github.com/owner/repo
```

#### Force npm ecosystem
```bash
python main_github.py --github https://github.com/owner/repo --ecosystem npm
```

#### Force Python ecosystem
```bash
python main_github.py --local /path/to/python/project --ecosystem pypi
```

## Benefits

1. **Override Auto-Detection**: Users can force a specific ecosystem when auto-detection fails or is incorrect
2. **Multi-Language Projects**: Handle projects with both npm and Python dependencies by running separate analyses
3. **Explicit Control**: Users have full control over which ecosystem to analyze
4. **Better UX**: Clear visual indication of selected ecosystem in the UI

## Testing

### Test npm Ecosystem
```bash
python main_github.py --github https://github.com/bahmutov/pre-git --ecosystem npm
```
Expected: Analyzes package.json and npm dependencies

### Test Python Ecosystem
```bash
python main_github.py --local /path/to/python/project --ecosystem pypi
```
Expected: Analyzes requirements.txt or setup.py and Python dependencies

### Test Auto-Detection
```bash
python main_github.py --github https://github.com/owner/repo --ecosystem auto
```
Expected: Automatically detects ecosystem based on manifest files

## UI Screenshot Description

The UI now shows:
```
┌─────────────────────────────────────┐
│ SCAN                                │
├─────────────────────────────────────┤
│ ANALYSIS MODE                       │
│ ┌─────────┬─────────┐              │
│ │ GitHub  │ Local   │              │
│ └─────────┴─────────┘              │
│                                     │
│ ECOSYSTEM                           │
│ ┌──────────────┬──────────────┐    │
│ │ npm          │ Python       │    │
│ │ (JavaScript) │ (PyPI)       │    │
│ └──────────────┴──────────────┘    │
│                                     │
│ TARGET                              │
│ ┌─────────────────────────────────┐│
│ │ Enter GitHub repository URL...  ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │      START ANALYSIS             ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## Future Enhancements

1. **More Ecosystems**: Add support for Maven, RubyGems, Go, Rust
2. **Multi-Ecosystem Analysis**: Analyze multiple ecosystems in one scan
3. **Ecosystem Icons**: Add visual icons for each ecosystem
4. **Smart Detection**: Show detected ecosystem before analysis starts
5. **Ecosystem-Specific Options**: Add ecosystem-specific configuration options
