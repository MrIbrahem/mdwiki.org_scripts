from __future__ import annotations

from flask_app.main_app.db.services.user_token_service import (
    delete_user_token,
    get_user_token,
    get_user_token_by_username,
    upsert_user_token,
)


def test_upsert_get_delete_user_token(app):
    with app.app_context():
        # Test insert
        upsert_user_token(user_id=1, username="service_test_user", access_key="key", access_secret="secret")

        token_record = get_user_token(1)
        assert token_record is not None
        assert token_record.username == "service_test_user"
        dec_key, dec_secret = token_record.decrypted()
        assert dec_key == "key"
        assert dec_secret == "secret"

        # Test update
        upsert_user_token(user_id=1, username="test_user_updated", access_key="new_key", access_secret="new_secret")
        token_record = get_user_token(1)
        assert token_record.username == "test_user_updated"
        dec_key, dec_secret = token_record.decrypted()
        assert dec_key == "new_key"

        # Test get by username
        token_record = get_user_token_by_username("test_user_updated")
        assert token_record is not None
        assert token_record.user_id == 1

        # Test delete
        delete_user_token(1)
        assert get_user_token(1) is None


def test_get_user_token_non_existent(app):
    with app.app_context():
        assert get_user_token(999) is None
        assert get_user_token_by_username("non_existent") is None
