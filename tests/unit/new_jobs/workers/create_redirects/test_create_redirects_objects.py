"""Unit tests for flask_app/main_app/public_jobs/workers/create_redirects/objects.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.base_worker_object import WorkerObject
from flask_app.main_app.jobs_workers.public_jobs_workers.create_redirects.objects import (
    CreateRedirectsWorkerObject,
    RedirectsSummary,
)


class TestSummary:
    def test_defaults(self):
        s = RedirectsSummary()
        assert s.scanned == 0
        assert s.total == 0
        assert s.created == 0
        assert s.errors == 0
        assert s.skipped == 0
        assert s.already_exists == 0
        assert s.target_missing == 0

    def test_mutable(self):
        s = RedirectsSummary()
        s.created = 5
        s.errors = 1
        assert s.created == 5
        assert s.errors == 1


class TestCreateRedirectsWorkerObject:
    def test_inherits_worker_object(self):
        obj = CreateRedirectsWorkerObject()
        assert isinstance(obj, WorkerObject)

    def test_default_lists_are_empty(self):
        obj = CreateRedirectsWorkerObject()
        assert obj.pages_to_work == []
        assert obj.pages_processed == []
        assert obj.pages_errors == []

    def test_default_summary(self):
        obj = CreateRedirectsWorkerObject()
        assert obj.summary.scanned == 0

    def test_lists_are_independent(self):
        a = CreateRedirectsWorkerObject()
        b = CreateRedirectsWorkerObject()
        a.pages_to_work.append("Page1")
        assert b.pages_to_work == []

    def test_to_json(self):
        obj = CreateRedirectsWorkerObject(status="completed")
        d = obj.to_json()
        assert d["status"] == "completed"
        assert "summary" in d
        assert "pages_to_work" in d
