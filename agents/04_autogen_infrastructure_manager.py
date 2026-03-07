#!/usr/bin/env python3
"""
AutoGen Infrastructure Manager Agent
Risk Level: CRITICAL
Manages cloud infrastructure with dangerous operations
"""
import os
import sys
import time
import random
from datetime import datetime

sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000", agent_id="autogen-infra-manager", timeout=10.0
)


def run_agent():
    """Run the AutoGen Infrastructure Manager agent."""
    print("🏗️  AutoGen Infrastructure Manager Agent Starting...")
    print(f"   Agent ID: autogen-infra-manager")
    print(f"   Risk Level: CRITICAL")
    print(f"   Framework: AutoGen")
    print()

    actions = [
        {
            "tool": "aws",
            "operation": "create_instance",
            "params": {
                "instance_type": "t3.micro",
                "ami_id": "ami-12345678",
                "region": "us-east-1",
                "security_groups": ["sg-default"],
            },
        },
        {
            "tool": "aws",
            "operation": "terminate_instance",
            "params": {"instance_id": "i-0123456789abcdef0", "region": "us-east-1"},
        },
        {
            "tool": "kubernetes",
            "operation": "delete_namespace",
            "params": {"namespace": "staging", "cluster": "prod-cluster"},
        },
        {
            "tool": "shell",
            "operation": "execute",
            "params": {"command": "sudo rm -rf /tmp/cache/*", "server": "prod-web-01"},
        },
        {
            "tool": "database",
            "operation": "drop_table",
            "params": {"table": "old_logs", "database": "analytics_archive"},
        },
        {
            "tool": "gcp",
            "operation": "delete_disk",
            "params": {"disk_name": "backup-disk-2023", "zone": "us-central1-a"},
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"⚠️  Iteration {iteration}: {action['tool']}.{action['operation']}")
            print(f"   CRITICAL OPERATION!")

            result = submit_action(
                agent_id="autogen-infra-manager",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "infrastructure management",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "environment": "production",
                    "requires_audit": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            if result.get("status") == "denied":
                print(f"   🚫 BLOCKED - Too dangerous!")
            elif result.get("status") == "pending_approval":
                print(f"   ⏳ Requires SRE Lead approval")
            print()

            iteration += 1
            time.sleep(random.uniform(6, 15))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
