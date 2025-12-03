# 📚 Report History Feature

## Overview

Spyder now includes a **Report History** system that automatically stores all analysis reports and allows you to view them anytime through a dedicated History tab.

## Features

### ✅ What's Included

- **Automatic Storage** - All reports saved automatically
- **History Tab** - Dedicated interface to browse past reports
- **Visual Cards** - Clean, organized display of reports
- **Quick Access** - One-click to view any past report
- **Download Option** - Download JSON reports anytime
- **Chronological Order** - Newest reports first
- **Metadata Display** - Date, time, and file size for each report
- **Persistent Storage** - Reports remain until manually deleted

## How to Use

### 1. Access History
```
1. Open Spyder web interface
2. Click the "History" tab
3. See all your past reports
```

### 2. View Past Report
```
1. Click on any report card
2. Automatically switches to Report tab
3. Shows full report with all findings
4. Can filter, export PDF, etc.
```

### 3. Download Report
```
1. Click "Download" button on report card
2. Downloads JSON file
3. Can be imported or analyzed elsewhere
```

## History Tab Interface

### Layout
```
┌─────────────────────────────────────────────────────┐
│ REPORT HISTORY                                      │
├─────────────────────────────────────────────────────┤
│ 💡 Tip: All your past analysis reports are stored  │
│    here. Click on any report to view it.            │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Report 3 │  │ Report 2 │  │ Report 1 │         │
│  │ Dec 3    │  │ Dec 2    │  │ Dec 1    │         │
│  │ 10:30 AM │  │ 3:45 PM  │  │ 9:15 AM  │         │
│  │ 45.2 KB  │  │ 38.7 KB  │  │ 52.1 KB  │         │
│  │[View][DL]│  │[View][DL]│  │[View][DL]│         │
│  └──────────┘  └──────────┘  └──────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Report Card
```
┌─────────────────────────────────────┐
│ 📊                            #3    │  ← Icon & Number
├─────────────────────────────────────┤
│ Security Analysis Report            │  ← Title
│                                     │
│ 📅 Dec 3, 2024                     │  ← Date
│ 🕐 10:30 AM                        │  ← Time
│ 💾 45.2 KB                         │  ← Size
├─────────────────────────────────────┤
│ [  View Report  ] [ Download ]     │  ← Actions
└─────────────────────────────────────┘
```

## Features in Detail

### 1. Automatic Storage
- **Every Analysis** - All reports automatically saved
- **No Action Needed** - Happens in background
- **JSON Format** - Standard, portable format
- **Unique Names** - Timestamped filenames
- **Location** - `outputs/` folder

### 2. Visual Organization
- **Grid Layout** - Clean, organized cards
- **Responsive** - Adapts to screen size
- **Chronological** - Newest first
- **Numbered** - Easy reference (#1, #2, #3...)
- **Metadata** - Date, time, size visible

### 3. Quick Actions
- **View** - Opens report in Report tab
- **Download** - Downloads JSON file
- **Click Card** - Same as View button
- **Hover Effect** - Visual feedback

### 4. Report Viewing
- **Full Report** - All findings and details
- **Filtering** - Can filter by severity
- **Export PDF** - Can export to PDF
- **Same Interface** - Familiar Report tab

## Storage Details

### File Location
```
outputs/
├── spyder_report_20241203_103045.json
├── spyder_report_20241203_154522.json
├── spyder_report_20241202_091234.json
└── ...
```

### File Naming
```
Format: [timestamp]_findings.json
        or security_analysis_[id]_[timestamp].json
Example: 20241203_103045_findings.json
```

### File Contents
```json
{
  "metadata": {
    "analysis_id": "...",
    "target": "...",
    "start_time": "...",
    "end_time": "..."
  },
  "summary": {
    "total_findings": 21,
    "critical_findings": 5,
    ...
  },
  "findings": [...],
  "security_findings": [...]
}
```

## Use Cases

### 1. Compare Analyses
- View multiple reports
- Compare findings over time
- Track remediation progress
- Identify trends

### 2. Historical Reference
- Review past scans
- Verify previous findings
- Check when issues were found
- Document security history

### 3. Audit Trail
- Maintain scan history
- Prove regular scanning
- Show compliance
- Track security posture

### 4. Re-analysis
- Review old findings
- Export to PDF again
- Share with new team members
- Document lessons learned

## API Endpoints

### List All Reports
```
GET /api/reports

Response: [
  {
    "filename": "20241203_103045_findings.json",
    "size": 46234,
    "modified": "2024-12-03T10:30:45"
  },
  ...
]
```

### Get Specific Report
```
GET /outputs/{filename}

