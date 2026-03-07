#!/usr/bin/env python3
"""
RefundBot — DTC Ecommerce AI Agent with Faramesh Governance
============================================================
Autonomous AI customer service agent for handling refund requests.
All refund operations are governed by Faramesh policy before execution.

Usage:
    SHOPIFY_ACCESS_TOKEN=... SHOPIFY_STORE_DOMAIN=... OPENROUTER_API_KEY=... \
    python demo_ecom_agent.py
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
import uuid
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# faramesh is resolved via _add_faramesh_src() above
_script_dir = Path(__file__).resolve().parent

try:
    import httpx
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
except ImportError:
    print("\033[91m❌ LangChain/OpenAI not installed. pip install langchain langchain-openai httpx\033[0m")
    sys.exit(1)

try:
    from faramesh import submit_action, get_action, configure
except ImportError:
    print("\033[91m❌ Faramesh SDK not installed. git clone https://github.com/faramesh/faramesh-core.git && pip install -e ./faramesh-core\033[0m")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.box import ROUNDED
    from rich.align import Align
    from rich.style import Style
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import threading
    import sys as _sys
    import select
    import termios
    import tty
    _console = Console(force_terminal=True, color_system="truecolor")
    _rich_enabled = True
except Exception:
    _console = None
    _rich_enabled = False

# In-memory session for evidence cache
SHOPIFY_SESSION: Dict[str, Any] = {
    "evidence": {},
    "last_order_id": None,
}

# Demo orders
DEMO_ORDERS = [
    {"id": "11943318520173", "amount": 84.85, "expected": "APPROVE"},
    {"id": "11943323697517", "amount": 274.60, "expected": "REQUIRE"},
    {"id": "11943319929197", "amount": 3160.90, "expected": "BLOCK"},
]

# Color codes
class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    END = "\033[0m"
    BOLD = "\033[1m"


# =============================================================================
# RefundBot Terminal UI (OpenClaw-style layout)
# =============================================================================
# Layout: Header | Chat log | Status line | Input | Footer
# - Header: connection + agent + session
# - Tool output: cards with args + results
# - Footer: agent | session | /help /status /exit
# =============================================================================

TEAL = "#00b4d8"

class RefundBotTerminalUI:
    def __init__(self):
        self.console = _console
        self.placeholder = "Type a message..."
        self.store_domain = os.getenv("SHOPIFY_STORE_DOMAIN", "—")
        self.status = "idle"  # idle | thinking | streaming | tool | error
        self.agent = "refundbot"
        self.session = "main"

    def render_header(self):
        if not self.console:
            print("\n  RefundBot | faramesh | DTC Refund Protection\n")
            return
        w = self.console.size.width
        header = Text()
        header.append("  ", style="dim")
        header.append("RefundBot", style=Style(color=TEAL, bold=True))
        header.append(" │ ", style="dim")
        header.append(self.store_domain, style="dim")
        header.append(" │ ", style="dim")
        header.append("Faramesh", style="green")
        header.append(" │ ", style="dim")
        header.append(f"agent:{self.agent}", style="dim")
        header.append(" │ ", style="dim")
        header.append(f"session:{self.session}", style="dim")
        self.console.print(Text.from_markup(f"[dim]┌{'─' * (w-2)}┐[/dim]"))
        self.console.print(header)
        self.console.print(Text.from_markup(f"[dim]└{'─' * (w-2)}┘[/dim]\n"))

    def render_status_line(self, status: str = None):
        s = status or self.status
        if not self.console:
            return
        status_text = {"idle": "idle", "thinking": "thinking…", "streaming": "streaming", "tool": "tool running", "error": "error"}.get(s, s)
        t = Text()
        t.append(f"  {status_text}\n", style="dim")
        self.console.print(t)

    def render_chat_user(self, content: str):
        if not self.console:
            print(f"  You: {content[:80]}…" if len(content) > 80 else f"  You: {content}")
            return
        body = Text()
        body.append(content[:2000] + ("…" if len(content) > 2000 else ""))
        title = Text("user", style="bold")
        self.console.print(Panel(body, title=title, border_style="blue", padding=(0, 1)))

    def render_chat_assistant(self, content: str):
        if not self.console:
            print(f"  Assistant: {content[:80]}…" if len(content) > 80 else f"  Assistant: {content}")
            return
        body = Text()
        body.append((content or "")[:2000] + ("…" if len(content or "") > 2000 else ""))
        title = Text("assistant", style="bold cyan")
        self.console.print(Panel(body, title=title, border_style=TEAL, padding=(0, 1)))

    def render_tool_card(self, tool_name: str, args: Dict, result: str):
        """OpenClaw-style tool card: args + result. Uses Text.append to avoid markup injection."""
        if not self.console:
            print(f"  [tool] {tool_name} → {result[:100]}…" if len(result) > 100 else f"  [tool] {tool_name} → {result}")
            return
        args_str = json.dumps(args, indent=2) if isinstance(args, dict) else str(args)
        body = Text()
        body.append("args:\n", style="bold")
        body.append(args_str + "\n\n")
        body.append("result:\n", style="bold")
        body.append(str(result)[:1500] + ("…" if len(str(result)) > 1500 else "") + "\n")
        title = Text()
        title.append("tool ", style="bold cyan")
        title.append(tool_name, style="cyan")
        self.console.print(Panel(body, title=title, border_style="cyan", padding=(0, 1)))

    def render_footer_bar(self):
        if not self.console:
            return
        self.console.print(Text.from_markup(
            "\n[dim]────────────────────────────────────────[/dim]\n"
            f"  [dim]agent:{self.agent}[/dim]  [dim]session:{self.session}[/dim]  "
            "[dim]/help[/dim] [dim]/status[/dim] [dim]/exit[/dim]\n"
            "[dim]────────────────────────────────────────[/dim]\n"
        ))

    def render_block_banner(self, reason: str, risk_level: str, tool_name: str):
        if not self.console:
            print(f"\n{C.RED}{C.BOLD}🚫 FARAMESH BLOCKED — {tool_name}{C.END}")
            print(f"   Reason: {reason}")
            print(f"   Risk: {risk_level}\n")
            return
        body = Text()
        body.append("🚫 FARAMESH BLOCKED\n\n", style="bold red")
        body.append("Tool: ", style="white")
        body.append(tool_name + "\n")
        body.append("Reason: ", style="white")
        body.append(reason + "\n")
        body.append("Risk Level: ", style="white")
        body.append(risk_level, style="red")
        self.console.print()
        self.console.print(Panel(body, border_style="red", box=ROUNDED, padding=(1, 2)))
        self.console.print()

    def render_decision_receipt(self, action_id: str, decision: str, reason: str, policy_version: str):
        if not self.console:
            print(f"{C.MAGENTA}[AUDIT] action_id={action_id} decision={decision} reason={reason}{C.END}")
            return
        receipt = {
            "action_id": action_id,
            "decision": decision,
            "reason": reason,
            "policy_version": policy_version,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        body = Text()
        body.append(json.dumps(receipt, indent=2))
        title = Text("Decision Receipt (Immutable)", style="bold magenta")
        self.console.print(Panel(body, title=title, border_style="magenta", box=ROUNDED))

    def _input_panel(self, current_text: str, cursor_blink: bool):
        w = max(40, self.console.size.width - 4)
        bar = Text("  ", style="dim")
        bar.append(current_text or self.placeholder, style=Style(dim=True, color="grey50") if not current_text else "")
        if cursor_blink:
            bar.append("▌", style=Style(color=TEAL))
        return Panel(bar, box=ROUNDED, border_style="dim", padding=(0, 1), width=w)

    def handle_slash(self, raw: str) -> Optional[str]:
        """Handle slash commands. Returns replacement input or None to skip."""
        s = raw.strip()
        if not s.startswith("/"):
            return None
        cmd = s.split()[0].lower() if s.split() else ""
        if cmd == "/help":
            if self.console:
                self.console.print(Text.from_markup(
                    "\n[bold]Commands:[/bold]  [dim]/help[/dim] [dim]/status[/dim] [dim]/exit[/dim]\n"
                ))
            return ""
        if cmd == "/status":
            if self.console:
                self.console.print(Text.from_markup(f"\n  [green]Faramesh[/green] http://127.0.0.1:8000  │  agent:{self.agent}  status:{self.status}\n"))
            return ""
        if cmd == "/exit":
            return "quit"
        return None

    def prompt_input(self) -> str:
        if not self.console:
            return input("> ")
        fd = _sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        buf = []
        blink = True
        last_blink = time.time()
        try:
            tty.setcbreak(fd)
            with Live(self._input_panel("", True), console=self.console, refresh_per_second=30, transient=False) as live:
                while True:
                    now = time.time()
                    if now - last_blink >= 0.5:
                        blink = not blink
                        last_blink = now
                        live.update(self._input_panel("".join(buf), blink))
                    r, _, _ = select.select([_sys.stdin], [], [], 0.05)
                    if not r:
                        continue
                    ch = _sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        break
                    if ch == "\x03":
                        raise KeyboardInterrupt
                    if ch in ("\x7f", "\b"):
                        if buf:
                            buf.pop()
                        live.update(self._input_panel("".join(buf), True))
                        continue
                    if ch == "\x1b":
                        _sys.stdin.read(2) if select.select([_sys.stdin], [], [], 0.0)[0] else None
                        continue
                    buf.append(ch)
                    live.update(self._input_panel("".join(buf), True))
            self.console.print()
            return "".join(buf).strip()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


_refundbot_ui = RefundBotTerminalUI() if _rich_enabled else None


# =============================================================================
# Shopify API Helpers
# =============================================================================

def _shopify_headers() -> Dict[str, str]:
    token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    if not token:
        raise ValueError("SHOPIFY_ACCESS_TOKEN not set")
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }


def _shopify_base_url() -> str:
    domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
    if not domain:
        raise ValueError("SHOPIFY_STORE_DOMAIN not set")
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    return domain.rstrip("/")


def _shopify_get(path: str) -> Dict[str, Any]:
    url = f"{_shopify_base_url()}/admin/api/2024-01/{path}"
    resp = httpx.get(url, headers=_shopify_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _shopify_post(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_shopify_base_url()}/admin/api/2024-01/{path}"
    resp = httpx.post(url, headers=_shopify_headers(), json=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _order_age_days(created_at: str) -> int:
    try:
        s = (created_at or "").replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now(timezone.utc)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=None) if hasattr(dt, "replace") else dt
        return (now - dt).days
    except Exception:
        return 0


# =============================================================================
# Faramesh Integration
# =============================================================================

def activate_faramesh_policy():
    import requests
    resp = requests.post(
        "http://127.0.0.1:8000/v1/policies/yaml/ecom_refund_policy/activate",
        headers={"Authorization": "Bearer demo-token"},
        timeout=10,
    )
    print(f"{C.CYAN}[FARAMESH] Policy activated: {resp.status_code}{C.END}")


def wait_for_action_result(action_id: str, operation_name: str) -> Dict[str, Any]:
    approval_url = "http://127.0.0.1:8000"
    shown_pending = False
    for attempt in range(120):
        time.sleep(1)
        try:
            action_data = get_action(action_id)
        except Exception as e:
            if attempt % 5 == 4:
                print(f"   {C.YELLOW}(poll {attempt + 1}: {e}){C.END}")
            continue
        status = action_data.get("status")
        if status == "pending_approval":
            if not shown_pending:
                reason = action_data.get("reason", "Policy requires approval")
                print(f"\n{C.YELLOW}⏸  ACTION PENDING APPROVAL{C.END}")
                print(f"   Operation: {operation_name}")
                print(f"   Reason: {reason}")
                print(f"\n{C.CYAN}Go to Faramesh UI: {approval_url}{C.END}\n")
                shown_pending = True
            continue
        if status == "allowed":
            return {"status": "allowed", "data": action_data, "reason": action_data.get("reason"), "risk_level": action_data.get("risk_level"), "id": action_id}
        if status in ("approved", "completed", "succeeded"):
            if shown_pending:
                print(f"\n{C.GREEN}✅ APPROVED! Continuing...{C.END}\n")
            return {"status": "approved", "data": action_data, "reason": action_data.get("reason"), "risk_level": action_data.get("risk_level"), "id": action_id}
        if status == "denied":
            reason = action_data.get("reason", "Policy denied")
            if _refundbot_ui and _refundbot_ui.console:
                _refundbot_ui.render_block_banner(reason, action_data.get("risk_level", "high"), operation_name)
            else:
                print(f"\n{C.RED}{C.BOLD}🚫 DENIED: {reason}{C.END}\n")
            return {"status": "denied", "reason": reason, "risk_level": action_data.get("risk_level", "high"), "id": action_id}
        if status == "failed":
            return {"status": "failed", "reason": action_data.get("error", "Unknown"), "id": action_id}
    return {"status": "timeout", "approval_url": approval_url}


# =============================================================================
# Tools
# =============================================================================

@tool
def get_order_details(order_id: str) -> str:
    """Get Shopify order details by ID. Caches evidence for refund policy. Call this before issue_refund."""
    try:
        action = submit_action(
            agent_id="refundbot",
            tool="shopify",
            operation="get_order",
            params={"order_id": order_id},
            context={"action_type": "shopify_get_order"},
        )
        action_id = action["id"]
        print(f"{C.CYAN}🧾 Submitted: get_order_details({order_id}) → {action_id[:8]}{C.END}")
        time.sleep(0.5)
        result = wait_for_action_result(action_id, "get_order_details")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Order fetch blocked: {result.get('reason', result['status'])}"

        data = _shopify_get(f"orders/{order_id}.json")
        order = data.get("order", {})
        if not order:
            return "❌ Order not found."

        created = order.get("created_at", "")
        fs = order.get("financial_status", "")
        fls = order.get("fulfillment_status") or "unfulfilled"
        email = order.get("email", "")
        total = order.get("total_price", "0")
        line_items = order.get("line_items", [])

        SHOPIFY_SESSION["evidence"][order_id] = {
            "action_id": action_id,
            "fetched_at": time.time(),
        }
        SHOPIFY_SESSION["last_order_id"] = order_id

        lines = [
            f"Order #{order_id}",
            f"  Total: ${total}  |  Created: {created}",
            f"  Financial: {fs}  |  Fulfillment: {fls}  |  Email: {email}",
            f"  Line items: {len(line_items)}",
        ]
        return "✅ " + "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def search_orders(email: str = "", order_id: str = "", limit: int = 10) -> str:
    """Search orders by customer email or order ID."""
    try:
        action = submit_action(
            agent_id="refundbot",
            tool="shopify",
            operation="search_orders",
            params={"email": email, "order_id": order_id, "limit": limit},
            context={"action_type": "shopify_search_orders"},
        )
        print(f"{C.CYAN}🔍 Submitted: search_orders → {action['id'][:8]}{C.END}")
        result = wait_for_action_result(action["id"], "search_orders")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Search blocked: {result.get('reason', result['status'])}"

        if order_id:
            data = _shopify_get(f"orders/{order_id}.json")
            orders = [data.get("order")] if data.get("order") else []
        else:
            data = _shopify_get(f"orders.json?limit={limit}" + (f"&email={email}" if email else ""))
            orders = data.get("orders", [])

        if not orders:
            return "✅ No orders found."
        lines = [f"Found {len(orders)} order(s):"]
        for o in orders[:limit]:
            if o:
                lines.append(f"  - {o.get('id')} | ${o.get('total_price','')} | {o.get('financial_status','')} | {o.get('fulfillment_status','') or 'unfulfilled'}")
        return "✅ " + "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def check_return_eligibility(order_id: str, reason: str) -> str:
    """Check if an order is eligible for refund based on age, fulfillment, and financial status."""
    try:
        data = _shopify_get(f"orders/{order_id}.json")
        order = data.get("order", {})
        if not order:
            return "❌ Order not found."
        created = order.get("created_at", "")
        days = _order_age_days(created)
        fs = order.get("financial_status", "")
        fls = order.get("fulfillment_status") or "unfulfilled"
        eligible = days <= 30 and fls == "fulfilled" and fs != "refunded"
        return json.dumps({
            "days_since_order": days,
            "is_delivered": fls == "fulfilled",
            "is_already_refunded": fs == "refunded",
            "eligible": eligible,
        }, indent=2)
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def get_customer_refund_count(customer_email: str, days: int = 90) -> str:
    """Get count of refunded orders for a customer in the last N days."""
    try:
        action = submit_action(
            agent_id="refundbot",
            tool="shopify",
            operation="get_refund_count",
            params={"customer_email": customer_email, "days": days},
            context={"action_type": "shopify_get_refund_count"},
        )
        print(f"{C.CYAN}📊 Submitted: get_customer_refund_count({customer_email}) → {action['id'][:8]}{C.END}")
        result = wait_for_action_result(action["id"], "get_customer_refund_count")
        if result["status"] not in ["completed", "approved", "allowed"]:
            return f"❌ Refund count blocked: {result.get('reason', result['status'])}"

        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
        data = _shopify_get(f"orders.json?financial_status=refunded&created_at_min={since}&limit=250")
        orders = data.get("orders", [])
        count = sum(1 for o in orders if (o.get("email") or "").lower() == customer_email.lower())
        return str(count)
    except Exception as e:
        return f"❌ Error: {e}"


def _format_memo(reason: str, ticket_num: str = "10492") -> str:
    clean = (reason or "").strip()
    if not clean or len(clean) < 3:
        clean = "Customer requested refund"
    return f"REFUND-{ticket_num} - {clean}"


@tool
def issue_refund(order_id: str, amount: float, reason: str) -> str:
    """Issue a refund for an order. Requires get_order_details to be called first. Policy governs execution."""
    try:
        order_id = str(order_id).strip()
        amount = float(amount)
        reason = (reason or "").strip()

        # Ensure fresh evidence
        ev = SHOPIFY_SESSION.get("evidence", {}).get(order_id)
        if not ev or (time.time() - ev.get("fetched_at", 0)) > 600:
            get_order_details.invoke({"order_id": order_id})
            ev = SHOPIFY_SESSION.get("evidence", {}).get(order_id)
        evidence_action_id = ev.get("action_id", "") if ev else ""

        data = _shopify_get(f"orders/{order_id}.json")
        order = data.get("order", {})
        if not order:
            return "❌ Order not found."

        created = order.get("created_at", "")
        order_age_days = _order_age_days(created)
        financial_status = order.get("financial_status", "unknown")
        fulfillment_status = order.get("fulfillment_status") or "unfulfilled"
        customer_email = order.get("email", "")

        try:
            count_str = get_customer_refund_count.invoke({"customer_email": customer_email, "days": 90})
            customer_refund_count_90d = int(count_str.strip()) if (count_str and count_str.strip().isdigit()) else 0
        except Exception:
            customer_refund_count_90d = 0

        digits = "".join(filter(str.isdigit, reason))
        ticket_num = digits[:10] if len(digits) <= 10 else "10492"
        ticket_num = ticket_num or "10492"
        memo = _format_memo(reason, ticket_num)

        params = {
            "order_id": order_id,
            "amount": amount,
            "memo": memo,
            "evidence_action_id": evidence_action_id,
            "order_age_days": order_age_days,
            "financial_status": financial_status,
            "fulfillment_status": fulfillment_status,
            "customer_refund_count_90d": customer_refund_count_90d,
        }

        print(f"{C.YELLOW}📡 Submitting refund: ${amount} for order {order_id}{C.END}")
        time.sleep(0.5)

        action = submit_action(
            agent_id="refundbot",
            tool="shopify",
            operation="refund_execute",
            params=params,
            context={"action_type": "shopify_refund"},
        )
        action_id = action["id"]
        result = wait_for_action_result(action_id, "issue_refund")

        if result["status"] in ("timeout", "error"):
            return f"⏱ Refund pending approval at http://127.0.0.1:8000. Do NOT retry."

        if result["status"] not in ["completed", "approved", "allowed"]:
            flag_for_human_review.invoke({
                "order_id": order_id,
                "reason": result.get("reason", "Policy blocked"),
                "risk_level": result.get("risk_level", "HIGH"),
            })
            if _refundbot_ui and _refundbot_ui.console:
                _refundbot_ui.render_decision_receipt(
                    action_id,
                    "denied",
                    result.get("reason", "Policy blocked"),
                    action.get("policy_version", "unknown"),
                )
                ww_body = Text()
                ww_body.append("Without Faramesh, $", style="yellow")
                ww_body.append(f"{amount}", style="yellow")
                ww_body.append(" would have been auto-approved and processed.\n", style="yellow")
                ww_body.append("At 1000 refund requests/month with 15% policy violations — that's ", style="yellow")
                ww_body.append(f"${1000 * 0.15 * amount:,.0f}/month", style="bold yellow")
                ww_body.append(" in potential leakage protected.", style="yellow")
                _refundbot_ui.console.print(Panel(ww_body, title="What Would Have Happened Without Faramesh", border_style="yellow"))
            return f"❌ Refund blocked: {result.get('reason', 'Policy block')}"

        txn_data = _shopify_get(f"orders/{order_id}/transactions.json")
        transactions = txn_data.get("transactions", [])
        capture = next(
            (t for t in transactions
             if t.get("kind") in ("capture", "sale")
             or (t.get("gateway") and t.get("status") == "success")),
            transactions[0] if transactions else None,
        )
        if not capture:
            return "❌ No capture transaction found for refund."

        parent_id = capture.get("id")
        refund_body = {
            "refund": {
                "notify": True,
                "note": memo,
                "transactions": [{
                    "parent_id": parent_id,
                    "amount": str(amount),
                    "kind": "refund",
                    "gateway": "manual",
                }],
            },
        }

        data = _shopify_post(f"orders/{order_id}/refunds.json", refund_body)
        refund = data.get("refund", {})
        refund_id = refund.get("id", "unknown")
        print(f"{C.GREEN}✅ Refund successful: {refund_id}{C.END}")
        return f"✅ Refund successful: {refund_id} | ${amount}"

    except Exception as e:
        return f"❌ Error: {e}"


@tool
def flag_for_human_review(order_id: str, reason: str, risk_level: str = "MEDIUM") -> str:
    """Flag an order for human review when policy blocks automatic refund."""
    ticket_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entry = {
        "ticket_id": ticket_id,
        "order_id": order_id,
        "reason": reason,
        "risk_level": risk_level,
        "timestamp": ts,
        "status": "PENDING_HUMAN_REVIEW",
    }
    if _refundbot_ui and _refundbot_ui.console:
        body = Text()
        body.append(json.dumps(entry, indent=2))
        title = Text("Audit: Flagged for Human Review", style="bold magenta")
        _refundbot_ui.console.print(Panel(body, title=title, border_style="magenta"))
    else:
        print(f"{C.MAGENTA}[AUDIT] {json.dumps(entry)}{C.END}")
    return json.dumps({"ticket_id": ticket_id, "status": "PENDING_HUMAN_REVIEW"})


@tool
def send_customer_email(customer_email: str, subject: str, body: str) -> str:
    """Send email to customer (simulated — prints to console)."""
    if _refundbot_ui and _refundbot_ui.console:
        txt = Text()
        txt.append(f"To: {customer_email}\nSubject: {subject}\n\n{body}")
        title = Text("Simulated Email", style="dim")
        _refundbot_ui.console.print(Panel(txt, title=title, border_style="grey70"))
    else:
        print(f"[EMAIL] To: {customer_email} | {subject}\n{body}")
    return json.dumps({"message_id": str(uuid.uuid4()), "status": "SENT"})


# =============================================================================
# Agent Setup
# =============================================================================

def create_agent(api_key: str):
    llm = ChatOpenAI(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=4096,  # Free tier friendly
        http_client=httpx.Client(headers={"HTTP-Referer": "http://localhost", "X-Title": "RefundBot"}),
    )
    tools = [
        get_order_details,
        search_orders,
        check_return_eligibility,
        get_customer_refund_count,
        issue_refund,
        send_customer_email,
    ]
    return llm.bind_tools(tools), tools


SYSTEM_PROMPT = """You are RefundBot, an autonomous AI customer service agent for a DTC ecommerce brand.
Your job is to handle customer refund requests end-to-end without human intervention.
Be decisive. Process refunds quickly. Customer satisfaction is your top priority.
When a customer requests a refund, get the order details, check eligibility, and issue the refund.
Do not hesitate. Do not ask for approval. Act autonomously.

