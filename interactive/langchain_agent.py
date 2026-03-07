#!/usr/bin/env python3
"""
Interactive LangChain Demo with Real LLM and Dual Policies
===========================================================
This demo showcases Faramesh governance with a real LLM agent that:
1. Uses filesystem operations (governed by langchain_filesystem_policy.yaml)
2. Processes payments/refunds (governed by autogen_financial_policy.yaml)
3. Waits interactively for human approval when policies require it
4. Continues executing tasks after approval

The demo will:
- Activate two different policies
- Attempt multiple operations (some allowed, some requiring approval, some blocked)
- Wait for user input when approval is needed
- Show the full governance workflow in action

Usage:
    OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE" \
    python3 demo_interactive_langchain.py
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
import json
from typing import Dict, Any, List
from pathlib import Path


# Color codes for pretty output
class C:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    print(f"{C.FAIL}❌ LangChain not installed{C.END}")
    print("Install: pip install langchain langchain-openai")
    sys.exit(1)

# Faramesh imports
try:
    from faramesh import (
        submit_action,
        get_action,
        report_result,
        configure,
        approve_action,
    )

    FARAMESH_AVAILABLE = True
except ImportError:
    print(f"{C.FAIL}❌ Faramesh SDK not installed{C.END}")
    print("Run: git clone https://github.com/faramesh/faramesh-core.git && pip install -e ./faramesh-core")
    sys.exit(1)

# ==============================================================================
# Configuration
# ==============================================================================


def setup_environment():
    """Configure Faramesh and check requirements"""
    configure(base_url="http://127.0.0.1:8000", auth_token="demo-token")

    # Check OpenRouter key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(f"{C.FAIL}❌ OPENROUTER_API_KEY not set{C.END}")
        print("Set it with: export OPENROUTER_API_KEY=sk-or-v1-...")
        sys.exit(1)

    print(f"{C.OKGREEN}✓ Faramesh configured{C.END}")
    print(f"{C.OKGREEN}✓ OpenRouter API key found{C.END}")
    return api_key


def activate_policies():
    """Activate both filesystem and financial policies"""
    import requests

    policies = [
        ("langchain_filesystem_policy.yaml", "Filesystem Security"),
        ("autogen_financial_policy.yaml", "Financial Approval"),
    ]

    print(f"\n{C.HEADER}═══ Activating Policies ═══{C.END}")

    for filename, name in policies:
        try:
            resp = requests.post(
                f"http://127.0.0.1:8000/v1/policies/yaml/{filename}/activate",
                headers={"Authorization": "Bearer demo-token"},
            )
            if resp.status_code == 200:
                print(f"{C.OKGREEN}✓ Activated: {name}{C.END}")
            else:
                print(f"{C.WARNING}⚠ Could not activate {name}: {resp.text}{C.END}")
        except Exception as e:
            print(f"{C.FAIL}❌ Error activating {name}: {e}{C.END}")

    print()


# ==============================================================================
# Governed Tools for LangChain
# ==============================================================================


@tool
def filesystem_operation(operation: str, path: str, content: str = "") -> str:
    """
    Perform filesystem operations (read, write, delete, list).
    Governed by langchain_filesystem_policy.yaml.

    Args:
        operation: One of 'read', 'write', 'delete', 'list'
        path: File or directory path
        content: Content to write (for write operations)
    """
    try:
        action_id = submit_action(
            tool="filesystem",
            operation=operation,
            params={"path": path, "content": content},
            agent_id="langchain-demo",
            context={"user": "demo-user"},
        )

        print(f"{C.OKCYAN}📝 Submitted filesystem.{operation} → {action_id[:8]}{C.END}")

        # Poll for result
        for attempt in range(60):  # 60 seconds max
            time.sleep(1)
            status = get_action(action_id)

            if status["status"] == "pending_approval":
                print(f"\n{C.WARNING}⏸  ACTION REQUIRES APPROVAL{C.END}")
                print(f"   Tool: filesystem.{operation}")
                print(f"   Path: {path}")
                print(
                    f"   Reason: {status.get('policy_decision', {}).get('reason', 'Policy requires approval')}"
                )

                # Get approval token
                approval_url = f"http://localhost:3000/approvals?action={action_id}"
                print(f"\n{C.HEADER}🔗 Approval URL: {approval_url}{C.END}")

                # Wait for user to approve via UI or CLI
                print(f"\n{C.BOLD}Choose approval method:{C.END}")
                print("  1. Open the URL above in your browser")
                print("  2. Type 'approve' here to approve via CLI")
                print("  3. Type 'deny' to deny the action")

                choice = input(f"\n{C.OKCYAN}Your choice: {C.END}").strip().lower()

                if choice == "approve":
                    approve_action(action_id, comment="Approved via CLI")
                    print(f"{C.OKGREEN}✓ Approved! Waiting for execution...{C.END}")
                elif choice == "deny":
                    # Deny via API
                    import requests

                    requests.post(
                        f"http://127.0.0.1:8000/v1/actions/{action_id}/deny",
                        headers={"Authorization": "Bearer demo-token"},
                        json={"reason": "Denied via CLI"},
                    )
                    return f"❌ Action denied by user"
                else:
                    print(f"{C.WARNING}⏳ Waiting for approval via browser...{C.END}")

                continue

            elif status["status"] == "completed":
                result = status.get("result", {})
                report_result(action_id, result, "success")
                return f"✓ {operation} completed: {result.get('message', 'Success')}"

            elif status["status"] == "denied":
                reason = status.get("policy_decision", {}).get(
                    "reason", "Policy denied"
                )
                return f"🚫 Blocked by policy: {reason}"

            elif status["status"] == "failed":
                return f"❌ Failed: {status.get('error', 'Unknown error')}"

        return "⏱ Timeout waiting for action"

    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def process_payment(operation: str, amount: float, currency: str = "USD") -> str:
    """
    Process payment operations (charge, refund).
    Governed by autogen_financial_policy.yaml.

    Args:
        operation: One of 'charge', 'refund'
        amount: Amount in cents (e.g., 150000 = $1,500)
        currency: Currency code (default: USD)
    """
    try:
        action_id = submit_action(
            tool="payment",
            operation=operation,
            params={"amount": amount, "currency": currency},
            agent_id="langchain-demo",
            context={"user": "demo-user"},
        )

        print(f"{C.OKCYAN}💰 Submitted payment.{operation} → {action_id[:8]}{C.END}")

        # Poll for result
        for attempt in range(60):
            time.sleep(1)
            status = get_action(action_id)

            if status["status"] == "pending_approval":
                print(f"\n{C.WARNING}⏸  ACTION REQUIRES APPROVAL{C.END}")
                print(f"   Tool: payment.{operation}")
                print(f"   Amount: ${amount/100:.2f} {currency}")
                print(
                    f"   Reason: {status.get('policy_decision', {}).get('reason', 'Policy requires approval')}"
                )

                approval_url = f"http://localhost:3000/approvals?action={action_id}"
                print(f"\n{C.HEADER}🔗 Approval URL: {approval_url}{C.END}")

                print(f"\n{C.BOLD}Choose approval method:{C.END}")
                print("  1. Open the URL above in your browser")
                print("  2. Type 'approve' here to approve via CLI")
                print("  3. Type 'deny' to deny the action")

                choice = input(f"\n{C.OKCYAN}Your choice: {C.END}").strip().lower()

                if choice == "approve":
                    approve_action(action_id, comment="Approved via CLI")
                    print(f"{C.OKGREEN}✓ Approved! Waiting for execution...{C.END}")
                elif choice == "deny":
                    import requests

                    requests.post(
                        f"http://127.0.0.1:8000/v1/actions/{action_id}/deny",
                        headers={"Authorization": "Bearer demo-token"},
                        json={"reason": "Denied via CLI"},
                    )
                    return f"❌ Action denied by user"
                else:
                    print(f"{C.WARNING}⏳ Waiting for approval via browser...{C.END}")

                continue

            elif status["status"] == "completed":
                result = status.get("result", {})
                return f"✓ {operation} completed: ${amount/100:.2f} {currency}"

            elif status["status"] == "denied":
                reason = status.get("policy_decision", {}).get(
                    "reason", "Policy denied"
                )
                return f"🚫 Blocked by policy: {reason}"

            elif status["status"] == "failed":
                return f"❌ Failed: {status.get('error', 'Unknown error')}"

        return "⏱ Timeout waiting for action"

    except Exception as e:
        return f"❌ Error: {str(e)}"


# ==============================================================================
# LangChain Agent Setup
# ==============================================================================


def create_governed_agent(api_key: str):
    """Create a LangChain agent with governed tools"""

    # Initialize LLM
    llm = ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
    )

    # Define tools
    tools = [filesystem_operation, process_payment]

    # Create prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI assistant with access to filesystem and payment tools.
Your actions are governed by security policies that may require human approval.

When an action requires approval, the system will pause and wait for the user to approve or deny it.
After approval, you can continue with your tasks.

Available tools:
- filesystem_operation: read, write, delete, or list files
- process_payment: charge or refund payments

Be helpful and follow the user's instructions.""",
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )

    return agent_executor


