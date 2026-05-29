""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ....new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class Summary:
    scanned: int = 0
    changed: int = 0
    skipped: int = 0
    errors: int = 0
    total: int = 0


@dataclass
class AddUnlinkedWikibaseWorkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "AddUnlinkedWikibaseWorkerObject",
]