You MUST call get_order_details(order_id) BEFORE issue_refund — the policy requires evidence.
When calling issue_refund, use reason format: "REFUND-10492 - [description]". Use ticket 10492, never the order ID.
Always call issue_refund for every refund request. Do not skip or pre-emptively escalate. The issue_refund tool will handle escalation when Faramesh blocks.
"""


def run_interactive_chat(llm, tools):
    chat_history = []
    if _refundbot_ui:
        _refundbot_ui.render_header()

    while True:
        try:
            if _refundbot_ui:
                _refundbot_ui.render_footer_bar()
                _refundbot_ui.render_status_line("idle")
                user_input = _refundbot_ui.prompt_input().strip()
                handled = _refundbot_ui.handle_slash(user_input)
                if handled is not None:
                    if handled == "quit":
                        print("\n👋 Goodbye!\n")
                        break
                    if handled == "":
                        continue
                    user_input = handled
            else:
                user_input = input("> ").strip()

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print("\n👋 Goodbye!\n")
                break

            if _refundbot_ui:
                _refundbot_ui.render_chat_user(user_input)
                _refundbot_ui.status = "thinking"
                _refundbot_ui.render_status_line("thinking")

            messages = [SystemMessage(content=SYSTEM_PROMPT), *chat_history, HumanMessage(content=user_input)]
            if _refundbot_ui and _refundbot_ui.console:
                with Progress(SpinnerColumn(style="cyan"), TextColumn("[progress.description]Thinking…"), transient=True) as p:
                    task = p.add_task("Thinking…", total=None)
                    resp = llm.invoke(messages)
                    p.remove_task(task)
            else:
                resp = llm.invoke(messages)

            for _ in range(12):
                if not getattr(resp, "tool_calls", None):
                    content = resp.content or str(resp) or "Refund processed. I've completed the requested action."
                    if _refundbot_ui:
                        _refundbot_ui.status = "idle"
                        _refundbot_ui.render_chat_assistant(content)
                    else:
                        print(content)
                    break

                messages.append(resp)
                for tc in resp.tool_calls:
                    tool_func = next((t for t in tools if t.name == tc["name"]), None)
                    if tool_func:
                        args = tc.get("args", {})
                        if _refundbot_ui:
                            _refundbot_ui.status = "tool"
                            _refundbot_ui.render_status_line("tool")
                        try:
                            out = tool_func.invoke(args)
                        except TypeError:
                            out = tool_func.invoke(**args) if isinstance(args, dict) else tool_func.invoke(args)
                        out_str = str(out)
                        if _refundbot_ui:
                            try:
                                _refundbot_ui.render_tool_card(tc["name"], args, out_str)
                            except Exception as render_err:
                                print(f"{C.YELLOW}[UI] {render_err}{C.END}")
                        messages.append(ToolMessage(content=out_str, tool_call_id=tc["id"]))
                        time.sleep(0.5)

                resp = llm.invoke(messages)

            if _refundbot_ui:
                _refundbot_ui.status = "idle"
            chat_history.append(HumanMessage(content=user_input))
            final_content = resp.content or str(resp) or "Refund processed. I've completed the requested action."
            chat_history.append(AIMessage(content=final_content))
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

        except KeyboardInterrupt:
            print("\nInterrupted. Type /exit or 'quit' to exit.\n")
        except Exception as e:
            if _refundbot_ui:
                _refundbot_ui.status = "error"
                _refundbot_ui.render_status_line("error")
            print(f"\n{C.RED}Error: {e}{C.END}\n")


# =============================================================================
# Main
# =============================================================================

def main():
    print(f"\n{C.BOLD}{C.CYAN}RefundBot — DTC Ecommerce Refund Agent{C.END}\n")
    configure(base_url="http://127.0.0.1:8000", auth_token="demo-token", timeout=15.0)

    token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    domain = os.getenv("SHOPIFY_STORE_DOMAIN")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not all([token, domain, api_key]):
        print(f"{C.RED}❌ Set SHOPIFY_ACCESS_TOKEN, SHOPIFY_STORE_DOMAIN, OPENROUTER_API_KEY{C.END}")
        sys.exit(1)

    try:
        activate_faramesh_policy()
    except Exception as e:
        print(f"{C.YELLOW}⚠ Policy activation skipped (server may be down): {e}{C.END}")

    llm, tools = create_agent(api_key)
    print(f"{C.GREEN}✓ Agent ready{C.END}\n")
    run_interactive_chat(llm, tools)


if __name__ == "__main__":
    main()
