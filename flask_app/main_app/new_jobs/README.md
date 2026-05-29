# new_jobs — Background Job System

## Project Overview

Thread-based background job processing system with a standardized worker lifecycle. Provides a base worker class (`BaseObjectsJobWorker`) and 8 concrete worker implementations for wiki operations.

### Structure

```
new_jobs/
├── __init__.py           # Empty
├── jobs_worker.py        # Job runner: start/cancel, thread management
├── workers_list.py       # Registry: job_type → entry function + templates
├── utils.py              # generate_result_file_name()
├── base_worker_object.py # BaseObjectsJobWorker ABC + WorkerObject dataclass
└── workers/
    ├── add_r_column/          # Add reference columns to pages
    ├── add_unlinkedwikibase/  # Add unlinked Wikibase items
    ├── create_redirects/      # Copy redirects from enwiki to mdwiki
    ├── duplicate_redirect/    # Handle duplicate redirects
    ├── find_and_replace/      # Find-and-replace across wiki pages
    ├── fixred_all/            # Fix all redirect links
    ├── fixref/                # Normalize cite templates
    └── import_history/        # Import revision history from enwiki
```

Each worker directory contains: `__init__.py`, `worker.py`, `objects.py` (result dataclass)

## Key Components

### jobs_worker.py — Job Runner

```python
def start_job_with_args(user, job_type, args) -> int:
    job = create_job(job_type, username)       # DB record
    cancel_event = threading.Event()           # Cancellation signal
    flask_app = current_app._get_current_object()
    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return job.id
```

-   `start_job()` / `start_job_with_args()` — Create DB record + spawn daemon thread
-   `cancel_job()` — Set local `Event` + mark DB as cancelled
-   `_runner()` — Thread target wrapping worker in Flask app context
-   `JOBS_CANCEL_EVENTS` — Dict mapping job_id → `threading.Event` (protected by Lock)

### base_worker_object.py — Worker Lifecycle

```
WorkerObject (dataclass)
├── status: str (pending/running/completed/failed/cancelled)
├── started_at, completed_at, cancelled_at, failed_at: str
├── error, error_type: Optional[str]
└── to_json() → Dict

BaseObjectsJobWorker (ABC)
├── before_run() → bool         # Set status to "running"
├── process() → Dict            # Abstract — implement actual work
├── after_run() → None          # Save results, update DB status
├── run() → Dict                # Orchestrates lifecycle
├── is_cancelled() → bool       # Check Event + DB status
└── _save_progress() → None     # Persist to JSON file
```

### Worker Types

| Worker                   | Job Type               | Description                                             |
| ------------------------ | ---------------------- | ------------------------------------------------------- |
| **fixref**               | `fixref`               | Normalize cite templates (lay source, title extraction) |
| **fixred_all**           | `fixred_all`           | Fix redirect links in all mainspace pages               |
| **find_and_replace**     | `find_and_replace`     | Search-based text replacement                           |
| **create_redirects**     | `create_redirects`     | Copy redirects from enwiki                              |
| **duplicate_redirect**   | `duplicate_redirect`   | Handle duplicate redirects                              |
| **import_history**       | `import_history`       | Import revision history via `action=import`             |
| **add_r_column**         | `add_r_column`         | Add reference columns                                   |
| **add_unlinkedwikibase** | `add_unlinkedwikibase` | Add Wikibase identifiers                                |

### workers_list.py — Registry

```python
jobs_targets_public = {
    "fixref": fixref_worker_entry,
    "fixred_all": fixred_all_worker_entry,
    # ... 8 total
}

JOB_TYPE_TEMPLATES_PUBLIC = {
    "fixref": "new_jobs_templates/fixref/details.html",
    # ... per-worker list + detail templates
}
```

## Strengths

-   **Clean abstract base class** with template method pattern
-   **Dual cancellation** — local `Event` (fast) + DB status (cross-process)
-   **Progress persistence** — results saved periodically during execution
-   **Standardized result objects** — per-worker dataclasses with summary + pages_processed
-   **Proper Flask app context** handling for background threads
-   **Error handling** at both worker and runner levels

## Weaknesses

-   **Daemon threads** — work lost on process restart, no job recovery
-   **No job queue** — all jobs run concurrently (no max limit)
-   **No connection pooling** — each worker creates its own `mwclient.Site`
-   **Duplicate Summary dataclasses** — similar structures per worker
-   **`is_cancelled()`** calls `db.session.refresh()` in tight loops

## Critical Issues

> **Warning**: No maximum concurrent job limit.

```python
# jobs_worker.py — every start_job() spawns a new daemon thread
thread = threading.Thread(target=_runner, daemon=True)
thread.start()
```

Under heavy load, this could spawn hundreds of threads and exhaust memory.

## Areas That Need Attention

-   [ ] Add maximum concurrent job limit
-   [ ] Add job recovery on restart (or document limitation)
-   [ ] Optimize `is_cancelled()` DB check frequency
-   [ ] Consolidate duplicate Summary dataclasses
-   [ ] Add graceful shutdown for running jobs

## Improvement Plan

### Quick Wins

1. Add `MAX_CONCURRENT_JOBS` setting with thread pool limit
2. Reduce `is_cancelled()` DB check frequency (every N iterations)

### Medium-Term

1. Consolidate Summary dataclasses into a shared base
2. Add connection pooling for mwclient.Site
3. Add job timeout (harakiri-style)

### Long-Term

1. Migrate to Celery with Redis broker for job persistence
2. Add job retry support
3. Add job scheduling (cron-like)

## Comprehensive Review

| Metric                   | Score                             |
| ------------------------ | --------------------------------- |
| **Overall Rating**       | **6.5/10**                        |
| **Production Readiness** | Moderate                          |
| **Architecture**         | Good (template method pattern)    |
| **Reliability**          | Low (daemon threads, no recovery) |
| **Maintainability**      | 7/10                              |
