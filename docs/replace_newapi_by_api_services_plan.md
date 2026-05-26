# Migration Plan: Replace `_api` / `newapi` with `api_services` (mwclient)

## 1. Executive Summary

This document details the migration strategy for replacing the legacy `_api` → `newapi` authentication and API layer with the `api_services` module built on `mwclient` with OAuth 1.0a.

### Scope

-   **7 worker modules** in `public_jobs_workers/` that call `get_api()` from `_api.py`
-   **1 shared factory** (`_api.py`) that wraps `newapi.AllAPIS` with username/password auth
-   **1 existing `api_services` module** already using `mwclient.Site` with OAuth
-   **113 Python files** total in `flask_app/`; ~20 are directly affected

### Key Findings

| Finding                                                                                                    | Impact                                              |
| ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| All 7 workers authenticate via `WIKI_USERNAME`/`WIKI_PASSWORD` env vars                                    | Must migrate to OAuth per-user tokens from DB       |
| `api_services` already exists with `mwclient.Site` + OAuth                                                 | Foundation is ready; needs expansion                |
| `api_services` covers page CRUD, text, categories, redirects                                               | 60% of needed operations already implemented        |
| Missing in `api_services`: search, batch existence, page import, raw API queries, category depth traversal | Must be added                                       |
| `settings.jobs.upload_host` referenced in `wiki_client.py` but undefined in `JobsConfig`                   | Pre-existing bug; must fix                          |
| `fixred` already uses both `_api` AND `api_services`                                                       | Partial migration exists as reference               |
| Background workers run in `ThreadPoolExecutor` threads with Flask app context                              | OAuth site must be created per-job, not per-request |
| No Celery — all background work is in-process threading                                                    | Simplifies migration                                |

### Estimated Complexity

| Module                   | Complexity            | Risk   |
| ------------------------ | --------------------- | ------ |
| `_api.py` (factory)      | Low                   | Low    |
| `replace` worker         | Low                   | Low    |
| `newupdater` worker      | Low                   | Low    |
| `redirect` worker        | Medium                | Medium |
| `fixref` worker          | Medium                | Medium |
| `imp` worker             | Medium                | Medium |
| `fix_duplicate` worker   | Medium                | Medium |
| `fixred` worker          | Low (already partial) | Low    |
| `api_services` expansion | High                  | Medium |
| `newapi` deprecation     | Low                   | Low    |

---

## 2. Dependency Analysis

### 2.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    public_jobs_workers/                       │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  fixref  │ │  fixred  │ │  replace │ │  redirect│       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │             │              │
│  ┌────┴─────┐ ┌─────┴────┐ ┌────┴─────┐ ┌────┴─────┐       │
│  │fix_dup   │ │   imp    │ │newupdater│ │          │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────┘       │
│       │             │            │                           │
│       └──────┬──────┴────────────┘                           │
│              ▼                                               │
│       ┌──────────────┐                                       │
│       │   _api.py    │ ◄── get_api() factory                 │
│       │  (lru_cache) │                                       │
│       └──────┬───────┘                                       │
│              │                                               │
│              ▼                                               │
│       ┌──────────────┐                                       │
│       │  newapi/     │                                       │
│       │  AllAPIS     │ ◄── username/password auth            │
│       │  WikiLogin   │                                       │
│       │  Client      │                                       │
│       └──────────────┘                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    api_services/                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ pages_api.py │  │  text_bot.py │  │ category.py  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
│         │                  │                                 │
│         ▼                  ▼                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │mwclient_page │  │  text_api.py │  │clients/      │       │
│  │   .py        │  │ (unauth)     │  │wiki_client.py│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  Used by: fixred (partially)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Files Importing `_api` (via `get_api`)

| #   | File                                            | Import                       | Operations Used                                                                |
| --- | ----------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------ |
| 1   | `public_jobs_workers/fixref/__init__.py`        | `from .._api import get_api` | `CatDepth`, `NewApi().Get_All_pages`, `MainPage().exists/get_text/save`        |
| 2   | `public_jobs_workers/fixred/__init__.py`        | `from .._api import get_api` | `MainPage().exists/get_text/save`, `NewApi().post_params`                      |
| 3   | `public_jobs_workers/replace/__init__.py`       | `from .._api import get_api` | `NewApi().Search`, `NewApi().Get_All_pages`, `MainPage().exists/get_text/save` |
| 4   | `public_jobs_workers/redirect/__init__.py`      | `from .._api import get_api` | `MainPage().exists/create`, `NewApi().Find_pages_exists_or_not`                |
| 5   | `public_jobs_workers/newupdater/__init__.py`    | `from .._api import get_api` | `MainPage().exists/get_text/save`                                              |
| 6   | `public_jobs_workers/fixred/__init__.py`        | `from .._api import get_api` | `MainPage().exists/get_text/save`, `NewApi().post_params`                      |
| 7   | `public_jobs_workers/fix_duplicate/__init__.py` | `from .._api import get_api` | `NewApi().post_params`, `MainPage().exists/get_text/save`                      |
| 8   | `public_jobs_workers/imp/__init__.py`           | `from .._api import get_api` | `MainPage().exists/get_text/import_page/save`                                  |

### 2.3 Files Importing `newapi` Directly

