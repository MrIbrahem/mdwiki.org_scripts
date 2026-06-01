# Refactoring Plan: MDWiki Tools (Flask Application)

**Analysis Date**: May 30, 2026
**Analyst**: Claude Refactoring Analyst
**Repository**: `i:\MD_TOOLS\mdwiki.org_scripts\repo`

## Executive Summary

This is a well-architected Flask application with a clean layered structure (Controller → Service → Repository → Database) serving Wikimedia Toolforge. The application factory pattern, frozen dataclass configuration, and worker lifecycle template method are genuine strengths. However, there are significant code quality issues: unused/stub code, layering violations in controllers, a dead API wrapper, duplicate utility functions, sparse test coverage for workers, and several `# pragma: no cover` guards masking untested error paths. The top priority is addressing architectural layering violations and removing dead code, followed by improving test coverage and consolidating duplicated logic.

---

## Current State Assessment

### Strengths

-   **Layered Architecture**: Strict Controller → Service → Repository → Database dependency flow is documented and mostly followed.
-   **Application Factory Pattern**: `create_app()` provides clean initialization with graceful DB-failure fallback.
-   **Frozen Dataclass Configuration**: Immutable `Settings` singleton loaded from environment variables — clean, testable, and well-documented.
-   **Worker Lifecycle Pattern**: `BaseObjectsJobWorker` with `before_run() → process() → after_run()` template method provides consistent job execution.
-   **Good Test Infrastructure**: `conftest.py` has session-scoped app, CSRF-aware client, login helper, and `stub_service` fixture.
-   **Type Hints**: Extensive use of `from __future__ import annotations` and type hints throughout.
-   **OAuth Security**: Fernet encryption for tokens, signed cookies, rate limiting on auth endpoints.
-   **Documentation**: `CLAUDE.md`, `README.md`, and inline `README.md` files in major subsystems.

### Areas for Improvement

1. **Architectural Layering Violations** — Controllers importing models and db services directly
2. **Dead/Stub Code** — Unused functions, commented-out code, empty TODO workers
3. **Code Duplication** — Duplicate utility functions, similar entry points
4. **Inconsistent Naming** — Cryptic abbreviations, confusing directory structure
5. **Test Coverage Gaps** — Missing tests for workers, API services, error paths
6. **Complex Wikitext Logic** — Undocumented, poorly structured wikitext processors
7. **Configuration Drift** — Stale `pyproject.toml` settings from copy-paste
8. **Potential Bugs** — Logic errors in retry logic, category filtering

---

## Detailed Findings

### 1. Architectural Layering Violations

**Priority**: Critical
**Impact**: Undermines the entire layered architecture, makes code harder to reason about and test

#### Issues Found:

-   [ ] **Controller imports model directly** — `flask_app/main_app/app_routes/new_jobs.py` (line 18) imports `JobRecord` from `..db.models`. Controllers should never import models.
-   [ ] **Controller imports db services directly** — `flask_app/main_app/app_routes/new_jobs.py` (lines 21-25) imports `active_coordinators`, `delete_job`, `get_job`, `list_jobs` from `..db.services`. These should be accessed through `su_services` or a dedicated service layer.
-   [ ] **Admin controller bypasses service layer** — `flask_app/main_app/app_routes/admin/routes.py` (line 21) imports `list_users` from `..db.services` directly.
-   [ ] **`create_app()` factory imports db services** — `flask_app/main_app/__init__.py` (line 18) imports `active_coordinators` from `.db.services`. This couples the app factory to the database layer.
-   [ ] **Service-layer logic in route utils** — `flask_app/main_app/app_routes/utils/routes_utils.py::load_auth_payload()` constructs auth payload dicts, which is business logic in a "utils" file.

#### Recommendations:

1. [ ] Create proper service modules in `su_services/` to wrap all `db.services` calls used by controllers
2. [ ] Move `load_auth_payload()` to `su_services/`
3. [ ] Remove all `from ..db.models import ...` statements from route files
4. [ ] Extract `active_coordinators()` usage from the factory into a lazy-loading pattern

