#!/usr/bin/env python3
"""
CrewAI + Faramesh Demo: Preventing multi-agent infinite loops

This demo shows how Faramesh prevents CrewAI agents from getting stuck
in infinite loops through rate limiting and circuit breaker patterns.

Scenario:
- Multiple CrewAI agents coordinate on a task
- Agent A keeps delegating to Agent B, and B delegates back to A
- Faramesh detects the loop via rate limiting and blocks further actions

Required Policy: crewai_rate_limit_policy.yaml
"""

import os
import sys
import time
from typing import List, Optional
from demo_utils import ensure_server_available

# Note: CrewAI might not be installed, so we'll simulate the structure
try:
    from crewai import Agent, Task, Crew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("⚠️  CrewAI not installed. Running in simulation mode.")

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-python-sdk-code")
    ),
)

from faramesh import configure, submit_action, wait_for_action


FARAMESH_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
FARAMESH_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv(
    "FARAMESH_API_KEY", "demo-api-key-123"
)
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "crewai-coordinator-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


class FarameshProtectedTool:
    """Base class for Faramesh-protected tools."""

    def __init__(self, agent_id: str, tool_name: str):
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.call_count = 0

    def execute(
        self, operation: str, params: dict, context: Optional[dict] = None
    ) -> dict:
        """Execute tool through Faramesh gate."""
        self.call_count += 1

        context = context or {}
        context.update(
            {
                "agent_framework": "crewai",
                "agent_id": self.agent_id,
                "call_count": self.call_count,
            }
        )

        try:
            action = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool=self.tool_name,
                operation=operation,
                params=params,
                context=context,
            )

            print(
                f"  [{self.agent_id}] Action #{self.call_count} submitted: {action['id']}"
            )
            print(
                f"    Status: {action['status']} | Decision: {action.get('decision', 'N/A')}"
            )

            if action["status"] == "denied":
                print(f"    ❌ BLOCKED: {action.get('reason', 'Rate limit exceeded')}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": action.get("reason", "Rate limit exceeded"),
                }

            if action["status"] == "pending_approval":
                print(f"    ⏳ REQUIRES APPROVAL: {action.get('reason')}")
                return {
                    "success": False,
                    "requires_approval": True,
                    "action_id": action["id"],
                }

            # Wait for result
            result = wait_for_action(action["id"], timeout=10)

            return {
                "success": result["status"] == "succeeded",
                "result": result.get("reason", ""),
                "status": result["status"],
            }

        except Exception as e:
            print(f"    ❌ Error: {e}")
            return {"success": False, "error": str(e)}


class DelegationTool(FarameshProtectedTool):
    """Tool for delegating tasks between agents."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "delegation")

    def delegate_to_agent(self, target_agent: str, task: str) -> dict:
        """Delegate task to another agent."""
        return self.execute(
            operation="delegate",
            params={
                "target_agent": target_agent,
                "task": task,
                "delegator": self.agent_id,
            },
            context={"delegation_chain": [self.agent_id, target_agent]},
        )


def simulate_infinite_loop():
    """Simulate an infinite loop between two CrewAI agents."""
    print("\n" + "=" * 80)
    print("🔒 CrewAI + Faramesh Demo: Preventing Infinite Loops")
    print("=" * 80)
    print()
    print("Scenario: Agent A delegates to Agent B, B delegates back to A")
    print("Risk: Infinite delegation loop consuming resources")
    print("Protection: Faramesh rate limiting blocks excessive calls")
    print()
    print("-" * 80)
    print()

    # Create two agents with delegation tools
    agent_a_tool = DelegationTool("crewai-agent-a")
    agent_b_tool = DelegationTool("crewai-agent-b")

    print("📋 Starting delegation loop simulation...")
    print("-" * 80)
    print()

    loop_count = 0
    max_loops = 20  # Safety limit for demo
    blocked = False

    while loop_count < max_loops and not blocked:
        loop_count += 1
        print(f"\n🔄 Loop Iteration {loop_count}:")
        print("-" * 40)

        # Agent A delegates to Agent B
        print(f"Agent A → Agent B (delegation #{agent_a_tool.call_count + 1})")
        result_a = agent_a_tool.delegate_to_agent(
            target_agent="crewai-agent-b", task="Process user request"
        )

        if result_a.get("blocked"):
            print("\n🛑 LOOP STOPPED BY FARAMESH!")
            print(f"   Reason: {result_a['reason']}")
            print(f"   Total iterations: {loop_count}")
            blocked = True
            break

        time.sleep(0.5)  # Small delay between delegations

        # Agent B delegates back to Agent A
        print(f"Agent B → Agent A (delegation #{agent_b_tool.call_count + 1})")
        result_b = agent_b_tool.delegate_to_agent(
            target_agent="crewai-agent-a", task="Review processed request"
        )

        if result_b.get("blocked"):
            print("\n🛑 LOOP STOPPED BY FARAMESH!")
            print(f"   Reason: {result_b['reason']}")
            print(f"   Total iterations: {loop_count}")
            blocked = True
            break

        time.sleep(0.5)

    print()
    print("=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print()
    print("Statistics:")
    print(f"  - Agent A calls: {agent_a_tool.call_count}")
    print(f"  - Agent B calls: {agent_b_tool.call_count}")
    print(f"  - Loop iterations: {loop_count}")
    print(f"  - Blocked by Faramesh: {'YES' if blocked else 'NO'}")
    print()
    print("Key Takeaways:")
    print("1. Rate limiting prevents infinite loops")
    print("2. Each agent's calls are tracked independently")
    print("3. Circuit breaker activates after threshold")
    print("4. System remains responsive even during loops")
    print()


def run_demo():
    """Run the CrewAI infinite loop demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    if not CREWAI_AVAILABLE:
        print("\n💡 Running simulation without CrewAI package...")
        print("   (Install crewai package for full demo)\n")

    simulate_infinite_loop()


if __name__ == "__main__":
    run_demo()
