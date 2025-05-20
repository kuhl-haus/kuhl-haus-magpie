import time
from logging import Logger
from threading import Thread
from unittest.mock import patch, create_autospec, MagicMock

import pytest

from kuhl_haus.magpie.metrics.tasks.thread_pool import ThreadPool


@pytest.fixture
def mock_logger():
    mock = MagicMock(spec=Logger)
    return mock


@pytest.fixture
def thread_pool_size():
    return 2


@pytest.fixture
def thread_pool_with_mock_logger(mock_logger, thread_pool_size):
    return ThreadPool(mock_logger, thread_pool_size)


@pytest.fixture
def test_func():
    mock = MagicMock()
    return mock


@pytest.fixture
def long_running_func():
    return lambda: time.sleep(1.0)


@pytest.fixture
def error_func():
    return lambda: 1 / 0


@pytest.fixture
def task_func():
    return lambda: time.sleep(0.001)


class TestException(Exception):
    pass


def test_init(mock_logger, thread_pool_size):
    """Test initialization of the ThreadPool."""
    # Arrange & Act
    idle_time_out = 5
    clean_up_sleep = 15.5
    thread_pool = ThreadPool(
        logger=mock_logger,
        size=thread_pool_size,
        idle_time_out=idle_time_out,
        clean_up_sleep=clean_up_sleep,
    )

    # Assert
    assert thread_pool.size == thread_pool_size
    assert thread_pool.thread_count == 0
    assert thread_pool.idle_time_out == idle_time_out
    assert thread_pool.clean_up_sleep == clean_up_sleep
    assert thread_pool.clean_up_thread_is_alive is True


def test_thread_count_property(thread_pool_with_mock_logger, task_func):
    """Test the thread_count property correctly reports active threads."""
    # Arrange

    # Act
    thread_pool_with_mock_logger.start_task("task1", task_func, {})
    thread_count_after_one = thread_pool_with_mock_logger.thread_count

    thread_pool_with_mock_logger.start_task("task2", task_func, {})
    thread_count_after_two = thread_pool_with_mock_logger.thread_count

    # Wait for tasks to complete
    time.sleep(0.3)
    thread_count_after_completion = thread_pool_with_mock_logger.thread_count

    # Assert
    assert thread_count_after_one == 1
    assert thread_count_after_two == 2
    assert thread_count_after_completion == 0


def test_start_task_basic(thread_pool_with_mock_logger, test_func):
    """Test starting a basic task."""
    # Arrange
    kwargs = {"value": 42}

    # Act
    thread_pool_with_mock_logger.start_task("test_task", test_func, kwargs)

    # Wait for task to execute
    time.sleep(0.1)

    # Assert
    test_func.assert_called_once_with(value=42)


def test_start_task_same_name_alive(thread_pool_with_mock_logger, long_running_func):
    """Test starting a task with the same name while previous is still alive."""
    # Arrange
    second_func = MagicMock()

    # Act
    thread_pool_with_mock_logger.start_task("same_name", long_running_func, {})

    # Try to start another task with the same name before first completes
    thread_pool_with_mock_logger.start_task("same_name", second_func, {})

    # Wait and verify
    time.sleep(0.3)

    # Assert
    second_func.assert_not_called()  # Second task should not be executed


def test_start_task_same_name_completed(thread_pool_with_mock_logger, test_func):
    """Test starting a task with the same name after previous has completed."""
    # Arrange
    second_func = MagicMock()

    # Act
    thread_pool_with_mock_logger.start_task("same_name", test_func, {})
    time.sleep(0.1)  # Let the first task complete

    thread_pool_with_mock_logger.start_task("same_name", second_func, {})
    time.sleep(0.1)  # Let the second task complete

    # Assert
    test_func.assert_called_once()
    second_func.assert_called_once()


def test_pool_size_limit_non_blocking(thread_pool_with_mock_logger, thread_pool_size, test_func, task_func):
    """Test pool size limits with non-blocking calls."""
    # Arrange
    blocking = False

    # Act - Fill the pool
    for i in range(thread_pool_size):
        thread_pool_with_mock_logger.start_task(f"task{i}", task_func, {})

    # Try to add one more task (non-blocking)
    thread_pool_with_mock_logger.start_task("extra_task", test_func, {}, blocking)

    # Assert
    assert thread_pool_with_mock_logger.thread_count == thread_pool_size
    test_func.assert_not_called()  # Extra task should not run