---

### 2. Dead / Stub / Commented-Out Code

**Priority**: High
**Impact**: Code clutter, misleading signals, maintenance burden

#### Issues Found:

-   [x] **Dead API wrapper** — `flask_app/main_app/api_services/query_api.py::get_template_pages_newapi()` (line 10) references `api.NewApi()` which doesn't exist. The function is unused anywhere.
-   [ ] **Stub workers** — `add_r_column` and `add_unlinkedwikibase` workers contain `TODO: import logic from ...` comments. They are essentially empty shells.
-   [x] **Commented-out blueprint registrations** — `flask_app/main_app/app_routes/admin/routes.py` (lines 103-108) has 5 commented-out blueprint registrations.
-   [ ] **Disabled teardown** — `flask_app/main_app/__init__.py` (lines 131-145) has a `_cleanup_connections` teardown function where the entire body is commented out with a pass statement.
-   [ ] **Empty `__init__.py` files** — `flask_app/main_app/app_routes/newupdater/__init__.py`, `flask_app/main_app/shared/fixref_shared/__init__.py`, `flask_app/main_app/new_jobs/__init__.py` are all empty (though some serve package marker purposes).
-   [ ] **Commented template code** — `flask_app/templates/jobs_templates/base_list2.html` and `base_details2.html` have commented-out `status_icon()` calls.
-   [ ] **Commented-out filter logic** — `create_redirects/worker.py` (line ~100) has `# if page.get("title") != title: continue` commented out.
-   [ ] **`flask_app/__init__.py`** — The root `flask_app/__init__.py` exists but is empty/trivial. Consider if needed.
-   [ ] **Unreferenced CSS files** — `static/css/navbar.css` is referenced in `<link>` but navbar is built with Bootstrap classes. Check if it's still needed.

#### Recommendations:

1. [ ] Remove `get_template_pages_newapi()` from `query_api.py`
2. [ ] Either implement the two stub workers or remove them from `workers_list.py`
3. [x] Remove commented-out blueprint registrations
4. [ ] Either implement the teardown logic or remove the handler entirely
5. [ ] Clean up commented template code
6. [ ] Remove or implement the commented filter logic

---

### 3. Code Duplication

**Priority**: High
**Impact**: Maintainability cost when fixing bugs or updating logic

#### Issues Found:

-   [ ] **Duplicate bytes coercion** — `flask_app/main_app/api_services/clients/wiki_client.py::coerce_encrypted()` (lines 27-38) duplicates the same logic as `flask_app/main_app/shared/decode_bytes.py::coerce_bytes()`. Both handle bytes, bytearray, memoryview. The `coerce_encrypted` variant also handles str→bytes.
-   [ ] **Two app entry points** — `flask_app/app.py` (production) and `flask_app/app1.py` (development) are nearly identical. The only differences are `load_dotenv()` call and `use_colorlog` setting.
-   [ ] **Duplicate flash/redirect patterns** — Almost every controller function follows the same `try/except: logger.exception(); flash()/redirect()` pattern — ~14 instances of `# pragma: no cover - defensive guard`.
-   [ ] **Duplicate template structure** — `all_jobs_list.html`, `base_list2.html`, and per-worker list templates share very similar table structures.

#### Recommendations:

1. [ ] Consolidate bytes-coercion into a single utility module (keep `decode_bytes.py`, remove from `wiki_client.py`)
2. [ ] Combine `app.py` and `app1.py` into a single entry point that detects environment
3. [ ] Consider a shared error-handling decorator for routes to replace the repetitive try/except patterns
4. [ ] Refactor template inheritance to reduce duplication in job list templates

---

### 4. Inconsistent Naming & Organization

**Priority**: Medium
**Impact**: Developer confusion, onboarding friction

#### Issues Found:

