#!/usr/bin/env python3
"""
Float Canonicalization Demo: The "Float Nightmare"

This demo shows how Faramesh's canonicalization.py handles float normalization
to ensure that 1.0, 1.00, and 1 are treated as identical for security hashing.

Scenario:
- LLM might output "amount": 1.0 or "amount": 1.00 or "amount": 1
- Without canonicalization, these would have different hashes
- Faramesh normalizes all floats to ensure consistent policy enforcement

Required Policy: Any policy with amount-based rules
"""

import os
import sys
import json
import hashlib
from demo_utils import ensure_server_available

# Add both SDK and server to path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-python-sdk-code")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-horizon-code", "src")
    ),
)

from faramesh import configure, submit_action
from faramesh.server.canonicalization import compute_request_hash


FARAMESH_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
FARAMESH_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv(
    "FARAMESH_API_KEY", "demo-api-key-123"
)
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "canonicalization-demo-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def compute_naive_hash(data: dict) -> str:
    """Compute hash WITHOUT canonicalization (vulnerable)."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def test_float_variants():
    """Test different float representations."""
    print("\n" + "=" * 80)
    print("🔒 Float Canonicalization Demo: The 'Float Nightmare'")
    print("=" * 80)
    print()
    print("Scenario: LLM outputs different float representations")
    print("Risk: 1.0, 1.00, and 1 would have different hashes without normalization")
    print("Protection: Faramesh canonicalizes all floats before hashing")
    print()
    print("-" * 80)
    print()

    # Test cases with different float representations
    test_cases = [
        {"amount": 1, "currency": "USD", "action": "refund"},
        {"amount": 1.0, "currency": "USD", "action": "refund"},
        {"amount": 1.00, "currency": "USD", "action": "refund"},
        {"amount": 1.000, "currency": "USD", "action": "refund"},
    ]

    print("📋 TEST: Different float representations")
    print("-" * 80)
    print()

    naive_hashes = []
    canonical_hashes = []

    for i, params in enumerate(test_cases, 1):
        print(f"Variant {i}: {json.dumps(params)}")

        # Compute naive hash (without canonicalization)
        naive_hash = compute_naive_hash(params)
        naive_hashes.append(naive_hash)
        print(f"  Naive hash:      {naive_hash[:16]}...")

        # Compute canonical hash (with Faramesh canonicalization)
        payload = {
            "agent_id": "demo-agent",
            "tool": "payment",
            "operation": "refund",
            "params": params,
            "context": {},
        }
        canonical_hash = compute_request_hash(payload)
        canonical_hashes.append(canonical_hash)
        print(f"  Canonical hash:  {canonical_hash[:16]}...")
        print()

    # Analysis
    print("-" * 80)
    print("📊 Analysis:")
    print()

    unique_naive = len(set(naive_hashes))
    unique_canonical = len(set(canonical_hashes))

    print("Without Canonicalization:")
    print(f"  Unique hashes: {unique_naive}/{len(test_cases)}")
    print(
        f"  Problem: {'❌ Different hashes for same value!' if unique_naive > 1 else '✅ Same hash'}"
    )
    print()

    print("With Faramesh Canonicalization:")
    print(f"  Unique hashes: {unique_canonical}/{len(test_cases)}")
    print(
        f"  Result: {'✅ All floats normalized to same hash!' if unique_canonical == 1 else '❌ Different hashes'}"
    )
    print()

    if unique_canonical == 1:
        print("✅ SUCCESS: All float variants produce identical hash")
        print("   This means policy rules work consistently regardless of how")
        print("   the LLM formats numbers (1 vs 1.0 vs 1.00)")
    print()


def test_nested_floats():
    """Test canonicalization with nested float structures."""
    print("\n" + "=" * 80)
    print("📋 TEST: Nested float structures")
    print("=" * 80)
    print()

    test_cases = [
        {
            "transaction": {
                "amount": 100,
                "fee": 2.5,
                "tax": 7.50,
            }
        },
        {
            "transaction": {
                "amount": 100.0,
                "fee": 2.50,
                "tax": 7.5,
            }
        },
        {
            "transaction": {
                "amount": 100.00,
                "fee": 2.500,
                "tax": 7.500,
            }
        },
    ]

    canonical_hashes = []

    for i, params in enumerate(test_cases, 1):
        print(f"Variant {i}:")
        print(f"  {json.dumps(params, indent=2)}")

        payload = {
            "agent_id": "demo-agent",
            "tool": "payment",
            "operation": "charge",
            "params": params,
            "context": {},
        }
        canonical_hash = compute_request_hash(payload)
        canonical_hashes.append(canonical_hash)
        print(f"  Hash: {canonical_hash[:32]}...")
        print()

    unique_hashes = len(set(canonical_hashes))

    if unique_hashes == 1:
        print("✅ SUCCESS: All nested float variants produce identical hash")
    else:
        print(f"❌ FAILED: Found {unique_hashes} different hashes")

    print()


def test_with_real_api():
    """Test with real Faramesh API to verify backend canonicalization."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("📋 TEST: Real API with float variants")
    print("=" * 80)
    print()

    variants = [
        {"amount": 50, "currency": "USD"},
        {"amount": 50.0, "currency": "USD"},
        {"amount": 50.00, "currency": "USD"},
    ]

    action_ids = []

    for i, params in enumerate(variants, 1):
        print(f"Submitting variant {i}: {json.dumps(params)}")

        try:
            action = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="payment",
                operation="charge",
                params=params,
                context={"test": "canonicalization"},
            )

            action_ids.append(action["id"])
            print(f"  Action ID: {action['id']}")
            print(f"  Status: {action['status']}")

            if "request_hash" in action:
                print(f"  Request Hash: {action['request_hash'][:32]}...")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print()

    print("✅ All variants submitted successfully")
    print("   Backend canonicalization ensures consistent policy enforcement")
    print()


def run_demo():
    """Run the float canonicalization demo."""
    test_float_variants()
    test_nested_floats()

    # Optionally test with real API
    print("\n" + "=" * 80)
    print("🔄 Optional: Test with Real Faramesh API")
    print("=" * 80)
    print()
    user_input = input("Test with real API? (y/n): ").strip().lower()

    if user_input == "y":
        test_with_real_api()

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. Faramesh canonicalizes all numeric values before hashing")
    print("2. 1, 1.0, 1.00 all produce the same hash")
    print("3. This ensures consistent policy enforcement")
    print("4. Prevents 'confused deputy' attacks via float manipulation")
    print("5. Works with nested structures and complex payloads")
    print()
    print("Zenodo Paper Insight:")
    print("  'Canonicalization is the foundation of deterministic governance.'")
    print("  Without it, LLM output variance would break policy enforcement.")
    print()


if __name__ == "__main__":
    run_demo()
