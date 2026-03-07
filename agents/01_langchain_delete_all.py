#!/usr/bin/env python3
"""
LangChain + Faramesh Demo: Stopping a "delete_all" hallucination

This demo shows how Faramesh prevents a LangChain agent from executing
a dangerous delete_all command due to LLM hallucination.

Scenario:
- Agent is asked to "clean up temporary files"
- LLM hallucinates and tries to run "rm -rf /"
- Faramesh blocks the dangerous command at the gate

Required Policy: langchain_filesystem_policy.yaml
"""

import os
import sys
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from demo_utils import ensure_server_available

# Add parent directory to path for imports
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
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "langchain-agent-001")

configure(
    base_url=FARAMESH_BASE_URL,
    token=FARAMESH_TOKEN,
    agent_id=FARAMESH_AGENT_ID,
)


def execute_shell_command(cmd: str) -> str:
    """Execute shell command through Faramesh gate.

    This tool is intentionally simple to show how even basic
    tools can be protected by Faramesh.
    """
    try:
        # Submit action to Faramesh
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="shell",
            operation="execute",
            params={"cmd": cmd},
            context={
                "agent_framework": "langchain",
                "agent_name": "cleanup_agent",
                "user_request": "clean up temporary files",
            },
        )

        print(f"✓ Action submitted: {action['id']}")
        print(f"  Status: {action['status']}")
        print(f"  Decision: {action.get('decision', 'N/A')}")

        if action["status"] == "denied":
            return f"❌ Command BLOCKED by Faramesh: {action.get('reason', 'Security policy violation')}"

        if action["status"] == "pending_approval":
            return (
                f"⏳ Command REQUIRES APPROVAL: {cmd}\n"
                f"   Action ID: {action['id']}\n"
                f"   Reason: {action.get('reason', 'Requires human approval')}"
            )

        # Wait for execution
        result = wait_for_action(action["id"], timeout=30)

        if result["status"] == "succeeded":
            return f"✓ Command executed: {result.get('reason', 'ok')}"
        else:
            return f"❌ Command failed: {result.get('reason', 'unknown error')}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


def list_files(directory: str = ".") -> str:
    """List files in directory through Faramesh gate."""
    try:
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="shell",
            operation="execute",
            params={"cmd": f"ls -la {directory}"},
            context={"agent_framework": "langchain", "operation_type": "read_only"},
        )

        result = wait_for_action(action["id"], timeout=10)

        if result["status"] == "succeeded":
            return result.get("reason", "")
        else:
            return f"Failed: {result.get('reason', 'unknown')}"
    except Exception as e:
        return f"Error: {str(e)}"


# Create LangChain tools
tools = [
    Tool(
        name="Execute Shell Command",
        func=execute_shell_command,
        description=(
            "Execute a shell command on the system. "
            "Use this for any file system operations, cleanup tasks, or system commands. "
            "The command will be validated by Faramesh security gate."
        ),
    ),
    Tool(
        name="List Files",
        func=list_files,
        description="List files in a directory. Useful for inspecting file system structure.",
    ),
]


# Create React agent
template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

llm = ChatOpenAI(temperature=0, model="gpt-4")

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
)


def run_demo():
    """Run the LangChain delete_all hallucination demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 LangChain + Faramesh Demo: Preventing delete_all Hallucination")
    print("=" * 80)
    print()
    print("Scenario: Agent is asked to 'clean up all temporary files'")
    print("Risk: LLM might hallucinate and try dangerous commands like 'rm -rf /'")
    print("Protection: Faramesh blocks dangerous commands at the gate")
    print()
    print("-" * 80)
    print()

    # Test 1: Safe command (should work)
    print("📋 TEST 1: Safe command - list files")
    print("-" * 80)
    try:
        response = agent_executor.invoke(
            {"input": "List the files in the current directory"}
        )
        print(f"\n✓ Result: {response['output']}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

    # Test 2: Dangerous command (should be blocked)
    print("\n📋 TEST 2: Dangerous command - simulated hallucination")
    print("-" * 80)
    print("Simulating LLM hallucination: Agent tries to run 'rm -rf /'")

    # Directly test the dangerous command
    result = execute_shell_command("rm -rf /")
    print(f"\n{result}\n")

    # Test 3: Another dangerous pattern
    print("\n📋 TEST 3: Another dangerous pattern - delete all with wildcard")
    print("-" * 80)
    result = execute_shell_command("rm -rf *")
    print(f"\n{result}\n")

    # Test 4: Safe cleanup command
    print("\n📋 TEST 4: Safe cleanup command - remove specific temp files")
    print("-" * 80)
    result = execute_shell_command("rm -f /tmp/test_*.tmp")
    print(f"\n{result}\n")

    print("=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. Dangerous commands (rm -rf /) are BLOCKED by Faramesh")
    print("2. Safe commands (ls, targeted rm) are ALLOWED")
    print("3. All actions are logged with full audit trail")
    print("4. Zero-trust: Every command is validated before execution")
    print()


if __name__ == "__main__":
    run_demo()
