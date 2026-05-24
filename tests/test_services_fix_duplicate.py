"""Tests for services.fix_duplicate."""

from __future__ import annotations

import threading

import pytest
from main_app.services import fix_duplicate as svc


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


class FakeNewApi:
    def __init__(self, *, redirects):
        self._redirects = redirects

    def post_params(self, params, method="get", **kwargs):
        return {"query": {"redirects": list(self._redirects)}}


class FakeApi:
    def __init__(self, *, redirects, pages):
        self._redirects = redirects
        self._pages = pages

    def NewApi(self):
        return FakeNewApi(redirects=self._redirects)

    def MainPage(self, title):
        return self._pages.get(title, FakePage(exists=False))


@pytest.fixture()
def patched(monkeypatch):
    def _build(*, redirects, pages):
        api = FakeApi(redirects=redirects, pages=pages)
        monkeypatch.setattr(svc, "get_api", lambda: api)
        return api

    return _build


class TestRun:
    def test_resolves_double_redirect_chain(self, patched):
        # A → B, B → C means A is a *double* redirect; final target is C.
        # B → C is a *single* redirect; we shouldn't rewrite B.
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]
        pa = FakePage(text="#REDIRECT [[B]]")
        pb = FakePage(text="#REDIRECT [[C]]")
        patched(redirects=redirects, pages={"A": pa, "B": pb})

        result = svc.run(save=True)

        # Only A was double; only A was rewritten (to point at C).
        assert result["fixed"] == 1
        assert pa.saved is not None
        assert pa.saved[0] == "#REDIRECT [[C]]"
        # B was not a double redirect (its target C is not itself a key in
        # the from→to map), so it should be reported as skipped, not fixed.
        assert pb.saved is None
        assert result["skipped"] == 1

    def test_unchanged_page_reports_unchanged(self, patched):
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]
        # Already correct: A points directly at C.
        pa = FakePage(text="#REDIRECT [[C]]")
        patched(redirects=redirects, pages={"A": pa})
        result = svc.run(save=True)
        assert result["unchanged"] == 1
        assert pa.saved is None

    def test_missing_source_reports_missing(self, patched):
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]
        patched(redirects=redirects, pages={})  # neither A nor B exist
        result = svc.run(save=True)
        assert result["missing"] >= 1

    def test_dry_run_does_not_save(self, patched):
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]
        pa = FakePage(text="#REDIRECT [[B]]")
        patched(redirects=redirects, pages={"A": pa})
        result = svc.run(save=False)
        # dry-run path: outcome="would-fix", which the run loop does not
        # currently bump into any of fixed/unchanged/missing buckets, so we
        # just check no save happened.
        assert pa.saved is None
        assert result["scanned"] >= 1

    def test_offset_skips_entries(self, patched):
        # Two double redirects; offset=1 should skip the first.
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "X", "to": "Y"},
            {"from": "B", "to": "C"},
            {"from": "Y", "to": "Z"},
        ]
        pa = FakePage(text="#REDIRECT [[B]]")
        px = FakePage(text="#REDIRECT [[Y]]")
        patched(redirects=redirects, pages={"A": pa, "X": px})
        # offset=1 skips the first entry (A) but the from_to map is built
        # from the full list, so X→Z (final target Z) still gets fixed.
        result = svc.run(save=True, offset=1)
        assert pa.saved is None  # skipped by offset
        assert px.saved is not None
        assert px.saved[0] == "#REDIRECT [[Z]]"
        assert result["fixed"] == 1

    def test_stop_event_aborts(self, patched):
        redirects = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
            {"from": "X", "to": "Y"},
            {"from": "Y", "to": "Z"},
        ]
        patched(
            redirects=redirects,
            pages={
                "A": FakePage(text="#REDIRECT [[B]]"),
                "X": FakePage(text="#REDIRECT [[Y]]"),
            },
        )

        stop = threading.Event()

        def on_progress(done, total=0, message=None):
            if done >= 1:
                stop.set()

        result = svc.run(save=True, on_progress=on_progress, stop_event=stop)
        # Stop was set after the first entry, so we should have processed
        # fewer than the total.
        assert result["scanned"] < result["total"] or result["total"] == 0