| #   | File                                            | Import                          |
| --- | ----------------------------------------------- | ------------------------------- |
| 1   | `public_jobs_workers/_api.py`                   | `from ..newapi import AllAPIS`  |
| 2   | `public_jobs_workers/fixred/__init__.py`        | `from ...newapi import AllAPIS` |
| 3   | `public_jobs_workers/fix_duplicate/__init__.py` | `from ...newapi import AllAPIS` |

### 2.4 Files Importing `api_services`

| #   | File                                     | Import                                                          |
| --- | ---------------------------------------- | --------------------------------------------------------------- |
| 1   | `public_jobs_workers/fixred/__init__.py` | `from ...api_services.clients.wiki_client import get_user_site` |
| 2   | `public_jobs_workers/fixred/__init__.py` | `from ...api_services.pages_api import resolve_redirects`       |

---

## 3. API Surface Comparison — Compatibility Matrix

### 3.1 Page Operations

| Legacy (`newapi.MainPage`)              | `api_services` Equivalent                         | Migration Complexity | Notes                                                                                                                                                                        |
| --------------------------------------- | ------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `page.exists()`                         | `is_page_exists()`                                | Low                  | Return type differs: legacy returns `bool\|str`, new returns `bool`                                                                                                          |
| `page.get_text()`                       | `get_page_text(page_name, site)` in `text_bot.py` | Low                  | Legacy populates side-channel metadata (`self.ns`, `self.meta`); new returns bare `str`                                                                                      |
| `page.save(newtext, summary, nocreate)` | `MwClientPage.edit_page(text, summary)`           | **Medium**           | Legacy returns `bool\|str`; new returns `dict{success, error}`. `nocreate` param has no equivalent — `mwclient.Site.edit()` supports it but `MwClientPage` doesn't expose it |
| `page.create(text, summary)`            | `create_page(page_name, wikitext, site, summary)` | Low                  | Both create pages; return types differ                                                                                                                                       |
| `page.import_page(family)`              | **No equivalent**                                 | **High**             | Must add to `api_services` using `site.raw_api("import", ...)`                                                                                                               |
| `page.isRedirect()`                     | `MwClientPage.is_redirect()`                      | Low                  | Both check redirect status                                                                                                                                                   |
| `page.get_newrevid()`                   | **No equivalent**                                 | **Medium**           | Must capture from edit response                                                                                                                                              |

### 3.2 Bulk/Bot Operations

| Legacy (`newapi.NewApi`)               | `api_services` Equivalent                                  | Migration Complexity | Notes                                                                                                                                                                                 |
| -------------------------------------- | ---------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Get_All_pages(start, namespace, ...)` | `site.allpages(...)` via mwclient                          | **Medium**           | Return type: legacy returns `list[str]`, mwclient returns iterator of `mwclient.page.Page`. Must extract titles. Semantic diff: `apfilterredir="nonredirects"` vs `filterredir="all"` |
| `Search(value, ns, srlimit, ...)`      | **No equivalent**                                          | **High**             | Must add using `site.raw_api("query", list="search", ...)`                                                                                                                            |
| `Find_pages_exists_or_not(titles)`     | `is_pages_exists(titles, site)` in `pages_api.py`          | Low                  | Already implemented; return format differs slightly                                                                                                                                   |
| `PrefixSearch(pssearch, ns)`           | **No equivalent**                                          | Medium               | Can add via `site.raw_api("query", list="prefixsearch", ...)`                                                                                                                         |
| `Get_Newpages(limit, namespace)`       | **No equivalent**                                          | Medium               | Can add via `site.raw_api("query", list="recentchanges", ...)`                                                                                                                        |
| `post_params(params, method)`          | `site.get(action, **params)` or `site.raw_api(...)`        | **High**             | This is the escape hatch for arbitrary API calls. Must provide equivalent                                                                                                             |
| `move(old_title, to, reason)`          | `move_page(site, title, new_title, ...)` in `pages_api.py` | Low                  | Already implemented                                                                                                                                                                   |

### 3.3 Category Operations

| Legacy (`newapi.CatDepth`)           | `api_services` Equivalent | Migration Complexity | Notes                                                                                                                                                                |
| ------------------------------------ | ------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CatDepth(title, depth, ns, ...)`    | **No equivalent**         | **High**             | Must add recursive category traversal using `site.categories[title]` or raw API. Complex: handles depth, namespace filtering, template filtering, langlink filtering |
| `subcatquery(login_bot, title, ...)` | **No equivalent**         | **High**             | Same as above — the entry point for category traversal                                                                                                               |

### 3.4 Authentication

| Legacy                                      | `api_services` Equivalent               | Migration Complexity | Notes                                                   |
| ------------------------------------------- | --------------------------------------- | -------------------- | ------------------------------------------------------- |
| `WIKI_USERNAME` + `WIKI_PASSWORD` env vars  | OAuth tokens from DB (Fernet-encrypted) | **High**             | Core auth change; affects all workers                   |
| `AllAPIS(lang, family, username, password)` | `get_user_site(user_dict)`              | **High**             | Must pass user dict with `access_token`/`access_secret` |
| `lru_cache` on `get_api()`                  | No caching in `get_user_site()`         | Medium               | Need to decide: cache mwclient.Site or create per-job   |
| Cookie-based session persistence            | No cookies (OAuth tokens in DB)         | Low                  | OAuth tokens don't expire like sessions                 |

