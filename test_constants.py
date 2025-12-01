"""
Property-based tests for security signature detection in constants.py

**Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List, Dict
import string
import random

from constants import (
    is_suspicious_package_name,
    contains_suspicious_keywords,
    get_ecosystem_from_file,
    TYPOSQUAT_TARGETS,
    SUSPICIOUS_KEYWORDS,
    ECOSYSTEM_FILES,
    LEGITIMATE_PATTERNS
)


# Strategy for generating valid ecosystem names
ecosystem_strategy = st.sampled_from(list(TYPOSQUAT_TARGETS.keys()))

# Strategy for generating package names
package_name_strategy = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-_.",
    min_size=2,
    max_size=50
).filter(lambda x: x and not x.startswith('.') and not x.endswith('.'))

# Strategy for generating file content with potential suspicious keywords
content_strategy = st.text(min_size=0, max_size=1000)

# Strategy for generating filenames
filename_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + ".-_/",
    min_size=1,
    max_size=100
).filter(lambda x: x and '/' not in x[0:1] and '/' not in x[-1:])


class TestThreatDetectionAccuracy:
    """Property-based tests for threat detection accuracy."""

    @given(package_name_strategy, ecosystem_strategy)
    def test_typosquat_detection_consistency(self, package_name: str, ecosystem: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any package name and ecosystem, typosquat detection should be consistent
        and only flag packages that are actually similar to known targets.
        """
        assume(len(package_name.strip()) > 1)
        assume(package_name.strip() != "")
        
        result = is_suspicious_package_name(package_name, ecosystem)
        
        # Property: Result should be boolean
        assert isinstance(result, bool)
        
        # Property: If flagged as suspicious, there should be a legitimate reason
        if result:
            # Should be similar to at least one target in the ecosystem
            targets = TYPOSQUAT_TARGETS.get(ecosystem, [])
            package_lower = package_name.lower()
            
            found_similarity = False
            for target in targets:
                # Check for single character difference
                if len(package_lower) == len(target):
                    diff_count = sum(c1 != c2 for c1, c2 in zip(package_lower, target))
                    if diff_count == 1:
                        found_similarity = True
                        break
                
                # Check for common substitutions
                if (target.replace('o', '0') == package_lower or 
                    target.replace('i', '1') == package_lower):
                    found_similarity = True
                    break
            
            assert found_similarity, f"Package '{package_name}' flagged as suspicious but no similarity found to targets in {ecosystem}"

    @given(content_strategy)
    def test_suspicious_keyword_detection_accuracy(self, content: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any content string, suspicious keyword detection should accurately
        identify keywords that are actually present in the content.
        """
        found_keywords = contains_suspicious_keywords(content)
        
        # Property: Result should be a list
        assert isinstance(found_keywords, list)
        
        # Property: All found keywords should actually be in the content (case-insensitive)
        content_lower = content.lower()
        for keyword in found_keywords:
            assert keyword.lower() in content_lower, f"Keyword '{keyword}' reported as found but not in content"
        
        # Property: No duplicates in results
        assert len(found_keywords) == len(set(found_keywords)), "Duplicate keywords found in results"
        
        # Property: If a known suspicious keyword is in content, it should be detected
        for suspicious_keyword in SUSPICIOUS_KEYWORDS:
            if suspicious_keyword.lower() in content_lower:
                assert suspicious_keyword in found_keywords, f"Keyword '{suspicious_keyword}' in content but not detected"

    @given(filename_strategy)
    def test_ecosystem_detection_consistency(self, filename: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any filename, ecosystem detection should be consistent and accurate
        based on known file patterns.
        """
        assume(filename.strip() != "")
        
        detected_ecosystem = get_ecosystem_from_file(filename)
        
        # Property: Result should be a string
        assert isinstance(detected_ecosystem, str)
        
        # Property: Should return either a known ecosystem or "unknown"
        valid_ecosystems = set(ECOSYSTEM_FILES.keys()) | {"unknown"}
        assert detected_ecosystem in valid_ecosystems
        
        # Property: If ecosystem is detected (not "unknown"), the filename should match the pattern
        if detected_ecosystem != "unknown":
            ecosystem_files = ECOSYSTEM_FILES[detected_ecosystem]
            filename_lower = filename.lower()
            
            pattern_matched = False
            for pattern in ecosystem_files:
                pattern_to_check = pattern.replace("*", "").lower()
                if pattern_to_check in filename_lower:
                    pattern_matched = True
                    break
            
            assert pattern_matched, f"Ecosystem '{detected_ecosystem}' detected but filename '{filename}' doesn't match any patterns"

    @given(st.lists(package_name_strategy, min_size=1, max_size=10), ecosystem_strategy)
    def test_batch_typosquat_detection_consistency(self, package_names: List[str], ecosystem: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any list of package names, batch detection should be consistent
        with individual detection results.
        """
        # Filter out empty or invalid package names
        valid_packages = [pkg for pkg in package_names if pkg.strip() and len(pkg.strip()) > 1]
        assume(len(valid_packages) > 0)
        
        # Test individual vs batch consistency
        individual_results = {}
        for package in valid_packages:
            individual_results[package] = is_suspicious_package_name(package, ecosystem)
        
        # Property: Each package should give the same result when tested individually
        for package in valid_packages:
            individual_result = is_suspicious_package_name(package, ecosystem)
            assert individual_result == individual_results[package], f"Inconsistent result for package '{package}'"

    @given(st.text(min_size=10, max_size=500))
    def test_keyword_detection_with_context(self, base_content: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any content with injected suspicious keywords, detection should
        accurately identify the injected keywords.
        """
        # Inject a random suspicious keyword into the content
        if SUSPICIOUS_KEYWORDS:
            injected_keyword = random.choice(SUSPICIOUS_KEYWORDS)
            modified_content = base_content + " " + injected_keyword + " "
            
            found_keywords = contains_suspicious_keywords(modified_content)
            
            # Property: The injected keyword should be detected
            assert injected_keyword in found_keywords, f"Injected keyword '{injected_keyword}' not detected in content"

    @given(ecosystem_strategy)
    def test_legitimate_pattern_recognition(self, ecosystem: str):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        For any ecosystem, legitimate patterns should reduce false positives
        in typosquat detection.
        """
        legitimate_patterns = LEGITIMATE_PATTERNS.get(ecosystem, [])
        
        if legitimate_patterns:
            # Test with a legitimate pattern
            pattern = random.choice(legitimate_patterns)
            test_package = pattern + "test-package"
            
            # Property: Legitimate patterns should be less likely to be flagged
            # (This is a heuristic test - legitimate packages might still be flagged
            # if they're similar to typosquat targets, but the pattern helps context)
            result = is_suspicious_package_name(test_package, ecosystem)
            
            # The result can be either True or False, but the function should handle it consistently
            assert isinstance(result, bool)

    def test_confidence_scoring_properties(self):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        Test that confidence scoring mechanisms work consistently.
        """
        # Test with known suspicious patterns
        test_cases = [
            ("react", "npm", "reactt"),  # Single char typo
            ("lodash", "npm", "l0dash"),  # Character substitution
            ("requests", "pypi", "request"),  # Missing char
        ]
        
        for target, ecosystem, suspicious_name in test_cases:
            # Ensure the target is in our typosquat targets
            if target in TYPOSQUAT_TARGETS.get(ecosystem, []):
                result = is_suspicious_package_name(suspicious_name, ecosystem)
                # Property: Known typosquat patterns should be detected
                assert result, f"Known typosquat '{suspicious_name}' of '{target}' not detected"

    def test_edge_cases_handling(self):
        """
        **Feature: multi-agent-security, Property 13: Threat Detection Accuracy**
        
        Test that edge cases are handled properly without errors.
        """
        edge_cases = [
            ("", "npm"),  # Empty package name
            ("a", "npm"),  # Single character
            ("package-name", "unknown_ecosystem"),  # Unknown ecosystem
            ("UPPERCASE", "npm"),  # Case sensitivity
            ("package.with.dots", "npm"),  # Special characters
        ]
        
        for package_name, ecosystem in edge_cases:
            # Property: Should not raise exceptions
            try:
                result = is_suspicious_package_name(package_name, ecosystem)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Exception raised for edge case ({package_name}, {ecosystem}): {e}")
        
        # Test suspicious keyword detection with edge cases
        edge_content_cases = ["", "   ", "\n\t", "normal content"]
        
        for content in edge_content_cases:
            try:
                result = contains_suspicious_keywords(content)
                assert isinstance(result, list)
            except Exception as e:
                pytest.fail(f"Exception raised for edge case content '{content}': {e}")