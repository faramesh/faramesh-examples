# MCP (Model Context Protocol) + Faramesh Integration

One-line governance for MCP tools.

## Quick Start

```bash
# Install dependencies
pip install mcp faramesh

# Start Faramesh server
faramesh serve

# Run example
python examples/mcp/governed_tool.py
```

## One-Line Integration

```python
from faramesh.integrations import govern_mcp_tool

def my_mcp_tool(query: str) -> str:
    """Your MCP tool."""
    # Your tool logic
    return f"Result: {query}"

# One line to add governance!
tool = govern_mcp_tool(my_mcp_tool, agent_id="my-agent")

# Use in MCP server
from mcp import Server

server = Server("my-server")
server.register_tool("my_tool", tool)  # Governed tool
```

## How It Works

1. **Wrap any MCP tool** with `govern_mcp_tool()`
2. **Submit to Faramesh** before execution
3. **Wait for approval** if required
4. **Execute only if allowed**
5. **Report results** back to Faramesh

## Policy Configuration

Create `policies/default.yaml` to control what requires approval:

```yaml
rules:
  # Require approval for file operations
  - match:
      tool: "read_file_tool"
      op: "call"
    require_approval: true
    description: "File operations require approval"
    risk: "medium"

  # Allow search operations
  - match:
      tool: "search_tool"
      op: "call"
    allow: true
    description: "Search is safe"
    risk: "low"

  # Default deny
  - match:
      tool: "*"
      op: "*"
    deny: true
```

## Universal One-Liner

Auto-detect framework:

```python
from faramesh.integrations import govern

# Auto-detects MCP
tool = govern(my_tool, agent_id="my-agent")
```

## Next Steps

- See [Policy Packs](../docs/POLICY_PACKS.md) for ready-to-use policies
- Check [Extending Faramesh](../docs/EXTENDING.md) for custom tools
- Read [Framework Integrations](../docs/INTEGRATIONS.md) for all integration options
- Read [MCP docs](https://modelcontextprotocol.io/) for full protocol guide
