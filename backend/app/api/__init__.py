"""API routers registration."""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.system import router as system_router
from backend.app.api.rag import router as rag_router
from backend.app.api.graph import router as graph_router
from backend.app.api.agentic import router as agentic_router
from backend.app.api.benchmark import router as benchmark_router
from backend.app.api.conflicts import router as conflicts_router
from backend.app.api.adaptive import router as adaptive_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(rag_router)
api_router.include_router(graph_router)
api_router.include_router(agentic_router)
api_router.include_router(benchmark_router)
api_router.include_router(conflicts_router)
api_router.include_router(adaptive_router)

__all__ = ["api_router", "health_router", "rag_router", "graph_router", "agentic_router", "benchmark_router", "conflicts_router", "adaptive_router"]
