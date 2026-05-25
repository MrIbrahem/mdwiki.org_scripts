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
# /fixred/
# ---------------------------------------------------------------------------


class TestFixred:
    def test_get_renders_form(self, client):
        r = client.get("/fixred/")
        assert r.status_code == 200
        assert b'name="title"' in r.data

    def test_post_with_title_submits_job(self, client, csrf_token, monkeypatch):
        from flask_app.main_app.services import fixred

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {"scanned": 1}

        monkeypatch.setattr(fixred, "run", stub)

        r = client.post(
            "/fixred/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/fixred/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["title"] == "Aspirin"
        assert captured["save"] is True

    def test_get_with_title_query_also_submits_job(self, client, monkeypatch):
        """Legacy bookmark URLs like /fixred/?title=Foo continue to work."""

        from flask_app.main_app.services import fixred

        called = []

        def stub(*, on_progress, stop_event, **kw):
            called.append(kw["title"])
            return {}

        monkeypatch.setattr(fixred, "run", stub)

        r = client.get("/fixred/?title=Foo")
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert called == ["Foo"]

    def test_post_without_title_re_renders_form(self, client, csrf_token):
        r = client.post("/fixred/", data={"csrf_token": csrf_token("/fixred/")})
        assert r.status_code == 200
        assert b"Please provide a title" in r.data
