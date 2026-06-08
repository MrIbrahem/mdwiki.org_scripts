"""Unit tests for flask_app/main_app/public_jobs/workers/add_r_column/objects.py."""

from __future__ import annotations

from flask_app.main_app.jobs_workers.base_worker_object import WorkerObject
from flask_app.main_app.jobs_workers.public_jobs_workers.add_r_column.objects import (
    AddRColumnWorkerObject,
    StepDetail,
    Steps,
)


class TestStepDetail:
    def test_defaults(self):
        s = StepDetail()
        assert s.status == "pending"
        assert s.title == ""
        assert s.message == ""
        assert s.newrevid is None

    def test_custom_values(self):
        s = StepDetail(status="running", title="Load", message="working", newrevid=123)
        assert s.status == "running"
        assert s.title == "Load"
        assert s.newrevid == 123


class TestSteps:
    def test_default_steps(self):
        s = Steps()
        assert s.load_page.title == "get page"
        assert s.load_text.title == "Load page text"
        assert s.add_empty_r_column.title == "Add empty R column"
        assert s.add_r_column.title == "Add R column"
        assert s.final_save.title == "Save page"

    def test_all_pending_by_default(self):
        s = Steps()
        for field_name in ("load_page", "load_text", "add_empty_r_column", "add_r_column", "final_save"):
            step = getattr(s, field_name)
            assert step.status == "pending", f"{field_name} not pending"


class TestAddRColumnWorkerObject:
    def test_inherits_worker_object(self):
        obj = AddRColumnWorkerObject()
        assert isinstance(obj, WorkerObject)

    def test_default_new_text(self):
        obj = AddRColumnWorkerObject()
        assert obj.new_text == ""

    def test_default_steps(self):
        obj = AddRColumnWorkerObject()
        assert isinstance(obj.steps, Steps)

    def test_set_step_status(self):
        obj = AddRColumnWorkerObject()
        obj.set_step_status("load_page", "running", "loading...")
        assert obj.steps.load_page.status == "running"
        assert obj.steps.load_page.message == "loading..."

    def test_set_step_status_invalid_step(self):
        obj = AddRColumnWorkerObject()
        # Should not raise for invalid step name
        obj.set_step_status("nonexistent", "running")

    def test_set_steps_skipped(self):
        obj = AddRColumnWorkerObject()
        obj.steps.load_page.status = "completed"
        obj.set_steps_skipped()
        assert obj.steps.load_page.status == "completed"  # not pending, stays
        assert obj.steps.load_text.status == "skipped"  # was pending, now skipped
        assert obj.steps.add_r_column.status == "skipped"

    def test_to_json(self):
        obj = AddRColumnWorkerObject(status="running", new_text="some text")
        d = obj.to_json()
        assert d["status"] == "running"
        assert d["new_text"] == "some text"
        assert "steps" in d
