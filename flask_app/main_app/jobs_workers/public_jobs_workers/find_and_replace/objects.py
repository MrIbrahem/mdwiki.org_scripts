""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ....jobs_workers.base_worker_object import WorkerObject
from ...shared_objects import Summary

logger = logging.getLogger(__name__)


@dataclass
class FindAndReplaceWorkerObject(WorkerObject):
    text_find: str = ""
    text_replace: str = ""
    stopped: bool = False
    cap: Optional[int] = None

    summary: Summary = field(default_factory=Summary)

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_changed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)

    pages_missing: list[str] = field(default_factory=list)


__all__ = [
    "FindAndReplaceWorkerObject",
]
