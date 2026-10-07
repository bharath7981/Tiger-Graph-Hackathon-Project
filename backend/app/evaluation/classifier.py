"""Question complexity classification model for Agentic Value Analysis."""

from typing import Dict, Any


def classify_question_complexity(question: str, question_type: str = "unknown") -> Dict[str, Any]:
    """Classifies a question into a 4-tier complexity hierarchy.

    Tiers:
    - Level 1 (Simple Lookup): Factoid questions answerable by direct keyword matching or single chunk retrieval.
    - Level 2 (Relational): Questions requiring 1-hop graph relationship (e.g. venue -> event, sport -> games).
    - Level 3 (Multi-Hop / Temporal): Questions requiring sequence traversal (e.g. previous edition, venue + date).
    - Level 4 (Complex / Aggregation / Superlative): High-order constraints (e.g. count filtering > N, max/min superlative).
    """
    q_lower = question.lower()
    qtype_lower = question_type.lower()

    # Level 4: Aggregation or Superlative
    if (
        qtype_lower in ["aggregation", "superlative"]
        or any(kw in q_lower for kw in ["how many", "more than", "highest number", "most competitors", "count"])
    ):
        return {
            "level": 4,
            "label": "Complex Aggregation / Superlative",
            "recommended_pipeline": "Agentic GraphRAG",
            "justification": "Requires relational filtering across multiple edges with cardinality constraints.",
        }

    # Level 3: Multi-Hop or Temporal
    if (
        qtype_lower in ["multi_hop", "temporal"]
        or any(kw in q_lower for kw in ["immediately before", "preceding", "held at", "previous edition", "prior"])
    ):
        return {
            "level": 3,
            "label": "Multi-Hop / Temporal Reasoning",
            "recommended_pipeline": "Agentic GraphRAG",
            "justification": "Requires connecting intermediate entity states across temporal or spatial links.",
        }

    # Level 2: Relational
    if (
        any(kw in q_lower for kw in ["venue", "sport", "events at", "hosted", "location"])
    ):
        return {
            "level": 2,
            "label": "Relational Traversal",
            "recommended_pipeline": "GraphRAG",
            "justification": "Direct 1-hop graph edge provides deterministic answer without heavy agent loop.",
        }

    # Level 1: Simple Lookup
    return {
        "level": 1,
        "label": "Simple Factoid Lookup",
        "recommended_pipeline": "Baseline RAG",
        "justification": "Direct semantic similarity retrieval is sufficient and maximizes efficiency.",
    }
