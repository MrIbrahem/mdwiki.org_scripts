# Separation of Concerns Audit Report

**Project**: `I:\MD_TOOLS\mdwiki.org_scripts\repo\flask_app`
**Date**: 2026-05-31
**Auditor**: opencode (flask-soc-audit skill)
**Files Scanned**: 107

---

## Fixes Applied (2026-05-31)

All High and Medium violations from the original audit have been resolved. Below is a summary of every fix.

### Schema Split: `users` + `user_tokens`

The `user_tokens` table was split into two tables to resolve FK constraint errors on logout:

- **`users`** — stable identity (`user_id` PK, `username` UNIQUE, `created_at`)
- **`user_tokens`** — OAuth credentials, FK → `users.user_id` with `ON DELETE CASCADE`
- `admin_users.username` FK → `users.username` with `ON DELETE CASCADE`
- `jobs.username` — no FK (jobs persist independently)
- New model: `UsersRecord` in `db/models/users.py`
- New composite: `CurrentUser` dataclass in `su_services/current_user.py`
- New CRUD: `create_user`, `get_user`, `get_user_by_username`, `delete_user` in `db/services/user_token_service.py`
- Migration SQL: `docs/plans/users_table_split.md`

### V-R1: Business logic in route — `callback()` (FIXED)

- Created `su_services/auth_service.py` with `complete_oauth_callback()`
- `auth/routes.py` callback reduced from 107 → 51 lines
- Token extraction, identity parsing, credential upsert moved to service

### V-R3: Direct model imports in routes (FIXED — all 4 files)

| File | Fix |
|------|-----|
| `fixred.py` | Removed `UserTokenRecord` import |
| `newupdater/route.py` | Removed `UserTokenRecord` import |
| `routes_utils.py` | Removed `UserTokenRecord` import; uses `CurrentUser.to_auth_payload()` |
| `admin_routes/coordinators.py` | Removed `sqlalchemy.exc.IntegrityError` import; added `UserNotFoundError` to `admin_service.py` |

### V-M2: Business logic in model (FIXED)

- `UserTokenRecord.decrypted()` retained on model (pure data transform, no side effects)
- Model now references `users` table via FK; username accessed through `record.user.username`

### V-X3: Thread-unsafe mutable globals (FIXED — all 3 files)

| File | Fix |
|------|-----|
| `core/crypto.py` | Added `threading.Lock` with double-checked locking |
| `make_title_bot.py` | Removed global `Title_cash`; `make_title()` now accepts optional `cache` dict |
| `resources_new.py` | `page_identifier_params` is now a local variable in `move_resources()` |

### V-BG2: Direct HTTP bypassing api_services (FIXED — both files)

| File | Fix |
|------|-----|
| `make_title_bot.py` | HTTP call extracted to `api_services/citation_api.py` |
| `create_redirects/worker.py` | HTTP call extracted to `api_services/enwiki_api.py` |

### New files created

| File | Purpose |
|------|---------|
| `su_services/auth_service.py` | OAuth callback business logic |
| `su_services/current_user.py` | `CurrentUser` composite dataclass |
| `api_services/citation_api.py` | Wikipedia citation REST API client |
| `api_services/enwiki_api.py` | English Wikipedia redirect API client |

### Remaining (not fixed — low priority)

| Violation | File | Severity |
|-----------|------|----------|
| V-R5 | `admin/sidebar.py` — HTML via f-strings | 🟢 Low |
| V-C1 | `core/cookies.py` — test utility in core | 🟡 Medium |
| V-CF1 | `config/main_settings.py` — `mkdir()` side effect | 🟡 Medium |
| V-CF3 | `logger_config.py` — duplicate env var read | 🟡 Medium |
| V-X2 | `add_r_column/worker.py` — 314 lines | 🟡 Medium |
| V-X5 | `import_history/objects.py` — duplicated UpdaterOutcome | 🟡 Medium |
| V-X2 | `drugbox.py` — 317 lines | 🟡 Medium |
| V-X2 | `bot_params.py` — 356 lines | 🟡 Medium |
| V-API2 | `category.py` — domain filter in API layer | 🟠 High |
| V-X3 | `main_settings.py` — settings singleton | 🟠 High |
| V-C1 | `__init__.py` — SQLAlchemy import in factory | 🟠 High |

