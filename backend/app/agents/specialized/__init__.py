"""Specialized investigation agents package."""

from backend.app.agents.specialized.base import BaseSpecializedAgent, AgentResult
from backend.app.agents.specialized.entity_linker import (
    EntityLinkingAgent,
    entity_linking_agent,
)
from backend.app.agents.specialized.graph_traverser import (
    GraphTraversalAgent,
    graph_traversal_agent,
)
from backend.app.agents.specialized.similarity_retriever import (
    SimilarityRetrievalAgent,
    similarity_retrieval_agent,
)
from backend.app.agents.specialized.evidence_evaluator import (
    EvidenceEvaluationAgent,
    evidence_evaluation_agent,
)
from backend.app.agents.specialized.multihop_reasoner import (
    MultiHopReasoningAgent,
    multihop_reasoning_agent,
)
from backend.app.agents.specialized.conflict_resolver import (
    ConflictResolutionAgent,
    conflict_resolution_agent,
)

__all__ = [
    "BaseSpecializedAgent",
    "AgentResult",
    "EntityLinkingAgent",
    "entity_linking_agent",
    "GraphTraversalAgent",
    "graph_traversal_agent",
    "SimilarityRetrievalAgent",
    "similarity_retrieval_agent",
    "EvidenceEvaluationAgent",
    "evidence_evaluation_agent",
    "MultiHopReasoningAgent",
    "multihop_reasoning_agent",
    "ConflictResolutionAgent",
    "conflict_resolution_agent",
]
