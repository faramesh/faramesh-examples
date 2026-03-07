#!/usr/bin/env python3
"""
Haystack Search Agent
Risk Level: LOW
Performs search and retrieval operations
"""
import os
import sys
import time
import random
from datetime import datetime

sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000", agent_id="haystack-search-agent", timeout=10.0
)


def run_agent():
    """Run the Haystack Search Agent."""
    print("🔍 Haystack Search Agent Starting...")
    print(f"   Agent ID: haystack-search-agent")
    print(f"   Risk Level: LOW")
    print(f"   Framework: Haystack")
    print()

    actions = [
        {
            "tool": "search",
            "operation": "query",
            "params": {
                "query": "machine learning best practices",
                "index": "knowledge_base",
                "limit": 10,
            },
        },
        {
            "tool": "http",
            "operation": "get",
            "params": {
                "url": "https://api.search.example.com/v1/search",
                "params": {"q": "AI governance", "limit": 20},
            },
        },
        {
            "tool": "elasticsearch",
            "operation": "search",
            "params": {
                "index": "documents",
                "query": {"match": {"content": "policy enforcement"}},
                "size": 50,
            },
        },
        {
            "tool": "database",
            "operation": "read",
            "params": {
                "query": "SELECT title, content FROM articles WHERE category = 'AI'",
                "database": "content_db",
            },
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"🔎 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="haystack-search-agent",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "information retrieval",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            print()

            iteration += 1
            time.sleep(random.uniform(2, 6))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
