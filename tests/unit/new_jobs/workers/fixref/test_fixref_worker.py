"""Unit tests for flask_app/main_app/new_jobs/workers/fixref/worker.py."""

from __future__ import annotations

from flask_app.main_app.new_jobs.workers.fixref.worker import FixRefWorker


class TestFixRefWorker:
    def test_get_job_type(self):
        worker = FixRefWorker(job_id=1, args={"titles": ["Test"]}, user=None)
        assert worker.get_job_type() == "fixref"

    def test_result_object_type(self):
        from flask_app.main_app.new_jobs.shared_objects import SharedworkerObject
        worker = FixRefWorker(job_id=1, args={"titles": ["Test"]}, user=None)
        assert isinstance(worker.result_object, SharedworkerObject)
