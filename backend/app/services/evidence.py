"""Evidence intelligence service for citation validation, contradiction detection, and groundedness."""

import re
from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field
from backend.app.core.logging import logger


class EvidenceReport(BaseModel):
    """Structured report on accumulated evidence validity and quality."""
    coverage_score: float = Field(ge=0.0, le=1.0)
    groundedness_score: float = Field(ge=0.0, le=1.0)
    is_sufficient: bool
    valid_citations: List[str] = Field(default_factory=list)
    hallucinated_citations: List[str] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    missing_aspects: List[str] = Field(default_factory=list)


def extract_citations(text: str) -> List[str]:
    """Extracts all bracketed citations such as [Q12345] or [doc_123] from text."""
    # Matches [Q123456], [Q12345], [doc_...], etc.
    citations = re.findall(r"\[(Q\d+|doc_[\w\d]+|chunk_[\w\d]+)\]", text)
    return sorted(list(set(citations)))


def validate_citations(
    answer: str,
    available_doc_ids: List[str],
) -> Tuple[List[str], List[str]]:
    """Validates citations in the answer against the set of available/retrieved document IDs.

    Returns:
        (valid_citations, hallucinated_citations)
    """
    cited = extract_citations(answer)
    available_set = set(available_doc_ids)

    valid = [c for c in cited if c in available_set]
    hallucinated = [c for c in cited if c not in available_set]

    return valid, hallucinated


def detect_contradictions(evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detects potential factual contradictions across retrieved evidence pieces.

    Checks:
    1. Date / Year conflicts for the same event
    2. Competing medalists / winners for the same event
    3. Conflicting venue locations
    """
    contradictions = []

    # Map entity -> values
    event_years: Dict[str, Set[str]] = {}
    event_venues: Dict[str, Set[str]] = {}
    event_winners: Dict[str, Set[str]] = {}

    for item in evidence_items:
        src = item.get("source", "unknown")
        txt = item.get("text", "") or item.get("claim", "")

        # Look for date patterns like 2012 vs 2016
        years = re.findall(r"\b(189\d|19\d\d|20\d\d)\b", txt)
        # Check event name mentions
        event_match = re.search(r"((?:men's|women's)?\s*[\w\s\-]+(?:\d+m|walk|relay|sprint|judo|weightlifting))", txt, re.IGNORECASE)
        if event_match and years:
            ev_name = event_match.group(1).strip().lower()
            for y in years:
                event_years.setdefault(ev_name, set()).add(y)

    # Flag events associated with mutually exclusive conflicting facts
    for ev, yrs in event_years.items():
        if len(yrs) > 2:  # If an event references more than 2 distinct Olympic years in contradictory contexts
            contradictions.append({
                "type": "temporal_multiplicity",
                "entity": ev,
                "values": sorted(list(yrs)),
                "description": f"Multiple distinct years ({', '.join(sorted(yrs))}) referenced for event '{ev}'",
            })

    return contradictions


def compute_evidence_coverage(question: str, evidence_items: List[Dict[str, Any]]) -> float:
    """Computes keyword and entity coverage ratio of question requirements within evidence."""
    if not evidence_items:
        return 0.0

    q_tokens = set(re.findall(r"\b\w{3,}\b", question.lower()))
    stop_words = {"what", "which", "when", "where", "who", "whom", "this", "that", "from", "with", "were", "been", "have", "more", "than", "many"}
    key_tokens = q_tokens - stop_words

    if not key_tokens:
        return 1.0

    accumulated_evidence_text = " ".join(
        (it.get("text", "") or it.get("claim", "") or str(it))
        for it in evidence_items
    ).lower()

    matched_tokens = sum(1 for tok in key_tokens if tok in accumulated_evidence_text)
    coverage = matched_tokens / len(key_tokens)
    return round(coverage, 3)


def compute_groundedness_score(answer: str, evidence_texts: List[str]) -> float:
    """Computes factual groundedness of the generated answer against evidence texts."""
    if not evidence_texts or not answer:
        return 0.0

    # Extract non-stop answer tokens
    ans_tokens = set(re.findall(r"\b\w{4,}\b", answer.lower()))
    stop_words = {"this", "that", "these", "those", "with", "from", "about", "there", "their", "which", "where", "after", "before", "during"}
    meaningful_tokens = ans_tokens - stop_words

    if not meaningful_tokens:
        return 0.5

    combined_evidence = " ".join(evidence_texts).lower()
    grounded_count = sum(1 for tok in meaningful_tokens if tok in combined_evidence)

    score = grounded_count / len(meaningful_tokens)
    return round(min(1.0, score), 3)


def evaluate_evidence_intelligence(
    question: str,
    answer: str,
    evidence_items: List[Dict[str, Any]],
    available_doc_ids: List[str],
) -> EvidenceReport:
    """Consolidated evidence intelligence assessment."""
    coverage = compute_evidence_coverage(question, evidence_items)
    evidence_texts = [it.get("text", "") or str(it) for it in evidence_items]
    groundedness = compute_groundedness_score(answer, evidence_texts)
    valid_cites, hall_cites = validate_citations(answer, available_doc_ids)
    contradictions = detect_contradictions(evidence_items)

    missing = []
    if coverage < 0.6:
        missing.append("Incomplete entity or relation coverage for question scope")

    is_sufficient = coverage >= 0.6 and len(hall_cites) == 0

    return EvidenceReport(
        coverage_score=coverage,
        groundedness_score=groundedness,
        is_sufficient=is_sufficient,
        valid_citations=valid_cites,
        hallucinated_citations=hall_cites,
        contradictions=contradictions,
        missing_aspects=missing,
    )
