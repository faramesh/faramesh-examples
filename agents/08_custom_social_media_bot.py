#!/usr/bin/env python3
"""
Custom Social Media Bot
Risk Level: MEDIUM
Posts to social media with approval requirements
"""
import sys, os as _os
from pathlib import Path as _Path

# --- faramesh source resolution ---
# Priority: 1) installed package  2) PYTHONPATH env  3) sibling faramesh-core/src
def _add_faramesh_src():
    try:
        import faramesh  # already installed or on PYTHONPATH
        return
    except ImportError:
        pass
    # Look for a sibling faramesh-core clone
    _here = _Path(__file__).resolve().parent
    for _candidate in [
        _here.parent / "faramesh-core" / "src",
        _here.parent.parent / "faramesh-core" / "src",
        _Path.home() / "faramesh-core" / "src",
    ]:
        if (_candidate / "faramesh").is_dir():
            sys.path.insert(0, str(_candidate))
            return
    print("\n[faramesh] Could not find faramesh. Run:")
    print("  git clone https://github.com/faramesh/faramesh-core.git")
    print("  pip install -e ./faramesh-core  OR  export PYTHONPATH=./faramesh-core/src")
    sys.exit(1)

_add_faramesh_src()
# --- end faramesh source resolution ---

import os
import sys
import time
import random
from datetime import datetime


from faramesh import configure, submit_action

configure(
    base_url="http://localhost:8000", agent_id="custom-social-media-bot", timeout=10.0
)


def run_agent():
    """Run the Custom Social Media Bot."""
    print("📱 Custom Social Media Bot Starting...")
    print(f"   Agent ID: custom-social-media-bot")
    print(f"   Risk Level: MEDIUM")
    print(f"   Framework: Custom")
    print()

    actions = [
        {
            "tool": "twitter",
            "operation": "post",
            "params": {
                "text": "Check out our latest AI governance features! 🚀",
                "media": [],
            },
        },
        {
            "tool": "linkedin",
            "operation": "post",
            "params": {
                "text": "We're hiring! Join our team to build the future of AI governance.",
                "visibility": "public",
            },
        },
        {
            "tool": "slack",
            "operation": "post_message",
            "params": {
                "channel": "#announcements",
                "text": "New release v2.0 is live!",
            },
        },
        {
            "tool": "twitter",
            "operation": "reply",
            "params": {
                "tweet_id": "123456789",
                "text": "Thanks for the feedback! We're working on it.",
            },
        },
        {
            "tool": "facebook",
            "operation": "post",
            "params": {
                "text": "Join us for our webinar on AI safety next week!",
                "link": "https://example.com/webinar",
            },
        },
    ]

    iteration = 1
    while True:
        try:
            action = random.choice(actions)

            print(f"💬 Iteration {iteration}: {action['tool']}.{action['operation']}")

            result = submit_action(
                agent_id="custom-social-media-bot",
                tool=action["tool"],
                operation=action["operation"],
                params=action["params"],
                context={
                    "purpose": "social media management",
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "brand_safe": True,
                },
            )

            print(f"   Status: {result.get('status')}")
            print(f"   Decision: {result.get('decision')}")
            print(f"   Risk: {result.get('risk_level')}")
            if result.get("status") == "pending_approval":
                print(f"   ⏳ Requires marketing approval")
            print()

            iteration += 1
            time.sleep(random.uniform(4, 10))

        except KeyboardInterrupt:
            print("\\n🛑 Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_agent()
