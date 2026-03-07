// examples/js/refund.js
require("dotenv").config();
const { guardedFunction, GovernorError } = require("../../src/faramesh/js-sdk");

const refundUser = guardedFunction(
  async (user, amount) => {
    console.log(`Refunding ${amount} to ${user} (JS)`);
    // do your Stripe/Adyen/etc work here
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
    const res = await refundUser("js_user", 101);
    console.log("RESULT:", res);
  } catch (err) {
    if (err instanceof GovernorError) {
      console.error("Governor blocked:", err.message);
    } else {
      console.error("Tool error:", err);
    }
  }
})();
