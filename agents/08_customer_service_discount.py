#!/usr/bin/env python3
"""
Customer Service Demo: Preventing 100% Discount (eBay/Artium Case)

This demo shows how Faramesh prevents customer service agents from
giving excessive discounts or refunds that would hurt the business.

Scenario:
- CS agent wants to make customer happy
- LLM suggests 100% discount to solve complaint
- Faramesh blocks discounts > 30% threshold
- Requires manager approval for >30% discounts

Required Policy: customer_service_policy.yaml
"""

import os
import sys
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
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "cs-agent-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def apply_discount(
    order_id: str, original_price: float, discount_percent: float, reason: str
) -> dict:
    """Apply discount through Faramesh gate."""
    discount_amount = original_price * (discount_percent / 100)
    final_price = original_price - discount_amount

    print(f"\n💳 Applying {discount_percent}% discount to order {order_id}")
    print(f"   Original: ${original_price:.2f}")
    print(f"   Discount: -${discount_amount:.2f} ({discount_percent}%)")
    print(f"   Final: ${final_price:.2f}")
    print(f"   Reason: {reason}")
    print()

    try:
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="billing",
            operation="apply_discount",
            params={
                "order_id": order_id,
                "original_price": original_price,
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "final_price": final_price,
                "reason": reason,
            },
            context={
                "agent_framework": "customer_service",
                "agent_role": "cs_representative",
                "risk_level": (
                    "high"
                    if discount_percent >= 50
                    else "medium" if discount_percent >= 30 else "low"
                ),
            },
        )

        print(f"✓ Action submitted: {action['id']}")
        print(f"  Status: {action['status']}")
        print(f"  Decision: {action.get('decision', 'N/A')}")

        if action["status"] == "denied":
            print(f"  ❌ BLOCKED: {action.get('reason')}")
            return {"success": False, "blocked": True, "reason": action.get("reason")}

        if action["status"] == "pending_approval":
            print("  ⏳ REQUIRES MANAGER APPROVAL")
            print(f"     Reason: {action.get('reason')}")
            print(f"     Action ID: {action['id']}")
            return {
                "success": False,
                "requires_approval": True,
                "action_id": action["id"],
                "discount_percent": discount_percent,
            }

        result = wait_for_action(action["id"], timeout=30)

        if result["status"] == "succeeded":
            print("  ✅ Discount applied successfully")
            return {"success": True, "final_price": final_price}
        else:
            return {"success": False, "reason": result.get("reason")}

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def run_demo():
    """Run the customer service discount demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 Customer Service Demo: Preventing Excessive Discounts")
    print("=" * 80)
    print()
    print("Scenario: CS agent wants to make unhappy customer happy")
    print("Risk: LLM might suggest 100% discount to solve complaint")
    print("Protection: Faramesh blocks excessive discounts and requires approval")
    print()
    print("Real-World Context:")
    print("  - eBay CS agents under pressure to satisfy customers")
    print("  - Artium case: AI agent gave away too much to make customer happy")
    print("  - Cost: Thousands of dollars in unnecessary discounts")
    print()
    print("-" * 80)
    print()

    # Test cases with different discount levels
    test_cases = [
        {
            "order_id": "ORD-001",
            "original_price": 99.99,
            "discount_percent": 10,
            "reason": "First-time customer welcome discount",
        },
        {
            "order_id": "ORD-002",
            "original_price": 299.99,
            "discount_percent": 25,
            "reason": "Product arrived 2 days late",
        },
        {
            "order_id": "ORD-003",
            "original_price": 499.99,
            "discount_percent": 50,
            "reason": "Customer very unhappy, wants to retain",
        },
        {
            "order_id": "ORD-004",
            "original_price": 799.99,
            "discount_percent": 100,
            "reason": "Major product defect, customer threatening lawsuit",
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 TEST CASE {i}/{len(test_cases)}")
        print("-" * 80)

        result = apply_discount(**case)
        results.append({**case, **result})

    # Summary
    print("\n" + "=" * 80)
    print("✅ Demo Complete - Summary")
    print("=" * 80)
    print()

    auto_approved = [r for r in results if r.get("success")]
    requires_approval = [r for r in results if r.get("requires_approval")]
    blocked = [r for r in results if r.get("blocked")]

    print("Results:")
    print(f"  - Auto-approved: {len(auto_approved)}")
    print(f"  - Requires manager approval: {len(requires_approval)}")
    print(f"  - Blocked: {len(blocked)}")
    print()

    if auto_approved:
        print("✅ Auto-approved discounts (safe threshold):")
        for r in auto_approved:
            print(
                f"   - {r['discount_percent']}% on {r['order_id']} (${r['original_price']:.2f})"
            )

    if requires_approval:
        print("\n⏳ Discounts requiring manager approval (30-80% range):")
        for r in requires_approval:
            print(
                f"   - {r['discount_percent']}% on {r['order_id']} (${r['original_price']:.2f})"
            )

    if blocked:
        print("\n❌ Discounts BLOCKED (>80% or 100%):")
        for r in blocked:
            print(
                f"   - {r['discount_percent']}% on {r['order_id']} - PREVENTED ${ (r['original_price'] * r['discount_percent'] / 100):.2f} loss"
            )

    print()
    print("Key Takeaways:")
    print("1. Small discounts (<30%) auto-approved for CS efficiency")
    print("2. Medium discounts (30-80%) require manager approval")
    print("3. Large discounts (>80%) blocked entirely")
    print("4. Prevents 'make customer happy at any cost' mentality")
    print("5. Saves thousands in prevented excessive discounts")
    print()
    print("Business Impact:")
    if blocked:
        total_saved = sum(
            r["original_price"] * r["discount_percent"] / 100 for r in blocked
        )
        print(f"  💰 In this demo alone, prevented ${total_saved:.2f} in losses!")
    print("  - CS agents can still help customers effectively")
    print("  - Business protected from runaway discounts")
    print("  - Complete audit trail for finance team")
    print()


if __name__ == "__main__":
    run_demo()
