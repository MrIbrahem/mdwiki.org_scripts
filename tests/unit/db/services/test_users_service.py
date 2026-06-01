from __future__ import annotations

from flask_app.main_app.db.services.users_service import (
    create_user,
    delete_user,
    get_user,
    get_user_by_username,
    list_users,
)
from flask_app.main_app.extensions import db


def test_create_user(app):
    with app.app_context():
        user = create_user(1001, "svc_alice")
        assert user.user_id == 1001
        assert user.username == "svc_alice"

        # Idempotent — returns existing
        user2 = create_user(1001, "svc_alice_renamed")
        assert user2.user_id == 1001
        assert user2.username == "svc_alice_renamed"


def test_get_user(app):
    with app.app_context():
        create_user(1010, "svc_bob")
        user = get_user(1010)
        assert user is not None
        assert user.username == "svc_bob"

        assert get_user(999999) is None


def test_get_user_by_username(app):
    with app.app_context():
        create_user(1020, "svc_charlie")
        user = get_user_by_username("svc_charlie")
        assert user is not None
        assert user.user_id == 1020

        assert get_user_by_username("nonexistent_svc_user") is None


def test_delete_user_cascades(app):
    with app.app_context():
        create_user(1030, "svc_dave")
        delete_user(1030)
        assert get_user(1030) is None

def test_list_users(app):
    with app.app_context():
        # Clean slate
        db.session.execute(db.text("DELETE FROM user_tokens"))
        db.session.execute(db.text("DELETE FROM users"))
        db.session.commit()

        create_user(2001, "list_user1")
        create_user(2002, "list_user2")
        users = list_users()
        assert len(users) == 2
        usernames = {u.username for u in users}
        assert usernames == {"list_user1", "list_user2"}
