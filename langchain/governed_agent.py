"""
Example: LangChain agent with Faramesh governance

This is a minimal, runnable demo showing how to wrap LangChain tools with Faramesh.
It demonstrates:
- Wrapping 1-2 simple tools (HTTP GET + shell run)
- Submitting to Faramesh before execution
- Detecting allow/deny/pending status
- Handling pending approval (wait or exit with message)

Run this after starting: faramesh serve
"""

import sys
import time
import requests
from typing import Any

# Simple HTTP tool (no LangChain dependency for minimal demo)
class SimpleHTTPTool:
    """Simple HTTP GET tool."""
    name = "http"
    
    def run(self, url: str) -> str:
        """Make HTTP GET request."""
        response = requests.get(url, timeout=5)
        return f"Status {response.status_code}: {response.text[:100]}"


# Simple Shell tool (no LangChain dependency for minimal demo)
class SimpleShellTool:
    """Simple shell command tool."""
    name = "shell"
    
    def run(self, cmd: str) -> str:
        """Execute shell command."""
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout


from faramesh.sdk.client import ExecutionGovernorClient
from faramesh.integrations.langchain.governed_tool import GovernedTool


def main():
    """Run governed agent demo."""
    print("=" * 60)
    print("Faramesh + LangChain Demo")
    print("=" * 60)
    print()
    
    # Initialize Faramesh client
    api_base = "http://127.0.0.1:8000"
    client = ExecutionGovernorClient(api_base)
    
    print(f"✓ Connected to Faramesh at {api_base}")
    print()
    
    # Create tools
    http_tool = SimpleHTTPTool()
    shell_tool = SimpleShellTool()
    
    # Wrap with Faramesh governance
    governed_http = GovernedTool(
        tool=http_tool,
        client=client,
        agent_id="langchain-demo",
        max_wait_time=30.0,  # Wait max 30 seconds for approval
    )
    
    governed_shell = GovernedTool(
        tool=shell_tool,
        client=client,
        agent_id="langchain-demo",
        max_wait_time=30.0,
    )
    
    print("✓ Tools wrapped with Faramesh governance")
    print()
    
    # Test 1: HTTP GET (usually allowed)
    print("Test 1: HTTP GET request")
    print("-" * 60)
    try:
        result = governed_http.run("https://httpbin.org/get")
        print(f"✓ Allowed - Result: {result[:80]}...")
    except PermissionError as e:
        print(f"✗ Denied: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 2: Safe shell command (may require approval)
    print("Test 2: Shell command (echo)")
    print("-" * 60)
    try:
        result = governed_shell.run("echo 'Hello from Faramesh'")
        print(f"✓ Allowed - Result: {result.strip()}")
    except PermissionError as e:
        print(f"✗ Denied: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 3: Potentially risky command (likely requires approval)
    print("Test 3: Shell command (list files)")
    print("-" * 60)
    try:
        result = governed_shell.run("ls -la /tmp | head -5")
        print(f"✓ Allowed - Result: {result.strip()}")
    except PermissionError as e:
        print(f"✗ Denied: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    print("=" * 60)
    print("Demo complete!")
    print()
    print("If any actions are pending approval:")
    print("  1. Open http://127.0.0.1:8000 in your browser")
    print("  2. Find the pending action in the table")
    print("  3. Click the row to see details")
    print("  4. Click 'Approve' or 'Deny'")
    print("  5. Re-run this script to see the result")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure Faramesh server is running:")
        print("  faramesh serve")
        sys.exit(1)
