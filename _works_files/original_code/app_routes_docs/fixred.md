# Analysis: fixred (Fix Redirects in Page Text)

## PHP: `php/fixred.php`

### Parameters

| Variable | Source  | Type            | Description                    |
| -------- | ------- | --------------- | ------------------------------ |
| `title`  | `$_GET` | text (required) | Page title to fix redirects in |

### Flow

1. Renders a GET form with a required `title` field
2. User enters a page title (or "all" for all pages)
3. On submit with logged-in user:
    - Sanitizes title: replaces `+` and spaces with `_`, then `rawurlencode`
    - Builds command: `fixred.py -page2:title save`
    - Executes via `do_py()`
4. Displays the result

### `get_results($title)` function

-   Calls `do_py()` with params:
    ```
    dir="c9", localdir="c9", pyfile="pwb.py", other="fixred.py -page2:title save"
    ```

## Python: `python/fixred.py`

### How it works

1. Reads CLI args:
    - `-page2:title` (URL-encoded) — single title
    - `-page:title` — single title
2. If the list is empty or "all" → fetches all non-redirect pages
3. For each page:
    - Gets page links (`Get_page_links`)
    - Finds redirect targets for each link (`find_redirects`)
    - Replaces old links with correct targets (`replace_links2`)
    - Saves the page with summary "Fix redirects"

### Mapping

| PHP              | Python CLI                |
| ---------------- | ------------------------- |
| `$_GET['title']` | `-page2:urlencoded_title` |

---

## Flask Migration Vision

### Current route: `flask_app/main_app/app_routes/fixred/__init__.py`

```
GET /fixred/?title=X  → process and display result
GET /fixred/          → render empty form
```

### Remaining work

1. **Direct `fixred.py` call**
    - Import `treat_page()` from `fixred.py`
    - Pass `title` directly instead of CLI args
2. **Handle "all"** — fetch all non-redirect pages
3. **Refactor `replace_links2`** to work independently of `sys.argv`
