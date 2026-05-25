""" """

from flask import Flask

from .main import bp_main
from .jobs import bp_jobs


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_jobs)


__all__ = [
    "register_blueprints",
]
