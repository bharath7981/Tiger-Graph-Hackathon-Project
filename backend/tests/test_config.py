"""Tests for configuration settings and abstractions."""

from backend.app.core.config import Settings
from backend.app.services.llm_provider import MockLLMProvider
from backend.app.graph.tigergraph_client import TigerGraphClient


def test_settings_initialization():
    settings = Settings()
    assert settings.PROJECT_NAME == "GraphMind — Adaptive Agentic GraphRAG"
    assert settings.BACKEND_PORT == 8000
    assert settings.API_PREFIX == "/api/v1"


def test_mock_llm_provider():
    provider = MockLLMProvider()
    res = provider.generate("Test prompt")
    assert res.provider == "mock"
    assert res.input_tokens > 0
    assert res.output_tokens > 0
    assert res.latency_ms >= 0
    assert len(res.text) > 0


def test_tigergraph_client_instantiation():
    tg = TigerGraphClient(host="http://localhost", restpp_port=9000, graph_name="OlympicGraph")
    assert tg.graph_name == "OlympicGraph"
    assert tg.base_url == "http://localhost:9000"
