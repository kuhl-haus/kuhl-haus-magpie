import pytest
import json
from unittest.mock import patch, mock_open, MagicMock, call
from typing import List, Any

import kuhl_haus.magpie.canary.helpers.canary_configs as canary_configs
from kuhl_haus.magpie.canary.models.dns_resolver import DnsResolver, DnsResolverList
from kuhl_haus.magpie.canary.models.endpoint_model import EndpointModel


@pytest.fixture
def mock_model():
    class MockModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return MockModel


@pytest.fixture
def sample_json_data():
    return [{"name": "test1", "value": "value1"}, {"name": "test2", "value": "value2"}]


@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
def test_from_file_success(mock_json_load, mock_file_open, mock_model, sample_json_data):
    """Test from_file when file exists and contains valid JSON."""
    # Arrange
    mock_json_load.return_value = sample_json_data
    file_path = "test_path.json"

    # Act
    sut = canary_configs.from_file(file_path, mock_model)

    # Assert
    mock_file_open.assert_called_once_with(file_path, 'r')
    assert len(sut) == 2
    assert sut[0].name == "test1"
    assert sut[1].value == "value2"


@patch('builtins.open')
@patch('builtins.print')
def test_from_file_file_not_found(mock_print, mock_file_open, mock_model):
    """Test from_file when file is not found."""
    # Arrange
    mock_file_open.side_effect = FileNotFoundError()
    file_path = "nonexistent_file.json"

    # Act
    sut = canary_configs.from_file(file_path, mock_model)

    # Assert
    assert isinstance(sut, list)
    assert len(sut) == 0
    mock_print.assert_called_once_with(f"File {file_path} not found.")


