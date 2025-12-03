# Web Application Verification Checklist

Use this checklist to verify that the web application is working correctly.

## ✅ Pre-Launch Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Flask installed (`pip install flask`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file exists with API keys
- [ ] `OPENAI_API_KEY` set in `.env`
- [ ] `outputs/` directory exists (created automatically)

### File Structure
- [ ] `app.py` exists
- [ ] `templates/` directory exists
- [ ] `templates/index.html` exists
- [ ] `main_github.py` exists (backend)
- [ ] All tool files exist in `tools/` directory

## 🚀 Launch Checklist

### Starting the Server
- [ ] Run `python app.py`
- [ ] Server starts without errors
- [ ] See "Running on http://localhost:5000" message
- [ ] No port conflict errors

### Accessing the Interface
- [ ] Open browser
- [ ] Navigate to `http://localhost:5000`
- [ ] Page loads successfully
- [ ] No 404 or 500 errors
- [ ] See purple gradient header
- [ ] See "Multi-Agent Security Analysis System" title

## 🎨 UI Verification Checklist

### Dashboard Tab
- [ ] Dashboard tab is active by default
- [ ] See "Analysis Configuration" section
- [ ] See three mode buttons (GitHub/Local/SBOM)
- [ ] GitHub mode is active by default
- [ ] See target input field
- [ ] Placeholder text shows GitHub URL example
- [ ] See confidence threshold input (default 0.7)
- [ ] See two checkboxes (Skip update, Skip OSV)
- [ ] See "Start Analysis" button
- [ ] See status bar (shows "Idle")
- [ ] See logs container with initial message

### Mode Toggle
- [ ] Click "Local Directory" button
- [ ] Button becomes active (purple background)
- [ ] Placeholder text changes to local path example
- [ ] Click "SBOM File" button
- [ ] Button becomes active
- [ ] Placeholder text changes to SBOM path example
- [ ] Click "GitHub Repository" button
- [ ] Returns to GitHub mode

### Report Tab
- [ ] Click "Report" tab
- [ ] Tab becomes active
- [ ] See "No Report Available" message
- [ ] See document icon
- [ ] See "Run an analysis to generate a security report" text

## 🧪 Functionality Checklist

### Test Analysis (SBOM Mode - Fastest)
- [ ] Switch to Dashboard tab
- [ ] Select "SBOM File" mode
- [ ] Enter: `./artifacts/backend-sbom.json`
- [ ] Set confidence: 0.7
- [ ] Check "Skip database update" (for speed)
- [ ] Check "Skip OSV queries" (for speed)
- [ ] Click "Start Analysis"
- [ ] Button text changes to "⏳ Starting..."
- [ ] Button becomes disabled
- [ ] Status bar changes to "Running" (orange)
- [ ] See spinner animation
- [ ] Logs start appearing
- [ ] Logs auto-scroll to bottom
- [ ] See timestamps in logs
- [ ] See [INFO] level indicators
- [ ] Wait for completion (should be fast)
- [ ] Status bar changes to "Completed" (green)
- [ ] Button re-enables
- [ ] Button text returns to "Start Analysis"
- [ ] Automatically switches to Report tab
- [ ] See statistics dashboard
- [ ] See finding cards (if any)
- [ ] See metadata section

### Report Verification
- [ ] See "Security Analysis Report" title
- [ ] See statistics cards (Total, Critical, High, Medium, Low)
- [ ] Numbers in statistics cards are correct
- [ ] See "Analysis Metadata" section
- [ ] Target is correct
- [ ] Analysis type is correct
- [ ] Timestamp is present
- [ ] See "Security Findings" section
- [ ] Findings are displayed (if any)
- [ ] Each finding has:
  - [ ] Package name
  - [ ] Version (if available)
  - [ ] Severity badge (colored)
  - [ ] Finding type
  - [ ] Confidence score
  - [ ] Evidence list (if available)
  - [ ] Recommendations (if available)

### Status Polling
- [ ] Start a new analysis
- [ ] Open browser developer tools (F12)
- [ ] Go to Network tab
- [ ] See requests to `/api/status` every 1 second
- [ ] Requests return 200 OK
- [ ] Response includes logs array
- [ ] Response includes running status
- [ ] Polling stops when analysis completes

### Multiple Analyses
- [ ] Run first analysis
- [ ] Wait for completion
- [ ] Run second analysis (different target)
- [ ] Previous logs are cleared
- [ ] New logs appear
- [ ] New report replaces old one
- [ ] Check `outputs/` directory
- [ ] See multiple result files

## 🔧 API Endpoint Checklist

### POST /api/analyze
- [ ] Accepts JSON request
- [ ] Returns {"status": "started"}
- [ ] Rejects empty target
- [ ] Rejects invalid confidence
- [ ] Rejects if analysis already running

