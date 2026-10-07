"""Unit and integration tests for Benchmark Engine and Value Analysis."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.evaluation.metrics import (
    compute_exact_match,
    compute_token_f1,
    compute_citation_metrics,
    evaluate_prediction,
)
from backend.app.evaluation.classifier import classify_question_complexity
from backend.app.evaluation.benchmark import benchmark_engine
from backend.app.evaluation.value_analysis import generate_agentic_value_analysis


client = TestClient(app)


def test_metrics_computations():
    """Validates exact match, token F1, and citation precision/recall metrics."""
    # 1. Exact Match
    assert compute_exact_match("Chen Ding", ["Chen Ding", "Ding Chen"]) == 1.0
    assert compute_exact_match("John Smith", ["Chen Ding"]) == 0.0

    # 2. Token F1
    f1 = compute_token_f1("The gold was won by Chen Ding in London", ["Chen Ding"])
    assert f1 > 0.0

    # 3. Citation metrics
    cites = compute_citation_metrics(["Q100", "Q200"], ["Q100", "Q300"])
    assert cites["hit_rate"] == 1.0
    assert cites["precision"] == 0.5
    assert cites["recall"] == 0.5
    assert cites["f1"] == 0.5


def test_question_complexity_classifier():
    """Validates 4-tier complexity classification."""
    # Level 4: Aggregation
    c4 = classify_question_complexity("How many biathlon events had more than 73 competitors?", "aggregation")
    assert c4["level"] == 4
    assert "Aggregation" in c4["label"]

    # Level 3: Temporal / Multi-hop
    c3 = classify_question_complexity("Who won gold in the event held immediately before 2016?", "temporal")
    assert c3["level"] == 3

    # Level 2: Relational
    c2 = classify_question_complexity("Which venue hosted Athletics at 2012 Summer Olympics?", "lookup")
    assert c2["level"] == 2

    # Level 1: Factoid
    c1 = classify_question_complexity("What was the date of the event?", "lookup")
    assert c1["level"] == 1


def test_benchmark_engine_run():
    """Runs a minimal 2-question benchmark and validates summary metrics."""
    summary = benchmark_engine.run_benchmark(limit=2, pipelines=["rag", "graphrag"])
    assert summary["total_questions"] == 2
    assert "rag" in summary["overall_metrics"]
    assert "graphrag" in summary["overall_metrics"]
    assert len(summary["detailed_results"]) == 2


def test_benchmark_api_endpoints():
    """Validates /api/v1/benchmark endpoints."""
    # 1. GET /api/v1/benchmark/questions
    resp = client.get("/api/v1/benchmark/questions?limit=5")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 5
    assert "complexity" in questions[0]
    assert "level" in questions[0]["complexity"]

    # 2. GET /api/v1/benchmark/summary
    summary_resp = client.get("/api/v1/benchmark/summary")
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "overall_metrics" in data

    # 3. GET /api/v1/benchmark/value-analysis
    val_resp = client.get("/api/v1/benchmark/value-analysis")
    assert val_resp.status_code == 200
    assert "markdown" in val_resp.json()
