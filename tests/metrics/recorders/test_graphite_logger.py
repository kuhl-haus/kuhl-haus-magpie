import threading
from logging import Logger
from unittest.mock import MagicMock, patch, call, create_autospec

import pytest

from kuhl_haus.magpie.metrics.clients.carbon_poster import CarbonPoster
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.metrics.recorders.graphite_logger import GraphiteLogger, GraphiteLoggerOptions
from kuhl_haus.magpie.metrics.tasks.thread_pool import ThreadPool


@pytest.fixture
def mock_logger():
    return create_autospec(Logger)


@pytest.fixture
def mock_carbon_poster():
    return create_autospec(CarbonPoster)


@pytest.fixture
def mock_thread_pool():
    mock = create_autospec(ThreadPool)
    mock.size = 5
    return mock


@pytest.fixture
def no_carbon_options():
    return GraphiteLoggerOptions(
        application_name="test_app",
        log_level="INFO",
        carbon_config={"server_ip": None, "pickle_port": 2004},
    )


@pytest.fixture
def basic_options():
    return GraphiteLoggerOptions(
        application_name="test_app",
        log_level="INFO",
        carbon_config={"server_ip": "127.0.0.1", "pickle_port": 2004},
    )


@pytest.fixture
def full_options():
    return GraphiteLoggerOptions(
        application_name="test_app",
        log_level="DEBUG",
        carbon_config={"server_ip": "127.0.0.1", "pickle_port": 2004},
        thread_pool_size=10,
        log_directory="/var/log",
        namespace_root="test_root",
        metric_namespace="test_namespace",
        pod_name="test_pod"
    )


