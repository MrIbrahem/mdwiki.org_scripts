""" """

from flask import Flask

from .jobs import bp_jobs
from .main import bp_main
from .public_jobs import bp_public_jobs


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_jobs)
    app.register_blueprint(bp_public_jobs)


__all__ = [
    "register_blueprints",
]
