from __future__ import annotations

from flask.app import Flask
from flask_app.main_app.db.services.users_service import (
    create_user,
    delete_user,
    get_user,
    get_user_by_username,
    list_users,
)
from flask_app.main_app.extensions import db


def test_create_user(app: Flask) -> None:
    with app.app_context():
        user = create_user("svc_alice")
        assert user.user_id is not None
        assert user.username == "svc_alice"

        # Idempotent — returns existing
        user2 = create_user("svc_alice")
        assert user2.user_id == user.user_id
        assert user2.username == "svc_alice"


def test_get_user(app: Flask) -> None:
    with app.app_context():
        user = create_user("svc_bob")
        fetched = get_user(user.user_id)
        assert fetched is not None
        assert fetched.username == "svc_bob"

        assert get_user(999999) is None


def test_get_user_by_username(app: Flask) -> None:
    with app.app_context():
        user = create_user("svc_charlie")
        fetched = get_user_by_username("svc_charlie")
        assert fetched is not None
        assert fetched.user_id == user.user_id

        assert get_user_by_username("nonexistent_svc_user") is None


def test_delete_user_cascades(app: Flask) -> None:
    with app.app_context():
        user = create_user("svc_dave")
        delete_user(user.user_id)
        assert get_user(user.user_id) is None


def test_list_users(app: Flask) -> None:
    with app.app_context():
        # Clean slate
        db.session.execute(db.text("DELETE FROM user_tokens"))
        db.session.execute(db.text("DELETE FROM users"))
        db.session.commit()

        create_user("list_user1")
        create_user("list_user2")
        users = list_users()
        assert len(users) == 2
        usernames = {u.username for u in users}
        assert usernames == {"list_user1", "list_user2"}
