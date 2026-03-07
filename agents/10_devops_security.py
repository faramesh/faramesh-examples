#!/usr/bin/env python3
"""
DevOps Security Demo: Allow 'ls' but Block 'rm -rf'

This demo shows surgical command filtering - allowing safe read-only
operations while blocking dangerous write/delete operations.

Scenario:
- DevOps AI agent helps with server management
- Agent can list files, check processes, read logs
- Agent CANNOT delete files, kill processes, or modify system
- Faramesh enforces op-level granular control

Required Policy: devops_security_policy.yaml
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
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "devops-agent-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def execute_devops_command(cmd: str, purpose: str) -> dict:
    """Execute DevOps command through Faramesh gate."""
    print("\n💻 Executing DevOps command")
    print(f"   Command: {cmd}")
    print(f"   Purpose: {purpose}")
    print()

    # Categorize command for context
    if any(
        read_cmd in cmd.lower()
        for read_cmd in ["ls", "cat", "grep", "tail", "head", "ps", "top", "df"]
    ):
        risk_level = "low"
        operation_type = "read"
    elif any(
        write_cmd in cmd.lower() for write_cmd in ["echo", "touch", "mkdir", "cp"]
    ):
        risk_level = "medium"
        operation_type = "write"
    elif any(
        danger_cmd in cmd.lower()
        for danger_cmd in ["rm", "del", "kill", "shutdown", "reboot"]
    ):
        risk_level = "high"
        operation_type = "delete"
    else:
        risk_level = "medium"
        operation_type = "unknown"

    try:
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="shell",
            operation="execute",
            params={"cmd": cmd},
            context={
                "agent_framework": "devops",
                "purpose": purpose,
                "risk_level": risk_level,
                "operation_type": operation_type,
            },
        )

        print(f"✓ Action submitted: {action['id']}")
        print(f"  Status: {action['status']}")
        print(f"  Decision: {action.get('decision', 'N/A')}")
        print(f"  Risk Level: {risk_level}")

        if action["status"] == "denied":
            print(f"  ❌ BLOCKED: {action.get('reason')}")
            return {"success": False, "blocked": True, "reason": action.get("reason")}

        if action["status"] == "pending_approval":
            print(f"  ⏳ REQUIRES APPROVAL: {action.get('reason')}")
            return {
                "success": False,
                "requires_approval": True,
                "action_id": action["id"],
            }

        # Wait for execution
        result = wait_for_action(action["id"], timeout=30)

        if result["status"] == "succeeded":
            print("  ✅ Command executed successfully")
            output = result.get("reason", "")
            if output and len(output) < 200:
                print(f"  Output: {output[:200]}")
            return {"success": True, "output": output}
        else:
            print(f"  ❌ Execution failed: {result.get('reason')}")
            return {"success": False, "reason": result.get("reason")}

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def run_demo():
    """Run the DevOps security demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 DevOps Security Demo: Surgical Command Filtering")
    print("=" * 80)
    print()
    print("Scenario: DevOps AI agent helps with server management")
    print("Risk: Agent might execute dangerous commands accidentally")
    print("Protection: Faramesh allows safe commands, blocks dangerous ones")
    print()
    print("-" * 80)
    print()

    # Test cases demonstrating safe vs dangerous commands
    test_cases = [
        # Safe read-only commands
        {
            "cmd": "ls -la /tmp",
            "purpose": "Check temporary files",
        },
        {
            "cmd": "cat /var/log/syslog | tail -n 20",
            "purpose": "Check recent system logs",
        },
        {
            "cmd": "ps aux | grep python",
            "purpose": "Check running Python processes",
        },
        {
            "cmd": "df -h",
            "purpose": "Check disk space",
        },
        # Medium risk commands (might require approval)
        {
            "cmd": "echo 'test' > /tmp/test.txt",
            "purpose": "Create test file in safe directory",
        },
        {
            "cmd": "mkdir -p /tmp/agent_workspace",
            "purpose": "Create workspace directory",
        },
        # Dangerous commands (should be blocked)
        {
            "cmd": "rm -rf /var/log/*",
            "purpose": "Clean up old logs (DANGEROUS)",
        },
        {
            "cmd": "rm -rf /",
            "purpose": "Clear everything (CATASTROPHIC)",
        },
        {
            "cmd": "kill -9 1",
            "purpose": "Kill init process (SYSTEM CRASH)",
        },
        {
            "cmd": "chmod 777 /etc/passwd",
            "purpose": "Fix permissions (SECURITY RISK)",
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"📋 TEST CASE {i}/{len(test_cases)}")
        print("-" * 80)

        result = execute_devops_command(**case)
        results.append({**case, **result})

    # Summary
    print("\n" + "=" * 80)
    print("✅ Demo Complete - Summary")
    print("=" * 80)
    print()

    allowed = [r for r in results if r.get("success")]
    blocked = [r for r in results if r.get("blocked")]
    requires_approval = [r for r in results if r.get("requires_approval")]

    print("Results:")
    print(f"  - Allowed (safe commands): {len(allowed)}")
    print(f"  - Blocked (dangerous commands): {len(blocked)}")
    print(f"  - Requires approval: {len(requires_approval)}")
    print()

    if allowed:
        print("✅ Allowed Commands:")
        for r in allowed:
            print(f"   - {r['cmd'][:50]}... ({r['purpose'][:30]}...)")

    if blocked:
        print("\n❌ Blocked Commands (Prevented Disasters):")
        for r in blocked:
            print(f"   - {r['cmd'][:50]}...")
            print(f"     Purpose: {r['purpose']}")
            print(f"     Reason: {r.get('reason', 'Policy violation')}")

    if requires_approval:
        print("\n⏳ Commands Requiring Approval:")
        for r in requires_approval:
            print(f"   - {r['cmd'][:50]}...")

    print()
    print("Key Takeaways:")
    print("1. Read-only commands (ls, cat, ps, df) ALLOWED")
    print("2. Safe write commands (echo to /tmp) might be allowed or require approval")
    print("3. Dangerous commands (rm -rf, kill, chmod 777) BLOCKED")
    print("4. Surgical control: not blanket allow/deny")
    print("5. Context-aware: same command different contexts = different decisions")
    print()
    print("Op-Level Granularity:")
    print("  Traditional: 'Agent can use shell' (too broad)")
    print("  Faramesh: 'Agent can run shell.read but not shell.delete'")
    print()
    print("Real-World Impact:")
    print("  - Prevents accidental system damage")
    print("  - Enables safe DevOps automation")
    print("  - Maintains security without blocking productivity")
    print("  - Complete audit trail for compliance")
    print()


if __name__ == "__main__":
    run_demo()
