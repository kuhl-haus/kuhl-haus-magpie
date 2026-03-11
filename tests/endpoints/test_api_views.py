"""Tests for endpoints/api_views.py."""
import pytest
from rest_framework.test import APIClient

from kuhl_haus.magpie.endpoints.models import (
    ScriptConfig,
    DnsResolver,
    DnsResolverList,
    EndpointModel,
)


@pytest.fixture
def api_client():
    return APIClient()


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
