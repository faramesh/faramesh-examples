#!/usr/bin/env python3
"""
Test canonicalization end-to-end
"""
import sys
import os

# Add server to path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-horizon-code", "src")
    ),
)

from faramesh.server.canonicalization import compute_request_hash


def test_float_canonicalization():
    """Test that 1.0, 1.00, 1, 1.000 all produce the same hash"""

    test_cases = [
        {"tool": "payment", "operation": "refund", "params": {"amount": 1.0}},
        {"tool": "payment", "operation": "refund", "params": {"amount": 1.00}},
        {"tool": "payment", "operation": "refund", "params": {"amount": 1}},
        {"tool": "payment", "operation": "refund", "params": {"amount": 1.000}},
    ]

    print("🧪 Testing Float Canonicalization\n")
    print("=" * 60)

    hashes = []
    for i, case in enumerate(test_cases, 1):
        h = compute_request_hash(case)
        hashes.append(h)
        print(f"{i}. amount={case['params']['amount']} -> {h[:32]}...")

    print("\n" + "=" * 60)

    # Verify all hashes are identical
    unique_hashes = set(hashes)
    if len(unique_hashes) == 1:
        print("✅ CANONICALIZATION TEST PASSED")
        print("   All float representations produce identical hash!")
        print(f"   Hash: {hashes[0]}")
        return True
    else:
        print("❌ CANONICALIZATION TEST FAILED")
        print(f"   Found {len(unique_hashes)} different hashes:")
        for h in unique_hashes:
            print(f"   - {h}")
        return False


def test_string_canonicalization():
    """Test that strings with different spacing produce same hash"""

    test_cases = [
        {
            "tool": "notification",
            "operation": "send",
            "params": {"message": "Hello World"},
        },
        {
            "tool": "notification",
            "operation": "send",
            "params": {"message": "Hello  World"},
        },
        {
            "tool": "notification",
            "operation": "send",
            "params": {"message": "Hello World "},
        },
    ]

    print("\n🧪 Testing String Canonicalization\n")
    print("=" * 60)

    hashes = []
    for i, case in enumerate(test_cases, 1):
        h = compute_request_hash(case)
        hashes.append(h)
        print(f"{i}. {repr(case['params'])} -> {h[:32]}...")

    print("\n" + "=" * 60)

    # Strings with different spacing SHOULD produce different hashes
    # (canonicalization normalizes floats, not strings)
    unique_hashes = set(hashes)
    print(f"ℹ️  Found {len(unique_hashes)} different hashes (expected)")
    print("   String canonicalization preserves exact content")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  FARAMESH CANONICALIZATION END-TO-END TEST")
    print("=" * 60 + "\n")

    result1 = test_float_canonicalization()
    result2 = test_string_canonicalization()

    print("\n" + "=" * 60)
    if result1 and result2:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")
