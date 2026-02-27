#!/usr/bin/env node
/**
 * Gated Execution Example - Non-bypassable execution gate pattern (Node.js)
 *
 * This example demonstrates how to use Faramesh's gate endpoint to implement
 * a non-bypassable execution pattern where:
 * 1. All actions must go through the gate for decision
 * 2. Only EXECUTE decisions proceed with actual execution
 * 3. HALT/ABSTAIN decisions are properly handled
 * 4. Request hashes are verified for integrity
 *
 * Usage:
 *   npm install @faramesh/sdk
 *   node gated_execution.js
 */

const {
  configure,
  gateDecide,
  executeIfAllowed,
  computeRequestHash,
  verifyRequestHash,
} = require("@faramesh/sdk");

/**
 * Example executor that would perform the actual HTTP request.
 * In production, this would call axios, fetch, etc.
 */
async function httpExecutor(tool, operation, params, context) {
  console.log(`  [EXECUTING] ${tool}:${operation} with params:`, params);
  return {
    status: "success",
    statusCode: 200,
    body: { message: "Request completed" },
  };
}

/**
 * Example executor that would run a shell command.
 * In production, this would call child_process.exec(), etc.
 */
async function shellExecutor(tool, operation, params, context) {
  const cmd = params.cmd || "";
  console.log(`  [EXECUTING] ${tool}:${operation} command: ${cmd}`);
  return {
    status: "success",
    output: `Simulated output for: ${cmd}`,
    exitCode: 0,
  };
}

async function main() {
  // Configure the SDK to connect to local Faramesh server
  configure({ baseUrl: "http://localhost:8000" });

  console.log("=".repeat(60));
  console.log("Faramesh Gated Execution Example (Node.js)");
  console.log("=".repeat(60));

  // Example 1: Safe HTTP GET request (should be allowed)
  console.log("\n[Example 1] HTTP GET Request");
  console.log("-".repeat(40));

  let result = await executeIfAllowed({
    agentId: "demo-agent",
    tool: "http",
    operation: "get",
    params: { url: "https://api.example.com/data" },
    context: { source: "gated_execution_example" },
    executor: httpExecutor,
  });

  console.log(`  Outcome: ${result.outcome}`);
  console.log(`  Reason Code: ${result.reasonCode}`);
  console.log(`  Executed: ${result.executed}`);
  if (result.executed) {
    console.log(`  Result:`, result.executionResult);
  }

  // Example 2: Potentially dangerous shell command (may be denied)
  console.log("\n[Example 2] Shell Command (potentially risky)");
  console.log("-".repeat(40));

  result = await executeIfAllowed({
    agentId: "demo-agent",
    tool: "shell",
    operation: "run",
    params: { cmd: "ls -la /tmp" },
    context: { source: "gated_execution_example" },
    executor: shellExecutor,
  });

  console.log(`  Outcome: ${result.outcome}`);
  console.log(`  Reason Code: ${result.reasonCode}`);
  console.log(`  Executed: ${result.executed}`);
  if (!result.executed && result.outcome !== "EXECUTE") {
    console.log(`  [BLOCKED] Action was not executed due to policy decision`);
  }

  // Example 3: Verify request hash locally before submission
  console.log("\n[Example 3] Request Hash Verification");
  console.log("-".repeat(40));

  const payload = {
    agent_id: "demo-agent",
    tool: "http",
    operation: "post",
    params: { url: "https://api.example.com/webhook", data: { event: "test" } },
    context: {},
  };

  // Compute hash locally
  const localHash = computeRequestHash(payload);
  console.log(`  Local request_hash: ${localHash.slice(0, 16)}...`);

  // Get decision from server
  const decision = await gateDecide(
    payload.agent_id,
    payload.tool,
    payload.operation,
    payload.params,
    payload.context
  );

  console.log(`  Server request_hash: ${decision.request_hash.slice(0, 16)}...`);
  console.log(`  Hashes match: ${localHash === decision.request_hash}`);
  console.log(`  Decision outcome: ${decision.outcome}`);

  // Example 4: Using gateDecide directly for pre-check
  console.log("\n[Example 4] Pre-check Before Committing");
  console.log("-".repeat(40));

  const preCheckDecision = await gateDecide(
    "demo-agent",
    "stripe",
    "refund",
    { amount: 100, currency: "usd" }
  );

  console.log(`  Outcome: ${preCheckDecision.outcome}`);
  console.log(`  Reason Code: ${preCheckDecision.reason_code}`);
  console.log(`  Policy Version: ${preCheckDecision.policy_version}`);
  console.log(`  Runtime Version: ${preCheckDecision.runtime_version}`);

  if (preCheckDecision.outcome === "EXECUTE") {
    console.log("  [OK] Safe to proceed with refund");
  } else if (preCheckDecision.outcome === "ABSTAIN") {
    console.log("  [PENDING] Requires approval before proceeding");
  } else {
    console.log("  [BLOCKED] Refund would be denied");
  }

  console.log("\n" + "=".repeat(60));
  console.log("Example completed!");
  console.log("=".repeat(60));
}

main().catch(console.error);
