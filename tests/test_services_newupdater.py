"""Tests for services.newupdater."""

from __future__ import annotations

import pytest
from main_app.services import newupdater as svc


class FakePage:
    def __init__(self, *, exists=True, text=""):
        self._exists = exists
        self._text = text
        self.saved: tuple[str, str] | None = None
        self._save_returns = True

    def exists(self) -> bool:
        return self._exists

    def get_text(self) -> str:
        return self._text

    def save(self, *, newtext, summary, **kwargs):
        self.saved = (newtext, summary)
        return self._save_returns


class FakeApi:
    def __init__(self, page: FakePage):
        self._page = page

    def MainPage(self, title: str) -> FakePage:
        return self._page


@pytest.fixture()
def patched_api(monkeypatch):
    """Patch get_api + the legacy text rewriter on the service module."""

    def _build(*, page: FakePage, rewriter):
        monkeypatch.setattr(svc, "get_api", lambda: FakeApi(page))
        monkeypatch.setattr(svc, "_legacy_work_on_text", rewriter)
        return page

    return _build


class TestWorkOnTitle:
    def test_empty_title_is_notext(self, patched_api):
        # No need to set up the api — the early return should fire.
        outcome = svc.work_on_title("")
        assert outcome.kind == "notext"
        assert not outcome.has_changes

    def test_missing_page_is_notext(self, patched_api):
        patched_api(page=FakePage(exists=False), rewriter=lambda t, x: x)
        outcome = svc.work_on_title("Foo")
        assert outcome.kind == "notext"

    def test_blank_text_is_notext(self, patched_api):
        patched_api(page=FakePage(text="   \n"), rewriter=lambda t, x: x)
        outcome = svc.work_on_title("Foo")
        assert outcome.kind == "notext"

    def test_rewriter_returns_blank_is_notext(self, patched_api):
        patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: "")
        outcome = svc.work_on_title("Foo")
        assert outcome.kind == "notext"

    def test_rewriter_returns_same_text_is_no_changes(self, patched_api):
        patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: x)
        outcome = svc.work_on_title("Foo")
        assert outcome.kind == "no_changes"
        assert outcome.old_text == "hello"
        assert outcome.new_text == "hello"

    def test_rewriter_returns_different_text_is_changes(self, patched_api):
        patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: x.upper())
        outcome = svc.work_on_title("Foo")
        assert outcome.kind == "changes"
        assert outcome.has_changes
        assert outcome.old_text == "hello"
        assert outcome.new_text == "HELLO"


class TestSavePage:
    def test_save_re_runs_work_on_title_then_saves(self, patched_api):
        page = patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: x.upper())
        ok, status = svc.save_page("Foo", summary="my summary")
        assert ok is True
        assert status == "saved"
        assert page.saved == ("HELLO", "my summary")

    def test_save_no_changes_returns_false(self, patched_api):
        page = patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: x)
        ok, status = svc.save_page("Foo")
        assert ok is False
        assert status == "no_changes"
        assert page.saved is None

    def test_save_notext_returns_false(self, patched_api):
        page = patched_api(page=FakePage(exists=False), rewriter=lambda t, x: x)
        ok, status = svc.save_page("Foo")
        assert ok is False
        assert status == "notext"
        assert page.saved is None

    def test_save_failure_returns_false_save_failed(self, patched_api):
        page = patched_api(page=FakePage(text="hello"), rewriter=lambda t, x: x.upper())
        page._save_returns = "rate-limited"
        ok, status = svc.save_page("Foo")
        assert ok is False
        assert status == "save_failed"

    def test_save_does_not_accept_user_supplied_new_text(self):
        """The contract is: save_page re-runs the rewriter server-side; it
        must not take a new_text parameter that a malicious client could
        smuggle in. Lock this down at the signature level."""

        import inspect

        sig = inspect.signature(svc.save_page)
        params = list(sig.parameters)
        assert "new_text" not in params
        assert "newtext" not in params
