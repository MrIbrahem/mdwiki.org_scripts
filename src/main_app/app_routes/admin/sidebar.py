from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from flask import has_request_context, url_for

logger = logging.getLogger(__name__)


def _safe_url_for(endpoint: str, fallback: str, **values: str) -> str:
    if has_request_context():
        return url_for(endpoint, **values)
    return fallback


@dataclass
class SidebarItem:
    """Sidebar menu item definition."""

    id: str
    admin: int
    href: str
    title: str
    icon: str | None = None
    target: str | None = None
    disabled: bool = False


def generate_list_item(item: SidebarItem) -> str:
    """Generate HTML for a single navigation link."""
    href_full = item.href if item.target else f"/admin/{item.href}"
    if item.href.startswith("/admin/"):
        href_full = item.href

    icon_tag = f"<i class='bi {item.icon} me-1'></i>" if item.icon else ""
    target_attr = "target='_blank'" if item.target else ""
    link = f"""
        <a {target_attr} class='link_nav rounded' href='{href_full}' title='{item.title}'
           data-bs-toggle='tooltip' data-bs-placement='right'>
            {icon_tag}
            <span class='hide-on-collapse-inline'>{item.title}</span>
        </a>
    """
    return link.strip()


def create_side(active_route: str, path: str | None = None) -> str:
    """Generate sidebar HTML structure based on menu definitions."""
    main_menu_icons = {
        "Translations": "bi-translate",
        "Main": "bi-file-text",
        "Fix Nested Tasks": "bi-database",
        "Others": "bi-three-dots",
        "Tools": "bi-tools",
        "DB jobs": "bi-database-fill",
        "Files jobs": "bi-files",
        "OWID Templates/Pages": "bi-file-earmark-richtext",
        "Settings": "bi-sliders",
        "Users": "bi-person",
    }

    main_menu = {
        "Users": [
            SidebarItem(
                id="admins",
                admin=1,
                href=_safe_url_for("admin.coordinators.dashboard", "/admin/coordinators/"),
                title="Coordinators",
                icon="bi-person-gear",
            ),
            SidebarItem(
                id="users",
                admin=1,
                href=_safe_url_for("admin.users.dashboard", "/admin/users/"),
                title="Users",
                icon="bi-person",
            ),
        ],
        "Main": [],
    }

    sidebar = ["<ul class='list-unstyled'>"]

    # logger.debug(f"Generating sidebar for active_route='{active_route}'")

    for key, items in main_menu.items():
        lis: list[Any] = []
        group_is_active = False
        key_id = key.lower().replace(" ", "_")
        css_class_full = [item.href for item in items if path == item.href]

        for item in items:
            if item.disabled:
                continue

            css_class = "active" if item.href in css_class_full else ""

            if not css_class_full:
                if path == item.href or (path and path.startswith(item.href)):
                    css_class = "active"

                if not css_class and active_route == item.id:
                    css_class = "active"

            link = generate_list_item(item)

            lis.append(f"<li id='{item.id}' class='{css_class}'>{link}</li>")
            if css_class:
                group_is_active = True

        if lis:
            show = "show" if group_is_active else ""
            expanded = "true" if group_is_active else "false"
            icon = main_menu_icons.get(key, "")
            icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""

            group_html = f"""
                <li class="mb-1">
                    <button class="btn btn-toggle align-items-center rounded"
                            data-bs-toggle="collapse"
                            data-bs-target="#{key_id}-collapse"
                            aria-expanded="{expanded}">
                        {icon_tag}
                        <span class='hide-on-collapse-inline'>{key}</span>
                    </button>
                    <div class="collapse {show}" id="{key_id}-collapse">
                        <div class="d-none d-md-inline">
                            <!-- desktop -->
                            <ul class="btn-toggle-nav list-unstyled fw-normal pb-1 small">
                                {"".join(lis)}
                            </ul>
                        </div>
                        <div class="d-inline d-md-none">
                            <!-- mobile -->
                            <ul class="navbar-nav flex-row flex-wrap btn-toggle-nav-mobile list-unstyled fw-normal pb-1 small">
                                {"".join(lis)}
                            </ul>
                        </div>
                    </div>
                </li>
                <li class="border-top my-1"></li>
            """
            sidebar.append(group_html.strip())

    sidebar.append("</ul>")
    return "\n".join(sidebar)


__all__ = [
    "SidebarItem",
    "generate_list_item",
    "create_side",
]
