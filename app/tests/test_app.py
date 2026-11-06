import hashlib
import hmac

from fastapi.testclient import TestClient

from main import PLAY_SECRET, app

client = TestClient(app)


def make_token(user_id: str) -> str:
    return hmac.new(PLAY_SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()


def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Match live, stream available"


def test_score_shape():
    response = client.get("/score")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"match", "score", "overs", "updated"}


def test_score_cache_header():
    response = client.get("/score")
    assert response.headers["cache-control"] == "public, max-age=5"


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_play_valid_token():
    response = client.post("/play", json={"user_id": "u42", "token": make_token("u42")})
    assert response.status_code == 200
    body = response.json()
    assert "sig=" in body["playback_url"]
    assert body["expires"] > 0


def test_play_bad_token_401():
    response = client.post("/play", json={"user_id": "u42", "token": "not-a-token"})
    assert response.status_code == 401


def test_home_personalised():
    response = client.get("/home")
    assert response.status_code == 200
    body = response.json()
    assert body["personalised"] is True
    assert len(body["rails"]) > 0
