"""Domain types for the in-process job runtime."""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

JOBS_PATH: Path = Path(settings.paths.jobs_path)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Job:
    """A single tool invocation tracked across its lifecycle.

    The lifecycle is ``pending → running → done | error``. Termination via
    :attr:`stop_event` is cooperative: services check it and decide where to
    cut off.
    """

    id: str
    tool: str
    submitted_by: str = ""
    params: dict = field(default_factory=dict)
    status: str = "pending"
    progress: dict = field(default_factory=lambda: {"done": 0, "total": 0})
    log: deque = field(default_factory=lambda: deque(maxlen=settings.jobs.jobs_log_lines))
    result: Any = None
    error: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    stop_event: Event = field(default_factory=Event)

    def to_dict(self) -> dict:
        """JSON-safe view used by the polling endpoint."""

        return {
            "id": self.id,
            "tool": self.tool,
            "submitted_by": self.submitted_by,
            "params": self.params,
            "status": self.status,
            "progress": dict(self.progress),
            "log": list(self.log),
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_json(json_data: dict[str, any]):
        """ """
        json_data["created_at"] = (
            datetime.fromisoformat(json_data.get("created_at")) if json_data.get("created_at") else _now()
        )
        json_data["updated_at"] = (
            datetime.fromisoformat(json_data.get("updated_at")) if json_data.get("updated_at") else _now()
        )

        json_data.pop("stop_event", None)
        return Job(**json_data)

    def dump(self) -> None:
        """
        save job to_dict to json file
        """
        try:
            with open(JOBS_PATH / f"{self.id}.json", "w") as f:
                json.dump(self.to_dict(), f)
        except Exception:
            logger.exception(f"Error saving job {self.id} to file.")


__all__ = ["Job"]
