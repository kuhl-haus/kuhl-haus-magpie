"""Tests for canary_tasks/tasks.py — Celery task wrappers."""
import pytest
from unittest.mock import patch, MagicMock

from kuhl_haus.magpie.endpoints.models import (
    ScriptConfig,
    DnsResolver,
    DnsResolverList,
    EndpointModel,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def script_config_http(db):
    return ScriptConfig.objects.create(
        name="http_health_check",
        application_name="canary",
        log_level="INFO",
        carbon_metrics_enabled=False,
        carbon_server_ip=None,
        carbon_pickle_port=2004,
        namespace_root="test",
        metric_namespace="dev",
    )


@pytest.fixture
def script_config_tls(db):
    return ScriptConfig.objects.create(
        name="tls_check",
        application_name="canary",
        log_level="INFO",
        carbon_metrics_enabled=False,
        carbon_server_ip=None,
        carbon_pickle_port=2004,
        namespace_root="test",
        metric_namespace="dev",
    )


@pytest.fixture
def script_config_dns(db):
    return ScriptConfig.objects.create(
        name="dns_check",
        application_name="canary",
        log_level="INFO",
        carbon_metrics_enabled=False,
        carbon_server_ip=None,
        carbon_pickle_port=2004,
        namespace_root="test",
        metric_namespace="dev",
    )


@pytest.fixture
def basic_endpoint(db):
    return EndpointModel.objects.create(
        mnemonic="test-ep",
        hostname="192.0.2.1",
        scheme="https",
        port=443,
        path="/health",
        environment="prod",
        health_check=True,
        tls_check=True,
        dns_check=True,
        ignore=False,
    )


@pytest.fixture
def dns_endpoint(db):
    resolver = DnsResolver.objects.create(name="test-dns", ip_address="192.0.2.53")
    resolver_list = DnsResolverList.objects.create(name="test-resolvers")
    resolver_list.resolvers.add(resolver)
    return EndpointModel.objects.create(
        mnemonic="dns-ep",
        hostname="192.0.2.1",
        scheme="https",
        port=443,
        path="/health",
        environment="prod",
        health_check=True,
        tls_check=True,
        dns_check=True,
        ignore=False,
        dns_resolver_list=resolver_list,
    )


# ---------------------------------------------------------------------------
# http_health_check task tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_http_health_check_config_not_found():
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    result = http_health_check.run("nonexistent_config")
    assert result["status"] == "failed"
    assert "not found" in result["results"]["message"]


@pytest.mark.django_db
def test_http_health_check_no_endpoints(script_config_http):
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_health_check"):
            result = http_health_check.run("http_health_check")
    assert result["status"] == "success"
    assert "No metrics" in result["results"]["message"]


@pytest.mark.django_db
def test_http_health_check_with_endpoints(script_config_http, basic_endpoint):
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_health_check") as mock_check:
            mock_check.return_value = None
            result = http_health_check.run("http_health_check")
    assert result["status"] == "success"
    assert "metadata" in result
    assert result["metadata"]["script_config"]["name"] == "http_health_check"


@pytest.mark.django_db
def test_http_health_check_carbon_poster_instantiation_error(script_config_http):
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    with patch(
        "kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster",
        side_effect=Exception("connection refused"),
    ):
        result = http_health_check.run("http_health_check")
    assert result["status"] == "failed"
    assert "CarbonPoster" in result["results"]["message"]


@pytest.mark.django_db
def test_http_health_check_skips_ignored_endpoints(script_config_http, db):
    EndpointModel.objects.create(
        mnemonic="ignored-ep",
        hostname="192.0.2.99",
        ignore=True,
        health_check=True,
    )
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_health_check") as mock_check:
            result = http_health_check.run("http_health_check")
    # No endpoints (filter excludes ignore=True)
    assert result["status"] == "success"


# ---------------------------------------------------------------------------
# tls_check task tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tls_check_config_not_found():
    from kuhl_haus.magpie.canary_tasks.tasks import tls_check
    result = tls_check.run("nonexistent_config")
    assert result["status"] == "failed"
    assert "not found" in result["results"]["message"]


@pytest.mark.django_db
def test_tls_check_no_endpoints(script_config_tls):
    from kuhl_haus.magpie.canary_tasks.tasks import tls_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_tls_check"):
            result = tls_check.run("tls_check")
    assert result["status"] == "success"
    assert "No metrics" in result["results"]["message"]


@pytest.mark.django_db
def test_tls_check_with_endpoints(script_config_tls, basic_endpoint):
    from kuhl_haus.magpie.canary_tasks.tasks import tls_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_tls_check") as mock_check:
            mock_check.return_value = None
            result = tls_check.run("tls_check")
    assert result["status"] == "success"
    assert result["metadata"]["script_config"]["name"] == "tls_check"


@pytest.mark.django_db
def test_tls_check_carbon_poster_error(script_config_tls):
    from kuhl_haus.magpie.canary_tasks.tasks import tls_check
    with patch(
        "kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster",
        side_effect=Exception("tls error"),
    ):
        result = tls_check.run("tls_check")
    assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# dns_check task tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dns_check_config_not_found():
    from kuhl_haus.magpie.canary_tasks.tasks import dns_check
    result = dns_check.run("nonexistent_config")
    assert result["status"] == "failed"
    assert "not found" in result["results"]["message"]


@pytest.mark.django_db
def test_dns_check_no_endpoints(script_config_dns):
    from kuhl_haus.magpie.canary_tasks.tasks import dns_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.query_dns"):
            result = dns_check.run("dns_check")
    assert result["status"] == "success"
    assert "No metrics" in result["results"]["message"]


@pytest.mark.django_db
def test_dns_check_with_endpoints(script_config_dns, dns_endpoint):
    from kuhl_haus.magpie.canary_tasks.tasks import dns_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.return_value = None
        with patch("kuhl_haus.magpie.canary_tasks.tasks.query_dns") as mock_check:
            mock_check.return_value = None
            result = dns_check.run("dns_check")
    assert result["status"] == "success"
    assert result["metadata"]["script_config"]["name"] == "dns_check"


@pytest.mark.django_db
def test_dns_check_carbon_poster_error(script_config_dns):
    from kuhl_haus.magpie.canary_tasks.tasks import dns_check
    with patch(
        "kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster",
        side_effect=Exception("dns error"),
    ):
        result = dns_check.run("dns_check")
    assert result["status"] == "failed"


@pytest.mark.django_db
def test_http_health_check_metrics_exception_propagates(script_config_http, basic_endpoint):
    """Test that exceptions during metric posting are re-raised."""
    from kuhl_haus.magpie.canary_tasks.tasks import http_health_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.side_effect = RuntimeError("carbon down")
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_health_check"):
            with pytest.raises(RuntimeError):
                http_health_check.run("http_health_check")


@pytest.mark.django_db
def test_tls_check_metrics_exception_propagates(script_config_tls, basic_endpoint):
    from kuhl_haus.magpie.canary_tasks.tasks import tls_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.side_effect = RuntimeError("carbon down")
        with patch("kuhl_haus.magpie.canary_tasks.tasks.invoke_tls_check"):
            with pytest.raises(RuntimeError):
                tls_check.run("tls_check")


@pytest.mark.django_db
def test_dns_check_metrics_exception_propagates(script_config_dns, dns_endpoint):
    from kuhl_haus.magpie.canary_tasks.tasks import dns_check
    with patch("kuhl_haus.magpie.canary_tasks.tasks.CarbonPoster") as mock_cp_class:
        mock_cp_class.return_value.post_metrics.side_effect = RuntimeError("carbon down")
        with patch("kuhl_haus.magpie.canary_tasks.tasks.query_dns"):
            with pytest.raises(RuntimeError):
                dns_check.run("dns_check")
