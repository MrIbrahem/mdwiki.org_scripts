"""Unit tests for flask_app/main_app/public_jobs/workers/import_history/worker.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.public_jobs_workers.import_history.worker import (
    ImportHistoryWorker,
)


class TestImportHistoryWorker:
    def test_get_job_type(self):
        worker = ImportHistoryWorker(job_id=1, args={"titles": ["Test"]}, user=None)
        assert worker.get_job_type() == "import_history"

    def test_result_type(self):
        from flask_app.main_app.jobs_workers.public_jobs_workers.import_history.objects import ImportHistoryWorkerObject

        worker = ImportHistoryWorker(job_id=1, args={"titles": ["Test"]}, user=None)
        assert isinstance(worker.result, ImportHistoryWorkerObject)
