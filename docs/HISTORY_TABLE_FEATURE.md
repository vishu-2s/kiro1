# 📊 History Table Feature - Sortable & Searchable

## Overview

The Report History tab now features a **professional data table** with sorting, searching, and intelligent report naming extracted from analysis targets.

## New Features

### ✅ What's New

1. **Sortable Table** - Click column headers to sort
2. **Search Bar** - Filter reports by name, type, or date
3. **Smart Report Names** - Extracted from target paths
4. **More Metadata** - Findings count, packages count
5. **Type Badges** - Visual indicators for analysis type
6. **Quick Actions** - View and download buttons
7. **Result Counter** - Shows filtered vs total reports

## Table Columns

| Column | Description | Sortable |
|--------|-------------|----------|
| **#** | Report number (newest = highest) | ✅ Yes |
| **Report Name** | Extracted from target path | ✅ Yes |
| **Type** | Analysis type (GitHub/Local/SBOM) | ✅ Yes |
| **Date** | When analysis was run | ✅ Yes |
| **Findings** | Total security findings | ✅ Yes |
| **Packages** | Total packages analyzed | ✅ Yes |
| **Size** | File size in KB | ✅ Yes |
| **Actions** | View (👁️) and Download (⬇️) | - |

## Report Name Extraction

### How It Works

The system automatically extracts meaningful names from target paths:

**Examples:**

| Target Path | Extracted Name |
|-------------|----------------|
| `C:\Users\Lokesh-PC\Downloads\QA-Agency` | `QA-Agency` |
| `https://github.com/expressjs/express` | `expressjs/express` |
| `/home/user/projects/my-app` | `my-app` |
| `./artifacts/backend-sbom.json` | `backend-sbom.json` |

### Benefits

- ✅ **Recognizable** - See project names at a glance
- ✅ **Searchable** - Find reports by project name
- ✅ **Organized** - Group related analyses mentally
- ✅ **Professional** - Clean, readable names

## Sorting

### How to Sort

1. Click any column header
2. First click: Sort descending (↓)
3. Second click: Sort ascending (↑)
4. Third click: Toggle back

### Default Sort

- **Column**: Date
- **Direction**: Descending (newest first)

### Sort Examples

**By Findings (High to Low):**
```
Click "Findings" column
Shows reports with most findings first
```

**By Report Name (A to Z):**
```
Click "Report Name" column twice
Alphabetical order
```

**By Date (Oldest First):**
```
Click "Date" column twice
Chronological order
```

## Searching

### Search Bar

Located at the top of the History tab:
```
🔍 Search by report name, type, or date...
```

### What You Can Search

- **Report Names**: "QA-Agency", "express", "my-app"
- **Analysis Types**: "github", "local", "sbom"
- **Dates**: "Dec 3", "2024", "12/03"
- **Targets**: Any part of the full path

### Search Examples

**Find QA-Agency reports:**
```
Type: QA-Agency
Shows: All reports for QA-Agency project
```

**Find GitHub analyses:**
```
Type: github
Shows: All GitHub repository analyses
```

**Find recent reports:**
```
Type: Dec 3
Shows: All reports from December 3rd
```

**Find by path:**
```
Type: Downloads
Shows: All reports from Downloads folder
```

### Real-time Filtering

- Results update as you type
- Case-insensitive search
- Matches partial text
- Shows count: "Showing X of Y reports"

## Type Badges

Visual indicators for analysis type:

### GitHub Repository
```
[github_repository]  ← Black badge
```

### Local Directory
```
[local_directory]    ← Dark grey badge
```

### SBOM File
```
[sbom_file]          ← Light grey badge
```

## Actions

### View Button (👁️)
- Opens report in Report tab
- Shows full analysis
- Can filter and export

### Download Button (⬇️)
- Downloads JSON file
- Original report data
- Can import elsewhere

## User Interface

