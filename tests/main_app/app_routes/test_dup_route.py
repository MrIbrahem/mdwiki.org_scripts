""" """

from __future__ import annotations

import time

from flask_app.main_app.jobs.store import get_store


def _wait_done(client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/jobs/{job_id}.json").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.005)
    return data


# ---------------------------------------------------------------------------
# /dup/
# ---------------------------------------------------------------------------


class TestDup:
    def test_get_renders_form(self, client):
        r = client.get("/dup/")
        assert r.status_code == 200
        assert b'name="start"' in r.data
        assert b"csrf_token" in r.data

    def test_post_starts_job_and_redirects(self, client, login, csrf_token, monkeypatch):
        # from flask_app.main_app.app_routes.dup import bp_dup  # noqa: F401  ensure import
        from flask_app.main_app.public_jobs_workers import fix_duplicate

        seen: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            seen["called"] = True
            seen["save"] = kw.get("save")
            on_progress(1, 1, "ok")
            return {"fixed": 0}

        monkeypatch.setattr(fix_duplicate, "run", stub)

        login("Doc James")
        r = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        assert r.status_code == 302
        job_id = r.headers["Location"].rsplit("/", 1)[-1]
        data = _wait_done(client, job_id)
        assert data["status"] == "done"
        assert seen == {"called": True, "save": True}

    def test_concurrent_post_returns_existing_job(self, client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import fix_duplicate

        # Slow stub so the first job is still running when the second POST lands.
        def stub(*, on_progress, stop_event, **kw):
            stop_event.wait(timeout=2.0)
            return {}

        monkeypatch.setattr(fix_duplicate, "run", stub)

        login("Doc James")
        r1 = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        r2 = client.post("/dup/", data={"start": "start", "csrf_token": csrf_token("/dup/")})
        assert r1.headers["Location"] == r2.headers["Location"]

        # Cleanup: signal stop so the worker finishes.
        store = get_store()
        for job in store.all():
            job.stop_event.set()
