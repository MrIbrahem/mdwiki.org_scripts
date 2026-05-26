""" """

from flask import Flask

from .jobs import bp_jobs
from .main import bp_main
from .new_jobs import bp_public_jobs
from .newupdater.route import bp_newupdater
from .fixred import bp_fixred


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_jobs)
    app.register_blueprint(bp_public_jobs)
    app.register_blueprint(bp_newupdater)
    app.register_blueprint(bp_fixred)


__all__ = [
    "register_blueprints",
]
