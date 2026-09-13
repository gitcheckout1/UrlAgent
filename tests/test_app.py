import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.shared.memory_store import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()


def test_create_then_redirect_then_stats():
    created = client.post("/v1/urls", json={"url": "https://example.com/page"})
    assert created.status_code == 201
    code = created.json()["code"]
    assert len(code) == 7

    hop = client.get(f"/{code}", follow_redirects=False)
    assert hop.status_code == 302
    assert hop.headers["location"] == "https://example.com/page"

    stats = client.get(f"/v1/urls/{code}/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["clicks"] == 1
    assert body["last_clicked_at"] is not None


def test_rejects_javascript_scheme():
    rejected = client.post("/v1/urls", json={"url": "javascript:alert(1)"})
    assert rejected.status_code == 400


def test_unknown_code_returns_404():
    assert client.get("/nope123", follow_redirects=False).status_code == 404
