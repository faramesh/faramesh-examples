# CrewAI + Faramesh Integration

One-line governance for CrewAI agents.

## Quick Start

```bash
# Install dependencies
pip install crewai crewai-tools faramesh

# Start Faramesh server
faramesh serve

# Run example
python examples/crewai/governed_agent.py
```

## One-Line Integration

```python
from crewai_tools import FileReadTool
from faramesh.integrations import govern_crewai_tool

# One line to add governance!
tool = govern_crewai_tool(FileReadTool(), agent_id="researcher")

# Use in CrewAI agent
from crewai import Agent, Task, Crew

agent = Agent(
    role='Researcher',
    goal='Research and analyze information',
    tools=[tool],  # Governed tool
    verbose=True
)

task = Task(
    description='Read and analyze file.txt',
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

## How It Works

1. **Wrap any CrewAI tool** with `govern_crewai_tool()`
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
      tool: "FileReadTool"
      op: "*"
    require_approval: true
    description: "File operations require approval"
    risk: "medium"

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

# Auto-detects CrewAI
tool = govern(FileReadTool(), agent_id="my-agent")
```

## Next Steps

- See [Policy Packs](../docs/POLICY_PACKS.md) for ready-to-use policies
- Check [Extending Faramesh](../docs/EXTENDING.md) for custom tools
- Read [Framework Integrations](../docs/INTEGRATIONS.md) for all integration options
- Read [CrewAI docs](https://docs.crewai.com/) for full framework guide
