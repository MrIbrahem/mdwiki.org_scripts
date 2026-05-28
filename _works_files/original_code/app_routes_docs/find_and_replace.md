# Analysis: replace (Find and Replace)

## PHP: `php/replace/index.php`

### Parameters

| Variable   | Source              | Type                | Description                                     |
| ---------- | ------------------- | ------------------- | ----------------------------------------------- |
| `listtype` | `$_GET` or `$_POST` | radio               | `newlist` (API search) or `oldlist` (all pages) |
| `find`     | `$_GET` or `$_POST` | textarea (required) | Text to find                                    |
| `replace`  | `$_GET` or `$_POST` | textarea (required) | Replacement text                                |
| `number`   | `$_GET` or `$_POST` | number              | Max number of replacements                      |

### Authorization

-   Authorized users only: `Doc James`, `Mr. Ibrahem`
-   Unauthorized users see "Access denied"

### Flow — File-Based Mechanism

1. Renders a POST form with:
    - `find` (textarea) — search text
    - `replace` (textarea) — replacement text
    - `number` — max replacements
    - `listtype` — `newlist` or `oldlist`
2. On submit with authorized user:
    - Generates `$nn` (random integer)
    - **Writes to files:**
        - `replace/find/{nn}/find.txt` ← `$find`
        - `replace/find/{nn}/replace.txt` ← `$replace`
        - `replace/find/{nn}/info.json` ← `{find, replace, number, listtype, nn}`
    - Displays link: `replace-log.php?id={nn}`

### Key Note

This is the **only** PHP file that writes parameters to files instead of passing them directly to the bot. The bot (`find_replace_bot`) runs as a separate process and reads from these files.

## Python: `python/find_replace_bot/`

### File Structure

| File         | Role                                                       |
| ------------ | ---------------------------------------------------------- |
| `bot.py`     | Gets job list from directories, runs `do_one_job` for each |
| `one_job.py` | Executes the find-and-replace for a single job             |

### How it works

1. `bot.py::get_jobs()`:
    - Reads subdirectories in `replace/find/`
    - Skips directories containing `done.txt`
2. `bot.py::main()`:
    - For each job: calls `one_job.do_one_job(nn)`
3. `one_job.py::do_one_job(nn)`:
    - Reads `info.json`, `find.txt`, `replace.txt` from `replace/find/{nn}/`
    - Determines titles: API search (if `newlist`) or all pages
    - For each page: replaces text and saves
    - Writes `log.txt`, `text.txt`, and `done.txt`

### Mapping

| PHP Form   | Storage Location        | Consumer                               |
| ---------- | ----------------------- | -------------------------------------- |
| `find`     | `find/{nn}/find.txt`    | `one_job.get_find_and_replace()`       |
| `replace`  | `find/{nn}/replace.txt` | `one_job.get_find_and_replace()`       |
| `number`   | `find/{nn}/info.json`   | `one_job.do_one_job()` → `max_numbers` |
| `listtype` | `find/{nn}/info.json`   | `one_job.get_titles()`                 |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/replace/__init__.py`

```
GET  /replace/  → render form
POST /replace/  → accept and process
```

### Remaining work — Major Refactor Needed

1. **Pass data directly** instead of the file-based system

    - Import `do_one_job` or refactor it to accept data directly:
        ```python
        def do_replace(find, replace, number, listtype):
            # instead of reading from files
        ```
    - Remove dependency on `work_dir` and temp directories

2. **Job tracking system**

    - Replace random `{nn}` with a proper task ID
    - Store status in a database instead of `done.txt`, `log.txt`

3. **Sync vs async execution**

    - Large jobs (oldlist = all pages) need background workers
    - Small jobs (newlist with few results) can run synchronously

4. **Stop mechanism**

    - Replace `stop.txt` with an API-based stop endpoint

5. **Authorization**
    - Integrate with Flask authentication system
