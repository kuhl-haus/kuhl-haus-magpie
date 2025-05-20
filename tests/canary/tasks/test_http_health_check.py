import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
import requests

from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.endpoints.models import EndpointModel
from kuhl_haus.magpie.canary.tasks.http_health_check import invoke_health_check, handle_json_response


@pytest.fixture
def mock_metrics():
    """Fixture for a mock Metrics object."""
    metrics = MagicMock(spec=Metrics)
    metrics.attributes = {}
    metrics.set_counter = MagicMock()
    metrics.mnemonic = "test_mnemonic"
    metrics.version_to_float = MagicMock(return_value=1.0)
    return metrics


@pytest.fixture
def mock_logger():
    """Fixture for a mock Logger object."""
    return MagicMock()


@pytest.fixture
def endpoint_model():
    """Fixture for an EndpointModel with default test values."""
    return EndpointModel(
        mnemonic="test-endpoint",
        hostname="test.example.com",
        port=8080,
        path="/health",
        scheme="http",
        connect_timeout=1.0,
        read_timeout=2.0,
        healthy_status_code=200,
        response_format="text",
        status_key="status",
        healthy_status="UP",
        version_key="version"
    )


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_success_with_status_code(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test successful health check validated by status code."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.headers = {}
    mock_get.return_value = mock_response

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_get.assert_called_once_with(
        url=endpoint_model.url,
        timeout=(endpoint_model.connect_timeout, endpoint_model.read_timeout)
    )
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('responses', 1),
    ])

    assert 'response_time' in mock_metrics.attributes
    assert 'response_time_ms' in mock_metrics.attributes
    assert mock_metrics.attributes['status_code'] == 200
    assert mock_metrics.attributes['text'] == "OK"


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_error_status_code(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test health check with error status code."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.headers = {}
    mock_get.return_value = mock_response

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('errors', 1),
    ])
    # mock_metrics.set_counter.assert_called_once_with('errors', 1)
    assert mock_metrics.attributes['status_code'] == 500


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_response_headers(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test that response headers are correctly processed."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.headers = {
        "X-Request-Time": "123",
        "X-Request-Time-MS": "123",
        "X-Metrics-Time": "456",
        "X-Metrics-Time-MS": "456"
    }
    mock_get.return_value = mock_response

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    assert mock_metrics.attributes['request_time'] == "123"
    assert mock_metrics.attributes['request_time_ms'] == "123"
    assert mock_metrics.attributes['metrics_time'] == "456"
    assert mock_metrics.attributes['metrics_time_ms'] == "456"


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_connect_timeout(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test health check connection timeout exception handling."""
    # Arrange
    mock_get.side_effect = requests.ConnectTimeout("Connection timed out")

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_logger.exception.assert_called_once()
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('exceptions', 1),
    ])
    assert 'exception' in mock_metrics.attributes
    assert mock_metrics.attributes['response_time'] == 3  # sum of connect and read timeout in seconds


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_read_timeout(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test health check read timeout exception handling."""
    # Arrange
    mock_get.side_effect = requests.ReadTimeout("Read timed out")

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_logger.exception.assert_called_once()
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('exceptions', 1),
    ])
    assert 'exception' in mock_metrics.attributes


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_unhandled_exception(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test health check with an unhandled exception."""
    # Arrange
    mock_get.side_effect = Exception("Unexpected error")

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_logger.exception.assert_called_once()
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('exceptions', 1),
    ])
    assert 'exception' in mock_metrics.attributes


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.get')
def test_invoke_health_check_json_response_success(mock_get, endpoint_model, mock_metrics, mock_logger):
    """Test health check with successful JSON response."""
    # Arrange
    endpoint_model.response_format = "json"  # Changed from json_response = True
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({"status": "UP", "version": "1.2.3"})
    mock_response.headers = {}
    mock_get.return_value = mock_response

    # Act
    invoke_health_check(ep=endpoint_model, metrics=mock_metrics, logger=mock_logger)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('responses', 1),
    ])
    assert mock_metrics.attributes['version'] == 1.0
    mock_metrics.version_to_float.assert_called_once_with("1.2.3")


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.json.loads')
def test_handle_json_response_success(mock_json_loads, endpoint_model, mock_metrics):
    """Test handling successful JSON response."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = '{"status":"UP", "version":"1.2.3"}'
    mock_json_loads.return_value = {"status": "UP", "version": "1.2.3"}

    # Act
    handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('responses', 1),
    ])
    mock_metrics.version_to_float.assert_called_once_with("1.2.3")
    assert mock_metrics.attributes['version'] == 1.0


def test_handle_json_response_error_status(endpoint_model, mock_metrics):
    """Test handling JSON response with error status."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = '{"status":"DOWN", "version":"1.2.3"}'

    # Act
    handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('errors', 1),
    ])
    mock_metrics.version_to_float.assert_called_once_with("1.2.3")
    assert mock_metrics.attributes['version'] == 1.0


def test_handle_json_response_missing_status(endpoint_model, mock_metrics):
    """Test handling JSON response with missing status key."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = '{"version":"1.2.3"}'

    # Act
    handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('errors', 1),
    ])
    mock_metrics.version_to_float.assert_called_once_with("1.2.3")
    assert mock_metrics.attributes['version'] == 1.0


def test_handle_json_response_missing_version(endpoint_model, mock_metrics):
    """Test handling JSON response with missing version key."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = '{"status":"UP"}'

    # Act
    handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('responses', 1),
    ])
    assert 'version' not in mock_metrics.attributes


def test_handle_json_response_none_text(endpoint_model, mock_metrics):
    """Test handling JSON response with None text."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = None

    # Act
    handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)

    # Assert
    mock_metrics.set_counter.assert_has_calls([
        call('errors', 1),
    ])


@patch('kuhl_haus.magpie.canary.tasks.http_health_check.json.loads')
def test_handle_json_response_invalid_json(mock_json_loads, endpoint_model, mock_metrics):
    """Test handling invalid JSON response."""
    # Arrange
    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON'
    mock_json_loads.side_effect = json.JSONDecodeError("Expecting value", "Invalid JSON", 0)

    # Act and Assert
    with pytest.raises(json.JSONDecodeError):
        handle_json_response(response=mock_response, ep=endpoint_model, metrics=mock_metrics)
