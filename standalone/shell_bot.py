# examples/shell/shell_bot.py
import os
from faramesh.sdk.decorators import governed_subprocess, GovernorError, PendingAction

os.environ["GOVERNOR_URL"] = "http://localhost:8000"
os.environ["GOVERNOR_AGENT_ID"] = "shell-bot"


def handle(name: str, res):
    if isinstance(res, PendingAction):
        print(f"[{name}] pending approval →", res.id)
        return
    print(f"[{name}] exit:", res.returncode)


def main():
    print("[shell] List /tmp")
    try:
        res = governed_subprocess("sleep 10 && echo 1")
        handle("ls", res)
    except GovernorError as e:
        print("blocked:", e)

    print("[shell] Now try rm -rf — should be stopped")
    try:
        res = governed_subprocess("rm -rf /tmp")
        handle("rm", res)
    except GovernorError as e:
        print("blocked (expected):", e)


if __name__ == "__main__":
    main()
