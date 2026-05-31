from __future__ import annotations

import pytest
from flask_app.main_app.db.services.jobs_service import (
    cancel_job_db,
    create_job,
    delete_job,
    get_job,
    is_job_cancelled,
    list_jobs,
    update_job_status,
)


def test_jobs_service_lifecycle(app):
    with app.app_context():
        # Create
        job = create_job(job_type="test_type", username="user")
        job_id = job.id
        assert job_id is not None

        # Get
        job = get_job(job_id, job_type="test_type")
        assert job.status == "pending"

        # Update status to running
        update_job_status(job_id, "running", job_type="test_type")
        job = get_job(job_id, job_type="test_type")
        assert job.status == "running"
        assert job.started_at is not None

        # Check not cancelled
        assert is_job_cancelled(job_id, "test_type") is False

        # Cancel
        assert cancel_job_db(job_id, "test_type") is True
        assert is_job_cancelled(job_id, "test_type") is True
        job = get_job(job_id, job_type="test_type")
        assert job.status == "cancelled"
        assert job.completed_at is not None

        # List
        jobs = list_jobs(limit=10, job_type="test_type")
        assert len(jobs) >= 1
        assert jobs[0].id == job_id

        # Delete
        assert delete_job(job_id, "test_type") is True
        with pytest.raises(LookupError):
            get_job(job_id, job_type="test_type")


def test_get_job_not_found(app):
    with app.app_context():
        with pytest.raises(LookupError):
            get_job(999, "any")


def test_update_status_not_found(app):
    with app.app_context():
        with pytest.raises(LookupError):
            update_job_status(999, "running", job_type="any")


def test_cancel_non_existent(app):
    with app.app_context():
        assert cancel_job_db(999, "any") is False


def test_delete_non_existent(app):
    with app.app_context():
        assert delete_job(999, "any") is False