---

## 4. Authentication Migration Analysis

### 4.1 Current Auth Flow (Legacy)

```
Environment Variables
  WIKI_USERNAME ──┐
  WIKI_PASSWORD ──┤
                  ▼
           _api.get_api()
                  │
                  ▼
           AllAPIS(lang, family, username, password)
                  │
                  ▼
           WikiLoginClient.__init__()
                  │
                  ▼
           mwclient.Site("{lang}.{family}.org")
                  │
                  ▼
           site.login(username, password)  ◄── username/password auth
                  │
                  ▼
           Cached via @lru_cache(maxsize=8)
```

### 4.2 Target Auth Flow (api_services)

```
Flask Request / Background Thread
                  │
                  ▼
           current_user() from users_service
                  │
                  ▼
           UserTokenRecord from DB (user_id)
                  │
                  ▼
           record.decrypted() → (access_key, access_secret)
                  │
                  ▼
           get_user_site(user_dict)
                  │
                  ▼
           coerce_encrypted(access_token) → bytes
           coerce_encrypted(access_secret) → bytes
                  │
                  ▼
           build_upload_site(token_bytes, secret_bytes)
                  │
                  ▼
           decrypt_value(token) → str
           decrypt_value(secret) → str
                  │
                  ▼
           mwclient.Site(
               host,
               scheme="https",
               consumer_token=OAUTH_CONSUMER_KEY,
               consumer_secret=OAUTH_CONSUMER_SECRET,
               access_token=decrypted_key,
               access_secret=decrypted_secret,
           )
```

### 4.3 Critical Auth Differences

| Aspect              | Legacy (`newapi`)                    | Target (`api_services`)                       |
| ------------------- | ------------------------------------ | --------------------------------------------- |
| Credential type     | Username/password (bot password)     | OAuth 1.0a access token/secret                |
| Storage             | Environment variables                | Fernet-encrypted in DB (`user_tokens` table)  |
| Identity            | Single bot account                   | Per-user (each logged-in user has own tokens) |
| Permissions         | Bot account may have elevated rights | User's actual wiki permissions                |
| Token lifetime      | No expiry (password-based)           | OAuth tokens may be revoked by user           |
| Session persistence | Cookie jar on disk                   | No session; tokens from DB each time          |
| Caching             | `lru_cache` (process lifetime)       | None; create per-request/per-job              |

### 4.4 Background Worker Auth Strategy

**Problem**: Workers run in background threads. `current_user()` reads from Flask `g` and `session`, which are only available in the request thread.

**Solution**: The job runner already captures `user` at submission time and passes it to the worker. The `fixred` worker demonstrates this pattern:

```python
# In the route handler (request thread):
user = current_user()
site = get_user_site(user)

# In the worker function (background thread):
# site is passed as a parameter, or user dict is passed
```

**Recommended approach**: Pass the `mwclient.Site` (or the user dict) as a parameter to each worker's `run()` function, rather than calling `current_user()` inside the worker.

### 4.5 Service Account for Background Jobs

**Alternative**: Create a dedicated service account whose OAuth tokens are stored as a special `UserTokenRecord` (e.g., `user_id=0` or a well-known username). This avoids requiring a logged-in user for background jobs.

```python
# In config:
SERVICE_ACCOUNT_TOKEN = os.getenv("SERVICE_ACCOUNT_TOKEN")
SERVICE_ACCOUNT_SECRET = os.getenv("SERVICE_ACCOUNT_SECRET")

# Factory:
def get_service_site() -> mwclient.Site:
    """Create an mwclient.Site using the service account."""
    return _build_site(
        settings.oauth.service_account_token,
        settings.oauth.service_account_secret,
    )
```

**Recommendation**: Implement both paths — per-user OAuth for interactive operations, service account for unattended background jobs.

---

## 5. mwclient Integration Architecture

### 5.1 Site Creation Strategy

**Current state**: `api_services` creates a new `mwclient.Site` on every call to `get_user_site()`. No caching.

**Recommendation**: Create a `SiteFactory` with optional caching:

```python
# api_services/clients/wiki_client.py

import threading
from typing import Any, Dict, Optional
import mwclient
from ...config import settings
from ...core.crypto import decrypt_value

class SiteFactory:
    """Thread-safe factory for mwclient.Site instances."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, mwclient.Site] = {}

    def get_user_site(self, user: Dict[str, Any] | None) -> mwclient.Site | None:
        """Create or retrieve a cached mwclient.Site for the given user."""
        if user is None:
            return None

        user_id = user.get("user_id")
        cache_key = f"user_{user_id}" if user_id else None

        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]

        access_token = coerce_encrypted(user.get("access_token"))
        access_secret = coerce_encrypted(user.get("access_secret"))

        if not access_token or not access_secret:
            return None

        try:
            site = build_upload_site(access_token, access_secret)
        except Exception:
            logger.exception("Failed to build OAuth site")
            return None

        if cache_key:
            with self._lock:
                self._cache[cache_key] = site

        return site

    def get_service_site(self) -> mwclient.Site | None:
        """Create a site using the service account credentials."""
        # Implementation depends on service account setup
        ...

    def clear_cache(self):
        with self._lock:
            self._cache.clear()

# Module-level singleton
_site_factory = SiteFactory()
get_user_site = _site_factory.get_user_site
get_service_site = _site_factory.get_service_site
```

