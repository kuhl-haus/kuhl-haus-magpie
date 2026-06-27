"""Tests for endpoints/serializers.py."""
import pytest
from kuhl_haus.magpie.endpoints.models import (
    ScriptConfig,
    DnsResolver,
    DnsResolverList,
    EndpointModel,
)
from kuhl_haus.magpie.endpoints.serializers import (
    ScriptConfigSerializer,
    DnsResolverSerializer,
    DnsResolverListSerializer,
    EndpointModelSerializer,
)


@pytest.mark.django_db
def test_script_config_serializer_fields():
    obj = ScriptConfig.objects.create(
        name="http_health_check",
        application_name="canary",
        log_level="INFO",
        carbon_metrics_enabled=False,
        carbon_pickle_port=2004,
    )
    serializer = ScriptConfigSerializer(obj)
    data = serializer.data
    assert data["name"] == "http_health_check"
    assert data["application_name"] == "canary"
    assert data["log_level"] == "INFO"
    assert data["carbon_metrics_enabled"] is False
    assert data["carbon_pickle_port"] == 2004
    assert "namespace_root" in data
    assert "metric_namespace" in data
    assert "carbon_server_ip" in data


@pytest.mark.django_db
def test_dns_resolver_serializer_fields():
    obj = DnsResolver.objects.create(name="google", ip_address="8.8.8.8")
    serializer = DnsResolverSerializer(obj)
    data = serializer.data
    assert data["name"] == "google"
    assert data["ip_address"] == "8.8.8.8"


@pytest.mark.django_db
def test_dns_resolver_list_serializer_with_resolvers():
    resolver = DnsResolver.objects.create(name="cf-dns", ip_address="1.1.1.1")
    resolver_list = DnsResolverList.objects.create(name="primary")
    resolver_list.resolvers.add(resolver)

    serializer = DnsResolverListSerializer(resolver_list)
    data = serializer.data

    assert data["name"] == "primary"
    assert len(data["resolvers"]) == 1
    assert data["resolvers"][0]["name"] == "cf-dns"
    assert data["resolvers"][0]["ip_address"] == "1.1.1.1"


@pytest.mark.django_db
def test_dns_resolver_list_serializer_empty():
    resolver_list = DnsResolverList.objects.create(name="empty-list")
    serializer = DnsResolverListSerializer(resolver_list)
    data = serializer.data
    assert data["name"] == "empty-list"
    assert data["resolvers"] == []


@pytest.mark.django_db
def test_endpoint_model_serializer_fields():
    obj = EndpointModel.objects.create(
        mnemonic="api-health",
        hostname="api.example.com",
        scheme="https",
        port=443,
        path="/health",
        environment="prod",
        verb="GET",
        healthy_status_code=200,
        connect_timeout=7.0,
        read_timeout=7.0,
        ignore=False,
        health_check=True,
        tls_check=True,
        dns_check=True,
    )
    serializer = EndpointModelSerializer(obj)
    data = serializer.data
    assert data["mnemonic"] == "api-health"
    assert data["hostname"] == "api.example.com"
    assert data["scheme"] == "https"
    assert data["port"] == 443
    assert data["environment"] == "prod"
    assert data["verb"] == "GET"
    assert data["healthy_status_code"] == 200
    assert data["health_check"] is True
    assert data["tls_check"] is True
    assert data["dns_check"] is True
    assert data["dns_resolver_list"] is None


@pytest.mark.django_db
def test_endpoint_model_serializer_with_dns_resolver_list_expect_slug_in_output():
    resolver_list = DnsResolverList.objects.create(name="default")
    endpoint = EndpointModel.objects.create(
        mnemonic="ep-dns",
        hostname="example.com",
        dns_resolver_list=resolver_list,
    )
    data = EndpointModelSerializer(endpoint).data
    assert data["dns_resolver_list"] == "default"


@pytest.mark.django_db
def test_endpoint_model_serializer_with_no_dns_resolver_list_expect_null():
    endpoint = EndpointModel.objects.create(
        mnemonic="ep-no-dns",
        hostname="example.com",
    )
    data = EndpointModelSerializer(endpoint).data
    assert data["dns_resolver_list"] is None


@pytest.mark.django_db
def test_endpoint_model_serializer_with_valid_resolver_list_name_expect_deserializes():
    DnsResolverList.objects.create(name="default")
    serializer = EndpointModelSerializer(
        data={"mnemonic": "ep", "hostname": "h.com", "dns_resolver_list": "default"}
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["dns_resolver_list"].name == "default"


@pytest.mark.django_db
def test_endpoint_model_serializer_with_invalid_resolver_list_name_expect_validation_error():
    serializer = EndpointModelSerializer(
        data={"mnemonic": "ep", "hostname": "h.com", "dns_resolver_list": "nonexistent"}
    )
    assert not serializer.is_valid()
    assert "dns_resolver_list" in serializer.errors


@pytest.mark.django_db
def test_endpoint_model_serializer_list():
    EndpointModel.objects.create(
        mnemonic="ep-one",
        hostname="one.example.com",
    )
    EndpointModel.objects.create(
        mnemonic="ep-two",
        hostname="two.example.com",
    )
    queryset = EndpointModel.objects.all()
    serializer = EndpointModelSerializer(queryset, many=True)
    data = serializer.data
    assert len(data) == 2
