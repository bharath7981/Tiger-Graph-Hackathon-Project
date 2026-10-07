"""Tests for TigerGraph GraphRAG pipeline and inspection endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.graph.schema import generate_gsql_schema, VERTEX_TYPES, EDGE_TYPES
from backend.app.graph.entity_extractor import entity_extractor
from backend.app.graph.client import graph_client
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.models.document import DocumentRecord
from backend.app.models.graphrag import GraphRAGResult

client = TestClient(app)


def test_schema_definitions():
    """Verify schema structures and GSQL generator."""
    assert "Event" in VERTEX_TYPES
    assert "Games" in VERTEX_TYPES
    assert "PART_OF_GAMES" in EDGE_TYPES
    assert "WON_MEDAL" in EDGE_TYPES

    gsql = generate_gsql_schema("OlympicGraph")
    assert "CREATE VERTEX Event" in gsql
    assert "CREATE DIRECTED EDGE PART_OF_GAMES" in gsql
    assert "CREATE GRAPH OlympicGraph" in gsql


def test_entity_extractor():
    """Verify deterministic entity extraction from infoboxes."""
    sample_doc = DocumentRecord(
        document_id="Q303623",
        source="https://en.wikipedia.org/wiki/Canoeing",
        title="Canoeing at the 2012 Summer Olympics – Men's K-2 1000 metres",
        content="""[Infobox Olympic event]
  event: Men's canoe sprint K-2 1,000 metres
  games: 2012 Summer
  venue: Eton Dorney
  date: 6 to 8 August
  competitors: 24
  nations: 12
  gold: Rudolf Dombi
  goldNOC: HUN
""",
        metadata={"approx_tokens": 50},
    )
    elements = entity_extractor.extract_from_document(sample_doc)
    assert len(elements.vertices["Event"]) == 1
    assert elements.vertices["Event"][0]["id"] == "Q303623"
    assert elements.vertices["Event"][0]["competitors"] == 24
    assert elements.vertices["Event"][0]["sport"] == "Canoeing"
    assert len(elements.vertices["Games"]) == 1
    assert elements.vertices["Games"][0]["name"] == "2012 Summer"
    assert len(elements.vertices["Athlete"]) == 1
    assert elements.vertices["Athlete"][0]["name"] == "Rudolf Dombi"
    assert len(elements.edges["WON_MEDAL"]) == 1
    assert elements.edges["WON_MEDAL"][0]["medal_type"] == "gold"


def test_graphrag_pipeline_query():
    """Verify GraphRAG query execution and structured output."""
    res = tigergraph_rag.query("Who won gold in canoe sprint at the 2012 Summer Olympics?")
    assert isinstance(res, GraphRAGResult)
    assert res.latency_ms > 0
    assert res.graph_latency_ms >= 0
    assert res.llm_latency_ms >= 0
    assert res.total_tokens >= 0
    assert len(res.answer) > 0


def test_api_graphrag_query_endpoint():
    """Verify POST /api/v1/graphrag/query."""
    response = client.post(
        "/api/v1/graphrag/query",
        json={"question": "Who won gold in Men's 20km walk at the 2016 Summer Olympics?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "graph_paths" in data
    assert "evidence" in data
    assert "total_tokens" in data
    assert "latency_ms" in data


def test_api_graph_inspection_endpoints():
    """Verify GET /api/v1/graph/entities/{id} and /api/v1/graph/neighbors/{id}."""
    # Ensure at least one test entity exists in graph
    graph_client.upsert_vertices("Sport", [{"id": "Athletics", "name": "Athletics"}])
    graph_client.upsert_vertices("Games", [{"id": "2012 Summer", "name": "2012 Summer"}])
    graph_client.upsert_edges("PART_OF_GAMES", [{"from_id": "Athletics", "to_id": "2012 Summer"}])

    # Entity endpoint
    res_entity = client.get("/api/v1/graph/entities/Athletics")
    assert res_entity.status_code == 200
    data = res_entity.json()
    assert data["entity_id"] == "Athletics"
    assert data["entity_type"] == "Sport"

    # Neighbors endpoint
    res_neighbors = client.get("/api/v1/graph/neighbors/Athletics")
    assert res_neighbors.status_code == 200
    neighbors = res_neighbors.json()
    assert isinstance(neighbors, list)
    assert len(neighbors) >= 1
    assert any(n["neighbor_id"] == "2012 Summer" for n in neighbors)