### 5.2 Thread Safety

-   `mwclient.Site` is **not thread-safe** internally (shared `requests.Session` state).
-   Each background worker thread should have its own `mwclient.Site` instance.
-   The `SiteFactory` cache should use thread-local storage or per-thread instances for production safety.

**Revised recommendation**: Use `threading.local()` for per-thread site caching:

```python
_thread_local = threading.local()

def get_user_site(user):
    if not hasattr(_thread_local, "sites"):
        _thread_local.sites = {}
    user_id = user.get("user_id")
    if user_id in _thread_local.sites:
        return _thread_local.sites[user_id]
    site = _build_site_for_user(user)
    _thread_local.sites[user_id] = site
    return site
```

### 5.3 Host Configuration Bug

**Pre-existing bug**: `api_services/clients/wiki_client.py` line 21 references `settings.jobs.upload_host`, but `JobsConfig` only has `jobs_max_workers` and `jobs_log_lines`.

**Fix required**: Add `host` field to `JobsConfig`:

```python
# config/classes.py
@dataclass(frozen=True)
class JobsConfig:
    jobs_max_workers: int
    jobs_log_lines: int
    host: str  # NEW: wiki host for API calls
```

```python
# config/main_settings.py
def _load_jobs_config() -> JobsConfig:
    _lang = os.getenv("WIKI_LANG") or "www"
    _family = os.getenv("WIKI_FAMILY") or "mdwiki"
    host = os.getenv("WIKI_HOST") or f"{_lang}.{_family}.org"

    return JobsConfig(
        jobs_max_workers=max(1, _env_int("JOBS_MAX_WORKERS", 2)),
        jobs_log_lines=max(10, _env_int("JOBS_LOG_LINES", 200)),
        host=host,
    )
```

---

## 6. Phased Migration Plan

### Phase 0: Preparation (No Behavioral Changes)

**Goal**: Fix bugs, add missing config, prepare `api_services` for expansion.

**Files modified**:

-   `config/classes.py` — add `host: str` to `JobsConfig`
-   `config/main_settings.py` — populate `host` from env vars
-   `api_services/clients/wiki_client.py` — fix `settings.jobs.upload_host` → `settings.jobs.host`

**Validation**: All existing tests pass. No behavioral change.

---

### Phase 1: Expand `api_services` with Missing Operations

**Goal**: Add all operations that workers need but `api_services` doesn't yet provide.

**New functions to add**:

#### 1a. `api_services/pages_api.py` additions

```python
def get_page_text(site: mwclient.Site, title: str) -> str:
    """Fetch wikitext. Delegates to text_bot.get_page_text."""
    from .text_bot import get_page_text
    return get_page_text(title, site)


def search_pages(site: mwclient.Site, value: str, ns: str = "*",
                 srlimit: str = "max", **kwargs) -> list[str]:
    """Full-text search. Returns list of titles."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": value,
        "srnamespace": ns,
        "srlimit": srlimit,
        "srwhat": kwargs.get("srwhat", "text"),
        "srsort": kwargs.get("srsort", "just_match"),
    }
    data = site.get("query", **params)
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def get_all_pages(site: mwclient.Site, start: str = "", namespace: str = "0",
                  limit: int = 100000, filterredir: str = "all") -> list[str]:
    """List all pages in a namespace. Returns list of titles."""
    kwargs = {"start": start, "namespace": int(namespace), "filterredir": filterredir}
    titles = []
    for page in site.allpages(**kwargs):
        titles.append(page.name)
        if len(titles) >= limit:
            break
    return titles


def batch_existence(site: mwclient.Site, titles: list[str]) -> dict[str, bool]:
    """Check existence of multiple pages. Alias for is_pages_exists."""
    return is_pages_exists(titles, site)


def import_page(site: mwclient.Site, title: str, family: str = "wikipedia") -> dict:
    """Import page history from another wiki family."""
    page = site.pages[title]
    try:
        result = site.raw_api("import", token=site.get_token("csrf"),
                              summary="", interwiki=family,
                              fullhistory=1, templates=1,
                              **{"forupdate": 1})
        site.raw_api("purge", titles=title)  # purge after import
        return {"success": True, "result": result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def raw_query(site: mwclient.Site, **params) -> dict:
    """Execute an arbitrary query API call. Replacement for post_params."""
    action = params.pop("action", "query")
    method = params.pop("method", "GET")
    if method.upper() == "POST":
        return site.raw_api(action, **params)
    return site.get(action, **params)
```

#### 1b. `api_services/category.py` additions

```python
def get_category_depth(site: mwclient.Site, title: str, depth: int = 0,
                       namespace: str = "0", limit: int = 100000) -> dict[str, dict]:
    """Recursive category member traversal.

    Replacement for newapi.CatDepth / subcatquery.
    Returns dict mapping title -> {"ns": int, "revid": int}.
    """
    # Implementation using mwclient's category iteration
    # with recursive subcategory walking
    ...
```

