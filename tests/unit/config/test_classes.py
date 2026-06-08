"""Unit tests for flask_app/main_app/config/classes.py module."""

from __future__ import annotations

import pytest
from flask_app.main_app.config.classes import (
    CookieConfig,
    DbConfig,
    JobsConfig,
    OAuthConfig,
    OtherConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
)


class TestDbConfig:
    def test_frozen(self):
        cfg = DbConfig(db_name="x", db_host="h", db_user="u", db_password="p")
        with pytest.raises(AttributeError):
            cfg.db_name = "y"

    def test_to_dict(self):
        cfg = DbConfig(db_name="mydb", db_host="localhost", db_user="user", db_password="pass")
        d = cfg.to_dict()
        assert d == {"db_name": "mydb", "db_host": "localhost", "db_user": "user", "db_password": "pass"}

    def test_none_user_password(self):
        cfg = DbConfig(db_name="x", db_host="h", db_user=None, db_password=None)
        assert cfg.db_user is None
        assert cfg.db_password is None


class TestCookieConfig:
    def test_frozen(self):
        cfg = CookieConfig(name="c", max_age=100, secure=True, httponly=True, samesite="Lax")
        with pytest.raises(AttributeError):
            cfg.name = "other"

    def test_fields(self):
        cfg = CookieConfig(name="uid", max_age=3600, secure=False, httponly=True, samesite="Strict")
        assert cfg.name == "uid"
        assert cfg.max_age == 3600
        assert cfg.secure is False
        assert cfg.samesite == "Strict"


class TestSessionConfig:
    def test_fields(self):
        cfg = SessionConfig(state_key="sk", request_token_key="rtk")
        assert cfg.state_key == "sk"
        assert cfg.request_token_key == "rtk"


class TestOAuthConfig:
    def test_fields(self):
        cfg = OAuthConfig(mw_uri="https://x.org", consumer_key="ck", consumer_secret="cs", encryption_key="ek")
        assert cfg.mw_uri == "https://x.org"
        assert cfg.encryption_key == "ek"

    def test_none_encryption_key(self):
        cfg = OAuthConfig(mw_uri="https://x.org", consumer_key="ck", consumer_secret="cs", encryption_key=None)
        assert cfg.encryption_key is None


class TestSecurityConfig:
    def test_fields(self):
        cfg = SecurityConfig(
            salt="",
            secret_key="sk",
            max_content_length=1024,
            max_form_memory_size=512,
            max_form_parts=100,
            secret_key_fallbacks=("old1", "old2"),
        )
        assert cfg.secret_key == "sk"
        assert cfg.max_content_length == 1024
        assert cfg.secret_key_fallbacks == ("old1", "old2")


class TestOtherConfig:
    def test_fields(self):
        cfg = OtherConfig(
            csrf_time_limit=3600,
            user_agent="test/1.0",
            allowlist_users=("Alice",),
            wiki_domain="example.org",
            static_server="https://cdn.example.org",
        )
        assert cfg.csrf_time_limit == 3600
        assert cfg.allowlist_users == ("Alice",)


class TestJobsConfig:
    def test_fields(self):
        cfg = JobsConfig(jobs_max_workers=4, jobs_log_lines=100)
        assert cfg.jobs_max_workers == 4
        assert cfg.jobs_log_lines == 100


class TestPaths:
    def test_fields(self):
        p = Paths(log_dir="/tmp/logs", jobs_path="/tmp/jobs", public_jobs_path="/tmp/public_jobs")
        assert p.log_dir == "/tmp/logs"


class TestSettings:
    def test_fields(self):
        db = DbConfig(db_name="x", db_host="h", db_user=None, db_password=None)
        paths = Paths(log_dir="/l", jobs_path="/j", public_jobs_path="/n")
        cookie = CookieConfig(name="c", max_age=1, secure=False, httponly=False, samesite="Lax")
        sessions = SessionConfig(state_key="sk", request_token_key="rtk")
        security = SecurityConfig(
            salt="",
            secret_key="s",
            max_content_length=1,
            max_form_memory_size=1,
            max_form_parts=1,
            secret_key_fallbacks=(),
        )
        other = OtherConfig(csrf_time_limit=1, user_agent="t", allowlist_users=(), wiki_domain="w", static_server="s")
        jobs = JobsConfig(jobs_max_workers=1, jobs_log_lines=1)
        s = Settings(
            database_data=db,
            paths=paths,
            cookie=cookie,
            sessions=sessions,
            oauth=None,
            security=security,
            other=other,
            jobs=jobs,
        )
        assert s.database_data == db
        assert s.oauth is None
