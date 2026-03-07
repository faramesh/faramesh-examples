#!/usr/bin/env python3
"""
🎬 2-MINUTE DEMO WITH REAL LLM (OpenRouter)
Real LangChain agent with real LLM reasoning + Faramesh governance.
Model: allenai/molmo-2-8b:free (no cost)
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
from pathlib import Path

# Add Faramesh to path


try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
except ImportError:
    print("❌ Missing deps. Install: pip install langchain langchain-openai")
    sys.exit(1)

from faramesh.adapters.langchain import faramesh_action_tool

# Demo environment
os.environ.setdefault("FARAMESH_API_BASE", "http://localhost:8000/v1")
os.environ.setdefault("FARAMESH_DEMO", "1")


class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    C = "\033[96m"
    W = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def build_llm() -> ChatOpenAI:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print(f"{C.R}❌ OPENROUTER_API_KEY not set{C.END}")
        print(f"{C.Y}Get a free key at https://openrouter.ai/ and run:{C.END}")
        print("  export OPENROUTER_API_KEY=sk-or-v1-...\n")
        sys.exit(1)

    return ChatOpenAI(
        model="allenai/molmo-2-8b:free",
        api_key=key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
    )


def llm_to_action(llm: ChatOpenAI, prompt: str) -> dict:
    """Ask the LLM to propose a database action JSON and return it as dict."""

    schema_hint = 'Return ONLY JSON: {"tool": "database|payment|shell", "operation": "read|drop_table|process|execute", "params": {...}}'
    tmpl = PromptTemplate.from_template(
        """You are a cautious assistant that can work with databases and payments.
Given a user request, propose ONE action as JSON.
{schema}
User request: {user_request}
JSON:"""
    )
    msg = tmpl.format(schema=schema_hint, user_request=prompt)
    resp = llm.invoke(msg)
    content = getattr(resp, "content", "") or ""

    import json

    try:
        start = content.find("{")
        end = content.rfind("}")
        action_obj = json.loads(content[start : end + 1])
    except Exception:
        action_obj = {
            "tool": "database",
            "operation": "read",
            "params": {"table_name": "users", "query": "SELECT COUNT(*) FROM users"},
        }

    return action_obj


def send_action(action_obj: dict) -> dict:
    """Send action through Faramesh governance and return response."""

    tool = action_obj.get("tool", "database")
    operation = action_obj.get("operation")
    params = action_obj.get("params", {})

    # Fallback for old format
    if not params and "table" in action_obj:
        params = {
            "table_name": action_obj.get("table"),
            "query": action_obj.get("query"),
        }

    try:
        result = faramesh_action_tool(
            agent_id="real-langchain-agent",
            tool=tool,
            operation=operation,
            params=params,
            context={"env": "production", "demo": "real-llm"},
        )
        return result
    except Exception as e:
        import traceback

        error_msg = str(e)
        if "403" in error_msg:
            raise Exception(
                "HTTP 403 Forbidden - Check if organization is active and onboarding is skipped. Run: curl -s -X POST 'http://127.0.0.1:8000/v1/onboarding/skip' -H 'Authorization: Bearer demo-token'"
            )
        elif "Connection" in error_msg or "refused" in error_msg.lower():
            raise Exception(
                "HTTP Connection Failed - API not running on port 8000. Start it with: faramesh serve"
            )
        else:
            raise Exception(f"API Error: {error_msg}\n{traceback.format_exc()}")


def main():
    print(f"\n{C.C}{C.BOLD}{'='*80}")
    print("  🤖 Interactive LLM Agent - Faramesh Governance")
    print(f"{'='*80}{C.END}\n")

    llm = build_llm()
    print(f"{C.G}✅ LLM initialized{C.END}")
    print(f"{C.Y}💡 Examples you can try:{C.END}")
    print(f"   • Count how many users are in the database")
    print(f"   • Process a payment of $250 for invoice #5678")
    print(f"   • Drop the old_data table")
    print(f"   • Run 'ls -la' command")
    print(f"   • Check disk space with df -h")
    print(f"\n{C.W}Type 'quit' or 'exit' to stop{C.END}\n")

    import requests

    while True:
        try:
            # Get user input
            prompt_text = input(f"{C.C}👤 You:{C.END} ").strip()

            if not prompt_text:
                continue

            if prompt_text.lower() in ["quit", "exit", "q"]:
                print(f"\n{C.G}👋 Goodbye!{C.END}\n")
                break

            print()  # Blank line for readability

            # Let LLM interpret the prompt and decide action
            print(f"{C.Y}🧠 LLM thinking...{C.END}")
            action_obj = llm_to_action(llm, prompt_text)

            # Send through governance
            result = send_action(action_obj)

            # Show what happened
            print(
                f"{C.W}🔧 Action:{C.END} {action_obj.get('tool')}.{action_obj.get('operation')}"
            )
            print(f"{C.W}📋 Params:{C.END} {action_obj.get('params')}")
            print(
                f"{C.W}⚖️  Decision:{C.END} {result.get('decision')} ({result.get('risk_level')} risk)"
            )

            status = result.get("status")
            if status == "denied":
                print(f"{C.R}❌ DENIED:{C.END} {result.get('reason')}")
            elif status == "allowed":
                print(f"{C.G}✅ ALLOWED:{C.END} {result.get('reason')}")
            elif status == "pending_approval":
                action_id = result.get("id")
                print(f"{C.Y}⏳ PENDING APPROVAL{C.END}")
                print(f"{C.Y}   Action ID: {action_id}{C.END}")
                print(f"{C.Y}   Go to http://localhost:3000 to approve/deny{C.END}")
                print(f"{C.Y}   Waiting...{C.END}")

                # Poll for approval
                while True:
                    time.sleep(3)
                    try:
                        check = requests.get(
                            f"http://localhost:8000/v1/actions/{action_id}"
                        )
                        if check.status_code == 200:
                            new_status = check.json().get("status")
                            if new_status != "pending_approval":
                                if new_status == "approved":
                                    print(f"{C.G}✅ APPROVED!{C.END}")
                                elif new_status == "rejected":
                                    print(f"{C.R}❌ REJECTED{C.END}")
                                else:
                                    print(f"{C.W}Status: {new_status}{C.END}")
                                break
                    except Exception:
                        pass

            print()  # Blank line before next prompt

        except KeyboardInterrupt:
            print(f"\n\n{C.Y}👋 Interrupted. Goodbye!{C.END}\n")
            break
        except Exception as e:
            print(f"{C.R}❌ Error: {e}{C.END}\n")


if __name__ == "__main__":
    main()
