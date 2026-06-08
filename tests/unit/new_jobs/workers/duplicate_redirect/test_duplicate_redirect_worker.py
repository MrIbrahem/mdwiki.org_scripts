"""Unit tests for flask_app/main_app/public_jobs/workers/duplicate_redirect/worker.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.public_jobs_workers.duplicate_redirect.worker import (
    DuplicateRedirectWorker,
)


class TestDuplicateRedirectWorker:
    def test_get_job_type(self):
        worker = DuplicateRedirectWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "duplicate_redirect"

    def test_result_type(self):
        from flask_app.main_app.jobs_workers.shared_objects import SharedworkerObject

        worker = DuplicateRedirectWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result, SharedworkerObject)
