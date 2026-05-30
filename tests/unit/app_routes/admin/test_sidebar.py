"""Unit tests for flask_app/main_app/app_routes/admin/sidebar.py."""

from __future__ import annotations

from flask_app.main_app.app_routes.admin.sidebar import (
    SidebarItem,
    create_side,
    generate_list_item,
)


class TestSidebarItem:
    def test_create(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test")
        assert item.id == "test"
        assert item.admin == 0
        assert item.href == "/test"
        assert item.title == "Test"
        assert item.icon is None
        assert item.target is None
        assert item.disabled is False

    def test_with_icon(self):
        item = SidebarItem(id="x", admin=1, href="/x", title="X", icon="bi-gear")
        assert item.icon == "bi-gear"


class TestGenerateListItem:
    def test_basic_link(self):
        html = generate_list_item("/test", "Test Page")
        assert "/test" in html
        assert "Test Page" in html
        assert "<a" in html

    def test_with_icon(self):
        html = generate_list_item("/test", "Test", icon="bi-gear")
        assert "bi-gear" in html

    def test_with_target_blank(self):
        html = generate_list_item("/test", "Test", target="_blank")
        assert "target='_blank'" in html

    def test_no_target_by_default(self):
        html = generate_list_item("/test", "Test")
        assert "target=" not in html


class TestCreateSide:
    def test_returns_html_string(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert isinstance(html, str)
            assert "<ul" in html

    def test_contains_coordinators_link(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert "Coordinators" in html

    def test_contains_users_link(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert "Users" in html
