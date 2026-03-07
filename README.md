# Faramesh Examples

Runnable examples for governing AI agent tool calls with [Faramesh](https://github.com/faramesh/faramesh-core).

## Installation

> **The PyPI package is not yet updated. Install from source.**

### Fastest — clone and run (no `pip install` needed)

```bash
# 1. Get the core server
git clone https://github.com/faramesh/faramesh-core.git

# 2. Get the examples
git clone https://github.com/faramesh/faramesh-examples.git

# 3. Point examples at the source (no install step)
export PYTHONPATH=$(pwd)/faramesh-core/src

# 4. Start the server
cd faramesh-core
python -m uvicorn faramesh.server.main:app --host 0.0.0.0 --port 8000

# 5. In a second terminal, run any example
cd ../faramesh-examples
python quickstart/quick_demo.py
```

### With uv (recommended if you have uv)

```bash
git clone https://github.com/faramesh/faramesh-core.git
cd faramesh-core
uv pip install -e .
faramesh serve
```

### With pip editable install

```bash
git clone https://github.com/faramesh/faramesh-core.git
pip install -e ./faramesh-core
faramesh serve
```

All three approaches work. The examples automatically detect `faramesh-core/src` as a sibling directory if it is not installed — so the `PYTHONPATH` export in option 1 is all you need.

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
