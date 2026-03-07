#!/usr/bin/env python3
"""
Quick SDK Test - Verify Faramesh SDK works correctly
"""

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
    print("   cd faramesh-horizon-code && python3 -m faramesh.server.main")

print("\n" + "=" * 60)
print("✅ SDK TEST COMPLETE")