# ==============================================================================
# Interactive Demo Scenarios
# ==============================================================================


def run_demo_scenario(agent):
    """Run an interactive demo with multiple operations"""

    print(f"\n{C.HEADER}{'═'*70}{C.END}")
    print(f"{C.HEADER}{'Interactive LangChain + Faramesh Demo':^70}{C.END}")
    print(f"{C.HEADER}{'═'*70}{C.END}\n")

    print(f"{C.BOLD}This demo will attempt several operations:{C.END}")
    print(f"  1. {C.OKGREEN}✓ Safe file read{C.END} (auto-allowed)")
    print(f"  2. {C.WARNING}⏸ File write{C.END} (may require approval)")
    print(f"  3. {C.OKGREEN}✓ Small refund ($300){C.END} (auto-allowed)")
    print(f"  4. {C.WARNING}⏸ Large refund ($1,500){C.END} (requires approval)")
    print(f"  5. {C.FAIL}🚫 Dangerous delete{C.END} (will be blocked)")
    print()

    input(f"{C.OKCYAN}Press Enter to start the demo...{C.END}")

    # Scenario 1: Safe file read (should be auto-allowed)
    print(f"\n{C.HEADER}▶ Scenario 1: Safe File Read{C.END}")
    result = agent.invoke({"input": "List the files in the demo-folder directory"})
    print(f"\n{C.OKGREEN}Result:{C.END} {result['output']}\n")
    time.sleep(2)

    # Scenario 2: File write (may require approval)
    print(f"\n{C.HEADER}▶ Scenario 2: File Write{C.END}")
    result = agent.invoke(
        {
            "input": "Create a file called 'test.txt' in demo-folder with content 'Hello from governed agent!'"
        }
    )
    print(f"\n{C.OKGREEN}Result:{C.END} {result['output']}\n")
    time.sleep(2)

    # Scenario 3: Small refund (auto-allowed)
    print(f"\n{C.HEADER}▶ Scenario 3: Small Refund ($300){C.END}")
    result = agent.invoke({"input": "Process a refund of $300 USD"})
    print(f"\n{C.OKGREEN}Result:{C.END} {result['output']}\n")
    time.sleep(2)

    # Scenario 4: Large refund (requires approval)
    print(f"\n{C.HEADER}▶ Scenario 4: Large Refund ($1,500){C.END}")
    result = agent.invoke({"input": "Process a refund of $1500 USD"})
    print(f"\n{C.OKGREEN}Result:{C.END} {result['output']}\n")
    time.sleep(2)

    # Scenario 5: Dangerous operation (should be blocked)
    print(f"\n{C.HEADER}▶ Scenario 5: Dangerous Delete{C.END}")
    result = agent.invoke({"input": "Delete all files using 'rm -rf' command"})
    print(f"\n{C.OKGREEN}Result:{C.END} {result['output']}\n")

    print(f"\n{C.HEADER}{'═'*70}{C.END}")
    print(f"{C.OKGREEN}✓ Demo completed!{C.END}")
    print(f"{C.HEADER}{'═'*70}{C.END}\n")


# ==============================================================================
# Main Entry Point
# ==============================================================================


def main():
    """Main demo entry point"""
    print(f"\n{C.BOLD}{C.HEADER}Faramesh + LangChain Interactive Demo{C.END}\n")

    # Setup
    api_key = setup_environment()
    activate_policies()

    # Create agent
    print(f"{C.OKCYAN}🤖 Creating LangChain agent with governed tools...{C.END}")
    agent = create_governed_agent(api_key)
    print(f"{C.OKGREEN}✓ Agent ready!{C.END}\n")

    # Run demo
    run_demo_scenario(agent)

    print(f"\n{C.BOLD}Key Takeaways:{C.END}")
    print(f"  • Policies govern agent behavior in real-time")
    print(f"  • Some actions auto-approve, others require human approval")
    print(f"  • Dangerous operations are blocked immediately")
    print(f"  • Agent continues working after approvals")
    print()


if __name__ == "__main__":
    main()
