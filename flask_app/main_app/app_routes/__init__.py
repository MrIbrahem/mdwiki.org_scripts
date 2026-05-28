""" """

from flask import Flask

from .fixred import bp_fixred
from .main import bp_main
from .new_jobs import bp_public_jobs
from .newupdater.route import bp_newupdater
from .profile import bp_profile


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_public_jobs)
    app.register_blueprint(bp_newupdater)
    app.register_blueprint(bp_fixred)
    app.register_blueprint(bp_profile)


__all__ = [
    "register_blueprints",
]
