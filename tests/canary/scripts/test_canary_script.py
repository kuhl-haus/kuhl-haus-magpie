import pytest
from unittest.mock import Mock, patch, create_autospec
from logging import Logger

from kuhl_haus.magpie.canary.models.canary_script import CanaryScript


class ConcreteCanaryScript(CanaryScript):
    """Concrete implementation of CanaryScript for testing."""

    def invoke(self):
        pass


@pytest.fixture
def mock_logger():
    return create_autospec(Logger, spec_set=True)


def test_canary_script_constructor_initializes_properties(mock_logger):
    """Test that CanaryScript constructor properly initializes instance properties."""
    # Arrange
    delay = 5
    count = 3

    # Act
    with patch('kuhl_haus.magpie.canary.models.canary_script.sleep'):
        sut = ConcreteCanaryScript(
            logger=mock_logger,
            delay=delay,
            count=count
        )

    # Assert
    assert sut.logger == mock_logger
    assert sut.delay == delay
    assert sut.count == count


@patch('kuhl_haus.magpie.canary.models.canary_script.sleep')
def test_canary_script_runs_correct_number_of_times(patched_sleep, mock_logger):
    """Test that CanaryScript calls invoke for the specified count."""
    # Arrange
    count = 3
    delay = 1

    # Act
    with patch.object(ConcreteCanaryScript, 'invoke') as mock_invoke:
        sut = ConcreteCanaryScript(
            logger=mock_logger,
            delay=delay,
            count=count
        )

    # Assert
    assert mock_invoke.call_count == count
    assert patched_sleep.call_count == count - 1
    patched_sleep.assert_called_with(delay)


@patch('kuhl_haus.magpie.canary.models.canary_script.sleep')
def test_canary_script_handles_zero_count(patched_sleep, mock_logger):
    """Test that CanaryScript correctly handles count=0."""
    # Arrange
    count = 0
    delay = 1

    # Act
    with patch.object(ConcreteCanaryScript, 'invoke') as mock_invoke:
        sut = ConcreteCanaryScript(
            logger=mock_logger,
            delay=delay,
            count=count
        )

    # Assert
    assert mock_invoke.call_count == 0
    assert patched_sleep.call_count == 0


@patch('kuhl_haus.magpie.canary.models.canary_script.sleep')
def test_canary_script_negative_count_continues_until_stopped(patched_sleep, mock_logger):
    """Test that CanaryScript runs indefinitely with negative count."""
    # Arrange
    count = -1
    delay = 1

    # Create a side effect to break the infinite loop after 5 iterations
    patched_sleep.side_effect = [None, None, None, None, Exception("Stop test")]

    # Act & Assert
    with patch.object(ConcreteCanaryScript, 'invoke') as mock_invoke:
        try:
            sut = ConcreteCanaryScript(
                logger=mock_logger,
                delay=delay,
                count=count
            )
        except Exception as e:
            assert str(e) == "Stop test"

    # Assert it ran the expected number of times before we stopped it
    assert mock_invoke.call_count == 5
    assert patched_sleep.call_count == 5


@patch('kuhl_haus.magpie.canary.models.canary_script.traceback.format_exc')
def test_canary_script_logs_exceptions(patched_format_exc, mock_logger):
    """Test that CanaryScript logs exceptions from invoke method."""
    # Arrange
    count = 1
    delay = 0
    exception_message = "Test exception"
    traceback_output = "Test traceback"
    patched_format_exc.return_value = traceback_output

    # Create a concrete class where invoke raises an exception
    class ExceptionCanaryScript(CanaryScript):
        def invoke(self):
            raise ValueError(exception_message)

    # Act
    sut = ExceptionCanaryScript(
        logger=mock_logger,
        delay=delay,
        count=count
    )

    # Assert
    mock_logger.error.assert_called_once()
    error_message = mock_logger.error.call_args[0][0]
    assert f"Unhandled exception raised (ValueError('{exception_message}'))" in error_message
    assert traceback_output in error_message


@patch('kuhl_haus.magpie.canary.models.canary_script.sleep')
def test_canary_script_waits_between_invocations(patched_sleep, mock_logger):
    """Test that CanaryScript waits the specified delay between invocations."""
    # Arrange
    count = 3
    delay = 5

    # Act
    with patch.object(ConcreteCanaryScript, 'invoke'):
        sut = ConcreteCanaryScript(
            logger=mock_logger,
            delay=delay,
            count=count
        )

    # Assert
    assert patched_sleep.call_count == count - 1
    for call_args in patched_sleep.call_args_list:
        assert call_args[0][0] == delay


def test_canary_script_is_abstract():
    """Test that CanaryScript cannot be instantiated directly."""
    # Arrange & Act & Assert
    with pytest.raises(TypeError):
        CanaryScript(logger=Mock(), delay=1, count=1)