@pytest.fixture
def mock_metrics():
    mock = create_autospec(Metrics)
    mock.mnemonic = "test_mnemonic"
    mock.post_metrics = MagicMock()
    mock.log_metrics = MagicMock()
    return mock


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.time")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.random")
def test_graphite_logger_init_with_no_carbon_options(
        patched_random, patched_time, no_carbon_options, mock_metrics, mock_logger, mock_carbon_poster, mock_thread_pool
):
    """Test that log_metrics starts the expected thread pool tasks."""
    # Arrange
    fake_time = 0x12345678
    patched_time.time_ns.return_value = fake_time
    fake_random = 0x42
    patched_random.getrandbits.return_value = fake_random

    sut = GraphiteLogger(no_carbon_options)
    sut.logger = mock_logger
    # sut.poster = mock_carbon_poster
    sut.thread_pool = mock_thread_pool

    expected_template = f"{mock_metrics.mnemonic}_%s_{fake_time:x}_{fake_random:02x}"

    # Act
    sut.log_metrics(mock_metrics)

    # Assert
    assert mock_thread_pool.start_task.call_count == 1
    mock_thread_pool.start_task.assert_has_calls([
        call(
            task_name=expected_template % "log_metrics",
            target=mock_metrics.log_metrics,
            kwargs={"logger": mock_logger},
            blocking=False
        )
    ])
    post_metrics_call = call(
        task_name=expected_template % "post_metrics",
        target=mock_metrics.post_metrics,
        kwargs={"logger": mock_logger, "poster": mock_carbon_poster},
        blocking=False
    )
    assert post_metrics_call not in mock_thread_pool.start_task.call_args_list


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
def test_graphite_logger_init_with_basic_options(
        patched_thread_pool, patched_carbon_poster, patched_get_logger,
        basic_options, mock_logger
):
    """Test GraphiteLogger initialization with basic options."""
    # Arrange
    patched_get_logger.return_value = mock_logger
    mock_poster = MagicMock()
    patched_carbon_poster.return_value = mock_poster
    mock_pool = MagicMock()
    patched_thread_pool.return_value = mock_pool

    # Act
    sut = GraphiteLogger(basic_options)

    # Assert
    patched_get_logger.assert_called_once_with(
        log_level=basic_options.log_level,
        application_name=basic_options.application_name,
        log_directory=basic_options.log_directory
    )
    patched_carbon_poster.assert_called_once_with(**basic_options.carbon_config)
    patched_thread_pool.assert_called_once_with(mock_logger, basic_options.thread_pool_size)
    assert sut.logger == mock_logger
    assert sut.poster == mock_poster
    assert sut.thread_pool == mock_pool


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
def test_graphite_logger_init_with_full_options(
        patched_thread_pool, patched_carbon_poster, patched_get_logger,
        full_options, mock_logger
):
    """Test GraphiteLogger initialization with all options specified."""
    # Arrange
    patched_get_logger.return_value = mock_logger
    mock_poster = MagicMock()
    patched_carbon_poster.return_value = mock_poster
    mock_pool = MagicMock()
    patched_thread_pool.return_value = mock_pool

    # Act
    sut = GraphiteLogger(full_options)

    # Assert
    patched_get_logger.assert_called_once_with(
        log_level=full_options.log_level,
        application_name=full_options.application_name,
        log_directory=full_options.log_directory
    )
    patched_carbon_poster.assert_called_once_with(**full_options.carbon_config)
    patched_thread_pool.assert_called_once_with(mock_logger, full_options.thread_pool_size)
    assert sut.namespace_root == full_options.namespace_root
    assert sut.metric_namespace == full_options.metric_namespace
    assert sut.pod_name == full_options.pod_name


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.Metrics")
def test_get_metrics_with_required_args(patched_metrics, mock_logger, mock_carbon_poster, mock_thread_pool):
    """Test get_metrics method with only required arguments."""
    # Arrange
    mock_metrics_instance = MagicMock()
    patched_metrics.return_value = mock_metrics_instance

    sut = GraphiteLogger.__new__(GraphiteLogger)
    sut.logger = mock_logger
    sut.poster = mock_carbon_poster
    sut.thread_pool = mock_thread_pool
    sut.namespace_root = "test_root"
    sut.metric_namespace = "test_namespace"
    sut.application_name = "test_app"
    sut.pod_name = "test_pod"

    mnemonic = "test_mnemonic"
    metric_name = "test_metric"

    # Act
    result = sut.get_metrics(metric_name, mnemonic)

    # Assert
    patched_metrics.assert_called_once_with(
        mnemonic=mnemonic,
        namespace=f"{sut.namespace_root}.{sut.metric_namespace}",
        name=f"{metric_name}",
        hostname=None,
        meta={'pod': sut.pod_name},
        counters={
            'exceptions': 0,
            'requests': 0,
            'responses': 0,
            'threads': threading.active_count(),
        },
        attributes={
            'request_time': 0,
            'request_time_ms': 0,
            'response_length': 0,
            'thread_pool_size': sut.thread_pool.size,
        },
    )
    assert result == mock_metrics_instance


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.Metrics")
def test_get_metrics_with_hostname(patched_metrics, mock_logger, mock_carbon_poster, mock_thread_pool):
    """Test get_metrics method with hostname specified."""
    # Arrange
    mock_metrics_instance = MagicMock()
    patched_metrics.return_value = mock_metrics_instance

    sut = GraphiteLogger.__new__(GraphiteLogger)
    sut.logger = mock_logger
    sut.poster = mock_carbon_poster
    sut.thread_pool = mock_thread_pool
    sut.namespace_root = "test_root"
    sut.metric_namespace = "test_namespace"
    sut.application_name = "test_app"
    sut.pod_name = "test_pod"

    mnemonic = "test_mnemonic"
    metric_name = "test_metric"
    hostname = "test.hostname.com"

    # Act
    result = sut.get_metrics(metric_name, mnemonic, hostname)

    # Assert
    patched_metrics.assert_called_once_with(
        mnemonic=mnemonic,
        namespace=f"{sut.namespace_root}.{sut.metric_namespace}",
        name=f"{metric_name}",
        hostname=hostname,
        meta={'pod': sut.pod_name},
        counters={
            'exceptions': 0,
            'requests': 0,
            'responses': 0,
            'threads': threading.active_count(),
        },
        attributes={
            'request_time': 0,
            'request_time_ms': 0,
            'response_length': 0,
            'thread_pool_size': sut.thread_pool.size,
        },
    )
    assert result == mock_metrics_instance