def test_pool_size_limit_blocking(thread_pool_with_mock_logger, thread_pool_size, test_func, task_func):
    """Test pool size limits with blocking calls."""
    # Arrange
    blocking = True

    # Act - Fill the pool
    for i in range(thread_pool_size):
        thread_pool_with_mock_logger.start_task(f"task{i}", task_func, {})

    # Start a thread to add one more task (blocking)
    def add_blocking_task():
        thread_pool_with_mock_logger.start_task("blocking_task", test_func, {}, blocking)

    blocking_thread = Thread(target=add_blocking_task)
    blocking_thread.start()

    # Wait a bit - the blocking task shouldn't run yet
    time.sleep(0.05)
    was_called_before = test_func.called

    # Wait for original tasks to complete
    time.sleep(0.2)
    blocking_thread.join(0.2)  # Wait for blocking thread to complete

    # Assert
    assert not was_called_before  # Should not be called before pool has space
    test_func.assert_called_once()  # Should run once pool has space


def test_cleanup_threads(thread_pool_with_mock_logger, thread_pool_size, test_func, task_func):
    """Test that threads are cleaned up after completion."""
    # Arrange

    # Act
    for i in range(thread_pool_size):
        thread_pool_with_mock_logger.start_task(f"cleanup_task{i}", task_func, {})

    count_during = thread_pool_with_mock_logger.thread_count
    time.sleep(0.3)  # Wait for tasks to complete and cleanup to run
    count_after = thread_pool_with_mock_logger.thread_count

    # Assert
    assert count_during == thread_pool_size
    assert count_after == 0


@patch('kuhl_haus.magpie.metrics.tasks.thread_pool.Thread')
def test_error_handling(patched_thread, thread_pool_with_mock_logger, error_func, mock_logger):
    """Test error handling in tasks."""
    # Arrange
    # Act
    mock_thread = create_autospec(Thread)
    mock_thread.start = MagicMock()
    mock_thread.start.side_effect = TestException
    patched_thread.return_value = mock_thread

    thread_pool_with_mock_logger.start_task("error_task", error_func, {})
    time.sleep(0.1)  # Give error time to be caught

    # Assert
    mock_thread.start.assert_called()
    mock_logger.error.assert_called()
    assert "Unhandled exception raised" in str(mock_logger.error.call_args)


@patch('kuhl_haus.magpie.metrics.tasks.thread_pool.Thread')
def test_cleanup_thread_restart(patched_thread, mock_logger, test_func):
    """Test that the cleanup thread is restarted if needed."""
    # Arrange
    cleanup_thread_1 = create_autospec(Thread)
    cleanup_thread_1.is_alive = MagicMock()
    cleanup_thread_1.start = MagicMock()
    cleanup_thread_1.is_alive.return_value = False

    task_thread = create_autospec(Thread)
    task_thread.is_alive = MagicMock()
    task_thread.start = MagicMock()
    task_thread.is_alive.side_effect = [True, False, False, False, False, False, False]

    cleanup_thread_2 = create_autospec(Thread)
    cleanup_thread_2.is_alive = MagicMock()
    cleanup_thread_2.start = MagicMock()
    cleanup_thread_2.is_alive.return_value = True

    patched_thread.side_effect = [cleanup_thread_1, task_thread, cleanup_thread_2]
    sut = ThreadPool(logger=mock_logger, size=3, idle_time_out=0, clean_up_sleep=0.01)

    before_start_clean_up_thread_is_alive = sut.clean_up_thread_is_alive
    # Start a task to trigger a new cleanup thread
    sut.start_task("new_task", test_func, {})
    after_start_clean_up_thread_is_alive = sut.clean_up_thread_is_alive

    # Assert
    assert before_start_clean_up_thread_is_alive is False
    assert after_start_clean_up_thread_is_alive is True
    assert before_start_clean_up_thread_is_alive != after_start_clean_up_thread_is_alive
    assert patched_thread.call_count == 3
    assert "starting a new thread" in str(mock_logger.debug.call_args)
