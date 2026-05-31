from __future__ import annotations

from flask_app.main_app.core.crypto import encrypt_value
from flask_app.main_app.db.models.users import AdminUserRecord, UsersRecord, UserTokenRecord
from flask_app.main_app.extensions import db


def test_users_record(app):
    with app.app_context():
        user = UsersRecord(user_id=42, username="test_user")
        db.session.add(user)
        db.session.commit()

        assert user.user_id == 42
        assert user.username == "test_user"
        assert user.created_at is not None


def test_admin_user_record(app):
    with app.app_context():
        user = UsersRecord(user_id=1, username="admin_user")
        db.session.add(user)
        db.session.commit()

        admin = AdminUserRecord(username="admin_user", is_active=True)
        db.session.add(admin)
        db.session.commit()

        assert admin.id is not None
        assert admin.username == "admin_user"
        assert admin.is_active is True


def test_user_token_record(app):
    with app.app_context():
        user = UsersRecord(user_id=123, username="test_user")
        db.session.add(user)
        db.session.commit()

        token = encrypt_value("access_token_val")
        secret = encrypt_value("access_secret_val")

        user_token = UserTokenRecord(user_id=123, access_token=token, access_secret=secret)
        db.session.add(user_token)
        db.session.commit()

        assert user_token.user_id == 123
        assert user_token.user.username == "test_user"

        dec_token, dec_secret = user_token.decrypted()
        assert dec_token == "access_token_val"
        assert dec_secret == "access_secret_val"


def test_user_token_record_validation(app):
    with app.app_context():
        user = UsersRecord(user_id=456, username="test_user_2")
        db.session.add(user)
        db.session.commit()

        user_token = UserTokenRecord(user_id=456, access_token=bytearray(b"token"), access_secret=memoryview(b"secret"))
        assert isinstance(user_token.access_token, bytes)
        assert isinstance(user_token.access_secret, bytes)
