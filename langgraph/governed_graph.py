"""
LangGraph + Faramesh Integration Example

Simple graph with 2 nodes that submit actions to Faramesh before execution.

Usage:
    pip install faramesh langgraph
    faramesh serve
    python examples/langgraph/governed_graph.py

If action is pending approval:
    1. Open http://127.0.0.1:8000
    2. Approve the pending action
    3. Re-run this script
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.sdk.client import ExecutionGovernorClient


def http_node(state: dict) -> dict:
    """Node 1: HTTP GET request."""
    client = ExecutionGovernorClient("http://127.0.0.1:8000")
    
    url = state.get("url", "https://httpbin.org/get")
    
    # Submit to Faramesh
    action = client.submit_action(
        tool="http",
        operation="get",
        params={"url": url},
        context={"agent_id": "langgraph-demo", "node": "http_node"},
    )
    
    action_id = action['id']
    status = action['status']
    decision = action.get('decision', '')
    
    print(f"[HTTP Node] Action ID: {action_id[:8]}...")
    print(f"[HTTP Node] Status: {status}, Decision: {decision}")
    
    # Check decision
    if decision == 'deny' or status == 'denied':
        reason = action.get('reason', 'Action denied by policy')
        print(f"[HTTP Node] ✗ Denied: {reason}")
        return {"error": reason, "http_result": None}
    
    if status == 'pending_approval':
        print(f"[HTTP Node] ⏳ Pending approval. Action ID: {action_id}")
        print(f"[HTTP Node] → Open http://127.0.0.1:8000 to approve")
        print(f"[HTTP Node] → After approving, re-run this script to continue")
        return {"error": "pending_approval", "action_id": action_id, "http_result": None}
    
    # Execute if allowed
    if status not in ('allowed', 'approved'):
        print(f"[HTTP Node] ✗ Not approved. Status: {status}")
        return {"error": f"Status: {status}", "http_result": None}
    
    # Execute HTTP request
    try:
        import requests
        response = requests.get(url, timeout=5)
        result = f"Status {response.status_code}: {response.text[:100]}"
        
        # Report result
        client.report_result(action_id, success=True, result=result)
        
        print(f"[HTTP Node] ✓ Executed: {result[:50]}...")
        return {"http_result": result, "error": None}
    except Exception as e:
        client.report_result(action_id, success=False, error=str(e))
        print(f"[HTTP Node] ✗ Error: {e}")
        return {"error": str(e), "http_result": None}


def print_node(state: dict) -> dict:
    """Node 2: Print result."""
    http_result = state.get("http_result")
    error = state.get("error")
    
    if error == "pending_approval":
        print(f"[Print Node] ⏸ Skipping - action pending approval")
        print(f"[Print Node] → Approve in UI, then re-run script")
        return state
    
    if error:
        print(f"[Print Node] ✗ Error: {error}")
        return state
    
    if http_result:
        print(f"[Print Node] ✓ Result: {http_result[:100]}...")
    else:
        print(f"[Print Node] ⚠ No result to print")
    
    return state


def main():
    """Run governed graph."""
    print("=" * 60)
    print("LangGraph + Faramesh Integration")
    print("=" * 60)
    print()
    
    try:
        from langgraph.graph import StateGraph, END
        
        # Create graph
        graph = StateGraph(dict)
        
        # Add nodes
        graph.add_node("http", http_node)
        graph.add_node("print", print_node)
        
        # Set entry point
        graph.set_entry_point("http")
        
        # Add edges
        graph.add_edge("http", "print")
        graph.add_edge("print", END)
        
        # Compile
        app = graph.compile()
        
        print("✓ Graph created")
        print()
        print("Running graph...")
        print("-" * 60)
        
        # Run graph
        initial_state = {"url": "https://httpbin.org/get"}
        result = app.invoke(initial_state)
        
        print("-" * 60)
        print()
        print("Graph execution complete!")
        
        if result.get("error") == "pending_approval":
            print()
            print("Next steps:")
            print("  1. Open http://127.0.0.1:8000")
            print("  2. Approve the pending action")
            print("  3. Re-run this script")
        
    except ImportError:
        print("LangGraph not installed. Install with:")
        print("  pip install langgraph")
        print()
        print("Example usage:")
        print("""
        from langgraph.graph import StateGraph, END
        from faramesh.sdk.client import ExecutionGovernorClient
        
        def http_node(state):
            client = ExecutionGovernorClient("http://127.0.0.1:8000")
            action = client.submit_action(
                tool="http",
                operation="get",
                params={"url": state["url"]},
                context={"agent_id": "langgraph-demo"},
            )
            # Check decision and execute...
            return state
        
        graph = StateGraph(dict)
        graph.add_node("http", http_node)
        graph.set_entry_point("http")
        graph.add_edge("http", END)
        app = graph.compile()
        result = app.invoke({"url": "https://example.com"})
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