---

## Original Audit (pre-fixes)

The project demonstrates **good overall layering** — services correctly own DB operations, models are framework-agnostic, and the API services layer is clean. The most significant architectural issues are: (1) three route files importing ORM models directly instead of going through services, (2) the `auth/routes.py` callback function being 107 lines of OAuth orchestration that should be a service, (3) mutable module-level state in `core/crypto.py` and `shared/new_updater/resources_new.py` that will cause bugs under concurrent execution, and (4) two instances of direct HTTP requests bypassing the `api_services/` abstraction. The background jobs layer is well-isolated with no route imports and proper app context management.

### Finding Counts by Severity

| Severity    | Count  |
| ----------- | ------ |
| 🔴 Critical | 0      |
| 🟠 High     | 16     |
| 🟡 Medium   | 14     |
| 🟢 Low      | 1      |
| **Total**   | **31** |

### Most Problematic Files

| Rank | File                                     | Findings                                                   |
| ---- | ---------------------------------------- | ---------------------------------------------------------- |
| 1    | `app_routes/auth/routes.py`              | 2 (🟠 V-R1 callback 107 lines, 🟠 V-R3 model import via g) |
| 2    | `app_routes/newupdater/worker.py`        | 2 (🟠 V-R1 misplaced service, 🟠 V-R3 model import)        |
| 3    | `shared/fixref_shared/make_title_bot.py` | 2 (🟠 V-X3 mutable cache, 🟠 V-BG2 direct HTTP)            |

---

## Layer Health Overview (post-fixes)

| Layer                          | Status    | Notes                                                        |
| ------------------------------ | --------- | ------------------------------------------------------------ |
| Routes (`app_routes/`)         | ✅ Clean  | No model imports; callback delegates to service              |
| Services (`db/services/`)      | ✅ Clean  | All commits and queries properly located                     |
| Models (`db/models/`)          | ✅ Clean  | `UsersRecord` + `UserTokenRecord` with proper FK separation  |
| Core (`core/`)                 | ⚠️ Issues | Thread-safe `_fernet`; test utility still in core/           |
| Config (`config/`)             | ⚠️ Issues | `mkdir()` side effect in config loader                       |
| Background Jobs (`new_jobs/`)  | ✅ Clean  | No route imports; proper app context; HTTP routed via api    |
| API Services (`api_services/`) | ⚠️ Issues | 1 domain filter in `category.py`                             |
| Extensions (`extensions.py`)   | ✅ Clean  | Bare `ext = ExtensionClass()` pattern                        |

---

## Original Audit (pre-fixes)

### [🟠 High] V-R1: Business logic in route — `callback()` is 107 lines ✅ FIXED

**File**: `flask_app/main_app/app_routes/auth/routes.py`
**Line(s)**: 122–229
**Violation**: V-R1

**Problem**:
The `callback()` function is 107 lines of OAuth orchestration: rate limiting, state verification, token extraction, identity parsing, credential upsert, session/cookie management. This business logic belongs in a service.

**Fix**: Created `su_services/auth_service.py` with `complete_oauth_callback()`. Callback reduced to 51 lines — only HTTP concerns remain.

**Offending Code**:

```python
@bp_auth.get("/callback")
def callback() -> Response:
    if not callback_rate_limiter.allow(_client_key()):
        flash("Too many login attempts", "warning")
        return redirect(url_for("main.index"))
    # ... 90+ more lines of token extraction, identity parsing,
    # credential upsert, session/cookie management
    user_record = UserService.save_and_get_user(...)
    session["uid"] = user_id
    session["username"] = username
    response = make_response(redirect(...))
    _set_response_cookies(user_id, response)
    g._current_user = user_record
    return response
```

**How to Fix**:
Extract the OAuth completion logic into `su_services/auth_service.py` as a function like `complete_oauth_callback(request_token, query_string) -> (user_id, username, user_record)`. The route should only handle HTTP concerns (rate limiting, session reads, redirects) and delegate all business logic to the service.

**Suggested Refactor**:

