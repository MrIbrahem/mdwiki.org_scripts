"""Unit tests for flask_app/main_app/new_jobs/workers/import_history/objects.py."""

from __future__ import annotations

import pytest
from flask_app.main_app.new_jobs.base_worker_object import WorkerObject
from flask_app.main_app.new_jobs.workers.import_history.objects import (
    ImportHistoryWorkerObject,
    UpdaterOutcome,
)


class TestUpdaterOutcome:
    def test_create_with_defaults(self):
        o = UpdaterOutcome(kind="missing")
        assert o.kind == "missing"
        assert o.newrevid == 0
        assert o.msg == ""

    def test_frozen(self):
        o = UpdaterOutcome(kind="imported")
        with pytest.raises(AttributeError):
            o.kind = "error"

    def test_to_json(self):
        o = UpdaterOutcome(kind="imported_fallback", newrevid=123, msg="ok")
        d = o.to_json()
        assert d["kind"] == "imported_fallback"
        assert d["newrevid"] == 123
        assert d["msg"] == "ok"

    def test_all_kind_values(self):
        for kind in ("missing", "imported", "imported_fallback", "error"):
            o = UpdaterOutcome(kind=kind)
            assert o.kind == kind


class TestImportHistoryWorkerObject:
    def test_inherits_worker_object(self):
        obj = ImportHistoryWorkerObject()
        assert isinstance(obj, WorkerObject)

    def test_default_from_lang(self):
        obj = ImportHistoryWorkerObject()
        assert obj.from_lang == "en"

    def test_default_lists_are_empty(self):
        obj = ImportHistoryWorkerObject()
        assert obj.pages_processed == []
        assert obj.pages_imported == []
        assert obj.pages_imported_fallback == []
        assert obj.pages_errors == []
        assert obj.pages_skipped == []
        assert obj.pages_missing == []

    def test_default_summary(self):
        obj = ImportHistoryWorkerObject()
        assert obj.summary.scanned == 0
        assert obj.summary.total == 0

    def test_lists_are_independent(self):
        a = ImportHistoryWorkerObject()
        b = ImportHistoryWorkerObject()
        a.pages_imported.append({"title": "Test"})
        assert b.pages_imported == []

    def test_to_json(self):
        obj = ImportHistoryWorkerObject(status="running", from_lang="de")
        d = obj.to_json()
        assert d["status"] == "running"
        assert d["from_lang"] == "de"
        assert "summary" in d
