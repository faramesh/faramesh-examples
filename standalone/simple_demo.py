#!/usr/bin/env python3
import requests, json, time

URL = "http://localhost:8000/v1/actions"
HEADERS = {"Content-Type": "application/json", "X-User-ID": "demo-user"}

print("\n🎭 FARAMESH INVESTOR DEMO\n")

tests = [
    {
        "agent": "ecommerce-bot",
        "tool": "email",
        "op": "send",
        "params": {"to": "customer@example.com", "subject": "Welcome"},
        "expect": "✅ APPROVED",
    },
    {
        "agent": "financial-bot",
        "tool": "payment",
        "op": "refund",
        "params": {"amount": 499.99, "txn": "tx_123"},
        "expect": "⏳ PENDING",
    },
    {
        "agent": "admin-bot",
        "tool": "database",
        "op": "delete",
        "params": {"table": "users", "id": "123"},
        "expect": "🚫 DENIED",
    },
    {
        "agent": "analytics-bot",
        "tool": "database",
        "op": "query",
        "params": {"query": "SELECT *"},
        "expect": "✅ APPROVED",
    },
    {
        "agent": "social-bot",
        "tool": "social",
        "op": "publish",
        "params": {"msg": "Hello!"},
        "expect": "⏳ PENDING",
    },
]

print("Submitting 5 actions from 5 different agents...\n")

for i, test in enumerate(tests, 1):
    payload = {
        "agent_id": test["agent"],
        "tool": test["tool"],
        "operation": test["op"],
        "params": test["params"],
        "context": {},
    }

    r = requests.post(URL, json=payload, headers=HEADERS)
    data = r.json()

    action_id = data.get("id", "N/A")[:12]
    status = data.get("status", "unknown")
    decision = data.get("decision", "unknown")

    print(f"{i}. [{test['agent']}] {test['tool']}.{test['op']}")
    print(f"   ID: {action_id}...")
    print(f"   Status: {status} | Decision: {decision}")
    print(f"   Expected: {test['expect']}\n")

    time.sleep(0.5)

print("=" * 60)
print("✅ 5 ACTIONS SUBMITTED!")
print("=" * 60)
print("\n🌐 Open UI: http://localhost:3000")
print("\n📋 Check these pages:")
print("  • Dashboard - See 5 new actions")
print("  • Actions - Full list with statuses")
print("  • Agents - 5 unique agents")
print("  • Approvals - Pending actions\n")
