"""
Demo Agent Task: Create 10 files in a folder named "demo-folder"
Only executes after you approve the pending action in the UI.

Usage:
    FARAMESH_DEMO=1 FARA_API_BASE="http://127.0.0.1:8000" \
    FARA_AUTH_TOKEN="demo-token" \
    /Users/xquark_home/Faramesh-Nexus/.venv/bin/python demo_agents/05_batch_create_demo_files.py

This script submits an action (tool=filesystem, op=batch_create) to Faramesh,
waits until you approve it from the dashboard, then creates 10 files locally.
"""

import os
import sys
from pathlib import Path
from typing import List

from faramesh import submit_action, get_action, report_result

AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "demo-files-agent")
FOLDER_NAME = "demo-folder"
FILE_COUNT = 10
FILE_PREFIX = "demo_file_"
FILE_EXT = ".txt"


def create_files(target_dir: Path, count: int, prefix: str, ext: str) -> List[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    created: List[str] = []
    for i in range(count):
        name = f"{prefix}{i+1}{ext}"
        path = target_dir / name
        path.write_text(f"Sample file #{i+1}\n", encoding="utf-8")
        created.append(str(path))
    return created


def main() -> None:
    workspace_root = Path.cwd()
    target_dir = workspace_root / FOLDER_NAME

    print("📨 Submitting batch_create action (requires approval)...")
    initial = submit_action(
        agent_id=AGENT_ID,
        tool="filesystem",
        operation="batch_create",
        params={
            "folder": str(target_dir),
            "count": FILE_COUNT,
            "prefix": FILE_PREFIX,
            "extension": FILE_EXT,
        },
        context={
            "purpose": "demo: create 10 files in demo-folder",
        },
    )

    init_status = initial.get("status")
    action_id = initial.get("id")
    decision = initial.get("decision")
    reason = initial.get("reason")
    print(f"📥 Initial status: {init_status} | decision: {decision}")

    if init_status == "denied":
        print(f"❌ Denied by policy: {reason or 'Policy rule matched deny'}")
        sys.exit(1)

    if init_status == "allowed":
        print(f"✅ Allowed by policy. Creating {FILE_COUNT} files in {target_dir}...")
        created = create_files(target_dir, FILE_COUNT, FILE_PREFIX, FILE_EXT)
        try:
            if action_id:
                report_result(action_id, success=True, result={"created": created})
        except Exception as e:
            print(f"⚠️ Report result failed: {e}")
        print("🎉 Done. Files created:")
        for f in created:
            print(f" - {f}")
        return

    if init_status != "pending_approval":
        print(f"❌ Unexpected initial status: {init_status}. Aborting.")
        sys.exit(1)

    print("⏳ Waiting for approval...")
    import time

    start_time = time.time()
    timeout = 600.0
    poll_interval = 1.0
    final = initial
    while time.time() - start_time < timeout:
        time.sleep(poll_interval)
        try:
            final = get_action(action_id)
            fstatus = final.get("status")
            if fstatus in ("approved", "denied", "allowed"):
                break
        except Exception:
            continue

    fstatus = final.get("status")
    fdecision = final.get("decision")
    freason = final.get("reason")
    print(f"📥 Final status: {fstatus} | decision: {fdecision}")

    if fstatus == "denied":
        # Since we started in pending_approval, a terminal denied means human rejection
        print(f"❌ Denied by human: {freason or 'Approval rejected'}")
        sys.exit(1)

    if fstatus == "approved":
        print(f"✅ Approved by human. Creating {FILE_COUNT} files in {target_dir}...")
    elif fstatus == "allowed":
        # Handle edge-case if server transitions to allowed
        print(f"✅ Allowed. Creating {FILE_COUNT} files in {target_dir}...")
    else:
        print(f"❌ Unexpected terminal status: {fstatus}. Aborting.")
        sys.exit(1)

    created = create_files(target_dir, FILE_COUNT, FILE_PREFIX, FILE_EXT)

    try:
        if action_id:
            report_result(action_id, success=True, result={"created": created})
    except Exception as e:
        print(f"⚠️ Report result failed: {e}")

    print("🎉 Done. Files created:")
    for f in created:
        print(f" - {f}")


if __name__ == "__main__":
    main()
