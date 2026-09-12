"""Tests for endpoints/api_views.py."""
import pytest
from django.contrib.auth.models import User
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
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


_AUTH_CLASSES = [TokenAuthentication, SessionAuthentication]


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
# create/modify/delete any endpoint. These run against the REAL branch
# settings the test process already booted with (no monkeypatching) so
# they are genuine end-to-end regression guards, not a re-test of DRF
# itself: per Bishop's review on PR #30, a version of these tests that
# monkeypatched EndpointModelViewSet's permission_classes to the value it
# then asserted on stayed green even when a viewset opted back out with
# its own `permission_classes = [AllowAny]` -- it only proved "DRF
# enforces what it's told," not "this application tells it the right
# thing." Removing the monkeypatch (except in the unsafe-setting test
# below, which has a real reason for it) closes that gap.

@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, payload, model",
    [
        pytest.param(
            "/api/endpoints/",
            {"mnemonic": "no-auth-test", "hostname": "no-auth.example.com"},
            EndpointModel,
            id="endpoints",
        ),
        pytest.param(
            "/api/resolvers/",
            {"name": "no-auth-test", "ip_address": "10.0.0.1"},
            DnsResolver,
            id="resolvers",
        ),
        pytest.param(
            "/api/resolver-lists/",
            {"name": "no-auth-test"},
            DnsResolverList,
            id="resolver-lists",
        ),
        pytest.param(
            "/api/scripts/",
            {"name": "no-auth-test", "application_name": "no-auth-app"},
            ScriptConfig,
            id="scripts",
        ),
    ],
)
def test_api_write_with_no_auth_expect_401(api_client, url, payload, model):
    """
    Ensures every one of the four viewsets rejects an unauthenticated write
    under the real, unpatched branch settings (#29). The fix applies
    globally today via web/settings.py's REST_FRAMEWORK block; this is
    what keeps it global if a future per-viewset override reintroduces
    the hole for just one of the four.

    :param model: model class used to assert nothing was persisted
    """
    # Arrange
    count_before = model.objects.count()

    # Act
    response = api_client.post(url, payload, format="json")

    # Assert
    assert response.status_code == 401
    assert model.objects.count() == count_before


@pytest.mark.django_db
def test_endpoint_list_with_no_auth_expect_200(api_client):
    """Reads stay open under the real branch settings -- only writes need auth (#29)."""
    # Arrange
    EndpointModel.objects.create(mnemonic="read-test", hostname="read.example.com")

    # Act
    response = api_client.get("/api/endpoints/")

    # Assert
    assert response.status_code == 200
    assert any(e["mnemonic"] == "read-test" for e in response.data)


@pytest.mark.django_db
def test_endpoint_create_with_token_expect_201(api_client):
    """A token-authenticated caller can still write under real branch settings (#29)."""
    # Arrange
    user = User.objects.create_user(username="api-user", password="irrelevant")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # Act
    response = api_client.post(
        "/api/endpoints/",
        {"mnemonic": "auth-test", "hostname": "auth.example.com"},
        format="json",
    )

    # Assert
    assert response.status_code == 201
    assert EndpointModel.objects.filter(mnemonic="auth-test").exists()


@pytest.mark.django_db
def test_endpoint_create_with_unsafe_setting_expect_201(api_client, monkeypatch):
    """
    MAGPIE_UNSAFE_SETTING_DISABLE_API_AUTH=True restores the old, open behavior.

    This is the ONLY test in this module that monkeypatches
    EndpointModelViewSet's class attributes directly, rather than relying
    on the real branch settings the process already booted with like the
    three tests above. It has to: exercising both the safe default and the
    unsafe opt-out in the same pytest run means one of them can't come
    from the actual settings.py the process started with. DRF's
    APIView.permission_classes/authentication_classes are class attributes
    snapshotted once from api_settings at class-body-execution time, so a
    later override_settings(REST_FRAMEWORK=...) doesn't reach them --
    hence monkeypatching the viewset directly instead. The settings.py
    toggle itself is unit-tested directly in tests/web/test_settings.py,
    and only takes effect via an actual process restart in production
    anyway, which this monkeypatch stands in for.
    """
    # Arrange
    monkeypatch.setattr(EndpointModelViewSet, "authentication_classes", _AUTH_CLASSES)
    monkeypatch.setattr(EndpointModelViewSet, "permission_classes", [AllowAny])

    # Act
    response = api_client.post(
        "/api/endpoints/",
        {"mnemonic": "unsafe-test", "hostname": "unsafe.example.com"},
        format="json",
    )

    # Assert
    assert response.status_code == 201
    assert EndpointModel.objects.filter(mnemonic="unsafe-test").exists()
