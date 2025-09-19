"""Trigger endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path

from ..deps import get_trigger_service
from ..schemas import TriggerCatalogResponse, TriggerRequest, TriggerResponse
from ..services.triggers import TriggerInvocationError, TriggerService, UnknownJobError

router = APIRouter(prefix="/v1/trigger", tags=["trigger"])


@router.get("", response_model=TriggerCatalogResponse)
async def list_triggers(service: TriggerService = Depends(get_trigger_service)) -> TriggerCatalogResponse:
    return service.list_jobs()


@router.post("/{job}", response_model=TriggerResponse)
async def invoke_trigger(
    job: str = Path(..., description="Registered trigger identifier."),
    request: TriggerRequest | None = None,
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerResponse:
    parameters = request.parameters if request else {}
    try:
        return await service.trigger(job, parameters)
    except UnknownJobError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TriggerInvocationError as exc:
        raise HTTPException(status_code=502, detail=exc.detail) from exc


__all__ = ["router"]
