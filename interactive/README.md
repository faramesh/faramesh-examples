# Interactive AI Agent Examples

These examples demonstrate interactive AI agents governed by Faramesh, where the agent can take actions on your machine in response to natural-language instructions.

## Examples

| File | Description |
|------|-------------|
| `agent_with_human_input.py` | Full interactive agent — chat with an AI that can perform governed shell/file/HTTP actions |
| `agent_simple.py` | Simplified interactive agent using direct OpenRouter LLM calls |
| `langchain_agent.py` | Interactive LangChain agent with real LLM and dual-policy demonstration |

## Quick Start

```bash
pip install faramesh langchain openai
export OPENROUTER_API_KEY=your_key
python agent_simple.py
```

The agent will prompt for user input and submit actions through Faramesh for policy evaluation before execution.
