"""Tests to cover remaining gaps in metrics/data/metrics.py."""
import pytest
from logging import Logger
from unittest.mock import MagicMock

from kuhl_haus.magpie.metrics.data.metrics import Metrics


@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)


def test_get_tags_skips_value_error_in_meta():
    """Cover lines 207-208: ValueError exception in __get_tags."""

    class BadBool:
        def __bool__(self):
            raise ValueError("cannot evaluate truthiness")

        def __str__(self):
            return "bad"

    m = Metrics(
        mnemonic="test",
        namespace="ns",
        name="test",
        meta={"good_key": "good_value", "bad_key": BadBool()},
    )
    # Should not raise — ValueError is caught and skipped
    tags = m._Metrics__get_tags()
    assert "good_key=good_value" in tags
    assert "bad_key" not in tags


def test_add_counters_skips_value_error():
    """Cover lines 260-261: ValueError in __add_counters when int(v) fails."""
    m = Metrics(
        mnemonic="test",
        namespace="ns",
        name="test",
        counters={"valid": 5, "invalid": "not_a_number"},
    )
    # Should not raise; 'invalid' counter is skipped
    result = m.carbon
    counter_paths = [path for path, _ in result]
    assert any("valid" in p for p in counter_paths)
    # 'invalid' non-numeric counter should be skipped
    invalid_paths = [p for p in counter_paths if p.endswith("invalid")]
    assert len(invalid_paths) == 0


def test_log_metrics_handles_exception(mock_logger):
    """Cover lines 304-305: exception handling in log_metrics."""
    m = Metrics(
        mnemonic="test",
        namespace="ns",
        name="test",
    )
    # Make logger.info raise to trigger the exception handler (lines 304-305)
    mock_logger.info.side_effect = RuntimeError("simulated logging failure")

    # Should not raise; error is caught and logged
    m.log_metrics(mock_logger)
    mock_logger.error.assert_called_once()
    error_msg = mock_logger.error.call_args[0][0]
    assert "Unhandled exception" in error_msg


def test_add_attributes_skips_non_numeric_non_string():
    """Cover 237->233 branch: attribute value that is neither int/float nor str."""
    m = Metrics(
        mnemonic="test",
        namespace="ns",
        name="test",
        attributes={"numeric": 42, "text": "100", "none_val": None, "list_val": [1, 2]},
    )
    result = m.carbon
    paths = [p for p, _ in result]
    # numeric and text should be included
    assert any("numeric" in p for p in paths)
    assert any("text" in p for p in paths)
    # None and list should be excluded
    assert not any("none_val" in p for p in paths)
    assert not any("list_val" in p for p in paths)
