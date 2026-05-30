You are a senior Python software architect and migration engineer.

Your task is to analyze the codebase inside the `flask_app` folder only and create a comprehensive migration plan to replace all usages of `_api` and `newapi` with `api_services` built on `mwclient`.

## Scope Restriction

ONLY analyze files and dependencies inside:

```text
flask_app/
```

Ignore:

-   external services
-   infrastructure repositories
-   deployment configs outside `flask_app`
-   unrelated monorepo packages
-   vendor libraries
-   generated files

All findings, dependency graphs, migration steps, and risk analysis must be limited to the `flask_app` directory.

---

## Context

Current implementations (`_api` and `newapi`) authenticate using username/password:

```python
username = os.getenv("WIKI_USERNAME")
password = os.getenv("WIKI_PASSWORD")
```

Target implementation (`api_services`) uses OAuth credentials with `mwclient`:

```python
access_token = coerce_encrypted(user.get("access_token"))
access_secret = coerce_encrypted(user.get("access_secret"))

site = mwclient.Site(
    settings.jobs.host,
    scheme="https",
    clients_useragent=user_agent,
    consumer_token=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_secret=access_secret,
)
```

---

## Example Migration Pattern

Example replacement of legacy `_api` usage with `mwclient`:

```diff
- titles = _api.NewApi().Get_All_pages(
-     start="!",
-     namespace=_NS_MAIN,
-     apfilterredir="nonredirects"
- )

+ titles = site.allpages(
+     start="!",
+     prefix=None,
+     namespace=_NS_MAIN,
+     filterredir="all",
+     minsize=None,
+     maxsize=None,
+     prtype=None,
+     prlevel=None,
+     limit=None,
+     dir="ascending",
+     filterlanglinks="all",
+     generator=True,
+     end=None,
+     max_items=None,
+     api_chunk_size=None,
+ )
```

Analyze semantic differences including:

-   `apfilterredir="nonredirects"` vs `filterredir="all"`
-   iterator behavior
-   pagination behavior
-   generator semantics
-   return type differences
-   lazy loading implications
-   performance implications
-   ordering guarantees
-   API chunking behavior

Document all required behavioral adjustments when replacing legacy calls.

---

## Objectives

Perform a deep architectural and implementation analysis of the `flask_app` codebase and produce a fully detailed migration strategy.

---

## Required Analysis

### 1. Full Dependency Mapping

Inside `flask_app` only:

Identify every file importing or referencing:

-   `_api`
-   `newapi`
-   authentication helpers
-   MediaWiki API wrappers
-   login/session logic
-   wiki service abstractions

Build a dependency graph showing:

-   direct imports
-   indirect dependencies
-   shared utilities
-   circular dependencies

Categorize usages by:

-   read operations
-   write operations
-   authentication
-   Flask routes
-   background jobs
-   Celery tasks
-   maintenance scripts
-   CLI commands
-   tests

---

### 2. API Surface Comparison

Compare `_api` / `newapi` against `api_services`:

-   method names
-   parameters
-   return formats
-   exception handling
-   retry behavior
-   session lifecycle
-   authentication flow
-   rate limiting behavior
-   pagination handling
-   upload/edit/token workflows

Create a compatibility matrix:

| Legacy API | api_services Equivalent | Migration Complexity | Notes |
| ---------- | ----------------------- | -------------------- | ----- |

---

### 3. Authentication Migration Analysis

Analyze:

-   all current username/password assumptions
-   environment variable usage
-   session persistence behavior
-   token refresh behavior
-   OAuth integration requirements

Explain:

-   how OAuth credentials are obtained
-   where credentials should be stored
-   encryption/decryption flow
-   multi-user implications
-   service account implications
-   worker/background-task authentication strategy

Identify all places requiring auth refactoring.

---

### 4. mwclient Integration Review

Analyze how `mwclient.Site` should be integrated across `flask_app`:

-   Flask request lifecycle integration
-   singleton vs per-request creation
-   thread safety
-   Celery/background worker compatibility
-   retry handling
-   timeout configuration
-   logging hooks
-   observability
-   caching opportunities

Recommend best practices.

---

### 5. Refactor Strategy

Produce a phased migration plan including:

-   preparation phase
-   abstraction layer creation
-   adapter/shim implementation
-   incremental replacement strategy
-   dead code removal
-   rollback strategy

For each phase include:

-   goals
-   exact files/modules affected
-   implementation details
-   risks
-   validation steps
-   deployment considerations

---

### 6. Backward Compatibility Plan

Determine whether temporary compatibility wrappers are needed.

If yes:

-   design adapter interfaces
-   provide example wrapper implementations
-   explain deprecation path
-   estimate removal timeline

---

### 7. Risk Assessment

Identify:

-   authentication risks
-   permission differences
-   concurrency issues
-   token expiration edge cases
-   API behavior differences
-   production deployment risks
-   testing gaps

Provide mitigation strategies.

---

### 8. Testing Strategy

Create a detailed testing plan covering:

-   unit tests
-   Flask integration tests
-   Celery/background task tests
-   authentication tests
-   OAuth failure scenarios
-   MediaWiki API mocking
-   regression testing
-   performance testing
-   staging validation
-   rollout verification

Include example test structures where useful.

---

### 9. Implementation Recommendations

Provide:

-   recommended architecture
-   service boundaries
-   reusable client factories
-   dependency injection strategy
-   error handling patterns
-   logging standards
-   retry standards
-   type safety improvements

---

### 10. Deliverables

Produce:

1. Executive summary
2. Dependency analysis
3. Migration architecture
4. Step-by-step implementation plan
5. Risk matrix
6. Testing strategy
7. Rollback strategy
8. Recommended code patterns
9. Technical debt identified
10. Estimated migration complexity by module

---

## Output Requirements

-   Be extremely detailed and technical.
-   Include concrete code examples where appropriate.
-   Reference specific files/modules/functions discovered during analysis.
-   Do not give generic advice.
-   Prioritize production-safe migration practices.
-   Highlight hidden edge cases and operational concerns.
-   Structure the response with clear headings and tables.
-   Assume this migration will be executed in a large production Flask production system with active users.

```

```
