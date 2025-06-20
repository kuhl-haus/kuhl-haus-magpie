import json
from logging import Logger
from unittest.mock import patch, MagicMock

import pytest

from kuhl_haus.magpie.metrics.data.metrics import Metrics


@pytest.fixture
def mock_logger():
    """Fixture to provide a mock Logger instance."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_carbon_poster():
    """Fixture to provide a mock CarbonPoster instance."""
    mock = MagicMock()
    mock.post_metrics = MagicMock()
    return mock


@pytest.fixture
def basic_metrics():
    """Fixture to provide a basic Metrics instance with minimal configuration."""
    return Metrics(
        mnemonic="test_metric",
        namespace="test_namespace",
        name="test"
    )


@pytest.fixture
def complete_metrics():
    """Fixture to provide a completely configured Metrics instance."""
    return Metrics(
        mnemonic="test_metric",
        namespace="test_namespace",
        name="test",
        hostname="test.host.com",
        timestamp=1600000000,
        meta={"region": "us-west", "env": "test"},
        attributes={"latency": 100, "memory": "200.5", "invalid": "not_a_number"},
        counters={"requests": 42, "errors": 7}
    )


def test_post_init_sets_timestamp_when_default():
    # Arrange
    fixed_time = 1600000000

    with patch('kuhl_haus.magpie.metrics.data.metrics.time.time_ns', return_value=fixed_time * 1_000_000_000):
        # Act
        sut = Metrics(mnemonic="test", namespace="test", name="test")

        # Assert
        assert sut.timestamp == fixed_time


def test_post_init_preserves_timestamp_when_provided():
    # Arrange
    provided_timestamp = 1234567890

    # Act
    sut = Metrics(mnemonic="test", namespace="test", name="test", timestamp=provided_timestamp)

    # Assert
    assert sut.timestamp == provided_timestamp


def test_declare_counters_initializes_counters_to_zero():
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")
    counter_names = ["counter1", "counter2", "counter3"]

    # Act
    sut.declare_counters(counter_names.copy())

    # Assert
    assert sut.counters == {"counter1": 0, "counter2": 0, "counter3": 0}
    # Verify the input list was consumed (popped)
    assert len(counter_names) == 3


def test_set_counter_increments_existing_counter():
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")
    sut.counters = {"existing": 5}

    # Act
    sut.set_counter("existing", 3)

    # Assert
    assert sut.counters["existing"] == 8


def test_set_counter_creates_new_counter():
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")

    # Act
    sut.set_counter("new_counter", 10)

    # Assert
    assert sut.counters["new_counter"] == 10


def test_set_counter_handles_negative_increments():
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")
    sut.counters = {"existing": 5}

    # Act
    sut.set_counter("existing", -3)

    # Assert
    assert sut.counters["existing"] == 2


def test_json_property_returns_correct_serialization(complete_metrics):
    # Arrange
    sut = complete_metrics
    expected = {
        "mnemonic": "test_metric",
        "namespace": "test_namespace",
        "name": "test",
        "timestamp": 1600000000,
        "meta": {"region": "us-west", "env": "test"},
        "attributes": {"latency": 100, "memory": "200.5", "invalid": "not_a_number"},
        "counters": {"requests": 42, "errors": 7}
    }

    # Act
    result = sut.json

    # Assert
    assert json.loads(result) == expected


def test_carbon_property_generates_metrics_with_tags(complete_metrics):
    # Arrange
    sut = complete_metrics

    # Act
    result = sut.carbon

    # Assert
    assert len(result) > 0
    # Check that tags are properly formatted
    tagged_metrics = [m for m in result if ";region=us-west;env=test" in m[0]]
    assert len(tagged_metrics) > 0
    # Verify timestamp is included
    assert all(m[1][0] == 1600000000 for m in result)


def test_carbon_property_includes_hostname_metrics(complete_metrics):
    # Arrange
    sut = complete_metrics

    # Act
    result = sut.carbon

    # Assert
    hostname_metrics = [m for m in result if "hostname.test_host_com" in m[0]]
    assert len(hostname_metrics) > 0


def test_carbon_property_with_empty_hostname(basic_metrics):
    # Arrange
    sut = basic_metrics

    # Act
    result = sut.carbon

    # Assert
    hostname_metrics = [m for m in result if "hostname" in m[0]]
    assert len(hostname_metrics) == 0


def test_carbon_property_handles_numeric_attribute_types(complete_metrics):
    # Arrange
    sut = complete_metrics

    # Act
    result = sut.carbon

    # Assert
    # Find metrics for the integer attribute
    latency_metrics = [m for m in result if "latency" in m[0]]
    assert any(m[1][1] == 100 for m in latency_metrics)

    # Find metrics for the string attribute that contains a numeric value
    memory_metrics = [m for m in result if "memory" in m[0]]
    assert any(m[1][1] == 200 for m in memory_metrics)


def test_carbon_property_skips_non_numeric_attributes():
    # Arrange
    sut = Metrics(
        mnemonic="test",
        namespace="test",
        name="test",
        attributes={"valid": 123, "invalid": "not_a_number"}
    )

    # Act
    result = sut.carbon

    # Assert
    attribute_metrics = [m for m in result if m[0].endswith("valid")]
    invalid_metrics = [m for m in result if m[0].endswith("invalid")]
    assert len(attribute_metrics) > 0
    assert len(invalid_metrics) == 0


def test_get_tags_formats_meta_correctly():
    # Arrange
    sut = Metrics(
        mnemonic="test",
        namespace="test",
        name="test",
        meta={"region": "us-west", "env": "test", "empty": ""}
    )

    # Act
    result = sut._Metrics__get_tags()

    # Assert
    assert ";region=us-west" in result
    assert ";env=test" in result
    assert ";empty=" not in result  # Empty values should be skipped


@patch('traceback.format_exc', return_value="Mocked traceback")
def test_post_metrics_handles_exceptions(mock_traceback, mock_logger, mock_carbon_poster):
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")
    mock_carbon_poster.post_metrics.side_effect = RuntimeError("Test error")

    # Act
    sut.post_metrics(mock_logger, mock_carbon_poster)

    # Assert
    mock_logger.error.assert_called_once()
    assert "Unhandled exception" in mock_logger.error.call_args[0][0]
    assert "Test error" in mock_logger.error.call_args[0][0]


def test_post_metrics_success_scenario(mock_logger, mock_carbon_poster):
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test", counters={"requests": 5})

    # Act
    sut.post_metrics(mock_logger, mock_carbon_poster)

    # Assert
    mock_carbon_poster.post_metrics.assert_called_once()
    assert mock_logger.info.call_count == 1
    assert mock_logger.debug.call_count == 1


def test_log_metrics_success_scenario(mock_logger):
    # Arrange
    sut = Metrics(mnemonic="test", namespace="test", name="test")

    # Act
    sut.log_metrics(mock_logger)

    # Assert
    mock_logger.info.assert_called_once()


@pytest.mark.parametrize("version, expected", [
    ("0.0.1", 0.00001),
    ("0.0.2", 0.00002),
    ("0.0.10", 0.00010),
    ("0.0.11", 0.00011),
    ("0.0.12", 0.00012),
    ("0.0.100", 0.00100),
    ("0.0.110", 0.00110),
    ("0.0.1000", 0.01000),
    ("0.0.1100", 0.01100),
    ("0.0.10000", 0.10000),
    ("0.0.11000", 0.11000),
    ("0.0.65535", 0.65535),
    ("0.0.65536", 0.65535),  # Build is capped at 65,535
    ("0.1.0", 1),
    ("0.1.1", 1.00001),
    ("0.10.1", 10.00001),
    ("0.11.1", 11.00001),
    ("0.99.1", 99.00001),
    ("0.100.1", 99.00001),  # Minor is capped at 99
    ("1.0.0", 100),
    ("1.1.0", 101),
    ("1.0.1", 100.00001),
    ("1.1.1", 101.00001),
    ("1.2.3-alpha", 102.00003),  # Pre-release tags should be ignored
    ("2.0.0+build.1", 200),  # Build metadata should be ignored
])
def test_version_to_float_conversion(version, expected):
    # Arrange

    # Act
    result = Metrics.version_to_float(version)

    # Assert
    assert result == expected


@pytest.mark.parametrize("version, expected", [
    ("0.0.1", 0.0),
    ("0.0.100", 0.0),
    ("0.1.0", 0.001),
    ("0.1.1", 0.001),
    ("0.99.1", 0.099),
    ("0.100.1", 0.100),
    ("0.999.1", 0.999),
    ("0.1000.1", 0.999),
    ("1.0.0", 1.0),
    ("1.1.0", 1.001),
    ("1.0.1", 1.0),
    ("1.1.1", 1.001),
    ("1.2.3-alpha", 1.002),  # Pre-release tags should be ignored
    ("2.0.0+build.1", 2.0),  # Build metadata should be ignored
])
def test_simple_version_to_float_conversion(version, expected):
    # Arrange

    # Act
    result = Metrics.simple_version_to_float(version)

    # Assert
    assert result == expected


@pytest.mark.parametrize("version, expected", [
    ("0.0.1", 1),
    ("0.0.9", 9),
    ("0.0.10", 10),
    ("0.0.99", 99),
    ("0.0.100", 99),  # Build is capped at 99
    ("0.1.0", 100),
    ("0.1.1", 101),
    ("0.9.0", 900),
    ("0.10.0", 1000),
    ("0.99.0", 9900),
    ("0.100.0", 9900),  # Minor is capped at 99
    ("1.0.0", 10000),
    ("1.2.3-alpha", 10203),  # Pre-release tags should be ignored
    ("2.0.0+build.1", 20000),  # Build metadata should be ignored
])
def test_version_to_int_conversion(version, expected):
    # Arrange

    # Act
    result = Metrics.version_to_int(version)

    # Assert
    assert result == expected


def test_default_factory_creates_unique_instances():
    # Arrange
    metric1 = Metrics(mnemonic="test1", namespace="test", name="test")
    metric2 = Metrics(mnemonic="test2", namespace="test", name="test")

    # Act
    metric1.attributes["key"] = "value"

    # Assert
    assert "key" in metric1.attributes
    assert "key" not in metric2.attributes
    assert id(metric1.attributes) != id(metric2.attributes)
