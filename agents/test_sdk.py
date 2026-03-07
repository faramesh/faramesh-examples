#!/usr/bin/env python3
"""
Quick SDK Test - Verify Faramesh SDK works correctly
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
from faramesh import configure, submit_action

print("🧪 Testing Faramesh SDK")
print("=" * 60)

# Configure SDK
print("\n1. Configuring SDK...")
configure(
    base_url=os.getenv("FARAMESH_URL", "http://localhost:8000"),
    token=os.getenv("FARAMESH_API_KEY", "demo-api-key-123"),
)
print("✅ SDK configured")

# Submit test action
print("\n2. Submitting test action...")
try:
    result = submit_action(
        agent_id="sdk-test-agent",
        tool="shell",
        operation="execute",
        params={"cmd": "echo 'Hello from SDK'"},
    )
    print(f"✅ Action submitted: {result.get('id', 'unknown')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Decision: {result.get('decision')}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  Make sure Faramesh server is running:")
    print("   python -m faramesh.server.main  # or: faramesh serve")

print("\n" + "=" * 60)
print("✅ SDK TEST COMPLETE")
