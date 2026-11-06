"""mini-Hotstar control-path API.

Stands in for the API calls a Hotstar app makes before video starts.
Video itself never touches this service; it comes from the CDN.
"""

import hashlib
import hmac
import os
import time

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

PLAY_SECRET = os.environ.get("PLAY_SECRET", "group4-demo-secret")
# PBKDF2 rounds per /play call: the CPU cost of "DRM signing". About 20 ms on t3.micro.
PLAY_ITERATIONS = int(os.environ.get("PLAY_ITERATIONS", "20000"))
# Rounds per /home call: a medium CPU cost for "personalisation".
HOME_ITERATIONS = int(os.environ.get("HOME_ITERATIONS", "5000"))

app = FastAPI(title="mini-Hotstar")


class PlayRequest(BaseModel):
    user_id: str
    token: str


@app.get("/")
def root():
    return {"status": "Match live, stream available"}


@app.get("/score")
def score(response: Response):
    # Light, identical for every viewer: the kind of response a CDN can cache.
    # Hotstar served scorecards from the CDN; 5 s keeps the score fresh enough.
    response.headers["Cache-Control"] = "public, max-age=5"
    return {
        "match": "IND vs AUS",
        "score": "287/4",
        "overs": "45.2",
        "updated": int(time.time()),
    }


@app.post("/play")
def play(request: PlayRequest):
    # 1. Check the viewer's token (stands in for login + subscription check).
    expected = hmac.new(PLAY_SECRET.encode(), request.user_id.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.token):
        raise HTTPException(status_code=401, detail="invalid token")

    # 2. Sign a short-lived playback URL (stands in for DRM licence work). Deliberately CPU-heavy.
    expires = int(time.time()) + 300
    payload = f"{request.user_id}:{expires}".encode()
    signature = hashlib.pbkdf2_hmac("sha256", payload, PLAY_SECRET.encode(), PLAY_ITERATIONS).hex()
    return {
        "playback_url": f"https://cdn.example.com/live/master.m3u8?exp={expires}&sig={signature[:32]}",
        "expires": expires,
    }


@app.get("/home")
def home():
    # Medium CPU: pretend to rank rails for this viewer.
    hashlib.pbkdf2_hmac("sha256", b"home", PLAY_SECRET.encode(), HOME_ITERATIONS)
    return {
        "rails": ["Live now", "Because you watched IND vs PAK", "Highlights", "Top picks for you"],
        "personalised": True,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
