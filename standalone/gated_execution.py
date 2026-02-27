#!/usr/bin/env python3
"""
Gated Execution Example - Non-bypassable execution gate pattern.

This example demonstrates how to use Faramesh's gate endpoint to implement
a non-bypassable execution pattern where:
1. All actions must go through the gate for decision
2. Only EXECUTE decisions proceed with actual execution
3. HALT/ABSTAIN decisions are properly handled
4. Request hashes are verified for integrity

Usage:
    pip install faramesh
    python gated_execution.py
"""

from faramesh import (
    configure,
    gate_decide,
    execute_if_allowed,
    compute_request_hash,
    verify_request_hash,
)


def example_http_executor(tool: str, operation: str, params: dict, context: dict) -> dict:
    """
    Example executor that would perform the actual HTTP request.
    
    In production, this would call httpx, requests, etc.
    Here we just simulate the execution.
    """
    print(f"  [EXECUTING] {tool}:{operation} with params: {params}")
    return {
        "status": "success",
        "status_code": 200,
        "body": {"message": "Request completed"},
    }


def example_shell_executor(tool: str, operation: str, params: dict, context: dict) -> dict:
    """
    Example executor that would run a shell command.
    
    In production, this would call subprocess.run(), etc.
    Here we just simulate the execution.
    """
    cmd = params.get("cmd", "")
    print(f"  [EXECUTING] {tool}:{operation} command: {cmd}")
    return {
        "status": "success",
        "output": f"Simulated output for: {cmd}",
        "exit_code": 0,
    }


def main():
    # Configure the SDK to connect to local Faramesh server
    configure(base_url="http://localhost:8000")
    
    print("=" * 60)
    print("Faramesh Gated Execution Example")
    print("=" * 60)
    
    # Example 1: Safe HTTP GET request (should be allowed)
    print("\n[Example 1] HTTP GET Request")
    print("-" * 40)
    
    result = execute_if_allowed(
        agent_id="demo-agent",
        tool="http",
        operation="get",
        params={"url": "https://api.example.com/data"},
        context={"source": "gated_execution_example"},
        executor=example_http_executor,
    )
    
    print(f"  Outcome: {result['outcome']}")
    print(f"  Reason Code: {result['reason_code']}")
    print(f"  Executed: {result['executed']}")
    if result['executed']:
        print(f"  Result: {result['execution_result']}")
    
    # Example 2: Potentially dangerous shell command (may be denied)
    print("\n[Example 2] Shell Command (potentially risky)")
    print("-" * 40)
    
    result = execute_if_allowed(
        agent_id="demo-agent",
        tool="shell",
        operation="run",
        params={"cmd": "ls -la /tmp"},
        context={"source": "gated_execution_example"},
        executor=example_shell_executor,
    )
    
    print(f"  Outcome: {result['outcome']}")
    print(f"  Reason Code: {result['reason_code']}")
    print(f"  Executed: {result['executed']}")
    if not result['executed'] and result['outcome'] != "EXECUTE":
        print(f"  [BLOCKED] Action was not executed due to policy decision")
    
    # Example 3: Verify request hash locally before submission
    print("\n[Example 3] Request Hash Verification")
    print("-" * 40)
    
    payload = {
        "agent_id": "demo-agent",
        "tool": "http",
        "operation": "post",
        "params": {"url": "https://api.example.com/webhook", "data": {"event": "test"}},
        "context": {},
    }
    
    # Compute hash locally
    local_hash = compute_request_hash(payload)
    print(f"  Local request_hash: {local_hash[:16]}...")
    
    # Get decision from server
    decision = gate_decide(
        agent_id=payload["agent_id"],
        tool=payload["tool"],
        operation=payload["operation"],
        params=payload["params"],
        context=payload["context"],
    )
    
    print(f"  Server request_hash: {decision.request_hash[:16]}...")
    print(f"  Hashes match: {local_hash == decision.request_hash}")
    print(f"  Decision outcome: {decision.outcome}")
    
    # Example 4: Using gate_decide directly for pre-check
    print("\n[Example 4] Pre-check Before Committing")
    print("-" * 40)
    
    decision = gate_decide(
        agent_id="demo-agent",
        tool="stripe",
        operation="refund",
        params={"amount": 100, "currency": "usd"},
    )
    
    print(f"  Outcome: {decision.outcome}")
    print(f"  Reason Code: {decision.reason_code}")
    print(f"  Policy Version: {decision.policy_version}")
    print(f"  Runtime Version: {decision.runtime_version}")
    
    if decision.outcome == "EXECUTE":
        print("  [OK] Safe to proceed with refund")
    elif decision.outcome == "ABSTAIN":
        print("  [PENDING] Requires approval before proceeding")
    else:
        print("  [BLOCKED] Refund would be denied")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