### Table Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search by report name, type, or date...                     │
├──┬──────────────┬──────────┬──────────┬─────────┬─────────┬────┤
│# │ Report Name  │ Type     │ Date     │Findings │Packages │Size│
├──┼──────────────┼──────────┼──────────┼─────────┼─────────┼────┤
│5 │ QA-Agency    │[local]   │Dec 3 5:52│   21    │   11    │40KB│
│4 │ express      │[github]  │Dec 3 5:47│   15    │   42    │38KB│
│3 │ my-app       │[local]   │Dec 2 3:15│    8    │   25    │35KB│
└──┴──────────────┴──────────┴──────────┴─────────┴─────────┴────┘
Showing 3 of 5 reports
```

### Hover Effects

- **Row Hover**: Light grey background
- **Column Header Hover**: Slightly darker background
- **Button Hover**: Black background (View), Grey (Download)

### Click Behavior

- **Row Click**: Opens report
- **Column Header Click**: Sorts by that column
- **Button Click**: Performs action (stops row click)

## Technical Details

### Data Loading

1. Fetches report list from `/api/reports`
2. Loads metadata from each JSON file
3. Extracts report names from targets
4. Calculates findings and packages
5. Renders sortable table

### Performance

- **Initial Load**: 1-3 seconds (depends on report count)
- **Sorting**: Instant (client-side)
- **Searching**: Instant (client-side)
- **Cached**: Metadata loaded once

### Storage

All data stored in browser memory:
- `allReports` - Full report list with metadata
- `currentSortColumn` - Active sort column
- `currentSortDirection` - Sort direction (asc/desc)

## Use Cases

### 1. Find Specific Project
```
1. Type project name in search
2. See all analyses for that project
3. Click to view latest
```

### 2. Compare Over Time
```
1. Search for project name
2. Sort by date
3. View oldest to newest
4. Track improvements
```

### 3. Find High-Risk Reports
```
1. Click "Findings" column
2. Sort descending
3. See reports with most findings
4. Review critical issues
```

### 4. Review Recent Analyses
```
1. Default view (sorted by date)
2. See newest reports first
3. Quick access to latest scans
```

### 5. Find Large Reports
```
1. Click "Size" column
2. Sort descending
3. See largest reports
4. Identify complex analyses
```

## Advantages

### Over Card View

**Before (Cards):**
- ❌ Hard to compare
- ❌ No sorting
- ❌ No searching
- ❌ Generic titles
- ❌ Limited metadata

**After (Table):**
- ✅ Easy comparison
- ✅ Sort any column
- ✅ Search everything
- ✅ Smart names
- ✅ Rich metadata

### Benefits

- **Faster Navigation** - Find reports quickly
- **Better Organization** - Sort by any criteria
- **More Information** - See key metrics at a glance
- **Professional** - Clean, data-table appearance
- **Scalable** - Works with hundreds of reports

## Responsive Design

### Desktop (1400px+)
- Full table with all columns
- Comfortable spacing
- Easy to read

### Tablet (768px - 1399px)
- Horizontal scroll if needed
- Maintained functionality
- Compact spacing

### Mobile (< 768px)
- Horizontal scroll
- Smaller fonts
- Touch-friendly buttons

## Keyboard Navigation

- **Tab**: Navigate between elements
- **Enter**: Activate focused button
- **Type**: Search automatically focuses

## Accessibility

- ✅ Semantic table markup
- ✅ Clear column headers
- ✅ High contrast text
- ✅ Keyboard accessible
- ✅ Screen reader friendly

## Future Enhancements

Possible improvements:
- 🔮 Multi-column sorting
- 🔮 Column visibility toggle
- 🔮 Export table to CSV
- 🔮 Bulk actions (delete, export)
- 🔮 Advanced filters (date range, severity)
- 🔮 Pagination for large datasets
- 🔮 Column resizing
- 🔮 Custom column order

## Troubleshooting

### Report Names Show "Unknown"
- Report metadata may be missing
- Target field not in JSON
- File may be corrupted

### Search Not Working
- Check JavaScript console for errors
- Verify search input has correct ID
- Refresh the page

### Sorting Not Working
- Click column header directly
- Check for JavaScript errors
- Verify data loaded correctly

### Slow Loading
- Many reports to process
- Network latency
- Large JSON files
- Normal for 50+ reports

---

🕷️ **SPYDER** - PROFESSIONAL HISTORY TABLE

**Sort. Search. Analyze.**

A professional data table interface for browsing your security analysis history. Find reports quickly, compare results, and track your security posture over time.

**Try it now:**
1. Click "History" tab
2. See your reports in table format
3. Click columns to sort
4. Use search to filter
5. Click rows to view reports

---

**Added:** December 3, 2024
**Features:** Sorting, Searching, Smart Names
**Status:** ✅ Complete and Ready to Use
