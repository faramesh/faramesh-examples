#!/usr/bin/env python3
"""
LangChain Email Manager Agent
Risk Level: MEDIUM
Manages email operations with approval requirements
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
    base_url="http://localhost:8000", agent_id="langchain-email-manager", timeout=10.0
)


def run_agent():
    """Run the LangChain Email Manager agent."""
    print("📧 LangChain Email Manager Agent Starting...")
    print(f"   Agent ID: langchain-email-manager")
    print(f"   Risk Level: MEDIUM")
    print(f"   Framework: LangChain")
    print()

    actions = [
        {
            "tool": "email",
            "operation": "read",
            "params": {"folder": "inbox", "limit": 50},
        },
        {
            "tool": "email",
            "operation": "send",
            "params": {
                "to": "team@company.com",
                "subject": "Weekly Report",
                "body": "Here is the weekly summary...",
                "attachments": [],
            },
        },
        {
            "tool": "email",
            "operation": "send",
            "params": {
                "to": "external-partner@example.com",
                "subject": "Partnership Inquiry",
                "body": "We'd like to discuss collaboration...",
                "cc": ["manager@company.com"],
            },
        },
        {
            "tool": "email",
            "operation": "delete",
            "params": {"message_ids": ["msg-12345"], "folder": "spam"},
        },
        {
            "tool": "email",
            "operation": "forward",
            "params": {"message_id": "msg-67890", "to": "archive@company.com"},
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"📨 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="langchain-email-manager",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "email management",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "user_initiated": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            if result.get("status") == "pending_approval":
                print(
                    f"   ⏳ Requires approval - Token: {result.get('approval_token')}"
                )
            print()

            iteration += 1
            time.sleep(random.uniform(4, 10))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
