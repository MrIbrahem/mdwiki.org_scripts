# Plan: Merge Old Jobs into New Jobs System

## Goal

Migrate 6 jobs from `flask_app/main_app/jobs/` into `flask_app/main_app/new_jobs/` using the `BaseJobWorker` pattern. Old `jobs/` folder stays untouched for reference.

## Jobs to Migrate

| #   | Job Type             | Old Worker                    | Args from Form                                      |
| --- | -------------------- | ----------------------------- | --------------------------------------------------- |
| 1   | `create_redirects`   | `workers/create_redirects.py` | `titles` (merged from title+titlelist)              |
| 2   | `duplicate_redirect` | `workers/fix_duplicate.py`    | _(no args)_                                         |
| 3   | `find_and_replace`   | `workers/find_and_replace.py` | `find`, `replace`, `listtype`, `number`             |
| 4   | `fixred_all`         | `workers/fixred_all.py`       | _(no args)_                                         |
| 5   | `fixref`             | `workers/fixref.py`           | `titles` (from titlelist), `category`, `number`     |
| 6   | `import_history`     | `workers/import_history.py`   | `titles` (merged from title+titlelist), `from_lang` |

---

## Per-Job Checklist (repeat for each job)

### Step 1: Create Worker Folder

Create `flask_app/main_app/new_jobs/workers/<job_type>/` with:

**`__init__.py`** — re-export the entry function:

```python
from .worker import <job_type>_worker_entry

__all__ = [
    "<job_type>_worker_entry",
]
```

**`worker.py`** — implement the worker class:

-   Class extends `BaseJobWorker`
-   `get_job_type()` returns `"<job_type>"`
-   `get_initial_result()` returns initial result dict with `status`, timestamps, `summary` counters, and any tracking lists
-   `process()` contains the migrated logic from the old `run()` function
-   Constructor takes `job_id`, `args`, `user`, `cancel_event`; stores `self.args` and calls `super().__init__()`
-   Use `get_user_site(self.user)` to get an authenticated `mwclient.Site`
-   Access `self.args` dict for form parameters (with defaults)
-   Check `self.is_cancelled()` between iterations
-   Call `self._save_progress()` at intervals via `self.get_priority(total)`
-   Entry function `<job_type>_worker_entry(job_id, user, cancel_event, args)` instantiates the class and calls `.run()`

### Step 2: Create Templates

Create `flask_app/templates/new_jobs_templates/<job_type>/` with:

**`list.html`** — extends `base_list2.html`:

-   Set `job_type = '<job_type>'`
-   Set `hide_start_button = '1'` (if the job has form args)
-   Block `list_title` / `list_headline`: human-readable name
-   Block `list_info`: form that POSTs to `url_for('new_jobs.start_job_with_args', job_type=job_type)`
    -   Form fields match the old template's inputs
    -   Use `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />`
    -   For jobs with `title` + `titlelist` fields: add JS to merge them into a single `titles` field before submit, OR use a single textarea named `titles`

**`details.html`** — extends `base_details2.html`:

-   Set `job_type = '<job_type>'`
-   Block `detail_title` / `detail_headline`: human-readable name
-   Block `job_summary`: show summary counters from `result_data.summary`
-   Block `job_details`: show any per-page tracking lists if applicable

### Step 3: Register in `workers_list.py`

Edit `flask_app/main_app/new_jobs/workers_list.py`:

1. Add import: `from .workers.<job_type>.worker import <job_type>_worker_entry`
2. Add to `jobs_targets_public`: `"<job_type>": <job_type>_worker_entry`
3. Add to `JOB_TYPE_TEMPLATES_PUBLIC`: `"<job_type>": "new_jobs_templates/<job_type>/details.html"`
4. Add to `JOB_TYPE_LIST_TEMPLATES_PUBLIC`: `"<job_type>": "new_jobs_templates/<job_type>/list.html"`

---

## Job-Specific Details

### 1. `create_redirects`

**Worker logic:** Copy `_process_one()` and helpers (`_enwiki_session`, `_valid_title`, `_enwiki_redirects_for`) from old worker. Replace `get_api()` with `get_user_site(self.user)`. The `api.MainPage(title).exists()` calls become `mwclient.Site` page operations. The enwiki query stays as `requests` (anonymous, no auth needed).

**Args:** `self.args.get("titles")` — list of title strings. The list template provides a single textarea named `titles` (one per line).

**Template form:** Single textarea for titles (one per line). Max 500 titles validation can be done in the worker.

**Initial result summary:** `scanned`, `target_missing`, `created`, `already_exists`, `skipped`, `errors`, `total`.

### 2. `duplicate_redirect`

**Worker logic:** Copy `_list_double_redirects()` and `_fix_one()` from old worker. Use `get_user_site(self.user)` for page read/write. The `NewApi().post_params()` call needs to be adapted to use `mwclient.Site` API directly or keep using `AllAPIS` via `get_api()`.

**Args:** None (no form inputs needed). Set `hide_start_button = '0'` to use the default "Start" button from `base_list2.html` which POSTs to `start_job` (no args).

**Template form:** None — just use the default start button.

**Initial result summary:** `scanned`, `fixed`, `unchanged`, `missing`, `skipped`, `errors`, `total`.

### 3. `find_and_replace`

