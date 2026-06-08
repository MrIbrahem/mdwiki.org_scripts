""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from typing import Optional

from ...base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class StepDetail:
    status: str = "pending"  # ["pending", "running", "completed", "failed", "skipped", "cancelled"]
    title: str = ""
    message: str = ""
    newrevid: Optional[int] = None  # Kept optional as some steps don't require this field


@dataclass
class Steps:
    load_page: StepDetail = field(default_factory=lambda: StepDetail(title="get page"))
    load_text: StepDetail = field(default_factory=lambda: StepDetail(title="Load page text"))
    add_empty_r_column: StepDetail = field(default_factory=lambda: StepDetail(title="Add empty R column"))
    add_r_column: StepDetail = field(default_factory=lambda: StepDetail(title="Add R column"))
    final_save: StepDetail = field(default_factory=lambda: StepDetail(title="Save page", newrevid=0))


@dataclass
class AddRColumnWorkerObject(WorkerObject):
    steps: Steps = field(default_factory=Steps)
    new_text: str = ""

    def set_step_status(self, step: str, status: str, message: str = "") -> None:
        """
        Updates the status and message of a specific step dynamically.
        """
        step_attr = getattr(self.steps, step, None)
        if step_attr:
            step_attr.status = status
            step_attr.message = message

    def set_steps_skipped(self) -> None:
        """
        Loops through all dataclass fields in steps and skips any pending ones.
        """
        for f in fields(self.steps):
            step = getattr(self.steps, f.name)
            if step.status == "pending":
                step.status = "skipped"


__all__ = [
    "AddRColumnWorkerObject",
]
