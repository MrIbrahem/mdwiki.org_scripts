"""
Unit tests for flask_app/main_app/public_jobs/workers/create_redirects/worker.py
"""

from __future__ import annotations

from flask_app.main_app.jobs_workers.public_jobs_workers.create_redirects.worker import (
    CreateRedirectsWorker,
)


class TestCreateRedirectsWorker:
    def test_get_job_type(self):
        worker = CreateRedirectsWorker(job_id=1, args={}, user=None)
        assert worker.get_job_type() == "create_redirects"

    def test_result_type(self):
        from flask_app.main_app.jobs_workers.public_jobs_workers.create_redirects.objects import (
            CreateRedirectsWorkerObject,
        )

        worker = CreateRedirectsWorker(job_id=1, args={}, user=None)
        assert isinstance(worker.result, CreateRedirectsWorkerObject)
