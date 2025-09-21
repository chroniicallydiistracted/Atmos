"""WSGI module for the Atmos API service."""
from __future__ import annotations

from .atmos_api import create_app

app = create_app()


__all__ = ["app", "create_app"]