#### 1c. `api_services/mwclient_page.py` additions

```python
class MwClientPage:
    # Add missing methods:

    def get_text(self) -> str:
        """Fetch wikitext content."""
        page = self.load_page()
        if not page:
            return ""
        return page.text()

    def import_page(self, family: str = "wikipedia") -> dict:
        """Import page history from another wiki family."""
        ...

    def get_newrevid(self) -> int:
        """Get the revision ID of the last edit."""
        return self._newrevid

    def create(self, text: str, summary: str = "") -> dict:
        """Create a new page. Returns success dict."""
        ...
```

**Files modified**:

-   `api_services/pages_api.py` — add search, allpages, import, raw_query
-   `api_services/mwclient_page.py` — add get_text, import_page, create, get_newrevid
-   `api_services/category.py` — add get_category_depth
-   `api_services/text_bot.py` — already sufficient

**Validation**: Write unit tests for each new function with mocked `mwclient.Site`.

---

### Phase 2: Migrate Workers One-by-One

**Goal**: Replace `get_api()` calls with `api_services` equivalents. Each worker is migrated independently.

**Strategy**: For each worker:

1. Add `site` parameter to the `run()` function
2. Replace `get_api()` with `site` usage
3. Replace `api.MainPage(title)` with `MwClientPage(title, site)` or `pages_api` functions
4. Replace `api.NewApi().X()` with `pages_api` equivalents
5. Update the route handler to pass `site` from `get_user_site(current_user())`

#### 2a. `replace` worker (Low complexity)

**File**: `public_jobs_workers/replace/__init__.py`

**Changes**:

```diff
-from .._api import get_api
+from ...api_services.clients.wiki_client import get_user_site
+from ...api_services.pages_api import search_pages, get_all_pages, edit_page, is_page_exists
+from ...api_services.text_bot import get_page_text

 def run(*, find, replace="", listtype="newlist", number=None, save=True,
-        on_progress=None, stop_event=None):
+        on_progress=None, stop_event=None, site=None):
     ...
-    api = get_api()
-    titles = _resolve_titles(api, find=find, listtype=listtype)
+    titles = _resolve_titles(site, find=find, listtype=listtype)
     ...

-def _resolve_titles(api, *, find, listtype):
+def _resolve_titles(site, *, find, listtype):
     if listtype == "newlist":
-        return api.NewApi().Search(value=find, ns="0", srlimit="max", ...) or []
-    return api.NewApi().Get_All_pages() or []
+        return search_pages(site, value=find, ns="0", srlimit="max") or []
+    return get_all_pages(site) or []

-def _process_one(api, title, *, find, replace, save, log):
-    page = api.MainPage(title)
-    if not page.exists():
+def _process_one(site, title, *, find, replace, save, log):
+    if not is_page_exists(title, site):
         return "missing"
-    text = page.get_text() or ""
+    text = get_page_text(site, title) or ""
     ...
     if save:
-        saved = page.save(newtext=new_text, summary=summary)
-        if saved is True:
+        result = edit_page(site, title, new_text, summary)
+        if result.get("success"):
             return "changed"
```

#### 2b. `newupdater` worker (Low complexity)

**File**: `public_jobs_workers/newupdater/__init__.py`

Same pattern as `replace`. Only uses `MainPage().exists/get_text/save`.

#### 2c. `redirect` worker (Medium complexity)

**File**: `public_jobs_workers/redirect/__init__.py`

**Additional change**: `Find_pages_exists_or_not` → `batch_existence`:

```diff
-    existing = api.NewApi().Find_pages_exists_or_not(redirect_titles, noprint=True) or {}
+    existing = batch_existence(site, redirect_titles) or {}

-    new_page = api.MainPage(r_title)
-    if new_page.exists():
+    if is_page_exists(r_title, site):
         ...
-    new_page.create(redirect_text, summary)
+    create_page(r_title, redirect_text, site, summary)
```

#### 2d. `fixref` worker (Medium complexity)

**File**: `public_jobs_workers/fixref/__init__.py`

**Additional change**: `CatDepth` → `get_category_depth`:

```diff
-    members = api.CatDepth(cat, sitecode="www", family="mdwiki", depth=0, ns="0") or []
+    members = get_category_depth(site, cat, depth=0, namespace="0") or {}

-    return api.NewApi().Get_All_pages("", limit_all=capped)[:capped]
+    return get_all_pages(site, limit=capped)[:capped]
```

#### 2e. `fix_duplicate` worker (Medium complexity)

**File**: `public_jobs_workers/fix_duplicate/__init__.py`

**Additional change**: `post_params` → `raw_query`:

```diff
-    data = new_api.post_params(params, method="post") or {}
+    data = raw_query(site, **params) or {}

-    page = api.MainPage(from_title)
-    if not page.exists():
+    if not is_page_exists(from_title, site):
         return "missing"
-    oldtext = page.get_text()
+    oldtext = get_page_text(site, from_title)
     ...
-    ok = page.save(newtext=newtext, summary=summary)
+    result = edit_page(site, from_title, newtext, summary)
+    ok = result.get("success")
```

#### 2f. `imp` worker (Medium complexity)

**File**: `public_jobs_workers/imp/__init__.py`

**Additional change**: `import_page` must be added to `api_services`:

