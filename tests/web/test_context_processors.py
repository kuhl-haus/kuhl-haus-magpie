"""Tests for web/context_processors.py."""
import pytest


@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


def test_version_info_cache_miss(monkeypatch):
    monkeypatch.setenv("IMAGE_VERSION", "v1.0.0")
    monkeypatch.setenv("CONTAINER_IMAGE", "ghcr.io/test/app:v1.0.0")

    from kuhl_haus.magpie.web.context_processors import version_info

    result = version_info(None)

    assert "version_info" in result
    assert result["version_info"]["image_version"] == "v1.0.0"
    assert result["version_info"]["container_image"] == "ghcr.io/test/app:v1.0.0"


def test_version_info_cache_hit():
    from django.core.cache import cache
    from kuhl_haus.magpie.web.context_processors import version_info

    cached_value = {
        "version_info": {
            "image_version": "cached-version",
            "container_image": "cached-image",
        }
    }
    cache.set("version_info", cached_value, 300)

    result = version_info(None)

    assert result == cached_value
    assert result["version_info"]["image_version"] == "cached-version"


def test_version_info_sets_cache(monkeypatch):
    from django.core.cache import cache
    from kuhl_haus.magpie.web.context_processors import version_info

    monkeypatch.setenv("IMAGE_VERSION", "v2.0.0")

    assert cache.get("version_info") is None
    version_info(None)
    assert cache.get("version_info") is not None


def test_domain_info_cache_miss(monkeypatch):
    monkeypatch.setenv("MAGPIE_DOMAIN", "example.com")
    monkeypatch.setenv("FLOWER_DOMAIN", "flower.example.com")

    from kuhl_haus.magpie.web.context_processors import domain_info

    result = domain_info(None)

    assert "MAGPIE_DOMAIN" in result
    assert "FLOWER_DOMAIN" in result
    assert result["MAGPIE_DOMAIN"] == "example.com"
    assert result["FLOWER_DOMAIN"] == "flower.example.com"


def test_domain_info_cache_hit():
    from django.core.cache import cache
    from kuhl_haus.magpie.web.context_processors import domain_info

    cached_value = {
        "MAGPIE_DOMAIN": "cached.example.com",
        "FLOWER_DOMAIN": "cached.flower.com",
    }
    cache.set("domain_info", cached_value, 300)

    result = domain_info(None)

    assert result == cached_value
    assert result["MAGPIE_DOMAIN"] == "cached.example.com"


def test_domain_info_sets_cache(monkeypatch):
    from django.core.cache import cache
    from kuhl_haus.magpie.web.context_processors import domain_info

    assert cache.get("domain_info") is None
    domain_info(None)
    assert cache.get("domain_info") is not None
