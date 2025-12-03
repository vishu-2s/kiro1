# 🚀 Installation Guide - PDF Export & Report History

## Quick Start (2 Minutes)

### 1. Install Dependencies
```bash
pip install weasyprint>=60.0
```

### 2. Restart Spyder
```bash
python app.py
```

### 3. You're Done!
- PDF Export button now available in Report tab
- History tab now shows all past reports

---

## Detailed Installation

### Step 1: Install WeasyPrint

**On Windows:**
```bash
pip install weasyprint

# If you get errors, install GTK:
# Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
# Run the installer, then retry: pip install weasyprint
```

**On macOS:**
```bash
# Install system dependencies first
brew install cairo pango gdk-pixbuf libffi

# Then install WeasyPrint
pip install weasyprint
```

**On Linux (Ubuntu/Debian):**
```bash
# Install system dependencies
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

# Then install WeasyPrint
pip install weasyprint
```

**On Linux (Fedora/RHEL):**
```bash
# Install system dependencies
sudo dnf install python3-cffi python3-brotli pango

# Then install WeasyPrint
pip install weasyprint
```

### Step 2: Verify Installation
```bash
python -c "import weasyprint; print('WeasyPrint installed successfully!')"
```

If you see "WeasyPrint installed successfully!" you're good to go!

### Step 3: Restart Spyder
```bash
# Stop the current server (Ctrl+C)
# Start again
python app.py
```

---

## Troubleshooting

### WeasyPrint Installation Fails

**Error: "cairo" not found**
```bash
# Windows: Install GTK (see link above)
# macOS: brew install cairo
# Linux: sudo apt-get install libcairo2-dev
```

**Error: "pango" not found**
```bash
# Windows: Install GTK (see link above)
# macOS: brew install pango
# Linux: sudo apt-get install libpango1.0-dev
```

**Error: "gdk-pixbuf" not found**
```bash
# Windows: Install GTK (see link above)
# macOS: brew install gdk-pixbuf
# Linux: sudo apt-get install libgdk-pixbuf2.0-dev
```

### PDF Generation Fails

**Error: "WeasyPrint not installed"**
```bash
# Reinstall WeasyPrint
pip uninstall weasyprint
pip install weasyprint
```

**Error: "Failed to generate PDF"**
- Check console for detailed error
- Verify report data is valid
- Try with a smaller report first
- Check system dependencies installed

### History Tab Empty

**No reports showing:**
- Run an analysis first
- Check `outputs/` folder exists
- Verify JSON files present
- Refresh the page

---

## Verification Steps

### 1. Test PDF Export
```
1. Run an analysis
2. Go to Report tab
3. Click "📄 Export PDF"
4. Should see "Generating PDF..." message
5. PDF should download automatically
6. Check outputs/ folder for PDF file
```

### 2. Test Report History
```
1. Click "History" tab
2. Should see past reports (if any)
3. Click on a report card
4. Should switch to Report tab
5. Should show full report
```

### 3. Test Download
```
1. Go to History tab
2. Click "Download" on any report
3. JSON file should download
4. Verify file opens correctly
```

---

## System Requirements

### Minimum
- Python 3.8+
- 100 MB free disk space
- Modern web browser

### Recommended
- Python 3.10+
- 500 MB free disk space
- Chrome/Edge/Firefox (latest)

### Dependencies
```
weasyprint>=60.0    # PDF generation
flask>=3.0.0        # Web framework
```

---

## File Locations

### Application Files
```
spyder/
├── app.py                    # Main application
├── templates/
│   └── index.html           # Web interface
├── outputs/                 # Reports stored here
│   ├── *.json              # Analysis reports
│   └── *.pdf               # Exported PDFs
└── requirements.txt         # Dependencies
```

### Generated Files
```
outputs/
├── 20241203_103045_findings.json          # Report
├── spyder_report_20241203_103045.pdf      # PDF
└── ...
```

---

## Quick Commands

### Install Everything
```bash
pip install -r requirements.txt
```

### Update Dependencies
```bash
pip install --upgrade weasyprint flask
```

### Check Installation
```bash
python -c "import weasyprint, flask; print('All dependencies OK!')"
```

### Start Application
```bash
python app.py
```

### Access Application
```
http://localhost:5000
```

---

## Platform-Specific Notes

### Windows
- May need GTK runtime for WeasyPrint
- Use PowerShell or CMD
- Paths use backslashes: `outputs\report.pdf`

### macOS
- Use Homebrew for system dependencies
- Use Terminal
- Paths use forward slashes: `outputs/report.pdf`

### Linux
- Use apt/dnf for system dependencies
- Use Terminal
- Paths use forward slashes: `outputs/report.pdf`

---

## Docker Installation (Optional)

If you prefer Docker:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Run application
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t spyder .
docker run -p 5000:5000 -v $(pwd)/outputs:/app/outputs spyder
```

---

## Uninstallation

If you need to remove the features:

```bash
# Uninstall WeasyPrint
pip uninstall weasyprint

# Remove PDF exports (optional)
rm outputs/*.pdf

# Keep JSON reports (they're still useful)
```

---

## Support

### Getting Help

**Installation Issues:**
1. Check this guide first
2. Verify system dependencies
3. Check Python version
4. Try reinstalling

**Runtime Issues:**
1. Check console for errors
2. Verify files in outputs/
3. Test with simple report
4. Check browser console

**Documentation:**
- PDF_EXPORT_FEATURE.md
- REPORT_HISTORY_FEATURE.md
- NEW_FEATURES_COMPLETE.md

---

## Success Checklist

After installation, verify:

- [ ] WeasyPrint installed: `python -c "import weasyprint"`
- [ ] Spyder starts: `python app.py`
- [ ] Web interface loads: `http://localhost:5000`
- [ ] History tab visible
- [ ] Can run analysis
- [ ] Export PDF button visible
- [ ] PDF generates successfully
- [ ] History shows past reports
- [ ] Can view historical reports
- [ ] Can download JSON files

---

🕷️ **SPYDER** - INSTALLATION COMPLETE

**Ready to Export PDFs and Browse History!**

All dependencies installed and features ready to use. Start analyzing and generating professional reports!

**Next:** Run an analysis and try the new features!
