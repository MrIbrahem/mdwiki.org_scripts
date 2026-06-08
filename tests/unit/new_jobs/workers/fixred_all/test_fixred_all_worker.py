"""Unit tests for flask_app/main_app/new_jobs/workers/fixred_all/worker.py."""

from __future__ import annotations

from flask_app.main_app.new_jobs.workers.fixred_all.worker import FixRedAllWorker


class TestFixRedAllWorker:
    def test_get_job_type(self):
        worker = FixRedAllWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "fixred_all"

    def test_result_type(self):
        from flask_app.main_app.new_jobs.shared_objects import SharedworkerObject

        worker = FixRedAllWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result, SharedworkerObject)