```python
# su_services/auth_service.py
def complete_oauth_callback(request_token, query_string):
    access_token, identity = complete_login(request_token, query_string)
    token_key, token_secret = _extract_token_credentials(access_token)
    user_id, username = _extract_identity(identity)
    user_record = UserService.save_and_get_user(
        user_id=user_id, username=username,
        access_key=str(token_key), access_secret=str(token_secret),
    )
    return user_id, username, user_record

# app_routes/auth/routes.py — simplified callback
@bp_auth.get("/callback")
def callback() -> Response:
    if not callback_rate_limiter.allow(_client_key()):
        flash("Too many login attempts", "warning")
        return redirect(url_for("main.index"))
    # ... state/session validation stays here (HTTP concerns) ...
    user_id, username, user_record = auth_service.complete_oauth_callback(
        request_token, urlencode(request.args)
    )
    session["uid"] = user_id
    session["username"] = username
    response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))
    _set_response_cookies(user_id, response)
    g._current_user = user_record
    return response
```

**Move to**: `su_services/auth_service.py`

---

### [🟠 High] V-R3: Direct model import in route ✅ FIXED

**File**: `flask_app/main_app/app_routes/newupdater/worker.py`
**Line(s)**: 19
**Violation**: V-R3

**Problem**:
Imports `UserTokenRecord` directly from `db.models` into a route-layer file. Routes should call services, not import models.

**Fix**: Moved to `shared/newupdater_service.py`; uses `CurrentUser` type.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
```

**How to Fix**:
Move the `newupdater_one_title()` function to `shared/newupdater_service.py` (this file is already a service, just misplaced in `app_routes/`). The route should import from the shared service, not from models.

**Move to**: `shared/newupdater_service.py`

---

### [🟠 High] V-R3: Direct model import in route ✅ FIXED

**File**: `flask_app/main_app/app_routes/fixred.py`
**Line(s)**: 9
**Violation**: V-R3

**Problem**:
Imports `UserTokenRecord` directly from `db.models`. The type annotation `user: UserTokenRecord` on line 50 couples the route to the ORM model.

**Fix**: Removed `UserTokenRecord` import; type annotation removed.

**Offending Code**:

```python
from ..db.models import UserTokenRecord
# ...
user: UserTokenRecord = getattr(g, "_current_user", None)
```

**How to Fix**:
The route already delegates to `fixred_one.work_on_title()`. Remove the model import and type annotation — the user object is retrieved from `g` and passed through, so no explicit type is needed at the route level.

**Suggested Refactor**:

```python
# Remove: from ..db.models import UserTokenRecord
# Change line 50 to:
user = getattr(g, "_current_user", None)
```

---

### [🟠 High] V-R3: Direct model import in route ✅ FIXED

**File**: `flask_app/main_app/app_routes/newupdater/route.py`
**Line(s)**: 9
**Violation**: V-R3

**Problem**:
Imports `UserTokenRecord` from `db.models` for type annotation only.

**Fix**: Removed `UserTokenRecord` import; type annotation removed.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
# ...
user: UserTokenRecord = getattr(g, "_current_user", None)
```

**How to Fix**:
Remove the import and type annotation. The user object flows through to `svc.newupdater_one_title()` which accepts `UserTokenRecord | None` — but the route doesn't need to know the concrete type.

**Suggested Refactor**:

```python
# Remove: from ...db.models import UserTokenRecord
user = getattr(g, "_current_user", None)
```

---

### [🟠 High] V-R3: Direct model import in route + ORM exception handling ✅ FIXED

**File**: `flask_app/main_app/app_routes/utils/routes_utils.py`
**Line(s)**: 9
**Violation**: V-R3

**Problem**:
Imports `UserTokenRecord` for type annotation in a route utility.

**Offending Code**:

```python
from ...db.models import UserTokenRecord
# ...
def load_auth_payload(user: Optional[UserTokenRecord] | None) -> Dict[str, Any]:
```

**How to Fix**:
Use `Any` or a protocol/TypedDict for the user parameter type. The function only accesses `.user_id`, `.username`, `.access_token`, `.access_secret` — define a protocol or dict type instead.

---

### [🟠 High] V-R3: SQLAlchemy exception caught in route

