// E5: push past what E1 showed the fixed group can take, once with panic mode
// off and once with it on, and compare /play latency and errors.
//
//   k6 run -e BASE_URL=http://<alb> -e RATE=500 -e DURATION=5m loadtest/overload.js
//
// Set RATE above the highest rate E1 sustained. 2 c7i-flex.large servers take
// about 340 journeys/s, so 500 is about 1.5x. Results are split by the "name"
// tag, so /play can be read on its own.
import { runMix, summaryTrendStats } from "./lib/journey.js";

const RATE = parseInt(__ENV.RATE || "500", 10);

export const options = {
  summaryTrendStats,
  // Overload is the point: never abort early, just record what happened.
  thresholds: {
    "http_req_duration{name:play}": ["p(95)<100000"],
  },
  scenarios: {
    overload: {
      executor: "constant-arrival-rate",
      rate: RATE,
      timeUnit: "1s",
      duration: __ENV.DURATION || "5m",
      preAllocatedVUs: parseInt(__ENV.PRE_VUS || String(RATE * 2), 10),
      maxVUs: parseInt(__ENV.MAX_VUS || String(RATE * 5), 10), // the k6 box has 4 GB
    },
  },
};

export default function () {
  runMix();
}
