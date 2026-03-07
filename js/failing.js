require("dotenv").config();
const { guardedFunction, GovernorError } = require("../../src/faramesh/js-sdk");

const failing = guardedFunction(
  async () => {
    throw new Error("boom");
  },
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
  try {
    await failing("userA", 20);
  } catch (e) {
    console.log("caught expected:", e.message);
  }
})();
