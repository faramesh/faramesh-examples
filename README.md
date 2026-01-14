# Faramesh Examples

Example code demonstrating how to use Faramesh with various AI frameworks and tools.

## Examples

### Framework Integrations

- **langchain/** - LangChain integration examples
- **langgraph/** - LangGraph integration examples
- **llamaindex/** - LlamaIndex integration examples
- **crewai/** - CrewAI integration examples
- **autogen/** - AutoGen integration examples
- **mcp/** - MCP (Model Context Protocol) integration examples

### Basic Examples

- **basic_submit.py** - Basic Python SDK example
- **basic_submit.js** - Basic Node.js SDK example
- **sdk_batch_submit.py** - Batch submission example
- **sdk_submit_and_wait.py** - Submit and wait example
- **sdk_policy_builder.py** - Policy builder example

### Gated Execution Examples

- **gated_execution.py** - Non-bypassable execution gate pattern (Python)
- **gated_execution.js** - Non-bypassable execution gate pattern (Node.js)

### Docker

- **docker/** - Docker deployment examples

### Action Files

- **file_apply.yaml** - Example action YAML file
- **http_action.json** - Example action JSON file

## Getting Started

1. Install Faramesh:
   ```bash
   pip install faramesh
   # or for Node.js
   npm install @faramesh/sdk
   ```

2. Start the Faramesh server:
   ```bash
   faramesh serve
   ```

3. Run an example:
   ```bash
   python examples/langchain/governed_agent.py
   ```

## Documentation

Full documentation: https://github.com/faramesh/faramesh-docs

## Repository

**Source**: https://github.com/faramesh/faramesh-examples

## Related Repositories

- **Main Repository**: https://github.com/faramesh/faramesh-core
- **Python SDK**: https://github.com/faramesh/faramesh-python-sdk
- **Node.js SDK**: https://github.com/faramesh/faramesh-node-sdk
- **Documentation**: https://github.com/faramesh/faramesh-docs

## License

Elastic License 2.0
