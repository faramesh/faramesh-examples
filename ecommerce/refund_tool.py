# examples/refund_tool.py
# Example: wrapping a “dangerous” tool
import os
from faramesh.sdk import guarded_action

os.environ["GOVERNOR_URL"] = "http://localhost:8000"
os.environ["GOVERNOR_AGENT_ID"] = "refund-bot"


@guarded_action(tool="payments", operation="refund")
def issue_refund(user_id: str, amount: float):
    print(f"[REAL TOOL] Refunding {amount} to {user_id}")
    # here you would call Stripe/Adyen/etc.
    return {"status": "ok", "refunded": amount}


if __name__ == "__main__":
    issue_refund("user_123", 50)   # likely allow
    issue_refund("user_999", 250)  # policy says require_approval → GovernorError
