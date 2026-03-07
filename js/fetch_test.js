require("dotenv").config();
const { governedFetch } = require("../../src/faramesh/js-sdk");

(async () => {
  const r = await governedFetch("https://httpbin.org/get");
  console.log("status:", r.status);
})();
