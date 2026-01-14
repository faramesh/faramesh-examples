# AutoGen + Faramesh Integration

One-line governance for AutoGen function calling.

## Quick Start

```bash
# Install dependencies
pip install pyautogen faramesh

# Start Faramesh server
faramesh serve

# Run example
python examples/autogen/governed_agent.py
```

## One-Line Integration

```python
import autogen
from faramesh.integrations import govern_autogen_function

def my_function(url: str) -> str:
    """Fetch a URL."""
    import requests
    return requests.get(url).text

# One line to add governance!
governed_func = govern_autogen_function(
    my_function,
    agent_id="assistant",
    tool_name="http_get"
)

# Use in AutoGen agent
agent = autogen.AssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    function_map={"http_get": governed_func}  # Governed function
)

# Create user proxy with function calling
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    function_map={"http_get": governed_func}
)

# Chat with agent
user_proxy.initiate_chat(
    agent,
    message="Fetch https://example.com"
)
```

## How It Works

1. **Wrap any function** with `govern_autogen_function()`
2. **Submit to Faramesh** before execution
3. **Wait for approval** if required
4. **Execute only if allowed**
5. **Report results** back to Faramesh

## Policy Configuration

Create `policies/default.yaml` to control what requires approval:

```yaml
rules:
  # Require approval for HTTP requests
  - match:
      tool: "http_get"
      op: "call"
    require_approval: true
    description: "HTTP requests require approval"
    risk: "medium"

  # Block shell commands
  - match:
      tool: "shell_command"
      op: "call"
    deny: true
    description: "Shell commands are blocked"
    risk: "high"

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

# Auto-detects function
governed_func = govern(my_function, agent_id="my-agent", framework="autogen")
```

## Next Steps

- See [Policy Packs](../docs/POLICY_PACKS.md) for ready-to-use policies
- Check [Extending Faramesh](../docs/EXTENDING.md) for custom tools
- Read [Framework Integrations](../docs/INTEGRATIONS.md) for all integration options
- Read [AutoGen docs](https://microsoft.github.io/autogen/) for full framework guide
