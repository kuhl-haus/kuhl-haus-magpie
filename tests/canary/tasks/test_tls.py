import pytest
from unittest.mock import Mock, patch, MagicMock
import ssl
import time
from datetime import datetime, timedelta
import OpenSSL

from kuhl_haus.magpie.endpoints.models import EndpointModel
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.canary.tasks.tls import invoke_tls_check, get_tls_cert_expiration_days

from datetime import datetime, timedelta


def create_timestamp_from_now(days=0, hour=23, minute=59, second=59):
    """
    Creates a byte encoded timestamp in the format b"YYYYMMDDHHMMSSZ"
    based on current date plus/minus specified number of days.

    Args:
        days (int, optional): Number of days to add (positive) or subtract (negative)
                             from current date. Defaults to 0.
        hour (int, optional): Hour (0-23) to use in result. Defaults to 23.
        minute (int, optional): Minute (0-59) to use in result. Defaults to 59.
        second (int, optional): Second (0-59) to use in result. Defaults to 59.

    Returns:
        bytes: Timestamp in ASN.1 GeneralizedTime format as bytes
    """
    # Get the current date and add/subtract days
    target_date = datetime.now().date() + timedelta(days=days)

    # Create a new datetime with the target date and specified time
    target_datetime = datetime.combine(
        target_date,
        datetime.min.time().replace(hour=hour, minute=minute, second=second)
    )

    # Format to the required string format and encode as bytes
    timestamp = target_datetime.strftime("%Y%m%d%H%M%S") + "Z"
    return timestamp.encode('ascii')


def create_timestamp_bytes(year, month, day, hour=23, minute=59, second=59):
    """
    Creates a byte encoded timestamp in the format b"YYYYMMDDHHMMSSZ"

    Args:
        year (int): Year (4 digits)
        month (int): Month (1-12)
        day (int): Day (1-31)
        hour (int, optional): Hour (0-23). Defaults to 23.
        minute (int, optional): Minute (0-59). Defaults to 59.
        second (int, optional): Second (0-59). Defaults to 59.

    Returns:
        bytes: Timestamp in ASN.1 GeneralizedTime format as bytes
    """
    timestamp = f"{year:04d}{month:02d}{day:02d}{hour:02d}{minute:02d}{second:02d}Z"
    return timestamp.encode('ascii')


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_metrics():
    metrics = MagicMock(spec=Metrics)
    metrics.attributes = {}
    return metrics


@pytest.fixture
def mock_endpoint():
    return EndpointModel(hostname="example.com", port=443, mnemonic="test-endpoint")


@patch("kuhl_haus.magpie.canary.tasks.tls.get_tls_cert_expiration_days")
def test_invoke_tls_check_successful_case(mock_get_days, mock_endpoint, mock_metrics, mock_logger):
    """Test successful TLS check with expected metrics updates."""
    # Arrange
    mock_get_days.return_value = 30

    # Act
    invoke_tls_check(mock_endpoint, mock_metrics, mock_logger)

    # Assert
    mock_metrics.set_counter.assert_any_call('requests', 1)
    mock_metrics.set_counter.assert_any_call('responses', 1)
    assert mock_metrics.attributes["days_until_expiration"] == 30
    assert mock_metrics.attributes["expires_today"] is False
    assert mock_metrics.attributes["is_valid"] is True
    mock_logger.exception.assert_not_called()


