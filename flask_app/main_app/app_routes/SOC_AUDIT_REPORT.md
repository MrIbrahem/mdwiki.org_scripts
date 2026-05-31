# Separation of Concerns Audit Report — `app_routes/`

**Project**: mdwiki.org Flask app
**Date**: 2026-05-31
**Auditor**: opencode (flask-soc-audit skill)
**Files Scanned**: 21

---

## Executive Summary

The `app_routes/` layer is **moderately healthy**. Most routes delegate to services properly, but there are two categories of recurring violations: (1) **direct model imports** in 4 files, and (2) a **service-layer worker file mislocated inside app_routes** (`newupdater/worker.py`). The `auth/routes.py` callback route is the longest function and contains significant orchestration logic. One file imports `sqlalchemy.exc.IntegrityError` directly.

### Finding Counts by Severity

| Severity    | Count |
| ----------- | ----- |
| 🔴 Critical | 0     |
| 🟠 High     | 7     |
| 🟡 Medium   | 1     |
| 🟢 Low      | 1     |
| **Total**   | **9** |

### Most Problematic Files

| Rank | File                           | Findings |
| ---- | ------------------------------ | -------- |
| 1    | `newupdater/worker.py`         | 2 (🟠🟠) |
| 2    | `auth/routes.py`               | 2 (🟠🟢) |
| 3    | `utils/routes_utils.py`        | 1 (🟠)   |
| 4    | `newupdater/route.py`          | 1 (🟠)   |
| 5    | `fixred.py`                    | 1 (🟠)   |
| 6    | `admin_routes/coordinators.py` | 1 (🟠)   |
| 7    | `admin/sidebar.py`             | 1 (🟡)   |

---

## Detailed Findings

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord`

**File**: `fixred.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Problem**:
Route file imports `UserTokenRecord` from `db.models`. Routes should interact with models only through services.

**Offending Code**:

```python
from ..db.models import UserTokenRecord
```

**How to Fix**:
Move the type annotation to use a protocol or service return type. If the type hint is needed only for `getattr(g, "_current_user")`, use `Any` or a typed service accessor.

**Move to**: Remove import; use `Any` or a service-layer helper.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord`

**File**: `newupdater/route.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Problem**:
Same pattern as `fixred.py` — imports `UserTokenRecord` directly for a type annotation on `g._current_user`.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
```

**How to Fix**:
Same as above — remove the model import and use `Any` or a service-layer type.

**Move to**: Remove import.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord`

**File**: `utils/routes_utils.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Problem**:
This utility file imports `UserTokenRecord` and uses it as a parameter type and accesses its attributes (`user.access_token`, `user.access_secret`, `user.user_id`, `user.username`) directly. This couples the utility layer to the ORM model.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
```

**How to Fix**:
Define a `TypedDict` or `Protocol` in the service layer for the auth payload shape, and have the service return that instead of the raw model.

**Move to**: Define auth payload type in `su_services/` or `shared/`.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord`

**File**: `newupdater/worker.py`
**Line(s)**: 19
**Violation**: V-R3 — Direct import of models in routes

**Problem**:
This file imports `UserTokenRecord` and uses it as a parameter type. It also accesses `user.access_token` and `user.access_secret` directly — reading ORM model attributes in what should be a route-layer file.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
```

**How to Fix**:
This entire file should be moved to `shared/` or `api_services/` (see V-R1 below). The model import is a symptom of misplaced code.

**Move to**: `shared/newupdater_service.py`

---

### [🟠 High] V-R1: Business logic / service code misplaced in `app_routes/`

**File**: `newupdater/worker.py`
**Line(s)**: 26–70 (entire function body)
**Violation**: V-R1 — Business logic in route functions

**Problem**:
`newupdater_one_title()` is a **service function** masquerading as a route utility. It:

-   Fetches page text via the MediaWiki API (`get_page_text`)
-   Runs a domain-specific text transformation (`work_on_text`)
-   Compares old/new text
-   Conditionally edits the page via the API (`edit_page`)
-   Constructs domain outcome objects (`UpdaterTextOutcome`)

This is 45 lines of orchestration/business logic with no request parsing or response building. It belongs in `shared/` or a dedicated service.

**Offending Code**:

