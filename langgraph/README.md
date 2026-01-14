# LangGraph + Faramesh Integration

Simple governance for LangGraph nodes.

## Quick Start

```bash
# 1. Install dependencies
pip install langgraph faramesh

# 2. Start Faramesh server
faramesh serve

# 3. Run example (in another terminal)
python examples/langgraph/governed_graph.py
```

## What Happens

1. Graph runs and submits HTTP action to Faramesh
2. If pending approval, script exits with instructions
3. Open `http://127.0.0.1:8000` to approve
4. Re-run script to continue execution

## How It Works

Wrap tool calls in graph nodes:

```python
from faramesh.sdk.client import ExecutionGovernorClient

def http_node(state):
    client = ExecutionGovernorClient("http://127.0.0.1:8000")
    action = client.submit_action(
        tool="http",
        operation="get",
        params={"url": state["url"]},
        context={"agent_id": "langgraph-demo"},
    )
    
    if action['status'] == 'pending_approval':
        return {"error": "pending_approval"}
    
    # Execute if allowed
    # ...
```

## Policy Configuration

**Important:** To see the pending approval flow, update `policies/default.yaml`:

```yaml
rules:
  # Require approval for HTTP requests (for testing)
  - match:
      tool: "http"
      op: "get"
    require_approval: true
    description: "HTTP requests require approval"
    risk: "medium"

  # Default deny
  - match:
      tool: "*"
      op: "*"
    deny: true
```

**Note:** The default policy allows HTTP GET automatically. Update it to `require_approval: true` to test the approval workflow.

## Next Steps

- See [Policy Packs](../docs/POLICY_PACKS.md) for ready-to-use policies
- Check [Framework Integrations](../docs/INTEGRATIONS.md) for all integration options
- Read [Extending Faramesh](../docs/EXTENDING.md) for custom tool integration