-   [ ] **`su_services/` name is cryptic** — "su" likely means "service-user" or "super-user" but is not documented. This should be renamed to something clear like `auth_services/` or `user_services/`.
-   [ ] **`new_jobs/` naming** — Implies there are "old jobs" somewhere. The directory houses the entire background job system. Should be renamed to `jobs/` or `workers/`.
-   [ ] **`app_routes/admin/` vs `app_routes/admin_routes/`** — There are TWO admin-related directories: `admin/` (sidecar pattern) and `admin_routes/` (coordinators blueprint). This is confusing and non-standard.
-   [ ] **`shared/` package is a grab-bag** — Contains fixred logic, new_updater logic, decode_bytes, shared_classes. It's not clear what unifies these.
-   [ ] **`core/` package naming overlap** — `core/cookies.py` (test client) vs `app_routes/auth/cookie.py` (signing). These are related but separated.
-   [ ] **`utils/` as dumping ground** — `main_app/utils/` contains one `verify.py` file. `api_services/utils/` has an empty `__init__.py`. Route `utils/` has `routes_utils.py`. Multiple `utils` directories dilute the concept.

#### Recommendations:

1. [ ] Rename `su_services/` to `auth_services/` or `user_services/` with a deprecation alias
2. [ ] Rename `new_jobs/` to `jobs/` (update all imports accordingly)
3. [ ] Consolidate `admin/` and `admin_routes/` into a single structure
4. [ ] Split `shared/` into more focused packages (e.g., `wikitext/`, `redirects/`)
5. [ ] Consolidate cookie-related code
6. [ ] Reduce the number of `utils/` packages — aim for one or two at most

---

### 5. Test Coverage Gaps

**Priority**: High
**Impact**: Low confidence in refactoring, risk of regression bugs

#### Issues Found:

-   [ ] **No worker implementation tests** — The 8 workers in `new_jobs/workers/` have no unit tests for their actual logic (only infrastructure tests in `tests/unit/new_jobs/`).
-   [ ] **No API service tests** — `tests/unit/api_services/` has no test files (the directory only has `__pycache__`).
-   [ ] **14 `# pragma: no cover` exclusions** — Many are legitimate (network interactions, teardowns), but several in route handlers indicate complex error paths without test coverage.
-   [ ] **`stub_service` fixture is underutilized** — It exists in `conftest.py` but virtually no tests use it.
-   [ ] **No integration tests for OAuth flow** — The OAuth flow has no integration test coverage (though this is hard without a real MW instance).
-   [ ] **`test_new_jobs_utils.py` and `test_utils.py`** — Need to check if they actually test anything meaningful or are just placeholder files.
-   [ ] **No tests for `shared/new_updater/` complex logic** — The medical content updater has extensive wikitext processing with no test coverage.

#### Recommendations:

1. [ ] Write unit tests for each worker's core logic, mocking the MW API calls
2. [ ] Add unit tests for `api_services/` functions (especially `category.py`, `pages_api.py`, `query_api.py`)
3. [ ] Remove `# pragma: no cover` from route handlers and write tests for those error paths
4. [ ] Use the `stub_service` fixture to test job lifecycle end-to-end
5. [ ] Add property-based or golden-file tests for wikitext processing logic

---

### 6. Complex / Undocumented Wikitext Processing

**Priority**: Medium
**Impact**: High risk of bugs, difficult to maintain or extend

#### Issues Found:

-   [ ] **`MedWorkNew.py` uses complex regexes** — Multiple multi-line regex patterns with minimal explanation of what they match.
-   [ ] **Mixed language comments** — Some files in `shared/new_updater/` mix Arabic and English comments, reducing accessibility.
-   [ ] **No tests for `_work_on_text_md()`** — The core function of the medical updater has zero test coverage.
-   [x] **`fixred_worker.py` uses string replacement for wikilink correction** — The `_replace_links()` function uses `str.replace()` and `re.sub()` instead of `wikitextparser`, despite the project depending on `wikitextparser`. There's even a TODO in `duplicate_redirect/worker.py` (line 195) suggesting this migration.
-   [ ] **`_drugbox_work()` has deeply nested logic** — Multiple regex passes with opaque transformations.

