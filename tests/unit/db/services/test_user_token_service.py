from __future__ import annotations

from flask_app.main_app.db.services.users_service import create_user
from flask_app.main_app.db.services.user_token_service import (
    delete_user_token,
    get_user_token,
    get_user_token_by_username,
    upsert_user_token,
)

def test_delete_user_cascades(app):
    with app.app_context():
        create_user(1030, "svc_dave")
        upsert_user_token(user_id=1030, access_key="k", access_secret="s")
        assert get_user_token(1030) is not None


def test_upsert_get_delete_user_token(app):
    with app.app_context():
        # Test insert
        create_user(1040, "svc_eve")
        upsert_user_token(user_id=1040, access_key="key", access_secret="secret")

        token_record = get_user_token(1040)
        assert token_record is not None
        assert token_record.access_token is not None
        assert token_record.access_secret is not None

        # Test update
        create_user(1040, "svc_eve_updated")
        upsert_user_token(user_id=1040, access_key="new_key", access_secret="new_secret")
        token_record = get_user_token(1040)

        # Test get by username
        token_record = get_user_token_by_username("svc_eve_updated")
        assert token_record is not None
        assert token_record.user_id == 1040

        # Test delete token only
        delete_user_token(1040)
        assert get_user_token(1040) is None

def test_get_user_token_non_existent(app):
    with app.app_context():
        assert get_user_token(999999) is None
        assert get_user_token_by_username("non_existent") is None
