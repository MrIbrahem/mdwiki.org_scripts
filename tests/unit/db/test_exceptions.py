from __future__ import annotations

import pytest
from flask_app.main_app.db.exceptions import (
    InsufficientDatabaseConfigError,
    MaxUserConnectionsError,
)


def test_max_user_connections_error():
    with pytest.raises(MaxUserConnectionsError):
        raise MaxUserConnectionsError("Too many connections")


def test_insufficient_database_config_error():
    with pytest.raises(InsufficientDatabaseConfigError, match="DB requires database configuration"):
        raise InsufficientDatabaseConfigError()
