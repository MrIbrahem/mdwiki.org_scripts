# workers — Background Job Worker Implementations

## Project Overview

Concrete worker implementations for the background job system. Each subdirectory contains a worker class that extends `BaseObjectsJobWorker` from the parent `new_jobs` package. Workers perform wiki maintenance operations (redirect fixing, reference normalization, content import, etc.) on mdwiki.org via the MediaWiki API.

### Structure

```
workers/
├── __init__.py                # Empty
├── add_r_column/
│   ├── __init__.py            # Exports add_r_column_worker_entry
│   ├── worker.py              # AddRColumnWorker — adds "R" column to Popular pages table
│   ├── objects.py             # AddRColumnWorkerObject, Steps, StepDetail dataclasses
│   └── add_rtt.py             # Table manipulation helpers (add_column, mark_rows, etc.)
├── add_unlinkedwikibase/
│   ├── __init__.py            # Exports add_unlinkedwikibase_worker_entry
│   └── worker.py              # AddUnlinkedwikibaseWorker — STUB (no actual logic)
├── create_redirects/
│   ├── __init__.py            # Exports create_redirects_worker_entry
│   ├── worker.py              # CreateRedirectsWorker — copies enwiki redirects to mdwiki
│   └── objects.py             # CreateRedirectsWorkerObject, custom Summary: RedirectsSummary
├── duplicate_redirect/
│   ├── __init__.py            # Exports duplicate_redirect_worker_entry
│   └── worker.py              # DuplicateRedirectWorker — fixes double redirects
├── find_and_replace/
│   ├── __init__.py            # Exports find_and_replace_worker_entry
│   ├── worker.py              # FindAndReplaceWorker — search-and-replace across pages
│   └── objects.py             # FindAndReplaceWorkerObject
├── fixred_all/
│   ├── __init__.py            # Exports fixred_all_worker_entry
│   └── worker.py              # FixredAllWorker — fixes redirect links in all mainspace pages
├── fixref/
│   ├── __init__.py            # Exports fixref_worker_entry
│   └── worker.py              # FixrefWorker — normalizes cite-template formatting
└── import_history/
    ├── __init__.py            # Exports import_history_worker_entry
    ├── worker.py              # ImportHistoryWorker — imports revision history from enwiki
    └── objects.py             # ImportHistoryWorkerObject, local UpdaterOutcome
```

Every subdirectory contains `__init__.py` (re-exports the entry function) and `worker.py`. Four workers (`add_r_column`, `create_redirects`, `find_and_replace`, `import_history`) have a local `objects.py` for specialized result dataclasses. The remaining four (`add_unlinkedwikibase`, `duplicate_redirect`, `fixred_all`, `fixref`) use `SharedworkerObject` from `shared_objects.py`.

## Key Components

### Worker Lifecycle (inherited from `BaseObjectsJobWorker`)

```
run()
├── before_run()          # Set DB status to "running"
├── process()             # Abstract — each worker implements this
└── after_run()           # Save results, update DB final status
```

Each worker implements:

-   `get_job_type() -> str` — Returns the job type key (e.g. `"fixref"`)
-   `process() -> Dict` — Main execution logic, returns result dict

### Object Type Distribution

| Worker                 | Object Type                   | Source              |
| ---------------------- | ----------------------------- | ------------------- |
| `add_unlinkedwikibase` | `SharedworkerObject`          | `shared_objects.py` |
| `duplicate_redirect`   | `SharedworkerObject`          | `shared_objects.py` |
| `fixred_all`           | `SharedworkerObject`          | `shared_objects.py` |
| `fixref`               | `SharedworkerObject`          | `shared_objects.py` |
| `add_r_column`         | `AddRColumnWorkerObject`      | Custom `objects.py` |
| `create_redirects`     | `CreateRedirectsWorkerObject` | Custom `objects.py` |
| `find_and_replace`     | `FindAndReplaceWorkerObject`  | Custom `objects.py` |
| `import_history`       | `ImportHistoryWorkerObject`   | Custom `objects.py` |

### Worker Implementations

#### add_r_column

