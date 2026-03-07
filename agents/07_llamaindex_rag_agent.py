#!/usr/bin/env python3
"""
LlamaIndex RAG Agent
Risk Level: LOW
Performs retrieval-augmented generation
"""
import os
import sys
import time
import random
from datetime import datetime

sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000", agent_id="llamaindex-rag-agent", timeout=10.0
)


def run_agent():
    """Run the LlamaIndex RAG Agent."""
    print("🧠 LlamaIndex RAG Agent Starting...")
    print(f"   Agent ID: llamaindex-rag-agent")
    print(f"   Risk Level: LOW")
    print(f"   Framework: LlamaIndex")
    print()

    actions = [
        {
            "tool": "vector_db",
            "operation": "query",
            "params": {
                "query_vector": [0.1, 0.2, 0.3],
                "collection": "embeddings",
                "top_k": 5,
            },
        },
        {
            "tool": "llm",
            "operation": "generate",
            "params": {
                "prompt": "Summarize the following document...",
                "model": "gpt-3.5-turbo",
                "max_tokens": 500,
            },
        },
        {
            "tool": "file",
            "operation": "read",
            "params": {"path": "/knowledge/documents/faq.txt", "encoding": "utf-8"},
        },
        {
            "tool": "embedding",
            "operation": "create",
            "params": {
                "text": "What is AI governance?",
                "model": "text-embedding-ada-002",
            },
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"🤔 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="llamaindex-rag-agent",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "rag pipeline",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            print()

            iteration += 1
            time.sleep(random.uniform(3, 8))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
