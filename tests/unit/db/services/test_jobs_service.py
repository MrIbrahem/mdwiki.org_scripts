import pytest
from flask_app.main_app.db.services.jobs_service import create_job, update_job_status, is_job_cancelled
from flask_app.main_app.extensions import db
from flask_app.main_app.db.models.jobs import JobRecord

def test_is_job_cancelled_stale_repro(app):
    with app.app_context():
        # Create a job and mark it as running
        job = create_job("test_job", "test_user")
        job_id = job.id
        update_job_status(job_id, "running", job_type="test_job")

        # Verify it's not cancelled
        assert is_job_cancelled(job_id, "test_job") is False

        # Verify the object is in the session
        job_in_session = db.session.query(JobRecord).get(job_id)
        assert job_in_session.status == "running"

        # Simulate an external update (bypassing the current session)
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job_id})
            conn.commit()

        # Check if is_job_cancelled sees it.
        # If it returns False, it's because it's using the stale object from the session.
        cancelled_status = is_job_cancelled(job_id, "test_job")

        # If this fails (cancelled_status is False), then we've reproduced the issue.
        # We want to fix it so it's True.
        assert cancelled_status is True
