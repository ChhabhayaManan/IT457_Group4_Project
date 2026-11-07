import hashlib
import hmac
import socket

from fastapi.testclient import TestClient

from instance import get_instance_id
from main import INSTANCE_ID, PLAY_SECRET, app

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


def test_instance_header_everywhere():
    paths = ["/", "/score", "/home", "/health"]
    for path in paths:
        assert client.get(path).headers["x-instance-id"] == INSTANCE_ID
    play = client.post("/play", json={"user_id": "u1", "token": make_token("u1")})
    assert play.headers["x-instance-id"] == INSTANCE_ID


def test_bodies_include_instance():
    for path in ["/", "/score", "/home"]:
        assert client.get(path).json()["instance"] == INSTANCE_ID
    play = client.post("/play", json={"user_id": "u1", "token": make_token("u1")})
    assert play.json()["instance"] == INSTANCE_ID


def test_instance_id_falls_back_to_hostname(monkeypatch):
    monkeypatch.delenv("INSTANCE_ID", raising=False)
    # Port 9 on localhost refuses at once, like a laptop with no EC2 metadata service.
    assert get_instance_id(imds_url="http://127.0.0.1:9") == socket.gethostname()


def test_instance_id_env_override(monkeypatch):
    monkeypatch.setenv("INSTANCE_ID", "i-local-test")
    assert get_instance_id() == "i-local-test"


def test_home_personalised():
    response = client.get("/home")
    assert response.status_code == 200
    body = response.json()
    assert body["personalised"] is True
    assert body["panic"] is False
    assert len(body["rails"]) > 0


def test_home_static_when_panic(monkeypatch):
    monkeypatch.setenv("PANIC_MODE", "on")
    body = client.get("/home").json()
    assert body["personalised"] is False
    assert body["panic"] is True
    assert len(body["rails"]) > 0


def test_play_still_works_in_panic(monkeypatch):
    monkeypatch.setenv("PANIC_MODE", "on")
    response = client.post("/play", json={"user_id": "u7", "token": make_token("u7")})
    assert response.status_code == 200
