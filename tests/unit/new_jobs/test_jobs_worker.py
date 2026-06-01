"""Unit tests for flask_app/main_app/new_jobs/jobs_worker.py module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from flask_app.main_app.db.exceptions import JobAlreadyRunningError
from flask_app.main_app.new_jobs.jobs_worker import (
    JOBS_CANCEL_EVENTS,
    JOBS_CANCEL_EVENTS_LOCK,
    _get_jobs_cancel_event,
    _pop_cancel_event,
    _register_cancel_event,
    start_job,
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


class TestStartJob:
    @patch("flask_app.main_app.new_jobs.jobs_worker.create_job")
    @patch("flask_app.main_app.new_jobs.jobs_worker.jobs_data")
    @patch("threading.Thread")
    def test_start_job_raises_error_if_running(
        self, mock_thread, mock_jobs_data, mock_create_job
    ):
        mock_create_job.side_effect = JobAlreadyRunningError("A job of type 'test_type' is already running.")
        mock_jobs_data.get.return_value = MagicMock(job_callable=lambda: None)

        with pytest.raises(JobAlreadyRunningError) as excinfo:
            start_job(user={"username": "test"}, job_type="test_type", args={})

        assert "A job of type 'test_type' is already running." in str(excinfo.value)

    @patch("flask_app.main_app.new_jobs.jobs_worker.create_job")
    @patch("flask_app.main_app.new_jobs.jobs_worker.jobs_data")
    @patch("threading.Thread")
    def test_start_job_starts_if_none_running(
        self, mock_thread, mock_jobs_data, mock_create_job
    ):
        mock_jobs_data.get.return_value = MagicMock(job_callable=lambda: None)
        mock_create_job.return_value = MagicMock(id=123)

        with patch("flask_app.main_app.new_jobs.jobs_worker.current_app", new_callable=MagicMock) as mock_current_app:
            # Mock current_app._get_current_object()
            mock_current_app._get_current_object.return_value = MagicMock()

            job_id = start_job(user={"username": "test"}, job_type="test_type", args={})

            assert job_id == 123
            mock_create_job.assert_called_once_with("test_type", "test")
            mock_thread.return_value.start.assert_called_once()
