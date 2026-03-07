#!/usr/bin/env python3
"""
Zero-Trust Demo: Cryptographic Hashes for Tool Calls

This demo shows how Faramesh uses cryptographic hashes to create
an immutable audit trail and verify tool call integrity.

Scenario:
- Every tool call is hashed with SHA-256
- Hashes link: request + policy + profile + runtime version
- Creates provenance_id for complete audit trail
- Impossible to tamper with execution history

Required: Any Faramesh configuration
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from demo_utils import ensure_server_available

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-python-sdk-code")
    ),
)

from faramesh import configure, submit_action


FARAMESH_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
FARAMESH_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv(
    "FARAMESH_API_KEY", "demo-api-key-123"
)
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "zero-trust-demo-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def demonstrate_cryptographic_trail():
    """Demonstrate cryptographic audit trail."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 Zero-Trust Demo: Cryptographic Hashes for Tool Calls")
    print("=" * 80)
    print()
    print("Scenario: Every tool call creates an immutable cryptographic audit trail")
    print("Protection: SHA-256 hashes link request + policy + profile + runtime")
    print()
    print("-" * 80)
    print()

    # Submit a few actions to demonstrate hash trail
    test_actions = [
        {
            "tool": "shell",
            "operation": "execute",
            "params": {"cmd": "echo 'Hello Faramesh'"},
            "context": {"user": "demo", "purpose": "test"},
        },
        {
            "tool": "payment",
            "operation": "charge",
            "params": {"amount": 100, "currency": "USD"},
            "context": {"user": "demo", "transaction_id": "TXN-001"},
        },
        {
            "tool": "database",
            "operation": "query",
            "params": {"query": "SELECT * FROM users WHERE active=true"},
            "context": {"user": "demo", "purpose": "analytics"},
        },
    ]

    results = []

    for i, action_spec in enumerate(test_actions, 1):
        print(f"📋 Action {i}: {action_spec['tool']}.{action_spec['operation']}")
        print("-" * 80)

        try:
            action = submit_action(agent_id=FARAMESH_AGENT_ID, **action_spec)

            print(f"  Action ID: {action['id']}")
            print(f"  Status: {action['status']}")

            # Extract hash information if available
            if "request_hash" in action:
                print(f"  Request Hash: {action['request_hash']}")

            if "provenance_id" in action:
                print(f"  Provenance ID: {action['provenance_id']}")

            # Show what's being hashed
            print("\n  Hashed Components:")
            print(f"    - Agent ID: {FARAMESH_AGENT_ID}")
            print(f"    - Tool: {action_spec['tool']}")
            print(f"    - Operation: {action_spec['operation']}")
            print(f"    - Params: {json.dumps(action_spec['params'], sort_keys=True)}")
            print(
                f"    - Context: {json.dumps(action_spec['context'], sort_keys=True)}"
            )
            print(f"    - Policy version: {action.get('policy_version', 'N/A')}")
            print(f"    - Profile version: {action.get('profile_version', 'N/A')}")

            results.append(action)

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print()

    # Demonstrate hash verification
    print("=" * 80)
    print("🔍 Hash Verification Demo")
    print("=" * 80)
    print()

    if results:
        print("Verifying hash integrity...")
        print()

        for i, action in enumerate(results, 1):
            print(f"Action {i} (ID: {action['id']}):")

            # Compute expected hash locally
            payload = {
                "agent_id": FARAMESH_AGENT_ID,
                "tool": test_actions[i - 1]["tool"],
                "operation": test_actions[i - 1]["operation"],
                "params": test_actions[i - 1]["params"],
                "context": test_actions[i - 1]["context"],
            }

            # Simple hash for demo (real implementation uses canonicalization)
            payload_str = json.dumps(payload, sort_keys=True)
            expected_hash = hashlib.sha256(payload_str.encode()).hexdigest()

            print(f"  Expected hash: {expected_hash}")

            if "request_hash" in action:
                actual_hash = action["request_hash"]
                print(f"  Actual hash:   {actual_hash}")

                # Note: Hashes may differ due to canonicalization
                print(
                    f"  Match: {expected_hash == actual_hash} (may differ due to canonicalization)"
                )
            else:
                print("  (Server hash not available in response)")

            print()

    print("=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. Every action gets a unique cryptographic hash (SHA-256)")
    print("2. Hash combines: request + policy + profile + runtime")
    print("3. Provenance ID enables complete audit trail reconstruction")
    print("4. Impossible to tamper with - hashes are deterministic")
    print("5. Can verify any action's integrity at any time")
    print()
    print("Zero-Trust Principle:")
    print("  'Trust nothing. Verify everything. Hash all interactions.'")
    print()
    print("CISO Value:")
    print("  - Complete cryptographic audit trail")
    print("  - Tamper-proof execution history")
    print("  - Forensic investigation capability")
    print("  - Compliance-ready evidence chain")
    print()


def demonstrate_provenance_chain():
    """Show how provenance IDs create a complete history chain."""
    print("\n" + "=" * 80)
    print("📜 Provenance Chain Demo")
    print("=" * 80)
    print()

    print("Provenance ID Formula:")
    print(
        "  provenance_id = SHA256(request_hash | policy_hash | profile_hash | runtime_version)"
    )
    print()
    print("This creates a unique fingerprint linking:")
    print("  1. The exact request (what was asked)")
    print("  2. The exact policy (what rules applied)")
    print("  3. The exact profile (what permissions existed)")
    print("  4. The exact runtime (what version executed it)")
    print()
    print("Use Case: Forensic Investigation")
    print("  Q: 'Who approved this $10,000 refund on Jan 15th?'")
    print("  A: Use provenance_id to trace:")
    print("     - Exact agent that submitted it")
    print("     - Exact policy version that evaluated it")
    print("     - Exact approver that authorized it")
    print("     - Exact runtime that executed it")
    print()
    print("Everything is version-bound and cryptographically verified.")
    print()


def run_demo():
    """Run the zero-trust cryptographic demo."""
    demonstrate_cryptographic_trail()
    demonstrate_provenance_chain()


if __name__ == "__main__":
    run_demo()
