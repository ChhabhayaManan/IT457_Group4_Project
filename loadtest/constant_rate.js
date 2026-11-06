// E1 (and E4): the same request rate for a fixed time.
// E1 runs this once per instance count (1, 2, 4, 8) and compares latency.
//
//   k6 run -e BASE_URL=http://<alb> -e RATE=100 -e DURATION=15m loadtest/constant_rate.js
//
// RATE is iterations per second; with MIX=journey one iteration is 4 requests.
// 100 is sized for c7i.large: more than 1 server can take, easy for 8.
import { runMix, summaryTrendStats } from "./lib/journey.js";

const RATE = parseInt(__ENV.RATE || "100", 10);

export const options = {
  summaryTrendStats,
  scenarios: {
    constant: {
      executor: "constant-arrival-rate",
      rate: RATE,
      timeUnit: "1s",
      duration: __ENV.DURATION || "15m",
      preAllocatedVUs: parseInt(__ENV.PRE_VUS || String(RATE * 2), 10),
      maxVUs: parseInt(__ENV.MAX_VUS || String(RATE * 10), 10),
    },
  },
};

export default function () {
  runMix();
}
