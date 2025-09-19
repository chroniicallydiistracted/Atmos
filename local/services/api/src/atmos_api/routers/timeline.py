"""Timeline endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path

from ..deps import get_timeline_service
from ..schemas import TimelineResponse
from ..services.timeline import TimelineService

router = APIRouter(prefix="/v1/timeline", tags=["timeline"])


@router.get("/{layer}", response_model=TimelineResponse)
async def list_timeline(
    layer: str = Path(..., description="Layer identifier, e.g. goes, nexrad."),
    service: TimelineService = Depends(get_timeline_service),
) -> TimelineResponse:
    try:
        return await service.list_entries(layer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = ["router"]
