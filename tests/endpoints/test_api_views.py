"""Tests for endpoints/api_views.py."""
import pytest
from django.contrib.auth.models import User
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.test import APIClient

from kuhl_haus.magpie.endpoints.api_views import EndpointModelViewSet
from kuhl_haus.magpie.endpoints.models import (
    ScriptConfig,
    DnsResolver,
    DnsResolverList,
    EndpointModel,
)


@pytest.fixture
def api_client():
    return APIClient()


# DRF's APIView.permission_classes/authentication_classes are class
# attributes assigned ONCE from api_settings.DEFAULT_* at class-body
# execution time (see rest_framework/views.py) -- i.e. snapshotted at
# Django app import/boot time. django.test.override_settings(REST_FRAMEWORK=
# ...) changes django.conf.settings.REST_FRAMEWORK and does trigger DRF's
# api_settings.reload(), but that does NOT retroactively change the already-
# bound class attributes on EndpointModelViewSet -- a real deployment reads
# MAGPIE_UNSAFE_SETTING_DISABLE_API_AUTH once at process boot too (a restart
# is required to change it), so directly monkeypatching the viewset's own
# class attributes for the duration of each test both sidesteps that DRF
# gotcha and matches how the toggle actually behaves in production.
_AUTH_CLASSES = [TokenAuthentication, SessionAuthentication]


def _set_endpoint_auth(monkeypatch, permission_classes):
    """Patch EndpointModelViewSet's auth classes for one test.

    See the _AUTH_CLASSES comment above for why this monkeypatches the
    viewset directly instead of using override_settings.
    """
    monkeypatch.setattr(EndpointModelViewSet, "authentication_classes", _AUTH_CLASSES)
    monkeypatch.setattr(EndpointModelViewSet, "permission_classes", permission_classes)


@pytest.mark.django_db
def test_script_config_list_empty(api_client):
    response = api_client.get("/api/scripts/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_script_config_list_with_data(api_client):
    ScriptConfig.objects.create(
        name="http_health_check",
        application_name="canary",
    )
    response = api_client.get("/api/scripts/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "http_health_check"


@pytest.mark.django_db
def test_endpoint_model_list_empty(api_client):
    response = api_client.get("/api/endpoints/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


@pytest.mark.django_db
def test_endpoint_model_list_with_data(api_client):
    EndpointModel.objects.create(
        mnemonic="test-ep",
        hostname="test.example.com",
    )
    response = api_client.get("/api/endpoints/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["mnemonic"] == "test-ep"


@pytest.mark.django_db
def test_dns_resolver_list_empty(api_client):
    response = api_client.get("/api/resolvers/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_dns_resolver_list_with_data(api_client):
    DnsResolver.objects.create(name="google", ip_address="8.8.8.8")
    response = api_client.get("/api/resolvers/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "google"


@pytest.mark.django_db
def test_dns_resolver_list_viewset_list_empty(api_client):
    response = api_client.get("/api/resolver-lists/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_dns_resolver_list_viewset_list_with_data(api_client):
    DnsResolverList.objects.create(name="primary-resolvers")
    response = api_client.get("/api/resolver-lists/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "primary-resolvers"


@pytest.mark.django_db
def test_dns_resolver_list_endpoints_action_empty(api_client):
    resolver_list = DnsResolverList.objects.create(name="test-list")
    response = api_client.get(f"/api/resolver-lists/{resolver_list.pk}/endpoints/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_dns_resolver_list_endpoints_action_with_data(api_client):
    resolver_list = DnsResolverList.objects.create(name="test-list")
    EndpointModel.objects.create(
        mnemonic="dns-ep",
        hostname="dns.example.com",
        dns_resolver_list=resolver_list,
    )
    response = api_client.get(f"/api/resolver-lists/{resolver_list.pk}/endpoints/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["mnemonic"] == "dns-ep"


# --- #29: REST API auth regression tests ---------------------------------
# The bug: every viewset above had no permission_classes, so DRF's own
# AllowAny default applied to writes too -- an unauthenticated POST could
# create/modify/delete any endpoint. These confirm the fix (auth required
# for writes by default) and the documented escape hatch
# (MAGPIE_UNSAFE_SETTING_DISABLE_API_AUTH) both actually work. Each test
# monkeypatches EndpointModelViewSet's class attributes directly rather
# than using override_settings(REST_FRAMEWORK=...) -- see the comment above
# _AUTH_CLASSES for why that doesn't work here.

@pytest.mark.django_db
def test_endpoint_create_unauthenticated_rejected_by_default(
    api_client, monkeypatch
):
    """Unauthenticated writes are rejected by default (the bug fixed in #29)."""
    _set_endpoint_auth(monkeypatch, [IsAuthenticatedOrReadOnly])
    response = api_client.post(
        "/api/endpoints/",
        {"mnemonic": "unauth-test", "hostname": "unauth.example.com"},
        format="json",
    )
    assert response.status_code in (401, 403)
    assert not EndpointModel.objects.filter(mnemonic="unauth-test").exists()


@pytest.mark.django_db
def test_endpoint_read_unauthenticated_still_allowed_by_default(
    api_client, monkeypatch
):
    """Reads stay open under the safe default -- only writes require auth."""
    EndpointModel.objects.create(mnemonic="read-test", hostname="read.example.com")
    _set_endpoint_auth(monkeypatch, [IsAuthenticatedOrReadOnly])
    response = api_client.get("/api/endpoints/")
    assert response.status_code == 200
    assert any(e["mnemonic"] == "read-test" for e in response.data)


@pytest.mark.django_db
def test_endpoint_create_authenticated_via_token_succeeds_under_default(
    api_client, monkeypatch
):
    """A token-authenticated caller can still create an endpoint under the default."""
    user = User.objects.create_user(username="api-user", password="irrelevant")
    token = Token.objects.create(user=user)
    _set_endpoint_auth(monkeypatch, [IsAuthenticatedOrReadOnly])
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    response = api_client.post(
        "/api/endpoints/",
        {"mnemonic": "auth-test", "hostname": "auth.example.com"},
        format="json",
    )
    assert response.status_code == 201
    assert EndpointModel.objects.filter(mnemonic="auth-test").exists()


@pytest.mark.django_db
def test_endpoint_create_unauthenticated_allowed_when_unsafe_setting_enabled(
    api_client, monkeypatch
):
    """MAGPIE_UNSAFE_SETTING_DISABLE_API_AUTH=True restores the old, open behavior."""
    _set_endpoint_auth(monkeypatch, [AllowAny])
    response = api_client.post(
        "/api/endpoints/",
        {"mnemonic": "unsafe-test", "hostname": "unsafe.example.com"},
        format="json",
    )
    assert response.status_code == 201
    assert EndpointModel.objects.filter(mnemonic="unsafe-test").exists()
