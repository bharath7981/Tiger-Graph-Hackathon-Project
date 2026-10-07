"""Tests for health check and system information endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "graphmind"


def test_system_info_endpoint():
    """Verify GET /api/v1/system/info returns valid metadata without leaking secrets."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "project_name" in data
    assert "backend_version" in data
    assert "configured_llm_provider" in data
    assert "vector_store" in data
    assert "graph_store" in data
    assert "environment" in data
    # Ensure no secrets leak
    assert "api_key" not in data
    assert "password" not in data
    assert "secret" not in data
