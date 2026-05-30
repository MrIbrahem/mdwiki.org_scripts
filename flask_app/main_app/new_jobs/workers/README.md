## Testing

```bash
pytest tests/unit/new_jobs/workers --cov=flask_app/main_app/new_jobs/workers
```

## Structure

```text
workers/
├── __init__.py           # Empty
├── base_worker_object.py # Base abstract worker class
├── jobs_worker.py        # Job runner
├── shared_objects.py     # Shared result dataclasses
├── utils.py              # Utility functions
└── workers/
    ├── add_r_column/
    ├── add_unlinkedwikibase/
    ├── create_redirects/
    ├── duplicate_redirect/
    ├── find_and_replace/
    ├── fixred_all/
    ├── fixref/
    └── import_history/
```

Each worker directory implements a specific job type; most contain a `worker.py` and optional `objects.py` for result structures.

## Key Components

- **jobs_worker.py — Job Runner**: Manages thread lifecycle and job registry.
- **base_worker_object.py — Worker Lifecycle**: Defines `BaseObjectsJobWorker` with lifecycle hooks.
- **shared_objects.py — Shared Result Objects**: Provides shared dataclasses like `Summary` and `UpdaterOutcome`.
- **workers_list.py — Registry**: Maps job types to worker callables and templates.

# Project Overview

## What the Project Does
The `workers` directory contains background job workers that process tasks for the mdwiki.org maintenance system. These workers handle operations like page edits, redirection fixes, and content updates via the MediaWiki API (`mwclient`). Each subfolder implements a specific job type (e.g., `find_and_replace/`, `create_redirects/`).

### Core Components
- **`BaseObjectsJobWorker`**: Abstract base class defining job lifecycle hooks (`before_run`, `process`, `after_run`).
- **Job Worker Classes**: Subclasses in subdirectories for specific tasks (e.g., `find_and_replace_worker`).
- **`jobs_worker.py`**: Central job runner managing thread-based execution.
- **`workers_list.py`**: Registry mapping job types to worker classes.

### Technologies Used
- Python 3.13
- `mwclient` (MediaWiki API client)
- `pwk` (threading utilities)
- `sqlalchemy` (job status tracking)
- `croniter` (scheduling)

---

## Architecture & Code Quality

### Code Structure
- Modular: Each job has its own subfolder with a dedicated worker class.
- Registry Pattern: `workers_list.py` dynamically loads workers for scalability.
- Layered Design: Follows controller-service-repository pattern.

### Design Patterns
- Factory Pattern: Workers instantiated via `workers_list.py`.
- Thread Pool: Jobs run in daemon threads to avoid blocking the main process.

### Maintainability
- High: Clear separation of concerns.
- Missing: Docstrings in worker files reduce readability.

### Readability
- Moderate: Code follows PEP8 but lacks detailed inline comments.

### Scalability
- Good: Thread-based architecture allows parallel job execution.

---

## Strengths
- Modular design simplifies adding new jobs.
- Reusable `BaseObjectsJobWorker` infrastructure.
- Defined workflow via lifecycle hooks.

---

## Weaknesses
- Documentation gaps in worker files.
- Limited error handling visibility.
- No centralized logging.

---

## Critical Issues
- Potential race conditions with concurrent MediaWiki edits.
- Missing rate limiting for API calls.
- Unclear token decryption practices.

---

## Areas Needing Attention
- No unit/integration tests for worker logic.
- Job parameters are hardcoded.
- Lack of monitoring for job health.

---

## Improvement Plan

### Quick Wins
1. Add docstrings to all worker classes/methods.
2. Standardize error handling with `try/except` blocks.
3. Implement centralized logging using the `logging` module.

### Medium-Term
1. Write unit tests for critical workflows (e.g., `create_redirects_worker`).
2. Refactor shared config into `workers_config.py`.
3. Add rate limiting for MediaWiki API calls.

### Long-Term
1. Introduce dependency injection for config/mwclient clients.
2. Add retry logic for API errors.
3. Consider async workers for high load.

---

## Comprehensive Review

## Overall Rating: 7/10
- Solid foundation but lacks testing and observability.

## Production Readiness
- Moderate: Requires testing and better error/rate limiting.

## Technical Debt
- Medium: Documentation gaps and potential concurrency risks.

## Risk Assessment
- **High**: Concurrent job conflicts (needs locking).
- **Medium**: Insufficient monitoring.

## Maintainability Score: 6/10
- Good organization but hindered by missing documentation and tests.

**Key Recommendations**:
1. Add rate limiting to prevent API abuse.
2. Implement proper error handling with retries.
3. Add unit tests for critical job workflows.

| Metric                   | Score                             |
| ------------------------ | --------------------------------- |
| **Overall Rating**       | **7/10**                          |
| **Production Readiness** | Moderate                          |
| **Architecture**         | Good (template method pattern)    |
| **Reliability**          | Low (daemon threads, no recovery) |
| **Maintainability**      | 6/10                              |