```python
def newupdater_one_title(
    title: str,
    save: bool = False,
    summary: str = "Med updater.",
    user: UserTokenRecord | None = None,
) -> UpdaterTextOutcome:
    title = (title or "").strip()
    if not title:
        return UpdaterTextOutcome(kind="skipped", msg="Invalid title")
    if user is None:
        return UpdaterTextOutcome(kind="skipped", msg="No user")
    user_dict = {
        "access_token": user.access_token,
        "access_secret": user.access_secret,
    }
    site = get_user_site(user_dict)
    old_text = get_page_text(title, site)
    if not old_text or not old_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)
    try:
        new_text = work_on_text(title, old_text)
    except Exception:
        logger.exception("work_on_text failed for %s", title)
        raise
    if not new_text or not new_text.strip():
        return UpdaterTextOutcome(kind="notext", old_text=old_text)
    if new_text == old_text:
        return UpdaterTextOutcome(kind="skipped", msg="No changes")
    if save:
        result = edit_page(site, title, new_text, summary)
        if result.get("success"):
            return UpdaterTextOutcome(kind="saved", newrevid=result.get("newrevid", 0))
    return UpdaterTextOutcome(kind="changes", old_text=old_text, new_text=new_text)
```

**How to Fix**:
Move `newupdater_one_title()` to `shared/newupdater_service.py`. The route in `newupdater/route.py` should call it from there.

**Move to**: `shared/newupdater_service.py`

---

### [🟠 High] V-R1: Business logic in callback route

**File**: `auth/routes.py`
**Line(s)**: 122–229 (`callback()` function, ~107 lines)
**Violation**: V-R1 — Business logic in route functions

**Problem**:
The `callback()` function is **107 lines long** and contains extensive orchestration logic:

-   State token verification (lines 132–141)
-   Request token deserialization and validation (lines 145–158)
-   OAuth completion and identity extraction (lines 162–168)
-   Access token key/secret extraction with multiple fallback paths (lines 172–182)
-   User identifier extraction from identity dict with 4 fallback keys (line 186)
-   User credential upsert via `UserService.save_and_get_user` (lines 205–210)
-   Session setup and cookie construction (lines 218–228)

While some of this is request parsing, the OAuth completion, identity extraction, and credential upsert logic should be in a service.

**Offending Code** (trimmed):

```python
@bp_auth.get("/callback")
def callback() -> Response:
    # ~107 lines of OAuth orchestration
    ...
    access_token, identity = complete_login(request_token, query_string)
    ...
    user_identifier = identity.get("sub") or identity.get("id") or identity.get("central_id") or identity.get("user_id")
    ...
    user_record = UserService.save_and_get_user(...)
    ...
```

**How to Fix**:
Extract lines 162–210 into a service function like `complete_oauth_callback(request_token, query_string) -> UserTokenRecord`. The route should only handle request parsing, calling the service, and building the response.

**Move to**: `su_services/auth_service.py` or `auth/oauth.py`

---

### [🟠 High] V-R2: SQLAlchemy exception import in route file

**File**: `admin_routes/coordinators.py`
**Line(s)**: 16
**Violation**: V-R2 (borderline) — Direct ORM coupling in routes

**Problem**:
The file imports `sqlalchemy.exc.IntegrityError` and catches it directly in `_add_coordinator()` (line 55). While the actual DB call goes through `admin_service.add_coordinator()`, the route is handling ORM-level exceptions. This couples the route layer to SQLAlchemy's exception hierarchy.

**Offending Code**:

```python
from sqlalchemy.exc import IntegrityError
...
    except IntegrityError as exc:
        if "a foreign key constraint fails" in str(exc):
```

**How to Fix**:
The service layer (`admin_service.add_coordinator`) should catch `IntegrityError` and raise a domain-specific exception (e.g., `UserNotFoundError`). The route should only catch domain exceptions.

**Move to**: `db/services/admin_service.py`

---

### [🟡 Medium] V-X2: God module — `admin/sidebar.py`

**File**: `admin/sidebar.py`
**Line(s)**: 1–144
**Violation**: V-X2 — God module (144 lines, mixed responsibilities)

**Problem**:
This file combines:

-   A dataclass definition (`SidebarItem`)
-   HTML string generation via f-strings (`generate_list_item`, `create_side`)
-   Menu structure definitions
-   CSS/JS-aware responsive layout logic

While under the 300-line threshold, the file mixes data definitions, presentation logic (HTML generation), and navigation structure — responsibilities that belong in a Jinja template.

**Offending Code**:

```python
def generate_list_item(href, title, icon=None, target=None):
    icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""
    target_attr = "target='_blank'" if target else ""
    link = f"""
        <a {target_attr} class='link_nav rounded' href='{href}' title='{title}'...>
```

**How to Fix**:
Move the sidebar HTML generation to a Jinja macro or partial template (`templates/admin/sidebar.html`). The Python side should only provide the menu data structure.

**Move to**: `templates/admin/sidebar.html` (Jinja template)

---

### [🟢 Low] V-R5: Raw HTML generation in route helper

