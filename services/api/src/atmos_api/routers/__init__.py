"""Router collection for the Atmos API."""
from __future__ import annotations

from . import health, timeline, triggers, radar, legend  # type: ignore

__all__ = ["health", "timeline", "triggers", "radar", "legend"]
