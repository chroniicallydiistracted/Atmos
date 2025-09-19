"""Health endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_health_service
from ..schemas import HealthResponse
from ..services.health import HealthService

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(service: HealthService = Depends(get_health_service)) -> HealthResponse:
    return await service.probe()


__all__ = ["router"]
