"""
Simple AI agent demo using Faramesh SDK to test governance.
Simulates an AI agent performing various tasks that get governed by policies.
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


import sys

# Add Horizon SDK to path

try:
    from faramesh.sdk import ExecutionGovernorClient, GovernorConfig

    # Initialize client
    config = GovernorConfig(base_url="http://localhost:8000")
    faramesh = ExecutionGovernorClient(config)
except ImportError:
    print("⚠️  Warning: Faramesh SDK not available. This is a demo simulation.")
    faramesh = None

print("=" * 80)
print("🤖 AI AGENT SIMULATION - Testing Faramesh Governance")
print("=" * 80)
print()

# Simulate AI agent tasks
tasks = [
    {
        "name": "Research Task",
        "agent_id": "research-assistant",
        "tool": "http",
        "operation": "get",
        "params": {"url": "https://api.github.com/repos/openai/gpt-3"},
        "context": {"task": "research latest AI models"},
    },
    {
        "name": "Database Query",
        "agent_id": "data-analyst",
        "tool": "database",
        "operation": "select",
        "params": {"query": "SELECT * FROM customers WHERE plan = 'enterprise'"},
        "context": {"report": "enterprise customer list"},
    },
    {
        "name": "Email Notification",
        "agent_id": "notification-bot",
        "tool": "email",
        "operation": "send",
        "params": {
            "to": "admin@company.com",
            "subject": "Alert: System Update Required",
        },
        "context": {"automated": True},
    },
    {
        "name": "File Cleanup (RISKY)",
        "agent_id": "maintenance-bot",
        "tool": "shell",
        "operation": "run",
        "params": {"cmd": "rm -rf /tmp/cache/*"},
        "context": {"cleanup": "cache files"},
    },
    {
        "name": "Payment Refund (NEEDS APPROVAL)",
        "agent_id": "support-agent",
        "tool": "payments",
        "operation": "refund",
        "params": {"amount": 450, "currency": "usd", "reason": "service issue"},
        "context": {"customer_complaint": True},
    },
]

print("Simulating AI agent performing tasks...\n")

for i, task in enumerate(tasks, 1):
    print(f"[{i}/{len(tasks)}] {task['name']}")
    print(f"  Agent: {task['agent_id']}")
    print(f"  Action: {task['tool']}.{task['operation']}")

    try:
        if faramesh is None:
            print("  ⚠️  SDK not available, skipping...")
            continue

        action = faramesh.submit_action(
            tool=task["tool"],
            operation=task["operation"],
            params=task["params"],
            context=task["context"],
        )

        status = action.get("status", "unknown")
        decision = action.get("decision", "unknown")
        reason = action.get("reason", "No reason provided")
        risk = action.get("risk_level", "unknown")

        if decision == "allow":
            print(f"  ✅ ALLOWED (risk: {risk})")
        elif decision == "deny":
            print(f"  ❌ DENIED (risk: {risk})")
            print(f"     Reason: {reason}")
        elif decision == "require_approval":
            print(f"  ⏳ REQUIRES APPROVAL (risk: {risk})")
            print(f"     Reason: {reason}")
            print(f"     Action ID: {action.get('id')}")

    except Exception as e:
        print(f"  ⚠️  Error: {str(e)}")

    print()

print("=" * 80)
print("✅ AI Agent Simulation Complete!")
print()
print("Check the dashboard to see all actions:")
print("  • Agents Page:    http://localhost:3000/agents")
print("  • Approvals Page: http://localhost:3000/approvals")
print("  • Audit Logs:    http://localhost:3000/audit")
print("  • Usage Stats:    http://localhost:3000/usage")
print("=" * 80)
