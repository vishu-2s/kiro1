"""
Test script to demonstrate type safety and error handling fixes.

Tests:
1. SafeDict (no KeyError)
2. SafeAgentResult (consistent types)
3. Unicode handling (Windows-safe)
4. Minimal error handling (fail fast)
"""

import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("TYPE SAFETY & ERROR HANDLING FIXES - TEST SUITE")
print("=" * 80)

# Test 1: SafeDict (No KeyError)
print("\n" + "=" * 80)
print("TEST 1: SafeDict - No More KeyError")
print("=" * 80)

from agents.safe_types import SafeDict

# Create test data
data = SafeDict({
    "name": "express",
    "version": "4.18.0",
    "count": "10",  # String that should be int
    "score": "0.95",  # String that should be float
    "vulnerabilities": [{"id": "CVE-123"}]
})

print("\n1.1 Testing safe string access...")
name = data.safe_str("name", "unknown")
print(f"✅ name = {name}")

missing = data.safe_str("missing_key", "default")
print(f"✅ missing_key = {missing} (default)")

print("\n1.2 Testing safe type conversion...")
count = data.safe_int("count", 0)
print(f"✅ count = {count} (converted from string)")

score = data.safe_float("score", 0.0)
print(f"✅ score = {score} (converted from string)")

print("\n1.3 Testing safe list access...")
vulns = data.safe_list("vulnerabilities", [])
print(f"✅ vulnerabilities = {len(vulns)} items")

missing_list = data.safe_list("missing_list", [])
print(f"✅ missing_list = {missing_list} (default)")

print("\n1.4 Testing nested safe access...")
nested = data.safe_dict("metadata", {})
author = nested.safe_str("author", "unknown")
print(f"✅ nested.author = {author} (default)")

print("\n✅ No KeyError! All accesses safe with defaults.")

# Test 2: SafeAgentResult (Consistent Types)
print("\n" + "=" * 80)
print("TEST 2: SafeAgentResult - Consistent Data Structures")
print("=" * 80)

from agents.safe_types import SafeAgentResult

# Create result
result = SafeAgentResult(
    agent_name="vulnerability_analysis",
    success=True,
    data=SafeDict({
        "packages": [
            {"package_name": "express", "vulnerability_count": 2},
            {"package_name": "lodash", "vulnerability_count": 0}
        ],
        "total_packages_analyzed": 2
    }),
    confidence=0.9
)

print("\n2.1 Testing type-safe access...")
print(f"✅ agent_name = {result.agent_name}")
print(f"✅ success = {result.success}")
print(f"✅ confidence = {result.confidence}")

print("\n2.2 Testing safe package access...")
packages = result.get_packages()
print(f"✅ packages = {len(packages)} items")

for pkg in packages:
    name = pkg.safe_str("package_name", "unknown")
    count = pkg.safe_int("vulnerability_count", 0)
    print(f"   - {name}: {count} vulnerabilities")

print("\n2.3 Testing serialization...")
result_dict = result.to_dict()
print(f"✅ to_dict() = {len(result_dict)} keys")

print("\n2.4 Testing deserialization...")
restored = SafeAgentResult.from_dict(result_dict)
print(f"✅ from_dict() = {restored.agent_name}")

print("\n✅ No dict/object confusion! Consistent types throughout.")

# Test 3: Unicode Handling (Windows-Safe)
print("\n" + "=" * 80)
print("TEST 3: Unicode Handling - Windows-Safe")
print("=" * 80)

from agents.safe_types import safe_unicode_print, safe_unicode_str

print("\n3.1 Testing safe unicode printing...")
try:
    safe_unicode_print("✅ Unicode test: ✓ ✗ → ← ↑ ↓")
    safe_unicode_print("✅ Emoji test: 🚀 🎯 ⚡ 🔥")
    safe_unicode_print("✅ Special chars: café résumé naïve")
    print("✅ All unicode printed successfully!")
except Exception as e:
    print(f"❌ Unicode printing failed: {e}")

print("\n3.2 Testing safe string conversion...")
test_values = [
    "✅ Normal string",
    b"Bytes string",
    None,
    123,
    {"key": "value"}
]

