import pytest
from unittest.mock import MagicMock, Mock, patch, create_autospec
from logging import Logger
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.canary.scripts.script import Script
from kuhl_haus.magpie.metrics.clients.carbon_poster import CarbonPoster
from kuhl_haus.magpie.metrics.tasks.thread_pool import ThreadPool
from kuhl_haus.magpie.metrics.recorders.graphite_logger import GraphiteLogger, GraphiteLoggerOptions


class TestScript(Script):
    def __init__(self, count: int, errors: int = 0, exceptions: int = 0, **kwargs):
        super().__init__(count=count, **kwargs)
        self.__count = count
        self.__errors = errors
        self.__exceptions = exceptions
        if errors or exceptions:
            self.__responses = max(0, count - (errors + exceptions))

        else:
            self.__responses = count

    def invoke(self) -> Metrics:
        metrics: Metrics = Metrics(
            mnemonic="models",
            namespace=f"tests.unit",
            counters={
                'exceptions': self.__exceptions,
                'requests': self.__count,
                'responses': self.__count,
                'errors': self.__errors,
            },
        )
        return metrics


@pytest.fixture
def mock_graphite_logger() -> GraphiteLogger:
    mock_logger = create_autospec(spec=Logger)
    mock_poster = create_autospec(spec=CarbonPoster)
    mock_thread_pool = create_autospec(spec=ThreadPool)
    mock = create_autospec(spec=GraphiteLogger)
    mock.logger = MagicMock()
    mock.logger.return_value = mock_logger
    mock.poster = MagicMock()
    mock.poster.return_value = mock_poster
    mock.thread_pool = MagicMock()
    mock.thread_pool.return_value = mock_thread_pool
    return mock
    # request_logger = GraphiteLogger(GraphiteLoggerOptions(
    #     application_name='bedrock_api',
    #     log_level=LOG_LEVEL,
    #     carbon_server_ip=CARBON_SERVER_IP,
    #     carbon_pickle_port=CARBON_PICKLE_PORT,
    #     thread_pool_size=THREAD_POOL_SIZE,
    #     namespace_root=NAMESPACE_ROOT,
    #     metric_namespace=METRIC_NAMESPACE,
    #     pod_name=POD_NAME,
    # ))


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_script_single_execution(mock_graphite_logger):
    """Test script executes once with count=1"""
    # Arrange
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)
    thread_pool.start_task = MagicMock()

    # Act
    TestScript(
        recorder=mock_graphite_logger,
        delay=1,
        count=1
    )

    # Assert
    # poster.post_metrics.assert_called_once()
    # logger.info.assert_called_once()


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_script_multiple_executions(mock_graphite_logger):
    # Arrange
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)

    # Act
    TestScript(
        recorder=mock_graphite_logger,
        delay=0,
        count=2
    )

    # Assert
    # poster.post_metrics.assert_called()
    # logger.info.assert_called()
    # logger.error.assert_not_called()


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_script_handles_exception(mock_graphite_logger):
    """Test script properly handles exceptions"""

    # Arrange
    mock_graphite_logger.logger.info = MagicMock()
    mock_graphite_logger.logger.error = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)

    class ErrorScript(TestScript):
        def invoke(self):
            raise ValueError("Test error")

    # Act
    ErrorScript(
        recorder=mock_graphite_logger,
        delay=1,
        count=1
    )

    # Assert
    mock_graphite_logger.logger.error.assert_called_once()
    assert "ValueError" in mock_graphite_logger.logger.error.call_args[0][0]


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_script_negative_count(mock_graphite_logger):
    # Arrange
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)

    # Act
    with patch('kuhl_haus.magpie.canary.scripts.script.sleep') as mock_sleep:
        mock_sleep.side_effect = KeyboardInterrupt()
        with pytest.raises(KeyboardInterrupt):
            TestScript(
                recorder=mock_graphite_logger,
                delay=0,
                count=-1
            )


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_script_with_zero_count(mock_graphite_logger):
    # Arrange
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)

    # Act
    TestScript(
        recorder=mock_graphite_logger,
        delay=0,
        count=0
    )


# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.ThreadPool")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.CarbonPoster")
# @patch("kuhl_haus.magpie.metrics.recorders.graphite_logger.get_logger")
def test_delay_between_executions(mock_graphite_logger):
    # Arrange
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    poster = MagicMock(spec=CarbonPoster)
    poster.post_metrics = MagicMock()
    thread_pool = MagicMock(spec=ThreadPool)

    # Act
    TestScript(
        recorder=mock_graphite_logger,
        delay=1,
        count=2
    )
