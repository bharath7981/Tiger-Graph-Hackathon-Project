"""Strictly registered tools for the Agentic GraphRAG investigation."""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.graph.client import graph_client
from backend.app.services.evidence import detect_contradictions
from backend.app.agents.specialized import (
    entity_linking_agent,
    graph_traversal_agent,
    similarity_retrieval_agent,
    evidence_evaluation_agent,
    multihop_reasoning_agent,
    conflict_resolution_agent,
)


class ToolResult(BaseModel):
    """Normalized structured return value from any registered agent tool."""
    tool_name: str
    status: str = "success"  # success | error
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    tokens: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == "success"


# 1. Entity Linking Tool
def tool_entity_link(params: Dict[str, Any]) -> ToolResult:
    """Identifies and links candidate entities, years, sports, venues, and dates from text."""
    res = entity_linking_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="entity_link",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# 2. Vector Search Tool
def tool_vector_search(params: Dict[str, Any]) -> ToolResult:
    """Performs dense vector similarity search in ChromaDB."""
    res = similarity_retrieval_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="vector_search",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# 3. Graph Traversal Tool
def tool_graph_traversal(params: Dict[str, Any]) -> ToolResult:
    """Executes graph traversal patterns (aggregation, temporal, superlative, multi-hop, neighbors)."""
    start_time = time.perf_counter()
    traversal_type = params.get("traversal_type", "auto")

    # If neighbors explicitly requested
    if traversal_type == "neighbors":
        entity_id = params.get("entity_id", "")
        neighbors = graph_client.get_neighbors(entity_id)
        latency = (time.perf_counter() - start_time) * 1000.0
        summary = f"Traversed {len(neighbors)} neighbors for '{entity_id}'"
        return ToolResult(
            tool_name="graph_traversal",
            data={
                "neighbors": [n.model_dump() for n in neighbors],
                "entity_id": entity_id,
                "agent_name": "GraphTraversalAgent",
            },
            summary=summary,
            evidence_ids=[entity_id],
            latency_ms=round(latency, 2),
        )

    # Delegate to GraphTraversalAgent
    res = graph_traversal_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="graph_traversal",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# 4. Document Retrieval Tool
def tool_document_retrieval(params: Dict[str, Any]) -> ToolResult:
    """Retrieves full document vertex and metadata by document_id."""
    start_time = time.perf_counter()
    doc_id = params.get("document_id", "")
    if not doc_id:
        return ToolResult(
            tool_name="document_retrieval",
            status="error",
            error="Missing document_id",
            summary="Missing document_id",
        )

    try:
        vertex = graph_client.get_vertex(doc_id)
        latency = (time.perf_counter() - start_time) * 1000.0
        if vertex:
            title = vertex.properties.get("title", "")
            summary = f"Retrieved document record '{doc_id}' ({title})"
            return ToolResult(
                tool_name="document_retrieval",
                data={
                    "document": vertex.model_dump(),
                    "agent_name": "DocumentRetrievalAgent",
                },
                summary=summary,
                evidence_ids=[doc_id],
                latency_ms=round(latency, 2),
            )
        else:
            return ToolResult(
                tool_name="document_retrieval",
                status="success",
                data={"agent_name": "DocumentRetrievalAgent"},
                summary=f"Document '{doc_id}' not found in graph store.",
                latency_ms=round(latency, 2),
            )
    except Exception as e:
        logger.error(f"document_retrieval tool failed: {e}")
        return ToolResult(
            tool_name="document_retrieval",
            status="error",
            error=str(e),
            summary=f"Error retrieving document: {e}",
        )


# 5. Evidence Evaluation Tool
def tool_evidence_evaluation(params: Dict[str, Any]) -> ToolResult:
    """Evaluates whether current evidence is sufficient to answer the question."""
    res = evidence_evaluation_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="evidence_evaluation",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# 6. Conflict Detection Tool
def tool_conflict_detection(params: Dict[str, Any]) -> ToolResult:
    """Detects contradictions or conflicting claims among collected facts."""
    start_time = time.perf_counter()
    evidence = params.get("evidence", [])
    contradictions = detect_contradictions(evidence)
    has_conflict = len(contradictions) > 0
    latency = (time.perf_counter() - start_time) * 1000.0

    summary = (
        f"Detected {len(contradictions)} conflicting claim(s)"
        if has_conflict
        else "No conflicting claims detected among evidence sources."
    )

    return ToolResult(
        tool_name="conflict_detection",
        data={
            "has_conflict": has_conflict,
            "conflicts": contradictions,
            "agent_name": "EvidenceEvaluationAgent",
        },
        summary=summary,
        latency_ms=round(latency, 2),
    )


# 7. Conflict Resolution Tool
def tool_conflict_resolution(params: Dict[str, Any]) -> ToolResult:
    """Adjudicates competing assertions, source authority weighting, and retrospective medal reallocations."""
    res = conflict_resolution_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="conflict_resolution",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# 8. Final Answer Tool
def tool_final_answer(params: Dict[str, Any]) -> ToolResult:
    """Synthesizes grounded final response from accumulated evidence using MultiHopReasoningAgent."""
    res = multihop_reasoning_agent.run(params)
    data = res.data
    data["agent_name"] = res.agent_name
    return ToolResult(
        tool_name="final_answer",
        status=res.status,
        data=data,
        summary=res.summary,
        evidence_ids=res.evidence_ids,
        tokens=res.tokens,
        latency_ms=res.latency_ms,
        error=res.error,
    )


# Strictly registered tool dispatch registry (NO arbitrary code execution allowed!)
REGISTERED_TOOLS = {
    "entity_link": tool_entity_link,
    "vector_search": tool_vector_search,
    "graph_traversal": tool_graph_traversal,
    "document_retrieval": tool_document_retrieval,
    "evidence_evaluation": tool_evidence_evaluation,
    "conflict_detection": tool_conflict_detection,
    "conflict_resolution": tool_conflict_resolution,
    "final_answer": tool_final_answer,
}


def execute_tool(tool_name: str, params: Dict[str, Any]) -> ToolResult:
    """Safe dispatcher that only invokes explicitly registered tools."""
    if tool_name not in REGISTERED_TOOLS:
        logger.error(f"Unauthorized tool requested: {tool_name}")
        return ToolResult(
            tool_name=tool_name,
            status="error",
            error=f"Tool '{tool_name}' is not an authorized or registered tool.",
            summary=f"Tool '{tool_name}' is not authorized.",
        )
    return REGISTERED_TOOLS[tool_name](params)
