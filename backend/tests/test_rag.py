"""Tests for baseline RAG pipeline and endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.pipelines.rag import BaselineRAG, baseline_rag
from backend.app.models.rag import RetrievedChunk, RAGResult

client = TestClient(app)


def test_build_context():
    rag = BaselineRAG()
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="Q100",
            title="Archery at 2012 Olympics",
            text="South Korea won gold in women's team archery.",
            score=0.88,
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="Q101",
            title="Boxing at 2012 Olympics",
            text="Nicola Adams won gold in women's flyweight boxing.",
            score=0.75,
        ),
    ]
    context = rag.build_context(chunks)
    assert "[Chunk 1]" in context
    assert "Archery at 2012 Olympics" in context
    assert "Nicola Adams" in context


def test_extract_citations():
    rag = BaselineRAG()
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="Q1050909",
            title="Men's 20km walk",
            text="Chen Ding won gold.",
            score=0.9,
        )
    ]
    answer = "According to [Doc ID: Q1050909], Chen Ding won the gold medal."
    citations = rag.extract_citations(answer, chunks)
    assert "Q1050909" in citations


def test_baseline_rag_query():
    result = baseline_rag.query("Who won the gold medal in canoe sprint?", top_k=2)
    assert isinstance(result, RAGResult)
    assert result.latency_ms > 0
    assert result.retrieval_latency_ms >= 0
    assert result.llm_latency_ms >= 0
    assert result.total_tokens >= 0
    assert len(result.answer) > 0


def test_api_rag_query_endpoint():
    response = client.post(
        "/api/v1/rag/query",
        json={"question": "Who won gold in Olympic speed skating?", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "retrieved_chunks" in data
    assert "total_tokens" in data
    assert "latency_ms" in data


def test_api_rag_evaluate_endpoint():
    # Evaluate question pub-001
    response = client.post("/api/v1/rag/evaluate/pub-001?top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert data["question_id"] == "pub-001"
    assert "answer" in data
    assert "latency_ms" in data
    assert "ground_truth" in data