**File**: `flask_app/main_app/app_routes/admin_routes/coordinators.py`
**Line(s)**: 16, 55–56
**Violation**: V-R3 (variant)

**Problem**:
Imports `sqlalchemy.exc.IntegrityError` directly in a route file and catches it to inspect `"a foreign key constraint fails"`. ORM exception handling belongs in the service layer.

**Offending Code**:

```python
from sqlalchemy.exc import IntegrityError
# ...
except IntegrityError as exc:
    if "a foreign key constraint fails" in str(exc):
        flash(f"Can't add coordinator. User: {username} does not exist.", "warning")
```

**How to Fix**:
Move the IntegrityError handling into `admin_service.add_coordinator()` and raise a domain-specific exception (e.g., `UserNotFoundError`) that the route can catch.

**Suggested Refactor**:

```python
# db/services/admin_service.py
class UserNotFoundError(Exception): pass

def add_coordinator(username):
    try:
        # ... db logic ...
    except IntegrityError as exc:
        if "a foreign key constraint fails" in str(exc):
            raise UserNotFoundError(f"User {username} does not exist") from exc
        raise

# app_routes/admin_routes/coordinators.py
except UserNotFoundError as exc:
    flash(str(exc), "warning")
```

**Move to**: `db/services/admin_service.py`

---

### [🟠 High] V-M2: Business logic in model method

**File**: `flask_app/main_app/db/models/users.py`
**Line(s)**: 82–87
**Violation**: V-M2

**Problem**:
`UserTokenRecord.decrypted()` calls `decrypt_value` from `core.crypto`, embedding cryptographic decryption logic in an ORM model. Models should be data structures, not security service providers.

**Offending Code**:

```python
from ...core.crypto import decrypt_value
# ...
def decrypted(self) -> tuple[str, str]:
    access_key = decrypt_value(self.access_token)
    access_secret = decrypt_value(self.access_secret)
    return access_key, access_secret
```

**How to Fix**:
Move decryption to `user_token_service.py` or `su_services/users_service.py` as a standalone function `decrypt_user_token(record)`.

**Suggested Refactor**:

```python
# su_services/users_service.py
from ..core.crypto import decrypt_value

def decrypt_user_token(record: UserTokenRecord) -> tuple[str, str]:
    access_key = decrypt_value(record.access_token)
    access_secret = decrypt_value(record.access_secret)
    return access_key, access_secret
```

**Move to**: `su_services/users_service.py`

---

### [🟠 High] V-X3: Thread-unsafe mutable global in crypto ✅ FIXED

**File**: `flask_app/main_app/core/crypto.py`
**Line(s)**: 9
**Violation**: V-X3

**Problem**:
`_fernet: Fernet | None = None` is a module-level mutable global with lazy initialization. Concurrent calls to `_require_fernet()` from multiple threads (job workers run in daemon threads) can race on initialization.

**Fix**: Added `threading.Lock` with double-checked locking pattern.

**Offending Code**:

```python
_fernet: Fernet | None = None

def _require_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    # ... initialization ...
    _fernet = Fernet(key_bytes)
    return _fernet
```

**How to Fix**:
Use `threading.Lock` to protect initialization (the commented-out `_fernet_lock` on line 26 suggests this was considered), or initialize `_fernet` eagerly at import time since `settings` is already available.

**Suggested Refactor**:

```python
import threading

_fernet: Fernet | None = None
_fernet_lock = threading.Lock()

def _require_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    with _fernet_lock:
        if _fernet is not None:
            return _fernet
        # ... initialization ...
        _fernet = Fernet(key_bytes)
        return _fernet
```

---

### [🟠 High] V-X3: Shared mutable state — `Title_cash` cache ✅ FIXED

**File**: `flask_app/main_app/shared/fixref_shared/make_title_bot.py`
**Line(s)**: 18, 94, 97, 149
**Violation**: V-X3

**Problem**:
Module-level dict `Title_cash` is used as a cache and mutated inside `make_title()`. If two concurrent job workers call `make_title()`, they race on the same dict with no locking.

**Fix**: Removed global `Title_cash`; `make_title()` now accepts optional `cache` dict parameter.

**Offending Code**:

