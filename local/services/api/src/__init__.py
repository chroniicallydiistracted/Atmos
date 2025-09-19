"""Public entry point for the Atmos API package."""
from __future__ import annotations

from .atmos_api import app, create_app

__all__ = ["app", "create_app"]
