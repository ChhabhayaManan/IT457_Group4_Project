from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_status():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Match live, stream available"


def test_score_shape():
    response = client.get("/score")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"match", "score", "overs", "updated"}


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