Adds an "R" column to the `WikiProjectMed:WikiProject Medicine/Popular pages` wikitext table, marking articles that use `Template:RTT`. Uses `wikitextparser` for table parsing and a multi-step pipeline with per-step status tracking (`Steps` dataclass with 5 `StepDetail` fields). Has a helper module `add_rtt.py` for table column manipulation.

#### add_unlinkedwikibase

**Stub implementation** — intended to add unlinked Wikibase tags but contains no actual logic. Logs a message and sets status to `"completed"`. Requires implementation.

#### create_redirects

Copies redirects from English Wikipedia to mdwiki. For each target title: checks existence on mdwiki → fetches enwiki redirects via raw `requests.Session` POST to `en.wikipedia.org/w/api.php` → batch-checks which already exist → creates missing ones. Uses `@functools.lru_cache` for session reuse. Has `_valid_title()` filter to skip disambiguation, category, file, template, user, and Wikipedia namespace pages.

#### duplicate_redirect

Fixes double redirects on mdwiki (from `Special:DoubleRedirects`). Fetches all double redirects via `get_double_redirects()`, resolves chains to find root targets, then replaces each intermediate redirect with a direct `#REDIRECT [[final_target]]`. Uses `check_cancel_db_periodic()` for cooperative cancellation.

#### find_and_replace

Search-and-replace text across mdwiki pages. Two search modes: `newlist` (via `site.search()`) and `oldlist` (walk all pages). Has a `cap` feature to limit total modifications. Uses `UpdaterOutcome` from `shared_objects` and `check_cancel_db_periodic()`.

#### fixred_all

Fixes redirect links in all mdwiki mainspace pages. Walks non-redirect pages via `site.allpages()`, delegates to `work_on_text()` from `shared.fixref_shared.fixred_worker`. Uses `RunState()` for stateful redirect caching across pages.

#### fixref

Normalizes cite-template formatting. Accepts three input modes: explicit titles, category members (via `get_category_members_api`), or random N pages. Has a `MAX_PAGES_FIXREF = 20000` cap. Delegates to `fix_ref_template()` from `shared.fixref_shared.fixref_text_new`.

#### import_history

Imports revision history from English Wikipedia to mdwiki using `action=import`. For each title: checks existence → imports history → re-saves original text to preserve content. Falls back to saving at `User:{username}/{title}` if the main save fails. Defines its own `UpdaterOutcome` with different `kind` values (`"imported"`, `"imported_fallback"`) instead of extending the shared one.

### API Interaction Patterns

-   **mwclient** (`get_user_site`): All workers use authenticated mwclient for mdwiki operations
-   **Raw requests**: `create_redirects` uses `requests.Session` for enwiki API calls
-   **Service layer wrappers**: `edit_page`, `get_page_text`, `is_page_exists`, `is_pages_exists`, `create_page`, `import_page_from_wiki`, `get_category_members_api`, `get_double_redirects`, `get_template_pages`
-   **Direct mwclient**: `find_and_replace` uses `site.search()` and `site.allpages()` directly

### Error Handling

Consistent pattern across workers:

```python
try:
    result = self._process_one(title)
    # route to appropriate list based on result.kind
except Exception as e:
    logger.exception(f"Error processing {title}")
    self.result.pages_errors.append({"title": title, "error": str(e)})
```

-   Auth check: All workers validate `get_user_site()` result and fail early
-   Cancellation: `check_cancel_db_periodic()` used by workers that make edits
-   No retry logic anywhere

## Testing

```bash
pytest tests/unit/new_jobs/workers --cov=flask_app/main_app/new_jobs/workers
```

## Strengths

-   **Consistent worker pattern** — all workers follow the same `get_job_type()` / `process()` contract
-   **Dual object strategy** — simple workers reuse `SharedworkerObject`, complex ones get custom dataclasses
-   **Cooperative cancellation** — `check_cancel_db_periodic()` balances responsiveness with DB load
-   **Per-page error isolation** — failures on one page don't abort the entire job
-   **Progress persistence** — `_save_progress()` writes results to file during execution
-   **Batch API operations** — `create_redirects` and `fixred_all` use batched API calls for efficiency
-   **LRU caching** — `_enwiki_session()` in `create_redirects` avoids repeated session creation

