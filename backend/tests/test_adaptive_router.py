"""Tests for Adaptive Router pipeline and API endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.pipelines.adaptive import adaptive_router, AdaptiveResult

client = TestClient(app)


def test_adaptive_classify_endpoint():
    """Validates pre-flight classification across complexity tiers."""
    # Level 1: Factoid
    res1 = client.post(
        "/api/v1/adaptive/classify",
        json={"question": "What is the capital of France?"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["level"] == 1
    assert data1["recommended_pipeline"] == "Baseline RAG"
    assert data1["is_conflict_suspected"] is False

    # Level 2: Relational (venue/sport)
    res2 = client.post(
        "/api/v1/adaptive/classify",
        json={"question": "What events took place at the venue Sydney International Shooting Centre?"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["level"] == 2
    assert data2["recommended_pipeline"] == "GraphRAG"

    # Level 3: Temporal / Multi-hop
    res3 = client.post(
        "/api/v1/adaptive/classify",
        json={"question": "Who won gold at the Games held immediately before 2016?"},
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["level"] == 3
    assert data3["recommended_pipeline"] == "Agentic GraphRAG"

    # Level 4: Aggregation
    res4 = client.post(
        "/api/v1/adaptive/classify",
        json={"question": "How many sailing events had more than 46 competitors?"},
    )
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["level"] == 4
    assert data4["recommended_pipeline"] == "Agentic GraphRAG"

    # Conflict question
    res5 = client.post(
        "/api/v1/adaptive/classify",
        json={"question": "Who was stripped of the medal due to doping and reallocated?"},
    )
    assert res5.status_code == 200
    data5 = res5.json()
    assert data5["is_conflict_suspected"] is True


def test_adaptive_router_level1_execution():
    """Level 1 query should route to RAG and show token/latency savings."""
    res = adaptive_router.route_and_execute(
        question="Who was the flag bearer for Greece in 2004?",
        question_id="test-001",
    )
    assert isinstance(res, AdaptiveResult)
    assert res.chosen_paradigm == "rag"
    assert res.complexity_level == 1
    assert res.actual_tokens > 0
    assert len(res.answer) > 0
    assert res.routing_rationale != ""


def test_adaptive_router_level2_execution():
    """Level 2 query should route to GraphRAG with ultra-low latency and tokens."""
    res = adaptive_router.route_and_execute(
        question="Which venue hosted Archery at the 2012 Summer Olympics?",
        question_id="test-002",
    )
    assert isinstance(res, AdaptiveResult)
    assert res.chosen_paradigm == "graphrag"
    assert res.complexity_level == 2
    assert res.actual_tokens > 0
    assert res.tokens_saved > 0  # GraphRAG uses ~100 tokens vs 512 reference
    assert res.cost_efficiency_multiplier >= 1.0


def test_adaptive_router_level3_execution():
    """Level 3 temporal query should route to Agentic GraphRAG."""
    res = adaptive_router.route_and_execute(
        question="Who won the event held immediately before 2016?",
        question_id="test-003",
    )
    assert isinstance(res, AdaptiveResult)
    assert res.chosen_paradigm == "agentic"
    assert res.complexity_level == 3
    assert len(res.answer) > 0


def test_adaptive_override_execution():
    """Manual override should force chosen paradigm regardless of complexity."""
    res = adaptive_router.route_and_execute(
        question="Who won the race?",
        override_paradigm="graphrag",
    )
    assert res.chosen_paradigm == "graphrag"
    assert "override" in res.routing_rationale.lower()


def test_api_adaptive_query_endpoint():
    """API endpoint /api/v1/adaptive/query returns complete payload."""
    response = client.post(
        "/api/v1/adaptive/query",
        json={"question": "What events were hosted at Maracanã Stadium in 2016?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "chosen_paradigm" in data
    assert "complexity_level" in data
    assert "routing_rationale" in data
    assert "tokens_saved" in data
    assert "cost_efficiency_multiplier" in data
    assert "answer" in data