@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.time")
@patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.random")
def test_log_metrics_starts_tasks(
        patched_random, patched_time, mock_metrics, mock_logger, mock_carbon_poster, mock_thread_pool
):
    """Test that log_metrics starts the expected thread pool tasks."""
    # Arrange
    fake_time = 0x12345678
    patched_time.time_ns.return_value = fake_time
    fake_random = 0x42
    patched_random.getrandbits.return_value = fake_random

    sut = GraphiteLogger.__new__(GraphiteLogger)
    sut.logger = mock_logger
    sut.poster = mock_carbon_poster
    sut.thread_pool = mock_thread_pool

    expected_template = f"{mock_metrics.mnemonic}_%s_{fake_time:x}_{fake_random:02x}"

    # Act
    sut.log_metrics(mock_metrics)

    # Assert
    assert mock_thread_pool.start_task.call_count == 2
    mock_thread_pool.start_task.assert_has_calls([
        call(
            task_name=expected_template % "post_metrics",
            target=mock_metrics.post_metrics,
            kwargs={"logger": mock_logger, "poster": mock_carbon_poster},
            blocking=False
        ),
        call(
            task_name=expected_template % "log_metrics",
            target=mock_metrics.log_metrics,
            kwargs={"logger": mock_logger},
            blocking=False
        )
    ])


def test_log_metrics_with_none_metrics_raises_attribute_error(mock_logger, mock_carbon_poster, mock_thread_pool):
    """Test that log_metrics raises AttributeError when given None."""
    # Arrange
    sut = GraphiteLogger.__new__(GraphiteLogger)
    sut.logger = mock_logger
    sut.poster = mock_carbon_poster
    sut.thread_pool = mock_thread_pool

    # Act and Assert
    with pytest.raises(AttributeError):
        sut.log_metrics(None)


def test_graphite_logger_options_defaults():
    """Test GraphiteLoggerOptions default values."""
    # Arrange
    application_name = "test_app"
    log_level = "INFO"
    carbon_config = {"server_ip": "127.0.0.1", "pickle_port": 2004}

    # Act
    options = GraphiteLoggerOptions(
        application_name=application_name,
        log_level=log_level,
        carbon_config=carbon_config
    )

    # Assert
    assert options.application_name == application_name
    assert options.log_level == log_level
    assert options.carbon_config == carbon_config
    assert options.thread_pool_size is not None
    assert options.log_directory is None
    assert options.namespace_root is not None
    assert options.metric_namespace is not None
    assert options.pod_name is None


def test_graphite_logger_options_custom_values():
    """Test GraphiteLoggerOptions with custom values."""
    # Arrange
    application_name = "test_app"
    log_level = "DEBUG"
    carbon_config = {"server_ip": "127.0.0.1", "pickle_port": 2004}
    thread_pool_size = 10
    log_directory = "/var/log"
    namespace_root = "custom_root"
    metric_namespace = "custom_namespace"
    pod_name = "custom_pod"

    # Act
    options = GraphiteLoggerOptions(
        application_name=application_name,
        log_level=log_level,
        carbon_config=carbon_config,
        thread_pool_size=thread_pool_size,
        log_directory=log_directory,
        namespace_root=namespace_root,
        metric_namespace=metric_namespace,
        pod_name=pod_name
    )

    # Assert
    assert options.application_name == application_name
    assert options.log_level == log_level
    assert options.carbon_config == carbon_config
    assert options.thread_pool_size == thread_pool_size
    assert options.log_directory == log_directory
    assert options.namespace_root == namespace_root
    assert options.metric_namespace == metric_namespace
    assert options.pod_name == pod_name
