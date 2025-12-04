# Backup History Display Feature

## Overview
Enhanced the History tab to display all backup files alongside regular reports, with the ability to view, download, and restore backups.

## Features Implemented

### 1. Backup File Listing

**Backend** (`app.py`):
```python
@app.route('/api/reports')
def list_reports():
    """List all available reports including backups"""
    reports = []  # Regular reports
    backups = []  # Backup files (contain 'backup' in filename)
    
    return jsonify({
        'reports': reports,
        'backups': backups
    })
```

**Separation Logic**:
- Files with 'backup' in filename → backups array
- Other JSON files → reports array
- Both sorted by modified date (newest first)

### 2. Visual Distinction

**Backup Row Styling**:
- Light yellow background (`#FFF9E6`)
- 📦 icon instead of # number
- "(BACKUP)" label next to name
- Orange "backup" badge
- Restore button (green)

**CSS**:
```css
.type-badge.backup {
    border-color: #F57C00;
    background: #FFF9E6;
    color: #F57C00;
    font-weight: 600;
}
```

### 3. Backup Actions

#### View Backup
- Click on backup row to view in Report tab
- Same functionality as regular reports

#### Download Backup
- Download button to save backup file locally
- Opens in new tab

#### Restore Backup
- Green "Restore" button on backup rows
- Confirmation dialog before restoring
- Creates backup of current report first
- Replaces current report with selected backup

### 4. Restore Functionality

**Frontend** (`templates/index.html`):
```javascript
async function restoreBackup(backupFilename) {
    if (!confirm('Are you sure you want to restore this backup?')) {
        return;
    }
    
    const response = await fetch('/api/restore-backup', {
        method: 'POST',
        body: JSON.stringify({ backup_filename: backupFilename })
    });
    
    // Show success/error message
    // Reload history
}
```

**Backend** (`app.py`):
```python
@app.route('/api/restore-backup', methods=['POST'])
def restore_backup():
    # 1. Backup current report
    # 2. Copy selected backup to current report
    # 3. Return success
```

## UI Display

### History Table with Backups

```
┌────────────────────────────────────────────────────────────────────────────┐
│ REPORT HISTORY                                                             │
├────┬──────────────┬────────┬──────────────┬──────────┬──────────┬─────────┤
│ #  │ Report Name  │ Type   │ Date         │ Findings │ Packages │ Actions │
├────┼──────────────┼────────┼──────────────┼──────────┼──────────┼─────────┤
│ #1 │ pre-git      │ github │ Dec 3, 5:50  │    11    │    7     │ View ⬇  │
├────┼──────────────┼────────┼──────────────┼──────────┼──────────┼─────────┤
│ 📦 │ pre-git      │ backup │ Dec 3, 5:37  │    11    │    7     │ View ⬇ ✓│
│    │ (BACKUP)     │        │              │          │          │         │
├────┼──────────────┼────────┼──────────────┼──────────┼──────────┼─────────┤
│ 📦 │ pre-git      │ backup │ Dec 3, 5:20  │    11    │    7     │ View ⬇ ✓│
│    │ (BACKUP)     │        │              │          │          │         │
└────┴──────────────┴────────┴──────────────┴──────────┴──────────┴─────────┘

Legend:
View = View report button
⬇ = Download button
✓ = Restore button (backups only)
```

### Backup Row Appearance

**Regular Report Row**:
```
│ #1 │ pre-git │ github │ Dec 3, 5:50 │ 11 │ 7 │ [View] [Download] │
```

**Backup Row** (yellow background):
```
│ 📦 │ pre-git (BACKUP) │ backup │ Dec 3, 5:37 │ 11 │ 7 │ [View] [Download] [Restore] │
```

## Restore Process

### Step-by-Step Flow

1. **User clicks "Restore" button** on backup row
2. **Confirmation dialog** appears:
   ```
   Are you sure you want to restore this backup?
   
   This will replace the current report with:
   demo_ui_comprehensive_report_backup_20251203_175001.json
   
   The current report will be backed up first.
   
   [Cancel] [OK]
   ```