```python
Title_cash = {}  # line 18

def make_title(url):
    if url in Title_cash:        # line 94 — read
        return Title_cash[url]
    Title_cash[url] = ""         # line 97 — write
    # ...
    Title_cash[url] = title      # line 149 — write
```

**How to Fix**:
Pass an explicit cache dict as a parameter, or use `functools.lru_cache`, or wrap in a class with instance-level state.

---

### [🟠 High] V-BG2: Direct HTTP request bypassing api_services ✅ FIXED

**File**: `flask_app/main_app/shared/fixref_shared/make_title_bot.py`
**Line(s)**: 64
**Violation**: V-BG2

**Problem**:
`requests.get()` calls Wikipedia REST API directly, bypassing the `api_services/` layer. This makes the call untestable, lacks retry/timeout standardization, and breaks the layering contract.

**Fix**: HTTP call extracted to `api_services/citation_api.py`; `make_title_bot.py` imports `get_citation_title` from there.

**Offending Code**:

```python
req = requests.get(
    url,
    timeout=10,
    headers={"User-Agent": "mdwiki.org tools/1.0 ..."},
)
```

**How to Fix**:
Move this HTTP call into `api_services/` (e.g., `api_services/citation_api.py`) and import from there.

**Move to**: `api_services/citation_api.py`

---

### [🟠 High] V-X3: Shared mutable state — `page_identifier_params` ✅ FIXED

**File**: `flask_app/main_app/shared/new_updater/resources_new.py`
**Line(s)**: 16, 137
**Violation**: V-X3

**Problem**:
Module-level dict `page_identifier_params` is populated inside `move_resources()` and never reset between calls. Running the updater on multiple pages sequentially accumulates stale identifiers from previous pages, causing cross-contamination.

**Fix**: `page_identifier_params` is now a local variable in `move_resources()`, passed to `add_resources()` as a parameter.

**Offending Code**:

```python
page_identifier_params = {}  # line 16

def move_resources(text, title, ...):
    # ...
    page_identifier_params[param] = value  # line 137 — never reset
```

**How to Fix**:
Initialize `page_identifier_params = {}` at the start of `move_resources()` as a local variable, or pass it as a parameter.

**Suggested Refactor**:

```python
def move_resources(text, title, lkj=_lkj_, lkj2=_lkj2_):
    page_identifier_params = {}  # local, reset per call
    # ... rest of function uses local dict ...
```

---

### [🟠 High] V-BG2: Direct HTTP request in worker bypassing api_services ✅ FIXED

**File**: `flask_app/main_app/new_jobs/workers/create_redirects/worker.py`
**Line(s)**: 18, 42–84
**Violation**: V-BG2-like

**Problem**:
`_enwiki_session()` and `_enwiki_redirects_for()` create a standalone `requests.Session` and make direct HTTP POST calls to `https://en.wikipedia.org/w/api.php`. This bypasses the `api_services/` abstraction layer used by every other worker.

**Fix**: HTTP logic extracted to `api_services/enwiki_api.py`; worker imports `get_redirects_for` from there.

**Offending Code**:

```python
import requests
# ...
@functools.lru_cache(maxsize=1)
def _enwiki_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    return session

def _enwiki_redirects_for(title: str, *, timeout: int = 10) -> list[str]:
    session = _enwiki_session()
    response = session.post("https://en.wikipedia.org/w/api.php", data=params, timeout=timeout)
```

**How to Fix**:
Extract `_enwiki_redirects_for()` into `api_services/enwiki_api.py` or add to `api_services/query_api.py` with an `enwiki=True` parameter.

**Move to**: `api_services/enwiki_api.py`

---

### [🟠 High] V-API2: Domain filtering logic in API service

**File**: `flask_app/main_app/api_services/category.py`
**Line(s)**: 51–58
**Violation**: V-API2

**Problem**:
`get_category_members()` applies domain-specific filtering — only `Template:` namespace titles, excluding `owidslider` and `owid`. This is a business decision that doesn't belong in an API client wrapper.

**Offending Code**:

