# examples/github_bot.py
import os
from faramesh.sdk.http import governed_request
from faramesh.sdk.client import GovernorError

os.environ["GOVERNOR_URL"] = "http://localhost:8000"
os.environ["GOVERNOR_AGENT_ID"] = "github-bot"

GH_REPO = "https://api.github.com/repos/octocat/Hello-World/issues"


def main():
    print("[github] creating a test issue")
    try:
        resp = governed_request(
            "POST",
            GH_REPO,
            json={"title": "Hello from Faramesh", "body": "Agent was gated by control plane"},
            headers={"User-Agent": "Faramesh-Demo"},
        )
        print("Done:", getattr(resp, "status_code", "?"))
    except GovernorError as e:
        print("Blocked:", e)


if __name__ == "__main__":
    main()
