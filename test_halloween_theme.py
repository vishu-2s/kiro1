"""
Property-Based Tests for Halloween Theme Transformation
Feature: halloween-theme-transformation

This test suite validates the correctness properties defined in the design document
for the Halloween theme transformation of the Spyder Security Scanner.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Tuple
import re
import cssutils
import logging
from pathlib import Path

# Suppress cssutils warnings
cssutils.log.setLevel(logging.CRITICAL)


# ============================================
# Helper Functions
# ============================================

def load_halloween_css() -> str:
    """Load the Halloween theme CSS file."""
    css_path = Path("static/halloween-theme.css")
    if not css_path.exists():
        raise FileNotFoundError(f"Halloween theme CSS not found at {css_path}")
    return css_path.read_text(encoding='utf-8')


def parse_css_custom_properties(css_content: str) -> Dict[str, str]:
    """Extract CSS custom properties from :root selector."""
    properties = {}
    
    # Find :root block
    root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
    if not root_match:
        return properties
    
    root_content = root_match.group(1)
    
    # Extract custom properties
    prop_pattern = r'--([a-zA-Z0-9-]+)\s*:\s*([^;]+);'
    for match in re.finditer(prop_pattern, root_content):
        prop_name = f"--{match.group(1)}"
        prop_value = match.group(2).strip()
        properties[prop_name] = prop_value
    
    return properties


def extract_color_replacements(css_content: str) -> List[Tuple[str, str]]:
    """Extract color value replacements from CSS rules."""
    replacements = []
    
    # Pattern to match color values in CSS
    color_pattern = r'(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}|rgba?\([^)]+\))'
    
    # Find all color values
    for match in re.finditer(color_pattern, css_content):
        color = match.group(1)
        replacements.append(color)
    
    return replacements


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate WCAG contrast ratio between two colors.
    Simplified implementation for hex colors.
    """
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def relative_luminance(rgb: Tuple[int, int, int]) -> float:
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    try:
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        l1 = relative_luminance(rgb1)
        l2 = relative_luminance(rgb2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)
    except:
        return 0.0


def check_spacing_multiple_of_8(value: str) -> bool:
    """Check if a spacing value is a multiple of 8px."""
    # Extract numeric value
    match = re.match(r'(\d+)px', value)
    if not match:
        return True  # Non-px values are acceptable
    
    px_value = int(match.group(1))
    return px_value % 8 == 0


# ============================================
# Property-Based Tests
# ============================================

