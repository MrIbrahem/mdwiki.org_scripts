from __future__ import annotations

from flask_app.main_app.db.services.user_token_service import (
    create_user,
    delete_user,
    delete_user_token,
    get_user,
    get_user_by_username,
    get_user_token,
    get_user_token_by_username,
    list_users,
    upsert_user_token,
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
        upsert_user_token(user_id=1030, username="svc_dave", access_key="k", access_secret="s")
        assert get_user_token(1030) is not None

        delete_user(1030)
        assert get_user(1030) is None
        assert get_user_token(1030) is None


def test_upsert_get_delete_user_token(app):
    with app.app_context():
        # Test insert
        upsert_user_token(user_id=1040, username="svc_eve", access_key="key", access_secret="secret")

        token_record = get_user_token(1040)
        assert token_record is not None
        user = get_user(1040)
        assert user.username == "svc_eve"
        assert token_record.access_token is not None
        assert token_record.access_secret is not None

        # Test update
        upsert_user_token(user_id=1040, username="svc_eve_updated", access_key="new_key", access_secret="new_secret")
        token_record = get_user_token(1040)
        user = get_user(1040)
        assert user.username == "svc_eve_updated"

        # Test get by username
        token_record = get_user_token_by_username("svc_eve_updated")
        assert token_record is not None
        assert token_record.user_id == 1040

        # Test delete token only
        delete_user_token(1040)
        assert get_user_token(1040) is None
        # User identity persists
        assert get_user(1040) is not None


def test_get_user_token_non_existent(app):
    with app.app_context():
        assert get_user_token(999999) is None
        assert get_user_token_by_username("non_existent") is None


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
