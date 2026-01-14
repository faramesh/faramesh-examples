"""
LlamaIndex + Faramesh Integration Example

Simple tool wrapper that submits actions to Faramesh before execution.

Usage:
    pip install faramesh llama-index llama-index-llms-openai
    export OPENAI_API_KEY=your-key
    faramesh serve
    python examples/llamaindex/governed_agent.py

If action is pending approval:
    1. Open http://127.0.0.1:8000
    2. Approve the pending action
    3. Re-run or call the tool again
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.sdk.client import ExecutionGovernorClient


def create_governed_tool():
    """Create a governed tool for LlamaIndex."""
    try:
        from llama_index.core.tools import FunctionTool
        from llama_index.core.tools.types import ToolMetadata
        
        def http_get(url: str) -> str:
            """Fetch a URL."""
            client = ExecutionGovernorClient("http://127.0.0.1:8000")
            
            # Submit to Faramesh
            action = client.submit_action(
                tool="http",
                operation="get",
                params={"url": url},
                context={"agent_id": "llamaindex-demo"},
            )
            
            action_id = action['id']
            status = action['status']
            decision = action.get('decision', '')
            
            print(f"Action ID: {action_id[:8]}...")
            print(f"Status: {status}, Decision: {decision}")
            
            # Check decision
            if decision == 'deny' or status == 'denied':
                reason = action.get('reason', 'Action denied by policy')
                raise PermissionError(f"Action denied: {reason}")
            
            if status == 'pending_approval':
                print(f"⏳ Pending approval. Action ID: {action_id}")
                print(f"→ Open http://127.0.0.1:8000 to approve")
                print(f"→ After approving, re-run this script or call the tool again")
                raise PermissionError(f"Action pending approval: {action_id}")
            
            # Execute if allowed
            if status not in ('allowed', 'approved'):
                raise PermissionError(f"Action not approved. Status: {status}")
            
            # Execute HTTP request
            try:
                import requests
                response = requests.get(url, timeout=5)
                result = f"Status {response.status_code}: {response.text[:100]}"
                
                # Report result
                client.report_result(action_id, success=True, result=result)
                
                return result
            except Exception as e:
                client.report_result(action_id, success=False, error=str(e))
                raise
        
        # Create LlamaIndex tool
        tool = FunctionTool.from_defaults(
            fn=http_get,
            name="http_get",
            description="Fetch a URL via HTTP GET request",
        )
        
        return tool
        
    except ImportError:
        return None


def main():
    """Run governed agent."""
    print("=" * 60)
    print("LlamaIndex + Faramesh Integration")
    print("=" * 60)
    print()
    
    try:
        from llama_index.core.agent import ReActAgent
        from llama_index.llms.openai import OpenAI
        
        # Create governed tool
        tool = create_governed_tool()
        if not tool:
            raise ImportError("LlamaIndex not installed")
        
        print("✓ Governed tool created")
        print()
        
        # Create agent with governed tool
        llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
        agent = ReActAgent.from_tools(
            [tool],
            llm=llm,
            verbose=True,
        )
        
        print("✓ Agent created with governed tool")
        print()
        print("Example usage:")
        print("  agent.chat('Fetch https://httpbin.org/get')")
        print()
        print("Note: This example requires OpenAI API key.")
        print("Set OPENAI_API_KEY environment variable.")
        
    except ImportError as e:
        print("LlamaIndex not installed. Install with:")
        print("  pip install llama-index llama-index-llms-openai")
        print()
        print("Example usage:")
        print("""
        from llama_index.core.tools import FunctionTool
        from faramesh.sdk.client import ExecutionGovernorClient
        
        def http_get(url: str) -> str:
            client = ExecutionGovernorClient("http://127.0.0.1:8000")
            action = client.submit_action(
                tool="http",
                operation="get",
                params={"url": url},
                context={"agent_id": "llamaindex-demo"},
            )
            # Check decision and execute...
            return result
        
        tool = FunctionTool.from_defaults(
            fn=http_get,
            name="http_get",
        )
        """)


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
