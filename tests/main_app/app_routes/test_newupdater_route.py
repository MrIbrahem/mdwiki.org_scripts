""" """

from __future__ import annotations

# ---------------------------------------------------------------------------
# /newupdater/  — synchronous; not a job
# ---------------------------------------------------------------------------


class TestNewupdater:
    def test_get_no_title_renders_form_only(self, client):
        r = client.get("/newupdater/")
        assert r.status_code == 200
        assert b'name="title"' in r.data
        assert b"Save with edit summary" not in r.data

    def test_get_with_title_changes_renders_diff_and_save_button(self, client, monkeypatch):
        import main_app.services.newupdater as nu
        from flask_app.main_app.services.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a\n", new_text="b\n"),
        )
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"Save with edit summary" in r.data

    def test_get_with_title_no_changes_renders_info(self, client, monkeypatch):
        import main_app.services.newupdater as nu
        from flask_app.main_app.services.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="no_changes", old_text="x", new_text="x"),
        )
        r = client.get("/newupdater/?title=Aspirin")
        assert r.status_code == 200
        assert b"no changes" in r.data

    def test_get_with_title_notext_renders_warning(self, client, monkeypatch):
        import main_app.services.newupdater as nu
        from flask_app.main_app.services.newupdater import UpdaterOutcome

        monkeypatch.setattr(nu, "work_on_title", lambda title: UpdaterOutcome(kind="notext"))
        r = client.get("/newupdater/?title=Empty")
        assert r.status_code == 200
        assert b"empty" in r.data.lower()

    def test_post_save_calls_save_page_and_redirects(self, client, csrf_token, monkeypatch):
        import main_app.services.newupdater as nu
        from flask_app.main_app.services.newupdater import UpdaterOutcome

        # Render the diff page so the form has CSRF.
        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a", new_text="b"),
        )
        save_calls: list[str] = []
        monkeypatch.setattr(
            nu,
            "save_page",
            lambda title, summary="Med updater.": (save_calls.append(title) or (True, "saved")),
        )
        token = csrf_token("/newupdater/?title=Aspirin")
        r = client.post(
            "/newupdater/",
            data={"title": "Aspirin", "csrf_token": token},
        )
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/newupdater/?title=Aspirin")
        assert save_calls == ["Aspirin"]

    def test_post_without_title_redirects_with_flash(self, client, csrf_token, monkeypatch):
        import main_app.services.newupdater as nu
        from flask_app.main_app.services.newupdater import UpdaterOutcome

        monkeypatch.setattr(
            nu,
            "work_on_title",
            lambda title: UpdaterOutcome(kind="changes", old_text="a", new_text="b"),
        )
        token = csrf_token("/newupdater/?title=Aspirin")
        r = client.post(
            "/newupdater/",
            data={"title": "", "csrf_token": token},
        )
        assert r.status_code == 302
        # follow it, the index should carry the flash
        r2 = client.get(r.headers["Location"])
        assert b"Provide a title" in r2.data
