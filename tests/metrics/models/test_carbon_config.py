import json
import os
import pytest
from unittest.mock import mock_open, patch
from typing import Dict, Any

from kuhl_haus.magpie.metrics.models.carbon_config import CarbonConfig


@pytest.fixture
def valid_config_data() -> Dict[str, Any]:
    return {
        "server_ip": "127.0.0.1",
        "pickle_port": 2004
    }


@pytest.fixture
def valid_config_file_content(valid_config_data) -> str:
    return json.dumps(valid_config_data)


def test_carbon_config_initialization():
    """Test that CarbonConfig can be initialized with valid parameters."""
    # Arrange
    server_ip = "192.168.1.100"
    pickle_port = 2004

    # Act
    sut = CarbonConfig(server_ip=server_ip, pickle_port=pickle_port)

    # Assert
    assert sut.server_ip == server_ip
    assert sut.pickle_port == pickle_port


def test_carbon_config_equality():
    """Test that CarbonConfig instances with the same values are considered equal."""
    # Arrange
    config1 = CarbonConfig(server_ip="127.0.0.1", pickle_port=2004)
    config2 = CarbonConfig(server_ip="127.0.0.1", pickle_port=2004)

    # Act & Assert
    assert config1 == config2


def test_carbon_config_inequality():
    """Test that CarbonConfig instances with different values are not equal."""
    # Arrange
    config1 = CarbonConfig(server_ip="127.0.0.1", pickle_port=2004)
    config2 = CarbonConfig(server_ip="192.168.1.1", pickle_port=2004)
    config3 = CarbonConfig(server_ip="127.0.0.1", pickle_port=2005)

    # Act & Assert
    assert config1 != config2
    assert config1 != config3
    assert config2 != config3


@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
def test_from_file_creates_config_with_valid_data(mock_json_load, mock_file_open, valid_config_data):
    """Test that from_file creates a CarbonConfig instance from valid file data."""
    # Arrange
    file_path = "config.json"
    mock_json_load.return_value = valid_config_data

    # Act
    sut = CarbonConfig.from_file(file_path)

    # Assert
    mock_file_open.assert_called_once_with(file_path)
    assert isinstance(sut, CarbonConfig)
    assert sut.server_ip == valid_config_data["server_ip"]
    assert sut.pickle_port == valid_config_data["pickle_port"]


@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
def test_from_file_handles_missing_required_fields(mock_json_load, mock_file_open):
    """Test that from_file raises an appropriate error when required fields are missing."""
    # Arrange
    file_path = "config.json"
    incomplete_data = {"server_ip": "127.0.0.1"}  # Missing pickle_port
    mock_json_load.return_value = incomplete_data

    # Act & Assert
    with pytest.raises(TypeError) as excinfo:
        CarbonConfig.from_file(file_path)

    # Verify the error mentions the missing field
    assert "pickle_port" in str(excinfo.value)


@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
def test_from_file_with_unexpected_fields_expect_throw_type_error(mock_json_load, mock_file_open):
    """Test that from_file throws an exception when unexpected fields are in the config file."""
    # Arrange
    file_path = "config.json"
    extra_data = {
        "server_ip": "127.0.0.1",
        "pickle_port": 2004,
        "extra_field": "should result in an error"
    }
    mock_json_load.return_value = extra_data

    # Act & Assert
    with pytest.raises(TypeError):
        CarbonConfig.from_file(file_path)


@patch("builtins.open")
def test_from_file_handles_file_not_found(mock_file_open):
    """Test that from_file raises an appropriate error when the file doesn't exist."""
    # Arrange
    file_path = "nonexistent_config.json"
    mock_file_open.side_effect = FileNotFoundError(f"No such file: {file_path}")

    # Act & Assert
    with pytest.raises(FileNotFoundError) as excinfo:
        CarbonConfig.from_file(file_path)

    # Verify the error contains the file path
    assert file_path in str(excinfo.value)


@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
def test_from_file_handles_invalid_json(mock_json_load, mock_file_open):
    """Test that from_file raises an appropriate error when the file contains invalid JSON."""
    # Arrange
    file_path = "invalid_config.json"
    mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

    # Act & Assert
    with pytest.raises(json.JSONDecodeError):
        CarbonConfig.from_file(file_path)


@patch("builtins.open")
def test_from_file_handles_permission_error(mock_file_open):
    """Test that from_file raises an appropriate error when there are permission issues."""
    # Arrange
    file_path = "protected_config.json"
    mock_file_open.side_effect = PermissionError(f"Permission denied: {file_path}")

    # Act & Assert
    with pytest.raises(PermissionError) as excinfo:
        CarbonConfig.from_file(file_path)

    # Verify the error contains the file path
    assert file_path in str(excinfo.value)


def test_from_file_integration(tmp_path):
    """Integration test using an actual file."""
    # Arrange
    config_data = {
        "server_ip": "127.0.0.1",
        "pickle_port": 2004
    }

    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Act
    sut = CarbonConfig.from_file(config_file)

    # Assert
    assert sut.server_ip == config_data["server_ip"]
    assert sut.pickle_port == config_data["pickle_port"]
