import pytest
from unittest.mock import Mock, patch, call, create_autospec, MagicMock
import dns.message
import dns.name
import dns.rdatatype
import dns.rcode
import dns.flags
import dns.exception
import dns.query

from kuhl_haus.magpie.endpoints.models import DnsResolver, EndpointModel, DnsResolverList
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.canary.tasks.dns_check import query_dns, dns_query


# Using IP addresses from the 192.0.2.0/24 range (TEST-NET-1) which is reserved for
# documentation and examples as per RFC 5737. These addresses are guaranteed to not be
# routable on the public internet, making them ideal for unit testing.


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
    endpoint = MagicMock(spec=EndpointModel)
    endpoint.hostname = "example.com"
    return endpoint


@pytest.fixture
def mock_resolver_list_1():
    resolver = MagicMock(spec=DnsResolver)
    resolver.ip_address = "192.0.2.1"
    return resolver


@pytest.fixture
def mock_resolver_list_2():
    resolver = MagicMock(spec=DnsResolver)
    resolver.ip_address = "192.0.2.2"
    return resolver


@pytest.fixture
def mock_resolvers(mock_resolver_list_1, mock_resolver_list_2):
    resolver_list = MagicMock(spec=DnsResolverList)
    resolver_list.resolvers = MagicMock()
    resolver_list.resolvers.get = MagicMock()
    resolver_list.resolvers.get.return_value = [mock_resolver_list_1, mock_resolver_list_2]
    resolver_list.count = MagicMock()
    resolver_list.count.return_value = 2
    return resolver_list


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_successful_first_resolver(mock_dns_query, mock_resolvers, mock_resolver_list_1, mock_endpoint, mock_metrics, mock_logger):
    """Test successful DNS query with the first resolver."""
    # Arrange
    mock_response = MagicMock(spec=dns.message.Message)
    mock_response.flags = 0  # Not truncated
    mock_response.rcode.return_value = dns.rcode.NOERROR
    mock_response.to_text.return_value = "DNS Response Text"
    mock_dns_query.return_value = mock_response

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    mock_dns_query.assert_called_once_with(
        mock_resolver_list_1.ip_address, mock_endpoint.hostname, "A", use_tcp=False
    )
    mock_metrics.set_counter.assert_has_calls([
        call('requests', 1),
        call('responses', 1)
    ])
    assert mock_metrics.attributes['truncated'] == 0
    assert mock_metrics.attributes['rcode'] == 'NOERROR'
    assert mock_metrics.attributes['result'] == "DNS Response Text"
    mock_logger.exception.assert_not_called()


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_truncated_response(mock_dns_query, mock_resolvers, mock_endpoint, mock_metrics, mock_logger):
    """Test DNS query with truncated response."""
    # Arrange
    mock_response = MagicMock(spec=dns.message.Message)
    mock_response.flags = dns.flags.TC  # Truncated
    mock_response.rcode.return_value = dns.rcode.NOERROR
    mock_response.to_text.return_value = "Truncated DNS Response"
    mock_dns_query.return_value = mock_response

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_metrics.attributes['truncated'] == 1
    assert mock_metrics.attributes['rcode'] == 'NOERROR'
    assert mock_metrics.attributes['result'] == "Truncated DNS Response"


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_first_resolver_bad_response_second_ok(mock_dns_query, mock_resolvers, mock_endpoint, mock_metrics,
                                                         mock_logger):
    """Test when first resolver fails with BadResponse but second succeeds."""
    # Arrange
    mock_response = MagicMock(spec=dns.message.Message)
    mock_response.flags = 0
    mock_response.rcode.return_value = dns.rcode.NOERROR
    mock_response.to_text.return_value = "DNS Response Text"

    mock_dns_query.side_effect = [
        dns.query.BadResponse("Bad DNS response"),
        mock_response
    ]

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_dns_query.call_count == 2
    # assert mock_metrics.set_counter.call_count == 3  # requests, errors, responses
    assert mock_metrics.attributes['rcode'] == 'NOERROR'
    assert mock_metrics.attributes['result'] == "DNS Response Text"
    assert mock_logger.exception.call_count == 1


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_timeout_for_all_resolvers(mock_dns_query, mock_resolvers, mock_endpoint, mock_metrics, mock_logger):
    """Test when all resolvers fail with timeout."""
    # Arrange
    mock_dns_query.side_effect = dns.exception.Timeout("DNS timeout")

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_dns_query.call_count == mock_resolvers.count()
    assert mock_metrics.set_counter.call_args_list == [
        call('requests', 1),
        call('errors', 1),
        call('requests', 1),
        call('errors', 1)
    ]
    assert mock_metrics.attributes['rcode'] == 'TIMEOUT'
    assert 'exception' in mock_metrics.attributes
    assert mock_logger.exception.call_count == 2


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_unexpected_source_exception(mock_dns_query, mock_resolvers, mock_endpoint, mock_metrics,
                                               mock_logger):
    """Test handling of UnexpectedSource exception."""
    # Arrange
    mock_dns_query.side_effect = dns.query.UnexpectedSource("Unexpected source")

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_metrics.set_counter.call_args_list == [
        call('requests', 1),
        call('errors', 1),
        call('requests', 1),
        call('errors', 1)
    ]
    assert mock_metrics.attributes['rcode'] == 'ERROR'
    assert 'Unexpected source' in mock_metrics.attributes['exception']


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns_query')
def test_query_dns_unhandled_exception(mock_dns_query, mock_resolvers, mock_endpoint, mock_metrics, mock_logger):
    """Test handling of unhandled exceptions."""
    # Arrange
    mock_dns_query.side_effect = ValueError("Unexpected error")

    # Act
    query_dns(mock_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    assert mock_metrics.set_counter.call_args_list == [
        call('requests', 1),
        call('exceptions', 1),
        call('requests', 1),
        call('exceptions', 1)
    ]
    assert mock_metrics.attributes['rcode'] == 'FATAL'
    assert 'ValueError' in mock_metrics.attributes['exception']


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.tcp')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.udp')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.make_query')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.name.from_text')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.rdatatype.from_text')
def test_dns_query_tcp(mock_rdatatype, mock_name_from_text, mock_make_query,
                       mock_udp, mock_tcp):
    """Test DNS query over TCP."""
    # Arrange
    ip_address = "192.0.2.1"
    query_name = "example.com"
    rr_type = "A"

    mock_qname = MagicMock()
    mock_name_from_text.return_value = mock_qname

    mock_rdtype = MagicMock()
    mock_rdatatype.return_value = mock_rdtype

    mock_dns_message = MagicMock()
    mock_make_query.return_value = mock_dns_message

    mock_response = MagicMock(spec=dns.message.Message)
    mock_tcp.return_value = mock_response

    # Act
    result = dns_query(ip_address, query_name, rr_type, use_tcp=True)

    # Assert
    mock_name_from_text.assert_called_once_with(query_name)
    mock_rdatatype.assert_called_once_with(rr_type)
    mock_make_query.assert_called_once_with(qname=mock_qname, rdtype=mock_rdtype)
    mock_tcp.assert_called_once_with(mock_dns_message, ip_address, timeout=1)
    mock_udp.assert_not_called()
    assert result == mock_response


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.tcp')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.udp')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.make_query')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.name.from_text')
@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.rdatatype.from_text')
def test_dns_query_udp(mock_rdatatype, mock_name_from_text, mock_make_query,
                       mock_udp, mock_tcp):
    """Test DNS query over UDP."""
    # Arrange
    ip_address = "192.0.2.1"
    query_name = "example.com"
    rr_type = "A"

    mock_qname = MagicMock()
    mock_name_from_text.return_value = mock_qname

    mock_rdtype = MagicMock()
    mock_rdatatype.return_value = mock_rdtype

    mock_dns_message = MagicMock()
    mock_make_query.return_value = mock_dns_message

    mock_response = MagicMock(spec=dns.message.Message)
    mock_udp.return_value = mock_response

    # Act
    result = dns_query(ip_address, query_name, rr_type, use_tcp=False)

    # Assert
    mock_name_from_text.assert_called_once_with(query_name)
    mock_rdatatype.assert_called_once_with(rr_type)
    mock_make_query.assert_called_once_with(
        qname=mock_qname, rdtype=mock_rdtype, use_edns=True, ednsflags=0, payload=4096
    )
    mock_udp.assert_called_once_with(mock_dns_message, ip_address, timeout=1)
    mock_tcp.assert_not_called()
    assert result == mock_response


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.tcp')
def test_dns_query_tcp_exception(mock_tcp):
    """Test DNS query over TCP with exception."""
    # Arrange
    mock_tcp.side_effect = dns.exception.Timeout("TCP timeout")

    # Act & Assert
    with pytest.raises(dns.exception.Timeout) as exc_info:
        dns_query("192.0.2.1", "example.com", "A", use_tcp=True)

    assert "TCP timeout" in str(exc_info.value)


@patch('kuhl_haus.magpie.canary.tasks.dns_check.dns.query.udp')
def test_dns_query_udp_exception(mock_udp):
    """Test DNS query over UDP with exception."""
    # Arrange
    mock_udp.side_effect = dns.query.BadResponse("Bad response")

    # Act & Assert
    with pytest.raises(dns.query.BadResponse) as exc_info:
        dns_query("192.0.2.1", "example.com", "A", use_tcp=False)

    assert "Bad response" in str(exc_info.value)


def test_query_dns_empty_resolvers(mock_endpoint, mock_metrics, mock_logger):
    """Test query_dns with empty resolvers list."""
    # Arrange
    empty_resolvers = []

    # Act
    query_dns(empty_resolvers, mock_endpoint, mock_metrics, mock_logger)

    # Assert
    mock_metrics.set_counter.assert_not_called()
    mock_logger.exception.assert_not_called()
