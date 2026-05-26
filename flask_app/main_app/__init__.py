"""
Flask application factory.
"""

from __future__ import annotations

import logging
from typing import Any, Tuple, Type

from flask import Flask, flash, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from .app_routes import register_blueprints
from .app_routes.auth.routes import bp_auth
from .config import settings
from .core.cookies import CookieHeaderClient
from .db import init_db
from .extensions import db as _db
from .extensions import migrate
from .jobs_routes import register_jobs_blueprints
from .su_services.users_service import current_user

logger = logging.getLogger(__name__)


def context_user() -> dict[str, any]:
    """
    used in @app.context_processor
    """
    user = current_user()
    return {
        "current_user": user,
        "is_authenticated": user is not None,
        "username": user.username if user else None,
        "wiki_domain": settings.other.wiki_domain,
        "static_server": settings.other.static_server,
    }


def register_error_pages(app: Flask):
    @app.errorhandler(400)
    def bad_request(e: Exception) -> Tuple[str, int]:
        """Handle 400 errors"""
        logger.error("Bad request: %s", e)
        flash("Invalid request", "warning")
        return render_template("index.html", title="Bad Request"), 400

    @app.errorhandler(403)
    def forbidden(e: Exception) -> Tuple[str, int]:
        """Handle 403 errors"""
        logger.error("Forbidden access: %s", e)
        flash("Access denied", "danger")
        return render_template("index.html", title="Access Denied"), 403

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> Tuple[str, int]:
        """Handle 404 errors"""
        logger.error("Page not found: %s", e)
        flash("Page not found", "warning")
        return render_template("index.html", title="Page Not Found"), 404

    @app.errorhandler(405)
    def method_not_allowed(e: Exception) -> Tuple[str, int]:
        """Handle 405 errors"""
        logger.error("Method not allowed: %s", e)
        flash("Method not allowed", "warning")
        return render_template("index.html", title="Method Not Allowed"), 405

    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> Tuple[str, int]:
        """Handle 500 errors"""
        logger.error("Internal Server Error: %s", e)
        flash("Internal Server Error", "danger")
        return render_template("index.html", title="Internal Server Error"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> Tuple[str, int]:
        """Handle CSRF token errors"""
        logger.error("CSRF error: %s", e)
        flash("Session expired or invalid. Please try again.", "warning")
        return render_template("index.html", title="Session Expired"), 400


def create_app(config_class: Type) -> Flask:
    """Instantiate and configure the Flask application.

    Args:
        config_class: Configuration class for ``app.config.from_object()``.
            When *None*, auto-detected from the ``FLASK_ENV`` environment
            variable (defaults to ``ProductionConfig``).

    Returns:
        Configured Flask application instance.
    """

    if config_class is None:
        raise ValueError("config_class must be provided")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.url_map.strict_slashes = False
    app.test_client_class = CookieHeaderClient
    app.config.from_object(config_class())

    # Initialize CSRF protection
    csrf = CSRFProtect(app)  # noqa: F841

    # Initialize Flask-SQLAlchemy and Flask-Migrate
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        _db.init_app(app)
        migrate.init_app(app, _db)

        # Create database tables and views if they don't exist
        init_db(app, _db)

    @app.context_processor
    def _inject_user() -> dict[str, Any]:
        return context_user()

    # app.jinja_env.filters["format_stage_timestamp"] = format_stage_timestamp
    # app.jinja_env.filters["short_url"] = short_url

    register_error_pages(app)
    register_blueprints(app)
    app.register_blueprint(bp_auth)
    register_jobs_blueprints(app)

    return app
