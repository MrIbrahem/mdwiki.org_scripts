""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RunState:
    """Per-run mutable state.

    ``from_to``    maps redirect source -> resolved target.
    ``normalized`` maps the API-normalized title -> the input title (for
                   case-corrected matching when the page text uses a different
                   capitalization than the canonical title).
    """

    from_to: dict[str, str] = field(default_factory=dict)
    normalized: dict[str, str] = field(default_factory=dict)


__all__ = [
    "RunState",
]
