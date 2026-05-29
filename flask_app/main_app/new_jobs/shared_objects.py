""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

from ..new_jobs.base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "no_changes", "changed", "error"]
    newrevid: int = 0

    @property
    def has_changes(self) -> bool:
        return self.kind == "changed"

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Summary:
    scanned: int = 0
    changed: int = 0
    no_changes: int = 0
    missing: int = 0
    errors: int = 0
    total: int = 0
    skipped: Optional[int] = 0


@dataclass
class SharedworkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "Summary",
    "SharedworkerObject",
    "UpdaterOutcome",
]
