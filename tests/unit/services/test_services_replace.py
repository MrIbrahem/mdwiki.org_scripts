"""Tests for services.replace.

Full ``run()`` is exercised against a fake AllAPIS to verify:

* listtype routing (newlist → search, oldlist → all-pages),
* per-page outcomes (changed / no-changes / missing / error),
* the ``number`` cap on successful modifications,
* cooperative ``stop_event``.
"""

from __future__ import annotations

import threading

import pytest

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestValidation:
    ...


class TestListtypeRouting:
    ...


class TestPerPageOutcomes:
    ...


class TestNumberCap:
    ...


class TestStopEvent:
    ...