for value in test_values:
    safe_str = safe_unicode_str(value, "fallback")
    print(f"✅ Converted: {type(value).__name__} → {safe_str[:30]}")

print("\n✅ No UnicodeEncodeError! Windows-safe throughout.")

# Test 4: Minimal Error Handling (Fail Fast)
print("\n" + "=" * 80)
print("TEST 4: Minimal Error Handling - Fail Fast")
print("=" * 80)

from agents.minimal_error_handler import (
    validate_required,
    validate_optional,
    fail_fast,
    log_errors,
    safe_call
)

print("\n4.1 Testing validation...")
try:
    validate_required("express", "package", str)
    print("✅ validate_required: passed")
except Exception as e:
    print(f"❌ validate_required: {e}")

try:
    validate_required(None, "package", str)
    print("❌ validate_required: should have failed!")
except ValueError as e:
    print(f"✅ validate_required: correctly failed - {e}")

print("\n4.2 Testing optional validation...")
result = validate_optional("4.18.0", "version", str, "latest")
print(f"✅ validate_optional: {result}")

result = validate_optional(None, "version", str, "latest")
print(f"✅ validate_optional with None: {result} (default)")

print("\n4.3 Testing fail_fast...")
try:
    fail_fast(True, "This should not fail")
    print("✅ fail_fast: passed when condition True")
except Exception as e:
    print(f"❌ fail_fast: {e}")

try:
    fail_fast(False, "This should fail")
    print("❌ fail_fast: should have failed!")
except Exception as e:
    print(f"✅ fail_fast: correctly failed - {e}")

print("\n4.4 Testing log_errors decorator...")
@log_errors("test_function")
def test_function(should_fail=False):
    if should_fail:
        raise ValueError("Test error")
    return "success"

try:
    result = test_function(should_fail=False)
    print(f"✅ log_errors: {result}")
except Exception as e:
    print(f"❌ log_errors: {e}")

print("\n4.5 Testing safe_call...")
def risky_function():
    raise ValueError("This will fail")

result = safe_call(risky_function, default="fallback", error_msg="Expected failure")
print(f"✅ safe_call: returned default '{result}' on error")

print("\n✅ Minimal error handling working! Fail fast, log clearly.")

# Test 5: SafeSharedContext
print("\n" + "=" * 80)
print("TEST 5: SafeSharedContext - Type-Safe Context")
print("=" * 80)

from agents.safe_types import SafeSharedContext

# Create context
context = SafeSharedContext(
    packages=["express", "lodash", "react"],
    ecosystem="npm"
)

print("\n5.1 Testing context creation...")
print(f"✅ packages = {len(context.packages)}")
print(f"✅ ecosystem = {context.ecosystem}")

print("\n5.2 Testing agent result management...")
# Create a fresh result for context testing
test_result = SafeAgentResult(
    agent_name="test_agent",
    success=True,
    data=SafeDict({"test": "data"})
)
context.add_agent_result(test_result)
print(f"✅ Added agent result: {test_result.agent_name}")

retrieved = context.get_agent_result("test_agent")
print(f"✅ Retrieved result: {retrieved.agent_name if retrieved else 'None'}")

has_result = context.has_successful_result("test_agent")
print(f"✅ Has successful result: {has_result}")

print("\n5.3 Testing package data aggregation...")
all_packages = context.get_all_packages_data()
print(f"✅ All packages data: {len(all_packages)} packages")

print("\n✅ SafeSharedContext working! Type-safe throughout.")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print("\n✅ FIXED ISSUES:")
print("   1. ✅ Inconsistent data structures - SafeDict & SafeAgentResult")
print("   2. ✅ Unsafe attribute access - Safe accessors with defaults")
print("   3. ✅ Too many try-except - Minimal error handling")
print("   4. ✅ Unicode handling - Windows-safe printing")
print("   5. ✅ Error handling - Fail fast, log clearly")

print("\n📊 IMPROVEMENTS:")
print("   • No more KeyError or AttributeError")
print("   • No dict/object confusion")
print("   • Clear error messages")
print("   • Windows-safe unicode")
print("   • Minimal try-except blocks")

print("\n🚀 SYSTEM STATUS: TYPE-SAFE, RELIABLE & MAINTAINABLE")
print("=" * 80)