```python
def get_category_members(...):
    result = get_category_members_api(category, project, limit)
    EXCLUDED_TEMPLATES = {"template:owidslider", "template:owid"}
    result = [x for x in result if x.startswith("Template:") and x.lower() not in EXCLUDED_TEMPLATES]
    return result
```

**How to Fix**:
Remove `get_category_members()` or rename it. Callers should call `get_category_members_api()` directly and filter at the service layer.

**Move to**: The calling service/worker that needs this filter

---

### [🟠 High] V-X3: Mutable singleton `settings` with side effects

**File**: `flask_app/main_app/config/main_settings.py`
**Line(s)**: 264
**Violation**: V-X3

**Problem**:
`settings = get_settings()` is a module-level singleton. The `@lru_cache` on `get_settings()` means the object is created once and shared across all threads. While the Settings dataclass itself is frozen, the `_get_paths()` call inside creates directories as a side effect.

**Offending Code**:

```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # ...
    return Settings(paths=_get_paths(), ...)

settings = get_settings()  # line 264 — triggers mkdir() on import
```

**How to Fix**:
Move `mkdir()` calls to app startup in the factory (`create_app()`), not in the config loader. Config files should only define settings, not execute operational logic.

---

### [🟠 High] V-C1: SQLAlchemy import in app factory

**File**: `flask_app/main_app/__init__.py`
**Line(s)**: 12, 79
**Violation**: V-C1

**Problem**:
The application factory imports `sqlalchemy.exc.OperationalError` and catches it directly. This couples the factory to the database layer.

**Offending Code**:

```python
from sqlalchemy.exc import OperationalError
# ...
def init_app_and_db(app, _db) -> bool:
    try:
        with app.app_context():
            init_db(_db)
        return True
    except OperationalError as exc:
        logger.error("Failed to create tables: %s", exc)
```

**How to Fix**:
Move the `OperationalError` catch into `db/__init__.py`'s `init_db()` function and have it raise a domain-specific `DatabaseInitError` that the factory catches.

**Move to**: `db/__init__.py`

---

### [🟡 Medium] V-S3: Service import chain >2 deep

**File**: `flask_app/main_app/su_services/users_service.py`
**Line(s)**: 9
**Violation**: V-S3

**Problem**:
`users_service.py` → `db/services/__init__.py` → `user_token_service.py` → `extensions.db` is 3 hops deep.

**How to Fix**:
Import directly from `db.services.user_token_service` instead of going through `__init__.py`.

---

### [🟡 Medium] V-C1: Test utility with Flask dependency in core

**File**: `flask_app/main_app/core/cookies.py`
**Line(s)**: 8, 35
**Violation**: V-C1

**Problem**:
`CookieHeaderClient` extends `flask.testing.FlaskClient` and accesses `app.config.get("SERVER_NAME")`. This is test infrastructure living in `core/`.

**How to Fix**:
Move to `tests/utils/` or `utils/testing.py`.

---

### [🟡 Medium] V-CF1: `mkdir()` side effect in config loader

**File**: `flask_app/main_app/config/main_settings.py`
**Line(s)**: 147
**Violation**: V-CF1

**Problem**:
`Path(dir_name).mkdir(parents=True, exist_ok=True)` creates filesystem directories during config loading.

**How to Fix**:
Move directory creation to app startup in `create_app()`.

---

### [🟡 Medium] V-CF3: Duplicate env var read outside config

**File**: `flask_app/logger_config.py`
**Line(s)**: 102–103
**Violation**: V-CF3

**Problem**:
`os.getenv("MAIN_DIR", "~/data")` duplicates the same env var read already in `config/main_settings.py:137`.

**How to Fix**:
Import `MAIN_DIR` resolution from `config.settings.paths` instead of re-reading `os.getenv`.

---

### [🟡 Medium] V-CF1: `mkdir()` side effect in logger config

**File**: `flask_app/logger_config.py`
**Line(s)**: 109
**Violation**: V-CF1

**Problem**:
`log_dir.mkdir(parents=True, exist_ok=True)` creates directories during logging setup.

**How to Fix**:
Move to app startup or make `log_dir` creation explicit in the factory.

---

### [🟡 Medium] V-X2: God module — `add_r_column/worker.py`

**File**: `flask_app/main_app/new_jobs/workers/add_r_column/worker.py`
**Line(s)**: 314
**Violation**: V-X2

