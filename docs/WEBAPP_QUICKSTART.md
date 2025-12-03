# 🚀 Spyder Web Application Quick Start Guide

## What You Get

A beautiful, modern web interface for Spyder security analysis with:

✅ **3 Analysis Modes**: GitHub repos, local folders, or SBOM files  
✅ **Live Logs**: Watch the analysis happen in real-time  
✅ **Interactive Reports**: Beautiful visualizations of security findings  
✅ **Auto-Refresh**: Status updates every second  
✅ **Easy Configuration**: Simple toggles and inputs  

## 🎯 Quick Start (3 Steps)

### Step 1: Ensure Dependencies

```bash
pip install flask
```

(Flask should already be installed from requirements.txt)

### Step 2: Start the Server

**Windows:**
```bash
start_webapp.bat
```

**Linux/Mac:**
```bash
chmod +x start_webapp.sh
./start_webapp.sh
```

**Or directly:**
```bash
python app.py
```

### Step 3: Open Your Browser

Navigate to: **http://localhost:5000**

## 🎨 Using the Web Interface

### Dashboard Tab

1. **Choose Your Mode**:
   - 🌐 **GitHub**: `https://github.com/owner/repo`
   - 📁 **Local**: `C:\Projects\myapp` or `/home/user/myapp`
   - 📋 **SBOM**: `./artifacts/backend-sbom.json`

2. **Enter Target**: Paste your URL or path

3. **Adjust Settings** (optional):
   - Confidence threshold (default: 0.7)
   - Skip database update (faster)
   - Skip OSV queries (faster)

4. **Click "Start Analysis"**: Watch the magic happen! ✨

### Report Tab

After analysis completes:
- View statistics dashboard
- Browse security findings
- See severity levels (Critical → Low)
- Read evidence and recommendations

## 📊 Example Workflows

### Analyze a GitHub Repository

```
Mode: GitHub
Target: https://github.com/expressjs/express
Confidence: 0.7
Click: Start Analysis
```

### Scan a Local Project

```
Mode: Local
Target: C:\Users\YourName\Projects\myapp
Confidence: 0.7
Click: Start Analysis
```

### Check an SBOM File

```
Mode: SBOM
Target: ./artifacts/backend-sbom.json
Confidence: 0.7
Click: Start Analysis
```

## 🎯 What Happens During Analysis

1. **Initialization**: System loads configuration
2. **Data Collection**: Fetches/scans target
3. **SBOM Generation**: Creates software bill of materials
4. **Vulnerability Detection**: Checks against databases
5. **AI Analysis**: Multi-agent collaboration
6. **Report Generation**: Creates findings report

Watch it all happen in the live logs! 📝

## 📁 Output Files

Results are saved in `outputs/` directory:

```
outputs/
├── 20231201_143022_findings.json    # JSON report
└── 20231201_143022_report.html      # HTML report (if generated)
```

## 🔧 Configuration Tips

### For Faster Analysis

- ✅ Check "Skip database update" (if recently updated)
- ✅ Check "Skip OSV queries" (uses local DB only)
- ✅ Use SBOM mode (if you have an SBOM file)

### For Comprehensive Analysis

- ❌ Uncheck all skip options
- 📊 Set confidence to 0.6-0.7
- 🌐 Use GitHub mode (gets most data)

## 🎨 UI Features

### Live Logs
- Auto-scrolls to latest message
- Color-coded by severity
- Timestamps for each event

### Status Bar
- 🟦 Idle: Ready to start
- 🟧 Running: Analysis in progress
- 🟩 Completed: Success!
- 🟥 Failed: Check logs for errors

### Report Dashboard
- Total findings count
- Breakdown by severity
- Visual severity badges
- Expandable finding cards

## 🐛 Troubleshooting

### "Port already in use"

Edit `app.py` line 165:
```python
app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
```

### "No report available"

1. Wait for analysis to complete
2. Check Dashboard logs for errors
3. Verify `outputs/` directory exists

### Analysis stuck

1. Check console where `app.py` is running
2. Look for error messages
3. Verify API keys in `.env` file

### Logs not updating

- Refresh the page
- Check browser console (F12)
- Verify server is still running

## 🎓 Pro Tips

1. **Keep Dashboard Open**: Watch logs during analysis
2. **Use SBOM Mode**: Fastest for repeated analysis
3. **Adjust Confidence**: Lower = more findings, higher = fewer false positives
4. **Save Reports**: Download from `outputs/` directory
5. **Multiple Analyses**: Previous reports remain available

## 🔒 Security Notes

- Runs locally on your machine
- API keys stay in `.env` file
- No data sent to external servers (except API calls)
- Output files saved locally

## 📱 Browser Support

Works best on:
- Chrome/Edge (recommended)
- Firefox
- Safari

## 🎉 That's It!

You now have a fully functional web interface for security analysis. Enjoy! 🛡️

---

**Need Help?** Check the full documentation in `WEB_APP_README.md`
