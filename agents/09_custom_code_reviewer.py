#!/usr/bin/env python3
"""
Custom Code Reviewer Agent
Risk Level: MEDIUM
Reviews and comments on code
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
    base_url="http://localhost:8000", agent_id="custom-code-reviewer", timeout=10.0
)


def run_agent():
    """Run the Custom Code Reviewer Agent."""
    print("👨‍💻 Custom Code Reviewer Agent Starting...")
    print(f"   Agent ID: custom-code-reviewer")
    print(f"   Risk Level: MEDIUM")
    print(f"   Framework: Custom")
    print()

    actions = [
        {
            "tool": "github",
            "operation": "create_pr_comment",
            "params": {
                "repo": "company/product",
                "pr_number": 123,
                "comment": "LGTM! Great work on this feature.",
                "position": 45,
            },
        },
        {
            "tool": "github",
            "operation": "approve_pr",
            "params": {
                "repo": "company/product",
                "pr_number": 124,
                "comment": "Approved after review",
            },
        },
        {
            "tool": "github",
            "operation": "request_changes",
            "params": {
                "repo": "company/product",
                "pr_number": 125,
                "comment": "Please add tests for the new function",
            },
        },
        {
            "tool": "gitlab",
            "operation": "add_mr_comment",
            "params": {
                "project_id": 456,
                "mr_id": 78,
                "body": "Consider using async/await here for better performance",
            },
        },
        {
            "tool": "file",
            "operation": "read",
            "params": {"path": "/repos/company/product/src/main.py", "lines": [1, 100]},
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"🔍 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="custom-code-reviewer",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "code review",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "automated_review": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            print()

            iteration += 1
            time.sleep(random.uniform(4, 9))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
