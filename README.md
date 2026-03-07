# Faramesh Examples

Runnable examples for governing AI agent tool calls with [Faramesh](https://github.com/faramesh/faramesh-core).

## Installation & Quickstart

> **Note:** The PyPI package may lag behind. Install directly from source for the latest version.

### Option A — Install from source (recommended)

```bash
# Clone core and install in editable mode
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core

# with uv (fastest)
uv pip install -e ".[dev]"

# or with pip
pip install -e ".[dev]"

# Start the server
faramesh serve
# → http://localhost:8000
```

### Option B — Install from GitHub with pip

```bash
pip install "git+https://github.com/faramesh/faramesh-core.git"
faramesh serve
```

### Option C — Run the server directly without installing

```bash
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core
pip install fastapi uvicorn pyyaml pydantic pydantic-settings requests
python -m uvicorn faramesh.server.main:app --host 0.0.0.0 --port 8000
```

Then clone this examples repo and run any example:

```bash
git clone https://github.com/faramesh/faramesh-examples.git
cd faramesh-examples

# Point examples at the local core source if not installed
export PYTHONPATH=/path/to/faramesh-core/src

python quickstart/quick_demo.py
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
