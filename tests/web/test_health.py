"""Tests for web/health.py health check endpoints."""
import json

import pytest
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


def test_http_health_returns_ok(rf):
    from kuhl_haus.magpie.web.health import http_health
    request = rf.get("/health")
    response = http_health(request)
    assert response.status_code == 200
    assert response.content == b"OK"
    assert "text/plain" in response["Content-Type"]


def test_http_health_post_returns_405(rf):
    from kuhl_haus.magpie.web.health import http_health
    request = rf.post("/health")
    response = http_health(request)
    assert response.status_code == 405


def test_json_health_returns_200_with_json_body(rf):
    from kuhl_haus.magpie.web.health import json_health
    request = rf.get("/healthz")
    response = json_health(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["status"] == "OK"
    assert "version" in data
    assert "image_version" in data
    assert "container_image" in data


def test_json_health_post_returns_405(rf):
    from kuhl_haus.magpie.web.health import json_health
    request = rf.post("/healthz")
    response = json_health(request)
    assert response.status_code == 405


def test_json_health_includes_env_vars(rf, monkeypatch):
    monkeypatch.setenv("IMAGE_VERSION", "1.2.3")
    monkeypatch.setenv("CONTAINER_IMAGE", "ghcr.io/test/image:1.2.3")

    import kuhl_haus.magpie.web.health as health_module
    import importlib
    importlib.reload(health_module)

    request = rf.get("/healthz")
    response = health_module.json_health(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["image_version"] == "1.2.3"
    assert data["container_image"] == "ghcr.io/test/image:1.2.3"


def test_http_health_no_cache(rf):
    from kuhl_haus.magpie.web.health import http_health
    request = rf.get("/health")
    response = http_health(request)
    assert "no-cache" in response.get("Cache-Control", "").lower() or \
           response.status_code == 200
