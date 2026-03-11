"""Tests for endpoints/models.py — covers missing lines (str, properties)."""
import pytest
from kuhl_haus.magpie.endpoints.models import (
    ScriptConfig,
    DnsResolver,
    DnsResolverList,
    EndpointModel,
)


@pytest.mark.django_db
def test_script_config_str():
    obj = ScriptConfig(name="http_health_check", application_name="canary")
    assert str(obj) == "http_health_check.canary"


@pytest.mark.django_db
def test_dns_resolver_str():
    obj = DnsResolver(name="google-dns", ip_address="8.8.8.8")
    assert str(obj) == "google-dns (8.8.8.8)"


@pytest.mark.django_db
def test_dns_resolver_to_json():
    obj = DnsResolver(name="cloudflare", ip_address="1.1.1.1")
    result = obj.to_json()
    assert result == {"name": "cloudflare", "ip_address": "1.1.1.1"}


@pytest.mark.django_db
def test_dns_resolver_list_str():
    resolver_list = DnsResolverList.objects.create(name="primary")
    assert "primary" in str(resolver_list)
    assert "0" in str(resolver_list)


@pytest.mark.django_db
def test_endpoint_model_str():
    obj = EndpointModel(mnemonic="api-health", hostname="api.example.com")
    assert str(obj) == "api-health - api.example.com"


@pytest.mark.django_db
def test_endpoint_url_basic():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="https",
        port=443,
        path="/health",
    )
    assert obj.url == "https://example.com:443/health"


@pytest.mark.django_db
def test_endpoint_url_empty_path():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="https",
        port=443,
        path="",
    )
    assert obj.url == "https://example.com:443/"


@pytest.mark.django_db
def test_endpoint_url_path_without_leading_slash():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="https",
        port=443,
        path="health",
    )
    assert obj.url == "https://example.com:443/health"


@pytest.mark.django_db
def test_endpoint_url_path_with_double_slash():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="https",
        port=443,
        path="//health//check",
    )
    assert obj.url == "https://example.com:443/health/check"


@pytest.mark.django_db
def test_endpoint_url_with_query():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="https",
        port=443,
        path="/search",
        query={"q": "test"},
    )
    url = obj.url
    assert url == "https://example.com:443/search?q=test"
    assert "q" in url


@pytest.mark.django_db
def test_endpoint_url_with_fragment():
    obj = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        scheme="http",
        port=80,
        path="/page",
        fragment="section1",
    )
    url = obj.url
    assert "section1" in url
