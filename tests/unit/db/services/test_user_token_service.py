from __future__ import annotations

from flask_app.main_app.db.services.user_token_service import (
    create_user,
    delete_user,
    delete_user_token,
    get_user,
    get_user_token,
    get_user_token_by_username,
    list_users,
    upsert_user_token,
)


def test_create_user(app):
    with app.app_context():
        user = create_user(1, "alice")
        assert user.user_id == 1
        assert user.username == "alice"

        # Idempotent — returns existing
        user2 = create_user(1, "alice_renamed")
        assert user2.user_id == 1
        assert user2.username == "alice_renamed"


def test_get_user(app):
    with app.app_context():
        create_user(10, "bob")
        user = get_user(10)
        assert user is not None
        assert user.username == "bob"

        assert get_user(999) is None


def test_get_user_by_username(app):
    with app.app_context():
        create_user(20, "charlie")
        user = get_user_by_username("charlie")
        assert user is not None
        assert user.user_id == 20

        assert get_user_by_username("nonexistent") is None


def test_delete_user_cascades(app):
    with app.app_context():
        create_user(30, "dave")
        upsert_user_token(user_id=30, username="dave", access_key="k", access_secret="s")
        assert get_user_token(30) is not None

        delete_user(30)
        assert get_user(30) is None
        assert get_user_token(30) is None


def test_upsert_get_delete_user_token(app):
    with app.app_context():
        # Test insert
        upsert_user_token(user_id=1, username="service_test_user", access_key="key", access_secret="secret")

        token_record = get_user_token(1)
        assert token_record is not None
        # Username is on the users table, not on token
        user = get_user(1)
        assert user.username == "service_test_user"
        dec_key, dec_secret = token_record.decrypted()
        assert dec_key == "key"
        assert dec_secret == "secret"

        # Test update
        upsert_user_token(user_id=1, username="test_user_updated", access_key="new_key", access_secret="new_secret")
        token_record = get_user_token(1)
        user = get_user(1)
        assert user.username == "test_user_updated"
        dec_key, dec_secret = token_record.decrypted()
        assert dec_key == "new_key"

        # Test get by username
        token_record = get_user_token_by_username("test_user_updated")
        assert token_record is not None
        assert token_record.user_id == 1

        # Test delete token only
        delete_user_token(1)
        assert get_user_token(1) is None
        # User identity persists
        assert get_user(1) is not None


def test_get_user_token_non_existent(app):
    with app.app_context():
        assert get_user_token(999) is None
        assert get_user_token_by_username("non_existent") is None


def test_list_users(app):
    with app.app_context():
        create_user(1, "user1")
        create_user(2, "user2")
        users = list_users()
        assert len(users) == 2
        usernames = {u.username for u in users}
        assert usernames == {"user1", "user2"}
