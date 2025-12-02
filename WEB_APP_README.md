# Multi-Agent Security Analysis System - Web Application

A modern web interface for the Multi-Agent Security Analysis System that allows you to analyze GitHub repositories, local directories, and SBOM files for security vulnerabilities.

## Features

- 🌐 **Multiple Analysis Modes**: GitHub repositories, local directories, or SBOM files
- 📊 **Real-time Dashboard**: Live execution logs with auto-scroll
- 📄 **Interactive Reports**: Detailed security findings with severity levels
- 🎨 **Modern UI**: Clean, responsive design with gradient themes
- ⚡ **Live Updates**: Status polling every 1 second during analysis
- 📈 **Statistics**: Visual summary of findings by severity

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here  # Optional, for GitHub API
```

### 3. Run the Web Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### Dashboard Tab

1. **Select Analysis Mode**:
   - 🌐 **GitHub Repository**: Analyze a GitHub repository by URL
   - 📁 **Local Directory**: Analyze a local project directory
   - 📋 **SBOM File**: Analyze an existing SBOM file

2. **Configure Analysis**:
   - Enter the target (URL, path, or file)
   - Set confidence threshold (0.0 - 1.0)
   - Optional: Skip database update or OSV API queries

3. **Start Analysis**:
   - Click "Start Analysis" button
   - Watch live logs in real-time
   - Status updates automatically

### Report Tab

- View detailed security findings
- See statistics by severity level
- Review evidence and recommendations
- Automatically switches to report after successful analysis

## Analysis Modes

### GitHub Repository

Analyzes a GitHub repository for supply chain vulnerabilities:

```
Example: https://github.com/owner/repository
```

Features:
- Fetches repository data and dependencies
- Checks Dependabot alerts
- Analyzes workflow runs
- Generates comprehensive SBOM

### Local Directory

Scans a local project directory:

```
Example: C:\Projects\myapp or /home/user/myapp
```

Features:
- Detects multiple package ecosystems
- Scans package files (package.json, requirements.txt, etc.)
- Generates local SBOM
- Saves findings to analysis directory

### SBOM File

Analyzes an existing SBOM file:

```
Example: ./artifacts/backend-sbom.json
```

Features:
- Fast analysis of pre-generated SBOMs
- Cross-references with malicious package database
- Queries OSV API for vulnerabilities
- Generates detailed findings

## Configuration Options

### Confidence Threshold

Set the minimum confidence level for findings (0.0 - 1.0):
- **0.7** (default): Balanced - good mix of precision and recall
- **0.8-0.9**: High confidence - fewer false positives
- **0.5-0.6**: Lower threshold - more findings, may include false positives

### Skip Database Update

Check this to skip updating the malicious package database:
- Useful for faster analysis when database is recent
- Database auto-updates every 24 hours by default

### Skip OSV API

Check this to skip querying the OSV API:
- Faster analysis but may miss some vulnerabilities
- Only uses local malicious package database

## Report Details

### Statistics Dashboard

- **Total Findings**: Overall count of security issues
- **Critical**: Immediate action required
- **High**: Should be addressed soon
- **Medium**: Should be reviewed
- **Low**: Minor issues or informational

### Finding Cards

Each finding includes:
- **Package Name & Version**: Affected package
- **Severity Level**: Critical, High, Medium, or Low
- **Finding Type**: Malicious package, vulnerability, typosquat, etc.
- **Confidence Score**: How confident the system is (0-100%)
- **Evidence**: Supporting information for the finding
- **Recommendations**: Suggested remediation actions

## Output Files

Analysis results are saved to the `outputs/` directory:

- `{timestamp}_findings.json`: JSON format with all findings
- `{timestamp}_report.html`: HTML report (if generated)

## API Endpoints

The web application exposes several REST API endpoints:

### POST /api/analyze

Start a new analysis:

```json
{
  "mode": "github|local|sbom",
  "target": "target_url_or_path",
  "confidence": 0.7,
  "skip_update": false,
  "skip_osv": false
}
```

### GET /api/status

Get current analysis status and logs:

```json
{
  "running": true,
  "status": "running|completed|failed|idle",
  "logs": [...],
  "result_file": "filename.json",
  "start_time": "ISO timestamp",
  "end_time": "ISO timestamp"
}
```

### GET /api/report

Get the latest analysis report (JSON format)

### GET /api/reports

List all available reports

### GET /outputs/{filename}

Download a specific report file

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, modify `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
```

### Analysis Not Starting

1. Check that all dependencies are installed
2. Verify `.env` file has valid API keys
3. Check console logs for error messages
4. Ensure `main_github.py` is in the same directory

### No Report Displayed

1. Wait for analysis to complete
2. Check the Dashboard tab for any errors in logs
3. Verify output files exist in `outputs/` directory
4. Try refreshing the Report tab

## Development

### Running in Debug Mode

The application runs in debug mode by default for development:

```python
app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
```

### Customizing the UI

Edit `templates/index.html` to customize:
- Colors and styling (CSS in `<style>` section)
- Layout and components (HTML structure)
- Behavior and interactions (JavaScript functions)

### Adding New Features

The Flask application structure:
- `app.py`: Main Flask application and API routes
- `templates/index.html`: Frontend UI
- `main_github.py`: Backend analysis engine (existing)

## Security Considerations

- The web application runs locally by default
- API keys are stored in `.env` file (not committed to git)
- Analysis runs in background threads
- Output files are saved locally

## Browser Compatibility

Tested and working on:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

Same as the main Multi-Agent Security Analysis System project.

## Support

For issues or questions:
1. Check the logs in the Dashboard tab
2. Review the main project README.md
3. Check the console output where `app.py` is running
