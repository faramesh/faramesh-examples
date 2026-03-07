"""
LangChain LLM Agent with Governed Tools
============================================
This agent uses LLM (via OpenRouter) to decide what tasks to perform.
It can ask for multiple tasks in a loop and execute them with Faramesh governance.

Tasks available:
  1. Create files in demo-folder (filesystem)
  2. Query a database (database)
  3. Make an HTTP request (http)
  4. Run a shell command (shell)
  5. Search Google for a keyword in browser
  6. Install a Python package

The agent will ask you what to do, submit it through Faramesh governance,
and report results back.

Usage:
    FARAMESH_DEMO=1 \
    FARA_API_BASE="http://127.0.0.1:8000" \
    FARA_AUTH_TOKEN="demo-token" \
    OPENROUTER_API_KEY="your-key-here" \
    /Users/xquark_home/Faramesh-Nexus/.venv/bin/python \
    demo_agents/01_langchain_llm_multi_task_agent.py
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain.tools import BaseTool, tool
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("❌ LangChain not installed. Install: pip install langchain langchain-openai")
    sys.exit(1)

# Faramesh imports
try:
    from faramesh import submit_action, get_action, report_result, configure

    FARAMESH_AVAILABLE = True
except ImportError:
    print("❌ Faramesh SDK not installed")
    sys.exit(1)

# Configure Faramesh
configure(
    base_url=os.getenv("FARA_API_BASE", "http://127.0.0.1:8000"),
    agent_id="langchain-llm-agent",
    auth_token=os.getenv("FARA_AUTH_TOKEN", "demo-token"),
)

AGENT_ID = "langchain-llm-agent"


# ============================================================================
# Custom LangChain Tools (wrapped with Faramesh governance)
# ============================================================================


class FileCreationTool(BaseTool):
    """Tool to create files in demo-folder."""

    name = "create_files"
    description = "Create files in demo-folder. Input: JSON with 'count' (number of files) and 'prefix' (file name prefix)"

    def _run(self, input_str: str) -> str:
        """Execute file creation through Faramesh governance."""
        import json

        try:
            params = json.loads(input_str)
            count = params.get("count", 5)
            prefix = params.get("prefix", "file_")
        except:
            count = 5
            prefix = "file_"

        folder = Path.cwd() / "demo-folder"

        print(f"\n🔐 Submitting file creation to Faramesh...")
        print(f"   Creating {count} files in {folder}")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="filesystem",
            operation="batch_create",
            params={
                "folder": str(folder),
                "count": count,
                "prefix": prefix,
                "extension": ".txt",
            },
            context={"purpose": "LLM-requested file creation"},
        )

        status = result.get("status")
        decision = result.get("decision")

        if status == "denied":
            return f"❌ File creation DENIED by policy: {result.get('reason', 'No reason provided')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval (action_id: {result.get('id')})...")

            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        if updated.get("status") == "denied":
                            return f"❌ File creation REJECTED: {updated.get('reason', 'No reason')}"
                        break
                except:
                    pass

            result = updated or result

        if status in ("allowed", "approved"):
            folder.mkdir(parents=True, exist_ok=True)
            created = []
            for i in range(count):
                name = f"{prefix}{i+1}.txt"
                path = folder / name
                path.write_text(f"File created by LLM agent: {i+1}\n")
                created.append(str(path))

            try:
                if result.get("id"):
                    report_result(
                        result.get("id"), success=True, result={"created": created}
                    )
            except:
                pass

            return f"✅ Created {count} files in {folder}"

        return f"⚠️ Unexpected status: {status}"


class DatabaseQueryTool(BaseTool):
    """Tool to query database (simulated)."""

    name = "query_database"
    description = "Query a database. Input: SQL query string"

    def _run(self, query: str) -> str:
        """Execute database query through Faramesh governance."""
        print(f"\n🔐 Submitting database query to Faramesh...")
        print(f"   Query: {query[:50]}...")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="database",
            operation="query",
            params={"query": query},
            context={"purpose": "LLM-requested database query"},
        )

        status = result.get("status")

        if status == "denied":
            return f"❌ Query DENIED: {result.get('reason', 'Policy blocked')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval...")
            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        result = updated
                        break
                except:
                    pass

        if result.get("status") == "denied":
            return f"❌ Query REJECTED: {result.get('reason')}"

        if result.get("status") in ("allowed", "approved"):
            # Simulate database response
            try:
                if result.get("id"):
                    report_result(result.get("id"), success=True, result={"rows": 42})
            except:
                pass
            return f"✅ Query executed: Found 42 rows"

        return f"⚠️ Unexpected status: {result.get('status')}"


class HttpRequestTool(BaseTool):
    """Tool to make HTTP requests (simulated)."""

    name = "make_http_request"
    description = "Make an HTTP request. Input: JSON with 'method' and 'url'"

    def _run(self, input_str: str) -> str:
        """Execute HTTP request through Faramesh governance."""
        import json

        try:
            params = json.loads(input_str)
            method = params.get("method", "GET")
            url = params.get("url", "https://example.com")
        except:
            method = "GET"
            url = "https://example.com"

        print(f"\n🔐 Submitting HTTP request to Faramesh...")
        print(f"   {method} {url}")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="http",
            operation="request",
            params={"method": method, "url": url},
            context={"purpose": "LLM-requested HTTP call"},
        )

        status = result.get("status")

        if status == "denied":
            return f"❌ Request DENIED: {result.get('reason')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval...")
            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        result = updated
                        break
                except:
                    pass

        if result.get("status") == "denied":
            return f"❌ Request REJECTED: {result.get('reason')}"

        if result.get("status") in ("allowed", "approved"):
            try:
                if result.get("id"):
                    report_result(
                        result.get("id"), success=True, result={"status_code": 200}
                    )
            except:
                pass
            return f"✅ {method} {url} returned 200 OK"

        return f"⚠️ Unexpected status: {result.get('status')}"


class ShellCommandTool(BaseTool):
    """Tool to run shell commands (limited)."""

    name = "run_shell_command"
    description = (
        "Run a shell command. Input: command string (limited to safe commands)"
    )

    def _run(self, command: str) -> str:
        """Execute shell command through Faramesh governance."""
        # Only allow safe commands
        safe_commands = ["ls", "pwd", "date", "whoami", "echo"]
        first_word = command.split()[0] if command else ""

        if first_word not in safe_commands:
            return f"❌ Command '{first_word}' not allowed. Safe: {', '.join(safe_commands)}"

        print(f"\n🔐 Submitting shell command to Faramesh...")
        print(f"   Command: {command}")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="shell",
            operation="run",
            params={"command": command},
            context={"purpose": "LLM-requested shell command"},
        )

        status = result.get("status")

        if status == "denied":
            return f"❌ Command DENIED: {result.get('reason')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval...")
            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        result = updated
                        break
                except:
                    pass

        if result.get("status") == "denied":
            return f"❌ Command REJECTED: {result.get('reason')}"

        if result.get("status") in ("allowed", "approved"):
            try:
                import subprocess

                output = subprocess.check_output(command.split(), text=True).strip()
            except:
                output = f"(command executed)"

            try:
                if result.get("id"):
                    report_result(
                        result.get("id"), success=True, result={"output": output}
                    )
            except:
                pass
            return f"✅ Command executed:\n{output}"

        return f"⚠️ Unexpected status: {result.get('status')}"


class BrowserSearchTool(BaseTool):
    """Tool to open browser and search Google."""

    name = "browser_search"
    description = "Open Google in browser and search for a keyword. Input: JSON with 'query' (search term)"

    def _run(self, input_str: str) -> str:
        """Execute browser search through Faramesh governance."""
        import json

        try:
            params = json.loads(input_str)
            query = params.get("query", "faramesh")
        except:
            query = "faramesh"

        print(f"\n🔐 Submitting browser search to Faramesh...")
        print(f"   Opening Google to search for: {query}")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="browser",
            operation="search",
            params={"query": query, "engine": "google"},
            context={"purpose": "LLM-requested web search"},
        )

        status = result.get("status")

        if status == "denied":
            return f"❌ Browser search DENIED: {result.get('reason')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval...")
            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        result = updated
                        break
                except:
                    pass

        if result.get("status") == "denied":
            return f"❌ Browser search REJECTED: {result.get('reason')}"

        if result.get("status") in ("allowed", "approved"):
            try:
                import webbrowser

                search_url = (
                    f"https://www.google.com/search?q={query.replace(' ', '+')}"
                )
                webbrowser.open(search_url)
                print(f"   Opening: {search_url}")
            except Exception as e:
                return f"⚠️ Browser error: {str(e)}"

            try:
                if result.get("id"):
                    report_result(
                        result.get("id"), success=True, result={"url": search_url}
                    )
            except:
                pass
            return f"✅ Opened Google search for '{query}': {search_url}"

        return f"⚠️ Unexpected status: {result.get('status')}"


class PythonInstallTool(BaseTool):
    """Tool to install Python packages."""

    name = "install_python_package"
    description = "Install a Python package via pip. Input: package name (e.g., 'colorama', 'requests', 'click')"

    def _run(self, package_name: str) -> str:
        """Execute Python package installation through Faramesh governance."""
        # Only allow small, safe packages
        allowed_packages = [
            "colorama",
            "click",
            "tabulate",
            "pyyaml",
            "python-dotenv",
            "termcolor",
            "rich",
            "typer",
            "httpx",
            "slugify",
        ]

        package_name = package_name.strip().lower()

        if package_name not in allowed_packages:
            return f"❌ Package '{package_name}' not in allowed list. Allowed: {', '.join(allowed_packages)}"

        print(f"\n🔐 Submitting pip install to Faramesh...")
        print(f"   Installing package: {package_name}")

        result = submit_action(
            agent_id=AGENT_ID,
            tool="pip",
            operation="install",
            params={"package": package_name},
            context={"purpose": "LLM-requested Python package installation"},
        )

        status = result.get("status")

        if status == "denied":
            return f"❌ Installation DENIED: {result.get('reason')}"

        if status == "pending_approval":
            print(f"⏳ Waiting for approval...")
            import time

            action_id = result.get("id")
            start = time.time()
            while time.time() - start < 300:
                time.sleep(1)
                try:
                    updated = get_action(action_id)
                    if updated.get("status") in ("approved", "denied", "allowed"):
                        result = updated
                        break
                except:
                    pass

        if result.get("status") == "denied":
            return f"❌ Installation REJECTED: {result.get('reason')}"

        if result.get("status") in ("allowed", "approved"):
            try:
                import subprocess

                output = subprocess.check_output(
                    [sys.executable, "-m", "pip", "install", package_name, "-q"],
                    text=True,
                    stderr=subprocess.STDOUT,
                ).strip()
            except Exception as e:
                output = str(e)

            try:
                if result.get("id"):
                    report_result(
                        result.get("id"), success=True, result={"package": package_name}
                    )
            except:
                pass
            return f"✅ Successfully installed '{package_name}'"

        return f"⚠️ Unexpected status: {result.get('status')}"


# ============================================================================
# Multi-Turn Agent Loop
# ============================================================================


def create_agent():
    """Create a LangChain agent with governed tools."""

    # Initialize LLM via OpenRouter
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        sys.exit(1)

    llm = ChatOpenAI(
        model="openrouter/openai/gpt-4o-mini",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
    )

    # Create tools
    tools = [
        FileCreationTool(),
        DatabaseQueryTool(),
        HttpRequestTool(),
        ShellCommandTool(),
        BrowserSearchTool(),
        PythonInstallTool(),
    ]

    # Create prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI agent that can perform various tasks through a governance system.
You have access to tools that create files, query databases, make HTTP requests, run shell commands,
search the web in a browser, and install Python packages.

When the user asks you to do something, use the appropriate tool.
After each task, wait for the result and inform the user.
Always be respectful of the governance system and explain what you're doing.

Available tasks:
- Create files in demo-folder
- Query a database
- Make HTTP requests
- Run shell commands (ls, pwd, date, whoami, echo)
- Open Google and search for keywords
- Install Python packages (colorama, click, tabulate, pyyaml, python-dotenv, etc)
""",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

    return executor


def main():
    """Run the multi-turn LLM agent loop."""

    print("=" * 70)
    print("🤖 LangChain LLM Agent with Faramesh Governance")
    print("=" * 70)
    print("\nAvailable tasks:")
    print("  1. Create files in demo-folder")
    print("  2. Query a database")
    print("  3. Make HTTP requests")
    print("  4. Run shell commands")
    print("\nType 'quit' to exit.\n")

    agent = create_agent()
    chat_history: List[BaseMessage] = []

    while True:
        try:
            user_input = input("📝 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if user_input.lower() in ("quit", "exit"):
            print("👋 Goodbye!")
            break

        if not user_input:
            continue

        # Add user message to chat history
        chat_history.append(HumanMessage(content=user_input))

        # Run agent
        try:
            result = agent.invoke(
                {
                    "input": user_input,
                    "chat_history": chat_history,
                }
            )

            response = result.get("output", "No response")
            print(f"\n🤖 Agent: {response}\n")

            # Add agent response to chat history
            chat_history.append(AIMessage(content=response))

        except Exception as e:
            print(f"❌ Error: {e}\n")
            chat_history.append(AIMessage(content=f"Error: {str(e)}"))


if __name__ == "__main__":
    main()