```diff
-    page = api.MainPage(title)
-    if not page.exists():
+    if not is_page_exists(title, site):
         return "missing"
-    text = page.get_text()
+    text = get_page_text(site, title)
-    result = page.import_page(family="wikipedia") or {}
+    result = import_page_from_family(site, title, family="wikipedia")
     ...
-    saved = page.save(newtext=text, summary="", nocreate=1)
+    result = edit_page(site, title, text, "")
+    saved = result.get("success")
```

**Note**: `nocreate=1` parameter needs to be added to `MwClientPage.edit_page()`.

#### 2g. `fixred` worker (Low complexity — already partial)

**File**: `public_jobs_workers/fixred/__init__.py`

Already uses `api_services` for `resolve_redirects` and `get_user_site`. Remaining `get_api()` usage is for `MainPage` operations and `post_params`.

```diff
-from .._api import get_api
-# keep: from ...api_services.clients.wiki_client import get_user_site
-# keep: from ...api_services.pages_api import resolve_redirects
+from ...api_services.text_bot import get_page_text
+from ...api_services.pages_api import edit_page, is_page_exists, raw_query

-    api = get_api()
-    page = api.MainPage(title)
-    if not page.exists():
+    if not is_page_exists(title, site):
         return "missing"
-    text = page.get_text()
+    text = get_page_text(site, title)
```

**Route handler changes** (all job routes):

```diff
 # jobs_routes/replace/__init__.py (example)
+from ...api_services.clients.wiki_client import get_user_site
+from ...su_services.users_service import current_user

 def run_replace():
     ...
+    user = current_user()
+    site = get_user_site(user)
+    if not site:
+        abort(401, "Wiki authentication required")
     runner.submit(
         "replace",
         svc.run,
         submitted_by=user.username,
         params={...},
+        site=site,
     )
```

---

### Phase 3: Remove `_api.py` and `newapi` Imports

**Goal**: Delete the legacy factory and stop importing `newapi`.

**Files modified**:

-   Delete `public_jobs_workers/_api.py`
-   Remove `from .._api import get_api` from all 7 workers
-   Remove `from ...newapi import AllAPIS` from `fixred` and `fix_duplicate`

**Validation**: `grep -r "from.*_api import\|from.*newapi import" flask_app/` returns no results.

---

### Phase 4: Deprecate `newapi` Module

**Goal**: Mark `newapi` as deprecated. Do NOT delete yet — other codebases may reference it.

**Files modified**:

-   `newapi/__init__.py` — add deprecation warning:
    ```python
    import warnings
    warnings.warn(
        "newapi is deprecated. Use api_services instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    ```

**Timeline**: Delete `newapi/` after 3 months of zero internal usage confirmed via production logs.

---

### Phase 5: Cleanup and Hardening

**Goal**: Remove dead code, improve error handling, add comprehensive tests.

**Tasks**:

1. Remove unused `newapi` imports from any remaining files
2. Add type annotations to all new `api_services` functions
3. Add `__all__` exports to `api_services/pages_api.py` for new functions
4. Standardize return types across `api_services` (all write operations return `dict`)
5. Add structured logging for all API calls
6. Add metrics/observability hooks

---

## 7. Backward Compatibility Plan

### 7.1 Temporary Adapter

**Not recommended.** The `fixred` worker already demonstrates that `api_services` can be used directly alongside `newapi`. A shim layer would add complexity without benefit.

### 7.2 Deprecation Path

```
Phase 0: Fix bugs, expand api_services         (1 week)
Phase 1: Add missing operations to api_services (1-2 weeks)
Phase 2: Migrate workers one-by-one             (2-3 weeks)
Phase 3: Remove _api.py and newapi imports      (1 day)
Phase 4: Deprecate newapi                       (1 day)
Phase 5: Cleanup and hardening                  (1 week)
                                         Total: ~5-7 weeks
```

### 7.3 Rollback Strategy

**Per-worker rollback**: Each worker migration is independent. If a worker fails after migration:

1. Revert the worker's imports back to `get_api()`
2. Revert the route handler to not pass `site`
3. The `_api.py` factory remains available until Phase 3

**Full rollback**: Revert the entire `public_jobs_workers/` directory to the pre-migration commit.

**Feature flag approach** (optional):

```python
# In each worker:
import os
USE_MWCLIENT = os.getenv("USE_MWCLIENT", "0") == "1"

def run(*, ..., site=None):
    if USE_MWCLIENT and site:
        return _run_mwclient(site, ...)
    return _run_legacy(...)
```

---

## 8. Risk Assessment

### 8.1 Risk Matrix

| Risk                                           | Probability | Impact | Mitigation                                                 |
| ---------------------------------------------- | ----------- | ------ | ---------------------------------------------------------- |
| OAuth tokens revoked mid-job                   | Medium      | High   | Implement token refresh; fallback to service account       |
| `mwclient.Site` not thread-safe                | High        | Medium | Use per-thread instances via `threading.local()`           |
| Missing `nocreate` parameter in edit_page      | High        | Medium | Add `nocreate` support to `MwClientPage.edit_page()`       |
| `import_page` not available in mwclient        | Medium      | High   | Use `site.raw_api("import", ...)` directly                 |
| Category depth traversal performance           | Medium      | Medium | Implement with pagination limits and progress callbacks    |
| `settings.jobs.host` undefined                 | High        | Low    | Fix in Phase 0                                             |
| Worker fails without `site` parameter          | Medium      | Medium | Add validation at worker entry; fail fast with clear error |
| OAuth consumer credentials not configured      | Low         | High   | Fail fast at startup with clear error message              |
| Rate limiting differences between auth methods | Low         | Medium | Both use mwclient; rate limiting is handled by mwclient    |
| Edit conflicts (no `baserevid` in new path)    | Medium      | High   | Implement edit conflict detection using revision IDs       |

