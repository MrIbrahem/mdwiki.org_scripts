"""Per-blueprint route tests with stubbed services.

Each route is exercised end-to-end through ``app.test_client()`` with the
service ``run`` patched to a deterministic stub. We assert:

* GET renders the form (200, contains a CSRF token + key field).
* POST with valid input submits a job and redirects to ``/jobs/<id>``.
* POST with invalid input re-renders the form with a flash (200).
* The kwargs the blueprint passes to the service match the form data.

Service ``run()`` is monkeypatched directly on the module the blueprint
imports it from, so the stubs see exactly the call shape the blueprint
produces.
"""

from __future__ import annotations

import time


def _wait_done(mock_client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = mock_client.get(f"/jobs/{job_id}.json").get_json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.005)
    return data


# ---------------------------------------------------------------------------
# /replace/  — requires allowlist
# ---------------------------------------------------------------------------


class TestReplace:
    def test_unlisted_user_gets_403(self, mock_client, login):
        login("Plain User")
        r = mock_client.get("/replace/")
        assert r.status_code == 403

    def test_allowlisted_get_renders_form(self, mock_client, login):
        login("Doc James")
        r = mock_client.get("/replace/")
        assert r.status_code == 200
        assert b'name="find"' in r.data
        assert b'name="replace"' in r.data
        assert b'name="listtype"' in r.data

    def test_post_submits_job_with_find_replace_listtype(self, mock_client, login, csrf_token, monkeypatch):
        from flask_app.main_app.public_jobs_workers import replace as repsvc

        captured: dict = {}

        def stub(*, on_progress, stop_event, **kw):
            captured.update(kw)
            return {}

        monkeypatch.setattr(repsvc, "run", stub)
        login("Doc James")
        r = mock_client.post(
            "/replace/",
            data={
                "find": "foo",
                "replace": "bar",
                "listtype": "newlist",
                "number": "5",
                "csrf_token": csrf_token("/replace/"),
            },
        )
        assert r.status_code == 302
        job_id = r.headers["Location"].rsplit("/", 1)[-1]
        data = _wait_done(mock_client, job_id)
        assert captured["find"] == "foo"
        assert captured["replace"] == "bar"
        assert captured["listtype"] == "newlist"
        assert captured["number"] == 5
        # Job params should NOT contain the literal find/replace strings.
        assert "find" not in data["params"]
        assert data["params"]["find_len"] == 3
        assert data["params"]["replace_len"] == 3

    def test_post_empty_find_re_renders_with_flash(self, mock_client, login, csrf_token):
        login("Doc James")
        r = mock_client.post(
            "/replace/",
            data={"find": "", "replace": "x", "csrf_token": csrf_token("/replace/")},
        )
        assert r.status_code == 200
        assert b"<code>find</code>" in r.data or b"`find`" in r.data

    def test_replace_log_compat_redirects_to_jobs(self, mock_client):
        r = mock_client.get("/replace/log?id=abc123")
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/jobs/abc123")

    def test_replace_log_without_id_redirects_to_form(self, mock_client):
        r = mock_client.get("/replace/log")
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/replace/")
