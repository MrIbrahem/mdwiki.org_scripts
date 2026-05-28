# Analysis: dup (Fix Duplicate Redirects)

## PHP: `php/dup.php`

### Parameters

| Variable | Source   | Type          | Description                                    |
| -------- | -------- | ------------- | ---------------------------------------------- |
| `start`  | `$_POST` | submit button | Triggers the job (name="start", value="start") |

### Flow

1. Renders an HTML form with a single "start" button
2. If user is not logged in → login link instead of button
3. On POST with `start` and logged-in user:
    - Executes shell: `toolforge jobs run fixduplict --image python3.9 --command "python3 fix_duplicate.py save"`

## Python: `python/fix_duplicate.py`

### How it works

1. Queries the MediaWiki API for the `DoubleRedirects` list
2. For each double redirect:
    - Checks if the page exists
    - Compares current text with the new redirect text
    - Saves the page with summary "fix duplicate redirect to [[target]]"
3. CLI arguments:
    - `save` — actually save
    - Without `save` — dry run
    - `-offset:N` — start from a specific index

### Mapping

| PHP                        | Python CLI                       |
| -------------------------- | -------------------------------- |
| `$_POST['start']` (button) | triggers `fix_duplicate.py save` |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/dup/__init__.py`

```
GET  /dup/  → render form
POST /dup/  → accept start
```

### Remaining work

1. **Direct `fix_duplicate.py` call** instead of `shell_exec`
    - Import `main()` or `fix_dup()` from `fix_duplicate.py`
    - Pass data directly instead of CLI args
2. **Authentication** (Flask-Login / session)
    - Currently: `request.values.get("global_username")` as placeholder
3. **Live result display** (WebSocket or polling for job status)