### 8.2 Permission Differences

**Legacy bot account**: May have `bot` flag, `suppressredirect`, `import`, `autopatrol` rights.

**User OAuth tokens**: Have the user's actual permissions. Some operations may fail if the user lacks elevated rights.

**Mitigation**: For operations requiring elevated rights (import, suppressredirect), use the service account.

### 8.3 API Behavior Differences

| Behavior                                            | Legacy (`newapi`)                          | Target (`mwclient`)                                          |
| --------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| `Get_All_pages` with `apfilterredir="nonredirects"` | Returns only non-redirect pages            | `site.allpages(filterredir="nonredirects")` — same behavior  |
| `Get_All_pages` returns `list[str]`                 | Titles as strings                          | `site.allpages()` returns `Page` objects — must call `.name` |
| `Search` returns `list[str]`                        | Titles as strings                          | Must parse `site.get("query", list="search")` response       |
| `MainPage.save()` returns `bool\|str`               | `True` on success, error string on failure | `MwClientPage.edit_page()` returns `dict`                    |
| `MainPage.exists()` returns `bool\|str`             | Can return string "0" or "1"               | `is_page_exists()` returns `bool`                            |
| `post_continue` handles pagination                  | Automatic continuation                     | Must implement per-operation or use mwclient's built-in      |

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_api_services_pages.py

import pytest
from unittest.mock import MagicMock, patch
import mwclient

from main_app.api_services.pages_api import (
    is_page_exists,
    edit_page,
    search_pages,
    get_all_pages,
    batch_existence,
)


@pytest.fixture
def mock_site():
    site = MagicMock(spec=mwclient.Site)
    site.pages = {}
    return site


class TestIsPageExists:
    def test_existing_page(self, mock_site):
        page = MagicMock()
        page.exists = True
        mock_site.pages.__getitem__.return_value = page
        assert is_page_exists("Test", mock_site) is True

    def test_missing_page(self, mock_site):
        page = MagicMock()
        page.exists = False
        mock_site.pages.__getitem__.return_value = page
        assert is_page_exists("Nonexistent", mock_site) is False


class TestEditPage:
    def test_successful_edit(self, mock_site):
        page = MagicMock()
        page.exists = True
        page.edit.return_value = {}
        mock_site.pages.__getitem__.return_value = page
        result = edit_page(mock_site, "Test", "new text", "summary")
        assert result == {"success": True}

    def test_protected_page(self, mock_site):
        page = MagicMock()
        page.exists = True
        page.edit.side_effect = mwclient.errors.ProtectedPageError(
            code="protected", info="Page is protected"
        )
        mock_site.pages.__getitem__.return_value = page
        result = edit_page(mock_site, "Test", "new text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"


class TestSearchPages:
    def test_search_returns_titles(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "search": [
                    {"title": "Page1"},
                    {"title": "Page2"},
                ]
            }
        }
        result = search_pages(mock_site, "test query")
        assert result == ["Page1", "Page2"]
```

### 9.2 Integration Tests

```python
# tests/test_worker_migration.py

import pytest
from unittest.mock import MagicMock, patch
from main_app.public_jobs_workers.replace import run as replace_run


@pytest.fixture
def mock_site():
    """Mock mwclient.Site for integration testing."""
    site = MagicMock()
    return site


class TestReplaceWorker:
    @patch("main_app.public_jobs_workers.replace.get_all_pages")
    @patch("main_app.public_jobs_workers.replace.get_page_text")
    @patch("main_app.public_jobs_workers.replace.edit_page")
    @patch("main_app.public_jobs_workers.replace.is_page_exists")
    def test_replace_dry_run(self, mock_exists, mock_edit, mock_text, mock_pages, mock_site):
        mock_pages.return_value = ["Page1", "Page2"]
        mock_exists.return_value = True
        mock_text.return_value = "Hello World"
        mock_edit.return_value = {"success": True}

        result = replace_run(
            find="Hello",
            replace="Goodbye",
            save=False,
            site=mock_site,
        )
        assert result["scanned"] == 2
        assert result["changed"] == 2
        mock_edit.assert_not_called()  # dry run
```

### 9.3 OAuth Failure Tests

```python
# tests/test_oauth_failures.py

class TestOAuthFailures:
    def test_revoked_token_returns_none(self):
        """get_user_site returns None when tokens are invalid."""
        ...

    def test_missing_user_returns_none(self):
        """get_user_site returns None for None user."""
        ...

    def test_worker_fails_fast_without_site(self):
        """Worker raises clear error when site is None."""
        ...
