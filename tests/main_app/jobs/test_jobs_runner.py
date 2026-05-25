"""Unit tests for the in-process job runner."""

from __future__ import annotations

import time
from threading import Event

import pytest
from flask_app.main_app.jobs import runner
from flask_app.main_app.jobs.models import Job
from flask_app.main_app.jobs.store import JobStore, get_store


def wait_for(job: Job, *statuses: str, timeout: float = 2.0) -> str:
    """Block until ``job.status`` is one of ``statuses`` or ``timeout``."""

    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.status in statuses:
            return job.status
        time.sleep(0.005)
    return job.status


class TestJobStore:
    def test_create_assigns_id_and_remembers(self):
        store = JobStore()
        job = store.create("dup", submitted_by="user", params={"save": True})
        assert job.tool == "dup"
        assert job.submitted_by == "user"
        assert job.id and len(job.id) >= 8
        assert store.get(job.id) is job

    def test_get_unknown_returns_none(self):
        assert JobStore().get("missing") is None

    def test_find_active_only_pending_or_running(self):
        store = JobStore()
        a = store.create("dup")
        b = store.create("dup")
        a.status = "done"
        # a is finished, b is still pending
        active = store.find_active("dup")
        assert active is b

    def test_find_active_returns_none_when_nothing_running(self):
        store = JobStore()
        job = store.create("dup")
        job.status = "error"
        assert store.find_active("dup") is None

    def test_get_store_is_singleton(self):
        assert get_store() is get_store()


class TestSubmit:
    def test_status_transitions_pending_running_done(self):
        events: list[str] = []

        def fn(*, on_progress, stop_event):
            events.append(f"start={('pending', 'running')}")
            on_progress(1, 2, "halfway")
            return {"ok": True}

        job = runner.submit("test", fn)
        wait_for(job, "done", "error")

        assert job.status == "done"
        assert job.result == {"ok": True}
        assert job.progress["done"] == 1
        assert job.progress["total"] == 2
        # The progress message lands in the log.
        assert any("halfway" in line for line in job.log)

    def test_failure_captures_traceback_in_error(self):
        def fn(*, on_progress, stop_event):
            raise RuntimeError("kaboom")

        job = runner.submit("test", fn)
        wait_for(job, "done", "error")

        assert job.status == "error"
        assert "kaboom" in job.error

    def test_stop_event_is_passed_and_responded_to(self):
        def fn(*, on_progress, stop_event):
            for _ in range(50):
                if stop_event.wait(timeout=0.01):
                    return {"stopped": True}
            return {"stopped": False}

        job = runner.submit("test", fn)
        # Let the worker start, then signal stop.
        time.sleep(0.05)
        job.stop_event.set()
        wait_for(job, "done", "error")

        assert job.status == "done"
        assert job.result == {"stopped": True}

    def test_extra_kwargs_are_forwarded(self):
        captured: dict = {}

        def fn(*, on_progress, stop_event, foo, bar):
            captured["foo"] = foo
            captured["bar"] = bar
            return None

        job = runner.submit("test", fn, foo=1, bar="two")
        wait_for(job, "done", "error")
        assert captured == {"foo": 1, "bar": "two"}

    def test_log_buffer_is_capped(self):
        # The buffer respects settings.jobs_log_lines (default 200).
        # We don't assert the exact cap here, just that it's a deque
        # with a maxlen so a runaway service can't OOM us.
        def fn(*, on_progress, stop_event):
            for i in range(500):
                on_progress(i, 500, f"line {i}")
            return None

        job = runner.submit("test", fn)
        wait_for(job, "done", "error")
        assert job.log.maxlen is not None
        assert len(job.log) <= job.log.maxlen
