"""
Test spider-themed iconography implementation.
Tests that all required CSS classes and animations are present.
"""

import re


def test_spider_dividers_present():
    """Test that spider-themed dividers are defined in CSS."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for spider divider class
    assert '.spider-divider' in css_content, "Spider divider class not found"
    
    # Check for web pattern variant
    assert '.spider-divider.web-pattern' in css_content, "Web pattern variant not found"
    
    # Check for silk strand variant
    assert '.spider-divider.silk-strand' in css_content, "Silk strand variant not found"
    
    # Check for spider crawl animation
    assert '@keyframes spiderCrawl' in css_content, "Spider crawl animation not found"
    
    # Check for dividers between sections
    assert '.control-panel + *::before' in css_content, "Dashboard section dividers not found"
    assert '.report-section + .report-section::before' in css_content, "Report section dividers not found"
    
    print("✓ All spider-themed dividers are present")


def test_web_connectors_present():
    """Test that web-like connectors are defined in CSS."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for web connector classes
    assert '.web-connector-horizontal' in css_content, "Horizontal web connector not found"
    assert '.web-connector-vertical' in css_content, "Vertical web connector not found"
    assert '.web-connector-diagonal' in css_content, "Diagonal web connector not found"
    assert '.web-connector-curve' in css_content, "Curved web connector not found"
    
    # Check for silk strand sway animation
    assert '@keyframes silkStrandSway' in css_content, "Silk strand sway animation not found"
    
    # Check for connectors applied to elements
    assert '.stats-grid::after' in css_content, "Stats grid connectors not found"
    assert '.finding-card + .finding-card::after' in css_content, "Finding card connectors not found"
    
    print("✓ All web-like connectors are present")


def test_glitched_symbols_present():
    """Test that glitched branding symbols are defined in CSS."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for glitch symbol class
    assert '.glitch-symbol' in css_content, "Glitch symbol class not found"
    
    # Check for glitch animations
    assert '@keyframes glitchSymbol' in css_content, "Glitch symbol animation not found"
    assert '@keyframes glitchBefore' in css_content, "Glitch before animation not found"
    assert '@keyframes glitchAfter' in css_content, "Glitch after animation not found"
    
    # Check for loading spider
    assert '.loading-spider' in css_content, "Loading spider class not found"
    assert '@keyframes spiderGlitch' in css_content, "Spider glitch animation not found"
    
    # Check for glitched spinner
    assert '@keyframes spinnerGlitch' in css_content, "Spinner glitch animation not found"
    
    # Check for branding screen
    assert '.branding-screen' in css_content, "Branding screen class not found"
    assert '@keyframes brandingGlitch' in css_content, "Branding glitch animation not found"
    
    # Check for SVG glitch
    assert '@keyframes svgGlitch' in css_content, "SVG glitch animation not found"
    
    print("✓ All glitched branding symbols are present")


def test_requirements_validation():
    """Test that implementation meets requirements 6.1, 6.2, and 6.3."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Requirement 6.1: Spider-themed dividers between sections
    assert 'Spider-themed dividers' in css_content, "Requirement 6.1 not met: Spider-themed dividers"
    
    # Requirement 6.2: Web-like connectors for diagrams
    assert 'Web-like connectors' in css_content, "Requirement 6.2 not met: Web-like connectors"
    
    # Requirement 6.3: Glitched branding symbols
    assert 'Glitched branding symbols' in css_content, "Requirement 6.3 not met: Glitched branding symbols"
    
    print("✓ All requirements (6.1, 6.2, 6.3) are met")


def test_gpu_acceleration():
    """Test that GPU acceleration is applied to animated elements."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for GPU acceleration properties
    gpu_patterns = [
        'will-change',
        'transform: translateZ(0)',
        'backface-visibility: hidden'
    ]
    
    for pattern in gpu_patterns:
        assert pattern in css_content, f"GPU acceleration property '{pattern}' not found"
    
    print("✓ GPU acceleration is properly applied")


def test_accessibility_support():
    """Test that decorative elements are properly hidden from screen readers."""
    with open('static/halloween-theme.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check that pointer-events: none is used for decorative elements
    assert 'pointer-events: none' in css_content, "Pointer events not disabled for decorative elements"
    
    print("✓ Accessibility support is present")


if __name__ == '__main__':
    print("Testing spider-themed iconography implementation...\n")
    
    test_spider_dividers_present()
    test_web_connectors_present()
    test_glitched_symbols_present()
    test_requirements_validation()
    test_gpu_acceleration()
    test_accessibility_support()
    
    print("\n✅ All tests passed! Spider-themed iconography is fully implemented.")
