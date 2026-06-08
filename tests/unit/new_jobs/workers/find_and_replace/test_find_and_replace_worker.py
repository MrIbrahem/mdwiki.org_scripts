"""Unit tests for flask_app/main_app/new_jobs/workers/find_and_replace/worker.py."""

from __future__ import annotations

from flask_app.main_app.new_jobs.workers.find_and_replace.worker import (
    FindAndReplaceWorker,
)


class TestFindAndReplaceWorker:
    def test_get_job_type(self):
        worker = FindAndReplaceWorker(job_id=1, args={"find": "a", "replace": "b"}, user=None)
        assert worker.get_job_type() == "find_and_replace"

    def test_result_type(self):
        from flask_app.main_app.new_jobs.workers.find_and_replace.objects import FindAndReplaceWorkerObject

        worker = FindAndReplaceWorker(job_id=1, args={"find": "a", "replace": "b"}, user=None)
        assert isinstance(worker.result, FindAndReplaceWorkerObject)
