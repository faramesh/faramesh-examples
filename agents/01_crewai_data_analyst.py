#!/usr/bin/env python3
"""
CrewAI Data Analyst Agent
Risk Level: LOW
Performs safe data analysis operations
"""
import os
import sys
import time
import random
from datetime import datetime

# Add SDK to path
sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

from faramesh import configure, submit_action

# Configure SDK
configure(
    base_url="http://localhost:8000",
    agent_id="crewai-data-analyst",
    timeout=10.0,
    auth_token="demo-token-123",
)


def run_agent():
    """Run the CrewAI Data Analyst agent."""
    print("🤖 CrewAI Data Analyst Agent Starting...")
    print(f"   Agent ID: crewai-data-analyst")
    print(f"   Risk Level: LOW")
    print(f"   Framework: CrewAI")
    print()

    actions = [
        {
            "tool": "database",
            "operation": "read",
            "params": {
                "query": "SELECT * FROM users WHERE active = true LIMIT 100",
                "database": "analytics",
            },
        },
        {
            "tool": "http",
            "operation": "get",
            "params": {
                "url": "https://api.analytics.example.com/metrics",
                "headers": {"Content-Type": "application/json"},
            },
        },
        {
            "tool": "file",
            "operation": "read",
            "params": {"path": "/data/reports/monthly_stats.csv"},
        },
        {
            "tool": "data_processing",
            "operation": "aggregate",
            "params": {
                "dataset": "sales_data",
                "function": "sum",
                "groupby": "category",
            },
        },
    ]

    iteration = 1
    while True:
        try:
            # Pick a random action
            action = random.choice(actions)

            print(f"📊 Iteration {iteration}: {action['tool']}.{action['operation']}")

            # Submit action for governance
            result = submit_action(
                agent_id="crewai-data-analyst",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "data analysis",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            if result.get("reason"):
                print(f"   Reason: {result.get('reason')}")
            print()

            iteration += 1

            # Wait before next action
            time.sleep(random.uniform(3, 8))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
