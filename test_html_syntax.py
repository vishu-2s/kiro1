"""Quick test to check if the HTML file has valid structure"""
import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for common JavaScript syntax errors
errors = []

# Check for unmatched template literals
backticks = content.count('`')
if backticks % 2 != 0:
    errors.append(f"Unmatched backticks: {backticks} (should be even)")

# Check for unmatched curly braces in JavaScript sections
script_start = content.find('<script>')
script_end = content.rfind('</script>')
if script_start != -1 and script_end != -1:
    script_content = content[script_start:script_end]
    open_braces = script_content.count('{')
    close_braces = script_content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unmatched braces in script: {{ {open_braces} vs }} {close_braces}")

# Check for unmatched parentheses
open_parens = content.count('(')
close_parens = content.count(')')
if open_parens != close_parens:
    errors.append(f"Unmatched parentheses: ( {open_parens} vs ) {close_parens}")

if errors:
    print("❌ HTML/JavaScript Syntax Errors Found:")
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print("✅ HTML file syntax looks good!")
    print(f"   - Backticks: {backticks} (balanced)")
    print(f"   - File size: {len(content)} characters")
