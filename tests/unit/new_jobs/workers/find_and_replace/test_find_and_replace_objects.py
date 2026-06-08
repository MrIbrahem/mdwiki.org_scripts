"""Unit tests for flask_app/main_app/public_jobs/workers/find_and_replace/objects.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.base_worker_object import WorkerObject
from flask_app.main_app.jobs_workers.public_jobs_workers.find_and_replace.objects import (
    FindAndReplaceWorkerObject,
)


class TestFindAndReplaceWorkerObject:
    def test_inherits_worker_object(self):
        obj = FindAndReplaceWorkerObject()
        assert isinstance(obj, WorkerObject)

    def test_default_text_fields(self):
        obj = FindAndReplaceWorkerObject()
        assert obj.text_find == ""
        assert obj.text_replace == ""

    def test_default_stopped(self):
        obj = FindAndReplaceWorkerObject()
        assert obj.stopped is False

    def test_default_cap(self):
        obj = FindAndReplaceWorkerObject()
        assert obj.cap is None

    def test_default_lists_are_empty(self):
        obj = FindAndReplaceWorkerObject()
        assert obj.pages_processed == []
        assert obj.pages_changed == []
        assert obj.pages_errors == []
        assert obj.pages_skipped == []
        assert obj.pages_missing == []

    def test_lists_are_independent(self):
        a = FindAndReplaceWorkerObject()
        b = FindAndReplaceWorkerObject()
        a.pages_changed.append({"title": "X"})
        assert b.pages_changed == []

    def test_to_json(self):
        obj = FindAndReplaceWorkerObject(text_find="old", text_replace="new", cap=10)
        d = obj.to_json()
        assert d["text_find"] == "old"
        assert d["text_replace"] == "new"
        assert d["cap"] == 10
