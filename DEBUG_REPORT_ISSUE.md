# Debug: Report Not Showing

## Steps to Debug

### 1. Check Browser Console
1. Press `F12` to open Developer Tools
2. Click the "Console" tab
3. Click the "Report" tab in the app
4. Look for messages:
   - `renderReport called with data:` - Shows the data being loaded
   - `Findings count:` - Shows how many findings were found
   - Any red error messages

### 2. Check Network Tab
1. Press `F12`
2. Click "Network" tab
3. Click "Report" tab in the app
4. Look for `/api/report` request
5. Click on it to see:
   - Status: Should be 200 OK
   - Response: Should show JSON data

### 3. Test API Directly
Open a new browser tab and go to:
```
http://localhost:5000/api/report
```

You should see JSON data. If you see an error, that's the problem.

### 4. Check Server Logs
Look at the terminal where Flask is running. When you click "Report" tab, you should see:
```
127.0.0.1 - - [date] "GET /api/report HTTP/1.1" 200 -
```

If you see 404 or 500, there's a server error.

## Common Issues

### Issue: "No report available" message
**Cause**: No analysis has been run yet, or result file not found

**Solution**:
1. Run an analysis first (Dashboard tab → Start Analysis)
2. Wait for it to complete
3. Then click Report tab

### Issue: Blank page or "Error Rendering Report"
**Cause**: JavaScript error in rendering

**Solution**:
1. Check browser console (F12)
2. Look for the error message
3. Share the error with me

### Issue: API returns 404
**Cause**: No result file exists

**Solution**:
```bash
# Check if output files exist
ls outputs/
# or on Windows
dir outputs
```

Should show `.json` files. If empty, run an analysis.

### Issue: API returns 500
**Cause**: Server error reading the file

**Solution**: Check server console for Python errors

## Manual Test

### Test 1: Check if Report File Exists
```bash
python test_webapp.py
```

Should show:
```
✅ Found X JSON file(s)
✅ Found X security findings
```

### Test 2: Load Report Manually
```python
import json

# Load the latest report
with open('outputs/security_analysis_analysis_20251201_221507_23d804c3_20251201_221508.json', 'r') as f:
    data = json.load(f)

print(f"Findings: {len(data.get('security_findings', []))}")
print(f"Metadata: {data.get('metadata', {})}")
```

### Test 3: Test API Endpoint
```bash
# Windows PowerShell
Invoke-WebRequest -Uri http://localhost:5000/api/report | Select-Object -Expand Content

# Linux/Mac
curl http://localhost:5000/api/report
```

Should return JSON data.

## What to Share

If report still doesn't show, share:

1. **Browser console output** (F12 → Console)
   - Copy all messages when you click Report tab

2. **Network tab info** (F12 → Network)
   - Status code of `/api/report` request
   - Response preview

3. **Server console output**
   - Any error messages in terminal

4. **Output files**
   ```bash
   ls -la outputs/
   # or
   dir outputs
   ```

5. **Test results**
   ```bash
   python test_webapp.py
   ```

## Quick Fix Attempts

### Attempt 1: Restart Everything
```bash
# Stop server (Ctrl+C)
# Close browser
# Restart server
python app.py
# Open new browser window
# Hard refresh (Ctrl+Shift+R)
```

### Attempt 2: Run New Analysis
1. Go to Dashboard tab
2. Enter a target
3. Click "Start Analysis"
4. Wait for completion
5. Should auto-switch to Report tab

### Attempt 3: Load Existing Report
If you have existing output files:
1. Restart server
2. Go directly to Report tab
3. Should load the most recent file

---

**Most likely: Run an analysis first, then the report will show!**
