# Faramesh Examples

Runnable examples for governing AI agent tool calls with [Faramesh](https://github.com/faramesh/faramesh-core).

## Installation

> **The PyPI package is not updated yet — install from the cloned source instead.**

### With uv (recommended)

```bash
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core
uv sync
uv run faramesh serve
```

### With pip

```bash
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core
python3 -m pip install -e .
faramesh serve
```

### In a virtual environment (no global installs)

```bash
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
faramesh serve
```

Then run any example:

```bash
git clone https://github.com/faramesh/faramesh-examples.git
cd faramesh-examples
python3 quickstart/quick_demo.py
```

---

## Framework examples

| Directory | Framework | Run |
|---|---|---|
| [langchain/](langchain/) | LangChain | `python langchain/governed_agent.py` |
| [crewai/](crewai/) | CrewAI | `python crewai/governed_agent.py` |
| [autogen/](autogen/) | AutoGen | `python autogen/governed_agent.py` |
| [mcp/](mcp/) | MCP | `python mcp/governed_agent.py` |
| [langgraph/](langgraph/) | LangGraph | `python langgraph/governed_agent.py` |
| [llamaindex/](llamaindex/) | LlamaIndex | `python llamaindex/governed_agent.py` |

Every example wraps tools with one line:

```python
from faramesh.integrations import govern

tool = govern(YourTool(), agent_id="my-agent")
```

---

## Basic SDK examples

| File | What it shows |
|---|---|
| [basic_submit.py](standalone/basic_submit.py) | Submit a single action (Python) |
| [basic_submit.js](standalone/basic_submit.js) | Submit a single action (Node.js) |
| [gated_execution.py](standalone/gated_execution.py) | Non-bypassable execution gate (Python) |
| [gated_execution.js](standalone/gated_execution.js) | Non-bypassable execution gate (Node.js) |
| [sdk_submit_and_wait.py](standalone/sdk_submit_and_wait.py) | Submit action and wait for approval |
| [sdk_batch_submit.py](standalone/sdk_batch_submit.py) | Submit multiple actions |
| [sdk_policy_builder.py](standalone/sdk_policy_builder.py) | Build policies in Python |

---

## Docker

```bash
cd docker
docker compose up
```

See [docker/README.md](docker/README.md).

---

## Docs

Full documentation: [faramesh-docs](https://github.com/faramesh/faramesh-docs) · [faramesh.dev](https://faramesh.dev)
