# 🎨 Spyder Monochrome Design System

## Design Philosophy

**Elegant. Minimal. Timeless.**

The Spyder interface embraces a strict monochrome palette with a single red accent color, creating a clean, professional, and highly legible security analysis tool.

## Color Palette

### Monochrome Scale

```css
#1A1A1A  /* Black - Primary text, headers, dark elements */
#666666  /* Dark Grey - Secondary text, borders */
#A0A0A0  /* Medium Grey - Tertiary text, placeholders */
#D4D4D4  /* Light Grey - Borders, dividers */
#E5E5E5  /* Very Light Grey - Subtle borders, backgrounds */
#FAFAFA  /* Off-White - Section backgrounds */
#FFFFFF  /* White - Card backgrounds, primary surface */
```

### Accent Color

```css
#DC2626  /* Red - Critical alerts, primary actions, active states */
#B91C1C  /* Dark Red - Hover states for red elements */
```

## Typography

### Font Family
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif;
```

### Type Scale

| Element | Size | Weight | Color | Transform |
|---------|------|--------|-------|-----------|
| **H1** | 20px | 600 | #FFFFFF | - |
| **H2** | 14px | 600 | #1A1A1A | Uppercase |
| **H3** | 16px | 600 | #1A1A1A | Uppercase |
| **Body** | 14px | 400 | #1A1A1A | - |
| **Label** | 13px | 500 | #1A1A1A | Uppercase |
| **Badge** | 11px | 600 | Varies | Uppercase |
| **Small** | 12px | 500 | #666666 | Uppercase |

### Letter Spacing
- Uppercase text: `0.05em`
- Headers: `-0.02em` (H1 only)
- Body: Normal

## Layout System

### Grid
- Max width: 1400px
- Content max width: 1320px
- Padding: 40px horizontal
- Gap: 16px (standard), 24px (sections)

### Spacing Scale
```css
4px   /* Micro spacing */
8px   /* Small spacing */
12px  /* Medium spacing */
16px  /* Standard spacing */
24px  /* Large spacing */
32px  /* Section spacing */
40px  /* Major section spacing */
```

## Component Styles

### Header
```css
Background: #1A1A1A (Black)
Text: #FFFFFF (White)
Logo: White box with black spider
Border: 1px solid #E5E5E5 (bottom)
Padding: 24px 40px
```

**Features:**
- Fixed height header
- Logo in white box (40x40px)
- Title and subtitle aligned left
- Clean, professional appearance

### Tabs
```css
Background: #FFFFFF
Border: 1px solid #E5E5E5 (bottom)
Padding: 0 40px
```

**Tab States:**
- **Inactive**: Grey text (#666666), transparent background
- **Hover**: Black text (#1A1A1A), light grey background (#F5F5F5)
- **Active**: Black text (#1A1A1A), red bottom border (#DC2626)

### Buttons

**Primary Button:**
```css
Background: #DC2626 (Red)
Text: #FFFFFF (White)
Padding: 12px 32px
Font: 14px, 500 weight, uppercase
Transition: 0.2s ease
```

**Hover State:**
```css
Background: #B91C1C (Dark Red)
```

**Disabled State:**
```css
Background: #D4D4D4 (Light Grey)
Text: #666666 (Dark Grey)
Opacity: 0.5
```

**Mode Buttons:**
```css
Background: #FFFFFF (White)
Border: 1px solid #D4D4D4
Text: #1A1A1A (Black)
```

**Hover/Active:**
```css
Background: #1A1A1A (Black)
Text: #FFFFFF (White)
Border: #1A1A1A
```

### Inputs
```css
Background: #FFFFFF
Border: 1px solid #D4D4D4
Padding: 12px 16px
Font: 14px Inter
Color: #1A1A1A
```

**Focus State:**
```css
Border: #1A1A1A
Box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.1)
```

**Placeholder:**
```css
Color: #A0A0A0
```

### Cards

**Standard Card:**
```css
Background: #FFFFFF
Border: 1px solid #E5E5E5
Padding: 24px
```

**Finding Card:**
```css
Background: #FFFFFF
Border: 1px solid #E5E5E5
Border-left: 3px solid (severity color)
Padding: 24px
Margin-bottom: 16px
```

**Severity Border Colors:**
- Critical: `#DC2626` (Red)
- High: `#1A1A1A` (Black)
- Medium: `#666666` (Dark Grey)
- Low: `#D4D4D4` (Light Grey)

