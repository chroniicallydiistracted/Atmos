"""Pydantic models shared across routers."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: Literal["api"] = "api"
    status: Literal["ok", "error"] = "ok"
    ok: bool = True
    checks: Dict[str, str] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    layer: str
    count: int
    entries: List[str] = Field(default_factory=list)


class TriggerCatalogEntry(BaseModel):
    job: str
    description: str = ""


class TriggerCatalogResponse(BaseModel):
    jobs: List[TriggerCatalogEntry] = Field(default_factory=list)


class TriggerRequest(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    job: str
    status: Literal["ok"] = "ok"
    detail: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "HealthResponse",
    "TimelineResponse",
    "TriggerCatalogEntry",
    "TriggerCatalogResponse",
    "TriggerRequest",
    "TriggerResponse",
]
