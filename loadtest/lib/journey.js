// Shared request logic for every k6 script.
// One "journey" is what a viewer's app does when a match is on: open the app,
// check the score, press play, load the home page.
import http from "k6/http";
import crypto from "k6/crypto";
import { check } from "k6";

export const BASE_URL = (__ENV.BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const PLAY_SECRET = __ENV.PLAY_SECRET || "group4-demo-secret";

function token(userId) {
  // Same HMAC the app checks in POST /play.
  return crypto.hmac("sha256", PLAY_SECRET, userId, "hex");
}

function get(path, name) {
  const res = http.get(`${BASE_URL}${path}`, { tags: { name } });
  check(res, { [`${name} is 200`]: (r) => r.status === 200 });
  return res;
}

export function root() {
  return get("/", "root");
}

export function score() {
  return get("/score", "score");
}

export function home() {
  return get("/home", "home");
}

export function play() {
  const userId = `u${__VU}-${__ITER}`;
  const res = http.post(
    `${BASE_URL}/play`,
    JSON.stringify({ user_id: userId, token: token(userId) }),
    { headers: { "Content-Type": "application/json" }, tags: { name: "play" } },
  );
  check(res, { "play is 200": (r) => r.status === 200 });
  return res;
}

export function journey() {
  root();
  score();
  play();
  home();
}

// MIX picks what one iteration does: the full journey, or a single endpoint.
export function runMix() {
  const mix = __ENV.MIX || "journey";
  if (mix === "journey") return journey();
  if (mix === "score") return score();
  if (mix === "play") return play();
  if (mix === "home") return home();
  if (mix === "root") return root();
  throw new Error(`unknown MIX=${mix}; use journey, score, play, home or root`);
}

export const summaryTrendStats = ["avg", "min", "med", "p(95)", "p(99)", "max"];
