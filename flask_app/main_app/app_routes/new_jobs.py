"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..db.services import (
    active_coordinators,
    delete_job,
    get_job,
    list_jobs,
)
from ..new_jobs import jobs_worker
from ..new_jobs.workers_list import jobs_data
from ..su_services import load_job_result
from ..su_services.users_service import current_user
from .utils.routes_utils import load_auth_payload

logger = logging.getLogger(__name__)


bp_public_jobs = Blueprint("new_jobs", __name__, url_prefix="/new_jobs")


def _can_manage_job(job: Any, user: Any) -> bool:
    """Check if the current user can manage (cancel/delete) a job.

    Returns True if the user is an admin (coordinator) or if the user
    is the owner of the job.
    """
    if not user:
        return False
    if user.username in active_coordinators():
        return True
    if job.username and job.username == user.username:
        return True
    return False


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    if jobs_worker.cancel_job(job_id, job_type):
        flash(f"Job {job_id} cancellation requested.", "success")
    else:
        flash(f"Job {job_id} is not running or already cancelled.", "warning")

    return redirect(url_for("new_jobs.jobs_list", job_type=job_type))


def _delete_job(job_id: int, job_type: str) -> Response:
    """Delete a job by ID and job type."""

    try:
        # Cancel the job if it's running
        if jobs_worker.cancel_job(job_id, job_type):
            logger.info(f"Cancelled running job {job_id} before deletion")

        delete_job(job_id, job_type)
        flash(f"Job {job_id} deleted successfully.", "success")
    except Exception as exc:
        logger.exception("Failed to delete job")
        flash(f"Failed to delete job {job_id}: {str(exc)}", "danger")

    return redirect(url_for("new_jobs.jobs_list", job_type=job_type))


def _start_job(job_type: str) -> int | None:
    """Start a job."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_job(auth_payload, job_type)
        flash(f"Job {job_id} started to {job_type.replace('_', ' ')}.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return None


def _start_job_with_args(job_type: str, args: dict[str, Any]) -> int | None:
    """Start a job."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_job_with_args(auth_payload, job_type, args)
        flash(f"Job {job_id} started to {job_type.replace('_', ' ')}.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return None


# ================================
# Jobs handlers
# ================================


def _jobs_list(job_type: str) -> str:
    """Render the jobs list dashboard for any job type."""
    # Filter jobs at database level for better performance
    jobs = list_jobs(limit=100, job_type=job_type)

    # sort jobs by created_at key
    if jobs:
        jobs = sorted(jobs, key=lambda x: x.created_at.isoformat() if x.created_at else "", reverse=True)

    template_data = jobs_data.get(job_type)

    if not template_data:
        abort(404)

    template_name = template_data.job_list_template

    return render_template(
        template_name,
        jobs=jobs,
        job_type=job_type,
        list_title=template_data.job_name,
        list_headline=template_data.job_name,
    )


def _job_detail(job_id: int, job_type: str) -> Response | str:
    """Render the job detail page for any job type."""

    try:
        job = get_job(job_id, job_type)
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("new_jobs.jobs_list", job_type=job_type))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = load_job_result(job.result_file)

    template_data = jobs_data.get(job_type)

    if not template_data:
        abort(404)

    template_name = template_data.job_details_template

    return render_template(
        template_name,
        job=job,
        job_type=job_type,
        result_data=result_data,
        detail_title=template_data.job_name,
        detail_headline=template_data.job_name,
    )


class JobsPublicRoutes:
    """Jobs management routes."""

    def __init__(self, bp_public_jobs: Blueprint) -> None:
        # ================================
        # All Jobs List route
        # ================================

        @bp_public_jobs.get("/list")
        def all_jobs_list() -> str:
            jobs = list_jobs(limit=100)
            if jobs:
                jobs = sorted(jobs, key=lambda x: x.created_at.isoformat() if x.created_at else "", reverse=True)
            return render_template("jobs_templates/all_jobs_list.html", jobs=jobs)

        # ================================
        # Cancel Jobs routes
        # ================================

        @bp_public_jobs.post("/<string:job_type>/<int:job_id>/cancel")
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in jobs_data:
                abort(404)

            user = current_user()
            if not user:
                flash("You must be logged in to cancel jobs.", "danger")
                return redirect(url_for("new_jobs.jobs_list", job_type=job_type))

            try:
                job = get_job(job_id, job_type)
            except LookupError:
                flash("Job not found.", "warning")
                return redirect(url_for("new_jobs.jobs_list", job_type=job_type))

            if not _can_manage_job(job, user):
                flash("You don't have permission to cancel this job.", "danger")
                return redirect(url_for("new_jobs.jobs_list", job_type=job_type))

            return _cancel_job(job_id, job_type)

        # ================================
        # Jobs List routes
        # ================================

        @bp_public_jobs.get("/<string:job_type>")
        def jobs_list(job_type: str) -> str:
            return _jobs_list(job_type)

        # ================================
        # Job Detail routes
        # ================================

        @bp_public_jobs.get("/<string:job_type>/<int:job_id>")
        def job_detail(job_type: str, job_id: int) -> Response | str:
            return _job_detail(job_id, job_type)

        # ================================
        # Start Job routes
        # ================================

        @bp_public_jobs.post("/<string:job_type>/start")
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in jobs_data:
                abort(404)
            job_id = _start_job(job_type)
            if not job_id:
                return redirect(url_for("new_jobs.jobs_list", job_type=job_type))
            return redirect(url_for("new_jobs.job_detail", job_type=job_type, job_id=job_id))

        @bp_public_jobs.post("/<string:job_type>/start_with_args")
        def start_job_with_args(job_type: str) -> ResponseReturnValue:
            if job_type not in jobs_data:
                abort(404)

            args = request.form.to_dict()
            job_id = _start_job_with_args(job_type, args)
            if not job_id:
                return redirect(url_for("new_jobs.jobs_list", job_type=job_type))
            return redirect(url_for("new_jobs.job_detail", job_type=job_type, job_id=job_id))

        # ================================
        # Delete Job routes
        # ================================

        # @admin_required
        @bp_public_jobs.post("/<string:job_type>/<int:job_id>/delete")
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in jobs_data:
                abort(404)
            return _delete_job(job_id, job_type)

        @bp_public_jobs.get("/read-job-result-file/<path:result_file>")
        def read_job_result_file(result_file: str) -> ResponseReturnValue:
            """ """
            result_data = load_job_result(result_file)
            return jsonify(result_data)


JobsPublicRoutes(bp_public_jobs)
