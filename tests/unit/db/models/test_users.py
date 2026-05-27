from __future__ import annotations

from flask_app.main_app.core.crypto import encrypt_value
from flask_app.main_app.db.models.users import AdminUserRecord, UserTokenRecord
from flask_app.main_app.extensions import db


def test_admin_user_record(app):
    with app.app_context():
        admin = AdminUserRecord(username="admin_user", is_active=True)
        db.session.add(admin)
        db.session.commit()

        assert admin.id is not None
        assert admin.username == "admin_user"
        assert admin.is_active is True


def test_user_token_record(app):
    with app.app_context():
        token = encrypt_value("access_token_val")
        secret = encrypt_value("access_secret_val")

        user_token = UserTokenRecord(user_id=123, username="test_user", access_token=token, access_secret=secret)
        db.session.add(user_token)
        db.session.commit()

        assert user_token.user_id == 123
        assert user_token.username == "test_user"

        dec_token, dec_secret = user_token.decrypted()
        assert dec_token == "access_token_val"
        assert dec_secret == "access_secret_val"


def test_user_token_record_validation(app):
    with app.app_context():
        user_token = UserTokenRecord(
            user_id=456, username="test_user_2", access_token=bytearray(b"token"), access_secret=memoryview(b"secret")
        )
        assert isinstance(user_token.access_token, bytes)
        assert isinstance(user_token.access_secret, bytes)
