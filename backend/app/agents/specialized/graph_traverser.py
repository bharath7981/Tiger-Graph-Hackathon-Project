"""Specialized Graph Traversal Agent for deterministic multi-hop graph querying."""

import time
from typing import Any, Dict, List
from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.pipelines.graphrag import tigergraph_rag
from backend.app.graph.client import graph_client
from backend.app.core.logging import logger


class GraphTraversalAgent(BaseSpecializedAgent):
    """Specialized agent to execute structured graph traversals on TigerGraph/LocalGraph."""

    def __init__(self):
        super().__init__(name="GraphTraversalAgent")

    def run(self, params: Dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        question = params.get("question", "")
        entities = params.get("entities")
        traversal_type = params.get("traversal_type", "auto")

        try:
            # 1. Neighbor expansion if explicitly requested
            if traversal_type == "neighbors":
                entity_id = params.get("entity_id", "")
                neighbors = graph_client.get_neighbors(entity_id)
                latency = (time.perf_counter() - start_time) * 1000.0
                summary = f"Traversed {len(neighbors)} neighbors for '{entity_id}'"
                return AgentResult(
                    agent_name=self.name,
                    status="success",
                    data={
                        "neighbors": [n.model_dump() for n in neighbors],
                        "entity_id": entity_id,
                    },
                    summary=summary,
                    evidence_ids=[entity_id],
                    latency_ms=round(latency, 2),
                    tokens=30 + len(neighbors) * 15,
                )

            # 2. Extract or use linked entities
            if not entities:
                entities = tigergraph_rag.link_entities_from_question(question)

            # 3. Execute targeted graph traversal
            evidence_objs, path_objs, citations = tigergraph_rag.execute_graph_traversal(entities, question)

            # 4. Format structured paths and facts
            formatted_paths = [
                f"{p.source} -[{p.edge}]-> {p.target}" for p in path_objs
            ]
            formatted_facts = [
                {
                    "fact": ev.fact,
                    "claim": ev.fact,
                    "document_id": ev.document_id,
                    "entity_id": ev.entity_id,
                    "entity_type": ev.entity_type,
                    "properties": ev.properties,
                }
                for ev in evidence_objs
            ]

            latency = (time.perf_counter() - start_time) * 1000.0
            summary = (
                f"Traversed {len(path_objs)} graph paths, extracted {len(evidence_objs)} facts, "
                f"identified {len(citations)} document backlinks."
            )

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "paths": formatted_paths,
                    "evidence": formatted_facts,
                    "citations": citations,
                    "entity_summary": entities,
                },
                summary=summary,
                evidence_ids=citations,
                latency_ms=round(latency, 2),
                tokens=35 + len(path_objs) * 15 + len(evidence_objs) * 20,
            )

        except Exception as e:
            logger.error(f"GraphTraversalAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                error=str(e),
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )


graph_traversal_agent = GraphTraversalAgent()
