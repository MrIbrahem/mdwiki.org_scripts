# Separation of Concerns Audit Report — `app_routes/`

**Project**: mdwiki.org Flask app
**Date**: 2026-05-31
**Auditor**: opencode (flask-soc-audit skill)
**Files Scanned**: 21

---

## Fixes Applied (2026-05-31)

All 🟠 High violations in `app_routes/` have been resolved:

| File | Violation | Fix |
|------|-----------|-----|
| `fixred.py` | V-R3 (model import) | Removed `from ..db.models import UserTokenRecord` |
| `newupdater/route.py` | V-R3 (model import) | Removed `from ...db.models import UserTokenRecord` |
| `utils/routes_utils.py` | V-R3 (model import) | Removed import; uses `CurrentUser.to_auth_payload()` |
| `newupdater/worker.py` | V-R3 + V-R1 (misplaced service) | Moved to `shared/newupdater_service.py` |
| `auth/routes.py` | V-R1 (107-line callback) | Extracted `complete_oauth_callback()` to `su_services/auth_service.py`; callback now 51 lines |
| `admin_routes/coordinators.py` | V-R2 (IntegrityError import) | Moved to `admin_service.add_coordinator()` with `UserNotFoundError` |

### Current Finding Counts

| Severity    | Count |
| ----------- | ----- |
| 🔴 Critical | 0     |
| 🟠 High     | 0     |
| 🟡 Medium   | 1     |
| 🟢 Low      | 1     |
| **Total**   | **2** |

Only `admin/sidebar.py` remains (🟡 HTML via f-strings — low priority).

---

## Original Audit (pre-fixes)

### [🟠 High] V-R3: Direct model import — `UserTokenRecord` ✅ FIXED

**File**: `fixred.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Fix**: Removed `from ..db.models import UserTokenRecord`; type annotation removed.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord` ✅ FIXED

**File**: `newupdater/route.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Fix**: Removed `from ...db.models import UserTokenRecord`; type annotation removed.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord` ✅ FIXED

**File**: `utils/routes_utils.py`
**Line(s)**: 9
**Violation**: V-R3 — Direct import of models in routes

**Fix**: Removed import; `load_auth_payload()` now uses `CurrentUser.to_auth_payload()`.

---

### [🟠 High] V-R3: Direct model import — `UserTokenRecord` ✅ FIXED

**File**: `newupdater/worker.py`
**Line(s)**: 19
**Violation**: V-R3 — Direct import of models in routes

**Fix**: Entire file moved to `shared/newupdater_service.py`; uses `CurrentUser` type.

---

### [🟠 High] V-R1: Business logic / service code misplaced in `app_routes/` ✅ FIXED

**File**: `newupdater/worker.py`
**Line(s)**: 26–70 (entire function body)
**Violation**: V-R1 — Business logic in route functions

**Fix**: Moved to `shared/newupdater_service.py`. Route now imports from there.

---

### [🟠 High] V-R1: Business logic in callback route ✅ FIXED

**File**: `auth/routes.py`
**Line(s)**: 122–229 (`callback()` function, ~107 lines)
**Violation**: V-R1 — Business logic in route functions

**Fix**: Created `su_services/auth_service.py` with `complete_oauth_callback()`. Callback reduced to 51 lines — only HTTP concerns remain.

---

### [🟠 High] V-R2: SQLAlchemy exception import in route file ✅ FIXED

**File**: `admin_routes/coordinators.py`
**Line(s)**: 16
**Violation**: V-R2 (borderline) — Direct ORM coupling in routes

**Fix**: `IntegrityError` handling moved to `admin_service.add_coordinator()`. Route now catches domain-specific `UserNotFoundError`.

---

### [🟡 Medium] V-X2: God module — `admin/sidebar.py`

**File**: `admin/sidebar.py`
**Line(s)**: 1–144
**Violation**: V-X2 — God module (144 lines, mixed responsibilities)

**Problem**:
This file combines a dataclass definition, HTML string generation via f-strings, menu structure definitions, and responsive layout logic.

**How to Fix**:
Move the sidebar HTML generation to a Jinja macro or partial template. The Python side should only provide the menu data structure.

---

### [🟢 Low] V-R5: Raw HTML generation in route helper

**File**: `admin/sidebar.py`
**Line(s)**: 30–41, 44–144
**Violation**: V-R5 — Response formatting that should be Jinja templates

**Problem**:
`generate_list_item()` and `create_side()` build HTML via f-strings with Bootstrap classes, icons, tooltips, and responsive breakpoints.

**How to Fix**:
Create `templates/admin/_sidebar.html` as a Jinja macro. Pass the `SidebarItem` list to the template and let Jinja render the HTML.

---

## Clean Files

The following files had **no violations** detected:

-   `__init__.py` — Blueprint registration only
-   `main/__init__.py` — Two trivial routes
-   `auth/__init__.py` — Empty
-   `auth/routes.py` — Clean after refactor
-   `auth/utils.py` — Clean auth decorators
-   `auth/cookie.py` — Pure crypto utility
-   `auth/oauth.py` — Clean OAuth handshake helper
-   `auth/rate_limit.py` — Clean rate limiter
-   `newupdater/__init__.py` — Empty
-   `newupdater/route.py` — Clean after refactor
-   `admin/__init__.py` — Commented-out imports
-   `admin/routes.py` — Clean admin routes
-   `admin/admins_required.py` — Clean decorator
-   `admin_routes/__init__.py` — Re-export only
-   `admin_routes/coordinators.py` — Clean after refactor
-   `utils/__init__.py` — Re-export only
-   `utils/routes_utils.py` — Clean after refactor
-   `fixred.py` — Clean after refactor
-   `new_jobs.py` — Well-structured; delegates to services
-   `profile.py` — Clean; delegates to `get_user_jobs_stats`

---

_Generated by flask-soc-audit skill_
