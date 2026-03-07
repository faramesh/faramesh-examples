#!/usr/bin/env python3
"""
Custom Social Media Bot
Risk Level: MEDIUM
Posts to social media with approval requirements
"""
import os
import sys
import time
import random
from datetime import datetime

sys.path.insert(0, "/Users/xquark_home/Faramesh-Nexus/faramesh-horizon-code/src")

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