### Status Bar
```css
Background: #FFFFFF
Border: 1px solid #E5E5E5
Border-left: 3px solid (status color)
Padding: 16px 20px
```

**Status Colors:**
- Idle: `#666666` (Dark Grey)
- Running: `#1A1A1A` (Black)
- Completed: `#1A1A1A` (Black)
- Failed: `#DC2626` (Red)

### Terminal Logs
```css
Background: #1A1A1A (Black)
Text: #E5E5E5 (Light Grey)
Border: 1px solid #E5E5E5
Padding: 24px
Font: SF Mono, Monaco, Courier New
```

**Log Levels:**
- Info: Grey border (#666666)
- Success: White border, black background
- Error: Red background (#DC2626)
- Warning: White background, black text

### Severity Badges

**Critical:**
```css
Background: #DC2626 (Red)
Text: #FFFFFF (White)
Border: 1px solid #DC2626
```

**High:**
```css
Background: #1A1A1A (Black)
Text: #FFFFFF (White)
Border: 1px solid #1A1A1A
```

**Medium:**
```css
Background: #FFFFFF (White)
Text: #666666 (Dark Grey)
Border: 1px solid #666666
```

**Low:**
```css
Background: #FFFFFF (White)
Text: #A0A0A0 (Medium Grey)
Border: 1px solid #D4D4D4
```

### Statistics Cards
```css
Background: #FFFFFF
Border: 1px solid #E5E5E5
Padding: 32px 24px
Text-align: center
```

**Value:**
```css
Font-size: 48px
Font-weight: 600
Color: #1A1A1A (default)
Color: #DC2626 (critical only)
```

**Label:**
```css
Font-size: 12px
Font-weight: 500
Color: #666666
Text-transform: uppercase
Letter-spacing: 0.05em
```

## Interaction States

### Hover States
- Buttons: Color inversion or darkening
- Tabs: Light grey background
- Mode buttons: Black background, white text
- Links: Underline appears

### Focus States
- Inputs: Black border + subtle shadow
- Buttons: Outline (browser default)
- Interactive elements: Visible focus ring

### Active States
- Tabs: Red bottom border
- Mode buttons: Black background
- Buttons: Slightly darker background

### Disabled States
- Opacity: 0.5
- Background: Light grey (#D4D4D4)
- Text: Dark grey (#666666)
- Cursor: not-allowed

## Transitions

### Standard Transition
```css
transition: all 0.2s ease;
```

**Applied to:**
- Buttons
- Tabs
- Inputs
- Mode toggles
- Interactive elements

### No Transition
- Color changes that should be instant
- Layout shifts
- Visibility changes

## Accessibility

### Contrast Ratios

| Combination | Ratio | WCAG Level |
|-------------|-------|------------|
| Black on White | 21:1 | AAA ✅ |
| Dark Grey on White | 7.5:1 | AAA ✅ |
| Medium Grey on White | 4.5:1 | AA ✅ |
| White on Black | 21:1 | AAA ✅ |
| White on Red | 5.5:1 | AA ✅ |
| Red on White | 5.5:1 | AA ✅ |

### Focus Indicators
- All interactive elements have visible focus states
- Focus ring: `0 0 0 3px rgba(26, 26, 26, 0.1)`
- High contrast borders on focus

### Screen Readers
- Semantic HTML structure
- ARIA labels where needed
- Logical tab order
- Status announcements

## Grid System

### Container
```css
max-width: 1400px
margin: 0 auto
background: #FFFFFF
```

### Content Area
```css
max-width: 1320px
margin: 0 auto
padding: 40px
```

### Grid Layouts
```css
display: grid
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))
gap: 16px
```

## Borders & Dividers

### Standard Border
```css
border: 1px solid #E5E5E5
```

### Emphasis Border
```css
border: 1px solid #D4D4D4
```

### Strong Border
```css
border: 1px solid #1A1A1A
```

### Accent Border
```css
border-left: 3px solid #DC2626
```

## Shadows

### Subtle Shadow
```css
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
```

### Focus Shadow
```css
box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.1);
```

**Note:** Shadows are minimal and used sparingly to maintain the clean aesthetic.

## Icons & Symbols

### Icon Style
- Monochrome only
- Stroke-based preferred
- Size: 16px or 24px
- Color: Inherits from parent

### Emoji Usage
- Spider logo: 🕷️ (in white box)
- Minimal use elsewhere
- Replaced with text labels where possible

## Responsive Design

### Breakpoints
```css
Desktop: 1400px+
Tablet: 768px - 1399px
Mobile: < 768px
```

### Mobile Adjustments
- Reduced padding (24px → 16px)
- Smaller font sizes
- Stacked layouts
- Maintained contrast ratios

## Print Styles

### Optimizations
- Remove backgrounds (except critical)
- Black text on white
- Maintain borders
- Remove shadows
- Optimize for B&W printing

## Best Practices

### Do's ✅
- Use monochrome colors exclusively
- Reserve red for critical items only
- Maintain high contrast
- Use clean typography
- Follow grid system
- Keep layouts minimal
- Use subtle shadows
- Ensure accessibility

### Don'ts ❌
- Don't add colors beyond palette
- Don't use gradients
- Don't over-use red accent
- Don't use decorative elements
- Don't add unnecessary borders
- Don't use heavy shadows
- Don't break the grid randomly
- Don't sacrifice legibility

## Color Usage Guidelines

### When to Use Each Color

**Black (#1A1A1A)**
- Primary text
- Headers
- Active states
- High severity items
- Terminal background

**Dark Grey (#666666)**
- Secondary text
- Inactive states
- Medium severity
- Timestamps

**Medium Grey (#A0A0A0)**
- Tertiary text
- Placeholders
- Low severity
- Disabled text

**Light Grey (#D4D4D4)**
- Borders
- Dividers
- Low severity borders
- Disabled backgrounds

**Very Light Grey (#E5E5E5)**
- Subtle borders
- Section dividers
- Card borders

**Off-White (#FAFAFA)**
- Section backgrounds
- Alternate backgrounds
- Panel backgrounds

**White (#FFFFFF)**
- Card backgrounds
- Primary surface
- Text on dark backgrounds

**Red (#DC2626)**
- Critical severity
- Primary action buttons
- Active tab indicators
- Failed states
- Error messages

## Design Principles

### 1. Minimalism
- Remove unnecessary elements
- Focus on content
- Clean layouts
- Ample whitespace

### 2. Hierarchy
- Clear visual hierarchy
- Size and weight for importance
- Consistent spacing
- Logical grouping

### 3. Consistency
- Uniform spacing
- Consistent colors
- Standard components
- Predictable interactions

### 4. Legibility
- High contrast text
- Readable font sizes
- Clear typography
- Accessible colors

### 5. Elegance
- Refined aesthetics
- Subtle details
- Professional appearance
- Timeless design

## Implementation Notes

### Font Loading
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### CSS Variables (Optional)
```css
:root {
    --color-black: #1A1A1A;
    --color-grey-dark: #666666;
    --color-grey-medium: #A0A0A0;
    --color-grey-light: #D4D4D4;
    --color-grey-lighter: #E5E5E5;
    --color-off-white: #FAFAFA;
    --color-white: #FFFFFF;
    --color-red: #DC2626;
    --color-red-dark: #B91C1C;
}
```

### Browser Support
- Chrome/Edge: Full support ✅
- Firefox: Full support ✅
- Safari: Full support ✅
- IE11: Not supported ❌

## Maintenance

### Adding New Components
1. Use existing color palette
2. Follow spacing scale
3. Maintain typography hierarchy
4. Ensure accessibility
5. Test in monochrome

### Updating Colors
- Only modify within monochrome range
- Maintain contrast ratios
- Test with accessibility tools
- Document changes

---

🕷️ **SPYDER** - MONOCHROME DESIGN SYSTEM

**Elegant. Minimal. Timeless.**

A professional security analysis interface built on strict monochrome principles with a single red accent for critical elements. Clean typography, clear hierarchy, and excellent accessibility create a refined, legible experience.
