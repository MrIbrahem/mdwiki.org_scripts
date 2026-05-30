"""Unit tests for flask_app/main_app/config/main_settings.py module."""

from __future__ import annotations

import os

import pytest

from flask_app.main_app.config.main_settings import (
    _env_bool,
    _env_int,
    load_cookie_config,
    load_other_config,
    resolve_path,
    settings,
)
from flask_app.main_app.config.classes import OtherConfig, CookieConfig


class TestEnvBool:
    def test_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("TEST_BOOL_VAR", raising=False)
        assert _env_bool("TEST_BOOL_VAR", default=False) is False
        assert _env_bool("TEST_BOOL_VAR", default=True) is True

    def test_truthy_values(self, monkeypatch):
        for val in ("1", "true", "True", "TRUE", "yes", "Yes", "on", "On"):
            monkeypatch.setenv("TEST_BOOL_VAR", val)
            assert _env_bool("TEST_BOOL_VAR") is True, f"Expected True for {val!r}"

    def test_falsy_values(self, monkeypatch):
        for val in ("0", "false", "False", "no", "No", "off", "Off"):
            monkeypatch.setenv("TEST_BOOL_VAR", val)
            assert _env_bool("TEST_BOOL_VAR") is False, f"Expected False for {val!r}"

    def test_whitespace_stripped(self, monkeypatch):
        monkeypatch.setenv("TEST_BOOL_VAR", "  true  ")
        assert _env_bool("TEST_BOOL_VAR") is True


class TestEnvInt:
    def test_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("TEST_INT_VAR", raising=False)
        assert _env_int("TEST_INT_VAR", default=42) == 42

    def test_parses_integer(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_VAR", "100")
        assert _env_int("TEST_INT_VAR", default=0) == 100

    def test_raises_on_non_integer(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_VAR", "abc")
        with pytest.raises(ValueError, match="must be an integer"):
            _env_int("TEST_INT_VAR", default=0)

    def test_negative_values(self, monkeypatch):
        monkeypatch.setenv("TEST_INT_VAR", "-5")
        assert _env_int("TEST_INT_VAR", default=0) == -5


class TestResolvePath:
    def test_expands_user_home(self):
        result = resolve_path("~/data")
        assert "~" not in str(result)
        assert "data" in str(result)

    def test_returns_path_object(self):
        from pathlib import Path
        result = resolve_path("/tmp/test")
        assert isinstance(result, Path)


class TestLoadOtherConfig:
    def test_returns_other_config(self):
        result = load_other_config()
        assert isinstance(result, OtherConfig)

    def test_default_wiki_domain(self):
        result = load_other_config()
        assert result.wiki_domain == "mdwiki.org"

    def test_default_allowlist_users(self):
        result = load_other_config()
        assert "Doc James" in result.allowlist_users
        assert "Mr. Ibrahem" in result.allowlist_users

    def test_csrf_time_limit_default(self):
        result = load_other_config()
        assert result.csrf_time_limit == 3600


class TestLoadCookieConfig:
    def test_returns_cookie_config(self):
        result = load_cookie_config()
        assert isinstance(result, CookieConfig)

    def test_default_cookie_name(self):
        result = load_cookie_config()
        assert result.name == "uid_enc"

    def test_default_max_age(self):
        result = load_cookie_config()
        assert result.max_age == 30 * 24 * 3600


class TestSettingsSingleton:
    def test_settings_is_settings_instance(self):
        from flask_app.main_app.config.classes import Settings
        assert isinstance(settings, Settings)

    def test_settings_has_security(self):
        assert settings.security is not None
        assert settings.security.secret_key

    def test_settings_has_oauth(self):
        assert settings.oauth is not None

    def test_settings_has_cookie(self):
        assert settings.cookie is not None

    def test_settings_has_paths(self):
        assert settings.paths is not None
