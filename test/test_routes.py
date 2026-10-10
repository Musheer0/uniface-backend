"""Router surface: correct prefixes, fixed + legacy-compat routes, healthz."""

from src.routers import photo_routers, video_routers, video_timestamp_routers
from src.routers import health_routers


def _paths(router):
    return sorted({r.path for r in router.routes})


def test_photo_routes():
    paths = _paths(photo_routers.router)
    assert "/api/blur-photo/everyone" in paths
    assert "/api/blur-photo/everyone/filtered" in paths


def test_video_routes_with_legacy_alias():
    paths = _paths(video_routers.router)
    assert "/api/blur-video/everyone" in paths
    assert "/api/blur-video/everyone/filtered" in paths
    # backward compat for the old 'filerer' typo
    assert "/api/blur-video/everyone/filerer" in paths


def test_timestamp_routes_with_legacy_alias():
    paths = _paths(video_timestamp_routers.router)
    assert "/api/blur-video-timestamp/everyone" in paths
    assert "/api/blur-video-timestamp/everyone/filtered" in paths
    assert "/api/blur-video-timestamp/everyone/filerer" in paths


def test_health_routes():
    paths = _paths(health_routers.router)
    assert "/healthz" in paths
    assert "/readyz" in paths


def test_full_app_builds():
    from fastapi.testclient import TestClient

    from src.main import create_app

    app = create_app()
    paths = sorted(create_app().openapi()["paths"])
    assert "/healthz" in paths
    assert "/api/blur-photo/everyone" in paths
    client = TestClient(app)
    assert client.get("/healthz").json() == {"ok": True}
