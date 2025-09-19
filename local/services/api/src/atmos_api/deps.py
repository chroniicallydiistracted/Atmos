"""Dependency providers for FastAPI."""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from .config import Settings
from .services.health import HealthService
from .services.timeline import TimelineService
from .services.triggers import TriggerService


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


def get_health_service(settings: Settings = Depends(get_settings)) -> HealthService:
    return HealthService(settings)


def get_timeline_service(settings: Settings = Depends(get_settings)) -> TimelineService:
    return TimelineService(settings)


def get_trigger_service(settings: Settings = Depends(get_settings)) -> TriggerService:
    return TriggerService(settings)


__all__ = [
    "get_settings",
    "get_health_service",
    "get_timeline_service",
    "get_trigger_service",
]
