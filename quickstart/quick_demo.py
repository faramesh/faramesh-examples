#!/usr/bin/env python3
"""Quick investor demo with real actions"""
import sys, os as _os
from pathlib import Path as _Path

# --- faramesh source resolution ---
# Priority: 1) installed package  2) PYTHONPATH env  3) sibling faramesh-core/src
def _add_faramesh_src():
    try:
        import faramesh  # already installed or on PYTHONPATH
        return
    except ImportError:
        pass
    # Look for a sibling faramesh-core clone
    _here = _Path(__file__).resolve().parent
    for _candidate in [
        _here.parent / "faramesh-core" / "src",
        _here.parent.parent / "faramesh-core" / "src",
        _Path.home() / "faramesh-core" / "src",
    ]:
        if (_candidate / "faramesh").is_dir():
            sys.path.insert(0, str(_candidate))
            return
    print("\n[faramesh] Could not find faramesh. Run:")
    print("  git clone https://github.com/faramesh/faramesh-core.git")
    print("  pip install -e ./faramesh-core  OR  export PYTHONPATH=./faramesh-core/src")
    sys.exit(1)

_add_faramesh_src()
# --- end faramesh source resolution ---

import sys
from pathlib import Path


from faramesh.adapters.langchain import faramesh_action_tool

print("🎭 FARAMESH INVESTOR DEMO\n")
print("Submitting realistic actions from AI agents...\n")

# Test 1: Low risk - email send (should auto-approve)
print("1. [ecommerce-assistant] email.send - Low risk")
r1 = faramesh_action_tool(
    "ecommerce-assistant",
    "email",
    "send",
    {
        "to": "customer@example.com",
        "subject": "Welcome to our store!",
        "body": "Thank you for signing up.",
    },
)
print(f"   ✅ {r1.get('status')} - {r1.get('decision')}\n")

# Test 2: Medium risk - payment refund (requires approval)
print("2. [financial-analyst] payment.refund - Medium risk")
r2 = faramesh_action_tool(
    "financial-analyst",
    "payment",
    "refund",
    {
        "transaction_id": "txn_1234567890",
        "amount": 49.99,
        "reason": "Customer not satisfied",
    },
)
print(f"   ⚠️  {r2.get('status')} - {r2.get('decision')}\n")

# Test 3: High risk - database delete (should deny)
print("3. [content-manager] database.delete - High risk")
r3 = faramesh_action_tool(
    "content-manager",
    "database",
    "delete",
    {"table": "users", "user_id": "user_12345", "permanent": True},
)
print(f"   🚫 {r3.get('status')} - {r3.get('decision')}\n")

# Test 4: Safe read operation
print("4. [data-analyst] database.query - Safe read")
r4 = faramesh_action_tool(
    "data-analyst",
    "database",
    "query",
    {
        "query": "SELECT * FROM transactions WHERE date > '2024-01-01'",
        "database": "analytics",
    },
)
print(f"   ✅ {r4.get('status')} - {r4.get('decision')}\n")

# Test 5: Social media post (requires approval)
print("5. [social-bot] social.publish - Requires approval")
r5 = faramesh_action_tool(
    "social-bot",
    "social",
    "publish",
    {
        "platforms": ["twitter", "linkedin"],
        "message": "Announcing our new AI governance platform! 🚀",
        "schedule": "immediate",
    },
)
print(f"   ⏳ {r5.get('status')} - {r5.get('decision')}\n")

print("=" * 60)
print("✅ 5 ACTIONS SUBMITTED FROM 5 DIFFERENT AGENTS")
print("=" * 60)
print("\n🌐 Check the UI at: http://localhost:3000")
print("\n📋 What to review:")
print("  • Dashboard: Real-time stats and recent actions")
print("  • Actions page: All 5 actions with status and risk levels")
print("  • Agents page: 5 unique agents now connected")
print("  • Approvals: 2 actions pending your decision")
print("  • Analytics: Action distribution by tool and risk\n")
