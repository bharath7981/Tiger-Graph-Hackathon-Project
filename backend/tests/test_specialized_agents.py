"""Unit tests for specialized investigation agents and evidence intelligence service."""

import pytest
from backend.app.agents.specialized import (
    entity_linking_agent,
    graph_traversal_agent,
    similarity_retrieval_agent,
    evidence_evaluation_agent,
    multihop_reasoning_agent,
)
from backend.app.services.evidence import (
    validate_citations,
    detect_contradictions,
    compute_evidence_coverage,
    compute_groundedness_score,
    evaluate_evidence_intelligence,
)


def test_evidence_service_citation_validation():
    """Validates extraction and segregation of valid vs hallucinated citations."""
    answer = "The gold medal was won by Chen Ding [Q1050909], but another competitor cited was [Q99999999]."
    available_doc_ids = ["Q1050909", "Q26233122"]

    valid, hallucinated = validate_citations(answer, available_doc_ids)
    assert "Q1050909" in valid
    assert "Q99999999" in hallucinated


def test_evidence_service_coverage_and_groundedness():
    """Validates keyword coverage and answer groundedness metrics."""
    question = "Who won the men's 20km walk at the 2012 Summer Olympics?"
    evidence = [
        {"claim": "In 2012 Summer Olympics, men's 20km walk was won by Chen Ding [Q1050909]"},
    ]

    coverage = compute_evidence_coverage(question, evidence)
    assert coverage > 0.5

    answer = "Chen Ding won the men's 20km walk in 2012 [Q1050909]."
    evidence_texts = [evidence[0]["claim"]]
    groundedness = compute_groundedness_score(answer, evidence_texts)
    assert groundedness >= 0.7


def test_evidence_intelligence_consolidated():
    """Validates overall evidence intelligence evaluation."""
    question = "Which venue hosted Athletics in 2012?"
    answer = "The Olympic Stadium hosted Athletics in 2012 [Q100]."
    evidence_items = [{"text": "Athletics in 2012 was hosted at the Olympic Stadium [Q100]"}]
    available_docs = ["Q100"]

    report = evaluate_evidence_intelligence(question, answer, evidence_items, available_docs)
    assert report.is_sufficient
    assert len(report.hallucinated_citations) == 0
    assert "Q100" in report.valid_citations


def test_specialized_entity_linking_agent():
    """Tests EntityLinkingAgent extraction and schema mapping."""
    res = entity_linking_agent.run({
        "question": "According to the corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors?"
    })
    assert res.success
    assert res.agent_name == "EntityLinkingAgent"
    assert "2018 Winter" in res.data["extracted_list"]
    assert "Biathlon" in res.data["extracted_list"] or "biathlon" in str(res.data)


def test_specialized_similarity_retrieval_agent():
    """Tests SimilarityRetrievalAgent top-k search in ChromaDB."""
    res = similarity_retrieval_agent.run({
        "query": "biathlon 2018 Winter Olympics",
        "top_k": 3,
    })
    assert res.success
    assert res.agent_name == "SimilarityRetrievalAgent"
    assert len(res.data["chunks"]) > 0
    assert len(res.evidence_ids) > 0


def test_specialized_evidence_evaluation_agent():
    """Tests EvidenceEvaluationAgent sufficiency calculation."""
    res = evidence_evaluation_agent.run({
        "question": "Who won the men's 20km walk at the 2012 Summer Olympics?",
        "evidence": [{"claim": "Chen Ding won men's 20km walk in 2012", "document_id": "Q1050909"}],
        "retrieved_chunks": [{"text": "Chen Ding took gold in London 2012", "document_id": "Q1050909"}],
    })
    assert res.success
    assert res.agent_name == "EvidenceEvaluationAgent"
    assert "confidence" in res.data
    assert "is_sufficient" in res.data


def test_specialized_multihop_reasoning_agent():
    """Tests MultiHopReasoningAgent grounded synthesis and citation tagging."""
    res = multihop_reasoning_agent.run({
        "question": "Who won gold in the 2012 walk event?",
        "evidence": [{"claim": "Chen Ding won gold in 2012 20km walk", "document_id": "Q1050909"}],
        "retrieved_chunks": [],
        "citations": ["Q1050909"],
    })
    assert res.success
    assert res.agent_name == "MultiHopReasoningAgent"
    assert "answer" in res.data
    assert len(res.data["answer"]) > 0
