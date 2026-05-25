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
    def test_get_renders_form(self, client, login):
        login("Doc James")
        r = client.get("/fixred/")
        assert r.status_code == 200
        assert b'name="title"' in r.data

    def test_post_with_title_renders_outcome(self, client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import fixred as svc
        from flask_app.main_app.public_jobs_workers.fixred import UpdaterOutcome

        monkeypatch.setattr(
            svc,
            "work_on_title",
            lambda title, save=0, summary="Fix redirects.": UpdaterOutcome(
                kind="changes", old_text="a\n", new_text="b\n"
            ),
        )

        login("Doc James")
        r = client.post(
            "/fixred/",
            data={"title": "Aspirin", "csrf_token": csrf_token("/fixred/")},
        )
        assert r.status_code == 200
        assert b"Proposed changes" in r.data

    def test_get_with_title_query_renders_outcome(self, client, login, monkeypatch):
        """Legacy bookmark URLs like /fixred/?title=Foo continue to work."""

        from flask_app.main_app.public_jobs_workers import fixred as svc
        from flask_app.main_app.public_jobs_workers.fixred import UpdaterOutcome

        monkeypatch.setattr(
            svc,
            "work_on_title",
            lambda title, save=0, summary="Fix redirects.": UpdaterOutcome(
                kind="no_changes", old_text="x", new_text="x"
            ),
        )

        login("Doc James")
        r = client.get("/fixred/?title=Foo")
        assert r.status_code == 200
        assert b"no changes" in r.data

    def test_post_without_title_re_renders_form(self, client, login, csrf_token):
        login("Doc James")
        r = client.post("/fixred/", data={"csrf_token": csrf_token("/fixred/")})
        assert r.status_code == 200
        assert b'name="title"' in r.data