**File**: `admin/sidebar.py`
**Line(s)**: 30–41, 44–144
**Violation**: V-R5 — Response formatting that should be Jinja templates

**Problem**:
`generate_list_item()` and `create_side()` build HTML via f-strings with Bootstrap classes, icons, tooltips, and responsive breakpoints. This is exactly what Jinja templates are for.

**Offending Code**:

```python
link = f"""
    <a {target_attr} class='link_nav rounded' href='{href}' title='{title}'
       data-bs-toggle='tooltip' data-bs-placement='right'>
        {icon_tag}
        <span class='hide-on-collapse-inline'>{title}</span>
    </a>
"""
```

**How to Fix**:
Create `templates/admin/_sidebar.html` as a Jinja macro. Pass the `SidebarItem` list to the template and let Jinja render the HTML.

**Move to**: `templates/admin/_sidebar.html`

---

## Clean Files

The following files had **no violations** detected:

-   `__init__.py` — Blueprint registration only
-   `main/__init__.py` — Two trivial routes
-   `auth/__init__.py` — Empty
-   `auth/utils.py` — Clean auth decorators
-   `auth/cookie.py` — Pure crypto utility
-   `auth/oauth.py` — Clean OAuth handshake helper
-   `auth/rate_limit.py` — Clean rate limiter
-   `newupdater/__init__.py` — Empty
-   `admin/__init__.py` — Commented-out imports
-   `admin/routes.py` — Clean admin routes
-   `admin/admins_required.py` — Clean decorator
-   `admin_routes/__init__.py` — Re-export only
-   `utils/__init__.py` — Re-export only
-   `new_jobs.py` — Well-structured; delegates to services
-   `profile.py` — Clean; delegates to `get_user_jobs_stats`

---

## Architectural Recommendations

1. **Move `newupdater/worker.py` to `shared/`**: This file is a service, not a route utility. It imports API clients, model classes, and domain logic. Relocating it eliminates 2 violations immediately.

2. **Extract OAuth callback logic to a service**: The 107-line `callback()` in `auth/routes.py` should have its core logic (lines 162–210) extracted to `su_services/auth_service.py`. The route should become ~30 lines of request parsing + service call + response.

3. **Stop importing models in routes**: Four files import `UserTokenRecord` directly. Define a `Protocol` or `TypedDict` in `shared/` for the user shape, and have services return that instead of raw ORM objects.

4. **Move SQLAlchemy exception handling to services**: `admin_routes/coordinators.py` catching `IntegrityError` is a layer violation. Services should translate ORM exceptions into domain exceptions.

5. **Convert sidebar HTML generation to Jinja**: `admin/sidebar.py` builds 144 lines of HTML via f-strings. A Jinja template with macros would be more maintainable and testable.

---

## Appendix: Import Dependency Graph

```
app_routes/__init__.py
├── admin.routes
├── auth.routes
├── fixred
├── main
├── new_jobs
├── newupdater.route
└── profile

fixred ──────────────────────→ db.models (UserTokenRecord) ⚠️
                         ┌──→ shared.fixred_one
                         └──→ auth.utils

new_jobs ────────────────────→ db.services (active_coordinators, delete_job, get_job, list_jobs)
                         ┌──→ new_jobs.jobs_worker
                         ├──→ new_jobs.workers_list
                         ├──→ su_services
                         └──→ utils.routes_utils

profile ─────────────────────→ db.services (get_user_jobs_stats)

auth.routes ──────────────────→ db.services (delete_user_token)
                         ┌──→ su_services.users_service
                         ├──→ auth.cookie
                         ├──→ auth.oauth
                         ├──→ auth.rate_limit
                         └──→ auth.utils

auth.utils ───────────────────→ su_services.users_service
                         └──→ auth.cookie

newupdater.route ─────────────→ db.models (UserTokenRecord) ⚠️
                         └──→ newupdater.worker

newupdater.worker ────────────→ db.models (UserTokenRecord) ⚠️
                         ┌──→ api_services.clients.wiki_client
                         ├──→ api_services.pages_api
                         └──→ shared.new_updater

admin.routes ─────────────────→ db.services (list_users)
                         ┌──→ admin_routes.coordinators
                         ├──→ admin.admins_required
                         └──→ admin.sidebar

admin.admins_required ────────→ db.services (active_coordinators)

admin_routes.coordinators ────→ db.services.admin_service
                         └──→ sqlalchemy.exc (IntegrityError) ⚠️

utils.routes_utils ───────────→ db.models (UserTokenRecord) ⚠️
                         ┌──→ db.services.admin_service
                         └──→ new_jobs.workers_list
```

⚠️ = cross-layer violation

---

_Generated by flask-soc-audit skill_