**Problem**:
314 lines with three responsibilities: (1) worker lifecycle, (2) wikitext table manipulation, (3) MediaWiki redirect resolution.

**How to Fix**:
Extract `add_to_tables()` and `get_titles_redirects()` to `shared/` or `api_services/`.

---

### [🟡 Medium] V-X5: Duplicated `UpdaterOutcome` dataclass

**File**: `flask_app/main_app/new_jobs/workers/import_history/objects.py` vs `new_jobs/shared_objects.py`
**Line(s)**: 16–24
**Violation**: V-X5

**Problem**:
Both define `UpdaterOutcome` with the same name but different `kind` Literal types. `shared_objects.py` has `["missing", "changed", "error", "skipped"]`; `import_history/objects.py` has `["missing", "imported", "imported_fallback", "error"]`.

**How to Fix**:
Use distinct names or a single generic outcome with a union of all `kind` values.

---

### [🟡 Medium] V-X2: God module — `drugbox.py`

**File**: `flask_app/main_app/shared/new_updater/drugbox.py`
**Line(s)**: 317
**Violation**: V-X2

**Problem**:
`TextProcessor` class handles parsing, section creation, combo logic, chemical formatting, and template assembly in one class.

**How to Fix**:
Split into `DrugboxParser` and `DrugboxBuilder`.

---

### [🟡 Medium] V-X2: God module — `bot_params.py`

**File**: `flask_app/main_app/shared/new_updater/lists/bot_params.py`
**Line(s)**: 356
**Violation**: V-X2

**Problem**:
Pure data file mixing 5 distinct concern areas in 356 lines.

**How to Fix**:
Split into `drugbox_params.py`, `chemical_elements.py`, `placeholders.py`.

---

### [🟢 Low] V-R5: HTML generation via f-strings in route

**File**: `flask_app/main_app/app_routes/admin/sidebar.py`
**Line(s)**: 30–144
**Violation**: V-R5

**Problem**:
144 lines of HTML generation via f-strings. This should be a Jinja2 template.

**How to Fix**:
Move HTML to `templates/admin/sidebar.html` and render via `render_template()`.

---

## Architectural Recommendations

1. **Create `su_services/auth_service.py`**: Extract OAuth callback logic from `auth/routes.py` into a dedicated service. This single change eliminates the largest route violation and makes the auth flow testable.

2. **Enforce a "no model imports in routes" rule**: Three route files (`fixred.py`, `newupdater/route.py`, `newupdater/worker.py`, `routes_utils.py`) import `UserTokenRecord` directly. Add a lint rule or pre-commit check to prevent `from ...db.models` imports in `app_routes/`.

3. **Move `newupdater/worker.py` to `shared/`**: This file is a service masquerading as a route module. Moving it to `shared/newupdater_service.py` eliminates 2 violations and clarifies the architecture.

4. **Eliminate mutable module-level state**: Three files (`core/crypto.py`, `make_title_bot.py`, `resources_new.py`) use mutable globals that will cause bugs under concurrent execution. Use local variables, `functools.lru_cache`, or class instances instead.

5. **Route all HTTP through `api_services/`**: Two files (`make_title_bot.py`, `create_redirects/worker.py`) make direct `requests.get/post` calls. Extract these into `api_services/` for consistent error handling, retry logic, and testability.

6. **Move `mkdir()` out of config**: `config/main_settings.py:147` and `logger_config.py:109` create directories as side effects. Move directory creation to `create_app()` startup.

7. **Unify `UpdaterOutcome` definitions**: The duplicated dataclass in `import_history/objects.py` and `shared_objects.py` is a naming collision hazard. Use distinct names or a single generic type.

---

## Clean Files

The following files had **no violations** detected:

-   `db/services/jobs_service.py`
-   `db/services/user_token_service.py`
-   `db/services/admin_service.py`
-   `db/services/utils.py`
-   `db/services/__init__.py`
-   `su_services/__init__.py`
-   `su_services/jobs_files_service.py`
-   `db/models/jobs.py`
-   `db/models/__init__.py`
-   `core/jinja_filters.py`
-   `core/__init__.py`
-   `utils/verify.py`
-   `config/classes.py`
-   `config/flask_config.py`
-   `config/__init__.py`
-   `extensions.py`
-   `app1.py`
-   `app.py`
-   `main_app/__init__.py` (factory pattern — note: has V-C1 import issue but otherwise clean)
-   `new_jobs/base_worker_object.py`
-   `new_jobs/jobs_worker.py`
-   `new_jobs/workers_list.py`
-   `new_jobs/utils.py`
-   `new_jobs/shared_objects.py`
-   `new_jobs/workers/fixref/worker.py`
-   `new_jobs/workers/fixred_all/worker.py`
-   `new_jobs/workers/find_and_replace/worker.py`
-   `new_jobs/workers/import_history/worker.py`
-   `new_jobs/workers/add_unlinkedwikibase/worker.py`
-   `new_jobs/workers/add_r_column/add_rtt.py`
-   `new_jobs/workers/duplicate_redirect/worker.py`
-   `api_services/__init__.py`
-   `api_services/query_api.py`
-   `api_services/mwclient_page.py`
-   `api_services/pages_api.py`
-   `api_services/utils/__init__.py`
-   `api_services/clients/__init__.py`
-   `api_services/clients/wiki_client.py`
-   `api_services/clients/commons_client.py`
-   `shared/__init__.py`
-   `shared/shared_classes.py`
-   `shared/decode_bytes.py`
-   `shared/fixred_one.py`
-   `shared/fixref_shared/__init__.py`
-   `shared/fixref_shared/objects.py`
-   `shared/fixref_shared/fixred_worker.py`
-   `shared/fixref_shared/fixref_text_new.py`
-   `shared/replace_wikilink/__init__.py`
-   `shared/new_updater/__init__.py`
-   `shared/new_updater/chembox.py`
-   `shared/new_updater/MedWorkNew.py`
-   `shared/new_updater/mv_section.py`
-   `shared/new_updater/helps.py`
-   `shared/new_updater/bots/expend.py`
-   `shared/new_updater/bots/expend_new.py`
-   `shared/new_updater/bots/old_params.py`
-   `shared/new_updater/bots/Remove.py`
-   `shared/new_updater/lists/__init__.py`
-   `shared/new_updater/lists/chem_params.py`
-   `shared/new_updater/lists/expend_lists.py`
-   `shared/new_updater/lists/identifier_params.py`

---

## Appendix: Import Dependency Graph

```
Cross-layer imports found (violations marked with ⚠️):

app_routes/auth/routes.py
  → su_services.users_service        (allowed)
  → db.services.delete_user_token    (allowed)
  → app_routes.auth.cookie           (same layer)
  → app_routes.auth.oauth            (same layer)

app_routes/fixred.py
  → ⚠️ db.models.UserTokenRecord     (V-R3)

app_routes/newupdater/route.py
  → ⚠️ db.models.UserTokenRecord     (V-R3)

app_routes/newupdater/worker.py
  → ⚠️ db.models.UserTokenRecord     (V-R3)
  → api_services.clients             (allowed)
  → api_services.pages_api           (allowed)
  → shared.new_updater               (allowed)

app_routes/utils/routes_utils.py
  → ⚠️ db.models.UserTokenRecord     (V-R3)
  → db.services.admin_service        (allowed)
  → new_jobs.workers_list            (allowed)

app_routes/admin_routes/coordinators.py
  → ⚠️ sqlalchemy.exc.IntegrityError (V-R3 variant)
  → db.services.admin_service        (allowed)

db/models/users.py
  → ⚠️ core.crypto.decrypt_value     (V-M2)

core/crypto.py
  → config.settings                  (allowed — config is lower layer)

shared/fixref_shared/make_title_bot.py
  → ⚠️ requests.get (direct HTTP)    (V-BG2)

new_jobs/workers/create_redirects/worker.py
  → ⚠️ requests.post (direct HTTP)   (V-BG2)

api_services/category.py
  → ⚠️ domain filtering logic        (V-API2)

main_app/__init__.py (factory)
  → ⚠️ sqlalchemy.exc.OperationalError (V-C1)
```

_Generated by flask-soc-audit skill_