@patch("kuhl_haus.magpie.canary.tasks.tls.get_tls_cert_expiration_days")
def test_invoke_tls_check_expiring_today(mock_get_days, mock_endpoint, mock_metrics, mock_logger):
    """Test when certificate expires today."""
    # Arrange
    mock_get_days.return_value = 1

    # Act
    invoke_tls_check(mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_metrics.attributes["days_until_expiration"] == 1
    assert mock_metrics.attributes["expires_today"] is True
    assert mock_metrics.attributes["is_valid"] is True


@patch("kuhl_haus.magpie.canary.tasks.tls.get_tls_cert_expiration_days")
def test_invoke_tls_check_expired_cert(mock_get_days, mock_endpoint, mock_metrics, mock_logger):
    """Test when certificate has already expired."""
    # Arrange
    mock_get_days.return_value = 0

    # Act
    invoke_tls_check(mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_metrics.attributes["days_until_expiration"] == 0
    assert mock_metrics.attributes["expires_today"] is True
    assert mock_metrics.attributes["is_valid"] is False


@patch("kuhl_haus.magpie.canary.tasks.tls.get_tls_cert_expiration_days")
def test_invoke_tls_check_exception_handling(mock_get_days, mock_endpoint, mock_metrics, mock_logger):
    """Test exception handling during TLS check."""
    # Arrange
    test_exception = ssl.SSLError("Test SSL error")
    mock_get_days.side_effect = test_exception

    # Act
    invoke_tls_check(mock_endpoint, mock_metrics, mock_logger)

    # Assert
    mock_metrics.set_counter.assert_any_call('requests', 1)
    mock_metrics.set_counter.assert_any_call('exceptions', 1)
    assert mock_metrics.attributes['exception'] == repr(test_exception)
    mock_logger.exception.assert_called_once()
    assert f"unhandled exception processing {mock_endpoint.hostname}:{mock_endpoint.port}" in \
           mock_logger.exception.call_args[1]["msg"]


@patch("kuhl_haus.magpie.canary.tasks.tls.ssl.get_server_certificate")
@patch("kuhl_haus.magpie.canary.tasks.tls.OpenSSL.crypto.load_certificate")
def test_get_tls_cert_expiration_days_normal_case(mock_load_cert, mock_get_cert):
    """Test normal calculation of days until expiration."""
    # Arrange
    mock_get_cert.return_value = "MOCK_CERTIFICATE"

    mock_cert = MagicMock()
    expiration_days = 30
    mock_cert.get_notAfter.return_value = create_timestamp_from_now(days=expiration_days)
    mock_load_cert.return_value = mock_cert

    # Act
    result = get_tls_cert_expiration_days("example.com", 443)

    # Assert
    assert (result == expiration_days or result == expiration_days - 1)  # edge-case where this test fails around midnight.
    mock_get_cert.assert_called_once_with(("example.com", 443))
    mock_load_cert.assert_called_once()


@patch("kuhl_haus.magpie.canary.tasks.tls.ssl.get_server_certificate")
@patch("kuhl_haus.magpie.canary.tasks.tls.OpenSSL.crypto.load_certificate")
@patch("kuhl_haus.magpie.canary.tasks.tls.time.mktime")
def test_get_tls_cert_expiration_days_expired(mock_mktime, mock_load_cert, mock_get_cert):
    """Test when certificate has already expired."""
    # Arrange
    mock_get_cert.return_value = "MOCK_CERTIFICATE"

    mock_cert = MagicMock()
    expiration_days = -5
    mock_cert.get_notAfter.return_value = create_timestamp_from_now(days=expiration_days)
    mock_load_cert.return_value = mock_cert

    # Mock time values (certificate expired 5 days ago)
    # NOTE: Reversing the order of side_effect values
    current_time = time.mktime(datetime(2020, 1, 6).timetuple())
    expiration_time = time.mktime(datetime(2020, 1, 1).timetuple())
    mock_mktime.side_effect = [current_time, expiration_time]  # Changed order here

    # Act
    result = get_tls_cert_expiration_days("example.com", 443)

    # Assert
    assert result == 0  # does not return negative values for certificates past their expiration date.


@patch("kuhl_haus.magpie.canary.tasks.tls.ssl.get_server_certificate")
def test_get_tls_cert_expiration_days_connection_error(mock_get_cert):
    """Test error when connecting to server."""
    # Arrange
    mock_get_cert.side_effect = ssl.SSLError("Connection refused")

    # Act & Assert
    with pytest.raises(ssl.SSLError):
        get_tls_cert_expiration_days("example.com", 443)


@patch("kuhl_haus.magpie.canary.tasks.tls.ssl.get_server_certificate")
@patch("kuhl_haus.magpie.canary.tasks.tls.OpenSSL.crypto.load_certificate")
def test_get_tls_cert_expiration_days_invalid_cert_format(mock_load_cert, mock_get_cert):
    """Test invalid certificate format handling."""
    # Arrange
    mock_get_cert.return_value = "INVALID_CERTIFICATE"
    mock_load_cert.side_effect = OpenSSL.crypto.Error("Invalid certificate format")

    # Act & Assert
    with pytest.raises(OpenSSL.crypto.Error):
        get_tls_cert_expiration_days("example.com", 443)


@patch("kuhl_haus.magpie.canary.tasks.tls.ssl.get_server_certificate")
@patch("kuhl_haus.magpie.canary.tasks.tls.OpenSSL.crypto.load_certificate")
def test_get_tls_cert_expiration_days_invalid_date_format(mock_load_cert, mock_get_cert):
    """Test invalid date format in certificate."""
    # Arrange
    mock_get_cert.return_value = "MOCK_CERTIFICATE"

    mock_cert = MagicMock()
    mock_cert.get_notAfter.return_value = b"INVALID_DATE_FORMAT"
    mock_load_cert.return_value = mock_cert

    # Act & Assert
    with pytest.raises(ValueError):
        get_tls_cert_expiration_days("example.com", 443)


# Fix for test_invoke_tls_check_input_validation
def test_invoke_tls_check_input_validation():
    """Test input validation with None values."""
    # Arrange
    mock_logger = MagicMock()
    mock_metrics = MagicMock(spec=Metrics)
    mock_metrics.attributes = {}

    # Act & Assert
    with pytest.raises(AttributeError):
        invoke_tls_check(None, mock_metrics, mock_logger)

    # Act (with valid endpoint but None metrics)
    endpoint = EndpointModel(hostname="example.com", port=443, mnemonic="test-endpoint")
    with pytest.raises(AttributeError):
        invoke_tls_check(endpoint, None, mock_logger)
