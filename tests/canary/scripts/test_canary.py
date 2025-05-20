import pytest
from unittest.mock import Mock, patch, MagicMock, call

from kuhl_haus.magpie.canary.scripts.canary import Canary
from kuhl_haus.magpie.endpoints.models import DnsResolver, DnsResolverList, EndpointModel


@pytest.fixture
def mock_recorder():
    recorder = MagicMock()
    recorder.logger = MagicMock()
    recorder.get_metrics = MagicMock(return_value={})
    recorder.log_metrics = MagicMock()
    return recorder


@pytest.fixture
def mock_endpoint():
    endpoint = MagicMock(spec=EndpointModel)
    endpoint.mnemonic = "test-endpoint"
    endpoint.hostname = "test.example.com"
    endpoint.ignore = False
    return endpoint


@pytest.fixture
def mock_resolver():
    resolver = MagicMock(spec=DnsResolver)
    resolver.name = "test-resolver"
    return resolver


@patch('kuhl_haus.magpie.canary.scripts.canary.get_default_resolver_list')
@patch('kuhl_haus.magpie.canary.scripts.canary.get_endpoints')
def test_invoke_no_endpoints(patched_get_endpoints, get_default_resolver_list, mock_recorder):
    """Test that Canary exits gracefully when no endpoints are found."""
    # Arrange
    get_default_resolver_list.return_value = []
    patched_get_endpoints.return_value = []
    sut = Canary

    # Act
    sut(recorder=mock_recorder, delay=0, count=1)

    # Assert
    mock_recorder.logger.info.assert_called_once_with("No endpoints found, exiting.")
    mock_recorder.get_metrics.assert_not_called()
    mock_recorder.log_metrics.assert_not_called()


@patch('kuhl_haus.magpie.canary.scripts.canary.get_default_resolver_list')
@patch('kuhl_haus.magpie.canary.scripts.canary.get_endpoints')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_health_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_tls_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.query_dns')
def test_invoke_skips_ignored_endpoints(
        mock_query_dns, mock_invoke_tls, mock_invoke_health, get_endpoints, get_default_resolver_list,
        mock_recorder, mock_endpoint
):
    """Test that Canary skips endpoints with ignore flag set."""
    # Arrange
    ignored_endpoint = MagicMock(spec=EndpointModel)
    ignored_endpoint.mnemonic = "ignored-endpoint"
    ignored_endpoint.ignore = True

    get_endpoints.return_value = [mock_endpoint, ignored_endpoint]
    get_default_resolver_list.return_value = []

    sut = Canary

    # Act
    sut(recorder=mock_recorder, delay=0, count=1)

    # Assert
    mock_recorder.logger.info.assert_called_with(f"Skipping {ignored_endpoint.mnemonic}")
    assert mock_invoke_health.call_count == 1  # Only one endpoint processed
    assert mock_invoke_tls.call_count == 1
    assert mock_query_dns.call_count == 0  # No resolvers provided


@patch('kuhl_haus.magpie.canary.scripts.canary.get_default_resolver_list')
@patch('kuhl_haus.magpie.canary.scripts.canary.get_endpoints')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_health_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_tls_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.query_dns')
def test_invoke_calls_all_checks(
        mock_query_dns, mock_invoke_tls, mock_invoke_health, get_endpoints, get_default_resolver_list,
        mock_recorder, mock_endpoint, mock_resolver
):
    """Test that Canary invokes all checks for valid endpoints."""
    # Arrange
    get_endpoints.return_value = [mock_endpoint]
    get_default_resolver_list.return_value = [mock_resolver]

    sut = Canary

    # Define the metrics dictionaries that should be created
    dns_metrics = {"dns_metric": "value"}
    tls_metrics = {"tls_metric": "value"}
    health_metrics = {"health_metric": "value"}

    # Configure return values for get_metrics based on parameters
    def get_metrics_side_effect(name, mnemonic, hostname):
        if name == "dns":
            return dns_metrics
        elif name == "tls":
            return tls_metrics
        else:
            return health_metrics

    mock_recorder.get_metrics.side_effect = get_metrics_side_effect

    # Act
    sut(recorder=mock_recorder, delay=0, count=1)

    # Assert
    # Check that all checks were called with correct parameters
    mock_query_dns.assert_called_once_with(
        resolvers=[mock_resolver],
        ep=mock_endpoint,
        metrics=dns_metrics,
        logger=mock_recorder.logger
    )

    mock_invoke_tls.assert_called_once_with(
        ep=mock_endpoint,
        metrics=tls_metrics,
        logger=mock_recorder.logger
    )

    mock_invoke_health.assert_called_once_with(
        ep=mock_endpoint,
        metrics=health_metrics,
        logger=mock_recorder.logger
    )

    # Verify metrics were logged for each check
    assert mock_recorder.log_metrics.call_count == 3
    mock_recorder.log_metrics.assert_any_call(dns_metrics)
    mock_recorder.log_metrics.assert_any_call(tls_metrics)
    mock_recorder.log_metrics.assert_any_call(health_metrics)


@patch('kuhl_haus.magpie.canary.scripts.canary.get_default_resolver_list')
@patch('kuhl_haus.magpie.canary.scripts.canary.get_endpoints')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_health_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.invoke_tls_check')
@patch('kuhl_haus.magpie.canary.scripts.canary.query_dns')
def test_invoke_handles_exceptions(
        mock_query_dns, mock_invoke_tls, mock_invoke_health,
        get_endpoints, get_default_resolver_list, mock_recorder, mock_endpoint
):
    """Test that Canary handles exceptions from checks gracefully."""
    # Arrange
    get_endpoints.return_value = [mock_endpoint]
    get_default_resolver_list.return_value = []

    # Configure one of the invokes to raise an exception
    test_exception = RuntimeError("Test exception")
    mock_invoke_tls.side_effect = test_exception

    sut = Canary

    # Act
    sut(recorder=mock_recorder, delay=0, count=1)

    # Assert
    # Check that exception was logged
    mock_recorder.logger.exception.assert_called_once_with(
        msg=f"Unhandled exception testing mnemonic:{mock_endpoint.mnemonic}",
        exc_info=test_exception
    )


@patch('kuhl_haus.magpie.canary.scripts.canary.get_default_resolver_list')
@patch('kuhl_haus.magpie.canary.scripts.canary.get_endpoints')
def test_invoke_dns_check_skips_when_no_resolvers(
        get_endpoints, get_default_resolver_list, mock_recorder, mock_endpoint
):
    """Test that DNS check is skipped when no resolvers are available."""
    # Arrange
    get_endpoints.return_value = [mock_endpoint]
    get_default_resolver_list.return_value = []

    sut = Canary

    # Act
    with patch('kuhl_haus.magpie.canary.scripts.canary.query_dns') as mock_query_dns:
        sut(recorder=mock_recorder, delay=0, count=1)

    # Assert
    mock_query_dns.assert_not_called()


@patch('kuhl_haus.magpie.canary.scripts.canary.Script.__init__')
def test_canary_init_calls_parent_init(mock_script_init):
    """Test that Canary's __init__ calls the parent class's __init__."""
    # Arrange
    test_kwargs = {"recorder": MagicMock(), "delay": 0, "count": 1}
    sut = Canary

    # Act
    sut(**test_kwargs)

    # Assert
    mock_script_init.assert_called_once_with(**test_kwargs)
