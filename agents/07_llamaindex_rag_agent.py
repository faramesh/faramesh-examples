#!/usr/bin/env python3
"""
LlamaIndex RAG Agent
Risk Level: LOW
Performs retrieval-augmented generation
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
