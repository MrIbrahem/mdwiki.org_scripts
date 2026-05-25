""" """

from flask import Flask

from .dup import bp_dup
from .fixred import bp_fixred
from .fixref import bp_fixref
from .import_history import bp_import_history
from .newupdater import bp_newupdater
from .redirect import bp_redirect
from .replace import bp_replace


def register_jobs_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_dup)
    app.register_blueprint(bp_fixred)
    app.register_blueprint(bp_fixref)
    app.register_blueprint(bp_import_history)
    app.register_blueprint(bp_newupdater)
    app.register_blueprint(bp_redirect)
    app.register_blueprint(bp_replace)


__all__ = [
    "register_jobs_blueprints",
]
