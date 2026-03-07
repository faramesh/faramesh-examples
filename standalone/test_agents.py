#!/usr/bin/env python3
"""
Smoke test Faramesh onboarding and agent integrations.
- Posts actions for agents from Autogen, LangChain, CrewAI (if installed) or falls back to direct HTTP.
- Requires backend running and a valid Bearer token in FARAMESH_TOKEN.
"""
import os
import json
import time
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_BASE = os.environ.get("FARAMESH_API_BASE", "http://localhost:8000/v1")
TOKEN = os.environ.get("FARAMESH_TOKEN", None)
TENANT = os.environ.get("FARAMESH_TENANT", None)
DEMO = os.environ.get("FARAMESH_DEMO", "0") == "1"

HEADERS = {
    "Content-Type": "application/json",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"
elif DEMO:
    HEADERS["X-User-ID"] = "demo-user"
if TENANT:
    HEADERS["X-Tenant-ID"] = TENANT


def http_post(path: str, body: dict):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urlopen(req) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as e:
        try:
            err = e.read().decode("utf-8")
            print(f"HTTP {e.code}: {err}")
        except Exception:
            print(f"HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except URLError as e:
        print(f"URL error: {e.reason}")
        sys.exit(1)


def submit_action(agent_id: str, tool: str, operation: str, params: dict):
    body = {
        "agent_id": agent_id,
        "tool": tool,
        "operation": operation,
        "params": params,
        "context": {},
    }
    return http_post("/actions", body)


def test_noop_connector():
    body = {
        "operation": "dangerous_demo",
        "params": {"echo": "hello"},
        "context": {"dry_run": True},
    }
    return http_post("/connectors/noop/execute", body)


def main():
    print(
        "Testing onboarding basics: API key/agent (requires frontend or separate setup)."
    )

    print("Testing noop connector (dry-run)...")
    res = test_noop_connector()
    print("noop result:", res)

    print("Submitting actions for sample agents...")
    agents = [
        (
            "autogen-agent",
            "http",
            "post",
            {"url": "https://example.com", "body": {"hello": "world"}},
        ),
        (
            "langchain-agent",
            "email",
            "send",
            {"to": "test@example.com", "subject": "Test", "body": "Hi"},
        ),
        (
            "crewai-agent",
            "filesystem",
            "write",
            {"path": "/tmp/demo.txt", "content": "Hello"},
        ),
    ]
    for agent_id, tool, op, params in agents:
        try:
            resp = submit_action(agent_id, tool, op, params)
            print(
                f"Action for {agent_id}: status={resp.get('status')} id={resp.get('id')}"
            )
        except SystemExit:
            raise
        except Exception as e:
            print(f"Failed to submit action for {agent_id}: {e}")
        time.sleep(0.5)

    print("Done.")


if __name__ == "__main__":
    main()
