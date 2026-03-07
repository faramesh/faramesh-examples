#!/usr/bin/env python3
"""
Interactive AI Agent with Faramesh Governance (Direct OpenRouter)
=================================================================
Chat with an AI agent that can perform actions on your machine,
but all dangerous actions require your approval through the Faramesh UI.

This version uses OpenRouter API directly (no LangChain needed).

Usage:
    OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE" \
    python3 demo_interactive_ai_agent_simple.py
"""

import os
import sys
import time
import json
import subprocess
import webbrowser
import requests
from typing import Dict, Any, List


# Color codes
class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


# Faramesh SDK
try:
    from faramesh import submit_action, get_action, configure
except ImportError:
    print(f"{C.RED}❌ Faramesh SDK not installed{C.END}")
    sys.exit(1)


# ==============================================================================
# Configuration
# ==============================================================================


def setup_faramesh():
    """Configure Faramesh"""
    configure(base_url="http://127.0.0.1:8000", auth_token="demo-token")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(f"{C.RED}❌ OPENROUTER_API_KEY not set{C.END}")
        sys.exit(1)

    print(f"{C.GREEN}✓ Faramesh configured{C.END}")
    print(f"{C.GREEN}✓ API key found{C.END}\n")
    return api_key


def wait_for_action_result(action_id: str, operation_name: str) -> Dict[str, Any]:
    """
    Wait for action to complete, handling approvals interactively.
    Returns the final status.
    """
    approval_url = "http://localhost:3000/approvals"
    shown_pending_message = False

    for attempt in range(120):  # 2 minutes max
        time.sleep(1)

        # Get action status
        action_data = get_action(action_id)
        status = action_data.get("status")

        if status == "pending_approval":
            if not shown_pending_message:
                reason = action_data.get("reason", "Policy requires approval")
                print(f"\n{C.YELLOW}⏸  ACTION PENDING APPROVAL{C.END}")
                print(f"   Operation: {operation_name}")
                print(f"   Reason: {reason}")
                print(f"\n{C.CYAN}🌐 Go to Faramesh UI to approve/deny:{C.END}")
                print(f"   {C.BOLD}{approval_url}{C.END}")
                print(
                    f"\n{C.YELLOW}⏳ Waiting for your decision (I'll wait here)...{C.END}\n"
                )
                shown_pending_message = True
            continue

        elif status in ["approved", "completed"]:
            if shown_pending_message:
                print(f"\n{C.GREEN}✅ APPROVED! Continuing...{C.END}\n")
            return {"status": status, "data": action_data}

        elif status == "denied":
            reason = action_data.get("reason", "Policy denied")
            print(f"\n{C.RED}🚫 DENIED: {reason}{C.END}")
            print(
                f"{C.YELLOW}I can't do this action, but I'll continue with other tasks...{C.END}\n"
            )
            return {"status": "denied", "reason": reason}

        elif status == "failed":
            error = action_data.get("error", "Unknown error")
            print(f"\n{C.RED}❌ Action failed: {error}{C.END}\n")
            return {"status": "failed", "error": error}

    print(f"\n{C.YELLOW}⏱ Timeout waiting for action{C.END}\n")
    return {"status": "timeout"}


# ==============================================================================
# Tool Handlers
# ==============================================================================


