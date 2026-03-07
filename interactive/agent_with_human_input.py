
#!/usr/bin/env python3
"""
Interactive AI Agent with Faramesh Governance
==============================================
Chat with an AI agent that can perform actions on your machine,
but all dangerous actions require your approval through the Faramesh UI.

The agent can:
📁 Create files and folders
🔍 Search Google in your browser
📦 Install Python packages
🗄️ Query databases
🌐 Make web requests
💻 Run shell commands

But before doing anything risky, it asks for permission! 🛡️

Usage:
    .venv-py313/bin/python demo_interactive_ai_agent.py
"""


import os
import sys
import time
import subprocess
import webbrowser
from typing import Dict, Any, Optional
from pathlib import Path

# Enhanced Claude Code-style terminal UI (rich, fallback to print/input)
import threading
import itertools
import sys as _sys
import time as _time
import select
import termios
import tty

import json
import stripe

# In-memory session state so prompts like “for that customer” work
STRIPE_SESSION = {
    "customer_id": None,
    "payment_intent_id": None,
    "connected_account_id": None,
    "allowlisted_destinations": set(),
}

# Map email -> acct_xxx for transfers to "that destination" / "john@test.com"
CONNECT_ACCOUNT_BY_EMAIL: Dict[str, str] = {}

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.box import ROUNDED
    from rich.align import Align
    from rich.style import Style
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    _console = Console(force_terminal=True, color_system="truecolor")
    _rich_enabled = True
except Exception as e:
    print("Rich disabled:", repr(e))
    _console = None
    _rich_enabled = False

# Web search and extraction deps
class FarameshTerminalUI:
    def __init__(self):
        self.console = _console
        self.placeholder = 'Try "how does <filepath> work?"'
        self.tip_text = 'You can use tools, e.g. "create a folder" or "search Google".'
        self.status_right = ''
        self._stop_cursor = threading.Event()

    def render_header(self, cwd: str):
        if not self.console:
            print(f"* Welcome to Faramesh Agent!")
            print("/help for help, /status for your current setup")
            print(f"cwd: {cwd}")
            return
        pink = Style(color="#ff69b4", bold=True)
        normal = Style()
        bold = Style(bold=True)
        dim = Style(dim=True)
        italic = Style(italic=True, dim=True, color="grey50")
        dim_grey = Style(dim=True, color="grey50")
        t = Text()
        t.append("* ", style=pink)
        t.append("Welcome to ", style=normal)
        t.append("Faramesh Agent!", style=bold)
        line2 = Text("/help for help, /status for your current setup", style=italic)
        line3 = Text(f"cwd: {cwd}", style=dim_grey)
        panel = Panel(
            Align.left(Text.assemble(t, "\n", line2, "\n", line3)),
            border_style=pink,
            box=ROUNDED,
            padding=(1,2),
        )
        self.console.print(panel)

    def render_tip(self, text: str):
        if not self.console:
            print(f"* Tip: {text}")
            return
        tip = Text("* ", style=Style(dim=True, color="grey50"))
        tip.append(f"Tip: {text}", style=Style(dim=True, color="grey50"))
        self.console.print(tip)

    def render_input(self, current_text: str, cursor_blink=True):
        if not self.console:
            prompt = current_text if current_text else self.placeholder
            print(f"> {prompt}", end="", flush=True)
            return
        width = self.console.size.width
        bar_text = Text("> ", style=Style(color="grey50"))
        if current_text:
            bar_text.append(current_text)
        else:
            bar_text.append(self.placeholder, style=Style(dim=True, color="grey50"))
        if cursor_blink:
            bar_text.append("█", style=Style(color="grey70"))
        panel = Panel(bar_text, box=ROUNDED, border_style=Style(color="grey70"), padding=(0,1), width=width-2)
        self.console.print(panel)

    def render_footer(self, left_lines, right_text):
        if not self.console:
            for l in left_lines:
                print(l)
            if right_text:
                print(right_text)
            return
        left = Text("\n".join(left_lines), style=Style(dim=True, color="grey50"))
        right = Text(right_text, style=Style(color="#ff69b4", bold=True))
        width = self.console.size.width
        pad = width - len(right.plain) - 2
        footer = Text()
        footer.append(left)
        footer.append(" " * max(2, pad - len(left.plain)))
        footer.append(right)
        self.console.print(footer)


    def _input_panel(self, current_text, cursor_blink):
        width = self.console.size.width
        bar_text = Text("> ", style=Style(color="grey50"))
        if current_text:
            bar_text.append(current_text)
        else:
            bar_text.append(self.placeholder, style=Style(dim=True, color="grey50"))
        if cursor_blink:
            bar_text.append("█", style=Style(color="grey70"))
        return Panel(bar_text, box=ROUNDED, border_style=Style(color="grey70"), padding=(0,1), width=width-2)

    def prompt_input(self) -> str:
        if not self.console:
            return input("> ")

        fd = _sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        buf = []
        blink = True
        last_blink = _time.time()

        # make sure panel width never goes negative
        def panel_for(text, cursor_on):
            w = max(30, self.console.size.width - 2)
            return self._input_panel(text, cursor_on) if w else self._input_panel(text, cursor_on)

        try:
            # cbreak = no echo, but still gives us characters immediately
            tty.setcbreak(fd)

            with Live(panel_for("", True), console=self.console, refresh_per_second=30, transient=False) as live:
                while True:
                    now = _time.time()
                    if now - last_blink >= 0.5:
                        blink = not blink
                        last_blink = now
                        live.update(panel_for("".join(buf), blink))

                    r, _, _ = select.select([_sys.stdin], [], [], 0.05)
                    if not r:
                        continue

                    ch = _sys.stdin.read(1)

                    # Enter
                    if ch in ("\r", "\n"):
                        break

                    # Ctrl-C
                    if ch == "\x03":
                        raise KeyboardInterrupt

                    # Backspace (mac + linux)
                    if ch in ("\x7f", "\b"):
                        if buf:
                            buf.pop()
                        live.update(panel_for("".join(buf), True))
                        continue

                    # Ignore escape sequences (arrows, etc.) for now
                    if ch == "\x1b":
                        # swallow the rest of the escape sequence if present
                        _sys.stdin.read(2) if select.select([_sys.stdin], [], [], 0.0)[0] else None
                        continue

                    # normal char
                    buf.append(ch)
                    live.update(panel_for("".join(buf), True))

            # after live closes, print a clean newline so output starts below the bar
            self.console.print()
            return "".join(buf).strip()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def animate_ai_response(self, text, delay=0.012):
        if not self.console:
            print(text)
            return
        # Just print the text (no per-character panel animation) to avoid flicker/misalignment
        self.console.print(text)

_faramesh_ui = FarameshTerminalUI() if _rich_enabled else None


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
    UNDERLINE = "\033[4m"

STRIPE_SESSION.setdefault("evidence", {})  # pi_id -> {action_id, fetched_at, pi_status, amount}