@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
@patch('builtins.print')
def test_from_file_invalid_json(mock_print, mock_json_load, mock_file_open, mock_model):
    """Test from_file when file contains invalid JSON."""
    # Arrange
    mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    file_path = "invalid_json.json"

    # Act
    sut = canary_configs.from_file(file_path, mock_model)

    # Assert
    assert isinstance(sut, list)
    assert len(sut) == 0
    mock_print.assert_called_once_with(f"Error decoding JSON from file {file_path}")


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.CONFIG_API')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
def test_get_endpoints_api_success(mock_get, config_api):
    """Test get_endpoints when API returns valid data."""
    # Arrange
    config_api.return_value = "config-api"
    mock_response = MagicMock()
    mock_response.json.return_value = [
      {
        "mnemonic": "test1",
        "hostname": "test1.com",
        "scheme": "https",
        "port": 443,
        "path": "/health",
        "healthy_status_code": 200,
        "response_format": "json",
        "status_key": "status",
        "healthy_status": "ok",
        "version_key": "version",
        "connect_timeout": 7.0,
        "read_timeout": 7.0,
        "ignore": False
      }
    ]
    mock_get.return_value = mock_response

    # Act
    sut = canary_configs.get_endpoints()

    # Assert
    assert len(sut) == 1
    assert all(isinstance(item, EndpointModel) for item in sut)
    assert sut[0].mnemonic == "test1"
    assert sut[0].url == "https://test1.com:443/health"


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.from_file')
def test_get_endpoints_fallback_to_file(mock_from_file, mock_get):
    """Test get_endpoints falls back to file when API returns no data."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    expected_endpoints = [EndpointModel(mnemonic="test", hostname="example.com")]
    mock_from_file.return_value = expected_endpoints

    # Act
    sut = canary_configs.get_endpoints()

    # Assert
    assert sut == expected_endpoints
    mock_from_file.assert_called_once_with(
        canary_configs.CANARY_CONFIG_FILE_PATH, EndpointModel
    )


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.CONFIG_API')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
def test_get_resolvers_api_success(mock_get, config_api):
    """Test get_resolvers when API returns valid data."""
    # Arrange
    config_api.return_value = "config-api"
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"name": "resolver1", "ip_address": "8.8.8.8"},
        {"name": "resolver2", "ip_address": "1.1.1.1"}
    ]
    mock_get.return_value = mock_response

    # Act
    sut = canary_configs.get_resolvers()

    # Assert
    assert len(sut) == 2
    assert all(isinstance(item, DnsResolver) for item in sut)
    assert sut[0].name == "resolver1"
    assert sut[1].ip_address == "1.1.1.1"


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.get_resolver_lists')
def test_get_resolvers_fallback_to_resolver_lists(mock_get_resolver_lists, mock_get):
    """Test get_resolvers falls back to resolver lists when API returns no data."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    # Create mock resolver lists with some overlapping names
    resolver_list1 = DnsResolverList(
        name="default",
        resolvers=[
            DnsResolver(**{"name": "resolver1", "ip_address": "8.8.8.8"}),
            DnsResolver(**{"name": "resolver2", "ip_address": "1.1.1.1"}),
        ]
    )
    resolver_list2 = DnsResolverList(
        name="alternate",
        resolvers=[
            DnsResolver(**{"name": "resolver1", "ip_address": "8.8.8.8"}),  # Duplicate name
            DnsResolver(**{"name": "resolver3", "ip_address": "9.9.9.9"}),  # Unique name
        ]
    )

    mock_get_resolver_lists.return_value = [resolver_list1, resolver_list2]

    # Act
    sut = canary_configs.get_resolvers()

    # Assert
    assert all(isinstance(item, DnsResolver) for item in sut)

    # Only unique resolver names
    assert len(sut) == 3
    resolver_names = [r.name for r in sut]
    assert "resolver1" in resolver_names
    assert "resolver2" in resolver_names
    assert "resolver3" in resolver_names


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.get_resolver_lists')
def test_get_resolvers_empty_resolver_lists(mock_get_resolver_lists, mock_get):
    """Test get_resolvers when API returns no data and no resolvers found in lists."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    # Return empty resolver lists
    mock_get_resolver_lists.return_value = []

    # Act
    sut = canary_configs.get_resolvers()

    # Assert
    assert sut == []


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.CONFIG_API')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
def test_get_resolver_lists_api_success(mock_get, config_api):
    """Test get_resolver_lists when API returns valid data."""
    # Arrange
    config_api.return_value = "config-api"
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"name": "list1", "resolvers": [{"name": "resolver1", "ip": "8.8.8.8"}]},
        {"name": "list2", "resolvers": [{"name": "resolver2", "ip": "1.1.1.1"}]}
    ]
    mock_get.return_value = mock_response

    # Act
    sut = canary_configs.get_resolver_lists()

    # Assert
    assert len(sut) == 2
    assert all(isinstance(item, DnsResolverList) for item in sut)
    assert sut[0].name == "list1"
    assert sut[1].name == "list2"


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.from_file')
def test_get_resolver_lists_fallback_to_file(mock_from_file, mock_get):
    """Test get_resolver_lists falls back to file when API returns no data."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    expected_lists = [DnsResolverList(name="test", resolvers=[])]
    mock_from_file.return_value = expected_lists

    # Act
    sut = canary_configs.get_resolver_lists()

    # Assert
    assert sut == expected_lists
    mock_from_file.assert_called_once_with(
        canary_configs.RESOLVERS_CONFIG_FILE_PATH, DnsResolverList
    )


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.CONFIG_API')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
def test_get_default_resolver_list_api_success(mock_get, config_api):
    """Test get_default_resolver_list when API returns valid data."""
    # Arrange
    config_api.return_value = "config-api"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "name": "default",
        "resolvers": [
            {"name": "resolver1", "ip_address": "8.8.8.8"},
            {"name": "resolver2", "ip_address": "1.1.1.1"}
        ]
    }
    mock_get.return_value = mock_response

    # Act
    sut = canary_configs.get_default_resolver_list()

    # Assert
    assert len(sut) == 2
    assert all(isinstance(item, DnsResolver) for item in sut)
    assert sut[0].name == "resolver1"
    assert sut[1].ip_address == "1.1.1.1"


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.from_file')
def test_get_default_resolver_list_fallback_to_file(mock_from_file, mock_get):
    """Test get_default_resolver_list falls back to file when API returns no data."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    resolver_list = MagicMock()
    resolver_list.resolvers = [
        {"name": "resolver1", "ip_address": "8.8.8.8"},
        {"name": "resolver2", "ip_address": "1.1.1.1"}
    ]
    mock_from_file.return_value = resolver_list

    # Act
    sut = canary_configs.get_default_resolver_list()

    # Assert
    assert len(sut) == 2
    assert all(isinstance(item, DnsResolver) for item in sut)
    mock_from_file.assert_called_once_with(
        canary_configs.RESOLVERS_CONFIG_FILE_PATH, DnsResolverList
    )


@patch('kuhl_haus.magpie.canary.helpers.canary_configs.requests.get')
@patch('kuhl_haus.magpie.canary.helpers.canary_configs.from_file')
def test_get_default_resolver_list_empty_result(mock_from_file, mock_get):
    """Test get_default_resolver_list when no resolver list is found."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_get.return_value = mock_response

    # Return None as if no resolver list was found
    mock_from_file.return_value = None

    # Act
    sut = canary_configs.get_default_resolver_list()

    # Assert
    assert sut == []
