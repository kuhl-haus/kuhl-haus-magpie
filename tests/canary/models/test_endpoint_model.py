from urllib.parse import urlparse

import pytest

from kuhl_haus.magpie.canary.models.endpoint_model import EndpointModel


@pytest.fixture
def basic_endpoint_model():
    return EndpointModel(mnemonic="test", hostname="example.com")


@pytest.fixture
def complete_endpoint_model():
    return EndpointModel(
        mnemonic="complete",
        hostname="example.org",
        scheme="http",
        port=8080,
        path="/api/v1",
        query=[("key1", "value1"), ("key2", "value2")],
        fragment="section1",
        healthy_status_code=201,
        response_format="json",  # Changed from json_response=True
        status_key="state",
        healthy_status="OPERATIONAL",
        version_key="version_info",
        connect_timeout=10.0,
        read_timeout=15.0,
        ignore=True
    )


def test_endpoint_model_initialization_with_required_fields():
    """Test that EndpointModel can be initialized with only required fields."""
    # Arrange & Act
    sut = EndpointModel(mnemonic="test", hostname="example.com")

    # Assert
    assert sut.mnemonic == "test"
    assert sut.hostname == "example.com"
    assert sut.scheme == "https"  # Default value
    assert sut.port == 443  # Default value
    assert sut.path == "/"  # Default value


def test_endpoint_model_initialization_with_all_fields(complete_endpoint_model):
    """Test that EndpointModel can be initialized with all fields."""
    # Assert
    sut = complete_endpoint_model
    assert sut.mnemonic == "complete"
    assert sut.hostname == "example.org"
    assert sut.scheme == "http"
    assert sut.port == 8080
    assert sut.path == "/api/v1"
    assert sut.query == [("key1", "value1"), ("key2", "value2")]
    assert sut.fragment == "section1"
    assert sut.healthy_status_code == 201
    assert sut.response_format == "json"
    assert sut.status_key == "state"
    assert sut.healthy_status == "OPERATIONAL"
    assert sut.version_key == "version_info"
    assert sut.connect_timeout == 10.0
    assert sut.read_timeout == 15.0
    assert sut.ignore is True


def test_endpoint_model_url_property_basic(basic_endpoint_model):
    """Test the url property with basic settings."""
    # Arrange
    sut = basic_endpoint_model

    # Act
    result = sut.url

    # Assert
    parsed_url = urlparse(result)
    assert parsed_url.hostname == "example.com"
    assert parsed_url.scheme == "https"
    assert parsed_url.port == 443


def test_endpoint_model_url_property_with_path_and_port(basic_endpoint_model):
    """Test the url property with custom path and port."""
    # Arrange
    sut = basic_endpoint_model
    sut.path = "/api/health"
    sut.port = 8443

    # Act
    result = sut.url

    # Assert
    parsed_url = urlparse(result)
    assert parsed_url.hostname == "example.com"
    assert parsed_url.scheme == "https"
    assert parsed_url.port == 8443
    assert parsed_url.path == "/api/health"


def test_endpoint_model_url_property_with_query_params():
    """Test the url property with query parameters."""
    # Arrange
    sut = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        query=[("param1", "value1"), ("param2", "value2")]
    )

    # Act
    result = sut.url

    # Assert
    parsed_url = urlparse(result)
    assert parsed_url.hostname == "example.com"
    assert parsed_url.query == 'param1=value1&param2=value2'


def test_endpoint_model_url_property_with_fragment():
    """Test the url property with a fragment."""
    # Arrange
    sut = EndpointModel(
        mnemonic="test",
        hostname="example.com",
        fragment="section"
    )

    # Act
    result = sut.url

    # Assert
    parsed_url = urlparse(result)
    assert parsed_url.hostname == "example.com"
    assert parsed_url.fragment == "section"


def test_endpoint_model_url_property_with_all_components(complete_endpoint_model):
    """Test the url property with all components (scheme, hostname, port, path, query, fragment)."""
    # Arrange
    sut = complete_endpoint_model

    # Act
    result = sut.url

    # Assert
    parsed_url = urlparse(result)
    assert parsed_url.hostname == "example.org"
    assert parsed_url.fragment == "section1"
    assert parsed_url.query == 'key1=value1&key2=value2'


def test_endpoint_model_normalize_path_empty():
    """Test __normalize_path with empty path."""
    # Arrange
    sut = EndpointModel

    # Act
    result = sut(mnemonic="test", hostname="example.com", path="")

    # Assert
    assert result.path == "/"


def test_endpoint_model_normalize_path_missing_leading_slash():
    """Test __normalize_path with path missing leading slash."""
    # Arrange
    sut = EndpointModel

    # Act
    result = sut(mnemonic="test", hostname="example.com", path="api/v1")

    # Assert
    assert result.path == "/api/v1"


def test_endpoint_model_normalize_path_duplicate_slashes():
    """Test __normalize_path with duplicate slashes."""
    # Arrange
    sut = EndpointModel

    # Act
    result = sut(mnemonic="test", hostname="example.com", path="//api//v1///endpoint//")

    # Assert
    assert result.path == "/api/v1/endpoint/"
