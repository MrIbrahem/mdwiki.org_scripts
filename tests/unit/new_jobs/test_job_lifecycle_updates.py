from __future__ import annotations

import threading
from typing import Any, Dict

from flask_app.main_app.db.models.jobs import JobRecord
from flask_app.main_app.db.services.jobs_service import cancel_job, create_job, is_job_cancelled
from flask_app.main_app.extensions import db
from flask_app.main_app.new_jobs.base_worker_object import BaseObjectsJobWorker, WorkerObject


class MockWorker(BaseObjectsJobWorker):
    def __init__(self, job_id: int) -> None:
        self.job_id = job_id
        self.args = {}
        self.site = None

        super().__init__(job_id, None, None)

        self.result_object: WorkerObject = WorkerObject()

    def get_job_type(self) -> str:
        return "mock_job"

    def process(self) -> Dict[str, Any]:
        return self.result_object.to_json()


def test_before_run_updates_status(app):
    with app.app_context():
        job = create_job("mock_job", "test_user")
        worker = MockWorker(job.id)

        assert worker.result_object.status == "pending"
        worker.before_run()
        # This is expected to fail currently based on the issue description
        assert worker.result_object.status == "running"


def test_is_job_cancelled_detects_external_change(app):
    with app.app_context():
        job = create_job("mock_job", "test_user")

        # Load the job record into the session's identity map
        # is_job_cancelled currently uses scalar query which MIGHT avoid identity map,
        # but let's see if we can make it fail by loading the record.
        _ = db.session.query(JobRecord).get(job.id)

        assert is_job_cancelled(job.id, "mock_job") is False

        # Update status externally via a different session
        # In this test environment, we can just use a separate engine or connection
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        # Now is_job_cancelled should return True.
        # If it uses a session that has a stale view of the world, it might return False
        # (especially if the isolation level was REPEATABLE READ, but even in READ COMMITTED,
        # SQLAlchemy might cache some things if not careful).
        # Actually, scalar query usually DOES go to the DB, but let's see.
        # IF it passes, it means scalar() bypasses the identity map or it's not in it.
        # But let's try to get the record again via ORM.
        job_after = db.session.query(JobRecord).get(job.id)
        assert job_after.status == "pending"  # It is stale here!

        assert is_job_cancelled(job.id, "mock_job") is True

        # After is_job_cancelled calls refresh, job_after should also be updated if it's the same object
        assert job_after.status == "cancelled"


def test_is_cancelled_sets_cancelled_at(app):
    with app.app_context():
        job = create_job("mock_job", "test_user")
        worker = MockWorker(job.id)

        # Manually cancel in DB
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        assert worker.result_object.cancelled_at is None
        assert worker.is_cancelled() is True
        assert worker.result_object.status == "cancelled"
        assert worker.result_object.cancelled_at is not None
