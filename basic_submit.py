"""Basic example: submit an action using the Faramesh Python SDK."""

from faramesh import configure, submit_action


def main() -> None:
    # Point at local server (started with `faramesh serve`)
    configure(base_url="http://127.0.0.1:8000")

    action = submit_action(
        "example-agent",
        "http",
        "get",
        {"url": "https://example.com"},
    )

    print("Action submitted!")
    print(f"  id      = {action['id']}")
    print(f"  status  = {action['status']}")
    print(f"  risk    = {action.get('risk_level')}")
    print(f"  decision= {action.get('decision')}")


if __name__ == "__main__":
    main()