#### Recommendations:

1. [ ] Refactor wikitext processing to use `wikitextparser` library (already a dependency) instead of raw regex
2. [ ] Add comprehensive tests for all wikitext transformations using golden-file testing
3. [ ] Document the regex patterns with inline comments explaining what wiki markup they match
4. [ ] Add a migration path to unify `fixred_worker.py` with `wikitextparser`

---

### 7. Configuration & Tooling Drift

**Priority**: Medium
**Impact**: Developer tooling may not work correctly

#### Issues Found:

-   [ ] **`pyproject.toml` has stale settings** — `src_paths = "ArWikiCats"` and `known_first_party = "ArWikiCats"` are clearly from a different project (copy-paste artifact).
-   [ ] **`[tool.isort]` section references `ArWikiCats`** — isort's `known_first_party` is set to a non-existent package, meaning isort may mis-sort imports.
-   [ ] **`mypy` is mentioned in CLAUDE.md** — but there's no `mypy` configuration in `pyproject.toml` or `mypy.ini`.
-   [ ] **`.env.example` exists** — but its location wasn't checked. Ensure it's up to date with all required env vars.

#### Recommendations:

1. [ ] Fix `pyproject.toml` — remove or correct `src_paths` and `known_first_party`
2. [ ] Add `mypy` configuration if it's used, or remove references to it
3. [ ] Audit `.env.example` against `main_settings.py` to ensure all env vars are documented

---

### 8. Potential Bugs

**Priority**: High
**Impact**: May cause runtime failures

#### Issues Found:

-   [ ] **Retry logic sleeps before first attempt** — `flask_app/main_app/api_services/mwclient_page.py::_edit_with_retry()` (lines 56-67) iterates through `_RETRY_DELAYS = (5, 15, 30)` and always sleeps for 5 seconds BEFORE making the first API call. The first attempt should not sleep.
-   [ ] **`raise e` instead of `raise`** — `flask_app/main_app/new_jobs/jobs_worker.py` (line 103) uses `raise e` which loses the original traceback. Should use bare `raise`.
-   [ ] **`resolve_redirects()` in `query_api.py` appears incomplete** — The function signature suggests it returns a dict, but the code shown was truncated. The `normalized` dict and `from_to` dict are used in `fixred_worker.py` — ensure they align.
-   [ ] **`_get_current_object()` usage** — `jobs_worker.py` (line ~110) captures `current_app._get_current_object()` which is a green flag for potential context issues.

#### Recommendations:

1. [ ] Fix `_edit_with_retry()` to skip the sleep on the first attempt
2. [ ] Clarify the category filtering logic with better variable names or comments
3. [ ] Change `raise e` to `raise` in `jobs_worker.py`
4. [ ] Audit `resolve_redirects()` return type alignment with its consumers
5. [ ] Consider passing the Flask app reference more safely to background threads

---

### 9. Frontend & Template Issues

**Priority**: Low
**Impact**: Aesthetic and minor functionality concerns

#### Issues Found:

-   [ ] **Hardcoded CDN URLs** — `base.html` uses CDN versions for Bootstrap, jQuery, DataTables, etc. with hardcoded version numbers. Update scripts require manual changes.
-   [ ] **`static_server` config usage** — Templates use `{{ static_server }}` for CDN resources, which is good, but it's mixed with `url_for('static', ...)` for local assets. Consider a consistent strategy.
-   [ ] **Mixed Bootstrap 5 and Font Awesome 5** — Uses both Bootstrap Icons (`bi-*`) and Font Awesome (`fas fa-*`). Consider consolidating.
-   [ ] **`_navbar.html` uses `current_user` and `is_authenticated`** — The template checks both `current_user` and `is_authenticated`, which are redundant. The context processor always sets both.
-   [ ] **Ace editor included globally** — `base.html` loads Ace editor on every page, but only a few templates use it. Consider conditional loading.