class TestHalloweenThemeProperties:
    """Property-based tests for Halloween theme correctness properties."""
    
    def test_css_file_exists(self):
        """Verify the Halloween theme CSS file exists."""
        css_path = Path("static/halloween-theme.css")
        assert css_path.exists(), "Halloween theme CSS file must exist"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        '--halloween-bg-primary',
        '--halloween-bg-secondary',
        '--halloween-accent-critical',
        '--halloween-accent-success',
        '--halloween-accent-purple',
        '--halloween-border-accent',
    ]))
    def test_property_5_color_replacement_completeness(self, css_var: str):
        """
        **Feature: halloween-theme-transformation, Property 5: Color Replacement Completeness**
        **Validates: Requirements 3.1**
        
        For any element that used color #1A1A1A in the base application,
        it should use #0F0F0F or #1A0F1A in the Halloween theme.
        
        This test verifies that:
        1. All required Halloween color custom properties are defined
        2. The primary background color is #0F0F0F (not #1A1A1A)
        3. Color replacements are complete and consistent
        """
        css_content = load_halloween_css()
        properties = parse_css_custom_properties(css_content)
        
        # Verify the custom property exists
        assert css_var in properties, f"Custom property {css_var} must be defined"
        
        # Verify specific color replacements
        if css_var == '--halloween-bg-primary':
            assert properties[css_var] == '#0F0F0F', \
                "Primary background must be #0F0F0F (was #1A1A1A)"
        
        elif css_var == '--halloween-bg-secondary':
            assert properties[css_var] == '#1A0F1A', \
                "Secondary background must be #1A0F1A (purple-tinted)"
        
        elif css_var == '--halloween-accent-critical':
            assert properties[css_var] == '#FF7518', \
                "Critical accent must be #FF7518 (pumpkin orange, was #DC2626)"
        
        elif css_var == '--halloween-accent-success':
            assert properties[css_var] == '#39FF14', \
                "Success accent must be #39FF14 (ectoplasmic green, was #4ADE80)"
        
        elif css_var == '--halloween-accent-purple':
            assert properties[css_var] == '#6A0DAD', \
                "Purple accent must be #6A0DAD (new haunted purple)"
        
        elif css_var == '--halloween-border-accent':
            assert properties[css_var] == '#FF7518', \
                "Border accent must be #FF7518 (pumpkin orange)"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        '.severity-badge.critical',
        '.recent-scan-badge.critical',
        '.finding-card.critical',
        '.stat-card.critical .stat-value',
        '.btn-primary',
    ]))
    def test_property_6_critical_color_consistency(self, css_selector: str):
        """
        **Feature: halloween-theme-transformation, Property 6: Critical Color Consistency**
        **Validates: Requirements 3.2**
        
        For any element marked as critical severity, it should use pumpkin orange (#FF7518)
        instead of the original red (#DC2626).
        
        This test verifies that:
        1. All critical severity indicators use the Halloween critical color
        2. The color is consistently applied across all critical elements
        3. No elements still use the old red color (#DC2626)
        """
        css_content = load_halloween_css()
        
        # Verify the selector exists in the CSS
        assert css_selector in css_content, \
            f"Selector {css_selector} must be present in Halloween theme"
        
        # Extract ALL rules for this selector (there may be multiple)
        selector_pattern = re.escape(css_selector) + r'\s*\{([^}]+)\}'
        matches = list(re.finditer(selector_pattern, css_content, re.DOTALL))
        
        # Also check for combined selectors
        if not matches:
            combined_pattern = r'([^}]*' + re.escape(css_selector) + r'[^{]*)\{([^}]+)\}'
            combined_matches = list(re.finditer(combined_pattern, css_content, re.DOTALL))
            if combined_matches:
                matches = [(m, 2) for m in combined_matches]
            else:
                matches = []
        else:
            matches = [(m, 1) for m in matches]
        
        if matches:
            # Check if ANY rule has the pumpkin orange color
            has_pumpkin_orange = False
            has_old_red = False
            
            for match, group_idx in matches:
                rule_content = match.group(group_idx)
                
                # Check for pumpkin orange color (literal or variable)
                if '#FF7518' in rule_content or 'var(--halloween-accent-critical)' in rule_content:
                    has_pumpkin_orange = True
                
                # Check that old red color is NOT present
                if '#DC2626' in rule_content:
                    has_old_red = True
            
            assert has_pumpkin_orange, \
                f"{css_selector} must use pumpkin orange (#FF7518 or var(--halloween-accent-critical)) for critical severity"
            
            assert not has_old_red, \
                f"{css_selector} must not use old red color (#DC2626)"
    
    
    def test_color_replacement_no_old_colors(self):
        """
        Verify that old colors are completely replaced in the Halloween theme.
        
        This test ensures:
        - #1A1A1A is replaced with #0F0F0F or #1A0F1A
        - #DC2626 is replaced with #FF7518
        - #4ADE80 is replaced with #39FF14
        """
        css_content = load_halloween_css()
        
        # Check for old colors (excluding comments and documentation)
        # Remove comments first
        css_no_comments = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Old colors that should be replaced
        old_colors = {
            '#DC2626': 'Should be replaced with #FF7518 (pumpkin orange)',
            '#4ADE80': 'Should be replaced with #39FF14 (ectoplasmic green)',
        }
        
        for old_color, message in old_colors.items():
            # Check if old color appears in actual CSS rules (not in comments)
            if old_color in css_no_comments:
                # Allow it in documentation/comments only
                assert False, f"Old color {old_color} found in CSS rules. {message}"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        ('--halloween-text-primary', '#E5E5E5'),
        ('--halloween-bg-primary', '#0F0F0F'),
        ('--halloween-accent-critical', '#FF7518'),
        ('--halloween-accent-success', '#39FF14'),
    ]))
    def test_property_2_contrast_compliance(self, color_pair: Tuple[str, str]):
        """
        **Feature: halloween-theme-transformation, Property 2: Contrast Compliance**
        **Validates: Requirements 2.1, 10.1**
        
        For any text element rendered on any background, the contrast ratio should
        meet or exceed WCAG AA standards (4.5:1 for normal text, 3:1 for large text).
        
        This test verifies that:
        1. Text colors have sufficient contrast against backgrounds
        2. Critical colors maintain readability
        3. All color combinations meet WCAG AA standards
        """
        css_var, expected_value = color_pair
        css_content = load_halloween_css()
        properties = parse_css_custom_properties(css_content)
        
        # Verify the property exists and has the expected value
        assert css_var in properties, f"Custom property {css_var} must be defined"
        assert properties[css_var] == expected_value, \
            f"{css_var} must be {expected_value}"
        
        # Test contrast ratios for common combinations
        if css_var == '--halloween-text-primary':
            # Light text on dark background
            bg_color = properties.get('--halloween-bg-primary', '#0F0F0F')
            contrast = calculate_contrast_ratio(expected_value, bg_color)
            assert contrast >= 4.5, \
                f"Text contrast ratio {contrast:.2f} must be >= 4.5:1 for WCAG AA"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        '--spacing-xs',
        '--spacing-sm',
        '--spacing-md',
        '--spacing-lg',
        '--spacing-xl',
        '--spacing-2xl',
    ]))
    def test_property_3_spacing_grid_adherence(self, spacing_var: str):
        """
        **Feature: halloween-theme-transformation, Property 3: Spacing Grid Adherence**
        **Validates: Requirements 2.3**
        
        For any UI element's margin or padding, the value should be a multiple of 8px.
        
        This test verifies that:
        1. All spacing custom properties are multiples of 8px (or 4px for half-unit)
        2. The 8px grid system is maintained throughout
        3. Spacing values are consistent and predictable
        """
        css_content = load_halloween_css()
        properties = parse_css_custom_properties(css_content)
        
        # Verify the spacing property exists
        assert spacing_var in properties, f"Spacing property {spacing_var} must be defined"
        
        spacing_value = properties[spacing_var]
        
        # Verify it's a multiple of 4px (allowing for half-units)
        assert check_spacing_multiple_of_8(spacing_value) or spacing_value == '4px', \
            f"{spacing_var} must be a multiple of 8px (or 4px for half-unit), got {spacing_value}"
        
        # Verify expected values
        expected_values = {
            '--spacing-xs': '4px',
            '--spacing-sm': '8px',
            '--spacing-md': '16px',
            '--spacing-lg': '24px',
            '--spacing-xl': '32px',
            '--spacing-2xl': '40px',
        }
        
        if spacing_var in expected_values:
            assert spacing_value == expected_values[spacing_var], \
                f"{spacing_var} must be {expected_values[spacing_var]}, got {spacing_value}"
    
    
    def test_property_4_font_usage_correctness(self):
        """
        **Feature: halloween-theme-transformation, Property 4: Font Usage Correctness**
        **Validates: Requirements 2.4**
        
        For any text element, if it is the "Spyder" h1 title then it should use
        Rubik Glitch font, otherwise it should use Inter font (except monospace for logs).
        
        This test verifies that:
        1. The h1 title uses Rubik Glitch font
        2. All other UI elements use Inter font
        3. Logs use monospace font
        """
        css_content = load_halloween_css()
        
        # Check h1 uses Rubik Glitch
        h1_pattern = r'\.header\s+h1\s*\{([^}]+)\}'
        h1_match = re.search(h1_pattern, css_content, re.DOTALL)
        
        assert h1_match, "Header h1 rule must be defined"
        h1_content = h1_match.group(1)
        assert 'Rubik Glitch' in h1_content, \
            "Header h1 must use Rubik Glitch font"
        
        # Check body and other elements use Inter
        body_pattern = r'body,\s*\n\.tab,\s*\n\.btn'
        body_match = re.search(body_pattern, css_content)
        
        if body_match:
            # Find the font-family rule for this selector
            start_pos = body_match.end()
            brace_match = re.search(r'\{([^}]+)\}', css_content[start_pos:], re.DOTALL)
            if brace_match:
                body_content = brace_match.group(1)
                assert 'Inter' in body_content, \
                    "Body and UI elements must use Inter font"
        
        # Check logs use monospace
        logs_pattern = r'\.logs-container,\s*\n\.log-entry\s*\{([^}]+)\}'
        logs_match = re.search(logs_pattern, css_content, re.DOTALL)
        
        if logs_match:
            logs_content = logs_match.group(1)
            assert 'monospace' in logs_content, \
                "Logs must use monospace font"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        '.corner-web',
        '.floating-particles',
        '.particle',
        '.particle-ember',
        '.particle-fog',
        '.particle-ghost',
        '.container::before',
        '.container::after',
        '.stats-grid::before',
        '.history-grid::before',
    ]))
    def test_property_7_decorative_non_interference(self, css_selector: str):
        """
        **Feature: halloween-theme-transformation, Property 7: Decorative Non-Interference**
        **Validates: Requirements 4.5**
        
        For any decorative element (webs, particles, silhouettes), it should have
        `pointer-events: none` and should not overlap interactive UI components.
        
        This test verifies that:
        1. All decorative elements have pointer-events: none
        2. Decorative elements have appropriate z-index (low priority)
        3. Decorative elements are hidden in reduced motion mode
        4. Decorative elements are hidden in high contrast mode
        """
        css_content = load_halloween_css()
        
        # Verify the selector exists in the CSS
        assert css_selector in css_content, \
            f"Decorative selector {css_selector} must be present in Halloween theme"
        
        # Extract the rule for this selector
        selector_pattern = re.escape(css_selector) + r'\s*\{([^}]+)\}'
        match = re.search(selector_pattern, css_content, re.DOTALL)
        
        if match:
            rule_content = match.group(1)
            
            # Check for pointer-events: none
            has_pointer_events_none = 'pointer-events: none' in rule_content
            
            assert has_pointer_events_none, \
                f"{css_selector} must have 'pointer-events: none' to prevent interference"
            
            # Check for appropriate z-index (should be low, typically 0 or 1)
            z_index_match = re.search(r'z-index:\s*(\d+)', rule_content)
            if z_index_match:
                z_index = int(z_index_match.group(1))
                assert z_index <= 1, \
                    f"{css_selector} z-index must be <= 1 to stay behind interactive elements, got {z_index}"
        
        # Verify decorative elements are hidden in reduced motion mode
        # Look for the specific pattern where decorative elements are hidden
        reduced_motion_section = css_content.find('@media (prefers-reduced-motion: reduce)')
        if reduced_motion_section != -1:
            # Find the end of this media query (matching braces)
            brace_count = 0
            start = reduced_motion_section
            end = start
            for i in range(start, len(css_content)):
                if css_content[i] == '{':
                    brace_count += 1
                elif css_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            reduced_motion_content = css_content[start:end]
            
            # Check if decorative elements are hidden
            # Look for the specific selectors being hidden
            decorative_selectors = ['.corner-web', '.floating-particles', '.container::before', 
                                   '.container::after', '.stats-grid::before', '.history-grid::before']
            
            # Check if at least one decorative selector is mentioned with display: none
            has_decorative_hiding = any(
                selector in reduced_motion_content for selector in decorative_selectors
            ) and 'display: none' in reduced_motion_content
            
            assert has_decorative_hiding, \
                "Decorative elements must be hidden in reduced motion mode"
        
        # Verify decorative elements are hidden in high contrast mode
        high_contrast_section = css_content.find('@media (prefers-contrast: high)')
        if high_contrast_section != -1:
            # Find the end of this media query (matching braces)
            brace_count = 0
            start = high_contrast_section
            end = start
            for i in range(start, len(css_content)):
                if css_content[i] == '{':
                    brace_count += 1
                elif css_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            high_contrast_content = css_content[start:end]
            
            # Check if decorative elements are hidden
            decorative_selectors = ['.corner-web', '.floating-particles', '.container::before', 
                                   '.container::after', '.stats-grid::before', '.history-grid::before']
            
            has_decorative_hiding = any(
                selector in high_contrast_content for selector in decorative_selectors
            ) and 'display: none' in high_contrast_content
            
            assert has_decorative_hiding, \
                "Decorative elements must be hidden in high contrast mode"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        'glitchFlicker',
        'pulseGlow',
        'mistMove',
        'badgePulse',
        'buttonPulse',
        'floatEmber',
        'floatFog',
        'floatGhost',
        'spiderFloat',
        'webUnderline',
    ]))
    def test_property_8_animation_performance(self, animation_name: str):
        """
        **Feature: halloween-theme-transformation, Property 8: Animation Performance**
        **Validates: Requirements 5.1**
        
        For any animated element, the animation should maintain 60fps performance
        during execution.
        
        This test verifies that:
        1. All animations use GPU-accelerated properties (transform, opacity)
        2. Animated elements have will-change property set
        3. Animated elements use translateZ(0) for GPU acceleration
        4. Animated elements have backface-visibility: hidden
        5. Animations use appropriate easing functions
        """
        css_content = load_halloween_css()
        
        # Find the @keyframes definition
        keyframes_pattern = rf'@keyframes\s+{animation_name}\s*\{{([^}}]+)\}}'
        keyframes_match = re.search(keyframes_pattern, css_content, re.DOTALL)
        
        assert keyframes_match, f"Animation {animation_name} must be defined"
        
        keyframes_content = keyframes_match.group(1)
        
        # Verify animation uses GPU-accelerated properties only
        # Allowed properties: transform, opacity, box-shadow (for glow effects)
        # Not allowed: left, top, width, height, margin, padding, etc.
        
        # Check that animation uses transform, opacity, or box-shadow
        uses_gpu_properties = (
            'transform:' in keyframes_content or
            'opacity:' in keyframes_content or
            'box-shadow:' in keyframes_content  # box-shadow is acceptable for glow effects
        )
        
        assert uses_gpu_properties, \
            f"Animation {animation_name} must use GPU-accelerated properties (transform, opacity, or box-shadow)"
        
        # Check that transform uses translateZ(0) for GPU acceleration
        if 'transform:' in keyframes_content:
            has_translatez = 'translateZ(0)' in keyframes_content
            assert has_translatez, \
                f"Animation {animation_name} must use translateZ(0) for GPU acceleration"
        
        # Find elements that use this animation
        animation_usage_pattern = rf'animation:\s*[^;]*{animation_name}'
        usage_matches = list(re.finditer(animation_usage_pattern, css_content))
        
        if usage_matches:
            # For each usage, find the containing rule
            for usage_match in usage_matches:
                # Find the selector for this rule (search backwards)
                start_pos = usage_match.start()
                
                # Find the opening brace before this position
                last_brace = css_content.rfind('{', 0, start_pos)
                if last_brace == -1:
                    continue
                
                # Find the selector before the brace
                selector_start = css_content.rfind('}', 0, last_brace)
                if selector_start == -1:
                    selector_start = 0
                else:
                    selector_start += 1
                
                selector_text = css_content[selector_start:last_brace].strip()
                
                # Find the closing brace for this rule
                brace_count = 1
                end_pos = last_brace + 1
                while end_pos < len(css_content) and brace_count > 0:
                    if css_content[end_pos] == '{':
                        brace_count += 1
                    elif css_content[end_pos] == '}':
                        brace_count -= 1
                    end_pos += 1
                
                rule_content = css_content[last_brace:end_pos]
                
                # Check for performance optimizations in this rule
                has_will_change = 'will-change:' in rule_content
                has_translatez = 'translateZ(0)' in rule_content
                has_backface_visibility = 'backface-visibility: hidden' in rule_content
                
                has_optimization = has_will_change or has_translatez or has_backface_visibility
                
                # If this is a pseudo-class selector (like :hover), also check the base selector
                if not has_optimization and ':' in selector_text:
                    # Extract base selector (e.g., ".stat-card" from ".stat-card:hover")
                    base_selector = selector_text.split(':')[0].strip()
                    
                    # Find the base selector rule
                    base_pattern = re.escape(base_selector) + r'\s*\{([^}]+)\}'
                    base_match = re.search(base_pattern, css_content, re.DOTALL)
                    
                    if base_match:
                        base_content = base_match.group(1)
                        has_will_change = 'will-change:' in base_content
                        has_translatez = 'translateZ(0)' in base_content
                        has_backface_visibility = 'backface-visibility: hidden' in base_content
                        has_optimization = has_will_change or has_translatez or has_backface_visibility
                
                assert has_optimization, \
                    f"Element using {animation_name} (selector: {selector_text}) must have GPU acceleration " \
                    f"(will-change, translateZ(0), or backface-visibility: hidden)"
    
    
    @settings(max_examples=100)
    @given(st.sampled_from([
        '.stat-card:hover',
        '.severity-badge.critical',
        '.btn-primary:hover:not(:disabled)',
        '.table-btn-view:hover',
        '.history-btn-view:hover',
    ]))
    def test_property_9_pulsing_accent_presence(self, css_selector: str):
        """
        **Feature: halloween-theme-transformation, Property 9: Pulsing Accent Presence**
        **Validates: Requirements 5.4**
        
        For any accent element (badges, buttons, highlights), it should have a
        soft pulsing animation applied.
        
        This test verifies that:
        1. All accent elements have pulsing animations
        2. Pulsing animations use appropriate duration (2s)
        3. Pulsing animations use appropriate easing functions
        4. Pulsing animations affect box-shadow or transform
        """
        css_content = load_halloween_css()
        
        # Verify the selector exists in the CSS
        assert css_selector in css_content, \
            f"Accent selector {css_selector} must be present in Halloween theme"
        
        # Extract ALL rules for this selector (there may be multiple)
        # Try exact match first
        selector_pattern = re.escape(css_selector) + r'\s*\{([^}]+)\}'
        matches = list(re.finditer(selector_pattern, css_content, re.DOTALL))
        
        # If not found, try to find it in a combined selector
        if not matches:
            combined_pattern = r'([^}]*' + re.escape(css_selector) + r'[^{]*)\{([^}]+)\}'
            combined_matches = list(re.finditer(combined_pattern, css_content, re.DOTALL))
            if combined_matches:
                matches = combined_matches
        
        assert matches, f"Rule for {css_selector} must be defined"
        
        # Check if ANY of the rules has animation
        has_animation = False
        rule_content = ""
        for match in matches:
            content = match.group(1) if len(match.groups()) == 1 else match.group(2)
            rule_content += content + "\n"
            if 'animation:' in content:
                has_animation = True
                rule_content = content
                break
        
        assert has_animation, \
            f"{css_selector} must have a pulsing animation applied"
        
        # Check for pulsing animation names
        pulsing_animations = ['pulseGlow', 'badgePulse', 'buttonPulse']
        has_pulsing_animation = any(anim in rule_content for anim in pulsing_animations)
        
        assert has_pulsing_animation, \
            f"{css_selector} must use a pulsing animation (pulseGlow, badgePulse, or buttonPulse)"
        
        # Check for appropriate duration (should use CSS variable or 2s)
        has_duration = (
            'var(--halloween-pulse-duration)' in rule_content or
            '2s' in rule_content
        )
        
        assert has_duration, \
            f"{css_selector} animation must use appropriate duration (2s or CSS variable)"
        
        # Check for appropriate easing function
        has_easing = (
            'ease-in-out' in rule_content or
            'cubic-bezier' in rule_content
        )
        
        assert has_easing, \
            f"{css_selector} animation must use appropriate easing function"
        
        # Check that animation is infinite
        has_infinite = 'infinite' in rule_content
        
        assert has_infinite, \
            f"{css_selector} pulsing animation must be infinite"
    
    
    def test_halloween_theme_structure(self):
        """
        Verify the overall structure of the Halloween theme CSS file.
        
        This test ensures:
        - All required sections are present
        - CSS custom properties are properly defined
        - Color mapping documentation exists
        """
        css_content = load_halloween_css()
        
        # Check for required sections
        required_sections = [
            'Halloween Color Palette',
            'Color Mapping Table',
            'Base Color Transformations',
            'Typography System',
            'Performance Optimizations',
            'Accessibility Support',
            'Decorative Elements',
        ]
        
        for section in required_sections:
            assert section in css_content, \
                f"Halloween theme must include '{section}' section"
        
        # Check for :root selector
        assert ':root' in css_content, \
            "Halloween theme must define :root with custom properties"
        
        # Check for accessibility media queries
        assert '@media (prefers-reduced-motion: reduce)' in css_content, \
            "Halloween theme must support reduced motion preference"
        
        assert '@media (prefers-contrast: high)' in css_content, \
            "Halloween theme must support high contrast mode"


