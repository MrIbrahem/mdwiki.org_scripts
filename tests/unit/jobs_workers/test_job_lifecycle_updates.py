from __future__ import annotations

from typing import Any, Dict

from flask.app import Flask

from src.main_app.db.services.jobs_service import create_job, is_job_cancelled
from src.main_app.extensions import db
from src.main_app.jobs_workers.base_worker_object import BaseObjectsJobWorker, WorkerObject


class MockWorker(BaseObjectsJobWorker):
    def __init__(self, job_id: int, job_type_name: str = "mock_job") -> None:
        self.job_id = job_id
        self.args = {}
        self.site = None
        self._job_type_name = job_type_name

        super().__init__(job_id, None, None)

        self.result: WorkerObject = WorkerObject()

    def get_job_type(self) -> str:
        return self._job_type_name

    def process(self) -> Dict[str, Any]:
        return self.result.to_json()


def test_before_run_updates_status(app: Flask) -> None:
    with app.app_context():
        job = create_job("mock_job_before_run", "test_user")
        worker = MockWorker(job.id, "mock_job_before_run")

        assert worker.result.status == "pending"
        worker.before_run()
        # This is expected to fail currently based on the issue description
        assert worker.result.status == "running"


def test_is_job_cancelled_detects_external_change(app: Flask) -> None:
    with app.app_context():
        job = create_job("mock_job_cancel_detect", "test_user")

        assert is_job_cancelled(job.id, "mock_job_cancel_detect") is False

        # Update status externally via a different session
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        # is_job_cancelled should detect the external change because it uses a fresh session
        assert is_job_cancelled(job.id, "mock_job_cancel_detect") is True


def test_is_cancelled_sets_cancelled_at(app: Flask) -> None:
    with app.app_context():
        job = create_job("mock_job_cancelled_at", "test_user")
        worker = MockWorker(job.id, "mock_job_cancelled_at")

        # Manually cancel in DB
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        assert worker.result.cancelled_at is None
        assert worker.is_cancelled() is False
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"
        assert worker.result.cancelled_at is not None
