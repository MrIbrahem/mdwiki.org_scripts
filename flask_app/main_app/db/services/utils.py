from __future__ import annotations

import functools
import logging
import sqlalchemy

from typing import Callable, ParamSpec, TypeVar, Any

from ...extensions import db

logger = logging.getLogger(__name__)


# Define generic types for strict type hinting
P = ParamSpec("P")
R = TypeVar("R")

def db_try_except(default_return: Any = False):
    """Decorator factory to wrap a DB service function.

    On success, the original return value is passed through.
    On *any* exception, the session is rolled back, the error is logged,
    and the specified `default_return` value is returned.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except sqlalchemy.exc.OperationalError as exc:
                logger.error("Failed to check job status: %s", exc)
                db.session.rollback()
            except Exception:
                logger.exception("DB error in %s", func.__qualname__)
                db.session.rollback()
            return default_return
        return wrapper
    return decorator
