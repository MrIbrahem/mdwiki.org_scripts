"""Tests for the /jobs/<id> blueprint endpoints."""

from __future__ import annotations

import time

import pytest

from main_app.jobs import runner


def _wait(job, *statuses, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.status in statuses:
            return
        time.sleep(0.005)


def _no_op_done(*, on_progress, stop_event):
    return {"ok": True}


def _slow(*, on_progress, stop_event):
    """Loops until stop_event is set; lets us test the stop endpoint."""

    while not stop_event.wait(timeout=0.02):
        on_progress(0, 0, "tick")
    return {"stopped": True}


class TestStatusPages:
    def test_status_page_404_when_unknown(self, client):
        r = client.get("/jobs/zzzzzz")
        assert r.status_code == 404

    def test_status_json_404_when_unknown(self, client):
        r = client.get("/jobs/zzzzzz.json")
        assert r.status_code == 404
        assert r.get_json() == {"error": "not found"}

    def test_status_page_renders_for_known_job(self, client):
        job = runner.submit("dup", _no_op_done)
        _wait(job, "done")
        r = client.get(f"/jobs/{job.id}")
        assert r.status_code == 200
        assert job.id.encode() in r.data
        assert b"badge bg-" in r.data  # status badge

    def test_status_json_includes_lifecycle_fields(self, client):
        job = runner.submit("dup", _no_op_done)
        _wait(job, "done")
        data = client.get(f"/jobs/{job.id}.json").get_json()
        assert data["id"] == job.id
        assert data["tool"] == "dup"
        assert data["status"] == "done"
        assert data["result"] == {"ok": True}
        # Timestamps are isoformat strings, not datetimes.
        assert isinstance(data["created_at"], str)
        assert "T" in data["created_at"]


class TestStop:
    def test_stop_requires_csrf(self, client, login):
        login("Mr. Ibrahem")
        r = client.post("/jobs/anything/stop")
        assert r.status_code == 400  # CSRFProtect rejects with 400

    def test_stop_unknown_returns_404(self, client, login, csrf_token):
        login("Mr. Ibrahem")
        token = csrf_token("/dup/")
        r = client.post("/jobs/zzzzzz/stop", data={"csrf_token": token})
        assert r.status_code == 404

    def test_stop_sets_event_and_redirects_to_status(self, client, login, csrf_token):
        login("Mr. Ibrahem")
        job = runner.submit("dup", _slow)
        time.sleep(0.05)  # let it start
        token = csrf_token(f"/jobs/{job.id}")
        r = client.post(f"/jobs/{job.id}/stop", data={"csrf_token": token})
        assert r.status_code == 302
        assert r.headers["Location"].endswith(f"/jobs/{job.id}")
        # The slow stub returns once stop_event is set.
        _wait(job, "done", "error", timeout=1.0)
        assert job.status == "done"
        assert job.result == {"stopped": True}

    def test_stop_on_finished_job_is_friendly_redirect(self, client, login, csrf_token):
        login("Mr. Ibrahem")
        job = runner.submit("dup", _no_op_done)
        _wait(job, "done")
        # Status page no longer renders the stop form on a finished job,
        # so we scrape CSRF from any page that has a form.
        token = csrf_token("/dup/")
        r = client.post(f"/jobs/{job.id}/stop", data={"csrf_token": token})
        assert r.status_code == 302
        assert r.headers["Location"].endswith(f"/jobs/{job.id}")