Response: {
  "metadata": {...},
  "findings": [...],
  ...
}
```

## Technical Implementation

### Frontend (JavaScript)
```javascript
// Load report history
async function loadReportHistory() {
  const response = await fetch('/api/reports');
  const reports = await response.json();
  // Render cards...
}

// Load specific report
async function loadHistoricalReport(filename) {
  const response = await fetch(`/outputs/${filename}`);
  const data = await response.json();
  renderReport(data);
}
```

### Backend (Flask)
```python
@app.route('/api/reports')
def list_reports():
    """List all available reports"""
    reports = []
    for filename in os.listdir('outputs'):
        if filename.endswith('.json'):
            # Get file info
            reports.append({...})
    return jsonify(reports)
```

## Advantages

### Automatic
- ✅ No manual saving needed
- ✅ Never lose a report
- ✅ Always available
- ✅ Background operation

### Organized
- ✅ Clean visual interface
- ✅ Easy to browse
- ✅ Quick to find
- ✅ Chronological order

### Accessible
- ✅ One-click viewing
- ✅ Fast loading
- ✅ Full functionality
- ✅ Download option

### Persistent
- ✅ Stored on disk
- ✅ Survives restarts
- ✅ Can be backed up
- ✅ Portable format

## Best Practices

### Regular Cleanup
```bash
# Keep last 30 days
find outputs/ -name "*.json" -mtime +30 -delete

# Keep last 50 reports
ls -t outputs/*.json | tail -n +51 | xargs rm
```

### Backup Important Reports
```bash
# Backup to archive
mkdir -p archive/$(date +%Y-%m)
cp outputs/*.json archive/$(date +%Y-%m)/
```

### Organize by Project
```bash
# Create project folders
mkdir -p outputs/project-a
mkdir -p outputs/project-b
# Move reports manually or via script
```

## Troubleshooting

### No Reports Showing
1. Check `outputs/` folder exists
2. Verify JSON files present
3. Check file permissions
4. Refresh the History tab

### Report Won't Load
1. Verify file exists
2. Check JSON is valid
3. Look for console errors
4. Try downloading and checking manually

### Download Fails
1. Check browser settings
2. Verify file permissions
3. Try right-click → Save As
4. Check disk space

### Old Reports Missing
1. Check if files were deleted
2. Verify correct `outputs/` folder
3. Check file naming pattern
4. Look for backup copies

## Future Enhancements

Possible improvements:
- 🔮 Search/filter reports
- 🔮 Tags/labels for reports
- 🔮 Bulk operations (delete, export)
- 🔮 Report comparison view
- 🔮 Automatic cleanup (retention policy)
- 🔮 Cloud storage integration
- 🔮 Report sharing links
- 🔮 Favorites/bookmarks

## Integration Examples

### Backup Script
```bash
#!/bin/bash
# backup-reports.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="backups/reports_$DATE"

mkdir -p "$BACKUP_DIR"
cp outputs/*.json "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### Cleanup Script
```python
# cleanup-old-reports.py
import os
from datetime import datetime, timedelta

OUTPUTS_DIR = 'outputs'
DAYS_TO_KEEP = 30

cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)

for filename in os.listdir(OUTPUTS_DIR):
    if filename.endswith('.json'):
        filepath = os.path.join(OUTPUTS_DIR, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if file_time < cutoff_date:
            os.remove(filepath)
            print(f"Deleted: {filename}")
```

### Export All to PDF
```python
# export-all-pdfs.py
import requests
import json
import os

for filename in os.listdir('outputs'):
    if filename.endswith('.json'):
        with open(f'outputs/{filename}') as f:
            data = json.load(f)
        
        response = requests.post(
            'http://localhost:5000/api/export-pdf',
            json=data
        )
        
        if response.ok:
            result = response.json()
            print(f"Exported: {result['filename']}")
```

## Statistics

### View Report Count
```javascript
// In browser console
fetch('/api/reports')
  .then(r => r.json())
  .then(reports => console.log(`Total reports: ${reports.length}`))
```

### Calculate Total Size
```bash
# In terminal
du -sh outputs/
```

### Find Oldest Report
```bash
ls -lt outputs/*.json | tail -1
```

### Find Largest Report
```bash
ls -lhS outputs/*.json | head -1
```

---

🕷️ **SPYDER** - REPORT HISTORY

**Never Lose a Report. Access Anytime.**

All your security analysis reports are automatically stored and organized in an easy-to-browse interface. View past reports, compare findings, and maintain a complete audit trail.

**Browse now:** Click the "History" tab to see all your reports!
