#!/usr/bin/env python3
"""
Custom Security Scanner Agent
Risk Level: LOW
Scans for security vulnerabilities
"""
import os
import sys
import time
import random
from datetime import datetime

sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000", agent_id="custom-security-scanner", timeout=10.0
)


def run_agent():
    """Run the Custom Security Scanner Agent."""
    print("🔒 Custom Security Scanner Agent Starting...")
    print(f"   Agent ID: custom-security-scanner")
    print(f"   Risk Level: LOW")
    print(f"   Framework: Custom")
    print()

    actions = [
        {
            "tool": "security",
            "operation": "scan_dependencies",
            "params": {
                "project_path": "/repos/company/product",
                "package_manager": "npm",
            },
        },
        {
            "tool": "security",
            "operation": "scan_code",
            "params": {
                "path": "/repos/company/product/src",
                "rules": ["sql-injection", "xss", "csrf"],
            },
        },
        {
            "tool": "http",
            "operation": "get",
            "params": {
                "url": "https://api.security.example.com/vulns",
                "headers": {"Authorization": "Bearer token"},
            },
        },
        {
            "tool": "file",
            "operation": "read",
            "params": {"path": "/configs/security-policy.yml"},
        },
        {
            "tool": "security",
            "operation": "check_secrets",
            "params": {
                "path": "/repos/company/product",
                "patterns": ["aws_key", "api_key", "password"],
            },
        },
        {
            "tool": "shell",
            "operation": "run",
            "params": {"command": "ls -la /Users"},
        },
        {
            "tool": "shell",
            "operation": "run",
            "params": {"command": "df -h"},
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"🛡️  Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="custom-security-scanner",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "security scanning",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "compliance_required": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
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
