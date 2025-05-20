from logging import StreamHandler, FileHandler
from unittest.mock import patch, Mock, MagicMock

import pytest

from kuhl_haus.magpie.metrics.factories.logs import get_logger


@pytest.fixture
def temp_log_directory(tmp_path):
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return str(log_dir)


def test_get_logger_defaults():
    """Test get_logger with default parameters."""
    # Arrange
    expected_logger_name = "kuhl_haus.magpie.metrics.factories.logs"

    # Act
    sut = get_logger('DEBUG')

    # Assert
    assert sut.name == expected_logger_name
    assert len(sut.handlers) == 1
    assert isinstance(sut.handlers[0], StreamHandler)

    # Verify formatter
    handler = sut.handlers[0]
    formatter = handler.formatter
    assert '"timestamp"' in formatter._fmt
    assert '"message": "%(message)s"' in formatter._fmt
    for handler in sut.handlers:
        if isinstance(handler, FileHandler):
            assert False


def test_get_logger_with_custom_name():
    """Test get_logger with custom application name."""
    # Arrange
    custom_name = "custom_app"

    # Act
    sut = get_logger('DEBUG', application_name=custom_name)

    # Assert
    assert sut.name == custom_name
    assert len(sut.handlers) == 1
    for handler in sut.handlers:
        if isinstance(handler, FileHandler):
            assert False


@patch("kuhl_haus.magpie.metrics.factories.logs.StreamHandler")
def test_get_logger_with_custom_log_level(mock_stream_handler):
    """Test get_logger with custom log level."""
    # Arrange
    from logging import ERROR
    custom_level = ERROR
    mock_handler = MagicMock()
    mock_stream_handler.return_value = mock_handler
    mock_stream_handler.setLevel = MagicMock()

    # Act
    sut = get_logger(log_level=custom_level)

    # Assert
    assert sut.level == custom_level


@patch("kuhl_haus.magpie.metrics.factories.logs.FileHandler")
@patch("kuhl_haus.magpie.metrics.factories.logs.Path")
def test_get_logger_with_directory(mock_path, mock_file_handler, temp_log_directory):
    """Test get_logger with log directory specified."""
    # Arrange
    log_dir = "/path/to/logs"
    mock_path_instance = Mock()
    mock_path.return_value = mock_path_instance

    app_name = "test_app"
    log_level = "INFO"
    mock_handler = Mock()
    mock_file_handler.return_value = mock_handler

    # Act
    sut = get_logger(
        application_name=app_name,
        log_level=log_level,
        log_directory=log_dir
    )

    # Assert
    assert len(sut.handlers) == 2
    mock_file_handler.assert_called_once_with(f"{log_dir}/{app_name}.log")
    mock_handler.setLevel.assert_called_once_with(log_level)
    mock_handler.setFormatter.assert_called_once()

    # Verify both handlers are attached
    assert isinstance(sut.handlers[0], StreamHandler)
    assert sut.handlers[1] == mock_handler
    file_handler_attached = False
    stream_handler_attached = False
    for handler in sut.handlers:
        if isinstance(handler, StreamHandler):
            stream_handler_attached = True
        if isinstance(handler, Mock):
            file_handler_attached = True
    assert file_handler_attached is True
    assert stream_handler_attached is True


@patch("kuhl_haus.magpie.metrics.factories.logs.Path")
def test_get_logger_creates_directory(mock_path):
    """Test that get_logger creates the log directory if it doesn't exist."""
    # Arrange
    log_dir = "/path/to/logs"
    mock_path_instance = Mock()
    mock_path.return_value = mock_path_instance

    # Act
    with patch("kuhl_haus.magpie.metrics.factories.logs.FileHandler"):
        sut = get_logger('DEBUG', log_directory=log_dir)

    # Assert
    mock_path.assert_called_once_with(log_dir)
    mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_logger_caches_results():
    """Test that get_logger caches results for the same parameters."""
    # Arrange & Act
    logger1 = get_logger('DEBUG', "app1")
    logger2 = get_logger('DEBUG', "app1")
    logger3 = get_logger('DEBUG', "app2")

    # Assert
    assert logger1 is logger2  # Same params should return cached instance
    assert logger1 is not logger3  # Different params should return new instance


def test_get_logger_stream_handler_formatter():
    """Test the format of the stream handler formatter."""
    # Arrange & Act
    sut = get_logger('DEBUG', )
    formatter = sut.handlers[0].formatter

    # Assert
    format_str = formatter._fmt
    assert '"timestamp": "%(asctime)s"' in format_str
    assert '"filename": "%(filename)s"' in format_str
    assert '"function": "%(funcName)s"' in format_str
    assert '"line": "%(lineno)d"' in format_str
    assert '"level": "%(levelname)s"' in format_str
    assert '"pid": "%(process)d"' in format_str
    assert '"thr": "%(thread)d"' in format_str
    assert '"message": "%(message)s"' in format_str


@patch("kuhl_haus.magpie.metrics.factories.logs.FileHandler")
@patch("kuhl_haus.magpie.metrics.factories.logs.Path")
def test_get_logger_with_multiple_handlers(mock_path, mock_file_handler):
    """Test that get_logger doesn't add duplicate handlers when called multiple times."""
    # Arrange
    mock_path_instance = Mock()
    mock_path.return_value = mock_path_instance
    mock_handler = Mock()
    mock_file_handler.return_value = mock_handler

    # Act
    logger1 = get_logger('DEBUG', "app1", log_directory="/fake/path")

    # Call again with same parameters
    logger2 = get_logger('DEBUG', "app1", log_directory="/fake/path")

    # Assert
    assert logger1 is logger2  # Same params should return cached instance
