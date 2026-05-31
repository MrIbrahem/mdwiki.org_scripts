"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    render_template,
    request,
)

from ...db.services import list_users
from ..admin_routes import (
    coordinators_module,
)
from .admins_required import admin_required
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")

bp_admin.register_blueprint(coordinators_module.bp)


@bp_admin.app_context_processor
def inject_sidebar():
    path_parts = request.path.strip("/").split("/")
    active_route = path_parts[1] if len(path_parts) > 1 else ""
    # logger.debug(f"Injecting sidebar for path='{request.path}', {active_route=}")
    sidebar_html = create_side(active_route=active_route, path=request.path)
    return {"sidebar": sidebar_html}


@bp_admin.get("/")
@admin_required
def admin_dashboard():
    return render_template("admins.html")


@bp_admin.get("/users")
@admin_required
def users_dashboard() -> str:
    """Render the coordinator management dashboard."""
    try:
        users = list_users()
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        flash("Error listing users", "error")
        users = []

    total = len(users)

    return render_template(
        "admins/users.html",
        users=users,
        total_users=total,
    )


__all__ = [
    "bp_admin",
]
