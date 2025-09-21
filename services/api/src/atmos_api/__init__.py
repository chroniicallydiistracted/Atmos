"""Application factory and router wiring for the Atmos API."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .deps import get_settings
from .routers import health, timeline, triggers, legend, radar


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    settings = Settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(timeline.router)
    app.include_router(triggers.router)
    app.include_router(legend.router)
    app.include_router(radar.router)

    return app


app = create_app()

__all__ = ["create_app", "app", "get_settings"]
