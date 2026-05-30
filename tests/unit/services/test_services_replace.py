"""Tests for services.replace.

Full ``run()`` is exercised against a fake AllAPIS to verify:

* listtype routing (newlist → search, oldlist → all-pages),
* per-page outcomes (changed / skipped / missing / error),
* the ``number`` cap on successful modifications,
* cooperative ``stop_event``.

TODO: write tests
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestValidation: ...


class TestListtypeRouting: ...


class TestPerPageOutcomes: ...


class TestNumberCap: ...


class TestStopEvent: ...