**Worker logic:** Copy `_resolve_titles()` and `_process_one()` from old worker. Use `get_user_site(self.user)`.

**Args:** `self.args.get("find")`, `self.args.get("replace", "")`, `self.args.get("listtype", "newlist")`, `self.args.get("number")`.

**Template form:** Find/replace textareas, listtype dropdown, number input (same as old template).

**Initial result summary:** `scanned`, `changed`, `no_changes`, `missing`, `errors`, `total`, `stopped`, `cap`.

### 4. `fixred_all`

**Worker logic:** Copy `run_all()` logic and `_treat_page()` from old worker. Use `get_user_site(self.user)` for both `mwclient.Site` and pass to `work_on_text()`. The `get_api()` call for `AllAPIS` is also needed for `work_on_text()` — keep both.

**Args:** None. Use default start button.

**Template form:** None — just "Start All pages" button.

**Initial result summary:** `scanned`, `fixed`, `no_changes`, `missing`, `errors`, `total`.

### 5. `fixref`

**Worker logic:** Copy `_resolve_targets()` and main loop from old worker. Use `get_user_site(self.user)` and/or `get_api()` as needed for `CatDepth`, `Get_All_pages`, `MainPage`.

**Args:** `self.args.get("titles")` (list), `self.args.get("category")`, `self.args.get("number")`.

**Template form:** Titlelist textarea, category input, number input (same as old template).

**Initial result summary:** `scanned`, `fixed`, `no_changes`, `missing`, `errors`, `total`.

### 6. `import_history`

**Worker logic:** Copy `_process_one()` and main loop from old worker. Use `get_user_site(self.user)`.

**Args:** `self.args.get("titles")` (list), `self.args.get("from_lang", "en")`.

**Template form:** Single textarea for titles (one per line), from_lang input (defaults to "en").

**Initial result summary:** `scanned`, `imported`, `imported_fallback`, `no_revisions`, `missing`, `errors`, `total`, `from_lang`.

---

## Key Adaptation Notes

1. **API client:** Old workers use `get_api()` returning `AllAPIS`. New workers primarily use `get_user_site(self.user)` returning `mwclient.Site`. Some operations (like `CatDepth`, `NewApi().Search()`) may still need `AllAPIS` — keep `get_api()` available where needed.

2. **Args passing:** The new system passes form data as `args` dict via `request.form.to_dict()`. For jobs with `title` + `titlelist` fields, merge them into a single `titles` key in the list template (using JS or a single textarea).

3. **Progress reporting:** Old system uses `on_progress(done, total, message)` callback. New system uses `self._save_progress()` which persists the entire `self.result` dict. Update `self.result` counters directly.

4. **Cancellation:** Old system checks `stop_event.is_set()`. New system uses `self.is_cancelled()` which checks both the local `cancel_event` and the database.

5. **Status values:** Old uses `"done"`/`"error"`. New uses `"completed"`/`"failed"`/`"cancelled"`.

6. **Concurrent run protection:** The new system handles this at the DB level via `create_job()`. No need for `get_store().find_active()` checks.

---

## File Creation Summary

For each of the 6 jobs, create:

-   `flask_app/main_app/new_jobs/workers/<job_type>/__init__.py`
-   `flask_app/main_app/new_jobs/workers/<job_type>/worker.py`
-   `flask_app/templates/new_jobs_templates/<job_type>/list.html`
-   `flask_app/templates/new_jobs_templates/<job_type>/details.html`

Total: 24 new files.

Edit:

-   `flask_app/main_app/new_jobs/workers_list.py` (add 6 imports + 6 entries in each of 3 dicts)

---

## Progress

### Done

- [x] Created all 6 worker folders with `__init__.py` + `worker.py`
- [x] Created all 6 template folders with `list.html` + `details.html`
- [x] Registered all 6 jobs in `workers_list.py` (imports + 3 dicts)
- [x] Updated `index.html` — all 6 `url_for` links now point to `new_jobs.jobs_list`
- [x] Added `start_job()` to `jobs_worker.py` (delegates to `start_job_with_args` with empty args)
- [x] Added descriptive text to `duplicate_redirect/list.html` and `fixred_all/list.html`
- [x] Added `pages_processed` table + args JSON to `duplicate_redirect/details.html` and `fixred_all/details.html`
- [x] Created `/new_jobs/list` endpoint + `all_jobs_list.html` template (shows 100 recent jobs across all types)
- [x] Added "New Jobs" link to navbar in `header.html`
- [x] Added missing `api_services` functions: `get_page_text`, `search_pages`, `get_double_redirects`, `import_page_from_wiki`, `get_page_links`
- [x] Refactored `fixred_worker.py` to use `api_services` instead of `newapi`
- [x] Migrated all 6 workers to use `api_services` (no `_api`/`newapi` imports)
- [x] All workers append to `self.result["pages_processed"]` for detail tables

### Remaining

- [ ] Test the workers end-to-end

---

## Execution Order

1. `duplicate_redirect` (simplest — no args, no form)
2. `fixred_all` (no args, simple form)
3. `find_and_replace` (has args, straightforward)
4. `create_redirects` (has title list, enwiki API)
5. `import_history` (has title list, import API)
6. `fixref` (most complex args — titles/category/number)
