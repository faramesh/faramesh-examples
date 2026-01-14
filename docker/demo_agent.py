"""
Demo agent that continuously submits actions to Faramesh every 30-60 seconds.

This agent runs in Docker and demonstrates the full workflow:
- Submit actions
- Check status
- Handle pending approval gracefully
- Continue running indefinitely
"""

import os
import time
import sys
import random

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.sdk.client import ExecutionGovernorClient


def main():
    api_base = os.getenv("FARA_API_BASE", "http://faramesh:8000")
    agent_id = os.getenv("FARA_AGENT_ID", "demo-agent")
    
    client = ExecutionGovernorClient(api_base)
    
    print(f"🚀 Demo agent starting (agent_id: {agent_id})")
    print(f"📡 Connecting to: {api_base}")
    print()
    
    # Wait for Faramesh to be ready
    print("⏳ Waiting for Faramesh server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            # Try to get health endpoint
            import requests
            response = requests.get(f"{api_base}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Faramesh server is ready!")
                break
        except Exception:
            if i < max_retries - 1:
                time.sleep(2)
            else:
                print("✗ Could not connect to Faramesh server")
                sys.exit(1)
    print()
    
    # Action templates - varied actions to demonstrate different scenarios
    action_templates = [
        {
            "tool": "http",
            "operation": "get",
            "params": {"url": "https://httpbin.org/get"},
            "description": "HTTP GET request",
        },
        {
            "tool": "shell",
            "operation": "run",
            "params": {"cmd": "echo 'Hello from demo agent'"},
            "description": "Safe echo command",
        },
        {
            "tool": "shell",
            "operation": "run",
            "params": {"cmd": "date"},
            "description": "Get current date",
        },
        {
            "tool": "shell",
            "operation": "run",
            "params": {"cmd": "ls -la /tmp | head -3"},
            "description": "List temp directory",
        },
        {
            "tool": "http",
            "operation": "get",
            "params": {"url": "https://api.github.com/zen"},
            "description": "GitHub API call",
        },
    ]
    
    action_count = 0
    
    print("🔄 Starting continuous action submission...")
    print("   (Actions will be submitted every 30-60 seconds)")
    print("   (Press CTRL+C to stop)")
    print()
    
    try:
        while True:
            # Pick a random action template
            action_spec = random.choice(action_templates)
            action_count += 1
            
            try:
                print(f"[{action_count}] Submitting: {action_spec['description']}")
                print(f"    Tool: {action_spec['tool']} / Operation: {action_spec['operation']}")
                
                action = client.submit_action(
                    tool=action_spec["tool"],
                    operation=action_spec["operation"],
                    params=action_spec["params"],
                    context={"agent_id": agent_id, "demo": True},
                )
                
                action_id = action['id']
                status = action['status']
                decision = action.get('decision', 'N/A')
                
                print(f"    Action ID: {action_id[:8]}...")
                print(f"    Status: {status}")
                print(f"    Decision: {decision}")
                
                # Handle different statuses
                if status == 'allowed':
                    print("    ✓ Action allowed - will execute")
                elif status == 'denied':
                    reason = action.get('reason', 'No reason provided')
                    print(f"    ✗ Action denied: {reason}")
                elif status == 'pending_approval':
                    print("    ⏳ Action requires approval")
                    print("    → Open http://localhost:8000 to approve/deny")
                    print("    → Agent will continue with next action")
                else:
                    print(f"    ? Status: {status}")
                
                print()
                
            except Exception as e:
                print(f"    ✗ Error submitting action: {e}")
                print()
            
            # Wait 30-60 seconds before next action
            wait_time = random.randint(30, 60)
            print(f"⏸  Waiting {wait_time} seconds until next action...")
            print()
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print()
        print("🛑 Demo agent stopped by user")
        print(f"   Total actions submitted: {action_count}")
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
