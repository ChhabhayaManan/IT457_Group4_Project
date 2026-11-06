// E2 and E3: a match-moment spike.
// Baseline for BASELINE_MIN, jump to SPIKE_RATE in 30 s, hold HOLD_MIN,
// drop back in 30 s, then stay at baseline for COOLDOWN_MIN so scale-in shows.
//
//   k6 run -e BASE_URL=http://<alb> loadtest/spike.js
//
// Defaults: 30 -> 300 iterations/s (10x), 5 / 15 / 15 minutes (about 36 min).
// Sized for c7i.large: 300/s needs most of the 10-server ceiling.
// For a quick local check use UNIT=s so the "minutes" become seconds.
import { runMix, summaryTrendStats } from "./lib/journey.js";

const BASELINE = parseInt(__ENV.BASELINE_RATE || "30", 10);
const SPIKE = parseInt(__ENV.SPIKE_RATE || "300", 10);
const UNIT = __ENV.UNIT || "m";
const baselineFor = `${__ENV.BASELINE_MIN || "5"}${UNIT}`;
const holdFor = `${__ENV.HOLD_MIN || "15"}${UNIT}`;
const cooldownFor = `${__ENV.COOLDOWN_MIN || "15"}${UNIT}`;
const rampFor = UNIT === "s" ? "3s" : "30s";

export const options = {
  summaryTrendStats,
  scenarios: {
    spike: {
      executor: "ramping-arrival-rate",
      startRate: BASELINE,
      timeUnit: "1s",
      preAllocatedVUs: parseInt(__ENV.PRE_VUS || String(SPIKE), 10),
      maxVUs: parseInt(__ENV.MAX_VUS || String(SPIKE * 10), 10),
      stages: [
        { target: BASELINE, duration: baselineFor },
        { target: SPIKE, duration: rampFor },
        { target: SPIKE, duration: holdFor },
        { target: BASELINE, duration: rampFor },
        { target: BASELINE, duration: cooldownFor },
      ],
    },
  },
};

export default function () {
  runMix();
}
