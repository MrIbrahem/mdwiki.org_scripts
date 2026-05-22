"""Tests for services.replace.

Full ``run()`` is exercised against a fake AllAPIS to verify:

* listtype routing (newlist → search, oldlist → all-pages),
* per-page outcomes (changed / no-changes / missing / error),
* the ``number`` cap on successful modifications,
* cooperative ``stop_event``.
"""

from __future__ import annotations

import threading

import pytest

from main_app.services import replace as svc


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakePage:
    """Minimal stand-in for newapi.MainPage."""

    def __init__(self, title: str, *, exists=True, text="", save_returns=True):
        self.title = title
        self._exists = exists
        self._text = text
        self._save_returns = save_returns
        self.saved: tuple[str, str] | None = None

    def exists(self) -> bool:
        return self._exists

    def get_text(self) -> str:
        return self._text

    def save(self, *, newtext: str, summary: str) -> bool:
        self.saved = (newtext, summary)
        return self._save_returns


class FakeNewApi:
    def __init__(self, *, search_results=None, all_pages=None):
        self._search_results = search_results or []
        self._all_pages = all_pages or []
        self.search_calls: list[dict] = []
        self.all_calls: int = 0

    def Search(self, **kwargs):
        self.search_calls.append(kwargs)
        return list(self._search_results)

    def Get_All_pages(self, *args, **kwargs):
        self.all_calls += 1
        return list(self._all_pages)


class FakeApi:
    def __init__(self, *, pages: dict[str, FakePage], new_api: FakeNewApi):
        self._pages = pages
        self._new_api = new_api

    def NewApi(self):
        return self._new_api

    def MainPage(self, title: str) -> FakePage:
        # Default to a missing page for unknown titles.
        return self._pages.get(title, FakePage(title, exists=False))


@pytest.fixture()
def fake_api(monkeypatch):
    """Helper that patches ``services.replace`` to use a FakeApi.

    The factory takes a dict of titles → FakePage and a list of search/all
    page results, and returns the FakeApi (so tests can inspect the calls).
    """

    def _build(*, pages, search_results=None, all_pages=None):
        new_api = FakeNewApi(search_results=search_results, all_pages=all_pages)
        api = FakeApi(pages=pages, new_api=new_api)
        monkeypatch.setattr(svc, "get_api", lambda: api)
        return api

    return _build


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_empty_find_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            svc.run(find="", replace="x", listtype="newlist")

    def test_invalid_listtype_raises(self):
        with pytest.raises(ValueError, match="listtype"):
            svc.run(find="foo", replace="bar", listtype="garbage")  # type: ignore[arg-type]


class TestListtypeRouting:
    def test_newlist_uses_search(self, fake_api):
        api = fake_api(pages={}, search_results=["A", "B"])
        result = svc.run(find="needle", replace="X", listtype="newlist")
        assert result["total"] == 2
        # Search was called with the find string; Get_All_pages was not.
        assert api._new_api.search_calls
        assert api._new_api.search_calls[0]["value"] == "needle"
        assert api._new_api.all_calls == 0

    def test_oldlist_walks_all_pages(self, fake_api):
        api = fake_api(pages={}, all_pages=["X", "Y", "Z"])
        result = svc.run(find="needle", replace="X", listtype="oldlist")
        assert result["total"] == 3
        assert api._new_api.search_calls == []
        assert api._new_api.all_calls == 1


class TestPerPageOutcomes:
    def test_missing_page_is_skipped_and_counted(self, fake_api):
        fake_api(pages={}, search_results=["A"])
        result = svc.run(find="needle", replace="X", listtype="newlist")
        assert result["scanned"] == 1
        assert result["missing"] == 1
        assert result["changed"] == 0

    def test_unchanged_page_not_saved(self, fake_api):
        page = FakePage("A", text="this has no needle", exists=True)
        fake_api(pages={"A": page}, search_results=["A"])
        # `find` doesn't appear in the page text → no change.
        result = svc.run(find="zzzzzz", replace="X", listtype="newlist")
        assert result["no_changes"] == 1
        assert page.saved is None

    def test_changed_page_is_saved_with_replacement(self, fake_api):
        page = FakePage("A", text="hello needle world", exists=True)
        fake_api(pages={"A": page}, search_results=["A"])
        result = svc.run(find="needle", replace="X", listtype="newlist")
        assert result["changed"] == 1
        assert page.saved is not None
        new_text, summary = page.saved
        assert new_text == "hello X world"
        assert "find-and-replace" in summary

    def test_save_failure_counted_as_error(self, fake_api):
        page = FakePage("A", text="needle", exists=True, save_returns="rate-limited")
        fake_api(pages={"A": page}, search_results=["A"])
        result = svc.run(find="needle", replace="X", listtype="newlist")
        assert result["errors"] == 1
        assert result["changed"] == 0

    def test_dry_run_does_not_save(self, fake_api):
        page = FakePage("A", text="needle", exists=True)
        fake_api(pages={"A": page}, search_results=["A"])
        result = svc.run(find="needle", replace="X", listtype="newlist", save=False)
        # dry-run still counts as "would change"
        assert result["changed"] == 1
        assert page.saved is None


class TestNumberCap:
    def test_number_caps_successful_modifications(self, fake_api):
        # Three pages all match; cap to 2 modifications.
        pages = {t: FakePage(t, text="needle", exists=True) for t in ("A", "B", "C")}
        fake_api(pages=pages, search_results=list(pages))
        result = svc.run(find="needle", replace="X", listtype="newlist", number=2)
        assert result["changed"] == 2
        # Exactly two pages got saved; the third was not visited.
        assert sum(1 for p in pages.values() if p.saved is not None) == 2

    def test_no_number_means_no_cap(self, fake_api):
        pages = {t: FakePage(t, text="needle", exists=True) for t in ("A", "B", "C")}
        fake_api(pages=pages, search_results=list(pages))
        result = svc.run(find="needle", replace="X", listtype="newlist")
        assert result["changed"] == 3


class TestStopEvent:
    def test_stop_breaks_between_pages(self, fake_api):
        # Three pages, but stop after the first.
        pages = {t: FakePage(t, text="needle", exists=True) for t in ("A", "B", "C")}
        fake_api(pages=pages, search_results=list(pages))
        stop = threading.Event()

        progress_calls: list[int] = []

        def on_progress(done, total=0, message=None):
            progress_calls.append(done)
            if done >= 1:
                stop.set()

        result = svc.run(
            find="needle",
            replace="X",
            listtype="newlist",
            on_progress=on_progress,
            stop_event=stop,
        )
        assert result["stopped"] is True
        # We processed at least one page before stopping; not all three.
        saved = sum(1 for p in pages.values() if p.saved is not None)
        assert 1 <= saved < 3
