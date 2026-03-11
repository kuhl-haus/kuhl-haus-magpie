"""Tests for web/celery_app.py — cover the debug_task body (line 29)."""
from unittest.mock import patch


def test_debug_task_runs(capsys):
    from kuhl_haus.magpie.web.celery_app import debug_task
    # Call debug_task.run() to execute the task body directly.
    debug_task.run()
    captured = capsys.readouterr()
    assert "Request:" in captured.out
