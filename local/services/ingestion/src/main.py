"""FastAPI entrypoint for the local ingestion service."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .atmos_ingestion.config import IngestionSettings
from .atmos_ingestion.service import IngestionService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Atmos Ingestion", version="0.1.0")
settings = IngestionSettings()
ingestion_service = IngestionService(settings)
app.state.settings = settings
app.state.ingestion_service = ingestion_service


class NexradTrigger(BaseModel):
    site: Optional[str] = Field(default=None, description="Radar site identifier (e.g. KTLX)")
    timestamp: Optional[datetime] = Field(
        default=None,
        description="UTC time to target. When omitted the service selects the freshest volume automatically.",
    )


class TriggerResponse(BaseModel):
    status: str
    detail: Dict[str, Any]


class GoesTrigger(BaseModel):
    band: Optional[int] = Field(
        default=None,
        ge=1,
        le=16,
        description="ABI channel number. Defaults to configured GOES_DEFAULT_BAND.",
    )
    sector: Optional[str] = Field(
        default=None,
        description="GOES sector shorthand (e.g. CONUS, FULL). Defaults to GOES_DEFAULT_SECTOR.",
    )
    timestamp: Optional[Union[datetime, Literal["latest"]]] = Field(
        default=None,
        description="UTC time to target. When omitted or set to 'latest', the freshest scan is ingested.",
    )


@app.post("/trigger/nexrad", response_model=TriggerResponse)
async def trigger_nexrad(payload: NexradTrigger):
    try:
        result = await ingestion_service.run_nexrad(payload.site, payload.timestamp)
        return TriggerResponse(status="ok", detail=result)
    except Exception as exc:  # pragma: no cover - surfaced via HTTP
        logger.exception("NEXRAD ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/trigger/goes", response_model=TriggerResponse)
async def trigger_goes(payload: GoesTrigger):
    try:
        result = await ingestion_service.run_goes(payload.band, payload.sector, payload.timestamp)
        return TriggerResponse(status="ok", detail=result)
    except Exception as exc:  # pragma: no cover - surfaced via HTTP
        logger.exception("GOES ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "object_store": settings.derived_bucket,
        "minio_endpoint": settings.cleaned_minio_endpoint,
        "nexrad_bucket": settings.nexrad_bucket,
    }


@app.get("/")
async def root():
    return {"service": "ingestion", "docs": "/docs"}


@app.on_event("shutdown")
async def shutdown_event():
    ingestion_service.close()
