# 🕷️ Spyder Logo Placement Guide

## Quick Setup

1. Save your spider mascot image as: `spyder-logo.png`
2. Place it in this `static/` folder
3. Restart the Flask app (`python app.py`)
4. The logo will appear in the header with a floating animation!

## Image Specifications

### Recommended Format
- **Format**: PNG with transparent background
- **Size**: 200-300px width (will be displayed at 80px)
- **Aspect Ratio**: Square or slightly wider
- **Background**: Transparent (recommended) or solid color

### Current Mascot Design
Based on your reference image:
- Metallic blue-gray spider/robot
- Bright cyan glowing eyes
- Multiple articulated legs
- Tech-focused aesthetic
- Dark background (can be made transparent)

## Where It Appears

### Web Interface Header
```
┌─────────────────────────────────────────┐
│  [LOGO]  🕷️ Spyder                     │
│          AI-Powered Supply Chain        │
│          Security Scanner               │
└─────────────────────────────────────────┘
```

The logo will:
- Display at 80x80 pixels
- Float up and down with smooth animation
- Appear to the left of the title
- Be centered vertically with the text

## Alternative Placements (Future)

### Favicon
Create a 32x32px version for browser tabs:
```html
<link rel="icon" type="image/png" href="/static/favicon.png">
```

### Loading Screen
Use during analysis with spinning animation:
```css
.loading-logo {
    animation: spin 2s linear infinite;
}
```

### Report Header
Smaller version (40px) in generated reports

### Error Pages
Friendly spider mascot on 404/500 pages

## File Structure

```
static/
├── spyder-logo.png          ← Main logo (place here!)
├── favicon.png              ← Optional: 32x32 favicon
├── spyder-logo-small.png    ← Optional: 40px version
└── README.md                ← This file
```

## Testing

After placing the logo:

1. Start the app:
   ```bash
   python app.py
   ```

2. Open browser:
   ```
   http://localhost:5000
   ```

3. Check the header - you should see:
   - Your spider mascot floating gently
   - "Spyder" title next to it
   - Purple gradient background

## Troubleshooting

### Logo Not Showing?
- Check filename is exactly: `spyder-logo.png`
- Verify file is in `static/` folder
- Restart Flask app
- Clear browser cache (Ctrl+F5)

### Logo Too Large/Small?
Edit `templates/index.html` line with `.header-logo`:
```css
.header-logo {
    width: 80px;  /* Adjust this */
    height: 80px; /* And this */
}
```

### Animation Too Fast/Slow?
Edit the `@keyframes float` duration:
```css
animation: float 3s ease-in-out infinite;
              /* ↑ Change this number */
```

## Current Status

✅ HTML structure ready
✅ CSS styling configured
✅ Animation effects added
⏳ Waiting for logo image

Once you add `spyder-logo.png`, the branding will be complete!

---

🕷️ **Spyder** - Catching threats in the dependency web
