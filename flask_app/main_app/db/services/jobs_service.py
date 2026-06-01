from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func, text

from ...extensions import db
from ..exceptions import JobAlreadyRunningError
from ..models.jobs import JobRecord
from .utils import db_guard

logger = logging.getLogger(__name__)


# ------------------
# private API
# ------------------


def _update_status(job_id: int, status: str, result_file: str | None, job_type: str) -> JobRecord:
    """
    Update job status and result file.
    """
    query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    job = query.first()

    if not job:
        raise LookupError(f"Job id {job_id} was not found")

    job.status = status
    if status in ("completed", "failed", "cancelled"):
        job.completed_at = datetime.now(UTC)
    if result_file:
        job.result_file = result_file
    db.session.commit()
    db.session.refresh(job)

    return job


def _update_running_status(job_id: int, result_file: str | None = None, *, job_type: str) -> JobRecord:
    """
    Update running job status and optional result file.
    """
    job = db.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
    if not job:
        raise LookupError(f"Job id {job_id} was not found")

    job.status = "running"
    if not job.started_at:
        job.started_at = datetime.now(UTC)
    if result_file:
        job.result_file = result_file
    db.session.commit()
    db.session.refresh(job)
    return job


# ------------------
# public API
# ------------------


# ── SELECT ───────────────────────────────────────────────


def get_job(job_id: int, job_type: str) -> JobRecord:
    """
    Get a job by ID.

    def get(self, job_id: int, job_type: str = "fix_nested_main_files") -> JobRecord:
        rows = self.db.fetch_query_safe(
            '''
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = %s AND job_type = %s
            ''',
            (job_id, job_type),
        )
        if not rows:
            raise LookupError(f"Job id {job_id} was not found")
        return self._row_to_record(rows[0])
    """
    query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    job = query.first()
    if not job:
        raise LookupError(f"Job id {job_id} was not found")
    return job


def list_jobs(limit: int = 100, job_type: str | None = None) -> list[JobRecord]:
    """
    list recent jobs, optionally filtered by job_type.

    Query to match:
        if job_type:
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE job_type = %s
            ORDER BY created_at DESC
            LIMIT %s
        else:
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT %s
    """
    query = db.session.query(JobRecord)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    return query.order_by(JobRecord.created_at.desc()).limit(limit).all()


@db_guard(default_return=False)
def has_running_job(job_type: str) -> bool:
    """
    Check if there are any jobs of the given type with status 'pending' or 'running'.
    """
    exists = (
        db.session.query(JobRecord.id)
        .filter(JobRecord.job_type == job_type, JobRecord.status.in_(["pending", "running"]))
        .first()
        is not None
    )
    return exists


@db_guard(default_return=False)
def is_job_cancelled(job_id: int, job_type: str) -> bool:
    """
    Check if a job is marked as cancelled.

    Query to match:
        SELECT status FROM jobs WHERE id = %s AND job_type = %s
    """
    record = db.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
    if record:
        # Refresh from database to ensure we don't use a stale cached status
        db.session.refresh(record)
        return record.status == "cancelled"
    return False


def get_user_jobs_stats(username: str) -> dict[str, dict[str, int] | list[JobRecord]]:
    """
    Get user jobs
    """

    base_query = db.session.query(JobRecord).filter(JobRecord.username == username)

    status_counts = dict(
        db.session.query(JobRecord.status, func.count(JobRecord.id))
        .filter(JobRecord.username == username)
        .group_by(JobRecord.status)
        .all()
    )

    recent_jobs = base_query.order_by(JobRecord.created_at.desc()).limit(50).all()

    total_jobs = sum(status_counts.values())

    stats = {
        "total": total_jobs,
        "completed": status_counts.get("completed", 0),
        "failed": status_counts.get("failed", 0),
        "cancelled": status_counts.get("cancelled", 0),
        # "running": status_counts.get("running", 0),
        # "pending": status_counts.get("pending", 0),
    }

    data = {
        "stats": stats,
        "recent_jobs": recent_jobs,
    }

    return data


# ── INSERT, UPDATE, SET ──────────────────────────────────


def create_job(job_type: str, username: str | None = None) -> JobRecord:
    """
    Create a new job record atomically.
    Ensures that only one job of a given type can be in 'pending' or 'running' status.
    """
    # Determine the dialect to handle the "INSERT ... SELECT ... WHERE NOT EXISTS"
    # which requires "FROM DUAL" in MySQL/MariaDB but not in SQLite.
    dialect = db.engine.name

    if dialect == "mysql":
        sql = text(
            """
            INSERT INTO jobs (job_type, username, status)
            SELECT :job_type, :username, 'pending'
            FROM DUAL
            WHERE NOT EXISTS (
                SELECT 1 FROM jobs
                WHERE job_type = :job_type AND status IN ('pending', 'running')
            )
        """
        )
    else:
        # SQLite and others
        sql = text(
            """
            INSERT INTO jobs (job_type, username, status)
            SELECT :job_type, :username, 'pending'
            WHERE NOT EXISTS (
                SELECT 1 FROM jobs
                WHERE job_type = :job_type AND status IN ('pending', 'running')
            )
        """
        )

    result = db.session.execute(sql, {"job_type": job_type, "username": username})

    if result.rowcount == 0:
        raise JobAlreadyRunningError(f"A job of type '{job_type}' is already running.")

    # Get the inserted job record
    # In some dialects/drivers result.lastrowid might be available
    job_id = result.lastrowid

    # If lastrowid is not available (e.g. some Postgres drivers, though not used here),
    # we might need another way, but for MySQL and SQLite it should work.

    db.session.commit()

    # Fetch the full record to return it
    return get_job(job_id, job_type)


def update_job_status(job_id: int, status: str, result_file: str | None = None, *, job_type: str) -> JobRecord:
    """
    Update job status and optional result file.

    Query to match:

    """
    if status == "running":
        return _update_running_status(job_id, result_file, job_type=job_type)

    return _update_status(job_id, status, result_file, job_type)


def cancel_job_db(job_id: int, job_type: str | None = None) -> bool:
    """
    Mark a job as cancelled.
        query = "UPDATE jobs SET status = 'cancelled', completed_at = NOW() WHERE id = %s AND status IN ('pending', 'running')"
        params = [job_id]
        if job_type:
            query += " AND job_type = %s"
            params.append(job_type)

        rowcount = self.db.execute_query_safe(query, tuple(params))
        return rowcount > 0
    """

    try:
        query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
        if job_type:
            query = query.filter(JobRecord.job_type == job_type)

        job = query.filter(JobRecord.status.in_(["pending", "running"])).first()

        if job:
            job.status = "cancelled"
            job.completed_at = datetime.now(UTC)
            db.session.commit()
            db.session.refresh(job)
            return True

    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Failed to cancel job %s in database.", job_id)
        db.session.rollback()

    return False


# ── DELETE ───────────────────────────────────────────────


def delete_job(job_id: int, job_type: str) -> bool:
    """Delete a job by ID and job type efficiently."""
    affected_rows = (
        db.session.query(JobRecord)
        .filter(JobRecord.id == job_id, JobRecord.job_type == job_type)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    return affected_rows > 0


__all__ = [
    "create_job",
    "get_job",
    "list_jobs",
    "update_job_status",
    "cancel_job_db",
    "has_running_job",
    "is_job_cancelled",
    "delete_job",
    "get_user_jobs_stats",
]
