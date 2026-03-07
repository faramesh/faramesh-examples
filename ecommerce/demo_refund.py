import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"


def submit_refund(customer: str, amount: float) -> str:
    payload = {
        "agent_id": "demo-agent",
        "tool": "payments",
        "operation": "refund",
        "params": {"customer": customer, "amount": amount},
        "risk_level": 40,
        "metadata": {"request_id": str(uuid.uuid4())},
    }
    r = requests.post(f"{BASE_URL}/v1/actions", json=payload)
    r.raise_for_status()
    data = r.json()
    print("Submitted action:", data["id"], "status:", data["status"])
    return data["id"]


def wait_for_approval(action_id: str) -> None:
    while True:
        r = requests.get(f"{BASE_URL}/v1/actions/{action_id}")
        r.raise_for_status()
        data = r.json()
        print("Current status:", data["status"], "decision:", data["decision"])
        if data["status"] in ("approved", "denied"):
            break
        time.sleep(2.0)

    if data["status"] == "denied":
        print("Refund denied, aborting.")
        return

    # simulate actually doing the refund
    print("Executing refund now...")
    time.sleep(1.0)
    result = {"refund_id": str(uuid.uuid4()), "status": "completed"}

    r = requests.post(
        f"{BASE_URL}/v1/actions/{action_id}/result",
        json={"success": True, "result": result},
    )
    r.raise_for_status()
    print("Final record:", r.json())


if __name__ == "__main__":
    action_id = submit_refund("bob", 30)
    print("Ask human to run:  faramesh allow", action_id)
    wait_for_approval(action_id)