```

### 9.4 Regression Tests

For each worker, before migration:

1. Record the exact API calls made during a representative run
2. After migration, verify the same logical operations occur
3. Compare output (page text, edit summaries, result counts)

### 9.5 Staging Validation

1. Deploy to staging with feature flag `USE_MWCLIENT=0` (legacy path)
2. Run each tool against test pages
3. Switch to `USE_MWCLIENT=1` (new path)
4. Run same tools against same test pages
5. Compare results

---

## 10. Recommended Code Patterns

### 10.1 Worker Function Signature Pattern

All workers should accept `site` as an optional keyword argument:

```python
def run(
    *,
    titles: Iterable[str] | None = None,
    save: bool = True,
    on_progress: Callable | None = None,
    stop_event: Event | None = None,
    site: mwclient.Site | None = None,  # NEW
) -> dict[str, Any]:
    if site is None:
        raise ValueError("site parameter is required (use get_user_site)")
    ...
```

### 10.2 Error Handling Pattern

Standardize on the `api_services` dict return pattern:

```python
def operation(...) -> dict:
    try:
        ...
        return {"success": True, "data": result}
    except mwclient.errors.ProtectedPageError:
        return {"success": False, "error": "protected", "details": str(exc)}
    except mwclient.errors.APIError as exc:
        return {"success": False, "error": exc.code, "details": str(exc)}
    except Exception as exc:
        logger.exception("Operation failed")
        return {"success": False, "error": "unknown", "details": str(exc)}
```

### 10.3 Progress Callback Pattern

Maintain the existing progress callback interface:

```python
def _emit(done: int, total: int, msg: str) -> None:
    if on_progress is not None:
        on_progress(done, total, message=msg)
```

### 10.4 Site Factory Usage Pattern

In route handlers:

```python
from ...api_services.clients.wiki_client import get_user_site
from ...su_services.users_service import current_user, oauth_required

@bp.route("/replace/", methods=["POST"])
@oauth_required
def start_replace():
    user = current_user()
    site = get_user_site(user)
    if not site:
        abort(401, "Wiki authentication required. Please log in again.")
    runner.submit(
        "replace",
        svc.run,
        submitted_by=user.username,
        params={...},
        site=site,
    )
```

---

## 11. Technical Debt Identified

| Debt                                                  | Location                                      | Impact                      | Recommendation                  |
| ----------------------------------------------------- | --------------------------------------------- | --------------------------- | ------------------------------- |
| `settings.jobs.upload_host` undefined                 | `api_services/clients/wiki_client.py:21`      | Runtime crash if called     | Fix in Phase 0                  |
| Two parallel job systems (`jobs/` vs `jobs_workers/`) | `main_app/jobs/` and `main_app/jobs_workers/` | Confusion, code duplication | Consolidate in future sprint    |
| `newapi/core/exceptions.py` unused                    | `newapi/core/exceptions.py`                   | Dead code                   | Remove with `newapi` in Phase 4 |
| `AllAPIS` type annotation in `fix_duplicate`          | `fix_duplicate/__init__.py:22`                | Unused import               | Remove in Phase 3               |
| No `__all__` in several `api_services` modules        | Various                                       | Unclear public API          | Add in Phase 5                  |
| Inconsistent return types across workers              | All workers                                   | `bool` vs `str` vs `dict`   | Standardize in Phase 5          |
| `newapi` config.py has its own `Settings` singleton   | `newapi/config.py`                            | Parallel config system      | Remove with `newapi`            |
| `tqdm` dependency in `newapi`                         | `newapi/client_wiki/bot_api.py`               | External dependency         | Not needed in `api_services`    |

---

## 12. Migration Complexity by Module

| Module                                          | Lines Changed (est.) | New Code (est.) | Risk   | Priority |
| ----------------------------------------------- | -------------------- | --------------- | ------ | -------- |
| `config/classes.py`                             | 2                    | 0               | Low    | P0       |
| `config/main_settings.py`                       | 5                    | 0               | Low    | P0       |
| `api_services/clients/wiki_client.py`           | 1                    | 0               | Low    | P0       |
| `api_services/pages_api.py`                     | 0                    | ~100            | Medium | P1       |
| `api_services/mwclient_page.py`                 | 0                    | ~80             | Medium | P1       |
| `api_services/category.py`                      | 0                    | ~120            | High   | P1       |
| `public_jobs_workers/replace/__init__.py`       | ~20                  | 0               | Low    | P2       |
| `public_jobs_workers/newupdater/__init__.py`    | ~15                  | 0               | Low    | P2       |
| `public_jobs_workers/redirect/__init__.py`      | ~25                  | 0               | Medium | P2       |
| `public_jobs_workers/fixref/__init__.py`        | ~25                  | 0               | Medium | P2       |
| `public_jobs_workers/fix_duplicate/__init__.py` | ~25                  | 0               | Medium | P2       |
| `public_jobs_workers/imp/__init__.py`           | ~20                  | 0               | Medium | P2       |
| `public_jobs_workers/fixred/__init__.py`        | ~15                  | 0               | Low    | P2       |
| `public_jobs_workers/_api.py`                   | delete               | 0               | Low    | P3       |
| `newapi/` (deprecation warning)                 | 3                    | 0               | Low    | P4       |
| **Total**                                       | **~155**             | **~300**        |        |          |
