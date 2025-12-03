# Debug: Analysis Shows "Idle" Immediately

## What to Check

### 1. Server Console Output
When you click "Start Analysis", look at the terminal where Flask is running. You should see:

```
=== /api/analyze endpoint called ===
Request data: {'mode': 'local', 'target': '...', ...}
Mode: local, Target: ..., Confidence: 0.7
Starting background thread...
Thread started: True
Starting local analysis for: ...
Executing command: python main_github.py --local ...
```

If you don't see these messages, the request isn't reaching the server.

### 2. Check for Errors
Look for any error messages in the server console:
- Python tracebacks
- "ERROR in run_analysis:"
- "Analysis failed with exit code"

### 3. Browser Console
Press F12, Console tab. Look for:
- "Starting analysis..." message
- Any red error messages
- Network errors

### 4. Network Tab
Press F12, Network tab:
- Look for POST request to `/api/analyze`
- Should return 200 OK with `{"status": "started"}`
- If 400 or 500, there's an error

## Common Causes

### Cause 1: Analysis Already Running
**Symptom**: Server says "Analysis already running"

**Solution**: 
- Restart the Flask server
- The state gets stuck sometimes

### Cause 2: Invalid Target Path
**Symptom**: Analysis starts but fails immediately

**Solution**:
- Check the path exists
- Use absolute path: `C:\Users\...` not relative
- No spaces or special characters

### Cause 3: Python Script Error
**Symptom**: "Analysis failed with exit code 1"

**Solution**:
- Check server console for Python errors
- Try running manually:
  ```bash
  python main_github.py --local "C:\path\to\folder"
  ```

### Cause 4: Missing Dependencies
**Symptom**: Import errors in server console

**Solution**:
```bash
pip install -r requirements.txt
```

### Cause 5: Thread Not Starting
**Symptom**: "Thread started: False" in console

**Solution**:
- Restart Flask server
- Check Python version (needs 3.8+)

## Manual Test

### Test 1: Run Analysis Directly
```bash
python main_github.py --local "C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_eventstream" --confidence 0.7 --skip-update --skip-osv
```

Should complete and create a file in `outputs/`.

### Test 2: Check API Endpoint
```bash
# In PowerShell
$body = @{
    mode = "local"
    target = "C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_eventstream"
    confidence = 0.7
    skip_update = $true
    skip_osv = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/api/analyze -Method POST -Body $body -ContentType "application/json"
```

Should return: `{"status":"started"}`

### Test 3: Check State
While analysis is running, check:
```bash
# In another terminal or PowerShell
Invoke-WebRequest -Uri http://localhost:5000/api/status | Select-Object -Expand Content
```

Should show `"running": true`

## What to Share

If still showing Idle, share:

1. **Complete server console output** from when you click "Start Analysis"
2. **Browser console output** (F12 → Console)
3. **Network tab** (F12 → Network → /api/analyze request → Response)
4. **Result of manual test**:
   ```bash
   python main_github.py --local "your_path" --skip-update --skip-osv
   ```

## Quick Fixes

### Fix 1: Restart Server
```bash
# Stop server (Ctrl+C)
python app.py
# Try analysis again
```

### Fix 2: Use Absolute Path
Instead of:
```
C:\Users\VISHAKHA\Downloads\vuln_samples\vuln_eventstream
```

Try:
```
C:/Users/VISHAKHA/Downloads/vuln_samples/vuln_eventstream
```
(Forward slashes instead of backslashes)

### Fix 3: Check Permissions
Make sure the target directory is readable:
```bash
# Windows
icacls "C:\path\to\folder"

# Should show Read permissions
```

### Fix 4: Simplify Path
Try a simpler path without spaces:
```
C:\temp\test
```

---

**With the new debug logging, the server console will tell us exactly what's happening!**
