require("dotenv").config();
const { guardedFunction } = require("../../src/faramesh/js-sdk");

const fn = guardedFunction(
  async (u, amt) => console.log(`ran for ${u}:${amt}`),
  {
    tool: "payments",
    op: "refund",
    mapArgs: (args) => ({
      user: args[0],
      amount: args[1],
    }),
  }
);

(async () => {
  await fn("a", 10);     // allow
  await fn("b", 200);    // require_approval (if rule)
  await fn("c", 10);     // allow again
})();
