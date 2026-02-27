// Basic example: submit an action using the Faramesh Node.js SDK

const { configure, submitAction } = require("@faramesh/sdk");

async function main() {
  // Configure SDK to talk to local server
  configure({
    baseUrl: process.env.FARAMESH_BASE_URL || "http://127.0.0.1:8000",
    token: process.env.FARAMESH_TOKEN || undefined,
  });

  try {
    const action = await submitAction(
      "example-agent",
      "http",
      "get",
      { url: "https://example.com" },
      { source: "basic_submit.js" }
    );

    console.log("Action submitted!");
    console.log(`  id      = ${action.id}`);
    console.log(`  status  = ${action.status}`);
    console.log(`  risk    = ${action.risk_level}`);
    console.log(`  decision= ${action.decision}`);
  } catch (err) {
    console.error("Error submitting action:", err.message || err);
    process.exit(1);
  }
}

main();