def handle_create_files(folder_name: str, num_files: int = 5):
    """Create a folder with text files"""
    try:
        action_id = submit_action(
            tool="file",
            operation="write",
            params={"folder": folder_name, "num_files": num_files},
            agent_id="interactive-ai",
            context={"action_type": "file_creation"},
        )

        print(
            f"{C.CYAN}📝 Submitted: Create folder with {num_files} files → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"create_files({folder_name})")

        if result["status"] in ["completed", "approved"]:
            # Actually create the files
            os.makedirs(f"demo-folder/{folder_name}", exist_ok=True)
            for i in range(1, num_files + 1):
                with open(f"demo-folder/{folder_name}/file_{i}.txt", "w") as f:
                    f.write(f"This is test file {i} in {folder_name}\n")
            return f"✅ Created folder '{folder_name}' with {num_files} text files!"
        elif result["status"] == "denied":
            return f"❌ Can't create files. Reason: {result.get('reason')}"
        else:
            return f"⚠️ Action couldn't be completed"

    except Exception as e:
        return f"Error: {str(e)}"


def handle_list_files(directory: str = "."):
    """List files in a directory"""
    try:
        action_id = submit_action(
            tool="shell",
            operation="execute",
            params={"cmd": f"ls {directory}"},
            agent_id="interactive-ai",
            context={"action_type": "list_files"},
        )

        print(
            f"{C.CYAN}💻 Submitted: List files in {directory} → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"list_files({directory})")

        if result["status"] in ["completed", "approved"]:
            proc = subprocess.run(
                f"ls {directory}", shell=True, capture_output=True, text=True
            )
            files = proc.stdout.strip()
            return f"✅ Files in {directory}:\n{files}"
        elif result["status"] == "denied":
            return f"❌ Can't list files. Reason: {result.get('reason')}"
        else:
            return "⚠️ Couldn't complete"

    except Exception as e:
        return f"Error: {str(e)}"


def handle_read_file(filepath: str):
    """Read a file"""
    try:
        action_id = submit_action(
            tool="shell",
            operation="execute",
            params={"cmd": f"cat {filepath}"},
            agent_id="interactive-ai",
            context={"action_type": "read_file"},
        )

        print(f"{C.CYAN}📄 Submitted: Read file {filepath} → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, f"read_file({filepath})")

        if result["status"] in ["completed", "approved"]:
            proc = subprocess.run(
                f"cat {filepath}", shell=True, capture_output=True, text=True
            )
            content = proc.stdout[:500]  # First 500 chars
            return f"✅ Content of {filepath}:\n{content}"
        elif result["status"] == "denied":
            return f"❌ Can't read file. Reason: {result.get('reason')}"
        else:
            return "⚠️ Couldn't read"

    except Exception as e:
        return f"Error: {str(e)}"


def handle_delete_file(filepath: str):
    """Delete a file"""
    try:
        action_id = submit_action(
            tool="shell",
            operation="execute",
            params={"cmd": f"rm {filepath}"},
            agent_id="interactive-ai",
            context={"action_type": "delete_file"},
        )

        print(f"{C.CYAN}🗑️  Submitted: Delete file {filepath} → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, f"delete_file({filepath})")

        if result["status"] in ["completed", "approved"]:
            proc = subprocess.run(
                f"rm {filepath}", shell=True, capture_output=True, text=True
            )
            return f"✅ Deleted {filepath}"
        elif result["status"] == "denied":
            return f"❌ Can't delete. Reason: {result.get('reason')}"
        else:
            return "⚠️ Couldn't delete"

    except Exception as e:
        return f"Error: {str(e)}"


def handle_search_google(query: str):
    """Search Google"""
    try:
        action_id = submit_action(
            tool="browser",
            operation="search",
            params={"query": query},
            agent_id="interactive-ai",
            context={"action_type": "google_search"},
        )

        print(f"{C.CYAN}🔍 Submitted: Google search '{query}' → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, f"search_google({query})")

        if result["status"] in ["completed", "approved"]:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"✅ Opened Google search for '{query}'"
        elif result["status"] == "denied":
            return f"❌ Can't search. Reason: {result.get('reason')}"
        else:
            return "⚠️ Couldn't search"

    except Exception as e:
        return f"Error: {str(e)}"


# ==============================================================================
# AI Chat (Simple OpenRouter API)
# ==============================================================================


def chat_with_ai(api_key: str, user_message: str, conversation_history: List) -> str:
    """Send message to AI and get response"""

    messages = [
        {
            "role": "system",
            "content": """You are a helpful AI assistant. You can help users with:
- Creating files and folders (use: create_files <foldername> [numfiles])
- Listing files (use: list_files <directory>)
- Reading files (use: read_file <filepath>)
- Deleting files (use: delete_file <filepath>)
- Searching Google (use: search_google <query>)

When a user asks you to do something:
1. Explain what you'll do
2. Use the appropriate command
3. Wait for the result
4. Comment on the outcome

If an action is denied, acknowledge it and offer alternatives.
Always be conversational and helpful!""",
        }
    ]

    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "allenai/molmo-2-8b:free",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: API returned {response.status_code}"

    except Exception as e:
        return f"Error communicating with AI: {str(e)}"


def parse_ai_command(ai_response: str) -> tuple:
    """Extract command from AI response"""
    response_lower = ai_response.lower()

    if "create_files" in response_lower:
        # Extract folder name and number
        parts = ai_response.split("create_files")[1].strip().split()
        folder = parts[0] if parts else "test_folder"
        num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
        return ("create_files", folder, num)

    elif "list_files" in response_lower:
        parts = ai_response.split("list_files")[1].strip().split()
        directory = parts[0] if parts else "."
        return ("list_files", directory)

    elif "read_file" in response_lower:
        parts = ai_response.split("read_file")[1].strip().split()
        filepath = parts[0] if parts else ""
        return ("read_file", filepath)

    elif "delete_file" in response_lower:
        parts = ai_response.split("delete_file")[1].strip().split()
        filepath = parts[0] if parts else ""
        return ("delete_file", filepath)

    elif "search_google" in response_lower:
        query = ai_response.split("search_google")[1].strip()
        return ("search_google", query)

    return (None, None)


# ==============================================================================
# Main Chat Loop
# ==============================================================================


def run_interactive_chat(api_key: str, policy_name: str):
    """Run the interactive chat loop"""

    conversation = []

    print(f"\n{C.HEADER}{'='*70}{C.END}")
    print(f"{C.HEADER}{'🤖 Interactive AI Agent - Governed by Faramesh':^70}{C.END}")
    print(f"{C.HEADER}{'='*70}{C.END}\n")
    print(f"{C.CYAN}Active Policy: {policy_name}{C.END}")
    print(f"{C.YELLOW}Type 'quit' or 'exit' to end{C.END}\n")

    while True:
        try:
            user_input = input(f"{C.GREEN}You: {C.END}").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print(f"\n{C.CYAN}👋 Goodbye!{C.END}\n")
                break

            print(f"\n{C.BLUE}AI: {C.END}", end="", flush=True)

            # Get AI response
            ai_response = chat_with_ai(api_key, user_input, conversation)
            print(ai_response)

            # Parse for commands
            cmd, *args = parse_ai_command(ai_response)

            if cmd == "create_files":
                result = handle_create_files(*args)
                print(f"\n{result}\n")
                conversation.append({"role": "user", "content": user_input})
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"{ai_response}\n\nResult: {result}",
                    }
                )

            elif cmd == "list_files":
                result = handle_list_files(*args)
                print(f"\n{result}\n")
                conversation.append({"role": "user", "content": user_input})
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"{ai_response}\n\nResult: {result}",
                    }
                )

            elif cmd == "read_file":
                result = handle_read_file(*args)
                print(f"\n{result}\n")
                conversation.append({"role": "user", "content": user_input})
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"{ai_response}\n\nResult: {result}",
                    }
                )

            elif cmd == "delete_file":
                result = handle_delete_file(*args)
                print(f"\n{result}\n")
                conversation.append({"role": "user", "content": user_input})
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"{ai_response}\n\nResult: {result}",
                    }
                )

            elif cmd == "search_google":
                result = handle_search_google(*args)
                print(f"\n{result}\n")
                conversation.append({"role": "user", "content": user_input})
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"{ai_response}\n\nResult: {result}",
                    }
                )

            else:
                # Just conversational response
                conversation.append({"role": "user", "content": user_input})
                conversation.append({"role": "assistant", "content": ai_response})
                print()

            # Keep history manageable
            if len(conversation) > 10:
                conversation = conversation[-10:]

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}Interrupted. Type 'quit' to exit.{C.END}\n")
        except Exception as e:
            print(f"\n{C.RED}Error: {e}{C.END}\n")


# ==============================================================================
# Policy Management
# ==============================================================================


def activate_policy(policy_file: str):
    """Activate a YAML policy"""
    print(f"{C.CYAN}Activating policy: {policy_file}...{C.END}")

    try:
        resp = requests.post(
            f"http://127.0.0.1:8000/v1/policies/yaml/{policy_file}/activate",
            headers={"Authorization": "Bearer demo-token"},
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"{C.GREEN}✓ Policy activated: {data.get('policy_name')}{C.END}\n")
            return True
        else:
            print(f"{C.RED}Failed to activate policy: {resp.text}{C.END}\n")
            return False
    except Exception as e:
        print(f"{C.RED}Error: {e}{C.END}\n")
        return False


# ==============================================================================
# Main
# ==============================================================================


def main():
    """Main entry point"""

    print(f"\n{C.BOLD}{C.HEADER}Faramesh Interactive AI Agent{C.END}\n")

    # Setup
    api_key = setup_faramesh()

    # Activate demo policy
    print(f"{C.CYAN}Activating demo_policy.yaml...{C.END}")
    activate_policy("demo_policy.yaml")

    # Run interactive chat
    run_interactive_chat(api_key, "demo_policy.yaml")


if __name__ == "__main__":
    main()
