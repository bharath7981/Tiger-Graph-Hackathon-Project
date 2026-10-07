"""System information endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.graph.tigergraph_client import tigergraph_client

router = APIRouter(prefix="/system", tags=["System"])


class SystemInfoResponse(BaseModel):
    project_name: str
    backend_version: str
    configured_llm_provider: str
    configured_llm_model: str
    vector_store: str
    graph_store: str
    environment: str
    graph_connected: bool


@router.get("/info", response_model=SystemInfoResponse)
def get_system_info() -> SystemInfoResponse:
    """Returns runtime system configuration and component status without exposing secrets."""
    return SystemInfoResponse(
        project_name=settings.PROJECT_NAME,
        backend_version=settings.BACKEND_VERSION,
        configured_llm_provider=settings.LLM_PROVIDER,
        configured_llm_model=settings.LLM_MODEL,
        vector_store=settings.VECTOR_STORE_PROVIDER,
        graph_store=settings.GRAPH_STORE_PROVIDER,
        environment=settings.ENVIRONMENT,
        graph_connected=tigergraph_client.is_connected(),
    )
