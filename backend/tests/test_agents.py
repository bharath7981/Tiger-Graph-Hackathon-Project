"""Unit and integration tests for Agentic GraphRAG harness and tools."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.agents.state import InvestigationState, TraceStep
from backend.app.agents.stopping import evaluate_stopping_criteria
from backend.app.agents.tools import execute_tool, REGISTERED_TOOLS
from backend.app.agents.graph import run_agentic_investigation


client = TestClient(app)


def test_investigation_state_and_trace_step():
    """Validates trace step data model and serialization."""
    step = TraceStep(
        step_number=1,
        action="Execute entity_link",
        tool="entity_link",
        input_summary="query string",
        output_summary="found 2 entities",
        latency_ms=12.5,
        tokens=45,
        reason="Initial extraction",
        evidence_ids=["Q100"],
    )
    dumped = step.model_dump()
    assert dumped["step_number"] == 1
    assert dumped["tool"] == "entity_link"
    assert "Q100" in dumped["evidence_ids"]


def test_stopping_criteria():
    """Validates stopping criteria triggers on max iterations, budget, and confidence."""
    # 1. Normal state - should not stop
    state: InvestigationState = {
        "iteration": 2,
        "max_iterations": 6,
        "total_tokens": 1500,
        "token_budget": 8000,
        "confidence": 0.5,
        "evidence": ["Some fact"],
    }
    stop, reason = evaluate_stopping_criteria(state)
    assert not stop

    # 2. Max iterations exceeded
    state["iteration"] = 6
    stop, reason = evaluate_stopping_criteria(state)
    assert stop
    assert "iteration limit" in reason.lower()

    # 3. Budget exceeded
    state["iteration"] = 2
    state["total_tokens"] = 9000
    stop, reason = evaluate_stopping_criteria(state)
    assert stop
    assert "budget" in reason.lower()

    # 4. Sufficient confidence
    state["total_tokens"] = 1000
    state["confidence"] = 0.95
    stop, reason = evaluate_stopping_criteria(state)
    assert stop
    assert "sufficient" in reason.lower()


def test_safe_tool_execution():
    """Ensures registered tools work and unregistered tools are rejected securely."""
    # Check registered tools catalog
    assert "entity_link" in REGISTERED_TOOLS
    assert "graph_traversal" in REGISTERED_TOOLS
    assert "vector_search" in REGISTERED_TOOLS
    assert "final_answer" in REGISTERED_TOOLS

    # 1. Unregistered tool rejection
    unregistered_res = execute_tool("arbitrary_bash_command", {"cmd": "rm -rf"})
    assert not unregistered_res.success
    assert "not authorized" in unregistered_res.summary

    # 2. Registered entity linking tool
    res = execute_tool("entity_link", {"question": "Who won the men's 20km walk at the 2012 Summer Olympics?"})
    assert res.success
    assert "2012 Summer" in str(res.data)


def test_run_agentic_investigation_e2e():
    """Tests the full LangGraph investigation loop on an Olympic query."""
    question = "Who won the men's 20km walk at the 2012 Summer Olympics?"
    result = run_agentic_investigation(
        question=question,
        question_id="pub-002",
        max_iterations=4,
        token_budget=5000,
    )

    assert result["question"] == question
    assert result["question_id"] == "pub-002"
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert result["steps"] >= 1
    assert len(result["trace"]) >= 1
    assert "entity_link" in result["tools_used"]
    assert result["latency_ms"] > 0


def test_agentic_api_endpoint():
    """Validates the POST /api/v1/agentic/query REST endpoint."""
    payload = {
        "question": "Which venue hosted Athletics at the 2012 Summer Olympics?",
        "question_id": "test-agentic-01",
        "max_iterations": 3,
        "token_budget": 4000,
    }
    response = client.post("/api/v1/agentic/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["question"] == payload["question"]
    assert data["question_id"] == "test-agentic-01"
    assert "answer" in data
    assert isinstance(data["trace"], list)
    assert len(data["trace"]) > 0
    assert "steps" in data
    assert "latency_ms" in data
