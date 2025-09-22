"""Pydantic models shared across routers."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: Literal["api"] = "api"
    status: Literal["ok", "error"] = "ok"
    ok: bool = True
    checks: dict[str, str] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    layer: str
    count: int
    entries: list[str] = Field(default_factory=list)


class TriggerCatalogEntry(BaseModel):
    job: str
    description: str = ""


class TriggerCatalogResponse(BaseModel):
    jobs: list[TriggerCatalogEntry] = Field(default_factory=list)


class TriggerRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    job: str
    status: Literal["ok"] = "ok"
    detail: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "HealthResponse",
    "TimelineResponse",
    "TriggerCatalogEntry",
    "TriggerCatalogResponse",
    "TriggerRequest",
    "TriggerResponse",
]
