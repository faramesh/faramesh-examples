#!/usr/bin/env python3
"""
LangGraph Payment Processor Agent
Risk Level: HIGH
Processes financial transactions requiring strict oversight
"""
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

import os
import sys
import time
import random
from datetime import datetime


from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000",
    agent_id="langraph-payment-processor",
    timeout=10.0,
    auth_token="demo-token-123",
)


def run_agent():
    """Run the LangGraph Payment Processor agent."""
    print("💳 LangGraph Payment Processor Agent Starting...")
    print(f"   Agent ID: langraph-payment-processor")
    print(f"   Risk Level: HIGH")
    print(f"   Framework: LangGraph")
    print()

    actions = [
        {
            "tool": "payment",
            "operation": "process",
            "params": {
                "amount": 49.99,
                "currency": "USD",
                "customer_id": "cust_123",
                "payment_method": "card_ending_4242",
            },
        },
        {
            "tool": "payment",
            "operation": "refund",
            "params": {
                "transaction_id": "txn_abc123",
                "amount": 29.99,
                "reason": "customer_request",
            },
        },
        {
            "tool": "payment",
            "operation": "process",
            "params": {
                "amount": 1299.00,
                "currency": "USD",
                "customer_id": "cust_456",
                "payment_method": "card_ending_5555",
            },
        },
        {
            "tool": "stripe",
            "operation": "create_customer",
            "params": {"email": "newcustomer@example.com", "name": "New Customer"},
        },
        {
            "tool": "stripe",
            "operation": "charge",
            "params": {
                "amount": 5000,
                "currency": "usd",
                "source": "tok_visa",
                "description": "Subscription fee",
            },
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"💰 Iteration {iteration}: {action['tool']}.{action['operation']}")
            print(f"   Amount: ${action['params'].get('amount', 'N/A')}")

            result = submit_action(
                agent_id="langraph-payment-processor",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "payment processing",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "compliance_check": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            if result.get("status") == "pending_approval":
                print(f"   ⏳ HIGH VALUE - Requires CFO approval")
            print()

            iteration += 1
            time.sleep(random.uniform(5, 12))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
