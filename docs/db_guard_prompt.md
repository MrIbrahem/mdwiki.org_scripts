### Improved Prompt

Analyze all database-accessing functions in `flask_app/main_app/db/services`.

#### Objective

Ensure every database interaction is protected either by:

1. Existing `try/except` handling,
2. The `@db_guard` decorator, or
3. Caller-level exception handling when appropriate.

#### Instructions

1. **Identify all functions that interact with the database** within `flask_app/main_app/db/services`.

2. For each function:

    - If the function already contains a `try/except` block, **skip it**.
    - If the function is already decorated with `@db_guard`, **skip it**.

3. For functions that are not protected:

    - Find all usages/call sites of the function throughout the codebase.
    - Determine whether every call site is already wrapped in appropriate `try/except` handling.
    - If all usages are protected, **skip the function**.

4. For unprotected functions with unprotected usages:

    - **If the function is called only 1–2 times:**

        - Add `try/except` protection at each call site.
        - Follow the surrounding code style for logging, flashing messages, and fallback values.
        - Example:

        ```python
        try:
            coordinators = admin_service.list_coordinators()
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to list coordinators.")
            flash("Unable to list coordinators.", "danger")
            coordinators = []
        ```

    - **If the function is called 3 or more times:**

        - Add a `@db_guard` decorator to the service function instead of modifying multiple callers.
        - Choose an appropriate `default_return` value based on the function's return type.
        - Provide a clear, user-friendly error message.
        - Example:

        ```python
        @db_guard(
            default_return=[],
            msg="Failed to load active coordinators."
        )
        def active_coordinators() -> list[str]:
            """Get a list of active coordinator usernames from the database."""
            records = (
                db.session.query(AdminUserRecord)
                .filter(AdminUserRecord.is_active)
                .all()
            )
            return [u.username for u in records]
        ```

#### Requirements

-   Do not change business logic.
-   Preserve existing return types and function signatures.
-   Use defensive exception handling only where needed.
-   Match existing project conventions for logging, flash messages, and fallback values.
-   Before making changes, report:

    -   The function name.
    -   Whether it is already protected.
    -   Number of usages found.
    -   Recommended action (`skip`, `add try/except`, or `add @db_guard`).

-   After analysis, implement the recommended changes and show the resulting diffs.
