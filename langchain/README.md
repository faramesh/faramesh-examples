# LangChain Integration Example

This example demonstrates how to use Faramesh to govern LangChain tool calls in a real agent workflow.

## Prerequisites

```bash
pip install faramesh langchain requests
```

Or if you prefer minimal dependencies (this example works without LangChain):

```bash
pip install faramesh requests
```

## Quick Start

### 1. Start Faramesh Server

In one terminal:

```bash
faramesh serve
```

The server will start on `http://127.0.0.1:8000`

### 2. Run the Example

In another terminal:

```bash
python examples/langchain/governed_agent.py
```

## What You'll See

The demo will:

1. **Submit HTTP GET request** → Usually allowed immediately
2. **Submit safe shell command** → May require approval depending on policy
3. **Submit list command** → May require approval depending on policy

For each action, you'll see:
- ✓ **Allowed** - Action executed immediately
- ✗ **Denied** - Action blocked by policy
- ⏳ **Pending** - Waiting for approval (if max_wait_time exceeded, script exits)

## Handling Pending Approval

If an action requires approval:

1. **Open the UI**: `http://127.0.0.1:8000`
2. **Find the pending action** in the table (look for `pending_approval` status)
3. **Click the row** to open the details drawer
4. **Click "Approve"** or "Deny" button
5. **Re-run the script** to see the result

The `GovernedTool` wrapper will:
- Poll for approval status every 2 seconds
- Wait up to 30 seconds (configurable)
- Execute the tool once approved
- Raise `PermissionError` if denied

## How It Works

The `GovernedTool` wrapper:

1. **Intercepts** tool calls before execution
2. **Submits** them to Faramesh for policy evaluation
3. **Waits** for approval if `require_approval: true`
4. **Executes** the tool only if `allowed` or `approved`
5. **Reports** results back to Faramesh
6. **Raises** `PermissionError` if denied

## Integration with Full LangChain Agents

For a complete agent setup:

```python
from langchain.agents import initialize_agent, AgentType
from langchain.tools import ShellTool
from langchain.llms import OpenAI
from faramesh.sdk.client import ExecutionGovernorClient
from faramesh.integrations.langchain.governed_tool import GovernedTool

# Initialize Faramesh
client = ExecutionGovernorClient("http://127.0.0.1:8000")

# Create and wrap tools
shell_tool = ShellTool()
governed_shell = GovernedTool(
    tool=shell_tool,
    client=client,
    agent_id="my-agent",
)

# Create agent with governed tools
llm = OpenAI(temperature=0)
agent = initialize_agent(
    tools=[governed_shell],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# Use the agent
agent.run("List files in /tmp")
```

## Policy Configuration

To control what requires approval, edit `policies/default.yaml`:

```yaml
rules:
  # Allow HTTP GET
  - match:
      tool: "http"
      op: "get"
    allow: true
    risk: "low"

  # Require approval for shell commands
  - match:
      tool: "shell"
      op: "*"
    require_approval: true
    description: "Shell commands require approval"
    risk: "medium"

  # Default deny
  - match:
      tool: "*"
      op: "*"
    deny: true
```

## Troubleshooting

**"Connection refused" error:**
- Make sure `faramesh serve` is running
- Check the API base URL matches your server

**Actions always denied:**
- Check your policy file (`policies/default.yaml`)
- Use `faramesh explain <action-id>` to see why

**Actions stuck in pending:**
- Open the UI and approve/deny manually
- Increase `max_wait_time` in `GovernedTool` if needed

## Next Steps

- See [Extending Faramesh](../docs/EXTENDING.md) for custom tool integration
- Check [Policy Packs](../docs/POLICY_PACKS.md) for ready-to-use policies
- Read [Framework Integrations](../docs/INTEGRATIONS.md) for all integration options