## Weaknesses

-   **`add_unlinkedwikibase` is unimplemented** — dead code registered in `workers_list.py`
-   **Duplicate `UpdaterOutcome`** — `import_history/objects.py` defines its own with different `kind` values instead of extending the shared one
-   **Inconsistent `Summary` definitions** — `create_redirects` defines a custom `Summary` with extra fields; others import from `shared_objects`
-   **Hardcoded page title** — `add_r_column` hardcodes `WikiProjectMed:WikiProject Medicine/Popular pages` (not configurable via args)
-   **`tqdm` in background thread** — `add_rtt.py` uses `tqdm` progress bar (output goes to stderr, invisible to users)
-   **No retry logic** — transient API failures cause permanent page skips
-   **Mixed API approaches** — `create_redirects` uses raw `requests` for enwiki while others use mwclient

## Critical Issues

> **Warning**: Type annotation and safety concerns.

### 1. Missing `"skipped"` in Shared `UpdaterOutcome`

```python
# shared_objects.py:18
kind: Literal["missing", "skipped", "changed", "error"]
```

Multiple workers handle `"skipped"` outcomes via `record_page_outcome()`, but the shared `UpdaterOutcome` type doesn't include it. The type annotation is inaccurate.

### 2. `WorkerObject` Not in `__all__`

`base_worker_object.py` exports only `BaseObjectsJobWorker` in `__all__`, but `WorkerObject` is imported by every `objects.py`. Works due to explicit imports but is misleading.

### 3. Module-Level LRU Cache

```python
# create_redirects/worker.py:42
@functools.lru_cache(maxsize=1)
def _enwiki_session() -> requests.Session:
```

Session is shared across all job invocations in the same process. Fine for threading but the `maxsize=1` is unnecessary (single key).

### 4. Stub Worker Registered

`add_unlinkedwikibase` is registered in `workers_list.py` and visible in the UI but does nothing.

## Areas That Need Attention

-   [ ] Implement `add_unlinkedwikibase` or remove from registry
-   [ ] Unify `UpdaterOutcome` definitions — extend shared version to support all worker-specific `kind` values
-   [ ] Add `"skipped"` to shared `UpdaterOutcome.kind` Literal
-   [ ] Add retry logic for transient API failures
-   [ ] Add unit tests for all workers
-   [ ] Remove `tqdm` dependency from `add_rtt.py`
-   [ ] Make `add_r_column` page title configurable via job args
-   [ ] Export `WorkerObject` in `base_worker_object.py` `__all__`

## Improvement Plan

### Quick Wins

1. Add `"skipped"` to shared `UpdaterOutcome.kind` Literal type
2. Export `WorkerObject` in `base_worker_object.py` `__all__`
3. Remove or no-op the `tqdm` import in `add_rtt.py`
4. Mark `add_unlinkedwikibase` as inactive in the UI or implement basic logic

### Medium-Term

1. Consolidate `UpdaterOutcome` — make the shared version support `"imported"` and `"imported_fallback"` kinds, or use inheritance
2. Add retry decorator for transient mwclient/API errors
3. Add unit tests for each worker's `process()` method

### Long-Term

1. Standardize API interaction layer — use mwclient for all wiki operations (including enwiki in `create_redirects`)
2. Add integration tests with recorded API responses
3. Extract `add_r_column` page title to job arguments
4. Consider worker-level connection pooling (shared mwclient site per thread)

## Comprehensive Review

| Metric                   | Score                                             |
| ------------------------ | ------------------------------------------------- |
| **Overall Rating**       | **6/10**                                          |
| **Production Readiness** | Moderate (7 workers functional, 1 stub)           |
| **Consistency**          | Good (shared base class + result objects)         |
| **Code Quality**         | Moderate (some duplication, type annotation gaps) |
| **Test Coverage**        | Poor (no worker-level tests)                      |
| **Maintainability**      | 6/10                                              |
