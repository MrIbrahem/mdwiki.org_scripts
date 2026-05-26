""" """

from flask import Flask

from .create_redirects import bp_redirect
from .duplicate_redirect import bp_dup
from .find_and_replace import bp_replace
from .fixred_all import bp_fixred_all
from .fixref import bp_fixref
from .import_history import bp_import_history


def register_jobs_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_dup)
    app.register_blueprint(bp_fixred_all)
    app.register_blueprint(bp_fixref)
    app.register_blueprint(bp_import_history)
    app.register_blueprint(bp_redirect)
    app.register_blueprint(bp_replace)


__all__ = [
    "register_jobs_blueprints",
]
