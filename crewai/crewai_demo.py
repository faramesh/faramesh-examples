#!/usr/bin/env python3
"""
Demo: CrewAI-style task wrapper calling Faramesh (`faramesh_task`).
This does not depend on CrewAI; it shows how tasks could submit actions.

Run:
  FARAMESH_API_BASE=http://localhost:8000/v1 python examples/crewai_demo.py
"""


def main():
    print("Submitting via connector endpoint (no auth required)...")
    import json
    from urllib.request import Request, urlopen

    url = "http://localhost:8000/v1/connectors/noop/execute"
    body = {
        "operation": "dangerous_demo",
        "params": {"echo": "crewai"},
        "context": {"dry_run": True},
    }
    req = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        print("Response:", json.loads(resp.read().decode("utf-8")))


if __name__ == "__main__":
    main()
