"""
MCP (Model Context Protocol) + Faramesh Integration Example

One-line governance for MCP tools.

Run: python examples/mcp/governed_tool.py
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.integrations import govern_mcp_tool

# Example MCP tools
def search_tool(query: str) -> str:
    """Search tool for MCP."""
    return f"Search results for: {query}"


def read_file_tool(path: str) -> str:
    """Read file tool for MCP."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 60)
    print("MCP + Faramesh Integration")
    print("=" * 60)
    print()
    
    # One-line governance!
    governed_search = govern_mcp_tool(
        search_tool,
        agent_id="mcp-demo"
    )
    
    governed_read = govern_mcp_tool(
        read_file_tool,
        agent_id="mcp-demo"
    )
    
    print("✓ Tools wrapped with Faramesh governance")
    print()
    print("Usage:")
    print("""
    from faramesh.integrations import govern_mcp_tool
    
    def my_mcp_tool(query: str) -> str:
        # Your tool logic
        return f"Result: {query}"
    
    # One line to add governance!
    tool = govern_mcp_tool(my_mcp_tool, agent_id="my-agent")
    
    # Use in MCP server
    result = tool("search query")
    """)
    
    print()
    print("Example with MCP server:")
    print("""
    from mcp import Server
    from faramesh.integrations import govern_mcp_tool
    
    def my_tool(query: str) -> str:
        return f"Result: {query}"
    
    # Wrap with governance
    governed_tool = govern_mcp_tool(my_tool, agent_id="mcp-agent")
    
    # Register with MCP server
    server = Server("my-server")
    server.register_tool("my_tool", governed_tool)
    """)


if __name__ == "__main__":
    main()
