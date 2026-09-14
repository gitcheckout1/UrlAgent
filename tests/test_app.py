from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.shared.memory_store import store
from app.write.api import LINK_TTL, RATE_LIMIT_MAX, ratelimit

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()
    # Module-level window, so it has to be cleared between tests too.
    ratelimit.reset()


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


def test_expiry_behavior_brownfield():
    created = client.post("/v1/urls", json={"url": "https://example.com/expires"})
    assert created.status_code == 201
    code = created.json()["code"]

    record = store.get(code)
    assert record.expires_at == record.created_at + LINK_TTL

    # Not expired yet: normal redirect, click counted.
    assert client.get(f"/{code}", follow_redirects=False).status_code == 302
    assert store.get(code).clicks == 1

    # Force expiry. A 410 must not count as a click.
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    gone = client.get(f"/{code}", follow_redirects=False)
    assert gone.status_code == 410
    assert store.get(code).clicks == 1

    # Stats stay readable after expiry.
    stats = client.get(f"/v1/urls/{code}/stats")
    assert stats.status_code == 200
    assert stats.json()["clicks"] == 1


def test_eleventh_post_returns_429():
    for _ in range(RATE_LIMIT_MAX):
        allowed = client.post("/v1/urls", json={"url": "https://example.com/ok"})
        assert allowed.status_code == 201

    blocked = client.post("/v1/urls", json={"url": "https://example.com/ok"})
    assert blocked.status_code == 429

    ratelimit.reset()
    assert client.post("/v1/urls", json={"url": "https://example.com/ok"}).status_code == 201