# LangChain OpenAI imports for NVIDIA nemotron via OpenRouter
# LangChain OpenAI imports for NVIDIA nemotron via OpenRouter
try:
    import httpx
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
except ImportError:
    print(f"{C.RED}❌ LangChain OpenAI integration not installed{C.END}")
    print("Install: pip install -U langchain langchain-openai httpx")
    sys.exit(1)
# Web search tool (Tavily)

# Web fetch + extract tool (Trafilatura)
@tool
def web_fetch(url: str) -> str:
    """Fetch a URL and return clean extracted text (for the model to read)."""
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded) if downloaded else None
    return (text or "")[:6000]  # keep it bounded

# Faramesh SDK
try:
    from faramesh import submit_action, get_action, report_result, configure
except ImportError:
    print(f"{C.RED}❌ Faramesh SDK not installed{C.END}")
    sys.exit(1)

# ==============================================================================
# Configuration
# ==============================================================================


def setup_faramesh():
    """Configure Faramesh + fetch OpenRouter key"""
    configure(
        base_url="http://127.0.0.1:8000",
        auth_token="demo-token",
        timeout=15.0,
    )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(f"{C.RED}❌ OPENROUTER_API_KEY not set{C.END}")
        sys.exit(1)

    print(f"{C.GREEN}✓ Faramesh configured{C.END}")
    print(f"{C.GREEN}✓ OpenRouter API key found{C.END}\n")
    return api_key

def setup_stripe():
    key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")
    if not key:
        print(f"{C.RED}❌ STRIPE_SECRET_KEY not set{C.END}")
        sys.exit(1)
    stripe.api_key = key
    _ensure_allowlist_file()
    print(f"{C.GREEN}✓ Stripe configured{C.END}")










def _usd_to_cents(x: float) -> int:
    return int(round(float(x) * 100.0))


def _evidence_fields(pi_id: str) -> dict:
    ev = STRIPE_SESSION["evidence"].get(pi_id)
    if not ev:
        return {"evidence_action_id": "", "evidence_age_sec": 10**9, "pi_status": "", "amount": 0}
    age = int(time.time() - ev["fetched_at"])
    return {
        "evidence_action_id": ev["action_id"],
        "evidence_age_sec": age,
        "pi_status": ev.get("pi_status", ""),
        "amount": int(ev.get("amount") or 0),
    }

def _require_fresh_evidence_for_money_move() -> dict:
    """
    For demo simplicity: require evidence from the *last retrieved PI*.
    This enforces: "you must call stripe_get_object(pi_...) first".
    """
    pi_id = STRIPE_SESSION.get("payment_intent_id") or ""
    if not pi_id:
        return {"ok": False, "reason": "Missing PaymentIntent evidence. Call stripe_get_object(pi_...) first."}

    ev = _evidence_fields(pi_id)
    if not ev["evidence_action_id"] or ev["evidence_age_sec"] > 600:
        return {"ok": False, "reason": "Evidence missing/stale. Call stripe_get_object(pi_...) again (within 10 min)."}
    return {"ok": True, "pi_id": pi_id, "ev": ev}


