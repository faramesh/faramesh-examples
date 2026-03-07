// examples/js/shell/shell_bot.js
require("dotenv").config();
const { governedExec, GovernorError } = require("../../../src/faramesh/js-sdk");

(async () => {
  try {
    const res = await governedExec("ls -la");
    console.log("OK:", res.stdout.trim());
  } catch (err) {
    if (err instanceof GovernorError) {
      console.error("BLOCK:", err.message);
    } else {
      console.error("ERR:", err);
    }
  }
})();
