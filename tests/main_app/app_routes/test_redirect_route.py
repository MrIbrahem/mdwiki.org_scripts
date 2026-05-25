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
# /redirect/
# ---------------------------------------------------------------------------


class TestRedirect:
    def test_get_renders_form(self, client):
        r = client.get("/redirect/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b'name="titlelist"' in r.data

    def test_post_single_title_submits_job(self, client, csrf_token, monkeypatch):
        from flask_app.main_app.services import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        r = client.post(
            "/redirect/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        assert captured["titles"] == ["Aspirin"]

    def test_post_titlelist_dedupes_and_strips(self, client, csrf_token, monkeypatch):
        from flask_app.main_app.services import redirect as redsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(redsvc, "run", stub)
        r = client.post(
            "/redirect/",
            data={
                "titlelist": "A\nB\n\n  A  \nC\n",
                "csrf_token": csrf_token("/redirect/"),
            },
        )
        assert r.status_code == 302
        _wait_done(client, r.headers["Location"].rsplit("/", 1)[-1])
        # A appears twice in the input; deduped to once. Empties dropped.
        assert captured["titles"] == ["A", "B", "C"]

    def test_post_empty_re_renders_with_flash(self, client, csrf_token):
        r = client.post(
            "/redirect/",
            data={"csrf_token": csrf_token("/redirect/")},
        )
        assert r.status_code == 200
        assert b"Provide at least one title" in r.data
