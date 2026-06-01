""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from ...db.services import user_token_service
from ..admin.admins_required import admin_required

logger = logging.getLogger(__name__)


def _dashboard() -> str:
    """Render the user management dashboard."""
    try:
        users = user_token_service.list_users()
    except Exception as e: # pragma: no cover - defensive guard
        logger.error(f"Error listing users: {e}")
        flash("Error listing users", "error")
        users = []

    total = len(users)

    return render_template(
        "admins/users.html",
        users=users,
        total_users=total,
    )


def _update_user_active(user_id: int) -> ResponseReturnValue:
    """Toggle the active flag for a user."""

    desired = request.form.get("active", "0") == "1"
    try:
        record = user_token_service.set_user_active(user_id, desired)
    except LookupError as exc:
        logger.exception("Unable to update user.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update user.")
        flash("Unable to update user status. Please try again.", "danger")
    else:
        state = "activated" if record.is_active else "deactivated"
        flash(f"User '{record.username}' {state}.", "success")

    return redirect(url_for("admin.users.dashboard"))

class UsersRoutes:
    """Jobs management routes."""

    def __init__(self):
        self.bp = Blueprint("users", __name__, url_prefix="/users")
        self._setup_routes()

    def _setup_routes(self):
        @self.bp.get("/")
        @admin_required
        def dashboard():
            return _dashboard()

        @self.bp.post("/<int:user_id>/active")
        @admin_required
        def update_active(user_id: int) -> ResponseReturnValue:
            return _update_user_active(user_id)


        @self.bp.post("/<int:user_id>/can_run_jobs")
        @admin_required
        def update_can_run_jobs(user_id: int) -> ResponseReturnValue:
            return _update_user_active(user_id)

        @self.bp.post("/<int:user_id>/can_run_bg_jobs")
        @admin_required
        def update_can_run_bg_jobs(user_id: int) -> ResponseReturnValue:
            return _update_user_active(user_id)


users_module = UsersRoutes()

__all__ = [
    "users_module",
]
