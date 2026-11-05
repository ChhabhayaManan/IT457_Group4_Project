"""mini-Hotstar control-path API.

Stands in for the API calls a Hotstar app makes before video starts.
Video itself never touches this service; it comes from the CDN.
"""

import time

from fastapi import FastAPI

app = FastAPI(title="mini-Hotstar")


@app.get("/")
def root():
    return {"status": "Match live, stream available"}


@app.get("/score")
def score():
    # Light, identical for every viewer: the kind of response a CDN can cache.
    return {
        "match": "IND vs AUS",
        "score": "287/4",
        "overs": "45.2",
        "updated": int(time.time()),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
