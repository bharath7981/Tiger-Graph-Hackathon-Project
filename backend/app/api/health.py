"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "graphmind"


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """System health check endpoint."""
    return HealthResponse(status="ok", service="graphmind")