### GET /api/status
- [ ] Returns current status
- [ ] Returns logs array
- [ ] Returns running boolean
- [ ] Returns result_file when complete
- [ ] Returns start_time
- [ ] Returns end_time when complete

### GET /api/report
- [ ] Returns 404 if no report
- [ ] Returns JSON report when available
- [ ] Report has findings array
- [ ] Report has metadata object

### GET /api/reports
- [ ] Returns array of reports
- [ ] Each report has filename
- [ ] Each report has size
- [ ] Each report has modified timestamp
- [ ] Reports sorted by date (newest first)

## 🐛 Error Handling Checklist

### Invalid Input
- [ ] Try empty target → See error
- [ ] Try invalid confidence (e.g., 2.0) → Handled gracefully
- [ ] Try starting while running → See error message

### Network Errors
- [ ] Stop server while page is open
- [ ] Try to start analysis → See error
- [ ] Restart server
- [ ] Refresh page → Works again

### File Errors
- [ ] Try non-existent SBOM file
- [ ] See error in logs
- [ ] Status changes to "Failed"
- [ ] Button re-enables

## 📱 Responsive Design Checklist

### Desktop (1400px+)
- [ ] Layout looks good
- [ ] Statistics in 5 columns
- [ ] All elements visible
- [ ] No horizontal scroll

### Tablet (768px - 1399px)
- [ ] Layout adjusts
- [ ] Statistics in 3 columns
- [ ] Elements stack appropriately
- [ ] Still usable

### Mobile (< 768px)
- [ ] Layout is single column
- [ ] Statistics in 2 columns
- [ ] Buttons are touch-friendly
- [ ] Text is readable
- [ ] No elements cut off

## 🌐 Browser Compatibility Checklist

### Chrome/Edge
- [ ] Page loads correctly
- [ ] All features work
- [ ] Logs update in real-time
- [ ] Report displays correctly

### Firefox
- [ ] Page loads correctly
- [ ] All features work
- [ ] Logs update in real-time
- [ ] Report displays correctly

### Safari
- [ ] Page loads correctly
- [ ] All features work
- [ ] Logs update in real-time
- [ ] Report displays correctly

## 🎯 Performance Checklist

### Load Time
- [ ] Page loads in < 2 seconds
- [ ] No visible lag
- [ ] Smooth animations

### Polling Performance
- [ ] Status updates smoothly
- [ ] No browser freezing
- [ ] Memory usage stable
- [ ] CPU usage reasonable

### Large Reports
- [ ] Can handle 50+ findings
- [ ] Scrolling is smooth
- [ ] No rendering issues
- [ ] Page remains responsive

## 🔒 Security Checklist

### Local Deployment
- [ ] Server binds to localhost only
- [ ] No external access by default
- [ ] API keys not exposed in UI
- [ ] No sensitive data in logs

### Input Validation
- [ ] Target input is validated
- [ ] Confidence range is enforced
- [ ] Mode selection is validated
- [ ] No code injection possible

## 📊 Output Verification Checklist

### JSON Files
- [ ] Files created in `outputs/` directory
- [ ] Filename format: `YYYYMMDD_HHMMSS_findings.json`
- [ ] Valid JSON format
- [ ] Contains findings array
- [ ] Contains metadata object

### HTML Files (if generated)
- [ ] Files created in `outputs/` directory
- [ ] Filename format: `YYYYMMDD_HHMMSS_report.html`
- [ ] Valid HTML format
- [ ] Can be opened in browser
- [ ] Shows formatted report

## 🎓 User Experience Checklist

### First-Time User
- [ ] Interface is intuitive
- [ ] Placeholders are helpful
- [ ] Default values are sensible
- [ ] Error messages are clear
- [ ] Success feedback is obvious

### Returning User
- [ ] Can quickly start analysis
- [ ] Previous settings remembered (in session)
- [ ] Can access old reports
- [ ] Workflow is efficient

## 🚦 Final Verification

### Complete Workflow Test
1. [ ] Start server
2. [ ] Open browser
3. [ ] Select GitHub mode
4. [ ] Enter test repository URL
5. [ ] Start analysis
6. [ ] Watch logs update
7. [ ] Wait for completion
8. [ ] View report
9. [ ] Check statistics
10. [ ] Review findings
11. [ ] Verify output files
12. [ ] Run second analysis
13. [ ] Verify new report
14. [ ] Stop server
15. [ ] Restart server
16. [ ] Verify old reports still accessible

## ✅ Sign-Off

If all items are checked, the web application is ready to use! 🎉

### Issues Found
List any issues discovered during verification:

1. _____________________________________
2. _____________________________________
3. _____________________________________

### Notes
Additional observations or comments:

_____________________________________
_____________________________________
_____________________________________

---

**Verification Date:** _______________  
**Verified By:** _______________  
**Status:** ⬜ Pass  ⬜ Fail  ⬜ Pass with Notes
