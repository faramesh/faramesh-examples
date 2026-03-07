#!/usr/bin/env python3
"""
AutoGen + Faramesh Demo: Human-in-the-loop for $1,000+ transactions

This demo shows how Faramesh enforces human approval for high-value transactions
in AutoGen multi-agent conversations.

Scenario:
- AutoGen agents negotiate a refund amount
- If amount exceeds $1,000, Faramesh requires human approval
- Lower amounts are auto-approved

Required Policy: autogen_financial_policy.yaml
"""

import os
import sys
import time
from demo_utils import ensure_server_available

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-python-sdk-code")
    ),
)

from faramesh import configure, submit_action, wait_for_action


FARAMESH_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
FARAMESH_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv(
    "FARAMESH_API_KEY", "demo-api-key-123"
)
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "autogen-refund-agent-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def process_refund(customer_id: str, amount: float, reason: str) -> dict:
    """Process refund through Faramesh gate with amount-based approval.

    Args:
        customer_id: Customer identifier
        amount: Refund amount in USD
        reason: Reason for refund

    Returns:
        dict with success status and details
    """
    print(f"\n💰 Processing refund for customer {customer_id}")
    print(f"   Amount: ${amount:,.2f}")
    print(f"   Reason: {reason}")
    print()

    try:
        # Submit refund action to Faramesh
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="payment",
            operation="refund",
            params={
                "customer_id": customer_id,
                "amount": amount,
                "currency": "USD",
                "reason": reason,
            },
            context={
                "agent_framework": "autogen",
                "agent_role": "refund_processor",
                "transaction_type": "refund",
                "risk_level": (
                    "high" if amount >= 1000 else "medium" if amount >= 500 else "low"
                ),
            },
        )

        print(f"✓ Action submitted: {action['id']}")
        print(f"  Status: {action['status']}")
        print(f"  Decision: {action.get('decision', 'N/A')}")

        if action["status"] == "denied":
            print(f"  ❌ DENIED: {action.get('reason')}")
            return {
                "success": False,
                "denied": True,
                "reason": action.get("reason", "Policy violation"),
                "action_id": action["id"],
            }

            if action["status"] == "pending_approval":
                print("  ⏳ REQUIRES HUMAN APPROVAL")
                print(f"     Reason: {action.get('reason')}")
                print(f"     Action ID: {action['id']}")
                print()
                print("     👉 To approve, run:")
                print(
                    f"        curl -X POST http://localhost:8000/actions/{action['id']}/approve \\"
                )
                print("             -H 'X-API-Key: demo-api-key-123' \\")
                print("             -H 'Content-Type: application/json' \\")
                print(
                    '             -d \'{"approver_id": "human-approver-001", "notes": "Approved for demo"}\''
                )
                print()
                return {
                    "success": False,
                    "requires_approval": True,
                    "action_id": action["id"],
                    "reason": action.get("reason"),
                    "amount": amount,
                }

        # Wait for execution
        result = wait_for_action(action["id"], timeout=30)

        if result["status"] == "succeeded":
            print("  ✅ Refund processed successfully")
            if result["status"] == "succeeded":
                print("  ✅ Refund processed successfully")
            return {
                "success": True,
                "action_id": action["id"],
                "amount": amount,
                "status": "completed",
            }
        else:
            print(f"  ❌ Refund failed: {result.get('reason')}")
            return {
                "success": False,
                "reason": result.get("reason"),
                "status": result["status"],
            }

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def simulate_autogen_conversation():
    """Simulate AutoGen multi-agent conversation about refunds."""
    print("\n" + "=" * 80)
    print("🔒 AutoGen + Faramesh Demo: Human-in-the-Loop for High-Value Transactions")
    print("=" * 80)
    print()
    print("Scenario: AutoGen agents process customer refunds")
    print("Risk: Agents might approve large refunds without human oversight")
    print("Protection: Faramesh requires approval for transactions >= $1,000")
    print()
    print("-" * 80)
    print()

    # Test cases with different amounts
    test_cases = [
        {
            "customer_id": "CUST-001",
            "amount": 250.00,
            "reason": "Product defect - customer satisfaction",
        },
        {
            "customer_id": "CUST-002",
            "amount": 750.50,
            "reason": "Service not as described",
        },
        {
            "customer_id": "CUST-003",
            "amount": 1500.00,
            "reason": "Major product failure - business impact",
        },
        {
            "customer_id": "CUST-004",
            "amount": 5000.00,
            "reason": "Enterprise contract breach - legal requirement",
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 TEST CASE {i}/{len(test_cases)}")
        print("-" * 80)

        result = process_refund(**case)
        results.append({**case, **result})

        # Small delay between requests
        if i < len(test_cases):
            time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print("✅ Demo Complete - Summary")
    print("=" * 80)
    print()

    auto_approved = [r for r in results if r.get("success")]
    requires_approval = [r for r in results if r.get("requires_approval")]
    denied = [r for r in results if r.get("denied")]

    print("Results:")
    print(f"  - Auto-approved: {len(auto_approved)}")
    print(f"  - Requires human approval: {len(requires_approval)}")
    print(f"  - Denied: {len(denied)}")
    print()

    if auto_approved:
        print("✅ Auto-approved refunds:")
        for r in auto_approved:
            print(f"   - ${r['amount']:,.2f} for {r['customer_id']}")

    if requires_approval:
        print("\n⏳ Refunds requiring human approval:")
        for r in requires_approval:
            print(f"   - ${r['amount']:,.2f} for {r['customer_id']}")
            print(f"     Action ID: {r['action_id']}")

    print()
    print("Key Takeaways:")
    print("1. Low-value refunds (<$1,000) are auto-approved")
    print("2. High-value refunds (>=$1,000) require human approval")
    print("3. All transactions logged with full audit trail")
    print("4. Human-in-the-loop prevents costly mistakes")
    print("5. Policy is configurable per organization")
    print()


def run_demo():
    """Run the AutoGen refund approval demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    simulate_autogen_conversation()


if __name__ == "__main__":
    run_demo()
