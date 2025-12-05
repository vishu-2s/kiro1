# Spider-Themed Iconography Quick Reference

## 🕷 Spider Dividers

### Usage
```html
<!-- Standard divider with animated spider -->
<div class="spider-divider"></div>

<!-- Intricate web pattern -->
<div class="spider-divider web-pattern"></div>

<!-- Thin silk strand -->
<div class="spider-divider silk-strand"></div>
```

### Automatic Application
- Between Dashboard sections (after `.control-panel`)
- Between Report sections (`.report-section + .report-section`)
- Between recent scan items

### Customization
```css
.spider-divider {
    --spacing-lg: 24px;  /* Adjust vertical spacing */
}
```

---

## 🕸 Web Connectors

### Usage
```html
<!-- Horizontal connector with anchor points -->
<div class="web-connector-horizontal"></div>

<!-- Vertical connector -->
<div class="web-connector-vertical" style="height: 100px;"></div>

<!-- Diagonal connector -->
<div class="web-connector-diagonal"></div>

<!-- Curved silk strand -->
<div class="web-connector-curve"></div>
```

### Automatic Application
- Across stats grid (horizontal line)
- Between finding cards
- Between stat cards (subtle background)

### Animation
All connectors feature `silkStrandSway` animation - gentle vertical movement simulating silk in breeze.

---

## 👻 Glitched Symbols

### Usage
```html
<!-- Glitch effect with color layers -->
<div class="glitch-symbol" data-text="🕷">🕷</div>

<!-- Animated loading spider -->
<div class="loading-spider">🕷</div>

<!-- Glitched spinner (automatic) -->
<div class="spinner"></div>

<!-- Full branding screen -->
<div class="branding-screen">
    <h1>Spyder</h1>
    <p>AI-Powered Security Scanner</p>
</div>
```

### Automatic Application
- Status bar running indicator (🕷 icon)
- Loading spinners (color-shifting)
- No-report SVG icons
- Header badge icons (subtle glitch)

### Effects
- **Position Glitch:** Random horizontal shifts
- **Color Shift:** Cycles through orange → green → purple
- **Hue Rotation:** Dynamic color distortion
- **Scale Distortion:** Subtle size changes
- **Opacity Flicker:** Brief transparency changes

---

## 🎨 Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Pumpkin Orange | `#FF7518` | Primary accent, dividers, connectors |
| Ectoplasmic Green | `#39FF14` | Secondary accent, glitch layers |
| Haunted Purple | `#6A0DAD` | Tertiary accent, glitch layers |
| Deep Charcoal | `#0F0F0F` | Backgrounds |

---

## ⚡ Performance

All elements are GPU-accelerated:
```css
.animated-element {
    will-change: transform, opacity;
    transform: translateZ(0);
    backface-visibility: hidden;
}
```

**Target:** 60fps for all animations
**Optimization:** Only `transform` and `opacity` animated

---

## ♿ Accessibility

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
    /* All animations disabled */
    /* Decorative elements hidden */
}
```

### High Contrast
```css
@media (prefers-contrast: high) {
    /* Decorative elements hidden */
    /* Contrast ratios increased */
}
```

### Screen Readers
All decorative elements:
- Have `pointer-events: none`
- Should be marked with `aria-hidden="true"` in HTML
- Do not interfere with keyboard navigation

---

## 📐 Spacing System

All spacing uses 8px grid:
```css
--spacing-xs: 4px;   /* 0.5 units */
--spacing-sm: 8px;   /* 1 unit */
--spacing-md: 16px;  /* 2 units */
--spacing-lg: 24px;  /* 3 units */
--spacing-xl: 32px;  /* 4 units */
--spacing-2xl: 40px; /* 5 units */
```

---

## 🎭 Animation Timings

| Animation | Duration | Easing | Loop |
|-----------|----------|--------|------|
| spiderCrawl | 8s | ease-in-out | infinite |
| silkStrandSway | 4s | ease-in-out | infinite |
| glitchSymbol | 3s | ease-in-out | infinite |
| spiderGlitch | 1.5s | ease-in-out | infinite |
| spinnerGlitch | 2s | ease-in-out | infinite |
| svgGlitch | 4s | ease-in-out | infinite |
| brandingGlitch | 8s | ease-in-out | infinite |

---

## 🔧 Customization Examples

### Change Divider Color
```css
.spider-divider::before {
    background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 15px,
        #YOUR_COLOR 15px,
        #YOUR_COLOR 16px
    );
}
```

### Adjust Connector Opacity
```css
.web-connector-horizontal {
    opacity: 0.6; /* Default: 0.4 */
}
```

### Modify Glitch Intensity
```css
.glitch-symbol {
    animation-duration: 2s; /* Faster glitch */
}
```

### Disable Specific Elements
```css
.spider-divider {
    display: none;
}
```

---

## 🐛 Troubleshooting

### Dividers Not Showing
- Check that parent elements have proper spacing
- Verify CSS file is loaded after base styles
- Ensure no conflicting `display: none` rules

### Animations Not Playing
- Check browser supports CSS animations
- Verify `prefers-reduced-motion` is not set
- Ensure GPU acceleration is available

### Performance Issues
- Reduce number of animated elements
- Increase animation duration for slower devices
- Disable decorative elements on mobile

---

## 📱 Responsive Behavior

All elements are responsive:
- Dividers scale with container width
- Connectors adjust to parent dimensions
- Glitched symbols maintain aspect ratio
- Animations remain smooth on all screen sizes

---

## 🧪 Testing

Run the test suite:
```bash
python test_spider_iconography.py
```

View the demo:
```bash
# Open spider_iconography_demo.html in browser
# Or visit /spider_iconography_demo.html when app is running
```

---

## 📚 Requirements Validation

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 6.1 Spider-themed dividers | ✅ | `.spider-divider` with 3 variants |
| 6.2 Web-like connectors | ✅ | 4 connector types with animations |
| 6.3 Glitched branding symbols | ✅ | Multiple glitch effects and symbols |

---

## 🎯 Design Principles

1. **Subtle & Professional:** Low opacity, non-intrusive
2. **Brand Reinforcement:** Spider metaphor throughout
3. **Performance First:** GPU-accelerated, 60fps target
4. **Accessible:** Full reduced motion and high contrast support
5. **Consistent:** Uses Halloween color palette
6. **Non-Functional:** `pointer-events: none` on all decorative elements

---

## 📝 Notes

- All elements are purely decorative
- No functionality is affected by these additions
- Elements can be disabled without breaking the app
- Animations are optimized for performance
- Full browser fallback support included

---

## 🚀 Next Steps

Task 7 is complete! The spider-themed iconography is fully implemented and integrated with the Halloween theme. All requirements (6.1, 6.2, 6.3) have been met.

For questions or issues, refer to:
- `.kiro/specs/halloween-theme-transformation/design.md`
- `.kiro/specs/halloween-theme-transformation/TASK_7_COMPLETION.md`
- `test_spider_iconography.py`
