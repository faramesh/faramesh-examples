# LlamaIndex + Faramesh Integration

Simple governance for LlamaIndex tools.

## Quick Start

```bash
# 1. Install dependencies
pip install llama-index llama-index-llms-openai faramesh
export OPENAI_API_KEY=your-key

# 2. Start Faramesh server
faramesh serve

# 3. Run example (in another terminal)
python examples/llamaindex/governed_agent.py
```

## What Happens

1. Tool function wraps HTTP calls with Faramesh
2. If pending approval, raises PermissionError with instructions
3. Open `http://127.0.0.1:8000` to approve
4. Re-run or call tool again to continue

## How It Works

Wrap tool functions with Faramesh:

```python
from faramesh.sdk.client import ExecutionGovernorClient
from llama_index.core.tools import FunctionTool

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

tool = FunctionTool.from_defaults(fn=http_get, name="http_get")
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
