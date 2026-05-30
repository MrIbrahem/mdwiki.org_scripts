from __future__ import annotations

import functools
import logging
from typing import Callable

from ...extensions import db

logger = logging.getLogger(__name__)


def db_bool[**P](func: Callable[P, bool]) -> Callable[P, bool]:
    """Wrap a db service function that returns ``bool``.

    On success the original return value is passed through.
    On *any* exception the session is rolled back, the error is logged,
    and ``False`` is returned.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> bool:
        try:
            return func(*args, **kwargs)
        except Exception:
            db.session.rollback()
            logger.exception("DB error in %s", func.__qualname__)
            return False

    return wrapper  # type: ignore[return-value]
