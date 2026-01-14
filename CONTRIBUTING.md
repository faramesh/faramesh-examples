# Contributing to Faramesh

Thank you for your interest in contributing to Faramesh! This guide will help you get started.

## Project Layout

```
faramesh-examples/
├── langchain/            # LangChain integration examples
├── langgraph/            # LangGraph integration examples
├── llamaindex/           # LlamaIndex integration examples
├── crewai/               # CrewAI integration examples
├── autogen/              # AutoGen integration examples
├── mcp/                  # MCP integration examples
├── docker/               # Docker agent demo
└── ...                   # Other examples
```

---

## Development Setup

### Prerequisites

- Python 3.9+ or Node.js 16+ (depending on example)
- pip or npm
- Git
- Faramesh server running (or access to one)

### Installation

```bash
# Clone repository
git clone https://github.com/faramesh/faramesh-examples.git
cd faramesh-examples

# Install Faramesh (Python examples)
pip install faramesh

# Or install Node.js SDK (Node.js examples)
npm install @faramesh/sdk
```

### Running Examples

```bash
# Python example
python examples/langchain/governed_agent.py

# Node.js example
node examples/basic_submit.js
```

---

## Example Standards

### Code Quality

- **Clarity**: Examples should be clear and easy to understand
- **Completeness**: Include all necessary imports and setup
- **Comments**: Add comments explaining key concepts
- **Minimal**: Keep examples focused and minimal

### Documentation

- **README**: Each example directory should have a README.md
- **Setup**: Document prerequisites and setup steps
- **Usage**: Explain how to run the example
- **Expected Output**: Describe what users should see

### Testing

- **Working**: All examples should be tested and working
- **Up-to-date**: Examples should work with latest Faramesh version
- **Framework Versions**: Document required framework versions

### CLI Commands

- **Command Name**: Use `faramesh` (or `python3 -m faramesh.cli`)
- **Supported Commands**: `list`, `get`, `approve`, `deny`, `serve`, `migrate`, `policy-*`, etc.
- **Error Handling**: Return appropriate exit codes (0=success, 1=error, 130=interrupted)

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write code following coding standards
- Add tests for new features
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
python3 -m pytest

# Run linting
ruff check src/

# Test CLI commands
python3 -m faramesh.cli --help
python3 -m faramesh.cli list

# Test server
python3 -m faramesh.cli serve
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: fix bug in policy evaluation"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

---

## Running the Server

### Development Server

```bash
# Basic server
python3 -m faramesh.cli serve

# With hot reload (for policy changes)
python3 -m faramesh.cli serve --hot-reload

# With code auto-reload (for Python changes)
python3 -m faramesh.cli serve --reload
```

### Database Migrations

```bash
# Run migrations
python3 -m faramesh.cli migrate
```

### Policy Validation

```bash
# Validate policy file
python3 -m faramesh.cli policy-validate policies/default.yaml
```

---

## UI Development

### Setup

```bash
cd web
npm install
```

### Development Mode

```bash
# Start Vite dev server (with hot reload)
npm run dev
```

Access UI at `http://localhost:5173` (or Vite's default port).

### Build

```bash
# Build for production
npm run build
```

Built files go to `src/faramesh/web/` and are served by the FastAPI server.

---

## Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] **Tests pass**: `python3 -m pytest` passes
- [ ] **Linting passes**: `ruff check src/` passes
- [ ] **Documentation updated**: README, docs, or examples updated as needed
- [ ] **No new unused dependencies**: Check `pyproject.toml`
- [ ] **Imports use `faramesh.*`**: No relative imports in public APIs
- [ ] **Error messages consistent**: Use proper HTTP status codes and JSON error format
- [ ] **Type hints added**: For new functions and classes
- [ ] **Docstrings added**: For public APIs
- [ ] **Breaking changes documented**: If any, update CHANGELOG.md

---

## Testing Guidelines

### Unit Tests

Test individual functions and classes:

```python
def test_policy_evaluation():
    engine = PolicyEngine("policies/default.yaml")
    decision, reason, risk = engine.evaluate("shell", "run", {"cmd": "echo hello"})
    assert decision == Decision.REQUIRE_APPROVAL
```

### Integration Tests

Test API endpoints and workflows:

```python
def test_action_submission(client):
    response = client.post("/v1/actions", json={
        "agent_id": "test",
        "tool": "http",
        "operation": "get",
        "params": {"url": "https://example.com"}
    })
    assert response.status_code == 200
    assert response.json()["status"] in ("allowed", "pending_approval", "denied")
```

### CLI Tests

Test CLI commands:

```python
def test_list_command(cli_runner):
    result = cli_runner.invoke(cli.list, [])
    assert result.exit_code == 0
```

---

## Documentation

### When to Update Documentation

- **New features**: Update relevant docs
- **API changes**: Update API.md
- **CLI changes**: Update CLI.md
- **Breaking changes**: Update CHANGELOG.md
- **Examples**: Update example READMEs

### Documentation Structure

- **README.md**: Primary landing page and overview
- **QUICKSTART.md**: Getting started guide
- **docs/**: Detailed topic-specific guides
- **examples/*/README.md**: Example-specific instructions

---

## Code Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Review**: Maintainers review code
3. **Feedback**: Address any feedback
4. **Merge**: Once approved, maintainers merge

**Review Criteria:**
- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility
- Performance considerations

---

## Getting Help

- **GitHub Issues**: [Create an issue](https://github.com/faramesh/faramesh-examples/issues/new)
- **GitHub Discussions**: [Ask questions](https://github.com/faramesh/faramesh-examples/discussions)
- **Documentation**: See [docs/](docs/) for detailed guides

---

## See Also

- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines
- [Security Policy](SECURITY.md) - Security reporting
- [Architecture](ARCHITECTURE.md) - System architecture
- [Roadmap](ROADMAP.md) - Product roadmap
