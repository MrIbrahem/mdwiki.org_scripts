""" """

from flask import Flask

from .admin.routes import bp_admin
from .auth.routes import bp_auth
from .fixred import bp_fixred
from .main import bp_main
from .new_jobs import jobs_module
from .newupdater.route import bp_newupdater
from .profile import bp_profile


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)

    app.register_blueprint(jobs_module.bp)
    app.register_blueprint(bp_newupdater)
    app.register_blueprint(bp_fixred)
    app.register_blueprint(bp_profile)


__all__ = [
    "register_blueprints",
]
