"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

from ..admin_routes import (
    coordinators_module,
    users_module,
)
from .admins_required import admin_required
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")


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
    return render_template(
        "admins/admin.html",
    )


def register_blueprints(bp_admin) -> None:
    bp_admin.register_blueprint(coordinators_module.bp)
    bp_admin.register_blueprint(users_module.bp)


register_blueprints(bp_admin)


__all__ = [
    "bp_admin",
]
