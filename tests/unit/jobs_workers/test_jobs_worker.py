"""Unit tests for flask_app/main_app/public_jobs/jobs_worker.py module."""

from __future__ import annotations

import threading
from unittest.mock import patch

import pytest
from flask.app import Flask
from flask_app.main_app.db.exceptions import DuplicateJobError
from flask_app.main_app.jobs_workers.jobs_worker import (
    JOBS_CANCEL_EVENTS,
    JOBS_CANCEL_EVENTS_LOCK,
    _get_jobs_cancel_event,
    _pop_cancel_event,
    _register_cancel_event,
)


class TestCancelEventRegistry:
    def setup_method(self):
        with JOBS_CANCEL_EVENTS_LOCK:
            JOBS_CANCEL_EVENTS.clear()

    def test_register_and_get(self):
        evt = threading.Event()
        _register_cancel_event(1, evt)
        assert _get_jobs_cancel_event(1) is evt

    def test_get_nonexistent_returns_none(self):
        assert _get_jobs_cancel_event(999) is None

    def test_pop_removes(self):
        evt = threading.Event()
        _register_cancel_event(2, evt)
        popped = _pop_cancel_event(2)
        assert popped is evt
        assert _get_jobs_cancel_event(2) is None

    def test_pop_nonexistent_returns_none(self):
        assert _pop_cancel_event(999) is None

    def test_register_overwrites(self):
        evt1 = threading.Event()
        evt2 = threading.Event()
        _register_cancel_event(3, evt1)
        _register_cancel_event(3, evt2)
        assert _get_jobs_cancel_event(3) is evt2

    def test_multiple_ids(self):
        evt_a = threading.Event()
        evt_b = threading.Event()
        _register_cancel_event(10, evt_a)
        _register_cancel_event(20, evt_b)
        assert _get_jobs_cancel_event(10) is evt_a
        assert _get_jobs_cancel_event(20) is evt_b


def test_start_job_raises_duplicate_job_error(app: Flask) -> None:
    """start_job should propagate DuplicateJobError when create_job raises it."""
    with app.app_context():
        with (
            patch(
                "flask_app.main_app.jobs_workers.jobs_worker.create_job",
                side_effect=DuplicateJobError("A job of type 'test' is already active"),
            ),
            patch(
                "flask_app.main_app.jobs_workers.jobs_worker.jobs_data",
                {"test_type": type("JobData", (), {"job_callable": lambda: None})()},
            ),
        ):
            from flask_app.main_app.jobs_workers.jobs_worker import start_job

            with pytest.raises(DuplicateJobError):
                start_job(
                    user={"username": "testuser"},
                    job_type="test_type",
                    args={},
                )
