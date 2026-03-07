require("dotenv").config();
const { guardedFunction, GovernorError } = require("../../src/faramesh/js-sdk");

const risky = guardedFunction(
  async () => console.log("SHOULD NEVER RUN"),
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
    const pa = await risky("js_user", 99999);
    console.log("Pending:", pa);
  } catch (err) {
    console.error("Unexpected error:", err);
  }
})();
