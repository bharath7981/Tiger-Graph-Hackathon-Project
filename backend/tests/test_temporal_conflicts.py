"""Unit tests for temporal validity, competing claims, and conflict resolution service."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.temporal import TemporalInterval, CompetingClaim
from backend.app.services.conflict_resolution import conflict_service
from backend.app.agents.specialized.conflict_resolver import conflict_resolution_agent


client = TestClient(app)


def test_temporal_interval_and_competing_claim_models():
    """Validates temporal interval attributes and claim status transitions."""
    interval = TemporalInterval(valid_from="1988", valid_to="1992", is_current=False)
    assert not interval.is_current
    assert interval.valid_to == "1992"

    claim = CompetingClaim(
        claim_id="claim_01",
        entity="Weightlifting Men's 56 kg",
        attribute="gold_medalist",
        value="Mitko Grablev",
        authority_score=0.45,
        temporal_interval=interval,
        status="superseded",
    )
    assert claim.status == "superseded"
    assert claim.value == "Mitko Grablev"


def test_conflict_extraction_and_resolution_reallocation():
    """Validates detection and resolution of retrospective Olympic medal reallocations."""
    passage = (
        "Mitko Grablev of Bulgaria originally won the gold medal in the men's 56 kg event. "
        "However, he was disqualified after testing positive for furosemide. "
        "The gold medal was subsequently reallocated to Oksen Mirzoyan of the Soviet Union."
    )

    claims = conflict_service.extract_claims_from_text(passage)
    assert len(claims) >= 2

    # Check superseded vs active
    superseded = [c for c in claims if c.status == "superseded"]
    active = [c for c in claims if c.status == "active"]
    assert len(superseded) >= 1
    assert "Mitko Grablev" in superseded[0].value
    assert len(active) >= 1
    assert "Oksen Mirzoyan" in active[0].value

    # Resolve conflict
    report = conflict_service.resolve_conflicts(claims, entity_name="1988 Men's 56 kg Weightlifting")
    assert report.has_conflict
    assert report.conflict_type == "medal_reallocation"
    assert report.resolved_claim.value == "Oksen Mirzoyan"
    assert "reallocation" in report.resolution_rationale.lower()
    assert report.residual_uncertainty < 0.1


def test_conflict_resolution_unanimous():
    """Validates that unanimous claims are resolved with zero conflict and zero uncertainty."""
    claims = [
        CompetingClaim(
            claim_id="c1",
            entity="Athletics",
            attribute="gold_medalist",
            value="Chen Ding",
            authority_score=0.9,
            status="active",
        ),
        CompetingClaim(
            claim_id="c2",
            entity="Athletics",
            attribute="gold_medalist",
            value="Chen Ding",
            authority_score=0.85,
            status="active",
        ),
    ]
    report = conflict_service.resolve_conflicts(claims, entity_name="2012 Men's 20km walk")
    assert not report.has_conflict
    assert report.resolved_claim.value == "Chen Ding"
    assert report.residual_uncertainty == 0.0


def test_conflict_resolution_agent_run():
    """Validates specialized ConflictResolutionAgent execution."""
    res = conflict_resolution_agent.run({
        "question": "Who won gold in men's 56 kg weightlifting at 1988 Summer Olympics?",
        "evidence": [
            {
                "claim": "Mitko Grablev originally won gold but was disqualified. Oksen Mirzoyan was awarded gold.",
                "document_id": "Q12345",
            }
        ],
        "retrieved_chunks": [],
        "entity_name": "Weightlifting 1988",
    })

    assert res.success
    assert res.agent_name == "ConflictResolutionAgent"
    assert res.data["has_conflict"]
    assert res.data["resolved_claim"]["value"] == "Oksen Mirzoyan"


def test_conflict_api_endpoints():
    """Validates /api/v1/conflicts endpoints."""
    # 1. GET /api/v1/conflicts/examples
    resp = client.get("/api/v1/conflicts/examples")
    assert resp.status_code == 200
    examples = resp.json()
    assert len(examples) >= 3
    assert examples[0]["conflict_type"] == "medal_reallocation"

    # 2. POST /api/v1/conflicts/analyze
    analyze_resp = client.post(
        "/api/v1/conflicts/analyze",
        json={
            "text": "Angel Guenchev originally won gold in the 67.5 kg category. He was later stripped of the gold medal following a positive doping test, and Joachim Kunz was awarded the gold medal.",
            "entity_name": "Weightlifting 67.5 kg",
        },
    )
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()
    assert data["has_conflict"]
    assert data["resolved_claim"]["value"] == "Joachim Kunz"
