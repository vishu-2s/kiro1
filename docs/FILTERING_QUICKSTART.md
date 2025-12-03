# 🔍 Findings Filtering - Quick Start

## ⚡ 30-Second Guide

### How to Filter Findings

1. **Go to Report Tab** after analysis completes
2. **Click any severity card** (Critical, High, Medium, Low)
3. **See filtered findings** instantly
4. **Click again** to clear filter

That's it! 🎉

## 🎯 Visual Guide

### Step 1: See All Findings
```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│   21    │    5    │    3    │   14    │    4    │
│  TOTAL  │CRITICAL │  HIGH   │ MEDIUM  │   LOW   │
└─────────┴─────────┴─────────┴─────────┴─────────┘
         All cards are white (no filter)

📋 Showing all 21 findings below
```

### Step 2: Click "Critical"
```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│   21    │    5  ✓ │    3    │   14    │    4    │
│  TOTAL  │CRITICAL │  HIGH   │ MEDIUM  │   LOW   │
└─────────┴─────────┴─────────┴─────────┴─────────┘
         Critical card turns BLACK

📋 Showing only 5 critical findings below
```

### Step 3: Switch to "High"
```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│   21    │    5    │    3  ✓ │   14    │    4    │
│  TOTAL  │CRITICAL │  HIGH   │ MEDIUM  │   LOW   │
└─────────┴─────────┴─────────┴─────────┴─────────┘
         High card turns BLACK

📋 Showing only 3 high findings below
```

### Step 4: Clear Filter
```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│   21  ✓ │    5    │    3    │   14    │    4    │
│  TOTAL  │CRITICAL │  HIGH   │ MEDIUM  │   LOW   │
└─────────┴─────────┴─────────┴─────────┴─────────┘
         Click Total or same card again

📋 Showing all 21 findings below
```

## 🎨 What You'll See

### Active Filter Indicator
When a filter is active, you'll see:

**1. Black Card with Checkmark**
```
┌─────────✓───┐
│      5      │  ← Black background
│  CRITICAL   │  ← White text
└─────────────┘  ← Checkmark in corner
```

**2. Info Banner**
```
┌─────────────────────────────────────────────┐
│ Filter Active: Showing only critical       │
│ severity findings. [Clear filter]           │
└─────────────────────────────────────────────┘
```

**3. Updated Header**
```
🔍 Security Findings (Filtered: Critical - 5 of 21)
                     ↑                    ↑     ↑
                  Severity            Shown  Total
```

### No Filter Active
When no filter is active:

**1. All White Cards**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     21      │  │      5      │  │      3      │
│    TOTAL    │  │  CRITICAL   │  │    HIGH     │
└─────────────┘  └─────────────┘  └─────────────┘
```

**2. Tip Banner**
```
┌─────────────────────────────────────────────┐
│ 💡 Tip: Click on any statistic card below  │
│    to filter findings by severity.          │
└─────────────────────────────────────────────┘
```

**3. Simple Header**
```
🔍 Security Findings (Showing all 21 findings)
```

## 🖱️ Interaction Examples

### Example 1: Focus on Critical Issues
```
1. Click "Critical" card (5 findings)
2. Review all critical findings
3. Click "Total" to see all again
```

### Example 2: Review by Severity
```
1. Click "Critical" → Review 5 findings
2. Click "High" → Review 3 findings
3. Click "Medium" → Review 14 findings
4. Click "Low" → Review 4 findings
```

### Example 3: Toggle On/Off
```
1. Click "Critical" → Filter ON
2. Click "Critical" again → Filter OFF
3. Back to all findings
```

## 💡 Pro Tips

### Tip 1: Quick Navigation
Click severity cards to jump between finding types without scrolling.

### Tip 2: Count Verification
Use filters to verify the count matches what you expect.

### Tip 3: Focus Mode
Filter to critical/high to focus on urgent issues first.

### Tip 4: Clear Quickly
Click "Total Findings" card for instant clear.

### Tip 5: Visual Scanning
The black card makes it obvious which filter is active.

## 🎯 Common Workflows

### Workflow 1: Triage Critical Issues
```
1. Run analysis
2. Go to Report tab
3. Click "Critical" card
4. Review and document critical findings
5. Click "High" card
6. Review high severity findings
7. Click "Total" when done
```

### Workflow 2: Verify Counts
```
1. See "5 Critical" in card
2. Click "Critical" card
3. Count findings in list
4. Verify it matches (5 findings)
5. Repeat for other severities
```

### Workflow 3: Focus Analysis
```
1. Click "Critical" + "High" (future: multi-select)
2. Currently: Click "Critical" first
3. Review critical findings
4. Then click "High"
5. Review high findings
```

## 🚀 Try It Now

### Quick Test
1. Start Spyder: `python app.py`
2. Run an analysis
3. Go to Report tab
4. Click different severity cards
5. Watch findings update instantly!

## 📊 What Gets Filtered

### Filtered Elements
- ✅ Finding cards in the list
- ✅ Package groups
- ✅ Individual findings
- ✅ Count in header

### Not Filtered
- ❌ Statistics cards (always show totals)
- ❌ Metadata section
- ❌ Analysis information

## 🎨 Visual States

### Card States

**Default (No Hover):**
```
Background: White
Border: Light grey
Text: Black
Cursor: Pointer
```

**Hover:**
```
Background: Light grey
Border: Black
Text: Black
Effect: Lift up 2px
Shadow: Subtle
```

**Active (Filtered):**
```
Background: Black
Border: Black
Text: White
Indicator: Checkmark ✓
```

## 🔧 Keyboard Users

While primarily mouse-driven:
- Tab to navigate cards
- Enter/Space to activate (browser default)
- Visual feedback for all states

## 📱 Mobile Users

Works great on mobile:
- Large touch targets
- Clear visual feedback
- Responsive layout
- Easy to tap

## ❓ FAQ

**Q: Can I filter by multiple severities?**
A: Not yet, but it's planned for future updates.

**Q: Does the filter persist after refresh?**
A: No, filters reset when you reload the page.

**Q: Can I filter by finding type?**
A: Not yet, currently only severity filtering.

**Q: What if a severity has 0 findings?**
A: You'll see a message: "No [severity] findings detected."

**Q: Can I export filtered results?**
A: Not yet, but you can manually copy the filtered view.

## 🎉 Benefits

### Speed
- ⚡ Instant filtering (no page reload)
- ⚡ One-click operation
- ⚡ Quick toggle on/off

### Clarity
- 👁️ Clear visual feedback
- 👁️ Active state indicator
- 👁️ Count information

### Efficiency
- 🎯 Focus on specific severities
- 🎯 Systematic review process
- 🎯 Less scrolling needed

---

🕷️ **SPYDER** - SMART FILTERING

**One Click. Instant Results.**

Filter your security findings by severity with a single click. Focus on what matters most, review systematically, and analyze efficiently.

**Try it now:** Click any severity card in the Report tab!
