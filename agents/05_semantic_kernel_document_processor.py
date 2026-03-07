#!/usr/bin/env python3
"""
Semantic Kernel Document Processor Agent
Risk Level: LOW
Processes documents safely
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
    base_url="http://localhost:8000",
    agent_id="semantic-kernel-doc-processor",
    timeout=10.0,
    auth_token="demo-token-123",
)


def run_agent():
    """Run the Semantic Kernel Document Processor agent."""
    print("📄 Semantic Kernel Document Processor Agent Starting...")
    print(f"   Agent ID: semantic-kernel-doc-processor")
    print(f"   Risk Level: LOW")
    print(f"   Framework: Semantic Kernel")
    print()

    actions = [
        {
            "tool": "file",
            "operation": "read",
            "params": {"path": "/documents/contracts/agreement.pdf", "format": "pdf"},
        },
        {
            "tool": "ocr",
            "operation": "extract_text",
            "params": {"image_path": "/scans/invoice_001.png", "language": "en"},
        },
        {
            "tool": "nlp",
            "operation": "summarize",
            "params": {"text": "Long document text here...", "max_length": 500},
        },
        {
            "tool": "file",
            "operation": "convert",
            "params": {
                "source": "/documents/report.docx",
                "target_format": "pdf",
                "preserve_formatting": True,
            },
        },
        {
            "tool": "document",
            "operation": "classify",
            "params": {
                "document_id": "doc_12345",
                "categories": ["contract", "invoice", "report"],
            },
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"📝 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="semantic-kernel-doc-processor",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "document processing",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            print()

            iteration += 1
            time.sleep(random.uniform(3, 7))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