3. **If confirmed**:
   - Current report backed up with new timestamp
   - Selected backup copied to current report location
   - Success toast notification shown
   - History table refreshed

4. **Result**:
   - Current report now shows restored data
   - Old current report saved as new backup
   - All backups preserved

### Safety Features

- **Double backup**: Current report backed up before restore
- **Confirmation required**: User must confirm restore action
- **Non-destructive**: Original backup file preserved
- **Reversible**: Can restore previous state from new backup

## Example Scenario

### Initial State
```
outputs/
├── demo_ui_comprehensive_report.json          # Current (Analysis #3)
├── demo_ui_comprehensive_report_backup_20251203_175001.json  # Analysis #2
└── demo_ui_comprehensive_report_backup_20251203_173000.json  # Analysis #1
```

### User Restores Analysis #2
```
outputs/
├── demo_ui_comprehensive_report.json          # Now Analysis #2 (restored)
├── demo_ui_comprehensive_report_backup_20251203_180530.json  # Analysis #3 (auto-backed up)
├── demo_ui_comprehensive_report_backup_20251203_175001.json  # Analysis #2 (original)
└── demo_ui_comprehensive_report_backup_20251203_173000.json  # Analysis #1
```

## API Endpoints

### GET /api/reports
**Response**:
```json
{
  "reports": [
    {
      "filename": "demo_ui_comprehensive_report.json",
      "size": 45678,
      "modified": "2025-12-03T17:50:01"
    }
  ],
  "backups": [
    {
      "filename": "demo_ui_comprehensive_report_backup_20251203_175001.json",
      "size": 45123,
      "modified": "2025-12-03T17:50:01"
    },
    {
      "filename": "demo_ui_comprehensive_report_backup_20251203_173000.json",
      "size": 44890,
      "modified": "2025-12-03T17:30:00"
    }
  ]
}
```

### POST /api/restore-backup
**Request**:
```json
{
  "backup_filename": "demo_ui_comprehensive_report_backup_20251203_175001.json"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Backup restored successfully",
  "restored_from": "demo_ui_comprehensive_report_backup_20251203_175001.json"
}
```

## Benefits

1. **Visibility**: See all backups in one place
2. **Easy Access**: View and download any backup
3. **Quick Restore**: One-click restore with safety confirmation
4. **History Tracking**: Compare results across multiple analyses
5. **Safety**: Automatic backup before restore prevents data loss
6. **Organization**: Clear visual distinction between reports and backups

## Usage

### Viewing Backups
1. Navigate to History tab
2. Scroll through list
3. Backup rows have yellow background and 📦 icon
4. Click any backup row to view its report

### Restoring a Backup
1. Find the backup you want to restore
2. Click the green "Restore" button
3. Confirm the action in the dialog
4. Wait for success notification
5. Current report now shows restored data

### Downloading Backups
1. Click "Download" button on any backup row
2. File downloads to your browser's download folder
3. Can be imported or analyzed separately

## Testing

### Test Backup Display
```bash
# Run multiple analyses to create backups
python main_github.py --github https://github.com/owner/repo --ecosystem npm
# Wait for completion
python main_github.py --github https://github.com/owner/repo --ecosystem npm
# Wait for completion

# Check outputs directory
ls -la outputs/demo_ui_comprehensive_report_backup_*.json

# Open UI and check History tab
# Should see backups with yellow background
```

### Test Restore Functionality
```bash
# In UI:
# 1. Go to History tab
# 2. Click "Restore" on a backup
# 3. Confirm dialog
# 4. Check that current report updated
# 5. Verify new backup created
```

## Future Enhancements

1. **Backup Management**:
   - Delete old backups
   - Auto-cleanup (keep last N backups)
   - Backup compression

2. **Comparison**:
   - Compare two reports side-by-side
   - Diff view showing changes
   - Highlight new/removed findings

3. **Backup Notes**:
   - Add notes/tags to backups
   - Search backups by notes
   - Filter by date range

4. **Export/Import**:
   - Export backup set as ZIP
   - Import backups from other systems
   - Sync backups to cloud storage

## Conclusion

The History tab now provides complete visibility into all analysis reports and backups, with easy restore functionality and safety features to prevent data loss.
