"""Unit tests for src/main_app/public_jobs/workers/newupdater_all/worker.py."""

from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.newupdater_all.worker import NewUpdaterAllWorker


class TestNewUpdaterAllWorker:
    def test_get_job_type(self):
        worker = NewUpdaterAllWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "newupdater_all"

    def test_result_type(self):
        from src.main_app.jobs_workers.shared_objects import SharedworkerObject

        worker = NewUpdaterAllWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result, SharedworkerObject)
