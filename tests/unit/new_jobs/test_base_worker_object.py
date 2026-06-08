"""Unit tests for flask_app/main_app/public_jobs/base_worker_object.py module."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.base_worker_object import WorkerObject


class TestWorkerObject:
    def test_default_status(self):
        obj = WorkerObject()
        assert obj.status == "pending"

    def test_started_at_is_set(self):
        obj = WorkerObject()
        assert obj.started_at is not None
        assert "T" in obj.started_at  # ISO format

    def test_completed_at_none_by_default(self):
        obj = WorkerObject()
        assert obj.completed_at is None

    def test_cancelled_at_none_by_default(self):
        obj = WorkerObject()
        assert obj.cancelled_at is None

    def test_error_none_by_default(self):
        obj = WorkerObject()
        assert obj.error is None
        assert obj.error_type is None

    def test_to_json(self):
        obj = WorkerObject(status="running")
        d = obj.to_json()
        assert d["status"] == "running"
        assert "started_at" in d
        assert "completed_at" in d
        assert "cancelled_at" in d
        assert "error" in d
        assert "error_type" in d

    def test_to_json_with_error(self):
        obj = WorkerObject(status="failed", error="boom", error_type="RuntimeError")
        d = obj.to_json()
        assert d["error"] == "boom"
        assert d["error_type"] == "RuntimeError"

    def test_mutable(self):
        obj = WorkerObject()
        obj.status = "completed"
        obj.completed_at = "2025-01-01T00:00:00"
        assert obj.status == "completed"
        assert obj.completed_at == "2025-01-01T00:00:00"