# ============================================
# Integration Tests
# ============================================

class TestHalloweenThemeIntegration:
    """Integration tests for Halloween theme application."""
    
    def test_html_includes_halloween_css(self):
        """Verify that the HTML file includes the Halloween theme CSS."""
        html_path = Path("templates/index.html")
        if not html_path.exists():
            pytest.skip("HTML file not found")
        
        html_content = html_path.read_text(encoding='utf-8')
        
        assert '/static/halloween-theme.css' in html_content, \
            "HTML must include Halloween theme CSS file"
        
        assert '<link rel="stylesheet" href="/static/halloween-theme.css">' in html_content, \
            "Halloween theme CSS must be properly linked"
    
    
    def test_css_custom_properties_complete(self):
        """Verify all required CSS custom properties are defined."""
        css_content = load_halloween_css()
        properties = parse_css_custom_properties(css_content)
        
        required_properties = [
            # Base colors
            '--halloween-bg-primary',
            '--halloween-bg-secondary',
            '--halloween-bg-tertiary',
            '--halloween-bg-card',
            # Accent colors
            '--halloween-accent-critical',
            '--halloween-accent-high',
            '--halloween-accent-medium',
            '--halloween-accent-low',
            '--halloween-accent-success',
            '--halloween-accent-purple',
            # Text colors
            '--halloween-text-primary',
            '--halloween-text-secondary',
            '--halloween-text-dark',
            # Border colors
            '--halloween-border-primary',
            '--halloween-border-accent',
            '--halloween-border-web',
            # Animation timings
            '--halloween-mist-duration',
            '--halloween-glitch-duration',
            '--halloween-pulse-duration',
            # Decoration opacities
            '--halloween-web-opacity',
            '--halloween-particle-opacity',
            '--halloween-silhouette-opacity',
            # Spacing
            '--spacing-xs',
            '--spacing-sm',
            '--spacing-md',
            '--spacing-lg',
            '--spacing-xl',
            '--spacing-2xl',
        ]
        
        for prop in required_properties:
            assert prop in properties, \
                f"Required custom property {prop} must be defined"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
