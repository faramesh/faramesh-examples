# Docker Demo Agent

Example agent that continuously submits actions to demonstrate Faramesh in action.

## Quick Start

### Using Docker Compose

```bash
# Start Faramesh server and demo agent
docker compose up
```

This starts:
- **faramesh** service on port 8000
- **demo-agent** service that continuously submits actions

### Manual Run

```bash
# 1. Start Faramesh server
faramesh serve

# 2. Run demo agent (in another terminal)
python examples/docker/demo_agent.py
```

## What It Does

The demo agent:
1. Submits various actions (HTTP GET, shell commands)
2. Shows different statuses (allowed, pending_approval, denied)
3. Demonstrates the approval workflow
4. Runs continuously until stopped

## Configuration

Set environment variables:

```bash
export FARA_API_BASE=http://127.0.0.1:8000
export FARA_AGENT_ID=demo-agent
python examples/docker/demo_agent.py
```

## Expected Output

```
Submitting action: HTTP GET https://example.com
Action ID: 2755d4a8-... Status: allowed

Submitting action: Shell command 'ls -la'
Action ID: a1b2c3d4-... Status: pending_approval
Waiting for approval...
```

## Viewing Actions

Open `http://127.0.0.1:8000` in your browser to:
- See all submitted actions
- Approve/deny pending actions
- View event timelines
- Monitor real-time updates

## Policy Configuration

The demo agent respects your policy configuration. To test different scenarios:

1. **Allow all HTTP GET:**
   ```yaml
   rules:
     - match:
         tool: "http"
         op: "get"
       allow: true
   ```

2. **Require approval for shell:**
   ```yaml
   rules:
     - match:
         tool: "shell"
         op: "*"
       require_approval: true
   ```

## Stopping

Press `CTRL+C` to stop the demo agent.

## See Also

- [Docker Deployment](../docs/DOCKER.md) - Complete Docker guide
- [Quick Start](../QUICKSTART.md) - Getting started guide
- [Policy Configuration](../docs/POLICIES.md) - Policy file format