def _pretty(obj) -> str:
    try:
        if hasattr(obj, "to_dict_recursive"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                obj = obj.to_dict_recursive()
        elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            obj = obj.to_dict()
        return json.dumps(obj, indent=2, default=str)[:6000]
    except Exception:
        return str(obj)[:6000]

def _stripe_retrieve_any(object_id: str):
    # Common Stripe ID prefixes
    if object_id.startswith("cus_"):
        return stripe.Customer.retrieve(object_id)
    if object_id.startswith("pi_"):
        return stripe.PaymentIntent.retrieve(object_id)
    if object_id.startswith("ch_"):
        return stripe.Charge.retrieve(object_id)
    if object_id.startswith("re_"):
        return stripe.Refund.retrieve(object_id)
    if object_id.startswith("evt_"):
        return stripe.Event.retrieve(object_id)
    if object_id.startswith("acct_"):
        return stripe.Account.retrieve(object_id)
    if object_id.startswith("tr_"):
        return stripe.Transfer.retrieve(object_id)
    raise ValueError(f"Unsupported Stripe object id prefix: {object_id}")

@tool
def stripe_create_customer(email: str, name: str = "") -> str:
    """Create a Stripe Customer (email + optional name)."""
    try:
        action_id = submit_action(
            tool="stripe",
            operation="create_customer",
            params={"email": email, "name": name},
            agent_id="interactive-ai",
            context={"action_type": "stripe_create_customer"},
        )["id"]

        print(f"{C.CYAN}💳 Submitted: stripe_create_customer('{email}', name='{name}') → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_create_customer()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Stripe customer creation blocked: {result.get('reason', result['status'])}"

        cust = stripe.Customer.create(email=email, name=(name or None))
        STRIPE_SESSION["customer_id"] = cust["id"]
        STRIPE_SESSION["last_customer_email"] = (email or "").strip().lower()
        return f"✅ Created customer: {cust['id']}\n{_pretty(cust)}"
    except Exception as e:
        return f"Error: {e}"


@tool
def stripe_allowlist_destination(account_id: str, label: str = "") -> str:
    """
    Approve + label a destination account for transfers.
    This is the explicit “security team allowlisted vendor-bob” moment.
    """
    try:
        acct = account_id.replace("│", "").strip().split()[-1]
        if not acct or not acct.startswith("acct_"):
            return "❌ account_id must start with acct_"
        lbl = (label or "").strip()
        params = {"destination_account_id": acct, "label": lbl}

        dedupe_key = f"{acct}:{lbl}"
        now = time.time()
        last = _LAST_ALLOWLIST_SUBMIT
        if last.get("key") == dedupe_key and (now - last.get("submitted_at", 0)) < 120:
            aid = last.get("action_id")
            if aid:
                print(f"{C.CYAN}⏳ Reusing pending allowlist (do not retry){C.END}")
                res = wait_for_action_result(aid, "allowlist_destination()")
            else:
                aid = None
        else:
            aid = None

        if aid is None:
            action = submit_action(
                tool="stripe",
                operation="allowlist_destination",
                params=params,
                agent_id="interactive-ai",
                context={"action_type": "stripe_allowlist_destination"},
            )
            aid = action["id"]
            print(f"{C.CYAN}🧾 Submitted: allowlist_destination({acct}) → {aid[:8]}{C.END}")
            _LAST_ALLOWLIST_SUBMIT.update({"action_id": aid, "key": dedupe_key, "submitted_at": time.time()})
            res = wait_for_action_result(aid, "allowlist_destination()")

        if res["status"] in ("approved", "allowed", "completed", "denied", "failed"):
            _LAST_ALLOWLIST_SUBMIT.clear()
        if res["status"] in ("timeout", "error"):
            return "⏱ Still pending approval at http://127.0.0.1:8000. Approve/deny there, then tell me. Do NOT retry."
        if res["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Allowlist blocked: {res.get('reason', res['status'])}"

        data = _load_allowlist()
        entry = _get_allowlist_entry(acct)

        if entry:
            entry["approved"] = True
            if lbl:
                entry["label"] = lbl
        else:
            data.setdefault("destinations", []).append(
                {
                    "account_id": acct,
                    "label": lbl or acct,
                    "approved": True,
                    "added_at": int(time.time()),
                }
            )

        _save_allowlist(data)

        return f"✅ Allowlisted destination: {acct}\nlabel={_destination_label(acct)}\nDo NOT call this tool again for this account."
    except Exception as e:
        return f"Error: {e}"


@tool
def stripe_create_payment_intent(amount_usd: float, customer_id: str = "", currency: str = "usd", description: str = "") -> str:
    """Create + confirm a PaymentIntent for a customer (pm_card_visa) with optional description."""
    try:
        cid = customer_id.strip() or (STRIPE_SESSION["customer_id"] or "")
        if not cid:
            return "❌ Missing customer_id (create a customer first)."

        amount_cents = _usd_to_cents(amount_usd)

        action_id = submit_action(
            tool="stripe",
            operation="create_payment_intent",
            params={
                "amount_cents": amount_cents,
                "currency": currency,
                "customer_id": cid,
                "description": description,
                "confirm": True,
                "payment_method": "pm_card_visa",
            },
            agent_id="interactive-ai",
            context={"action_type": "stripe_create_payment_intent"},
        )["id"]

        print(f"{C.CYAN}💳 Submitted: stripe_create_payment_intent(${amount_usd}, {cid}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_create_payment_intent()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ PaymentIntent blocked: {result.get('reason', result['status'])}"

        pi = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            customer=cid,
            description=(description or None),
            payment_method="pm_card_visa",
            payment_method_types=["card"],
            confirm=True,
            off_session=True,
        )
        STRIPE_SESSION["payment_intent_id"] = pi["id"]
        return f"✅ Created PaymentIntent: {pi['id']} (status={pi.get('status')})\n{_pretty(pi)}"
    except Exception as e:
        return f"Error: {e}"

@tool
def stripe_get_object(object_id: str = "") -> str:
    """Retrieve a Stripe object by ID (cus_/pi_/ch_/re_/evt_/acct_/tr_) and cache it as evidence for refund policy."""
    try:
        oid = object_id.strip() or (STRIPE_SESSION["payment_intent_id"] or "")
        if not oid:
            return "❌ Missing object_id (provide one, or create a PaymentIntent first)."

        action_id = submit_action(
            tool="stripe",
            operation="get_object",
            params={"object_id": oid},
            agent_id="interactive-ai",
            context={"action_type": "stripe_get_object"},
        )["id"]

        print(f"{C.CYAN}🧾 Submitted: stripe_get_object({oid}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_get_object()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Retrieval blocked: {result.get('reason', result['status'])}"

        obj = _stripe_retrieve_any(oid)

        # cache evidence for PI only (refund policy needs these fields)
        if oid.startswith("pi_"):
            STRIPE_SESSION["payment_intent_id"] = oid
            STRIPE_SESSION.setdefault("evidence", {})
            STRIPE_SESSION["evidence"][oid] = {
                "action_id": action_id,
                "fetched_at": time.time(),
                "pi_status": obj.get("status", ""),
                "amount": obj.get("amount", 0),
            }

        return f"✅ Retrieved {oid}\n(evidence_action_id={action_id})\n{_pretty(obj)}"
    except Exception as e:
        return f"Error: {e}"


# Evidence considered fresh for 60 seconds (avoids redundant get_object in quick succession)
_EVIDENCE_FRESH_SEC = 60

# Dedupe: avoid submitting duplicate refund when LLM retries; reuse existing pending action
_LAST_REFUND_SUBMIT: Dict[str, Any] = {}  # {action_id, submitted_at, key}

# Dedupe: avoid submitting duplicate allowlist when LLM retries after approval
_LAST_ALLOWLIST_SUBMIT: Dict[str, Any] = {}  # {action_id, submitted_at, key}


@tool
def stripe_refund(payment_intent_id: str = "", amount_usd: float = 0.0, memo: str = "", ticket: str = "", break_glass_code: str = "") -> str:
    """Refund a PaymentIntent. Requires a ticket (e.g. 10492) and a description. For refunds > $250, requires break_glass_code."""
    try:
        # 1. Clean up ID (handles terminal junk/extra spaces)
        pi_id = payment_intent_id.replace("│", "").strip().split()[-1]
        if not pi_id or not pi_id.startswith("pi_"):
            pi_id = STRIPE_SESSION.get("payment_intent_id") or ""

        if not pi_id:
            return "❌ Missing payment_intent_id."

        # 2. Sync Status - only call get_object if evidence is missing or stale (>60s)
        ev = _evidence_fields(pi_id)
        if not ev["evidence_action_id"] or ev["evidence_age_sec"] > _EVIDENCE_FRESH_SEC:
            stripe_get_object.invoke({"object_id": pi_id})
            ev = _evidence_fields(pi_id)
        amount_cents = _usd_to_cents(amount_usd) if amount_usd > 0 else int(ev["amount"] or 0)

        # 3. Format Memo
        raw_memo = str(memo).replace("│", "").strip()
        raw_ticket = str(ticket).replace("│", "").strip()

        # Get digits for the ticket; default to 10492 if empty
        t_num = "".join(filter(str.isdigit, raw_ticket)) or "10492"
        clean_ticket = f"TICKET-{t_num}"

        # Clean the description text
        clean_desc = raw_memo.replace(clean_ticket, "").replace("TICKET-", "").strip(" -")
        if not clean_desc or len(clean_desc) < 3:
            clean_desc = "Customer requested refund"

        policy_memo = f"{clean_ticket} - {clean_desc}"

        # 4. Build params (currency must be present for payment_policy.yaml refund rules)
        # Omit empty optional params to avoid validate_action_params rejections
        params = {
            "payment_intent_id": pi_id,
            "amount": amount_cents,
            "memo": policy_memo,
            "currency": "usd",
            "pi_status": ev.get("pi_status", "") or "unknown",
        }
        ev_id = ev.get("evidence_action_id", "") or ""
        if ev_id:
            params["evidence_action_id"] = ev_id
        bg = (break_glass_code or "").strip()
        if bg:
            params["break_glass_code"] = bg

        if os.getenv("FARAMESH_DEBUG") == "1":
            print(f"[DEBUG] Refund params being sent:")
            print(f"  amount: {amount_cents} (${amount_cents/100})")
            print(f"  memo: '{policy_memo}'")
            print(f"  pi_status: '{ev['pi_status']}'")
            print(f"  evidence_action_id: '{ev['evidence_action_id']}'")
            print(f"  evidence_age_sec: {ev['evidence_age_sec']}")
            print(f"  break_glass_code: '{break_glass_code.strip()}'")
            print()

        # 5. Dedupe: if we submitted this exact refund recently, reuse that action (stops LLM retry loop)
        dedupe_key = f"{pi_id}:{amount_cents}:{policy_memo}"
        now = time.time()
        last = _LAST_REFUND_SUBMIT
        if last.get("key") == dedupe_key and (now - last.get("submitted_at", 0)) < 120:
            action_id = last.get("action_id")
            if action_id:
                print(f"{C.CYAN}⏳ Reusing pending refund (do not retry — awaiting approval){C.END}")
                result = wait_for_action_result(action_id, "stripe_refund")
            else:
                action_id = None
        else:
            action_id = None

        if action_id is None:
            print(f"{C.CYAN}📡 Submitting: {policy_memo} (${amount_cents/100}){C.END}")
            action = submit_action(
                tool="stripe",
                operation="refund_execute",
                params=params,
                agent_id="interactive-ai"
            )
            action_id = action["id"]
            _LAST_REFUND_SUBMIT.update({
                "action_id": action_id,
                "key": dedupe_key,
                "submitted_at": time.time(),
            })
            result = wait_for_action_result(action_id, "stripe_refund")

        # Clear dedupe cache on terminal status so future refunds can submit
        if result["status"] in ("approved", "allowed", "completed", "denied", "failed", "succeeded"):
            _LAST_REFUND_SUBMIT.clear()

        if result["status"] in ("timeout", "error"):
            url = result.get("approval_url", "http://127.0.0.1:8000")
            return (
                f"⏱ Refund is still pending your approval.\n"
                f"Go to {url} to approve or deny. Once you've decided, tell me.\n"
                f"Do NOT retry the refund - the same request is still in the queue."
            )
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Denied: {result.get('reason', 'Policy block')}"

        # 6. Finalize with Stripe
        re = stripe.Refund.create(
            payment_intent=pi_id,
            amount=amount_cents,
            metadata={"ticket": clean_ticket, "memo": clean_desc}
        )
        return f"✅ Refund successful: {re['id']}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
        
@tool
def stripe_list_recent_events(limit: int = 10) -> str:
    """List recent Stripe Events."""
    try:
        action_id = submit_action(
            tool="stripe",
            operation="list_recent_events",
            params={"limit": int(limit)},
            agent_id="interactive-ai",
            context={"action_type": "stripe_list_events"},
        )["id"]

        print(f"{C.CYAN}📜 Submitted: stripe_list_recent_events({limit}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_list_recent_events()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            if result["status"] == "denied":
                return f"❌ Events list blocked. Reason: {result.get('reason','Policy denied')}"
            return f"⚠️ Events list not completed: {result['status']}"

        ev = stripe.Event.list(limit=int(limit))
        # human-friendly summary + full payload (bounded)
        lines = []
        for e in ev.get("data", [])[:int(limit)]:
            lines.append(f"- {e.get('type')}  id={e.get('id')}  created={e.get('created')}")
        return "✅ Recent Stripe events:\n" + "\n".join(lines) + "\n\n" + _pretty(ev)
    except Exception as e:
        return f"Error: {e}"

@tool
def stripe_connect_create_account(email: str, country: str = "US", account_type: str = "express") -> str:
    """Create a Stripe Connect Account (NOT auto-allowlisted)."""
    try:
        action_id = submit_action(
            tool="stripe",
            operation="connect_create_account",
            params={"email": email, "country": country, "type": account_type},
            agent_id="interactive-ai",
            context={"action_type": "stripe_connect_create_account"},
        )["id"]

        print(f"{C.CYAN}🔗 Submitted: stripe_connect_create_account('{email}') → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_connect_create_account()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Connect account blocked: {result.get('reason', result['status'])}"

        acct = stripe.Account.create(type=account_type, country=country, email=email)
        STRIPE_SESSION["connected_account_id"] = acct["id"]
        DEST_CREATED_AT[acct["id"]] = time.time()
        CONNECT_ACCOUNT_BY_EMAIL[(email or "").strip().lower()] = acct["id"]


        # store as pending (not approved)
        data = _load_allowlist()
        existing = _get_allowlist_entry(acct["id"])
        if not existing:
            data.setdefault("destinations", []).append(
                {
                    "account_id": acct["id"],
                    "label": acct["id"],
                    "email": (email or "").strip().lower(),
                    "approved": False,
                    "added_at": int(time.time()),
                }
            )
            _save_allowlist(data)

        return f"✅ Connected account created: {acct['id']}\nStatus: pending allowlist approval\n{_pretty(acct)}"
    except Exception as e:
        return f"Error: {e}"


def _allowlist_path() -> Path:
    return Path(__file__).with_name("stripe_allowlist.json")


def _ensure_allowlist_file():
    p = _allowlist_path()
    if not p.exists():
        p.write_text(json.dumps({"destinations": []}, indent=2))


def _load_allowlist() -> dict:
    _ensure_allowlist_file()
    p = _allowlist_path()
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"destinations": []}


def _save_allowlist(data: dict):
    p = _allowlist_path()
    p.write_text(json.dumps(data, indent=2))


def _get_allowlist_entry(acct_id: str) -> Optional[dict]:
    data = _load_allowlist()
    for d in data.get("destinations", []):
        if d.get("account_id") == acct_id:
            return d
    return None


def _is_allowlisted_destination(acct_id: str) -> bool:
    entry = _get_allowlist_entry(acct_id)
    return bool(entry and entry.get("approved") is True)


def _destination_label(acct_id: str) -> str:
    entry = _get_allowlist_entry(acct_id)
    if entry and entry.get("label"):
        return entry["label"]
    return acct_id


def _resolve_destination(dest_input: str) -> str:
    """Resolve destination_id, label (vendor-bob), or email (john@test.com) to account_id."""
    s = (dest_input or "").strip()
    if not s:
        return ""
    if s.startswith("acct_"):
        return s
    lower = s.lower()
    if "@" in s:
        acct = CONNECT_ACCOUNT_BY_EMAIL.get(lower)
        if acct:
            return acct
    data = _load_allowlist()
    for d in data.get("destinations", []):
        if d.get("approved") and (
            (d.get("label") or "").lower() == lower or (d.get("email") or "").lower() == lower
        ):
            return d.get("account_id", "")
    return s


DEST_CREATED_AT: Dict[str, float] = {}

def _destination_age_sec(acct_id: str) -> int:
    created = DEST_CREATED_AT.get(acct_id)
    if not created:
        return 0
    return int(time.time() - created)



@tool
def stripe_create_invoice(customer_id: str, amount_usd: float, description: str = "") -> str:
    """Create a Stripe Invoice (gated via Faramesh)."""
    try:
        amount_cents = _usd_to_cents(amount_usd)
        action_id = submit_action(
            tool="stripe",
            operation="create_invoice",
            params={
                "customer_id": customer_id,
                "amount_cents": amount_cents,
                "description": description,
            },
            agent_id="interactive-ai",
            context={"action_type": "stripe_create_invoice"},
        )["id"]

        print(f"{C.CYAN}🧾 Submitted: create_invoice({customer_id}, ${amount_usd}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_create_invoice()")
        if result["status"] in ("timeout", "error"):
            return "⏱ Invoice creation still pending approval at http://127.0.0.1:8000. Approve/deny there, then tell me. Do NOT retry."
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Invoice creation blocked: {result.get('reason', result['status'])}"

        inv = stripe.Invoice.create(customer=customer_id, description=description, auto_advance=True)
        return f"✅ Invoice created: {inv['id']}\n{_pretty(inv)}"
    except Exception as e:
        return f"Error: {e}"


@tool
def stripe_transfer_test(amount_usd: float, destination_id: str = "", currency: str = "usd", memo: str = "", ticket: str = "", break_glass_code: str = "") -> str:
    """
    Transfer funds to a destination. Call this first - policy denies if destination not allowlisted.
    destination_id can be acct_xxx or a label (e.g. vendor-bob for allowlisted accounts).
    """
    try:
        raw = (destination_id or "").strip()
        dest = _resolve_destination(raw) or raw or STRIPE_SESSION.get("connected_account_id", "")
        if not dest.startswith("acct_") and STRIPE_SESSION.get("connected_account_id"):
            if not raw or "that" in raw.lower() or "the" in raw.lower() or "this" in raw.lower():
                dest = STRIPE_SESSION["connected_account_id"]
        if not dest or not dest.startswith("acct_"):
            return "❌ Missing or invalid destination_id. Use acct_xxx, an allowlisted label, or an email we created a Connect account for."

        if currency.lower() != "usd":
            return "❌ Demo only supports USD."

        amount_cents = _usd_to_cents(amount_usd)

        # Evidence gating
        ev_check = _require_fresh_evidence_for_money_move()
        if not ev_check["ok"]:
            return f"❌ Transfer blocked: {ev_check['reason']}"
        ev = ev_check["ev"]

        # Allowlist + label (submit to Faramesh even when not allowlisted; policy will deny)
        destination_allowlisted = _is_allowlisted_destination(dest)
        destination_label = _destination_label(dest)
        destination_age_sec = _destination_age_sec(dest)

        # Format memo
        raw_memo = str(memo).replace("│", "").strip()
        raw_ticket = str(ticket).replace("│", "").strip()
        t_num = "".join(filter(str.isdigit, raw_ticket)) or "10492"
        clean_ticket = f"TICKET-{t_num}"
        clean_desc = raw_memo.replace(clean_ticket, "").replace("TICKET-", "").strip(" -")
        if not clean_desc or len(clean_desc) < 3:
            clean_desc = "Transfer approved"
        policy_memo = f"{clean_ticket} - {clean_desc}"

        # Velocity snapshot (policy also checks; we only block locally for allowlisted dests)
        snap = _velocity_snapshot(dest)
        daily_total_cap = 100_000   # $1,000
        daily_dest_cap = 50_000     # $500

        if destination_allowlisted:
            if snap["total_cents_today"] + amount_cents > daily_total_cap:
                return f"❌ Transfer blocked: daily total cap exceeded (${daily_total_cap/100})"
            if snap["dest_cents_today"] + amount_cents > daily_dest_cap:
                return f"❌ Transfer blocked: daily cap for {destination_label} exceeded (${daily_dest_cap/100})"

        # Build params
        params = {
            "amount": amount_cents,
            "currency": currency.lower(),
            "destination_account_id": dest,
            "destination_allowlisted": destination_allowlisted,
            "destination_label": destination_label,
            "destination_age_sec": destination_age_sec,
            "evidence_action_id": ev["evidence_action_id"],
            "evidence_age_sec": ev["evidence_age_sec"],
            "pi_status": ev["pi_status"],
            "memo": policy_memo,
            "ticket": clean_ticket,
            "break_glass_code": break_glass_code.strip(),
            "daily_total_cents_today": snap["total_cents_today"],
            "daily_dest_cents_today": snap["dest_cents_today"],
            "daily_total_cap_cents": daily_total_cap,
            "daily_dest_cap_cents": daily_dest_cap,
        }

        # Single-step execution
        print(f"{C.CYAN}💸 Submitting: transfer_execute → {policy_memo} (${amount_cents/100}){C.END}")
        
        exec_id = submit_action(
            tool="stripe",
            operation="transfer_execute",
            params=params,
            agent_id="interactive-ai",
            context={"action_type": "stripe_transfer"}
        )
        
        exec_res = wait_for_action_result(exec_id["id"], "transfer_execute")
        if exec_res["status"] in ("timeout", "error"):
            return "⏱ Transfer still pending approval at http://127.0.0.1:8000. Approve/deny there, then tell me. Do NOT retry."
        if exec_res["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Transfer blocked: {exec_res.get('reason', exec_res['status'])}"

        # Create Stripe Transfer
        tr = stripe.Transfer.create(
            amount=amount_cents,
            currency=currency.lower(),
            destination=dest,
            metadata={
                "memo": clean_desc,
                "ticket": clean_ticket,
                "break_glass_code": break_glass_code.strip(),
                "destination_label": destination_label,
            }
        )

        _record_transfer(dest, amount_cents)

        return f"✅ Transfer created: {tr['id']}\nDestination={destination_label}\n{_pretty(tr)}"

    except Exception as e:
        return f"❌ Error: {str(e)}"



def wait_for_action_result(action_id: str, operation_name: str) -> Dict[str, Any]:
    """
    Wait for action to complete, handling approvals interactively.
    Returns the final status.
    """
    approval_url = "http://127.0.0.1:8000"
    shown_pending_message = False
    consecutive_failures = 0
    max_consecutive_failures = 5

    for attempt in range(120):  # 2 minutes max
        time.sleep(1)

        try:
            action_data = get_action(action_id)
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"\n{C.RED}❌ Polling failed: {e}{C.END}\n")
                return {"status": "error", "reason": str(e), "approval_url": approval_url}
            if attempt % 5 == 4:
                print(f"   {C.YELLOW}(poll {attempt + 1}: retrying after error){C.END}")
            continue

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

        elif status == "allowed":
            return {"status": "allowed", "data": action_data}

        elif status in ("approved", "completed", "succeeded"):
            if shown_pending_message:
                print(f"\n{C.GREEN}✅ APPROVED! Continuing...{C.END}\n")
            return {"status": "approved", "data": action_data}

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

    # Timeout
    print(f"\n{C.YELLOW}⏱ Timeout (2 min) waiting for approval.{C.END}")
    print(f"   The action is still pending at {approval_url}")
    print(f"   {C.BOLD}Please approve or deny there, then tell me when done.{C.END}")
    print(f"   {C.YELLOW}Do NOT retry this action - it is still in the queue.{C.END}\n")
    return {"status": "timeout", "approval_url": approval_url}


# ==============================================================================
# Governed Tools
# ==============================================================================


@tool
def create_files(folder_name: str, num_files: int = 10) -> str:
    """
    Create a folder with multiple text files.

    Args:
        folder_name: Name of the folder to create
        num_files: Number of .txt files to create (default: 10)
    """
    try:
        action_id = submit_action(
            tool="filesystem",
            operation="batch_create",
            params={
                "folder": folder_name,
                "num_files": num_files,
                "location": "demo-folder",
            },
            agent_id="interactive-ai",
            context={"action_type": "file_creation"},
        )["id"]

        print(
            f"{C.CYAN}📝 Submitted: Create folder with {num_files} files → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"create_files({folder_name})")

        if result["status"] in ["completed", "approved", "allowed"]:
            return f"✅ Successfully created folder '{folder_name}' with {num_files} .txt files!"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ I can't create files right now. Reason: {reason}"
        else:
            return f"⚠️ Action couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


# ============================
# Additional Stripe Tools
# ============================

@tool
def stripe_search_customer(email: str = "", limit: int = 5) -> str:
    """Search Stripe customers by email (read-only). Requires email parameter."""
    try:
        email = (email or "").strip().lower() or STRIPE_SESSION.get("last_customer_email", "")
        if not email:
            return "❌ Missing email. Pass the customer email to search for (e.g. leslie@test.com)."

        # read-only action record
        action_id = submit_action(
            tool="stripe",
            operation="search_customer",
            params={"email": email, "limit": limit},
            agent_id="interactive-ai",
            context={"action_type": "stripe_search_customer", "read_only": True},
        )["id"]
        print(f"{C.CYAN}🔎 Submitted: stripe_search_customer('{email}') → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_search_customer()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Search blocked: {result.get('reason', result['status'])}"

        res = stripe.Customer.list(email=email, limit=int(limit))
        customers = res.get("data", [])

        if not customers:
            return f"✅ No customers found for {email}"

        lines = [f"✅ Found {len(customers)} customer(s) for {email}:"]
        for c in customers:
            lines.append(f"- {c['id']} | name={c.get('name','')} | email={c.get('email','')}")
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"



@tool
def stripe_list_transfers(limit: int = 5) -> str:
    """List recent Stripe transfers (read-only)."""
    try:
        limit = int(limit)

        action_id = submit_action(
            tool="stripe",
            operation="list_transfers",
            params={"limit": limit},
            agent_id="interactive-ai",
            context={"action_type": "stripe_list_transfers", "read_only": True},
        )["id"]
        print(f"{C.CYAN}📤 Submitted: stripe_list_transfers({limit}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_list_transfers()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ List blocked: {result.get('reason', result['status'])}"

        res = stripe.Transfer.list(limit=limit)
        data = res.get("data", [])
        if not data:
            return "✅ No transfers found."

        lines = [f"✅ Recent transfers ({len(data)}):"]
        for t in data:
            amt = (t["amount"] or 0) / 100
            lines.append(f"- {t['id']} | ${amt:.2f} {t.get('currency','').upper()} | dest={t.get('destination','')}")
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"




@tool
def stripe_list_refunds(limit: int = 5) -> str:
    """List recent Stripe refunds (read-only)."""
    try:
        limit = int(limit)

        action_id = submit_action(
            tool="stripe",
            operation="list_refunds",
            params={"limit": limit},
            agent_id="interactive-ai",
            context={"action_type": "stripe_list_refunds", "read_only": True},
        )["id"]
        print(f"{C.CYAN}↩️ Submitted: stripe_list_refunds({limit}) → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_list_refunds()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ List blocked: {result.get('reason', result['status'])}"

        res = stripe.Refund.list(limit=limit)
        data = res.get("data", [])
        if not data:
            return "✅ No refunds found."

        lines = [f"✅ Recent refunds ({len(data)}):"]
        for r in data:
            amt = (r["amount"] or 0) / 100
            lines.append(f"- {r['id']} | ${amt:.2f} {r.get('currency','').upper()} | status={r.get('status','')}")
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"




@tool
def stripe_get_balance() -> str:
    """Get Stripe balance (read-only)."""
    try:
        action_id = submit_action(
            tool="stripe",
            operation="get_balance",
            params={},
            agent_id="interactive-ai",
            context={"action_type": "stripe_get_balance", "read_only": True},
        )["id"]
        print(f"{C.CYAN}🏦 Submitted: stripe_get_balance() → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "stripe_get_balance()")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Balance blocked: {result.get('reason', result['status'])}"

        bal = stripe.Balance.retrieve()
        return f"✅ Balance:\n{_pretty(bal)}"

    except Exception as e:
        return f"Error: {e}"

# ============================
# End of Additional Stripe Tools
# ============================


@tool
def search_google(keyword: str) -> str:
    """
    Search Google for a keyword in the default browser.

    Args:
        keyword: The search term
    """
    try:
        action_id = submit_action(
            tool="browser",
            operation="search",
            params={"query": keyword, "engine": "google"},
            agent_id="interactive-ai",
            context={"action_type": "browser_search"},
        )["id"]

        print(
            f"{C.CYAN}🔍 Submitted: Search Google for '{keyword}' → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"search_google({keyword})")

        if result["status"] in ["completed", "approved", "allowed"]:
            # Actually open the browser
            url = f"https://www.google.com/search?q={keyword}"
            webbrowser.open(url)
            return f"✅ Opened Google search for '{keyword}' in your browser!"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ I can't search right now. Reason: {reason}"
        else:
            return f"⚠️ Search couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


@tool
def install_package(package_name: str) -> str:
    """
    Install a Python package using pip.

    Args:
        package_name: Name of the package to install
    """
    try:
        action_id = submit_action(
            tool="pip",
            operation="install",
            params={"package": package_name},
            agent_id="interactive-ai",
            context={"action_type": "package_install"},
        )["id"]

        print(
            f"{C.CYAN}📦 Submitted: Install package '{package_name}' → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"install_package({package_name})")

        if result["status"] in ["completed", "approved", "allowed"]:
            return f"✅ Package '{package_name}' installation approved!"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ Can't install package. Reason: {reason}"
        else:
            return f"⚠️ Installation couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


@tool
def query_database(query: str) -> str:
    """
    Query a database (safe read-only operation).

    Args:
        query: The SQL query to execute
    """
    try:
        action_id = submit_action(
            tool="database",
            operation="read",
            params={"query": query},
            agent_id="interactive-ai",
            context={"action_type": "db_query"},
        )["id"]

        print(f"{C.CYAN}🗄️  Submitted: Database query → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, "query_database()")

        if result["status"] in ["completed", "approved", "allowed"]:
            return "✅ Database query executed successfully!"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ Query blocked. Reason: {reason}"
        else:
            return f"⚠️ Query couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


@tool
def make_web_request(url: str, method: str = "GET") -> str:
    """
    Make an HTTP request to a URL.

    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
    """
    try:
        action_id = submit_action(
            tool="http",
            operation=method.lower(),
            params={"url": url},
            agent_id="interactive-ai",
            context={"action_type": "web_request"},
        )["id"]

        print(f"{C.CYAN}🌐 Submitted: {method} {url} → {action_id[:8]}{C.END}")
        result = wait_for_action_result(action_id, f"make_web_request({url})")

        if result["status"] in ["completed", "approved", "allowed"]:
            return f"✅ Web request to {url} completed!"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ Request blocked. Reason: {reason}"
        else:
            return f"⚠️ Request couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


"""
Interactive AI Agent with Faramesh Governance
==============================================
Chat with an AI agent that can perform actions on your machine,
but all dangerous actions require your approval through the Faramesh UI.

The agent can:
📁 Create files and folders
🔍 Search Google in your browser
📦 Install Python packages
🗄️ Query databases
🌐 Make web requests
💻 Run shell commands

But before doing anything risky, it asks for permission! 🛡️

Usage:
    OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE" \
    .venv-py313/bin/python demo_interactive_ai_agent.py
"""


@tool
def run_shell_command(command: str) -> str:
    """
    Execute a shell command.

    Args:
        command: The shell command to run (e.g., 'ls', 'pwd', etc.)
    """
    try:
        action_id = submit_action(
            tool="shell",
            operation="execute",
            params={"cmd": command},
            agent_id="interactive-ai",
            context={"action_type": "shell_command"},
        )["id"]

        print(
            f"{C.CYAN}💻 Submitted: Shell command '{command}' → {action_id[:8]}{C.END}"
        )
        result = wait_for_action_result(action_id, f"run_shell_command({command})")

        if result["status"] in ["completed", "approved", "allowed"]:
            # Actually run the command
            try:
                proc = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=os.getcwd(),
                )
                output = proc.stdout if proc.stdout else proc.stderr
                if output:
                    return f"✅ Command executed successfully:\n{output[:500]}"
                else:
                    return f"✅ Command '{command}' executed (no output)"
            except subprocess.TimeoutExpired:
                return f"⚠️ Command timed out after 10 seconds"
            except Exception as e:
                return f"⚠️ Command approved but execution failed: {str(e)}"
        elif result["status"] == "denied":
            reason = result.get("reason", "Policy blocked this action")
            return f"❌ Command blocked. Reason: {reason}"
        else:
            return f"⚠️ Command couldn't be completed: {result['status']}"

    except Exception as e:
        return f"Error: {str(e)}"


# ==============================================================================
# Agent Setup
# ==============================================================================



def create_ai_agent(api_key: str):
    """Create the interactive AI agent (OpenRouter -> nvidia/nemotron-3-nano-30b-a3b:free)"""

    headers = {
        "HTTP-Referer": "http://localhost",
        "X-Title": "Faramesh Interactive Agent",
    }

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        http_client=httpx.Client(headers=headers),
    )

    tools = [
        create_files,
        search_google,
        install_package,
        query_database,
        make_web_request,
        run_shell_command,
        stripe_create_customer,
        stripe_create_payment_intent,
        stripe_get_object,
        stripe_refund,
        stripe_list_recent_events,
        stripe_connect_create_account,
        stripe_transfer_test,
        stripe_search_customer,
        stripe_list_transfers,
        stripe_list_refunds,
        stripe_get_balance,
        stripe_allowlist_destination,
        stripe_create_invoice,
    ]
    llm_with_tools = llm.bind_tools(tools)
    return llm_with_tools, tools

def run_interactive_chat(llm_with_tools, tools):
    """Run the interactive chat loop (multi-step, continuous tool use)"""
    chat_history = []
    system_prompt = """You are a helpful AI assistant with access to system tools. You're chatting with a user who can see everything you do.

🎯 IMPORTANT BEHAVIOR:
1. When the user asks you to do something, USE THE TOOL immediately
2. After using a tool, comment on the result
3. If an action is DENIED, acknowledge it and either:
   - Try an alternative approach
   - Ask the user what they'd like to do instead
   - Continue with other tasks from their request
4. NEVER stop or give up just because one action was denied!
5. Keep the conversation flowing naturally
6. If a tool returns "still pending approval" or "Do NOT retry" - STOP. Tell the user to go to the UI to approve, and wait for them to say they've done it. Do NOT call the same tool again.
7. TRANSFERS: ALWAYS call stripe_transfer_test immediately when the user asks to transfer. NEVER ask "would you like me to allowlist first" - just call the tool. For acct_FAKE or unallowlisted destinations, the policy will deny; report that to the user. Only call stripe_allowlist_destination when the user explicitly says "allowlist" or "approve that destination".
8. ALLOWLIST: Call stripe_allowlist_destination only when user explicitly asks to allowlist. After it returns success, do NOT call it again for that account.
9. "That destination" = the most recent connected account (STRIPE_SESSION). "john@test.com" = resolve to that account if we created it.

🔒 SECURITY:
- Some actions execute immediately (safe operations)
- Some need approval (creating files, web searches, installing packages)
- Some are always blocked (dangerous operations like rm -rf)
- When approval is needed, the system WAITS - you'll see the result after the user approves/denies

🛠️ Available tools:
- create_files(folder_name, num_files): Create a folder with text files
- search_google(keyword): Open Google search in browser
- install_package(package_name): Install Python package via pip
- query_database(query): Run read-only database queries
- make_web_request(url, method): Make HTTP requests
- run_shell_command(command): Execute shell commands (ls, cat, pwd, etc.)
- web_search(query, max_results): Search the web and return top results
- web_fetch(url): Fetch a URL and return clean extracted text

Stripe tools:
- stripe_create_customer(email)
- stripe_create_payment_intent(amount_usd, customer_id?, currency?)
- stripe_get_object(object_id?)
- stripe_refund(payment_intent_id?, amount_usd?, memo?, ticket?)
- stripe_list_recent_events(limit?)
- stripe_connect_create_account(email, country?, account_type?)
- stripe_transfer_test(amount_usd, destination_id, memo?, ticket?, break_glass_code?) — Call FIRST for transfers. Destination can be acct_xxx or label like vendor-bob. Policy denies if not allowlisted.
- stripe_allowlist_destination(account_id, label?) — Only when user explicitly asks to allowlist. Do NOT retry after success.

Be conversational, helpful, and respectful of security decisions!"""

    cwd = os.getcwd()
    if _faramesh_ui:
        _faramesh_ui.render_header(cwd)
        _faramesh_ui.render_tip('You can use tools, e.g. "create a folder" or "search Google".')
    else:
        print(f"* Welcome to Faramesh Agent!")
        print("/help for help, /status for your current setup")
        print(f"cwd: {cwd}")
        print()
        print(f"* Tip: You can use tools, e.g. 'create a folder' or 'search Google'.")

    while True:
        try:
            if _faramesh_ui:
                user_input = _faramesh_ui.prompt_input().strip()
            else:
                user_input = input(f"You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                if _faramesh_ui:
                    print("\n👋 Goodbye!\n")
                else:
                    print(f"\n{C.CYAN}👋 Goodbye!{C.END}\n")
                break

            if user_input.lower() == "test":
                run_test_scenarios(llm_with_tools, tools)
                continue

            if _faramesh_ui:
                print("\nAI:", end=" ", flush=True)
            else:
                print(f"\n{C.BLUE}AI: {C.END}", end="", flush=True)


            # Multi-step tool loop
            messages = [SystemMessage(content=system_prompt), *chat_history, HumanMessage(content=user_input)]
            for _ in range(12):
                if _faramesh_ui and _faramesh_ui.console:
                    with Progress(SpinnerColumn(style="pink3"), TextColumn("[progress.description]Thinking..."), transient=True) as progress:
                        task = progress.add_task("Thinking...", total=None)
                        resp = llm_with_tools.invoke(messages)
                        progress.remove_task(task)
                else:
                    resp = llm_with_tools.invoke(messages)

                if not getattr(resp, "tool_calls", None):
                    if _faramesh_ui:
                        _faramesh_ui.animate_ai_response(resp.content)
                    else:
                        print(resp.content)
                    break

                for tc in resp.tool_calls:
                    tool_func = next((t for t in tools if t.name == tc["name"]), None)
                    if tool_func:
                        args = tc.get("args", {})
                        # If the tool expects a single argument (like run_shell_command), pass as positional if needed
                        try:
                            out = tool_func.invoke(args)
                        except TypeError:
                            # fallback: try unpacking if args is a dict
                            if isinstance(args, dict):
                                out = tool_func.invoke(**args)
                            else:
                                out = tool_func.invoke(args)
                        messages.append(ToolMessage(content=str(out), tool_call_id=tc["id"]))

            print()

            # Update chat history
            chat_history.append(HumanMessage(content=user_input))
            # Only add the last AI message (not intermediate tool messages)
            if 'resp' in locals():
                chat_history.append(AIMessage(content=resp.content if resp.content else str(resp)))
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

            if _faramesh_ui:
                left = ["? for", "shortcuts"]
                right = "✕ Guard update is not initiated · Try faramesh doctor or pip install -U faramesh"
                _faramesh_ui.render_footer(left, right)

        except KeyboardInterrupt:
            if _faramesh_ui:
                print("\nInterrupted. Type 'quit' to exit.\n")
            else:
                print(f"\n\n{C.YELLOW}Interrupted. Type 'quit' to exit.{C.END}\n")
        except Exception as e:
            if _faramesh_ui:
                print(f"\nError: {e}\n")
            else:
                print(f"\n{C.RED}Error: {e}{C.END}\n")
                print(f"\n\n{C.YELLOW}Interrupted. Type 'quit' to exit.{C.END}\n")
        except Exception as e:
            if _faramesh_ui:
                print(f"\nError: {e}\n")
            else:
                print(f"\n{C.RED}Error: {e}{C.END}\n")


def _velocity_path() -> Path:
    return Path(__file__).with_name("stripe_velocity.json")


def _load_velocity() -> dict:
    p = _velocity_path()
    if not p.exists():
        return {"day": "", "total_cents": 0, "by_destination": {}}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"day": "", "total_cents": 0, "by_destination": {}}


def _save_velocity(v: dict):
    _velocity_path().write_text(json.dumps(v, indent=2))


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _velocity_snapshot(acct_id: str) -> dict:
    """
    Return a demo snapshot with all limits essentially ignored,
    so the demo can run in <60s without hitting first-time destination or daily caps.
    """
    return {
        "total_cents_today": 0,
        "dest_cents_today": 0,
        "daily_total_cap_cents": 10**9,
        "daily_dest_cap_cents": 10**9,
        "destination_age_sec": 0,  # immediately allow new destination
    }

def _record_transfer(destination_id: str, amount_cents: int):
    """Update velocity snapshot after a successful transfer (in-memory)."""
    STRIPE_SESSION.setdefault("_velocity_state", {"total_cents_today": 0, "per_dest": {}})
    state = STRIPE_SESSION["_velocity_state"]
    state["total_cents_today"] += int(amount_cents)
    state["per_dest"][destination_id] = state["per_dest"].get(destination_id, 0) + int(amount_cents)



def _velocity_commit(destination_id: str, amount_cents: int):
    v = _load_velocity()
    today = _today_key()
    if v.get("day") != today:
        v = {"day": today, "total_cents": 0, "by_destination": {}}

    v["total_cents"] = int(v.get("total_cents") or 0) + int(amount_cents)
    v.setdefault("by_destination", {})
    v["by_destination"][destination_id] = int(v["by_destination"].get(destination_id) or 0) + int(amount_cents)

    _save_velocity(v)



def run_test_scenarios(llm_with_tools, tools):
    """Run automated test scenarios"""

    print(f"\n{C.HEADER}{'='*70}{C.END}")
    print(f"{C.HEADER}{'Running Automated Test Scenarios':^70}{C.END}")
    print(f"{C.HEADER}{'='*70}{C.END}\n")

    test_prompts = [
        "Create a folder called 'test_folder' with 5 text files in it",
        "Query the database to check how many actions we have",
        "Search Google for 'faramesh governance'",
        "Run the 'ls demo-folder' command to see what's in that directory",
        "Install the 'requests' Python package",
        "Make a web request to https://api.github.com/repos/python/cpython",
        "Try to run 'rm -rf test_folder' to delete the folder we created",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(
            f"\n{C.CYAN}[Test {i}/{len(test_prompts)}]{C.END} {C.BOLD}{prompt}{C.END}\n"
        )

        try:
            messages = [HumanMessage(content=prompt)]
            response = llm_with_tools.invoke(messages)

            # Handle tool calls if present
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    tool_func = next((t for t in tools if t.name == tool_name), None)
                    if tool_func:
                        result = tool_func.invoke(tool_args)
                        print(f"{C.BLUE}Result: {result}{C.END}\n")
            else:
                print(f"{C.BLUE}Result: {response.content}{C.END}\n")

        except Exception as e:
            print(f"{C.RED}Error: {e}{C.END}\n")

        time.sleep(2)

    print(f"\n{C.GREEN}✓ All test scenarios completed!{C.END}\n")


# ==============================================================================
# Policy Management
# ==============================================================================


# Policy management removed - use Faramesh CLI instead:
#   cd faramesh-horizon-code
#   .venv/bin/python -m faramesh.cli_activate demo_policy.yaml
#   .venv/bin/python -m faramesh.cli_activate strict_policy_v2.yaml


# ==============================================================================
# Main
# ==============================================================================


def main():
    """Main entry point"""

    print(f"\n{C.BOLD}{C.HEADER}Faramesh Interactive AI Agent{C.END}\n")
    print(f"{C.CYAN}🔒 Testing Faramesh Action Authorization Boundary (AAB){C.END}\n")

    print(f"{C.YELLOW}⚠️  Policy activated: payment_policy.yaml (via start_demo.sh){C.END}")
    print(
        f"{C.YELLOW}   Policy enforcement is EXTERNAL to AI - non-bypassable{C.END}\n"
    )

    # Setup
    api_key = setup_faramesh()
    setup_stripe()

    # Create agent
    print(f"{C.CYAN}Creating AI agent...{C.END}")
    llm_with_tools, tools = create_ai_agent(api_key)
    print(f"{C.GREEN}✓ Agent ready!{C.END}\n")

    # Run interactive chat
    run_interactive_chat(llm_with_tools, tools)


if __name__ == "__main__":
    main()