#### Recommendations:

1. [ ] Consider using SRI hashes for CDN resources, or bundle locally
2. [ ] Consolidate icon libraries (pick Bootstrap Icons or Font Awesome, not both)
3. [ ] Remove redundant checks in navbar template
4. [ ] Defer Ace editor loading to only the pages that need it

---

## Refactoring Roadmap

### Phase 1: Quick Wins

-   [x] Remove dead code: `get_template_pages_newapi()` from `query_api.py`
-   [ ] Fix `pyproject.toml` stale settings (`ArWikiCats` → correct values)
-   [ ] Fix `raise e` to `raise` in `jobs_worker.py`
-   [ ] Fix retry logic in `_edit_with_retry()` — don't sleep before first attempt
-   [x] Remove commented-out blueprint registrations in `admin/routes.py`
-   [ ] Clean up commented-out template code in `base_list2.html` and `base_details2.html`
-   [ ] Consolidate `coerce_encrypted()` into `decode_bytes.py` or vice versa

### Phase 2: Structural Improvements

-   [ ] **Fix layering violations in controllers**:
    -   [ ] Remove `JobRecord` imports from `new_jobs.py`
    -   [ ] Move `load_auth_payload()` to `su_services/`
    -   [ ] Replace direct `db.services` imports in routes with service-layer calls
-   [ ] **Rename `su_services/`** to `user_services/` (add deprecation shim)
-   [ ] **Rename `new_jobs/`** to `jobs/` (update all imports)
-   [ ] **Consolidate admin blueprints** — merge `admin/` and `admin_routes/`
-   [ ] **Remove or implement stub workers** — Either implement `add_r_column` and `add_unlinkedwikibase`, or remove them from the registry
-   [ ] **Unify `app.py` and `app1.py`** — Single entry point with env-based config selection
-   [ ] **Clean up the teardown handler** — Either implement or remove

### Phase 3: Major Refactoring (2+ weeks)

-   [ ] **Refactor wikitext processing**:
    -   [x] Migrate `fixred_worker.py` to use `wikitextparser` instead of `str.replace()`
    -   [ ] Add comprehensive tests for all wikitext transformation functions
    -   [ ] Document regex patterns in `MedWorkNew.py` and related files
    -   [ ] Consider extracting `shared/new_updater/` into a standalone package
-   [ ] **Add test coverage**:
    -   [ ] Unit tests for all 8 workers
    -   [ ] Unit tests for `api_services/` functions
    -   [ ] Integration tests for job lifecycle (using `stub_service`)
    -   [ ] Remove unnecessary `# pragma: no cover` annotations
    -   [ ] Golden-file tests for wikitext processing
-   [ ] **Refactor error handling**:
    -   [ ] Create a shared `@route_error_handler` decorator to reduce repetitive try/except patterns
    -   [ ] Standardize error responses across all routes
-   [ ] **Frontend modernization**:
    -   [ ] Consolidate icon libraries
    -   [ ] Add SRI hashes to CDN resources or bundle locally
    -   [ ] Conditional loading of Ace editor

---

## Risk Assessment

| Risk                                            | Likelihood | Impact   | Mitigation                                                                 |
| ----------------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------- |
| Breaking OAuth flow during refactoring          | Low        | Critical | Ensure auth-related tests pass; manual testing with a real MW instance     |
| Renaming modules breaks imports                 | Medium     | High     | Use grep-search to find ALL import references; add deprecation shims       |
| Wikitext regex changes produce different output | Medium     | High     | Golden-file tests with known input/output pairs before/after changes       |
| Background thread issues from refactoring       | Low        | High     | Keep worker lifecycle untouched until Phase 3; test with integration tests |
| Losing uncommitted work from old plans          | Low        | Low      | Preserve `docs/old_plans/` as-is during refactoring                        |

## Testing Strategy

