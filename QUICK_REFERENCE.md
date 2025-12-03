# Quick Reference - New Features

## For Users

### Cancel a Running Analysis
1. Start an analysis
2. Click the **"Cancel Analysis"** button (replaces Start button)
3. Wait for confirmation toast
4. Analysis will terminate gracefully

### Toast Notifications
- **Green border** = Success (analysis completed, etc.)
- **Red border** = Error (invalid input, failure, etc.)
- **Yellow border** = Warning (cancelled, etc.)
- **Blue border** = Info (general messages)
- Click **×** to dismiss manually
- Auto-dismisses after 5 seconds

### Loading Indicators
- **Dashboard stats** show "..." while loading
- **Recent scans** show spinner while loading
- **History** shows spinner with message while loading

---

## For Developers

### New API Endpoints

#### GET /api/reports
```python
# Pagination support
GET /api/reports?page=1&per_page=10&metadata_only=true

Response:
{
    "reports": [...],
    "total": 150,
    "page": 1,
    "per_page": 10,
    "total_pages": 15
}
```

#### POST /api/cancel
```python
# Cancel running analysis
POST /api/cancel

Response:
{
    "status": "cancelling"
}

Error (no analysis running):
{
    "error": "No analysis is running"
}
```

### New JavaScript Functions

#### showToast(message, type, duration)
```javascript
// Display a toast notification
showToast('Analysis started', 'success', 5000);
showToast('Invalid input', 'error', 5000);
showToast('Processing...', 'info', 0); // No auto-dismiss
```

#### cancelAnalysis()
```javascript
// Cancel the running analysis
await cancelAnalysis();
```

#### loadMoreFindings()
```javascript
// Load next page of findings (prepared for use)
loadMoreFindings();
```

### Configuration Constants

```javascript
// Polling intervals
const INITIAL_POLL_INTERVAL = 500;  // Fast polling (first 10)
const NORMAL_POLL_INTERVAL = 2000;  // Normal polling (after 10)

// Pagination
const FINDINGS_PER_PAGE = 20;       // Findings per page
```

### Backend State

```python
analysis_state = {
    'running': bool,        # Is analysis running?
    'status': str,          # idle/running/completed/failed/cancelled
    'logs': list,           # Log entries
    'result_file': str,     # Result filename
    'start_time': str,      # ISO timestamp
    'end_time': str,        # ISO timestamp
    'process': Popen,       # Subprocess (for cancellation)
    'cancelled': bool       # Was cancellation requested?
}
```

---

## Testing

### Test Cancel Functionality
```bash
# Start the app
python app.py

# In browser:
1. Go to http://localhost:5000
2. Enter a target (e.g., https://github.com/lodash/lodash)
3. Click "Start Analysis"
4. Immediately click "Cancel Analysis"
5. Verify toast shows "Cancellation requested"
6. Verify logs show "Analysis cancelled by user"
```

### Test Toast Notifications
```javascript
// Open browser console on http://localhost:5000
showToast('Test success', 'success');
showToast('Test error', 'error');
showToast('Test warning', 'warning');
showToast('Test info', 'info');
```

### Test Pagination
```bash
# Test API directly
curl "http://localhost:5000/api/reports?page=1&per_page=5"
```

### Test Adaptive Polling
```javascript
// Watch console logs during analysis
// Should see:
// - Fast polling (500ms) for first 5 seconds
// - Then switches to slow polling (2s)
```

---

## Troubleshooting

### Cancel button doesn't appear
- Check that analysis actually started
- Check browser console for errors
- Verify `/api/analyze` returned success

### Toasts don't show
- Check browser console for JavaScript errors
- Verify `showToast()` function exists
- Check if `.toast-container` is created in DOM

### Polling too fast/slow
- Check `INITIAL_POLL_INTERVAL` and `NORMAL_POLL_INTERVAL` constants
- Verify `pollCount` is incrementing
- Check browser Network tab for request frequency

### Cancellation doesn't work
- Verify `/api/cancel` endpoint exists
- Check Flask logs for errors
- Verify `analysis_state['process']` is set
- Check if subprocess is actually running

---

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Toast Notifications | ✅ | ✅ | ✅ | ✅ |
| Cancel Analysis | ✅ | ✅ | ✅ | ✅ |
| Adaptive Polling | ✅ | ✅ | ✅ | ✅ |
| Loading States | ✅ | ✅ | ✅ | ✅ |
| Animations | ✅ | ✅ | ✅ | ✅ |

Minimum versions:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Performance Tips

1. **Dashboard**: Only loads 10 most recent reports
2. **History**: Loads 100 reports max initially
3. **Polling**: Starts fast (500ms), then slows (2s)
4. **Findings**: Prepared for pagination (20 per page)
5. **Cancellation**: Graceful termination (SIGTERM → SIGKILL)

---

## Security Notes

- Cancel endpoint requires POST method (CSRF protection)
- Subprocess termination is graceful (5s timeout)
- No sensitive data in toast messages
- All user input is escaped in toasts

---

## Maintenance

### Adding New Toast Types
```javascript
// In CSS, add new class:
.toast.custom {
    border-left-color: #YOUR_COLOR;
}

// Use it:
showToast('Custom message', 'custom');
```

### Changing Polling Intervals
```javascript
// Adjust constants at top of script:
const INITIAL_POLL_INTERVAL = 1000;  // 1 second
const NORMAL_POLL_INTERVAL = 5000;   // 5 seconds
```

### Changing Findings Per Page
```javascript
// Adjust constant:
const FINDINGS_PER_PAGE = 50;  // Show 50 at a time
```

---

## Files Modified

1. **app.py**
   - Added `/api/cancel` endpoint
   - Updated `/api/reports` with pagination
   - Added cancellation logic in `run_analysis()`
   - Updated `analysis_state` structure

2. **templates/index.html**
   - Added toast notification CSS
   - Added cancel button HTML
   - Added `showToast()` function
   - Added `cancelAnalysis()` function
   - Updated `startPolling()` for adaptive intervals
   - Added loading states to `loadDashboard()`
   - Added loading states to `loadReportHistory()`
   - Replaced all `alert()` with `showToast()`

---

## Support

For issues or questions:
1. Check browser console for errors
2. Check Flask logs for backend errors
3. Review `PERFORMANCE_IMPROVEMENTS.md` for details
4. Test with simple repository first
