"""Tests for web/settings.py conditional configuration blocks."""
import importlib
import pytest


def test_settings_with_magpie_domain(monkeypatch):
    """Test that setting MAGPIE_DOMAIN uses it for session/CSRF cookies and SSL header."""
    monkeypatch.setenv("MAGPIE_DOMAIN", "example.com")
    import kuhl_haus.magpie.web.settings as settings_module
    try:
        importlib.reload(settings_module)
        assert settings_module.SESSION_COOKIE_DOMAIN == "example.com"
        assert settings_module.CSRF_COOKIE_DOMAIN == "example.com"
        assert settings_module.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    finally:
        monkeypatch.delenv("MAGPIE_DOMAIN")
        importlib.reload(settings_module)


def test_settings_disable_https(monkeypatch):
    """Test that DISABLE_HTTPS=True sets insecure cookie settings."""
    monkeypatch.setenv("DISABLE_HTTPS", "True")
    import kuhl_haus.magpie.web.settings as settings_module
    try:
        importlib.reload(settings_module)
        assert settings_module.SESSION_COOKIE_SECURE is False
        assert settings_module.CSRF_COOKIE_SECURE is False
        assert settings_module.COOKIE_SAMESITE == "Lax"
        assert settings_module.SESSION_COOKIE_SAMESITE == "Lax"
    finally:
        monkeypatch.delenv("DISABLE_HTTPS")
        importlib.reload(settings_module)


def test_settings_with_magpie_domain_and_disable_https(monkeypatch):
    """Test MAGPIE_DOMAIN set with DISABLE_HTTPS=True covers the branch that skips SECURE_PROXY_SSL_HEADER."""
    monkeypatch.setenv("MAGPIE_DOMAIN", "example.com")
    monkeypatch.setenv("DISABLE_HTTPS", "True")
    import kuhl_haus.magpie.web.settings as settings_module
    try:
        importlib.reload(settings_module)
        assert settings_module.SESSION_COOKIE_DOMAIN == "example.com"
        assert settings_module.SESSION_COOKIE_SECURE is False
    finally:
        monkeypatch.delenv("MAGPIE_DOMAIN")
        monkeypatch.delenv("DISABLE_HTTPS")
        importlib.reload(settings_module)


def test_settings_postgres(monkeypatch):
    """Test that POSTGRES_HOST triggers the PostgreSQL DATABASES config."""
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
    import kuhl_haus.magpie.web.settings as settings_module
    try:
        importlib.reload(settings_module)
        assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert settings_module.DATABASES["default"]["NAME"] == "testdb"
    finally:
        monkeypatch.delenv("POSTGRES_HOST")
        monkeypatch.delenv("POSTGRES_DB")
        monkeypatch.delenv("POSTGRES_USER")
        monkeypatch.delenv("POSTGRES_PASSWORD")
        importlib.reload(settings_module)
