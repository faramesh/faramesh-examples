#!/usr/bin/env python3
"""
MCP (Model Context Protocol) + Faramesh Demo: Securing the Filesystem Server

This demo shows how Faramesh secures MCP filesystem server operations,
preventing unauthorized file access and dangerous operations.

Scenario:
- MCP server provides filesystem access to LLM
- Agent can read files but cannot write/delete system files
- Faramesh enforces path restrictions and operation constraints

Required Policy: mcp_filesystem_policy.yaml
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
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
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "mcp-filesystem-client-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


class SecuredMCPFilesystem:
    """MCP Filesystem server secured by Faramesh.

    This class wraps MCP filesystem operations with Faramesh security gates.
    All file operations must pass through the execution gate.
    """

    def __init__(self, allowed_paths: Optional[list[str]] = None):
        """Initialize with optional path restrictions."""
        self.allowed_paths = allowed_paths or [
            "/tmp",
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
        ]

    def read_file(self, file_path: str) -> dict:
        """Read file through Faramesh gate."""
        print(f"\n📖 Reading file: {file_path}")

        try:
            action = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="filesystem",
                operation="read",
                params={
                    "path": file_path,
                    "operation_type": "read",
                },
                context={
                    "agent_framework": "mcp",
                    "server_type": "filesystem",
                    "allowed_paths": self.allowed_paths,
                },
            )

            print(f"   Action: {action['id']}")
            print(f"   Status: {action['status']}")
            print(f"   Decision: {action.get('decision', 'N/A')}")

            if action["status"] == "denied":
                print(f"   ❌ BLOCKED: {action.get('reason')}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": action.get("reason"),
                }

            # Simulate file read (in real scenario, would read from filesystem)
            result = wait_for_action(action["id"], timeout=10)

            if result["status"] == "succeeded":
                print("   ✅ Read allowed")
                return {
                    "success": True,
                    "content": f"[Simulated content of {file_path}]",
                }
            else:
                return {"success": False, "reason": result.get("reason")}

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str) -> dict:
        """Write file through Faramesh gate."""
        print(f"\n✍️  Writing file: {file_path}")
        print(f"   Content length: {len(content)} bytes")

        try:
            action = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="filesystem",
                operation="write",
                params={
                    "path": file_path,
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "operation_type": "write",
                },
                context={
                    "agent_framework": "mcp",
                    "server_type": "filesystem",
                    "allowed_paths": self.allowed_paths,
                },
            )

            print(f"   Action: {action['id']}")
            print(f"   Status: {action['status']}")
            print(f"   Decision: {action.get('decision', 'N/A')}")

            if action["status"] == "denied":
                print(f"   ❌ BLOCKED: {action.get('reason')}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": action.get("reason"),
                }

            if action["status"] == "pending_approval":
                print(f"   ⏳ REQUIRES APPROVAL: {action.get('reason')}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "action_id": action["id"],
                }

            result = wait_for_action(action["id"], timeout=10)

            if result["status"] == "succeeded":
                print("   ✅ Write allowed")
                return {"success": True}
            else:
                return {"success": False, "reason": result.get("reason")}

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path: str) -> dict:
        """Delete file through Faramesh gate."""
        print(f"\n🗑️  Deleting file: {file_path}")

        try:
            action = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="filesystem",
                operation="delete",
                params={
                    "path": file_path,
                    "operation_type": "delete",
                },
                context={
                    "agent_framework": "mcp",
                    "server_type": "filesystem",
                    "allowed_paths": self.allowed_paths,
                },
            )

            print(f"   Action: {action['id']}")
            print(f"   Status: {action['status']}")
            print(f"   Decision: {action.get('decision', 'N/A')}")

            if action["status"] == "denied":
                print(f"   ❌ BLOCKED: {action.get('reason')}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": action.get("reason"),
                }

            if action["status"] == "pending_approval":
                print(f"   ⏳ REQUIRES APPROVAL: {action.get('reason')}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "action_id": action["id"],
                }

            result = wait_for_action(action["id"], timeout=10)

            if result["status"] == "succeeded":
                print("   ✅ Delete allowed")
                return {"success": True}
            else:
                return {"success": False, "reason": result.get("reason")}

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"success": False, "error": str(e)}


def run_demo():
    """Run the MCP filesystem security demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 MCP + Faramesh Demo: Securing Filesystem Server")
    print("=" * 80)
    print()
    print("Scenario: MCP server provides filesystem access to LLM")
    print("Risk: Agent could read sensitive files or delete system files")
    print("Protection: Faramesh enforces path restrictions and operation constraints")
    print()
    print("-" * 80)
    print()

    # Initialize secured filesystem
    fs = SecuredMCPFilesystem(allowed_paths=["/tmp", "/home/user/safe_directory"])

    # Test 1: Read allowed file
    print("📋 TEST 1: Read file in allowed directory")
    print("-" * 80)
    result = fs.read_file("/tmp/test.txt")
    print(f"Result: {'✅ Success' if result.get('success') else '❌ Failed'}")

    # Test 2: Read restricted file
    print("\n📋 TEST 2: Read restricted system file")
    print("-" * 80)
    result = fs.read_file("/etc/passwd")
    print(
        f"Result: {'✅ Success' if result.get('success') else '❌ Blocked (as expected)'}"
    )

    # Test 3: Write to allowed directory
    print("\n📋 TEST 3: Write file in allowed directory")
    print("-" * 80)
    result = fs.write_file("/tmp/output.txt", "Hello from MCP + Faramesh!")
    print(f"Result: {'✅ Success' if result.get('success') else '❌ Failed'}")

    # Test 4: Write to system directory
    print("\n📋 TEST 4: Write to system directory")
    print("-" * 80)
    result = fs.write_file("/etc/malicious.txt", "Bad content")
    print(
        f"Result: {'✅ Success' if result.get('success') else '❌ Blocked (as expected)'}"
    )

    # Test 5: Delete file
    print("\n📋 TEST 5: Delete file in allowed directory")
    print("-" * 80)
    result = fs.delete_file("/tmp/old_file.txt")
    print(
        f"Result: {'✅ Success' if result.get('success') else '❌ Requires approval'}"
    )

    # Test 6: Delete system file
    print("\n📋 TEST 6: Delete critical system file")
    print("-" * 80)
    result = fs.delete_file("/etc/hosts")
    print(
        f"Result: {'✅ Success' if result.get('success') else '❌ Blocked (as expected)'}"
    )

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. MCP filesystem operations are gated by Faramesh")
    print("2. Path-based access control prevents unauthorized file access")
    print("3. Dangerous operations (delete) require approval")
    print("4. Read operations allowed for safe paths")
    print("5. Complete audit trail of all file operations")
    print()


if __name__ == "__main__":
    run_demo()
