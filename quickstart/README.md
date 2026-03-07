# Quickstart Examples

Get up and running with Faramesh in under 2 minutes.

## Installation (without pip / latest source)

The PyPI package may lag behind. Install directly from source:

```bash
# Clone faramesh-core next to this repo
git clone https://github.com/faramesh/faramesh-core.git

# Option A: install editable (recommended)
pip install -e ./faramesh-core

# Option B: just add to PYTHONPATH — no install needed
export PYTHONPATH=$(pwd)/faramesh-core/src

# Start the server
faramesh serve          # if installed via option A
# OR
python -m faramesh.server.main  # always works
```

Then clone examples and run:

```bash
git clone https://github.com/faramesh/faramesh-examples.git
cd faramesh-examples
python quickstart/quick_demo.py
```

## Examples

| File | Description |
|------|-------------|
| `quickstart_llm.py` | 2-minute demo with a real LLM (OpenRouter, free model, no cost) |
| `quick_demo.py` | Quick demo of core Faramesh capabilities |

## Run with a real LLM

```bash
export OPENROUTER_API_KEY=sk-or-v1-...   # free key at https://openrouter.ai
python quickstart/quickstart_llm.py
```