1. **Before any refactoring**: Run full test suite to establish baseline (`python -m pytest tests/ -v`)
2. **After each Phase 1 change**: Run full test suite — these are small, safe changes
3. **After each Phase 2 change**: Run full test suite + manually verify the app starts without import errors
4. **Phase 3 testing**:
    - Wikitext changes: Use golden-file testing with real wiki markup samples
    - Worker tests: Mock `mwclient.Site` and test worker logic in isolation
    - New decorators: Test each error path explicitly
5. **Final validation**: Deploy to a staging Toolforge instance and run all job types

## Appendix: File-by-File Notes

### `flask_app/main_app/__init__.py`

-   **Strengths**: Clean factory pattern, good error handling, well-documented
-   **Issues**: Imports `active_coordinators` from `db.services` (layering violation); disabled teardown handler
-   **Priority**: Phase 2

### `flask_app/main_app/app_routes/new_jobs.py`

-   **Issues**: Imports `JobRecord` model directly; imports `db.services` directly; has `_can_manage_job()` business logic
-   **Priority**: Phase 2 (Critical)

### `flask_app/main_app/app_routes/fixred.py`

-   Clean, well-structured route handler. `_normalize_title()` extracted as pure function (good).

### `flask_app/main_app/app_routes/newupdater/route.py`

-   Clean, mirrors `fixred.py` pattern. Good separation.

### `flask_app/main_app/app_routes/auth/`

-   Well-structured OAuth module with `cookie.py`, `oauth.py`, `rate_limit.py` separation. Good.

### `flask_app/main_app/app_routes/admin/`

-   **Issues**: Routes import `db.services` directly; commented-out blueprint registrations
-   **Priority**: Phase 2

### `flask_app/main_app/config/`

-   **Strengths**: Excellent design — frozen dataclasses, singleton pattern, clear hierarchy
-   **Issues**: Minor — `Config.__init__()` re-assigns settings already set at class level (redundant)
-   **Priority**: Phase 2 (minor)

### `flask_app/main_app/api_services/`

-   **Issues**: `category.py` mixes API and filtering logic; `query_api.py` has dead function; `mwclient_page.py` retry bug
-   **Priority**: Phase 1 (retry bug), Phase 3 (refactor)

### `flask_app/main_app/db/`

-   **Strengths**: Clean model definitions, good service separation, `db_guard` decorator
-   **Minor**: `utils.py::db_guard` catches all exceptions — consider being more specific

### `flask_app/main_app/new_jobs/`

-   **Strengths**: Well-designed worker lifecycle; clean registry in `workers_list.py`
-   **Issues**: Two stub workers; `utils.py` is just one function; `__init__.py` is empty
-   **Priority**: Phase 2

### `flask_app/main_app/shared/`

-   **Issues**: Grab-bag package; complex undocumented regex logic; `fixred_worker.py` doesn't use wikitextparser
-   **Priority**: Phase 3

### `flask_app/main_app/su_services/`

-   **Issues**: Cryptic name; good functionality otherwise
-   **Priority**: Phase 2 (rename)

### `flask_app/main_app/core/`

-   Clean utilities. `cookies.py` (test client) could be in `tests/` instead.

### `flask_app/templates/`

-   Clean Bootstrap 5 templates with good inheritance. Minor issues: redundant CDN, dual icon libraries, global Ace editor.

### `tests/`

-   **Strengths**: Good conftest.py, session-scoped app, CSRF token fixture
-   **Issues**: Major gaps in worker, API, and wikitext tests; unused `stub_service` fixture
-   **Priority**: Phase 3

### `pyproject.toml`

-   **Issues**: Stale `ArWikiCats` references; no mypy config despite being mentioned
-   **Priority**: Phase 1

### `_works_files/`

-   Contains experimental/test scripts (`tree.py`, `tests_dirs.py`, `z.py`) and original PHP/Python reference code. Consider archiving to `_archive/` or removing if no longer needed.
-   **Priority**: Low

---

_Generated by Claude Refactoring Analyst after comprehensive codebase analysis._
