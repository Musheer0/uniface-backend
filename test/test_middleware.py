"""Auth dependency + tracking middleware (user_id/generation_id -> headers)."""

import os

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from src.middlewares.auth_middleware import InternalAuthorization, TrackingHeadersMiddleware


def _app_with_auth():
    app = FastAPI()
    app.add_middleware(TrackingHeadersMiddleware)

    @app.post("/ping", dependencies=[Depends(InternalAuthorization)])
    def ping():
        return {"ok": True}

    @app.post("/whoami")
    def whoami(request: Request):
        return {
            "user_id": getattr(request.state, "user_id", None),
            "generation_id": getattr(request.state, "generation_id", None),
        }

    return app


@pytest.fixture()
def api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-123")
    # auth reads env lazily per request; also clear dotenv-cached process env
    os.environ["API_KEY"] = "secret-123"
    return "secret-123"


def test_auth_accepts_canonical_and_legacy_headers(api_key):
    client = TestClient(_app_with_auth())
    assert client.post("/ping", headers={"x-api-key": api_key}).status_code == 200
    assert client.post("/ping", headers={"api-key": api_key}).status_code == 200


def test_auth_rejects_missing_and_wrong(api_key):
    client = TestClient(_app_with_auth())
    assert client.post("/ping").status_code == 401
    assert client.post("/ping", headers={"x-api-key": "nope"}).status_code == 401


def test_tracking_headers_echoed_from_body():
    client = TestClient(_app_with_auth())
    r = client.post("/whoami", json={"user_id": "u-9", "generation_id": "g-9"})
    assert r.status_code == 200
    assert r.json() == {"user_id": "u-9", "generation_id": "g-9"}
    assert r.headers["X-User-Id"] == "u-9"
    assert r.headers["X-Generation-Id"] == "g-9"


def test_tracking_headers_absent_without_body_keys():
    client = TestClient(_app_with_auth())
    r = client.post("/whoami", json={"hello": "world"})
    assert r.status_code == 200
    assert "X-User-Id" not in r.headers
    assert "X-Generation-Id" not in r.headers


def test_tracking_middleware_passes_through_non_json():
    client = TestClient(_app_with_auth())
    r = client.post("/whoami", content=b"not-json", headers={"Content-Type": "text/plain"})
    assert r.status_code == 200
